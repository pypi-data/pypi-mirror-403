#  -*- coding: utf-8 -*-
#
#  Copyright Featrix, Inc 2023-2025
#
#  Proprietary and Confidential.  Unauthorized use, copying or dissemination
#  of these materials is strictly prohibited.
#
"""
FeatrixFoundationInputData - Process large datasets for foundation model training.

This module handles the ingestion and preprocessing of large parquet files
(typically > 100,000 rows) for foundation model training. It creates a
SQLite database with proper splits and metadata for efficient training.

Usage:
    # Create foundation database from parquet file
    foundation = FeatrixFoundationInputData(
        input_path="/path/to/large_data.parquet",
        output_path="/path/to/foundation.sqlite",
    )
    foundation.build()

    # Then use with ESTrainingDataTimeline
    timeline = ESTrainingDataTimeline.from_foundation("/path/to/foundation.sqlite")

SQLite Schema:
    - metadata: Key-value pairs for dataset info
    - column_types: Detected types for each column
    - json_schemas: Schemas for columns containing JSON
    - warmup: 5% clean rows (<10% nulls) for initial training
    - train: 80% of data for main training
    - validation: 10% of data for validation
    - test: 5% of data for holdout testing
"""
from __future__ import annotations

import json
import logging
import math
import os
import random
import sqlite3
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import numpy as np
import pandas as pd

from featrix.neural.logging_config import configure_logging
configure_logging()

logger = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

FOUNDATION_MIN_ROWS = 100_000  # Warn if fewer rows
TYPE_DETECTION_SAMPLE_SIZE = 50_000  # Sample size for type detection
DEFAULT_MIN_FILL_RATE = 0.40  # Rows with >= 60% nulls are filtered
WARMUP_MAX_NULL_RATE = 0.10  # Warmup rows must have < 10% nulls
WARN_NULL_RATE = 0.80  # Warn about columns with >= 80% nulls


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class ColumnStats:
    """Statistics for a single column."""
    name: str
    detected_type: str
    null_count: int
    null_rate: float
    unique_count: int
    sample_values: List[Any] = field(default_factory=list)
    is_json: bool = False
    json_schema: Optional[Dict] = None


@dataclass
class FoundationStats:
    """Statistics for the entire foundation dataset."""
    total_rows: int
    total_columns: int
    filtered_rows: int
    warmup_rows: int
    train_rows: int
    val_rows: int
    test_rows: int
    high_null_columns: List[str]  # Columns with >= 80% nulls
    json_columns: List[str]
    created_at: str
    processing_time_seconds: float


# =============================================================================
# JSON Schema Inference
# =============================================================================

