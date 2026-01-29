#  -*- coding: utf-8 -*-
#
#  Copyright Featrix, Inc 2023-2025
#
#  Proprietary and Confidential.  Unauthorized use, copying or dissemination
#  of these materials is strictly prohibited.
"""
ES Training Callbacks - Extensible callback system for EmbeddingSpace training.

Callbacks allow injecting custom logic at various points during ES training
without modifying the core training loop.

Usage:
    from featrix.neural.es_training_callbacks import XGBoostQualityCallback

    # Create callback
    xgb_callback = XGBoostQualityCallback(target_col='target', check_interval=5)

    # Pass to ES training
    es.train(..., callbacks=[xgb_callback])
"""
import json
import logging
import os
import time
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from featrix.neural.embedded_space import EmbeddingSpace

logger = logging.getLogger(__name__)


class ESTrainingCallback(ABC):
    """
    Base class for ES training callbacks.

    Subclass this and implement the methods you need:
    - on_epoch_start: Called at the start of each epoch
    - on_epoch_end: Called at the end of each epoch (after validation)
    - on_training_start: Called once before training begins
    - on_training_end: Called once after training completes
    """

    def on_training_start(
        self,
        es: 'EmbeddingSpace',
        n_epochs: int,
        batch_size: int,
        **kwargs
    ) -> None:
        """Called once before training begins."""
        pass

    def on_epoch_start(
        self,
        es: 'EmbeddingSpace',
        epoch_idx: int,
        n_epochs: int,
        **kwargs
    ) -> None:
        """Called at the start of each epoch."""
        pass

    def on_epoch_end(
        self,
        es: 'EmbeddingSpace',
        epoch_idx: int,
        n_epochs: int,
        train_loss: float,
        val_loss: float,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Called at the end of each epoch (after validation).

        Returns:
            Optional dict of metrics to log/track
        """
        pass

    def on_training_end(
        self,
        es: 'EmbeddingSpace',
        n_epochs: int,
        **kwargs
    ) -> None:
        """Called once after training completes."""
        pass


class XGBoostQualityCallback(ESTrainingCallback):
    """
    Train XGBoost classifier on embeddings periodically to track downstream task quality.

    This is a cheap-to-train proxy metric for embedding quality during ES training.
    Every `check_interval` epochs, we:
    1. Encode train/val data using current embeddings
    2. Train XGBoost classifier on encoded data
    3. Log train/val AUC as embedding quality metrics
    4. Save results to xgboost_quality_tracking.json in output_dir

    Args:
        target_col: Name of target column for classification
        check_interval: Run check every N epochs (default: 5)
        batch_size: Batch size for encoding (default: 256)
        min_epoch: Minimum epoch before starting checks (default: 4)
        output_dir: Directory to save results JSON (default: current working directory)
    """

    def __init__(
        self,
        target_col: str,
        check_interval: int = 5,
        batch_size: int = 256,
        min_epoch: int = 4,
        output_dir: Optional[str] = None
    ):
        self.target_col = target_col
        self.check_interval = check_interval
        self.batch_size = batch_size
        self.min_epoch = min_epoch
        self.output_dir = output_dir
        self.history: List[Dict[str, Any]] = []
        self.output_file: Optional[str] = None

    def on_training_start(
        self,
        es: 'EmbeddingSpace',
        n_epochs: int,
        batch_size: int,
        **kwargs
    ) -> None:
        """Log callback registration."""
        logger.info("")
        logger.info("=" * 60)
        logger.info("🎯 XGBOOST QUALITY CALLBACK REGISTERED")
        logger.info(f"   Target column: {self.target_col}")
        logger.info(f"   Check interval: every {self.check_interval} epochs")
        logger.info(f"   Min epoch: {self.min_epoch + 1}")
        logger.info(f"   Will check at epochs: {', '.join(str(e) for e in range(self.check_interval, n_epochs + 1, self.check_interval) if e > self.min_epoch)}")
        logger.info("=" * 60)
        logger.info("")

    def on_epoch_end(
        self,
        es: 'EmbeddingSpace',
        epoch_idx: int,
        n_epochs: int,
        train_loss: float,
        val_loss: float,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """Train XGBoost and log metrics if this is a check epoch."""
        # Only run every check_interval epochs (starting after min_epoch)
        # epoch_idx is 0-based, so epoch_idx=4 is epoch 5
        is_check_epoch = (epoch_idx + 1) % self.check_interval == 0
        past_min_epoch = epoch_idx >= self.min_epoch

        if not past_min_epoch:
            logger.debug(f"XGBoostQualityCallback: epoch {epoch_idx+1} < min_epoch {self.min_epoch+1}, skipping")
            return None
        if not is_check_epoch:
            logger.debug(f"XGBoostQualityCallback: epoch {epoch_idx+1} not a check epoch (interval={self.check_interval})")
            return None

        logger.info(f"🎯 XGBoostQualityCallback: Running quality check at epoch {epoch_idx + 1}...")
        return self._run_quality_check(es, epoch_idx)

    def _run_quality_check(
        self,
        es: 'EmbeddingSpace',
        epoch_idx: int
    ) -> Optional[Dict[str, Any]]:
        """Run XGBoost quality check on current embeddings."""
        # Check if we have train/val data available
        if not hasattr(es, 'train_input_data') or es.train_input_data is None:
            logger.debug("XGBoost quality check skipped: no train_input_data")
            return None
        if not hasattr(es, 'val_input_data') or es.val_input_data is None:
            logger.debug("XGBoost quality check skipped: no val_input_data")
            return None

        train_df = es.train_input_data.df
        val_df = es.val_input_data.df

        # Verify target column exists
        if self.target_col not in train_df.columns:
            logger.debug(f"XGBoost quality check skipped: target '{self.target_col}' not in train data")
            return None
        if self.target_col not in val_df.columns:
            logger.debug(f"XGBoost quality check skipped: target '{self.target_col}' not in val data")
            return None

        try:
            from featrix.neural.xgboost_classifier import FeatrixXGBoostClassifier

            start_time = time.time()

            # Create XGBoost classifier with current embedding space
            clf = FeatrixXGBoostClassifier(es, name=f"es_epoch_{epoch_idx}_quality")

            # Fit on training data
            clf.fit(train_df, target_col=self.target_col, batch_size=self.batch_size, verbose=False)

            # Evaluate on validation data
            val_metrics = clf.evaluate(val_df, val_df[self.target_col], batch_size=self.batch_size)

            elapsed = time.time() - start_time

            # Log results with nice formatting
            logger.info("")
            logger.info("=" * 80)
            logger.info(f"🎯 XGBOOST EMBEDDING QUALITY CHECK @ epoch {epoch_idx + 1}")
            logger.info("=" * 80)
            logger.info(f"   Train AUC: {clf.fit_metrics_['auc']:.4f}")
            logger.info(f"   Val AUC:   {val_metrics['auc']:.4f}")
            logger.info(f"   Gap:       {clf.fit_metrics_['auc'] - val_metrics['auc']:.4f}")
            logger.info(f"   Time:      {elapsed:.1f}s")
            logger.info("=" * 80)
            logger.info("")

            # Store metrics for tracking
            metrics = {
                'epoch': epoch_idx + 1,
                'train_auc': clf.fit_metrics_['auc'],
                'val_auc': val_metrics['auc'],
                'train_acc': clf.fit_metrics_['accuracy'],
                'val_acc': val_metrics['accuracy'],
                'train_f1': clf.fit_metrics_['f1'],
                'val_f1': val_metrics['f1'],
                'gap': clf.fit_metrics_['auc'] - val_metrics['auc'],
                'time': elapsed,
            }

            self.history.append(metrics)
            return metrics

        except ImportError as e:
            logger.debug(f"XGBoost quality check skipped: {e}")
            return None
        except Exception as e:
            logger.warning(f"⚠️ XGBoost quality check failed: {e}")
            return None

    def on_training_end(
        self,
        es: 'EmbeddingSpace',
        n_epochs: int,
        **kwargs
    ) -> None:
        """Log summary of XGBoost quality metrics across training."""
        if not self.history:
            return

        logger.info("")
        logger.info("=" * 80)
        logger.info("📊 XGBOOST EMBEDDING QUALITY SUMMARY (across training)")
        logger.info("=" * 80)
        logger.info(f"   {'Epoch':>6}  {'Train AUC':>10}  {'Val AUC':>10}  {'Gap':>8}")
        logger.info(f"   {'-'*6}  {'-'*10}  {'-'*10}  {'-'*8}")
        for entry in self.history:
            logger.info(
                f"   {entry['epoch']:>6}  {entry['train_auc']:>10.4f}  "
                f"{entry['val_auc']:>10.4f}  {entry['gap']:>8.4f}"
            )
        logger.info("=" * 80)

        # Log best val AUC
        best = max(self.history, key=lambda x: x['val_auc'])
        logger.info(f"   Best Val AUC: {best['val_auc']:.4f} @ epoch {best['epoch']}")
        logger.info("=" * 80)
        logger.info("")

        # Store history on ES for later access
        if not hasattr(es, '_xgboost_quality_history'):
            es._xgboost_quality_history = []
        es._xgboost_quality_history.extend(self.history)

        # Save results to JSON file
        self._save_results_json(es, n_epochs, best)

    def _save_results_json(
        self,
        es: 'EmbeddingSpace',
        n_epochs: int,
        best: Dict[str, Any]
    ) -> None:
        """Save XGBoost quality tracking results to JSON file with metadata."""
        import socket

        # Determine output directory
        if self.output_dir:
            out_dir = Path(self.output_dir)
        else:
            # Try to get from ES output directory, fall back to cwd
            out_dir = Path(os.getcwd())
            if hasattr(es, 'output_dir') and es.output_dir:
                out_dir = Path(es.output_dir)

        out_dir.mkdir(parents=True, exist_ok=True)

        # Get version info
        try:
            from featrix.neural import __version__ as featrix_version
        except ImportError:
            featrix_version = "unknown"

        # Build metadata
        metadata = {
            "created_at": datetime.now().isoformat(),
            "hostname": socket.gethostname(),
            "featrix_version": featrix_version,
            "target_column": self.target_col,
            "check_interval": self.check_interval,
            "total_es_epochs": n_epochs,
            "d_model": es.d_model if hasattr(es, 'd_model') else None,
            "num_checks": len(self.history),
        }

        # Build summary
        summary = {
            "best_val_auc": best['val_auc'],
            "best_epoch": best['epoch'],
            "final_val_auc": self.history[-1]['val_auc'] if self.history else None,
            "final_train_auc": self.history[-1]['train_auc'] if self.history else None,
            "final_gap": self.history[-1]['gap'] if self.history else None,
        }

        # Compute trend (is val_auc improving?)
        if len(self.history) >= 2:
            first_val_auc = self.history[0]['val_auc']
            last_val_auc = self.history[-1]['val_auc']
            summary["val_auc_trend"] = last_val_auc - first_val_auc
            summary["val_auc_improving"] = last_val_auc > first_val_auc

        # Build full output
        output = {
            "metadata": metadata,
            "summary": summary,
            "history": self.history,
        }

        # Write to file
        output_file = out_dir / "xgboost_quality_tracking.json"
        with open(output_file, 'w') as f:
            json.dump(output, f, indent=2)

        self.output_file = str(output_file)
        logger.info(f"📁 XGBoost quality results saved to: {output_file}")
