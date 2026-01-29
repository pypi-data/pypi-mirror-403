#!/usr/bin/env python3
"""
Multi-Dataset QA Test

Runs the full ES + SP training pipeline on multiple datasets and produces
a summary table of results. Uses system defaults for all hyperparameters
except epochs.

Datasets:
- spaceship-titanic.csv (binary classification)
- credit-g.csv (binary classification)
- banknote-fraud.csv (binary classification)

Usage:
    python test_multi_dataset.py [--es-epochs=N] [--sp-epochs=N]
"""
import sys
import os
import argparse
import shutil
import time
import asyncio
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
import traceback

# Setup paths
test_dir = Path(__file__).parent
neural_dir = test_dir.parent
featrix_dir = neural_dir.parent
lib_dir = featrix_dir.parent
src_dir = lib_dir.parent

sys.path.insert(0, str(lib_dir))
sys.path.insert(0, str(src_dir))

# Import after path setup
from featrix.neural.input_data_file import FeatrixInputDataFile
from featrix.neural.embedded_space import EmbeddingSpace
from featrix.neural.input_data_set import FeatrixInputDataSet
from featrix.neural.single_predictor import FeatrixSinglePredictor
from featrix.neural.training_exceptions import TrainingFailureException, EarlyStoppingException

import pandas as pd
import numpy as np
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class DatasetConfig:
    """Configuration for a test dataset."""
    name: str
    filename: str
    target_column: str
    description: str


@dataclass
class TrainingResult:
    """Results from training on a single dataset."""
    dataset_name: str
    success: bool
    error_message: Optional[str] = None

    # ES metrics
    es_time_seconds: float = 0.0
    es_final_loss: Optional[float] = None
    es_quality: Optional[str] = None  # "GOOD", "MODERATE", "POOR"
    es_params: int = 0

    # SP metrics
    sp_time_seconds: float = 0.0
    sp_accuracy: Optional[float] = None
    sp_precision: Optional[float] = None
    sp_recall: Optional[float] = None
    sp_f1: Optional[float] = None
    sp_auc_roc: Optional[float] = None


# Define test datasets
DATASETS = [
    DatasetConfig(
        name="Titanic",
        filename="spaceship-titanic.csv",
        target_column="Transported",
        description="Spaceship Titanic passenger transport prediction"
    ),
    DatasetConfig(
        name="Credit-G",
        filename="credit_g_31.csv",
        target_column="target",
        description="German credit risk classification"
    ),
    DatasetConfig(
        name="Banknote",
        filename="banknote-fraud.csv",
        target_column="class",
        description="Banknote authentication (fraud detection)"
    ),
]


def find_data_file(filename: str) -> Optional[Path]:
    """Find a data file in various locations."""
    # Try multiple locations
    search_paths = [
        test_dir / "qa_data_sets" / filename,  # src/lib/featrix/neural/qa/qa_data_sets/
        Path.cwd() / "qa_data" / filename,  # project_root/qa_data/
        Path.cwd() / "src/lib/featrix/neural/qa/qa_data_sets" / filename,  # full path from cwd
    ]
    for filepath in search_paths:
        if filepath.exists():
            return filepath
    return None