def infer_json_schema(values: List[Any], max_samples: int = 1000, max_histogram_items: int = 50) -> Dict:
    """
    Infer a detailed schema from a list of JSON values.

    Returns a schema dict with:
    - type: "object", "array", "string", "number", "boolean", "null", "mixed"
    - frequency: How often each type appears
    - type_distribution: Count of each type

    For arrays:
    - item_type: Dominant type of items in arrays
    - item_schema: If items are objects, their property schema
    - value_histogram: Most common values (for string/number items)
    - arrangement_histogram: Most common combinations of values

    For objects:
    - properties: Schema for each property key
    - value_histograms: Most common values for each property
    """
    if not values:
        return {"type": "null", "frequency": 0}

    # Sample if too many
    if len(values) > max_samples:
        values = random.sample(values, max_samples)

    type_counts = Counter()

    # For top-level objects
    property_schemas = defaultdict(lambda: defaultdict(int))
    property_values = defaultdict(Counter)

    # For arrays
    array_item_types = Counter()
    array_item_values = Counter()  # For string/number items
    array_item_object_schemas = defaultdict(lambda: defaultdict(int))  # For object items
    array_item_object_values = defaultdict(Counter)  # Values within object items
    arrangement_counter = Counter()  # Combinations of values in arrays

    for val in values:
        if val is None:
            type_counts["null"] += 1
        elif isinstance(val, bool):
            type_counts["boolean"] += 1
        elif isinstance(val, (int, float)):
            type_counts["number"] += 1
        elif isinstance(val, str):
            type_counts["string"] += 1
        elif isinstance(val, dict):
            type_counts["object"] += 1
            for k, v in val.items():
                v_type = _get_simple_type(v)
                property_schemas[k][v_type] += 1
                # Track values for strings/numbers
                if isinstance(v, (str, int, float, bool)) and v is not None:
                    property_values[k][v] += 1
        elif isinstance(val, list):
            type_counts["array"] += 1
            _analyze_array(
                val,
                array_item_types,
                array_item_values,
                array_item_object_schemas,
                array_item_object_values,
                arrangement_counter,
            )

    total = len(values)

    # Determine dominant type
    if not type_counts:
        return {"type": "null", "frequency": 0}

    dominant_type, count = type_counts.most_common(1)[0]

    schema = {
        "type": dominant_type if count / total > 0.8 else "mixed",
        "frequency": total,
        "type_distribution": dict(type_counts),
    }

    # Object schema with value histograms
    if dominant_type == "object" and property_schemas:
        schema["properties"] = {}
        for k, type_counts_for_prop in property_schemas.items():
            prop_schema = {
                "types": dict(type_counts_for_prop),
                "frequency": sum(type_counts_for_prop.values()),
            }
            # Add value histogram if we have values
            if k in property_values and property_values[k]:
                prop_schema["value_histogram"] = dict(property_values[k].most_common(max_histogram_items))
            schema["properties"][k] = prop_schema

    # Array schema with detailed item analysis
    if dominant_type == "array" and array_item_types:
        dominant_item_type = array_item_types.most_common(1)[0][0] if array_item_types else "unknown"

        schema["item_type"] = dominant_item_type
        schema["item_type_distribution"] = dict(array_item_types)

        # Value histogram for string/number array items
        if array_item_values:
            schema["value_histogram"] = dict(array_item_values.most_common(max_histogram_items))

        # Object schema for object array items
        if dominant_item_type == "object" and array_item_object_schemas:
            schema["item_schema"] = {
                "properties": {}
            }
            for k, type_counts_for_prop in array_item_object_schemas.items():
                prop_schema = {
                    "types": dict(type_counts_for_prop),
                    "frequency": sum(type_counts_for_prop.values()),
                }
                if k in array_item_object_values and array_item_object_values[k]:
                    prop_schema["value_histogram"] = dict(
                        array_item_object_values[k].most_common(max_histogram_items)
                    )
                schema["item_schema"]["properties"][k] = prop_schema

        # Arrangement histogram - what combinations appear together
        # Convert tuple keys to JSON-serializable strings
        if arrangement_counter:
            schema["arrangement_histogram"] = {
                json.dumps(list(k)): v
                for k, v in arrangement_counter.most_common(max_histogram_items)
            }

    return schema


def _analyze_array(
    arr: List,
    item_types: Counter,
    item_values: Counter,
    item_object_schemas: Dict,
    item_object_values: Dict,
    arrangement_counter: Counter,
    max_items_per_array: int = 50,
):
    """Analyze contents of a single array."""
    # Track items in this array for arrangement
    arrangement_items = []

    for item in arr[:max_items_per_array]:
        item_type = _get_simple_type(item)
        item_types[item_type] += 1

        if isinstance(item, str):
            item_values[item] += 1
            arrangement_items.append(item)
        elif isinstance(item, (int, float)) and not isinstance(item, bool):
            item_values[item] += 1
            arrangement_items.append(str(item))
        elif isinstance(item, bool):
            item_values[str(item).lower()] += 1
            arrangement_items.append(str(item).lower())
        elif isinstance(item, dict):
            # Track object schema and values
            for k, v in item.items():
                v_type = _get_simple_type(v)
                item_object_schemas[k][v_type] += 1
                if isinstance(v, (str, int, float, bool)) and v is not None:
                    item_object_values[k][v] += 1
            # For arrangement, use a canonical representation of the object
            arrangement_items.append(_canonicalize_object(item))

    # Record the arrangement (sorted for consistency)
    if arrangement_items:
        # Sort for canonical ordering
        arrangement_key = tuple(sorted(arrangement_items))
        arrangement_counter[arrangement_key] += 1


