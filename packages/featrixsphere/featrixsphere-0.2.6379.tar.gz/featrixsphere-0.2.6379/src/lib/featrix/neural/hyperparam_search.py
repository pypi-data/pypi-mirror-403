#!/usr/bin/env python3
"""
Hyperparameter Search Runner

Loads experiments from ThingsToTry JSON files and runs them sequentially,
recording results to ThingsTried JSON files.

Usage:
    1. Set config.json:
       "hyperparam_search_file": "/sphere/app/ThingsToTry_taco.json"

    2. Start training - it will automatically:
       - Load next untried experiment
       - Apply hyperparameter overrides
       - Train for evaluate_at_epoch epochs
       - Record AUC/PR-AUC results
       - Move to next experiment
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

logger = logging.getLogger(__name__)


class HyperparameterSearch:
    """
    Manages hyperparameter search experiments.

    Reads experiments from ThingsToTry JSON, tracks which have been tried,
    and records results to ThingsTried JSON.
    """

    def __init__(self, search_file: str, results_file: Optional[str] = None):
        """
        Initialize hyperparameter search.

        Args:
            search_file: Path to ThingsToTry JSON file
            results_file: Path to ThingsTried JSON file (auto-generated if None)
        """
        self.search_file = Path(search_file)

        if results_file:
            self.results_file = Path(results_file)
        else:
            # Auto-generate results file name
            stem = self.search_file.stem.replace("ThingsToTry", "ThingsTried")
            self.results_file = self.search_file.parent / f"{stem}.json"

        self.experiments = []
        self.results = []
        self.evaluate_at_epoch = 20
        self.extend_threshold = 0.7  # If AUC > this, keep going
        self.extend_epochs = 10  # How many more epochs to run
        self.current_experiment = None
        self._current_target_epoch = None  # Tracks extended target for current experiment

        self._load_experiments()
        self._load_results()

    def _load_experiments(self) -> None:
        """Load experiments from ThingsToTry JSON."""
        if not self.search_file.exists():
            logger.warning(f"⚠️  Hyperparam search file not found: {self.search_file}")
            return

        try:
            with open(self.search_file, 'r') as f:
                data = json.load(f)

            self.experiments = data.get("experiments", [])
            self.evaluate_at_epoch = data.get("evaluate_at_epoch", 20)
            self.extend_threshold = data.get("extend_threshold", 0.7)
            self.extend_epochs = data.get("extend_epochs", 10)
            self.machine = data.get("machine", "unknown")

            logger.info(f"📋 Loaded {len(self.experiments)} experiments from {self.search_file}")
            logger.info(f"   Machine: {self.machine}, Evaluate at epoch: {self.evaluate_at_epoch}")
            logger.info(f"   Extend if AUC > {self.extend_threshold} by +{self.extend_epochs} epochs")

        except Exception as e:
            logger.error(f"❌ Failed to load experiments: {e}")
            self.experiments = []

    def _load_results(self) -> None:
        """Load existing results from ThingsTried JSON."""
        if not self.results_file.exists():
            logger.info(f"📝 Results file will be created: {self.results_file}")
            self.results = []
            return

        try:
            with open(self.results_file, 'r') as f:
                data = json.load(f)

            self.results = data.get("experiments", [])
            logger.info(f"📊 Loaded {len(self.results)} previous results from {self.results_file}")

        except Exception as e:
            logger.warning(f"⚠️  Failed to load results: {e}")
            self.results = []

    def _save_results(self) -> None:
        """Save results to ThingsTried JSON with fallback locations."""
        data = {
            "description": f"Hyperparameter search results from {self.search_file.name}",
            "machine": getattr(self, 'machine', 'unknown'),
            "last_updated": datetime.now().isoformat(),
            "experiments": self.results
        }

        # Try primary location first, then fallbacks
        fallback_paths = [
            self.results_file,
            Path("/tmp") / self.results_file.name,
            Path.home() / self.results_file.name,
        ]

        for path in fallback_paths:
            try:
                with open(path, 'w') as f:
                    json.dump(data, f, indent=2)
                if path != self.results_file:
                    logger.warning(f"⚠️  Using fallback location: {path}")
                    self.results_file = path  # Update for future saves
                logger.info(f"💾 Saved {len(self.results)} results to {path}")
                return
            except PermissionError:
                logger.warning(f"⚠️  Permission denied writing to {path}")
                continue
            except Exception as e:
                logger.warning(f"⚠️  Failed to write to {path}: {e}")
                continue

        # All file writes failed - log as JSON string as last resort
        logger.error(f"❌ Could not save results to any file location!")
        logger.error(f"📋 RESULTS JSON (copy this!):\n{json.dumps(data, indent=2)}")

    def get_tried_experiment_ids(self) -> set:
        """Get set of experiment IDs that have been tried."""
        return {r["id"] for r in self.results}

    def get_next_experiment(self) -> Optional[Dict[str, Any]]:
        """
        Get the next experiment to run.

        Returns:
            Experiment dict with id, name, changes, or None if all done
        """
        tried_ids = self.get_tried_experiment_ids()

        for exp in self.experiments:
            if exp["id"] not in tried_ids:
                self.current_experiment = exp
                self._current_target_epoch = self.evaluate_at_epoch  # Reset target
                logger.info(f"🔬 Next experiment: #{exp['id']} - {exp['name']}")
                logger.info(f"   Changes: {exp.get('changes', {})}")
                return exp

        logger.info("✅ All experiments completed!")
        return None

    def record_result(
        self,
        experiment_id: int,
        experiment_name: str,
        auc_roc: float,
        pr_auc: float,
        train_loss: float,
        val_loss: float,
        epoch: int,
        session_id: Optional[str] = None,
        log_path: Optional[str] = None,
        start_auc: Optional[float] = None,
        extra_metrics: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Record result for an experiment.

        Args:
            experiment_id: Experiment ID
            experiment_name: Experiment name
            auc_roc: AUC-ROC at evaluation epoch
            pr_auc: PR-AUC at evaluation epoch
            train_loss: Training loss at evaluation epoch
            val_loss: Validation loss at evaluation epoch
            epoch: Epoch at which metrics were recorded
            session_id: Session ID where this experiment ran
            log_path: Path to log files for this experiment
            start_auc: AUC-ROC at epoch 0/1 (starting point)
            extra_metrics: Additional metrics to record
        """
        result = {
            "id": experiment_id,
            "name": experiment_name,
            "epoch": epoch,
            "auc_roc": auc_roc,
            "pr_auc": pr_auc,
            "train_loss": train_loss,
            "val_loss": val_loss,
            "timestamp": datetime.now().isoformat(),
        }

        if session_id:
            result["session_id"] = session_id
        if log_path:
            result["log_path"] = log_path
        if start_auc is not None:
            result["start_auc"] = start_auc

        if extra_metrics:
            result["extra"] = extra_metrics

        # Find and update existing result or append new one
        existing_idx = None
        for i, r in enumerate(self.results):
            if r["id"] == experiment_id:
                existing_idx = i
                break

        if existing_idx is not None:
            self.results[existing_idx] = result
        else:
            self.results.append(result)

        self._save_results()

        logger.info(f"📊 Recorded result for #{experiment_id} ({experiment_name}):")
        logger.info(f"   AUC-ROC: {auc_roc:.4f}, PR-AUC: {pr_auc:.4f}")
        logger.info(f"   Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}")

    def get_best_experiment(self, metric: str = "auc_roc") -> Optional[Dict[str, Any]]:
        """
        Get the best experiment so far based on a metric.

        Args:
            metric: Metric to optimize ("auc_roc" or "pr_auc")

        Returns:
            Best result dict or None if no results
        """
        if not self.results:
            return None

        return max(self.results, key=lambda r: r.get(metric, 0))

    def get_summary(self) -> str:
        """Get summary of experiments and results."""
        lines = []
        lines.append("=" * 70)
        lines.append("HYPERPARAMETER SEARCH SUMMARY")
        lines.append("=" * 70)
        lines.append(f"Search file: {self.search_file}")
        lines.append(f"Results file: {self.results_file}")
        lines.append(f"Total experiments: {len(self.experiments)}")
        lines.append(f"Completed: {len(self.results)}")
        lines.append(f"Remaining: {len(self.experiments) - len(self.results)}")
        lines.append("")

        if self.results:
            # Sort by AUC-ROC descending
            sorted_results = sorted(self.results, key=lambda r: r.get("auc_roc", 0), reverse=True)

            lines.append("RESULTS (sorted by AUC-ROC):")
            lines.append("-" * 70)
            lines.append(f"{'#':>3} {'Name':<25} {'AUC-ROC':>10} {'PR-AUC':>10} {'Val Loss':>10}")
            lines.append("-" * 70)

            for r in sorted_results:
                lines.append(
                    f"{r['id']:>3} {r['name']:<25} {r.get('auc_roc', 0):>10.4f} "
                    f"{r.get('pr_auc', 0):>10.4f} {r.get('val_loss', 0):>10.4f}"
                )

            lines.append("-" * 70)
            best = sorted_results[0]
            lines.append(f"🏆 BEST: #{best['id']} {best['name']} (AUC-ROC: {best.get('auc_roc', 0):.4f})")

        lines.append("=" * 70)
        return "\n".join(lines)

    def should_stop_early(self, current_epoch: int, current_auc: float = 0.0) -> bool:
        """
        Check if we should stop the current experiment.

        If AUC > extend_threshold at target epoch, extends by extend_epochs.
        Keeps extending as long as AUC stays above threshold.

        Args:
            current_epoch: Current training epoch
            current_auc: Current AUC-ROC value

        Returns:
            True if we should stop, False to keep going
        """
        if self._current_target_epoch is None:
            self._current_target_epoch = self.evaluate_at_epoch

        if current_epoch < self._current_target_epoch:
            return False  # Not at target yet

        # We've reached the target epoch - check if we should extend
        if current_auc > self.extend_threshold:
            old_target = self._current_target_epoch
            self._current_target_epoch += self.extend_epochs
            logger.info(f"🚀 AUC {current_auc:.4f} > {self.extend_threshold} - extending from epoch {old_target} to {self._current_target_epoch}")
            return False  # Keep going

        # AUC dropped below threshold or was never above - stop
        logger.info(f"🛑 Stopping at epoch {current_epoch} (AUC {current_auc:.4f} <= {self.extend_threshold})")
        return True

    def is_experiment_active(self) -> bool:
        """Check if there's an active experiment running."""
        return self.current_experiment is not None

    def clear_current_experiment(self) -> None:
        """Clear the current experiment (after recording results)."""
        self.current_experiment = None


def load_hyperparam_search() -> Optional[HyperparameterSearch]:
    """
    Load hyperparameter search from config if configured.

    Returns:
        HyperparameterSearch instance or None if not configured
    """
    from featrix.neural.sphere_config import SphereConfig

    config = SphereConfig.get_instance()
    search_file = config.get_hyperparam_search_file()

    if not search_file:
        return None

    results_file = config.get_hyperparam_results_file()

    return HyperparameterSearch(search_file, results_file)


if __name__ == "__main__":
    # Test with sample files
    import sys

    if len(sys.argv) > 1:
        search_file = sys.argv[1]
    else:
        search_file = "/sphere/app/ThingsToTry_taco.json"

    search = HyperparameterSearch(search_file)

    print(search.get_summary())

    next_exp = search.get_next_experiment()
    if next_exp:
        print(f"\nNext experiment: {next_exp}")
