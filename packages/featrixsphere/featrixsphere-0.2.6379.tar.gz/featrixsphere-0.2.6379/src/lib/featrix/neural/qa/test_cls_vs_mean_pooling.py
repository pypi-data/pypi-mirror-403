#!/usr/bin/env python3
"""
CLS Token vs Mean Pooling Ablation Test

Compares classification AUC between:
1. CLS token pooling (position 0 output from transformer)
2. Mean pooling (average of all column embeddings)

Uses credit-g dataset for binary classification.
"""
import sys
import os
import json
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np
import argparse

# Paths
test_dir = Path(__file__).parent
neural_dir = test_dir.parent
featrix_dir = neural_dir.parent
lib_dir = featrix_dir.parent
src_dir = lib_dir.parent

import importlib
importlib.invalidate_caches()

sys.path.insert(0, str(lib_dir))
sys.path.insert(0, str(src_dir))

from featrix.neural.input_data_file import FeatrixInputDataFile
from featrix.neural.embedded_space import EmbeddingSpace
from featrix.neural.input_data_set import FeatrixInputDataSet
from featrix.neural.sphere_config import SphereConfig
from featrix.neural.single_predictor import FeatrixSinglePredictor
import asyncio


def run_ablation(use_cls_token: bool, output_dir: Path, es_epochs: int = 25, sp_epochs: int = 25):
    """
    Run a single ablation with either CLS token or mean pooling.

    Args:
        use_cls_token: True for CLS token pooling, False for mean pooling
        output_dir: Directory to save results
        es_epochs: Number of ES training epochs
        sp_epochs: Number of SP training epochs

    Returns:
        dict with AUC and other metrics
    """
    pooling_name = "CLS" if use_cls_token else "MEAN"
    print()
    print("=" * 80)
    print(f"ABLATION: {pooling_name} POOLING")
    print("=" * 80)

    # Load credit-g dataset
    data_file = Path(__file__).resolve().parent.parent.parent.parent.parent.parent / "qa_data" / "credit_g_31.csv"
    if not data_file.exists():
        raise FileNotFoundError(f"Dataset not found: {data_file}")

    input_file = FeatrixInputDataFile(str(data_file))
    df = input_file.df
    print(f"Dataset: {len(df)} rows, {len(df.columns)} columns")

    # Configure sphere with the pooling method (singleton pattern)
    sphere_config = SphereConfig.get_instance()
    sphere_config.set("use_cls_token_pooling", use_cls_token)

    print(f"Pooling method: {'CLS token' if use_cls_token else 'Mean of columns'}")

    # Create output directory for this run
    run_dir = output_dir / pooling_name
    run_dir.mkdir(parents=True, exist_ok=True)

    # Create FeatrixInputDataSet from dataframe
    dataset = FeatrixInputDataSet(df=df, ignore_cols=[], limit_rows=None, encoder_overrides=None)

    # Extract detected column types and set them on the dataset
    detected_types = {}
    for col_name, detector in dataset._detectors.items():
        detected_types[col_name] = detector.get_codec_name()
    dataset.encoderOverrides = detected_types

    # Split into train/val
    train_data, val_data = dataset.split(fraction=0.2)

    # Create embedding space
    es = EmbeddingSpace(
        train_input_data=train_data,
        val_input_data=val_data,
        output_dir=str(run_dir),
    )

    # Train embedding space (disable_recovery=True to prevent loading stale checkpoints)
    print(f"\nTraining ES for {es_epochs} epochs...")
    es.train(n_epochs=es_epochs, disable_recovery=True)

    # ES is unsupervised, no AUC. Get best loss instead.
    es_best_loss = getattr(es, '_best_val_loss', None)
    print(f"ES Best Val Loss: {es_best_loss}")

    # Train single predictor on 'target' column (credit-g binary classification)
    target_column = 'target'
    print(f"\nTraining SP on '{target_column}' for {sp_epochs} epochs...")

    # Create predictor
    sp = FeatrixSinglePredictor(embedding_space=es)

    # Prep for training
    sp.prep_for_training(
        train_df=df,
        target_col_name=target_column,
        target_col_type="set",
        use_class_weights=True,
    )

    # Train predictor
    training_results = asyncio.run(sp.train(n_epochs=sp_epochs))

    # Get SP metrics from LR timeline CSV (most reliable)
    sp_auc = None
    sp_pr_auc = None

    lr_timeline_path = run_dir / "sp_lr_timeline.csv"
    if lr_timeline_path.exists():
        lr_df = pd.read_csv(lr_timeline_path)
        if 'auc' in lr_df.columns:
            sp_auc = lr_df['auc'].max()
        if 'pr_auc' in lr_df.columns:
            sp_pr_auc = lr_df['pr_auc'].max()

    print(f"\nResults for {pooling_name} pooling:")
    print(f"  ES Best Val Loss: {es_best_loss}")
    print(f"  SP ROC-AUC:       {sp_auc}")
    print(f"  SP PR-AUC:        {sp_pr_auc}")

    results = {
        "pooling_method": pooling_name,
        "use_cls_token": use_cls_token,
        "es_epochs": es_epochs,
        "sp_epochs": sp_epochs,
        "es_best_val_loss": es_best_loss,
        "sp_roc_auc": sp_auc,
        "sp_pr_auc": sp_pr_auc,
        "timestamp": datetime.now().isoformat(),
    }

    # Save results
    results_file = run_dir / "results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to {results_file}")

    return results