def _canonicalize_object(obj: Dict) -> str:
    """Create a canonical string representation of an object for arrangement tracking."""
    # Sort keys and create a simple representation
    parts = []
    for k in sorted(obj.keys()):
        v = obj[k]
        if isinstance(v, (str, int, float, bool)):
            parts.append(f"{k}={v}")
        elif v is None:
            parts.append(f"{k}=null")
        else:
            parts.append(f"{k}=<{_get_simple_type(v)}>")
    return "{" + ",".join(parts) + "}"


def _get_simple_type(val: Any) -> str:
    """Get a simple type string for a value."""
    if val is None:
        return "null"
    if isinstance(val, bool):
        return "boolean"
    if isinstance(val, (int, float)):
        return "number"
    if isinstance(val, str):
        return "string"
    if isinstance(val, dict):
        return "object"
    if isinstance(val, list):
        return "array"
    return "unknown"


def is_json_column(series: pd.Series, sample_size: int = 100) -> bool:
    """
    Check if a column contains JSON data.

    Returns True if > 50% of non-null values are valid JSON objects/arrays.
    """
    non_null = series.dropna()
    if len(non_null) == 0:
        return False

    sample = non_null.sample(min(sample_size, len(non_null)))
    json_count = 0

    for val in sample:
        if isinstance(val, (dict, list)):
            json_count += 1
        elif isinstance(val, str):
            try:
                parsed = json.loads(val)
                if isinstance(parsed, (dict, list)):
                    json_count += 1
            except (json.JSONDecodeError, TypeError):
                pass

    return json_count / len(sample) > 0.5


# =============================================================================
# Type Detection
# =============================================================================

# Import the canonical type detection from detect.py
from featrix.neural.detect import detect_column_type as _detect_column_type


def detect_column_type(series: pd.Series, name: str) -> str:
    """
    Detect the Featrix encoder type for a column.

    Returns one of: "scalar", "set", "timestamp", "free_string", "email",
    "url", "domain_name", "json", "vector"

    Note: "vector" is only returned for columns ending in "_embedding" -
    vector detection must otherwise be manually specified.
    """
    # Check for embedding columns (must be manually specified, but we can
    # detect the common naming convention)
    if name.endswith("_embedding"):
        return "vector"

    # Use the canonical detection logic from detect.py
    return _detect_column_type(series, name)


# =============================================================================
# FeatrixFoundationInputData
# =============================================================================