def train_on_dataset(
    config: DatasetConfig,
    es_epochs: int,
    sp_epochs: int,
    output_dir: Path,
) -> TrainingResult:
    """Train ES + SP on a single dataset and return results."""

    result = TrainingResult(dataset_name=config.name, success=False)
    original_cwd = None  # Track original directory for cleanup

    # Find data file
    data_path = find_data_file(config.filename)
    if data_path is None:
        result.error_message = f"Data file not found: {config.filename}"
        return result

    logger.info(f"=" * 60)
    logger.info(f"Training on {config.name}: {config.description}")
    logger.info(f"=" * 60)
    logger.info(f"  Data file: {data_path}")
    logger.info(f"  Target column: {config.target_column}")
    logger.info(f"  ES epochs: {es_epochs}, SP epochs: {sp_epochs}")

    try:
        # Load data
        input_file = FeatrixInputDataFile(str(data_path))
        df = input_file.df
        logger.info(f"  Loaded {len(df)} rows, {len(df.columns)} columns")

        # Check target column exists
        if config.target_column not in df.columns:
            result.error_message = f"Target column '{config.target_column}' not found in dataset"
            return result

        # Create dataset (exclude target column from ES training)
        dataset = FeatrixInputDataSet(
            df=df,
            ignore_cols=[config.target_column],
            limit_rows=None,
            encoder_overrides=None
        )

        # Get detected types for encoder overrides
        detected_types = {}
        for col_name, detector in dataset._detectors.items():
            detected_types[col_name] = detector.get_codec_name()
        dataset.encoderOverrides = detected_types

        # Split data
        train_data, val_data = dataset.split(fraction=0.2)
        logger.info(f"  Train: {len(train_data.df)} rows, Val: {len(val_data.df)} rows")

        # Create output directory for this dataset and chdir to it
        # This ensures checkpoints are scoped to each dataset (avoids cross-dataset checkpoint confusion)
        dataset_output_dir = output_dir / config.name.lower().replace("-", "_")
        dataset_output_dir.mkdir(parents=True, exist_ok=True)
        original_cwd = os.getcwd()
        os.chdir(dataset_output_dir)
        logger.info(f"  Working directory: {dataset_output_dir}")

        # ===== TRAIN EMBEDDING SPACE =====
        # Only specify epochs - let system choose all other hyperparameters
        logger.info(f"  Training Embedding Space...")
        es_start = time.time()

        es = EmbeddingSpace(
            train_input_data=train_data,
            val_input_data=val_data,
            n_epochs=es_epochs,
            output_dir=str(dataset_output_dir),
        )
        es.train()

        es_end = time.time()
        result.es_time_seconds = es_end - es_start

        # Get ES metrics
        if hasattr(es, 'model_param_count'):
            result.es_params = es.model_param_count.get('total_params', 0)

        # Get quality assessment if available
        if hasattr(es, 'quality_assessment'):
            result.es_quality = es.quality_assessment
        else:
            result.es_quality = "N/A"

        logger.info(f"  ES training complete in {result.es_time_seconds:.1f}s")
        logger.info(f"  ES params: {result.es_params:,}")

        # ===== TRAIN SINGLE PREDICTOR =====
        # Only specify epochs - let system choose all other hyperparameters
        logger.info(f"  Training Single Predictor...")
        sp_start = time.time()

        # Create FeatrixSinglePredictor - predictor architecture auto-detected in prep_for_training
        fsp = FeatrixSinglePredictor(es)

        # Prepare for training - need to add target back to train_df
        train_df_for_sp = train_data.df.copy()
        train_df_for_sp[config.target_column] = df.loc[train_df_for_sp.index, config.target_column]

        fsp.prep_for_training(
            train_df=train_df_for_sp,
            target_col_name=config.target_column,
            target_col_type="set",
        )

        # Train the predictor - only specify epochs
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            training_results = loop.run_until_complete(fsp.train(
                n_epochs=sp_epochs,
            ))
        except (TrainingFailureException, EarlyStoppingException) as e:
            logger.info(f"  Early stopping triggered: {e}")
            training_results = getattr(fsp, 'training_info', [])
        finally:
            loop.close()

        sp_end = time.time()
        result.sp_time_seconds = sp_end - sp_start

        # Extract final metrics
        if hasattr(fsp, 'training_info') and fsp.training_info:
            # Get metrics from last epoch
            last_epoch = fsp.training_info[-1] if fsp.training_info else {}
            metrics = last_epoch.get('metrics', {})
            result.sp_accuracy = metrics.get('accuracy')
            result.sp_precision = metrics.get('precision')
            result.sp_recall = metrics.get('recall')
            result.sp_f1 = metrics.get('f1')
            result.sp_auc_roc = metrics.get('auc')

        # If we have best_model_metrics, prefer those
        if hasattr(fsp, 'best_model_metrics') and fsp.best_model_metrics:
            result.sp_accuracy = fsp.best_model_metrics.get('accuracy', result.sp_accuracy)
            result.sp_f1 = fsp.best_model_metrics.get('f1', result.sp_f1)
            result.sp_auc_roc = fsp.best_model_metrics.get('roc_auc', result.sp_auc_roc)

        logger.info(f"  SP training complete in {result.sp_time_seconds:.1f}s")
        if result.sp_accuracy is not None:
            logger.info(f"  SP Accuracy: {result.sp_accuracy:.4f}")

        result.success = True

    except Exception as e:
        result.error_message = str(e)
        logger.error(f"  FAILED: {e}")
        traceback.print_exc()

    finally:
        # Always restore original working directory
        if original_cwd is not None:
            os.chdir(original_cwd)

    return result


