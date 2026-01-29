#  -*- coding: utf-8 -*-
#
#  Copyright Featrix, Inc 2023-2025
#
#  Proprietary and Confidential.  Unauthorized use, copying or dissemination
#  of these materials is strictly prohibited.
"""
Training Movie Writer - Dumps per-epoch 3D embeddings for visualization.

This module generates JSON files compatible with the Featrix Sphere Viewer's
training movie format, allowing visualization of how embeddings evolve during
SP training.

Usage:
    from featrix.neural.training_movie_writer import TrainingMovieWriter

    writer = TrainingMovieWriter(output_dir="/path/to/output")

    # During training, after each epoch:
    writer.add_epoch(
        epoch_idx=epoch,
        embeddings=batch_full[:, :3],  # 3D short embeddings
        labels=labels,                  # target values
        splits=splits,                  # "train" or "val" per sample
        row_ids=row_ids,                # optional row identifiers
        metadata={"age": ages, "income": incomes}  # optional per-sample metadata
    )

    # After training completes:
    writer.add_training_metrics(
        validation_loss=val_losses,     # list of (epoch, value) tuples
        learning_rate=lr_values         # optional
    )

    writer.save("sp_training_movie.json")
"""

from __future__ import annotations

import json
import logging
import os
import traceback
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Union

import numpy as np
import torch

if TYPE_CHECKING:
    import pandas

logger = logging.getLogger(__name__)


