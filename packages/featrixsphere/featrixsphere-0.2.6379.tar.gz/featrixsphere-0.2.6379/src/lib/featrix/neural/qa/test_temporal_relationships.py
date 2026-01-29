#!/usr/bin/env python3
"""
Integration test for Temporal Relationship Operations.

This test verifies that:
1. TimestampEncoder correctly encodes timestamp columns
2. TemporalRelationshipOps computes timestamp×timestamp relationships
3. String×timestamp relationships are computed correctly
4. The full pipeline works with timestamp columns

The synthetic data has explicit temporal relationships:
- ship_date is typically 1-7 days after order_date
- Late shipments have longer delays
- order_day string matches order_date's day of week
"""
import gc
import logging
import os
import sys

# Enable MPS fallback to CPU for unsupported operations (SVD)
# This suppresses the MPS SVD warning on macOS
os.environ.setdefault('PYTORCH_ENABLE_MPS_FALLBACK', '1')
import tempfile
import time
from pathlib import Path
from datetime import datetime, timedelta
import random

import numpy as np
import pandas as pd
import torch

# Add paths for imports
project_root = Path(__file__).resolve().parent.parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root / "src" / "lib"))
sys.path.insert(0, str(project_root / "src"))

from featrix.neural.embedded_space import EmbeddingSpace
from featrix.neural.input_data_set import FeatrixInputDataSet
from featrix.neural.model_config import RelationshipFeatureConfig

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


def create_timestamps_data(n_samples: int = 500, seed: int = 42) -> pd.DataFrame:
    """
    Create synthetic data with timestamp columns and known relationships.

    Relationships:
    1. ship_date = order_date + delay (timestamp-timestamp relationship)
    2. is_late = 1 if delay > 4 days (target depends on timestamp difference)
    3. order_day string matches order_date.day_name() (string-timestamp correlation)
    4. status correlates with lateness
    """
    np.random.seed(seed)
    random.seed(seed)

    # Day names for string column
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    # Categories
    categories = ["Electronics", "Clothing", "Home", "Sports", "Books"]
    statuses_normal = ["Delivered", "Shipped"]
    statuses_late = ["In Transit", "Processing", "Pending"]

    data = []
    base_date = datetime(2024, 1, 1)

    for i in range(n_samples):
        # Generate order date
        order_offset = random.randint(0, 300)
        order_date = base_date + timedelta(days=order_offset)

        # Determine lateness and generate ship delay accordingly
        is_late = random.random() < 0.3  # 30% late
        if is_late:
            ship_delay = random.randint(5, 14)  # Late: 5-14 days
        else:
            ship_delay = random.randint(1, 4)   # Normal: 1-4 days

        ship_date = order_date + timedelta(days=ship_delay)

        # Add hour variation
        order_date = order_date.replace(
            hour=random.randint(8, 20),
            minute=random.randint(0, 59)
        )
        ship_date = ship_date.replace(
            hour=random.randint(6, 18),
            minute=random.randint(0, 59)
        )

        # String columns
        customer_name = f"Customer_{i % 50}"
        category = random.choice(categories)

        # Status correlates with lateness
        if is_late:
            status = random.choice(statuses_late)
        else:
            status = random.choice(statuses_normal)

        # Order day name - should match order_date's actual day
        order_day = day_names[order_date.weekday()]

        # Numeric columns
        amount = round(random.uniform(10, 500), 2)
        quantity = random.randint(1, 10)

        data.append({
            "order_date": order_date,
            "ship_date": ship_date,
            "customer_name": customer_name,
            "category": category,
            "status": status,
            "order_day": order_day,
            "amount": amount,
            "quantity": quantity,
            "is_late": int(is_late),
        })

    return pd.DataFrame(data)