def print_summary(results: List[TrainingResult]) -> None:
    """Print a summary table of all results."""

    print()
    print("=" * 100)
    print("                           MULTI-DATASET QA TEST SUMMARY")
    print("=" * 100)
    print()

    # Header
    print(f"{'Dataset':<12} {'Status':<8} {'ES Time':>10} {'ES Params':>12} {'SP Time':>10} "
          f"{'Accuracy':>10} {'F1':>10} {'AUC-ROC':>10}")
    print("-" * 100)

    # Results rows
    for r in results:
        status = "PASS" if r.success else "FAIL"
        es_time = f"{r.es_time_seconds:.1f}s" if r.es_time_seconds > 0 else "N/A"
        es_params = f"{r.es_params:,}" if r.es_params > 0 else "N/A"
        sp_time = f"{r.sp_time_seconds:.1f}s" if r.sp_time_seconds > 0 else "N/A"
        accuracy = f"{r.sp_accuracy:.4f}" if r.sp_accuracy is not None else "N/A"
        f1 = f"{r.sp_f1:.4f}" if r.sp_f1 is not None else "N/A"
        auc = f"{r.sp_auc_roc:.4f}" if r.sp_auc_roc is not None else "N/A"

        print(f"{r.dataset_name:<12} {status:<8} {es_time:>10} {es_params:>12} {sp_time:>10} "
              f"{accuracy:>10} {f1:>10} {auc:>10}")

        if r.error_message:
            print(f"             Error: {r.error_message[:70]}...")

    print("-" * 100)

    # Summary stats
    passed = sum(1 for r in results if r.success)
    failed = len(results) - passed
    total_time = sum(r.es_time_seconds + r.sp_time_seconds for r in results)

    print()
    print(f"Total: {passed} passed, {failed} failed, {total_time:.1f}s total time")

    # Average metrics for successful runs
    successful = [r for r in results if r.success and r.sp_accuracy is not None]
    if successful:
        avg_acc = sum(r.sp_accuracy for r in successful) / len(successful)
        f1_vals = [r.sp_f1 for r in successful if r.sp_f1 is not None]
        avg_f1 = sum(f1_vals) / len(f1_vals) if f1_vals else 0
        print(f"Average accuracy: {avg_acc:.4f}, Average F1: {avg_f1:.4f}")

    print()

    # Final verdict
    if failed == 0:
        print("RESULT: ALL TESTS PASSED")
    else:
        print(f"RESULT: {failed} TEST(S) FAILED")

    print("=" * 100)


def main():
    parser = argparse.ArgumentParser(description="Multi-dataset QA test")
    parser.add_argument("--es-epochs", type=int, default=25, help="ES training epochs (default: 25)")
    parser.add_argument("--sp-epochs", type=int, default=25, help="SP training epochs (default: 25)")
    parser.add_argument("--output-dir", type=str, default=None, help="Output directory")
    args = parser.parse_args()

    # Output directory
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = Path("/tmp/qa_multi_dataset_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory: {output_dir}")

    print()
    print("=" * 60)
    print("        MULTI-DATASET QA TEST")
    print("=" * 60)
    print(f"  ES epochs: {args.es_epochs}")
    print(f"  SP epochs: {args.sp_epochs}")
    print(f"  Datasets: {', '.join(d.name for d in DATASETS)}")
    print(f"  Started: {datetime.now()}")
    print("=" * 60)
    print()

    # Run training on each dataset
    results = []
    for config in DATASETS:
        result = train_on_dataset(
            config=config,
            es_epochs=args.es_epochs,
            sp_epochs=args.sp_epochs,
            output_dir=output_dir,
        )
        results.append(result)
        print()

    # Print summary
    print_summary(results)

    # Return exit code
    failed = sum(1 for r in results if not r.success)
    return failed


if __name__ == "__main__":
    sys.exit(main())