class TrainingMovieWriter:
    """
    Collects and writes per-epoch 3D embedding data for training movie visualization.

    The output format is compatible with the Featrix Sphere Viewer training movie
    feature, which animates embedding positions across epochs to show convergence.
    """

    def __init__(self, output_dir: Optional[str] = None):
        """
        Initialize the training movie writer.

        Args:
            output_dir: Directory where the JSON file will be saved.
                       If None, must be provided when calling save().
        """
        self.output_dir = output_dir
        self.epoch_projections: Dict[str, Dict[str, Any]] = {}
        self.training_metrics: Dict[str, List[Dict[str, float]]] = {}
        self._point_count: Optional[int] = None

    def add_epoch(
        self,
        epoch_idx: int,
        embeddings: Union[torch.Tensor, np.ndarray],
        labels: Union[torch.Tensor, np.ndarray, List],
        splits: Optional[Union[List[str], np.ndarray]] = None,
        row_ids: Optional[Union[torch.Tensor, np.ndarray, List]] = None,
        scalar_columns: Optional[Dict[str, Union[torch.Tensor, np.ndarray, List]]] = None,
        set_columns: Optional[Dict[str, Union[torch.Tensor, np.ndarray, List]]] = None,
        string_columns: Optional[Dict[str, Union[torch.Tensor, np.ndarray, List]]] = None,
        cluster_results: Optional[Dict[int, Dict[str, Any]]] = None,
    ) -> None:
        """
        Add embedding data for a single epoch.

        Args:
            epoch_idx: The epoch number (0-indexed or 1-indexed, will be stored as 1-indexed)
            embeddings: 3D embeddings tensor/array of shape (n_samples, 3)
            labels: Target labels for each sample (used in set_columns as "label")
            splits: "train" or "val" for each sample (used in set_columns as "split")
            row_ids: Optional unique identifiers for each row
            scalar_columns: Dict of column_name -> values for numeric metadata
            set_columns: Dict of column_name -> values for categorical metadata
            string_columns: Dict of column_name -> values for text metadata
            cluster_results: Optional clustering results dict {n_clusters: {cluster_labels, silhouette_score}}
        """
        # Convert tensors to numpy
        if isinstance(embeddings, torch.Tensor):
            embeddings = embeddings.detach().cpu().numpy()
        if isinstance(labels, torch.Tensor):
            labels = labels.detach().cpu().numpy()
        if isinstance(row_ids, torch.Tensor):
            row_ids = row_ids.detach().cpu().numpy()

        n_samples = len(embeddings)

        # Validate embedding shape
        if embeddings.shape[1] != 3:
            raise ValueError(f"Embeddings must have shape (n_samples, 3), got {embeddings.shape}")

        # Validate point count consistency
        if self._point_count is None:
            self._point_count = n_samples
        elif self._point_count != n_samples:
            logger.warning(
                f"Point count mismatch: epoch {epoch_idx} has {n_samples} points, "
                f"expected {self._point_count}. This may cause viewer issues."
            )

        # Build coords list
        coords = []
        for i in range(n_samples):
            coord = {
                "0": float(embeddings[i, 0]),
                "1": float(embeddings[i, 1]),
                "2": float(embeddings[i, 2]),
                "__featrix_row_offset": i,
            }

            # Add row ID if provided
            if row_ids is not None:
                coord["__featrix_row_id"] = int(row_ids[i]) if isinstance(row_ids[i], (int, np.integer)) else row_ids[i]
            else:
                coord["__featrix_row_id"] = i

            # Build scalar_columns
            coord_scalars = {}
            if scalar_columns:
                for col_name, values in scalar_columns.items():
                    val = values[i]
                    if isinstance(val, torch.Tensor):
                        val = val.item()
                    elif isinstance(val, np.ndarray):
                        val = val.item() if val.ndim == 0 else float(val)
                    elif isinstance(val, (np.floating, np.integer)):
                        val = float(val)
                    coord_scalars[col_name] = val
            if coord_scalars:
                coord["scalar_columns"] = coord_scalars

            # Build set_columns (includes label and split)
            coord_sets = {}

            # Add label
            label_val = labels[i]
            if isinstance(label_val, torch.Tensor):
                label_val = label_val.item()
            elif isinstance(label_val, np.ndarray):
                label_val = label_val.item() if label_val.ndim == 0 else str(label_val)
            elif isinstance(label_val, (np.floating, np.integer)):
                label_val = label_val.item()
            coord_sets["label"] = str(label_val)

            # Add split
            if splits is not None:
                split_val = splits[i]
                if isinstance(split_val, bytes):
                    split_val = split_val.decode('utf-8')
                coord_sets["split"] = str(split_val)

            # Add other set columns
            if set_columns:
                for col_name, values in set_columns.items():
                    val = values[i]
                    if isinstance(val, torch.Tensor):
                        val = val.item()
                    elif isinstance(val, bytes):
                        val = val.decode('utf-8')
                    coord_sets[col_name] = str(val)

            if coord_sets:
                coord["set_columns"] = coord_sets

            # Build string_columns
            coord_strings = {}
            if string_columns:
                for col_name, values in string_columns.items():
                    val = values[i]
                    if isinstance(val, bytes):
                        val = val.decode('utf-8')
                    coord_strings[col_name] = str(val)
            if coord_strings:
                coord["string_columns"] = coord_strings

            coords.append(coord)

        # Use 1-indexed epoch keys as per spec
        epoch_key = f"epoch_{epoch_idx + 1}"

        epoch_data = {"coords": coords}

        # Add cluster results if provided
        if cluster_results:
            formatted_clusters = {}
            for n_clusters, result in cluster_results.items():
                cluster_labels = result.get("cluster_labels", [])
                if isinstance(cluster_labels, torch.Tensor):
                    cluster_labels = cluster_labels.detach().cpu().tolist()
                elif isinstance(cluster_labels, np.ndarray):
                    cluster_labels = cluster_labels.tolist()

                formatted_clusters[str(n_clusters)] = {
                    "cluster_labels": cluster_labels,
                    "silhouette_score": float(result.get("silhouette_score", 0.0)),
                    "n_clusters": int(n_clusters),
                }
            epoch_data["entire_cluster_results"] = formatted_clusters

        self.epoch_projections[epoch_key] = epoch_data
        logger.debug(f"Added epoch {epoch_key} with {n_samples} points")

    def add_training_metrics(
        self,
        validation_loss: Optional[List[Tuple[int, float]]] = None,
        learning_rate: Optional[List[Tuple[int, float]]] = None,
        **kwargs: List[Tuple[int, float]]
    ) -> None:
        """
        Add training metrics for the loss chart visualization.

        Args:
            validation_loss: List of (epoch, value) tuples for validation loss
            learning_rate: List of (epoch, value) tuples for learning rate
            **kwargs: Additional metrics as lists of (epoch, value) tuples
        """
        if validation_loss:
            self.training_metrics["validation_loss"] = [
                {"epoch": int(epoch), "value": float(value)}
                for epoch, value in validation_loss
            ]

        if learning_rate:
            self.training_metrics["learning_rate"] = [
                {"epoch": int(epoch), "value": float(value)}
                for epoch, value in learning_rate
            ]

        for metric_name, values in kwargs.items():
            self.training_metrics[metric_name] = [
                {"epoch": int(epoch), "value": float(value)}
                for epoch, value in values
            ]

    def get_data(self) -> Dict[str, Any]:
        """
        Get the complete training movie data structure.

        Returns:
            Dict with epoch_projections and training_metrics
        """
        data = {"epoch_projections": self.epoch_projections}
        if self.training_metrics:
            data["training_metrics"] = self.training_metrics
        return data

    def save(self, filename: str = "sp_training_movie.json", output_dir: Optional[str] = None) -> str:
        """
        Save the training movie data to a JSON file.

        Args:
            filename: Name of the output file
            output_dir: Directory to save to (overrides constructor output_dir)

        Returns:
            Path to the saved file
        """
        save_dir = output_dir or self.output_dir
        if save_dir is None:
            raise ValueError("output_dir must be provided either in constructor or save()")

        os.makedirs(save_dir, exist_ok=True)
        filepath = os.path.join(save_dir, filename)

        data = self.get_data()

        from lib.utils import atomic_write_json
        atomic_write_json(filepath, data)

        n_epochs = len(self.epoch_projections)
        n_points = self._point_count or 0
        logger.info(f"📽️  Saved training movie: {filepath} ({n_epochs} epochs, {n_points} points)")

        return filepath

    def clear(self) -> None:
        """Clear all stored data to start fresh."""
        self.epoch_projections = {}
        self.training_metrics = {}
        self._point_count = None


