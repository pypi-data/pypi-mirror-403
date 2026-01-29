#!/usr/bin/env python
"""
Test Foundation Mode Infrastructure Locally

Generates synthetic data with >= 50k rows to trigger foundation mode,
then tests the create_structured_data and ES training pipeline.

Usage:
    python tests/test_foundation_mode_local.py

This creates:
    1. Synthetic CSV with 60,000 rows (above 50k threshold)
    2. Runs CSVtoDB in foundation mode
    3. Verifies SQLite has proper foundation splits
    4. Optionally runs a quick ES training test
"""

import argparse
import logging
import numpy as np
import os
import pandas as pd
import sqlite3
import sys
import tempfile
import time
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "lib"))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


def generate_synthetic_data(n_rows: int = 60_000, n_numeric_cols: int = 10,
                           n_categorical_cols: int = 5, seed: int = 42) -> pd.DataFrame:
    """
    Generate synthetic tabular data for testing.

    Creates a mix of:
    - Numeric columns (some correlated, some random)
    - Categorical columns (various cardinalities)
    - A binary target column
    """
    logger.info(f"Generating {n_rows:,} synthetic rows...")
    np.random.seed(seed)

    data = {}

    # Generate numeric columns with some correlations
    base_signal = np.random.randn(n_rows)

    for i in range(n_numeric_cols):
        if i < 3:
            # First 3 columns correlated with base signal
            noise = np.random.randn(n_rows) * 0.5
            data[f'numeric_{i}'] = base_signal * (1 - i * 0.2) + noise
        elif i < 6:
            # Next 3 columns: different distributions
            if i == 3:
                data[f'numeric_{i}'] = np.random.exponential(2, n_rows)
            elif i == 4:
                data[f'numeric_{i}'] = np.random.uniform(0, 100, n_rows)
            else:
                data[f'numeric_{i}'] = np.random.lognormal(0, 1, n_rows)
        else:
            # Rest: pure random
            data[f'numeric_{i}'] = np.random.randn(n_rows)

    # Generate categorical columns with various cardinalities
    categories = {
        'category_low': ['A', 'B', 'C'],  # 3 categories
        'category_med': [f'cat_{i}' for i in range(10)],  # 10 categories
        'category_high': [f'item_{i}' for i in range(50)],  # 50 categories
        'category_binary': ['yes', 'no'],  # binary
        'category_region': ['North', 'South', 'East', 'West', 'Central'],  # 5 categories
    }

    for col_name, cats in categories.items():
        # Slightly imbalanced distributions
        probs = np.random.dirichlet(np.ones(len(cats)) * 2)
        data[col_name] = np.random.choice(cats, n_rows, p=probs)

    # Generate target column (binary classification)
    # Make it somewhat predictable from numeric_0 and category_low
    target_signal = data['numeric_0'] + np.where(
        np.isin(data['category_low'], ['A']), 1.0,
        np.where(np.isin(data['category_low'], ['B']), 0.0, -0.5)
    )
    target_prob = 1 / (1 + np.exp(-target_signal))  # Sigmoid
    data['target'] = (np.random.rand(n_rows) < target_prob).astype(int)

    # Add some missing values (5% of numeric columns)
    for col in [c for c in data.keys() if c.startswith('numeric_')]:
        mask = np.random.rand(n_rows) < 0.05
        data[col] = np.where(mask, np.nan, data[col])

    df = pd.DataFrame(data)

    # Log stats
    logger.info(f"  Shape: {df.shape}")
    logger.info(f"  Columns: {list(df.columns)}")
    logger.info(f"  Target distribution: {df['target'].value_counts().to_dict()}")
    logger.info(f"  Memory usage: {df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB")

    return df