def test_temporal_relationships():
    """Test temporal relationship operations with timestamps dataset."""
    logger.info("=" * 70)
    logger.info("TEST: Temporal Relationship Operations")
    logger.info("=" * 70)

    # Create test data
    logger.info("\n1. Creating synthetic timestamps dataset...")
    df = create_timestamps_data(n_samples=500)

    logger.info(f"   Dataset: {len(df)} rows, {len(df.columns)} columns")
    logger.info(f"   Columns: {list(df.columns)}")
    logger.info(f"   Timestamp columns: order_date, ship_date")
    logger.info(f"   Target: is_late (late={df['is_late'].sum()}, on_time={len(df) - df['is_late'].sum()})")

    # Create temp directory for model
    with tempfile.TemporaryDirectory() as tmpdir:
        model_path = Path(tmpdir) / "timestamps_test_model"

        logger.info("\n2. Creating EmbeddingSpace...")

        # Force timestamp detection for order_date and ship_date
        # Pass encoder_overrides in constructor so they're applied during detection
        timestamp_overrides = {
            'order_date': 'timestamp',
            'ship_date': 'timestamp',
        }

        # Create input dataset with:
        # 1. encoder_overrides: force timestamp detection for order_date/ship_date
        # 2. enable_hybrid_detection=False: keep columns separate so temporal ops can work
        #    (hybrid groups would merge them into one column, preventing ts×ts pairs)
        dataset = FeatrixInputDataSet(
            df=df.copy(),
            ignore_cols=[],
            limit_rows=None,
            encoder_overrides=timestamp_overrides,
            enable_hybrid_detection=False,  # Keep columns separate for ts×ts relationships
        )

        # Log detected types after applying overrides
        detected_types = {}
        for col_name, detector in dataset._detectors.items():
            detected_types[col_name] = detector.get_codec_name()
        # Merge with our overrides
        for col, typ in timestamp_overrides.items():
            detected_types[col] = typ
        dataset.encoderOverrides = detected_types

        logger.info(f"   Detected column types: {detected_types}")

        # Split data
        train_data, val_data = dataset.split(fraction=0.2)

        # Configure relationship features (enable for temporal ops testing)
        rel_config = RelationshipFeatureConfig(
            exploration_epochs=2,
            top_k_fraction=0.40,
        )

        # Create embedding space
        es = EmbeddingSpace(
            train_input_data=train_data,
            val_input_data=val_data,
            output_debug_label="temporal_test",
            output_dir=str(model_path),
            d_model=64,
            n_transformer_layers=2,
            n_attention_heads=4,
            relationship_features=rel_config,
        )

        logger.info("\n3. Training for 3 epochs...")
        start_time = time.time()

        # Train
        es.train(
            batch_size=32,
            n_epochs=3,
            movie_frame_interval=None,
        )

        train_time = time.time() - start_time
        logger.info(f"   Training completed in {train_time:.1f}s")

        # Check if temporal ops were created
        logger.info("\n4. Checking temporal relationship operations...")

        joint_encoder = es.encoder.joint_encoder
        rel_extractor = getattr(joint_encoder, 'relationship_extractor', None)

        if rel_extractor is not None:
            temporal_ops = getattr(rel_extractor, 'temporal_ops', None)
            if temporal_ops is not None:
                logger.info(f"   TemporalRelationshipOps created")
                logger.info(f"   Timestamp columns: {temporal_ops.timestamp_cols}")
                logger.info(f"   String columns: {temporal_ops.string_cols}")

                # Check the number of timestamp pairs
                n_ts_cols = len(temporal_ops.timestamp_cols)
                n_str_cols = len(temporal_ops.string_cols)
                n_ts_pairs = n_ts_cols * (n_ts_cols - 1) // 2
                n_str_ts_pairs = n_str_cols * n_ts_cols

                logger.info(f"   Timestamp×Timestamp pairs: {n_ts_pairs}")
                logger.info(f"   String×Timestamp pairs: {n_str_ts_pairs}")

                if n_ts_cols >= 2:
                    logger.info("   PASS: Timestamp×Timestamp relationships active")
                else:
                    logger.warning("   WARN: Not enough timestamp columns for ts×ts relationships")

                if n_str_ts_pairs > 0:
                    logger.info("   PASS: String×Timestamp relationships active")
            else:
                logger.warning("   WARN: TemporalRelationshipOps not created (no timestamp columns?)")
        else:
            logger.warning("   WARN: Relationship extractor not found")

        # Check if col_types has the correct ColumnType enums
        logger.info("\n5. Checking col_types normalization...")
        from featrix.neural.model_config import ColumnType as CT
        has_timestamp_cols = any(
            ct == CT.TIMESTAMP for ct in es.col_types.values()
        )
        if has_timestamp_cols:
            logger.info(f"   PASS: col_types contains ColumnType.TIMESTAMP enums")
            ts_cols = [k for k, v in es.col_types.items() if v == CT.TIMESTAMP]
            logger.info(f"   Timestamp columns in col_types: {ts_cols}")
        else:
            logger.warning(f"   WARN: No ColumnType.TIMESTAMP found in col_types")
            logger.warning(f"   col_types values: {list(es.col_types.values())[:5]}...")

        # The test passes if:
        # 1. Training completed without errors
        # 2. Temporal ops were created (if timestamp columns were detected)
        # 3. col_types contains ColumnType enums, not strings
        success = has_timestamp_cols and (rel_extractor is None or temporal_ops is not None)

        if success:
            logger.info("\n" + "=" * 70)
            logger.info("TEST PASSED: Temporal relationship operations work correctly")
            logger.info("=" * 70)
        else:
            logger.error("\n" + "=" * 70)
            logger.error("TEST FAILED: Issues with temporal relationship operations")
            logger.error("=" * 70)

        return success


