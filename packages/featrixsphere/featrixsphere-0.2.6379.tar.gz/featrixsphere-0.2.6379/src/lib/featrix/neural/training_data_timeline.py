#  -*- coding: utf-8 -*-
#
#  Copyright Featrix, Inc 2023-2025
#
#  Proprietary and Confidential.  Unauthorized use, copying or dissemination
#  of these materials is strictly prohibited.
#
"""
ESTrainingDataTimeline - Unified data provider for ES training.

This module provides a consistent interface for feeding data to ES training,
supporting both simple in-memory DataFrames (current behavior) and large
SQLite-backed foundation datasets.

Usage:
    # Simple mode (mirrors current ES behavior)
    timeline = ESTrainingDataTimeline.from_dataset(dataset, val_fraction=0.2)

    # Or from existing train/val split
    timeline = ESTrainingDataTimeline.from_existing_split(train_ds, val_ds)

    # Foundation mode (SQLite-backed, chunked)
    timeline = ESTrainingDataTimeline.from_foundation("/path/to/foundation.sqlite")

    # Training loop
    warmup = timeline.get_warmup()  # May be None in simple mode
    for epoch_idx in range(timeline.total_epochs(num_passes=6)):
        train_data = timeline.get_next_train_set(epoch_idx)
        # ... train ...
"""
from __future__ import annotations

import logging
import math
import sqlite3
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Iterator, List, Optional, Tuple, TYPE_CHECKING

import pandas as pd

from featrix.neural.logging_config import configure_logging
configure_logging()

if TYPE_CHECKING:
    from featrix.neural.input_data_set import FeatrixInputDataSet

logger = logging.getLogger(__name__)


# =============================================================================
# Backend Interface
# =============================================================================

class TrainingDataBackend(ABC):
    """
    Abstract backend for ESTrainingDataTimeline.

    Implementations provide different storage strategies:
    - SimpleDataFrameBackend: In-memory, mirrors current ES behavior
    - FoundationBackend: SQLite-backed for large datasets
    """

    @abstractmethod
    def get_warmup_df(self) -> Optional[pd.DataFrame]:
        """Return warmup DataFrame, or None if not available."""
        pass

    @abstractmethod
    def get_train_rows(self, start_idx: int, end_idx: int) -> pd.DataFrame:
        """Return training rows in range [start_idx, end_idx)."""
        pass

    @abstractmethod
    def get_validation_df(self) -> pd.DataFrame:
        """Return validation DataFrame."""
        pass

    @abstractmethod
    def get_test_df(self) -> Optional[pd.DataFrame]:
        """Return test DataFrame, or None if not available."""
        pass

    @property
    @abstractmethod
    def train_row_count(self) -> int:
        """Total number of training rows."""
        pass

    @property
    @abstractmethod
    def locked_encoders(self) -> Dict[str, str]:
        """Encoder type overrides for consistent encoding across splits."""
        pass

    @property
    @abstractmethod
    def is_chunked(self) -> bool:
        """
        If True, get_train_rows returns different data based on indices.
        If False, get_train_rows returns full dataset (indices ignored).
        """
        pass

    @property
    def train_input_data(self) -> Optional["FeatrixInputDataSet"]:
        """Return the underlying train FeatrixInputDataSet if available."""
        return None

    @property
    def val_input_data(self) -> Optional["FeatrixInputDataSet"]:
        """Return the underlying val FeatrixInputDataSet if available."""
        return None


# =============================================================================
# Simple DataFrame Backend (Current ES Behavior)
# =============================================================================