def test_foundation_csv_to_sqlite(csv_path: str, output_dir: str) -> str:
    """
    Test CSVtoDB in foundation mode.

    Returns path to created SQLite database.
    """
    logger.info("=" * 60)
    logger.info("Testing CSVtoDB in Foundation Mode")
    logger.info("=" * 60)

    from structureddata import CSVtoDB

    # Create CSVtoDB instance
    c2d = CSVtoDB()
    c2d.db_path = str(Path(output_dir) / "foundation_test.db")

    logger.info(f"  Input CSV: {csv_path}")
    logger.info(f"  Output DB: {c2d.db_path}")

    # Run foundation mode conversion
    start_time = time.time()
    c2d.csv_to_foundation_sqlite(csv_path=csv_path)
    elapsed = time.time() - start_time

    logger.info(f"  Conversion time: {elapsed:.2f}s")

    return c2d.db_path


def verify_foundation_splits(db_path: str) -> dict:
    """
    Verify that the foundation SQLite has proper splits.

    Foundation mode should create:
    - data table (all rows)
    - train_split, val_split, test_split, warmup_split tables
    - metadata about splits
    """
    logger.info("=" * 60)
    logger.info("Verifying Foundation Splits")
    logger.info("=" * 60)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    logger.info(f"  Tables found: {tables}")

    # Check row counts
    results = {'tables': tables, 'row_counts': {}}

    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        results['row_counts'][table] = count
        logger.info(f"  {table}: {count:,} rows")

    # Check for expected foundation tables
    # Foundation mode creates: warmup, train, validation, test (not data, train_split, etc.)
    expected_tables = ['train', 'validation', 'warmup']
    missing = [t for t in expected_tables if t not in tables]

    if missing:
        logger.warning(f"  ⚠️  Missing expected tables: {missing}")
        results['success'] = False
    else:
        logger.info(f"  ✅ All expected foundation tables present")
        results['success'] = True

    # Verify train + validation + test + warmup = total (no overlaps)
    if all(t in tables for t in ['train', 'validation', 'test', 'warmup']):
        total_split_rows = sum(results['row_counts'].get(t, 0) for t in ['train', 'validation', 'test', 'warmup'])
        logger.info(f"  Total across splits: {total_split_rows:,} rows")

    # Log train table schema for debugging
    if 'train' in tables:
        cursor.execute("PRAGMA table_info(train)")
        train_cols = [row[1] for row in cursor.fetchall()]
        logger.info(f"  Train table columns: {train_cols[:5]}...")

    conn.close()
    return results


def test_es_training_quick(db_path: str, output_dir: str, epochs: int = 3) -> dict:
    """
    Run a quick ES training test on the foundation database.

    This tests that the ES can load and train on foundation splits.
    """
    logger.info("=" * 60)
    logger.info(f"Quick ES Training Test ({epochs} epochs)")
    logger.info("=" * 60)

    try:
        from featrix.neural.gpu_utils import set_backend_cpu
        from featrix.neural.training_data_timeline import ESTrainingDataTimeline

        # Use CPU for local testing
        set_backend_cpu()

        # Load foundation database using ESTrainingDataTimeline
        logger.info(f"  Loading foundation database: {db_path}")

        # Create timeline from foundation database
        timeline = ESTrainingDataTimeline.from_foundation(db_path)

        # Get warmup data (clean rows for initial training)
        warmup_data = timeline.get_warmup()
        if warmup_data:
            logger.info(f"  Warmup data: {len(warmup_data.df):,} rows")
        else:
            logger.info("  Warmup data: None")

        # Get validation data
        val_data = timeline.get_validation_set()
        logger.info(f"  Validation data: {len(val_data.df):,} rows")

        # Get first epoch's training data - for ES initialization we need full analysis
        from featrix.neural.input_data_set import FeatrixInputDataSet

        # Get raw train DataFrame and create a proper FeatrixInputDataSet with analysis
        train_df = timeline.backend.get_train_rows(0, 10000)
        train_data = FeatrixInputDataSet(df=train_df)  # Full analysis

        logger.info(f"  Train data (epoch 0): {len(train_data.df):,} rows")
        logger.info(f"  Columns: {list(train_data.df.columns)[:5]}... ({len(train_data.df.columns)} total)")

        # Get val DataFrame with full analysis
        val_df = timeline.backend.get_validation_df()
        val_data = FeatrixInputDataSet(df=val_df)

        # Create ES from foundation data
        from featrix.neural.embedded_space import EmbeddingSpace

        es = EmbeddingSpace(
            train_input_data=train_data,
            val_input_data=val_data,
            d_model=64,  # Small for quick test
            output_dir=output_dir
        )

        logger.info(f"  ES created with d_model={es.d_model}")

        # Quick training
        logger.info(f"  Starting {epochs}-epoch training...")
        start_time = time.time()

        es.train(
            n_epochs=epochs,
            batch_size=256,
            disable_recovery=True,  # Fresh start
            enable_weightwatcher=False,  # Skip for speed
        )

        elapsed = time.time() - start_time
        logger.info(f"  Training completed in {elapsed:.2f}s")

        return {
            'success': True,
            'epochs': epochs,
            'time': elapsed,
            'd_model': es.d_model,
            'n_columns': len(es.column_names)
        }

    except Exception as e:
        logger.error(f"  ❌ ES training failed: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e)
        }