def collect_epoch_embeddings_from_df(
    embedding_space,
    train_df: "pandas.DataFrame",
    val_df: "pandas.DataFrame",
    target_column: str,
    batch_size: int = 256,
) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Collect 3D embeddings for all samples in train and val dataframes.

    Uses the bulk encode_records_batch method for efficiency.

    Args:
        embedding_space: The EmbeddingSpace model
        train_df: Training dataframe
        val_df: Validation dataframe
        target_column: Name of the target column (for labels)
        batch_size: Batch size for encoding (default: 256)

    Returns:
        Tuple of (embeddings, labels, splits) where:
        - embeddings: numpy array of shape (n_samples, 3)
        - labels: numpy array of labels
        - splits: list of "train" or "val" for each sample
    """
    import pandas as pd

    # Combine train and val dataframes
    train_records = train_df.to_dict("records")
    val_records = val_df.to_dict("records") if val_df is not None and len(val_df) > 0 else []

    all_records = train_records + val_records

    # Build splits list
    splits = ["train"] * len(train_records) + ["val"] * len(val_records)

    # Extract labels
    train_labels = train_df[target_column].tolist() if target_column in train_df.columns else [None] * len(train_records)
    val_labels = val_df[target_column].tolist() if val_df is not None and target_column in val_df.columns else []
    labels = np.array(train_labels + val_labels)

    # Use bulk encoding - returns numpy array
    embeddings = embedding_space.encode_records_batch(
        records=all_records,
        batch_size=batch_size,
        short=True,  # Get 3D embeddings
        output_device=torch.device("cpu")
    )

    # embeddings should already be (n_samples, 3) for short=True
    if len(embeddings.shape) == 1:
        # Single sample case
        embeddings = embeddings.reshape(1, -1)

    return embeddings, labels, splits


# =============================================================================
# Inline epoch projection functions for real-time movie generation during training
# =============================================================================

EPOCH_PROJECTIONS_DIR = "epoch_projections"


class InlineMovieWriter:
    """
    Writes per-epoch projection JSON files during training using encode_records_batch.

    This replaces the async cluster_movie_renderer approach by encoding a fixed
    subsample inline at each epoch boundary, giving immediate movie frames.

    Usage:
        writer = InlineMovieWriter(output_dir="/path/to/output", target_column="label")

        # At start of training, select subsample:
        writer.initialize_subsample(train_df, val_df, max_samples=500)

        # Each epoch:
        writer.dump_epoch(embedding_space, epoch_idx)

        # After training, get combined movie:
        movie_data = writer.load_all_epochs()
    """

    def __init__(self, output_dir: Union[str, Path], target_column: str):
        self.output_dir = Path(output_dir)
        self.target_column = target_column
        self.projections_dir = self.output_dir / EPOCH_PROJECTIONS_DIR
        self.projections_dir.mkdir(parents=True, exist_ok=True)

        # Subsample state (initialized once, reused each epoch)
        self._sample_records: Optional[List[Dict]] = None
        self._sample_labels: Optional[np.ndarray] = None
        self._sample_splits: Optional[List[str]] = None
        self._sample_row_ids: Optional[List[int]] = None

        # Movement tracking state
        self._prev_embeddings: Optional[np.ndarray] = None  # Previous epoch's embeddings
        self._cumulative_distance: Optional[np.ndarray] = None  # Total distance traveled per point
        self._embedding_history: List[np.ndarray] = []  # History for net displacement calculation
        self._embedding_epochs: List[int] = []  # Epoch indices corresponding to history

    def initialize_subsample(
        self,
        train_df: "pandas.DataFrame",
        val_df: "pandas.DataFrame",
        max_samples: int = 500,
        random_state: int = 42,
    ) -> int:
        """
        Select and cache the subsample to encode each epoch.

        Args:
            train_df: Training dataframe
            val_df: Validation dataframe
            max_samples: Maximum number of samples (default 500)
            random_state: Random seed for reproducible sampling

        Returns:
            Number of samples selected
        """
        import pandas as pd

        # Combine train and val
        train_df = train_df.copy()
        val_df = val_df.copy() if val_df is not None and len(val_df) > 0 else pd.DataFrame()

        train_df["__split"] = "train"
        if len(val_df) > 0:
            val_df["__split"] = "val"
            combined_df = pd.concat([train_df, val_df], ignore_index=True)
        else:
            combined_df = train_df

        # Sample if needed
        if len(combined_df) > max_samples:
            sample_df = combined_df.sample(max_samples, random_state=random_state)
        else:
            sample_df = combined_df

        # Extract and cache
        self._sample_splits = sample_df["__split"].tolist()
        sample_df = sample_df.drop(columns=["__split"])

        self._sample_records = sample_df.to_dict("records")
        self._sample_labels = sample_df[self.target_column].values if self.target_column in sample_df.columns else np.arange(len(sample_df))
        self._sample_row_ids = list(range(len(self._sample_records)))

        # Save subsample metadata for reference
        meta_path = self.projections_dir / "subsample_meta.json"
        from lib.utils import atomic_write_json
        atomic_write_json(meta_path, {
            "n_samples": len(self._sample_records),
            "max_samples": max_samples,
            "target_column": self.target_column,
            "train_count": self._sample_splits.count("train"),
            "val_count": self._sample_splits.count("val"),
        })

        logger.info(f"Initialized inline movie subsample: {len(self._sample_records)} records")
        return len(self._sample_records)

    def _compute_movement_metrics(
        self,
        embeddings: np.ndarray,
        epoch_idx: int,
    ) -> Dict[str, Any]:
        """
        Compute movement metrics for the current epoch's embeddings.

        Metrics computed:
        1. epoch_distance: Distance each point moved from previous epoch
        2. cumulative_distance: Total distance traveled since training start
        3. net_displacement_N: Net displacement over last N epochs (5, 25, 35)

        Args:
            embeddings: Current epoch's embeddings, shape (n_samples, 3)
            epoch_idx: Current epoch number

        Returns:
            Dict with per-point and aggregate movement metrics
        """
        n_samples = len(embeddings)
        embeddings_np = embeddings if isinstance(embeddings, np.ndarray) else embeddings.numpy()

        # Initialize tracking arrays on first call
        if self._cumulative_distance is None:
            self._cumulative_distance = np.zeros(n_samples, dtype=np.float64)

        # Calculate distance from previous epoch
        epoch_distance = np.zeros(n_samples, dtype=np.float64)
        if self._prev_embeddings is not None:
            # Euclidean distance between current and previous positions
            diff = embeddings_np - self._prev_embeddings
            epoch_distance = np.linalg.norm(diff, axis=1)
            self._cumulative_distance += epoch_distance

        # Store current embeddings in history for net displacement calculation
        self._embedding_history.append(embeddings_np.copy())
        self._embedding_epochs.append(epoch_idx)

        # Keep history bounded (only need last 35 epochs worth)
        max_history = 40  # Slightly more than 35 to be safe
        if len(self._embedding_history) > max_history:
            self._embedding_history.pop(0)
            self._embedding_epochs.pop(0)

        # Calculate net displacement over windows (5, 25, 35 epochs)
        net_displacement = {}
        for window in [5, 25, 35]:
            # Find the embedding from ~window epochs ago
            target_epoch = epoch_idx - window
            displacement = np.zeros(n_samples, dtype=np.float64)

            # Search history for closest epoch
            if len(self._embedding_history) > 1:
                for i, hist_epoch in enumerate(self._embedding_epochs):
                    if hist_epoch <= target_epoch:
                        # Found an epoch at or before target, use this one
                        old_embeddings = self._embedding_history[i]
                        displacement = np.linalg.norm(embeddings_np - old_embeddings, axis=1)
                        break
                else:
                    # No epoch old enough found, use oldest available
                    if len(self._embedding_history) >= 2:
                        old_embeddings = self._embedding_history[0]
                        displacement = np.linalg.norm(embeddings_np - old_embeddings, axis=1)

            net_displacement[window] = displacement

        # Update previous embeddings for next epoch
        self._prev_embeddings = embeddings_np.copy()

        # Build metrics dict with per-point arrays and aggregates
        return {
            "epoch_distance": epoch_distance,  # Distance moved this epoch (per point)
            "cumulative_distance": self._cumulative_distance.copy(),  # Total distance traveled (per point)
            "net_displacement_5": net_displacement[5],  # Net displacement over last 5 epochs
            "net_displacement_25": net_displacement[25],  # Net displacement over last 25 epochs
            "net_displacement_35": net_displacement[35],  # Net displacement over last 35 epochs
            # Aggregate statistics
            "mean_epoch_distance": float(np.mean(epoch_distance)),
            "mean_cumulative_distance": float(np.mean(self._cumulative_distance)),
            "mean_net_displacement_5": float(np.mean(net_displacement[5])),
            "mean_net_displacement_25": float(np.mean(net_displacement[25])),
            "mean_net_displacement_35": float(np.mean(net_displacement[35])),
            "std_epoch_distance": float(np.std(epoch_distance)),
            "std_cumulative_distance": float(np.std(self._cumulative_distance)),
        }

    def dump_epoch(
        self,
        embedding_space,
        epoch_idx: int,
        batch_size: int = 256,
    ) -> Optional[str]:
        """
        Encode subsample and write single epoch projection JSON.

        Args:
            embedding_space: The EmbeddingSpace with encode_records_batch method
            epoch_idx: Current epoch number (0-indexed)
            batch_size: Batch size for encoding

        Returns:
            Path to written JSON file, or None on error
        """
        if self._sample_records is None:
            logger.warning("InlineMovieWriter: subsample not initialized, skipping epoch dump")
            return None

        import time as time_module
        frame_start = time_module.time()

        try:
            # Encode subsample - get 3D short embeddings
            encode_start = time_module.time()
            embeddings = embedding_space.encode_records_batch(
                records=self._sample_records,
                batch_size=batch_size,
                short=True,
                output_device=torch.device("cpu"),
            )
            encode_time = time_module.time() - encode_start

            # Convert to numpy for movement calculations
            embeddings_np = embeddings.numpy() if isinstance(embeddings, torch.Tensor) else embeddings

            # Compute movement metrics (distance traveled, net displacement)
            movement_metrics = self._compute_movement_metrics(embeddings_np, epoch_idx)

            # Build epoch data structure (compatible with viewer format)
            coords = []
            for i in range(len(embeddings)):
                coord = {
                    "0": float(embeddings[i, 0]),
                    "1": float(embeddings[i, 1]),
                    "2": float(embeddings[i, 2]),
                    "__featrix_row_offset": i,
                    "__featrix_row_id": self._sample_row_ids[i],
                    "set_columns": {
                        "label": str(self._sample_labels[i]),
                        "split": self._sample_splits[i],
                    },
                    # Per-point movement metrics
                    "scalar_columns": {
                        "epoch_distance": float(movement_metrics["epoch_distance"][i]),
                        "cumulative_distance": float(movement_metrics["cumulative_distance"][i]),
                        "net_displacement_5": float(movement_metrics["net_displacement_5"][i]),
                        "net_displacement_25": float(movement_metrics["net_displacement_25"][i]),
                        "net_displacement_35": float(movement_metrics["net_displacement_35"][i]),
                    },
                }
                coords.append(coord)

            epoch_data = {
                "epoch": epoch_idx,  # API expects 'epoch' key for compatibility
                "epoch_idx": epoch_idx,
                "epoch_key": f"epoch_{epoch_idx + 1}",
                "n_samples": len(coords),
                "coords": coords,
                # Aggregate movement metrics for the epoch
                "movement_metrics": {
                    "mean_epoch_distance": movement_metrics["mean_epoch_distance"],
                    "mean_cumulative_distance": movement_metrics["mean_cumulative_distance"],
                    "mean_net_displacement_5": movement_metrics["mean_net_displacement_5"],
                    "mean_net_displacement_25": movement_metrics["mean_net_displacement_25"],
                    "mean_net_displacement_35": movement_metrics["mean_net_displacement_35"],
                    "std_epoch_distance": movement_metrics["std_epoch_distance"],
                    "std_cumulative_distance": movement_metrics["std_cumulative_distance"],
                },
            }

            # Write to file atomically
            filename = f"projections_epoch_{epoch_idx + 1:04d}.json"
            filepath = self.projections_dir / filename
            from lib.utils import atomic_write_json
            atomic_write_json(filepath, epoch_data, indent=0)  # No indent for speed

            frame_time = time_module.time() - frame_start
            logger.info(f"🎬 Movie frame epoch {epoch_idx + 1}: {frame_time:.2f}s total (encode={encode_time:.2f}s, {len(self._sample_records)} samples)")
            return str(filepath)

        except Exception as e:
            logger.warning(f"⚠️  Failed to dump epoch {epoch_idx} projections: {e}")
            logger.warning(f"    Traceback: {traceback.format_exc()}")
            return None

    def load_all_epochs(self, include_metrics: bool = False) -> Dict[str, Any]:
        """
        Load all epoch projection files and combine into single movie structure.

        Args:
            include_metrics: If True, also load training_metrics.json if present

        Returns:
            Dict with epoch_projections (and optionally training_metrics)
        """
        return load_all_epoch_projections(self.output_dir, include_metrics=include_metrics)


def load_all_epoch_projections(
    output_dir: Union[str, Path],
    include_metrics: bool = False,
) -> Dict[str, Any]:
    """
    Load all per-epoch projection JSONs and combine into single movie structure.

    This is the API call to get all epochs at once, compatible with the viewer's
    expected sp_training_movie.json format.

    Args:
        output_dir: Directory containing epoch_projections/ subdirectory
        include_metrics: If True, also load training_metrics.json if present

    Returns:
        Dict with:
            - epoch_projections: {epoch_1: {coords: [...]}, epoch_2: {...}, ...}
            - training_metrics: {...} (if include_metrics and file exists)
    """
    output_dir = Path(output_dir)
    projections_dir = output_dir / EPOCH_PROJECTIONS_DIR

    if not projections_dir.exists():
        logger.warning(f"No epoch_projections directory found at {projections_dir}")
        return {"epoch_projections": {}}

    # Find all projection files
    projection_files = sorted(projections_dir.glob("projections_epoch_*.json"))

    epoch_projections = {}
    for filepath in projection_files:
        try:
            with open(filepath, 'r') as f:
                epoch_data = json.load(f)

            epoch_key = epoch_data.get("epoch_key", filepath.stem.replace("projections_", ""))
            # Store just coords (viewer format)
            epoch_projections[epoch_key] = {"coords": epoch_data["coords"]}

        except Exception as e:
            logger.warning(f"Failed to load {filepath}: {e}")

    result = {"epoch_projections": epoch_projections}

    # Optionally include training metrics
    if include_metrics:
        metrics_path = output_dir / "training_metrics.json"
        if metrics_path.exists():
            try:
                with open(metrics_path, 'r') as f:
                    result["training_metrics"] = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load training metrics: {e}")

    logger.info(f"Loaded {len(epoch_projections)} epoch projections from {projections_dir}")
    return result


def save_training_metrics(
    output_dir: Union[str, Path],
    validation_loss: Optional[List[Tuple[int, float]]] = None,
    learning_rate: Optional[List[Tuple[int, float]]] = None,
    **kwargs: List[Tuple[int, float]],
) -> str:
    """
    Save training metrics to a separate JSON file (for use with load_all_epoch_projections).

    Args:
        output_dir: Output directory
        validation_loss: List of (epoch, value) tuples
        learning_rate: List of (epoch, value) tuples
        **kwargs: Additional metrics

    Returns:
        Path to saved file
    """
    output_dir = Path(output_dir)
    metrics = {}

    if validation_loss:
        metrics["validation_loss"] = [
            {"epoch": int(e), "value": float(v)} for e, v in validation_loss if v is not None
        ]
    if learning_rate:
        metrics["learning_rate"] = [
            {"epoch": int(e), "value": float(v)} for e, v in learning_rate if v is not None
        ]
    for name, values in kwargs.items():
        metrics[name] = [
            {"epoch": int(e), "value": float(v)} for e, v in values if v is not None
        ]

    filepath = output_dir / "training_metrics.json"
    from lib.utils import atomic_write_json
    atomic_write_json(filepath, metrics)

    return str(filepath)


# =============================================================================
# Legacy convenience functions
# =============================================================================

# Convenience function for quick epoch dumps
def dump_epoch_embeddings(
    output_path: str,
    epoch_idx: int,
    embeddings: Union[torch.Tensor, np.ndarray],
    labels: Union[torch.Tensor, np.ndarray, List],
    splits: Optional[List[str]] = None,
) -> None:
    """
    Quick utility to dump a single epoch's embeddings to JSON.

    This creates a minimal training movie file with just one epoch,
    useful for debugging or single-epoch analysis.

    Args:
        output_path: Full path to output JSON file
        epoch_idx: Epoch number
        embeddings: 3D embeddings (n_samples, 3)
        labels: Labels for each sample
        splits: Optional "train"/"val" for each sample
    """
    writer = TrainingMovieWriter()
    writer.add_epoch(
        epoch_idx=epoch_idx,
        embeddings=embeddings,
        labels=labels,
        splits=splits,
    )

    output_dir = os.path.dirname(output_path)
    filename = os.path.basename(output_path)

    if output_dir:
        writer.save(filename=filename, output_dir=output_dir)
    else:
        writer.save(filename=filename, output_dir=".")