class FeatrixFoundationInputData:
    """
    Process large datasets for foundation model training.

    Creates a SQLite database with:
    - Filtered data (removes rows with too many nulls)
    - Shuffled and split into warmup/train/val/test
    - Column type metadata
    - JSON schema analysis

    Args:
        input_path: Path to input parquet/csv file, or a DataFrame
        output_path: Path for output SQLite database
        min_fill_rate: Minimum fill rate (1 - null_rate) for rows
        warmup_fraction: Fraction for warmup set (clean rows)
        train_fraction: Fraction for training set
        val_fraction: Fraction for validation set
        test_fraction: Fraction for test set
        random_seed: Seed for reproducibility
    """

    def __init__(
        self,
        input_path: Union[str, Path, pd.DataFrame],
        output_path: Union[str, Path],
        min_fill_rate: float = DEFAULT_MIN_FILL_RATE,
        warmup_fraction: float = 0.05,
        train_fraction: float = 0.80,
        val_fraction: float = 0.10,
        test_fraction: float = 0.05,
        random_seed: int = 42,
    ):
        self.output_path = Path(output_path)
        self.min_fill_rate = min_fill_rate
        self.warmup_fraction = warmup_fraction
        self.train_fraction = train_fraction
        self.val_fraction = val_fraction
        self.test_fraction = test_fraction
        self.random_seed = random_seed

        # Validate fractions
        total = warmup_fraction + train_fraction + val_fraction + test_fraction
        if not (0.99 <= total <= 1.01):
            raise ValueError(
                f"Fractions must sum to 1.0, got {total:.3f} "
                f"(warmup={warmup_fraction}, train={train_fraction}, "
                f"val={val_fraction}, test={test_fraction})"
            )

        # Load data
        if isinstance(input_path, pd.DataFrame):
            self.input_path = None
            self._df = input_path
            logger.info(f"📊 Using provided DataFrame: {len(self._df):,} rows x {len(self._df.columns)} columns")
        else:
            self.input_path = Path(input_path)
            self._df = None
            logger.info(f"📁 Will load from: {self.input_path}")

        # Results
        self.column_stats: Dict[str, ColumnStats] = {}
        self.foundation_stats: Optional[FoundationStats] = None

    def _load_data(self) -> pd.DataFrame:
        """Load data from file if not already loaded."""
        if self._df is not None:
            return self._df

        logger.info(f"📖 Loading data from {self.input_path}...")

        ext = self.input_path.suffix.lower()
        if ext == ".parquet":
            self._df = pd.read_parquet(self.input_path)
        elif ext in (".csv", ".gz"):
            self._df = pd.read_csv(self.input_path)
        elif ext == ".json" or ext == ".jsonl":
            self._df = pd.read_json(self.input_path, lines=ext == ".jsonl")
        else:
            # Try parquet first, then CSV
            try:
                self._df = pd.read_parquet(self.input_path)
            except Exception:
                self._df = pd.read_csv(self.input_path)

        logger.info(f"✅ Loaded {len(self._df):,} rows x {len(self._df.columns)} columns")
        return self._df

    def build(self) -> Path:
        """
        Build the foundation SQLite database.

        Returns the path to the created database.
        """
        start_time = datetime.now()

        logger.info("=" * 80)
        logger.info("🏛️  BUILDING FOUNDATION DATABASE")
        logger.info("=" * 80)

        # Load data
        df = self._load_data()
        original_rows = len(df)
        n_cols = len(df.columns)

        # Warn if small dataset
        if original_rows < FOUNDATION_MIN_ROWS:
            logger.warning(
                f"⚠️  Dataset has only {original_rows:,} rows. "
                f"Foundation training is designed for datasets >= {FOUNDATION_MIN_ROWS:,} rows."
            )

        # Step 1: Analyze columns and filter rows
        logger.info("")
        logger.info("📊 Step 1: Analyzing columns and filtering rows...")
        df, high_null_cols = self._filter_rows(df)
        filtered_rows = original_rows - len(df)

        # Step 2: Detect column types on sample
        logger.info("")
        logger.info("🔍 Step 2: Detecting column types...")
        self._detect_types(df)

        # Step 3: Shuffle and split
        logger.info("")
        logger.info("🔀 Step 3: Shuffling and splitting data...")
        splits = self._create_splits(df)

        # Step 4: Create SQLite database
        logger.info("")
        logger.info("💾 Step 4: Creating SQLite database...")
        self._create_sqlite(splits)

        # Calculate stats
        processing_time = (datetime.now() - start_time).total_seconds()

        json_columns = [
            name for name, stats in self.column_stats.items()
            if stats.is_json
        ]

        self.foundation_stats = FoundationStats(
            total_rows=original_rows,
            total_columns=n_cols,
            filtered_rows=filtered_rows,
            warmup_rows=len(splits["warmup"]),
            train_rows=len(splits["train"]),
            val_rows=len(splits["validation"]),
            test_rows=len(splits["test"]),
            high_null_columns=high_null_cols,
            json_columns=json_columns,
            created_at=datetime.now().isoformat(),
            processing_time_seconds=processing_time,
        )

        # Save stats to SQLite
        self._save_stats()

        logger.info("")
        logger.info("=" * 80)
        logger.info("✅ FOUNDATION DATABASE COMPLETE")
        logger.info("=" * 80)
        logger.info(f"   Output: {self.output_path}")
        logger.info(f"   Original rows: {original_rows:,}")
        logger.info(f"   Filtered rows: {filtered_rows:,}")
        logger.info(f"   Warmup: {self.foundation_stats.warmup_rows:,}")
        logger.info(f"   Train: {self.foundation_stats.train_rows:,}")
        logger.info(f"   Validation: {self.foundation_stats.val_rows:,}")
        logger.info(f"   Test: {self.foundation_stats.test_rows:,}")
        logger.info(f"   Processing time: {processing_time:.1f}s")

        return self.output_path

    def _filter_rows(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
        """
        Filter rows based on null rate.

        Returns:
            Filtered DataFrame and list of high-null columns
        """
        n_cols = len(df.columns)

        # Calculate null rates per row
        null_counts = df.isna().sum(axis=1)
        fill_rates = 1.0 - (null_counts / n_cols)

        # Filter rows
        keep_mask = fill_rates >= self.min_fill_rate
        n_filtered = (~keep_mask).sum()

        if n_filtered > 0:
            logger.info(f"   Filtering rows with < {self.min_fill_rate*100:.0f}% fill rate...")
            logger.info(f"   Removing {n_filtered:,} rows ({n_filtered/len(df)*100:.1f}%)")
            df = df[keep_mask].reset_index(drop=True)
        else:
            logger.info(f"   No rows filtered (all have >= {self.min_fill_rate*100:.0f}% fill rate)")

        # Identify high-null columns (>= 80% nulls)
        col_null_rates = df.isna().sum() / len(df)
        high_null_cols = col_null_rates[col_null_rates >= WARN_NULL_RATE].index.tolist()

        if high_null_cols:
            logger.warning(f"   ⚠️  {len(high_null_cols)} columns have >= {WARN_NULL_RATE*100:.0f}% nulls:")
            for col in high_null_cols[:5]:
                logger.warning(f"      - {col}: {col_null_rates[col]*100:.1f}% null")
            if len(high_null_cols) > 5:
                logger.warning(f"      ... and {len(high_null_cols) - 5} more")

        logger.info(f"   Remaining: {len(df):,} rows")
        return df, high_null_cols

    def _detect_types(self, df: pd.DataFrame):
        """Detect column types on a sample of the data."""
        # Sample for type detection
        sample_size = min(TYPE_DETECTION_SAMPLE_SIZE, len(df))
        sample_df = df.sample(sample_size, random_state=self.random_seed)

        logger.info(f"   Sampling {sample_size:,} rows for type detection...")

        for col in df.columns:
            series = sample_df[col]

            # Basic stats
            null_count = df[col].isna().sum()
            null_rate = null_count / len(df)
            unique_count = df[col].nunique()

            # Get sample values
            non_null = series.dropna()
            sample_values = []
            if len(non_null) > 0:
                sample_values = non_null.sample(min(5, len(non_null))).tolist()

            # Detect type
            detected_type = detect_column_type(series, col)

            # Check for JSON
            is_json = False
            json_schema = None
            if detected_type in ("categorical", "text"):
                is_json = is_json_column(series)
                if is_json:
                    detected_type = "json"
                    # Parse JSON values for schema inference
                    json_values = []
                    for val in non_null:
                        if isinstance(val, (dict, list)):
                            json_values.append(val)
                        elif isinstance(val, str):
                            try:
                                json_values.append(json.loads(val))
                            except (json.JSONDecodeError, TypeError):
                                pass
                    if json_values:
                        json_schema = infer_json_schema(json_values)

            self.column_stats[col] = ColumnStats(
                name=col,
                detected_type=detected_type,
                null_count=null_count,
                null_rate=null_rate,
                unique_count=unique_count,
                sample_values=sample_values,
                is_json=is_json,
                json_schema=json_schema,
            )

        # Log type summary
        type_counts = Counter(s.detected_type for s in self.column_stats.values())
        logger.info(f"   Detected types: {dict(type_counts)}")

    def _create_splits(self, df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """
        Create warmup/train/val/test splits.

        Warmup uses the cleanest rows (<10% nulls if available).
        """
        n_rows = len(df)
        n_cols = len(df.columns)

        # Shuffle
        df = df.sample(frac=1.0, random_state=self.random_seed).reset_index(drop=True)

        # Calculate null rates for warmup selection
        null_counts = df.isna().sum(axis=1)
        null_rates = null_counts / n_cols

        # Try to get clean rows for warmup (<10% nulls)
        clean_mask = null_rates < WARMUP_MAX_NULL_RATE
        n_clean = clean_mask.sum()
        n_warmup_target = int(n_rows * self.warmup_fraction)

        if n_clean >= n_warmup_target:
            # Use clean rows for warmup
            clean_indices = df.index[clean_mask].tolist()
            random.seed(self.random_seed)
            random.shuffle(clean_indices)
            warmup_indices = set(clean_indices[:n_warmup_target])
            logger.info(f"   Warmup: {n_warmup_target:,} clean rows (< {WARMUP_MAX_NULL_RATE*100:.0f}% nulls)")
        else:
            # Not enough clean rows, use what we have plus some others
            clean_indices = df.index[clean_mask].tolist()
            other_indices = df.index[~clean_mask].tolist()
            random.seed(self.random_seed)
            random.shuffle(other_indices)

            warmup_indices = set(clean_indices)
            n_needed = n_warmup_target - len(warmup_indices)
            if n_needed > 0:
                warmup_indices.update(other_indices[:n_needed])

            logger.warning(
                f"   ⚠️  Only {n_clean:,} clean rows available for warmup. "
                f"Using {len(warmup_indices):,} rows (some with higher null rates)."
            )

        # Split remaining rows
        remaining_indices = [i for i in df.index if i not in warmup_indices]
        random.seed(self.random_seed + 1)
        random.shuffle(remaining_indices)

        # Calculate split sizes from remaining
        n_remaining = len(remaining_indices)
        remaining_total = self.train_fraction + self.val_fraction + self.test_fraction

        n_train = int(n_remaining * (self.train_fraction / remaining_total))
        n_val = int(n_remaining * (self.val_fraction / remaining_total))
        n_test = n_remaining - n_train - n_val

        train_indices = remaining_indices[:n_train]
        val_indices = remaining_indices[n_train:n_train + n_val]
        test_indices = remaining_indices[n_train + n_val:]

        logger.info(f"   Train: {len(train_indices):,} rows")
        logger.info(f"   Validation: {len(val_indices):,} rows")
        logger.info(f"   Test: {len(test_indices):,} rows")

        return {
            "warmup": df.loc[list(warmup_indices)].reset_index(drop=True),
            "train": df.loc[train_indices].reset_index(drop=True),
            "validation": df.loc[val_indices].reset_index(drop=True),
            "test": df.loc[test_indices].reset_index(drop=True),
        }

    def _create_sqlite(self, splits: Dict[str, pd.DataFrame]):
        """Create SQLite database with splits and metadata."""
        # Remove existing database
        if self.output_path.exists():
            logger.info(f"   Removing existing database: {self.output_path}")
            os.remove(self.output_path)

        # Ensure parent directory exists
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(str(self.output_path))

        try:
            # Create metadata table
            conn.execute("""
                CREATE TABLE metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)

            # Create column_types table
            conn.execute("""
                CREATE TABLE column_types (
                    column_index INTEGER PRIMARY KEY,
                    column_name TEXT NOT NULL,
                    detected_type TEXT NOT NULL,
                    null_count INTEGER,
                    null_rate REAL,
                    unique_count INTEGER,
                    is_json INTEGER DEFAULT 0
                )
            """)

            # Create json_schemas table
            conn.execute("""
                CREATE TABLE json_schemas (
                    column_name TEXT PRIMARY KEY,
                    schema_json TEXT
                )
            """)

            # Insert column types
            for idx, (col, stats) in enumerate(self.column_stats.items()):
                conn.execute(
                    """
                    INSERT INTO column_types
                    (column_index, column_name, detected_type, null_count, null_rate, unique_count, is_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (idx, col, stats.detected_type, stats.null_count, stats.null_rate,
                     stats.unique_count, 1 if stats.is_json else 0)
                )

                # Insert JSON schema if available
                if stats.json_schema:
                    conn.execute(
                        "INSERT INTO json_schemas (column_name, schema_json) VALUES (?, ?)",
                        (col, json.dumps(stats.json_schema))
                    )

            # Create data tables with row_idx for efficient range queries
            for split_name, split_df in splits.items():
                logger.info(f"   Writing {split_name} table: {len(split_df):,} rows...")

                # Add row_idx column
                split_df = split_df.copy()
                split_df.insert(0, "row_idx", range(len(split_df)))

                # Write to SQLite
                split_df.to_sql(split_name, conn, index=False, if_exists="replace")

                # Create index on row_idx for efficient range queries
                conn.execute(f"CREATE INDEX idx_{split_name}_row_idx ON {split_name}(row_idx)")

            conn.commit()
            logger.info(f"   ✅ Database created: {self.output_path}")

        finally:
            conn.close()

    def _save_stats(self):
        """Save foundation stats to the metadata table."""
        if not self.foundation_stats:
            return

        conn = sqlite3.connect(str(self.output_path))
        try:
            stats_dict = {
                "total_rows": self.foundation_stats.total_rows,
                "total_columns": self.foundation_stats.total_columns,
                "filtered_rows": self.foundation_stats.filtered_rows,
                "warmup_rows": self.foundation_stats.warmup_rows,
                "train_rows": self.foundation_stats.train_rows,
                "val_rows": self.foundation_stats.val_rows,
                "test_rows": self.foundation_stats.test_rows,
                "high_null_columns": json.dumps(self.foundation_stats.high_null_columns),
                "json_columns": json.dumps(self.foundation_stats.json_columns),
                "created_at": self.foundation_stats.created_at,
                "processing_time_seconds": self.foundation_stats.processing_time_seconds,
                "min_fill_rate": self.min_fill_rate,
                "warmup_fraction": self.warmup_fraction,
                "train_fraction": self.train_fraction,
                "val_fraction": self.val_fraction,
                "test_fraction": self.test_fraction,
                "random_seed": self.random_seed,
            }

            for key, value in stats_dict.items():
                conn.execute(
                    "INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)",
                    (key, str(value))
                )

            conn.commit()
        finally:
            conn.close()

    @classmethod
    def load_stats(cls, sqlite_path: Union[str, Path]) -> Optional[FoundationStats]:
        """Load foundation stats from an existing SQLite database."""
        sqlite_path = Path(sqlite_path)
        if not sqlite_path.exists():
            return None

        conn = sqlite3.connect(str(sqlite_path))
        try:
            cursor = conn.execute("SELECT key, value FROM metadata")
            metadata = dict(cursor.fetchall())

            return FoundationStats(
                total_rows=int(metadata.get("total_rows", 0)),
                total_columns=int(metadata.get("total_columns", 0)),
                filtered_rows=int(metadata.get("filtered_rows", 0)),
                warmup_rows=int(metadata.get("warmup_rows", 0)),
                train_rows=int(metadata.get("train_rows", 0)),
                val_rows=int(metadata.get("val_rows", 0)),
                test_rows=int(metadata.get("test_rows", 0)),
                high_null_columns=json.loads(metadata.get("high_null_columns", "[]")),
                json_columns=json.loads(metadata.get("json_columns", "[]")),
                created_at=metadata.get("created_at", ""),
                processing_time_seconds=float(metadata.get("processing_time_seconds", 0)),
            )
        except Exception as e:
            logger.warning(f"Could not load stats from {sqlite_path}: {e}")
            return None
        finally:
            conn.close()