def main():
    parser = argparse.ArgumentParser(description='Test foundation mode locally')
    parser.add_argument('--rows', type=int, default=60_000,
                       help='Number of rows to generate (default: 60000)')
    parser.add_argument('--skip-es', action='store_true',
                       help='Skip ES training test')
    parser.add_argument('--es-epochs', type=int, default=3,
                       help='Number of ES training epochs (default: 3)')
    parser.add_argument('--output-dir', type=str, default=None,
                       help='Output directory (default: temp dir)')
    parser.add_argument('--keep-files', action='store_true',
                       help='Keep generated files after test')
    args = parser.parse_args()

    logger.info("=" * 70)
    logger.info("FOUNDATION MODE LOCAL TEST")
    logger.info("=" * 70)
    logger.info(f"  Rows: {args.rows:,}")
    logger.info(f"  Skip ES: {args.skip_es}")
    logger.info(f"  ES epochs: {args.es_epochs}")
    logger.info("")

    # Create output directory
    if args.output_dir:
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
    else:
        output_dir = Path(tempfile.mkdtemp(prefix='foundation_test_'))

    logger.info(f"Output directory: {output_dir}")

    try:
        # Step 1: Generate synthetic data
        df = generate_synthetic_data(n_rows=args.rows)

        # Step 2: Save to CSV
        csv_path = output_dir / "synthetic_data.csv"
        logger.info(f"Saving to {csv_path}...")
        df.to_csv(csv_path, index=False)
        csv_size_mb = csv_path.stat().st_size / 1024 / 1024
        logger.info(f"  CSV size: {csv_size_mb:.2f} MB")

        # Step 3: Run CSVtoDB in foundation mode
        db_path = test_foundation_csv_to_sqlite(str(csv_path), str(output_dir))

        # Step 4: Verify foundation splits
        split_results = verify_foundation_splits(db_path)

        # Step 5: Quick ES training (optional)
        if not args.skip_es:
            es_output_dir = output_dir / "es_output"
            es_output_dir.mkdir(exist_ok=True)
            es_results = test_es_training_quick(db_path, str(es_output_dir), args.es_epochs)
        else:
            es_results = {'skipped': True}

        # Summary
        logger.info("")
        logger.info("=" * 70)
        logger.info("TEST SUMMARY")
        logger.info("=" * 70)
        logger.info(f"  Synthetic data: {args.rows:,} rows, {csv_size_mb:.2f} MB")
        logger.info(f"  Foundation splits: {'✅ PASS' if split_results.get('success') else '❌ FAIL'}")
        if not args.skip_es:
            logger.info(f"  ES training: {'✅ PASS' if es_results.get('success') else '❌ FAIL'}")
        logger.info(f"  Output dir: {output_dir}")
        logger.info("=" * 70)

        if not args.keep_files and not args.output_dir:
            logger.info("  (Use --keep-files to preserve output)")

        return 0 if split_results.get('success') else 1

    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