def main():
    parser = argparse.ArgumentParser(description='CLS vs Mean Pooling Ablation Test')
    parser.add_argument('--es-epochs', type=int, default=25, help='ES training epochs (default: 25)')
    parser.add_argument('--sp-epochs', type=int, default=25, help='SP training epochs (default: 25)')
    parser.add_argument('--output-dir', type=str, default=None, help='Output directory')
    parser.add_argument('--cls-only', action='store_true', help='Only run CLS ablation')
    parser.add_argument('--mean-only', action='store_true', help='Only run Mean ablation')
    args = parser.parse_args()

    print("=" * 80)
    print("CLS TOKEN vs MEAN POOLING ABLATION TEST")
    print("=" * 80)
    print(f"Started: {datetime.now()}")
    print(f"ES epochs: {args.es_epochs}")
    print(f"SP epochs: {args.sp_epochs}")
    print()

    # Set output directory (use /tmp to avoid polluting the QA directory)
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = Path("/tmp") / "cls_vs_mean_ablation" / datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {output_dir}")

    results = []

    # Run CLS token ablation
    if not args.mean_only:
        try:
            cls_results = run_ablation(
                use_cls_token=True,
                output_dir=output_dir,
                es_epochs=args.es_epochs,
                sp_epochs=args.sp_epochs,
            )
            results.append(cls_results)
        except Exception as e:
            print(f"ERROR in CLS ablation: {e}")
            import traceback
            traceback.print_exc()

    # Run Mean pooling ablation
    if not args.cls_only:
        try:
            mean_results = run_ablation(
                use_cls_token=False,
                output_dir=output_dir,
                es_epochs=args.es_epochs,
                sp_epochs=args.sp_epochs,
            )
            results.append(mean_results)
        except Exception as e:
            print(f"ERROR in Mean ablation: {e}")
            import traceback
            traceback.print_exc()

    # Print comparison
    print()
    print("=" * 80)
    print("ABLATION COMPARISON")
    print("=" * 80)

    if len(results) == 2:
        cls_res = results[0]
        mean_res = results[1]

        print(f"{'Metric':<20} {'CLS Token':<15} {'Mean Pool':<15} {'Winner':<10}")
        print("-" * 60)

        for metric in ['sp_roc_auc', 'sp_pr_auc']:
            cls_val = cls_res.get(metric)
            mean_val = mean_res.get(metric)

            if cls_val is not None and mean_val is not None:
                winner = "CLS" if cls_val > mean_val else "MEAN" if mean_val > cls_val else "TIE"
                diff = abs(cls_val - mean_val)
                print(f"{metric:<20} {cls_val:<15.4f} {mean_val:<15.4f} {winner:<10} (diff={diff:.4f})")
            else:
                print(f"{metric:<20} {cls_val or 'N/A':<15} {mean_val or 'N/A':<15}")
    else:
        for res in results:
            print(f"{res['pooling_method']}:")
            print(f"  ES Best Val Loss: {res.get('es_best_val_loss')}")
            print(f"  SP ROC-AUC:       {res.get('sp_roc_auc')}")
            print(f"  SP PR-AUC:        {res.get('sp_pr_auc')}")

    # Save combined results
    combined_file = output_dir / "comparison.json"
    with open(combined_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nCombined results saved to {combined_file}")

    print()
    print(f"Completed: {datetime.now()}")


if __name__ == "__main__":
    main()