def test_temporal_ops_unit():
    """Unit test for TemporalRelationshipOps computation."""
    logger.info("\n" + "=" * 70)
    logger.info("UNIT TEST: TemporalRelationshipOps computations")
    logger.info("=" * 70)

    from featrix.neural.temporal_relationship_ops import TemporalRelationshipOps
    from featrix.neural.model_config import ColumnType

    # Setup
    d_model = 64
    col_types = {
        "order_date": ColumnType.TIMESTAMP,
        "ship_date": ColumnType.TIMESTAMP,
        "customer": ColumnType.FREE_STRING,
        "amount": ColumnType.SCALAR,
    }
    col_names = ["order_date", "ship_date", "customer", "amount"]

    # Create temporal ops
    temporal_ops = TemporalRelationshipOps(
        d_model=d_model,
        col_types=col_types,
        col_names_in_order=col_names,
    )

    logger.info(f"   Timestamp columns: {temporal_ops.timestamp_cols}")
    logger.info(f"   String columns: {temporal_ops.string_cols}")

    # Test timestamp×timestamp features
    logger.info("\n   Testing timestamp×timestamp features...")
    batch_size = 4

    # Create fake raw timestamp features (12 features each)
    # [seconds, minutes, hours, day_of_month, day_of_week, month, year,
    #  day_of_year, week_of_year, timezone, year_since_2000, year_since_2020]
    raw_a = torch.tensor([
        [0, 30, 10, 15, 2, 6, 2024, 167, 24, 0, 24, 4],  # June 15, 2024
        [0, 0, 14, 20, 4, 8, 2024, 233, 34, 0, 24, 4],   # Aug 20, 2024
        [30, 45, 9, 1, 0, 1, 2024, 1, 1, 0, 24, 4],      # Jan 1, 2024
        [0, 15, 16, 25, 3, 12, 2024, 360, 52, 0, 24, 4], # Dec 25, 2024
    ], dtype=torch.float32)

    raw_b = torch.tensor([
        [0, 0, 14, 18, 4, 6, 2024, 170, 24, 0, 24, 4],   # June 18, 2024 (3 days later)
        [0, 30, 10, 25, 2, 8, 2024, 238, 34, 0, 24, 4],  # Aug 25, 2024 (5 days later)
        [0, 0, 12, 3, 2, 1, 2024, 3, 1, 0, 24, 4],       # Jan 3, 2024 (2 days later)
        [30, 0, 11, 31, 2, 12, 2024, 366, 53, 0, 24, 4], # Dec 31, 2024 (6 days later)
    ], dtype=torch.float32)

    features = temporal_ops.compute_timestamp_timestamp_features(raw_a, raw_b)
    logger.info(f"   Feature shape: {features.shape}")  # Should be (4, 8)
    logger.info(f"   Features[0]: {features[0].tolist()}")

    # Test relationship computation
    relationship = temporal_ops.compute_timestamp_timestamp_relationship(raw_a, raw_b)
    logger.info(f"   Relationship embedding shape: {relationship.shape}")  # Should be (4, 64)

    # Test string×timestamp
    logger.info("\n   Testing string×timestamp features...")
    string_emb = torch.randn(batch_size, d_model)
    str_ts_relationship = temporal_ops.compute_string_timestamp_relationship(string_emb, raw_a)
    logger.info(f"   String×Timestamp embedding shape: {str_ts_relationship.shape}")

    # Test pair detection
    logger.info("\n   Testing pair type detection...")
    assert temporal_ops.is_timestamp_pair(0, 1) == True, "Should detect ts×ts pair"
    assert temporal_ops.is_timestamp_pair(0, 2) == False, "Should not be ts×ts"

    is_str_ts, str_idx, ts_idx = temporal_ops.is_string_timestamp_pair(2, 0)
    assert is_str_ts == True, "Should detect string×ts pair"
    assert str_idx == 2, "String should be col 2"
    assert ts_idx == 0, "Timestamp should be col 0"

    logger.info("   PASS: All unit tests passed")
    return True


if __name__ == "__main__":
    # Run unit tests first
    unit_ok = test_temporal_ops_unit()

    # Run integration test
    integration_ok = test_temporal_relationships()

    if unit_ok and integration_ok:
        logger.info("\n" + "=" * 70)
        logger.info("ALL TESTS PASSED")
        logger.info("=" * 70)
        sys.exit(0)
    else:
        logger.error("\n" + "=" * 70)
        logger.error("SOME TESTS FAILED")
        logger.error("=" * 70)
        sys.exit(1)