class SimpleDataFrameBackend(TrainingDataBackend):
    """
    In-memory backend that mirrors current ES training behavior.

    - All training data in memory
    - Train/val split (no separate test, no warmup)
    - Each epoch sees all training rows (DataLoader shuffles)
    - get_train_rows ignores indices and returns full dataset
    """

    def __init__(
        self,
        train_ds: "FeatrixInputDataSet",
        val_ds: "FeatrixInputDataSet",
    ):
        """
        Initialize from existing train/val split.

        Args:
            train_ds: Training FeatrixInputDataSet
            val_ds: Validation FeatrixInputDataSet
        """
        self._train_ds = train_ds
        self._val_ds = val_ds
        self._locked_encoders = train_ds.encoderOverrides or {}

        logger.info(
            f"📊 SimpleDataFrameBackend initialized: "
            f"train={len(train_ds.df):,} rows, val={len(val_ds.df):,} rows"
        )

    def get_warmup_df(self) -> Optional[pd.DataFrame]:
        """Simple mode has no warmup - return None."""
        return None

    def get_train_rows(self, start_idx: int, end_idx: int) -> pd.DataFrame:
        """
        Return full training DataFrame.

        In simple mode, indices are ignored - DataLoader handles shuffling.
        """
        return self._train_ds.df

    def get_validation_df(self) -> pd.DataFrame:
        """Return validation DataFrame."""
        return self._val_ds.df

    def get_test_df(self) -> Optional[pd.DataFrame]:
        """Simple mode has no separate test set - return None."""
        return None

    @property
    def train_row_count(self) -> int:
        return len(self._train_ds.df)

    @property
    def locked_encoders(self) -> Dict[str, str]:
        return self._locked_encoders

    @property
    def is_chunked(self) -> bool:
        """Simple backend returns full dataset each call."""
        return False

    @property
    def train_input_data(self) -> "FeatrixInputDataSet":
        """Return the underlying train FeatrixInputDataSet."""
        return self._train_ds

    @property
    def val_input_data(self) -> "FeatrixInputDataSet":
        """Return the underlying val FeatrixInputDataSet."""
        return self._val_ds


# =============================================================================
# Foundation Backend (SQLite-backed)
# =============================================================================

class FoundationBackend(TrainingDataBackend):
    """
    SQLite-backed backend for large datasets.

    - Data stored in SQLite tables: warmup, train, validation, test
    - Training data chunked by row_idx for memory-efficient iteration
    - Supports 10k rows per epoch with automatic rotation
    """

    def __init__(self, sqlite_path: str):
        """
        Initialize from existing foundation SQLite database.

        Args:
            sqlite_path: Path to foundation SQLite database
        """
        self.sqlite_path = sqlite_path
        self._locked_encoders = {}
        self._train_row_count = 0
        self._load_metadata()

        logger.info(
            f"📊 FoundationBackend initialized from {sqlite_path}: "
            f"train={self._train_row_count:,} rows"
        )

    def _load_metadata(self):
        """Load metadata and column types from SQLite."""
        conn = sqlite3.connect(self.sqlite_path)
        cursor = conn.cursor()

        # Load column types
        cursor.execute("SELECT column_name, detected_type FROM column_types ORDER BY column_index")
        rows = cursor.fetchall()
        self._locked_encoders = {col: dtype for col, dtype in rows}

        # Get train row count
        cursor.execute("SELECT COUNT(*) FROM train")
        self._train_row_count = cursor.fetchone()[0]

        conn.close()

    def get_warmup_df(self) -> Optional[pd.DataFrame]:
        """Load warmup table from SQLite."""
        conn = sqlite3.connect(self.sqlite_path)
        try:
            df = pd.read_sql("SELECT * FROM warmup", conn)
            # Drop row_idx if present (internal bookkeeping)
            if 'row_idx' in df.columns:
                df = df.drop(columns=['row_idx'])
            return df
        except Exception as e:
            logger.warning(f"Could not load warmup table: {e}")
            return None
        finally:
            conn.close()

    def get_train_rows(self, start_idx: int, end_idx: int) -> pd.DataFrame:
        """Load training rows in range [start_idx, end_idx) from SQLite."""
        conn = sqlite3.connect(self.sqlite_path)
        df = pd.read_sql(
            f"SELECT * FROM train WHERE row_idx >= {start_idx} AND row_idx < {end_idx}",
            conn
        )
        conn.close()

        # Drop row_idx (internal bookkeeping)
        if 'row_idx' in df.columns:
            df = df.drop(columns=['row_idx'])

        return df

    def get_validation_df(self) -> pd.DataFrame:
        """Load validation table from SQLite."""
        conn = sqlite3.connect(self.sqlite_path)
        df = pd.read_sql("SELECT * FROM validation", conn)
        conn.close()

        if 'row_idx' in df.columns:
            df = df.drop(columns=['row_idx'])

        return df

    def get_test_df(self) -> Optional[pd.DataFrame]:
        """Load test table from SQLite."""
        conn = sqlite3.connect(self.sqlite_path)
        try:
            df = pd.read_sql("SELECT * FROM test", conn)
            if 'row_idx' in df.columns:
                df = df.drop(columns=['row_idx'])
            return df
        except Exception as e:
            logger.warning(f"Could not load test table: {e}")
            return None
        finally:
            conn.close()

    @property
    def train_row_count(self) -> int:
        return self._train_row_count

    @property
    def locked_encoders(self) -> Dict[str, str]:
        return self._locked_encoders

    @property
    def is_chunked(self) -> bool:
        """Foundation backend returns different data based on indices."""
        return True


# =============================================================================
# ESTrainingDataTimeline
# =============================================================================

@dataclass
class EpochInfo:
    """Information about the current epoch's position in training."""
    epoch_idx: int
    pass_num: int
    epoch_within_pass: int
    start_row: int
    end_row: int
    is_pass_boundary: bool  # True if this is the last epoch of a pass


class ESTrainingDataTimeline:
    """
    Unified data provider for ES training.

    Handles both simple in-memory training (current behavior) and large
    SQLite-backed foundation datasets with chunked iteration.

    Key concepts:
    - In simple mode: Each epoch sees all training data, DataLoader shuffles
    - In foundation mode: Each epoch sees ~chunk_size rows, rotates through passes

    Attributes:
        backend: The storage backend (SimpleDataFrameBackend or FoundationBackend)
        chunk_size: Rows per epoch in chunked mode (default: 10,000)
    """

    DEFAULT_CHUNK_SIZE = 10_000

    def __init__(
        self,
        backend: TrainingDataBackend,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
    ):
        """
        Initialize timeline with a backend.

        Use factory methods instead of calling this directly:
        - ESTrainingDataTimeline.from_existing_split()
        - ESTrainingDataTimeline.from_dataset()
        - ESTrainingDataTimeline.from_foundation()
        """
        self.backend = backend
        self.chunk_size = chunk_size

        # Cache for FeatrixInputDataSet instances
        self._warmup_cache: Optional["FeatrixInputDataSet"] = None
        self._validation_cache: Optional["FeatrixInputDataSet"] = None
        self._test_cache: Optional["FeatrixInputDataSet"] = None

    # -------------------------------------------------------------------------
    # Factory Methods
    # -------------------------------------------------------------------------

    @classmethod
    def from_existing_split(
        cls,
        train_ds: "FeatrixInputDataSet",
        val_ds: "FeatrixInputDataSet",
    ) -> "ESTrainingDataTimeline":
        """
        Create timeline from existing train/val split.

        This mirrors current ES behavior exactly - wraps the existing
        FeatrixInputDataSet instances without any changes.

        Args:
            train_ds: Training FeatrixInputDataSet
            val_ds: Validation FeatrixInputDataSet

        Returns:
            ESTrainingDataTimeline in simple mode
        """
        backend = SimpleDataFrameBackend(train_ds, val_ds)
        return cls(backend=backend)

    @classmethod
    def from_dataset(
        cls,
        dataset: "FeatrixInputDataSet",
        val_fraction: float = 0.2,
    ) -> "ESTrainingDataTimeline":
        """
        Create timeline from single dataset, split internally.

        Args:
            dataset: FeatrixInputDataSet to split
            val_fraction: Fraction for validation (default: 0.2)

        Returns:
            ESTrainingDataTimeline in simple mode
        """
        train_ds, val_ds = dataset.split(fraction=val_fraction)
        return cls.from_existing_split(train_ds, val_ds)

    @classmethod
    def from_foundation(
        cls,
        sqlite_path: str,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
    ) -> "ESTrainingDataTimeline":
        """
        Create timeline from foundation SQLite database.

        Args:
            sqlite_path: Path to foundation SQLite database
            chunk_size: Rows per epoch (default: 10,000)

        Returns:
            ESTrainingDataTimeline in foundation/chunked mode
        """
        backend = FoundationBackend(sqlite_path)
        return cls(backend=backend, chunk_size=chunk_size)

    @classmethod
    def from_sqlite(
        cls,
        sqlite_path: str,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
    ) -> "ESTrainingDataTimeline":
        """
        Create timeline from SQLite database, auto-detecting foundation vs standard.

        This is the recommended factory method for creating timelines from SQLite.
        It inspects the database schema to determine if it's a foundation database
        (has train/validation/test/warmup tables) or a standard database (has data table).

        Args:
            sqlite_path: Path to SQLite database
            chunk_size: Rows per epoch for foundation mode (default: 10,000)

        Returns:
            ESTrainingDataTimeline in appropriate mode
        """
        if cls.is_foundation_sqlite(sqlite_path):
            logger.info(f"📊 Detected foundation SQLite database: {sqlite_path}")
            return cls.from_foundation(sqlite_path, chunk_size)
        else:
            # Standard SQLite - load into FeatrixInputDataSet and create simple timeline
            logger.info(f"📊 Detected standard SQLite database: {sqlite_path}")
            from featrix.neural.sqlite_utils import load_sqlite_file_to_df
            df = load_sqlite_file_to_df(sqlite_path)
            from featrix.neural.input_data_set import FeatrixInputDataSet
            dataset = FeatrixInputDataSet(df=df)
            return cls.from_dataset(dataset)

    @staticmethod
    def is_foundation_sqlite(sqlite_path: str) -> bool:
        """
        Check if a SQLite database is a foundation database.

        Foundation databases have:
        - train table
        - validation table
        - column_types table
        - optionally: warmup, test, metadata, json_schemas tables

        Standard databases have:
        - data table

        Args:
            sqlite_path: Path to SQLite database

        Returns:
            True if foundation database, False if standard
        """
        import os
        if not os.path.exists(sqlite_path):
            return False

        try:
            conn = sqlite3.connect(sqlite_path)
            cursor = conn.cursor()

            # Check for foundation tables
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('train', 'validation', 'column_types')"
            )
            foundation_tables = set(row[0] for row in cursor.fetchall())
            conn.close()

            # Foundation database must have at least train, validation, and column_types
            required_tables = {'train', 'validation', 'column_types'}
            return required_tables.issubset(foundation_tables)

        except Exception as e:
            logger.warning(f"Could not check SQLite schema: {e}")
            return False

    # -------------------------------------------------------------------------
    # Data Access Methods
    # -------------------------------------------------------------------------

    def get_warmup(self) -> Optional["FeatrixInputDataSet"]:
        """
        Return warmup dataset for initial training pass.

        Returns None in simple mode (no warmup).
        In foundation mode, returns clean rows (<10% nulls).
        """
        if self._warmup_cache is not None:
            return self._warmup_cache

        df = self.backend.get_warmup_df()
        if df is None:
            return None

        from featrix.neural.input_data_set import FeatrixInputDataSet
        self._warmup_cache = FeatrixInputDataSet(
            df=df,
            encoder_overrides=self.backend.locked_encoders,
            standup_only=True,  # Skip detection, use locked encoders
        )
        return self._warmup_cache

    def get_next_train_set(self, epoch_idx: int) -> "FeatrixInputDataSet":
        """
        Return training data for this epoch.

        In simple mode: Returns full training dataset (same every epoch).
                        DataLoader handles shuffling.

        In foundation mode: Returns ~chunk_size rows based on epoch_idx.
                           Rotates through data across passes.

        Args:
            epoch_idx: Current epoch index (0-based)

        Returns:
            FeatrixInputDataSet for this epoch's training
        """
        if not self.backend.is_chunked:
            # Simple mode - return the actual FeatrixInputDataSet
            # This preserves all the metadata (detectors, casted_df, etc.)
            return self.backend.train_input_data

        # Foundation/chunked mode - load specific rows
        epoch_info = self._get_epoch_info(epoch_idx)
        df = self.backend.get_train_rows(epoch_info.start_row, epoch_info.end_row)

        # Log chunk loading
        total_rows = self.backend.train_row_count
        chunk_size = epoch_info.end_row - epoch_info.start_row
        chunk_pct = chunk_size / total_rows * 100
        progress_pct = epoch_info.end_row / total_rows * 100

        if epoch_info.epoch_within_pass == 0:
            # Starting a new pass
            logger.info(f"🔄 FOUNDATION PASS {epoch_info.pass_num + 1}: Starting new pass through {total_rows:,} training rows")

        logger.info(
            f"📦 Epoch {epoch_idx}: Loading chunk [{epoch_info.start_row:,}-{epoch_info.end_row:,}] "
            f"({len(df):,} rows, {chunk_pct:.1f}% of data, pass progress: {progress_pct:.1f}%)"
        )

        # Post timeline event for chunk loading
        from featrix.neural.timeline_events import post_timeline_event
        post_timeline_event({
            'epoch': epoch_idx,
            'event_type': 'foundation_chunk_load',
            'pass_num': epoch_info.pass_num + 1,
            'epoch_within_pass': epoch_info.epoch_within_pass,
            'start_row': epoch_info.start_row,
            'end_row': epoch_info.end_row,
            'chunk_size': chunk_size,
            'total_train_rows': total_rows,
            'pass_progress_pct': progress_pct,
            'is_pass_boundary': epoch_info.is_pass_boundary,
        })

        if epoch_info.is_pass_boundary:
            logger.info(f"✅ Pass {epoch_info.pass_num + 1} complete - full rotation through training data")
            post_timeline_event({
                'epoch': epoch_idx,
                'event_type': 'foundation_pass_complete',
                'pass_num': epoch_info.pass_num + 1,
                'total_train_rows': total_rows,
            })

        from featrix.neural.input_data_set import FeatrixInputDataSet
        return FeatrixInputDataSet(
            df=df,
            encoder_overrides=self.backend.locked_encoders,
            standup_only=True,
        )

    def get_validation_set(self) -> "FeatrixInputDataSet":
        """
        Return validation dataset.

        Cached after first call for efficiency.
        """
        if self._validation_cache is not None:
            return self._validation_cache

        # In simple mode, return the actual FeatrixInputDataSet
        if not self.backend.is_chunked and self.backend.val_input_data is not None:
            self._validation_cache = self.backend.val_input_data
            return self._validation_cache

        # Foundation mode - load from SQLite
        df = self.backend.get_validation_df()

        from featrix.neural.input_data_set import FeatrixInputDataSet
        self._validation_cache = FeatrixInputDataSet(
            df=df,
            encoder_overrides=self.backend.locked_encoders,
            standup_only=True,
        )
        return self._validation_cache

    def get_test_set(self) -> Optional["FeatrixInputDataSet"]:
        """
        Return test dataset for holdout monitoring.

        Returns None in simple mode (no separate test set).
        """
        if self._test_cache is not None:
            return self._test_cache

        df = self.backend.get_test_df()
        if df is None:
            return None

        from featrix.neural.input_data_set import FeatrixInputDataSet
        self._test_cache = FeatrixInputDataSet(
            df=df,
            encoder_overrides=self.backend.locked_encoders,
            standup_only=True,
        )
        return self._test_cache

    # -------------------------------------------------------------------------
    # Direct Access to Underlying Data (for ES compatibility)
    # -------------------------------------------------------------------------

    @property
    def train_input_data(self) -> Optional["FeatrixInputDataSet"]:
        """
        Direct access to train FeatrixInputDataSet.

        Only available in simple mode. Returns None in foundation mode.
        Used for backward compatibility with ES code that accesses
        self.train_input_data directly.
        """
        return self.backend.train_input_data

    @property
    def val_input_data(self) -> Optional["FeatrixInputDataSet"]:
        """
        Direct access to val FeatrixInputDataSet.

        Only available in simple mode. Returns None in foundation mode.
        """
        return self.backend.val_input_data

    # -------------------------------------------------------------------------
    # Epoch Calculation
    # -------------------------------------------------------------------------

    @property
    def epochs_per_pass(self) -> int:
        """
        Number of epochs to complete one pass through training data.

        Simple mode: 1 (each epoch sees all data)
        Foundation mode: ceil(train_rows / chunk_size)
        """
        if not self.backend.is_chunked:
            return 1
        return math.ceil(self.backend.train_row_count / self.chunk_size)

    def total_epochs(self, num_passes: int) -> int:
        """
        Total epochs for given number of passes.

        Args:
            num_passes: Number of complete passes through training data

        Returns:
            Total epoch count
        """
        return self.epochs_per_pass * num_passes

    def _get_epoch_info(self, epoch_idx: int) -> EpochInfo:
        """
        Calculate epoch position information.

        Args:
            epoch_idx: Current epoch index

        Returns:
            EpochInfo with pass number, row range, etc.
        """
        epochs_per_pass = self.epochs_per_pass
        pass_num = epoch_idx // epochs_per_pass
        epoch_within_pass = epoch_idx % epochs_per_pass

        start_row = epoch_within_pass * self.chunk_size
        end_row = min(start_row + self.chunk_size, self.backend.train_row_count)

        is_pass_boundary = (epoch_within_pass == epochs_per_pass - 1)

        return EpochInfo(
            epoch_idx=epoch_idx,
            pass_num=pass_num,
            epoch_within_pass=epoch_within_pass,
            start_row=start_row,
            end_row=end_row,
            is_pass_boundary=is_pass_boundary,
        )

    def is_pass_boundary(self, epoch_idx: int) -> bool:
        """
        Check if this epoch completes a pass through training data.

        Useful for deciding when to validate.

        Args:
            epoch_idx: Current epoch index

        Returns:
            True if this is the last epoch of a pass
        """
        return self._get_epoch_info(epoch_idx).is_pass_boundary

    def get_pass_num(self, epoch_idx: int) -> int:
        """
        Get the pass number for an epoch.

        Args:
            epoch_idx: Current epoch index

        Returns:
            Pass number (0-indexed)
        """
        return self._get_epoch_info(epoch_idx).pass_num

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------

    @property
    def is_chunked(self) -> bool:
        """Whether this timeline uses chunked iteration."""
        return self.backend.is_chunked

    @property
    def train_row_count(self) -> int:
        """Total number of training rows."""
        return self.backend.train_row_count

    @property
    def locked_encoders(self) -> Dict[str, str]:
        """Encoder type overrides."""
        return self.backend.locked_encoders

    def __repr__(self) -> str:
        mode = "chunked" if self.is_chunked else "simple"
        return (
            f"ESTrainingDataTimeline(mode={mode}, "
            f"train_rows={self.train_row_count:,}, "
            f"epochs_per_pass={self.epochs_per_pass})"
        )
