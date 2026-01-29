#!/usr/bin/env python3
"""
Per-Epoch Cluster Cohesion Tracker

Tracks how cluster structure evolves during ES training by comparing
K-means clustering on raw features vs ES embeddings at each epoch.

Usage:
    from featrix.neural.cluster_cohesion_tracker import ClusterCohesionTracker

    tracker = ClusterCohesionTracker(raw_features, k_values=[3, 5, 7, 9])

    # During training loop:
    for epoch in range(n_epochs):
        es.train_one_epoch()
        embeddings = es.encode_batch(samples)
        tracker.record_epoch(epoch, embeddings)

    # After training:
    tracker.save_results("cluster_cohesion.json")
    tracker.generate_movie("cluster_cohesion_movie.gif")
"""

import json
import logging
import numpy as np
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from scipy.optimize import linear_sum_assignment
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler, OneHotEncoder

logger = logging.getLogger(__name__)


@dataclass
class EpochCohesionMetrics:
    """Metrics for a single epoch and K value."""
    epoch: int
    k: int
    raw_silhouette: float
    es_silhouette: float
    silhouette_improvement: float
    jaccard_mean: float
    jaccard_std: float
    jaccard_per_cluster: List[float]
    matched_pairs: List[Tuple[int, int]]
    raw_cluster_sizes: List[int]
    es_cluster_sizes: List[int]
    # Context-aligned metrics (optional, may be None for backward compat)
    missingness_jaccard: Optional[float] = None  # Jaccard between missingness clusters and ES clusters
    neighbor_preservation: Optional[float] = None  # Fraction of k-NN preserved in embedding space


@dataclass
class ClusterCohesionHistory:
    """Full history of cluster cohesion across epochs."""
    k_values: List[int]
    n_samples: int
    raw_feature_dim: int
    embedding_dim: int
    epochs: List[int] = field(default_factory=list)
    metrics: Dict[int, List[EpochCohesionMetrics]] = field(default_factory=dict)  # k -> list of epoch metrics

    def to_dict(self):
        """Convert to JSON-serializable dict."""
        return {
            'k_values': self.k_values,
            'n_samples': self.n_samples,
            'raw_feature_dim': self.raw_feature_dim,
            'embedding_dim': self.embedding_dim,
            'epochs': self.epochs,
            'metrics': {
                str(k): [asdict(m) for m in metrics_list]
                for k, metrics_list in self.metrics.items()
            }
        }


class ClusterCohesionTracker:
    """
    Tracks cluster cohesion between raw features and ES embeddings across epochs.

    This allows correlating cluster structure changes with training metrics like
    loss, AUC, etc.
    """

    def __init__(
        self,
        raw_features: np.ndarray,
        k_values: List[int] = [3, 5, 7, 9, 11, 13],
        random_state: int = 42,
        missingness_mask: Optional[np.ndarray] = None,
        n_neighbors_for_preservation: int = 10
    ):
        """
        Initialize tracker with raw feature data.

        Args:
            raw_features: Pre-processed raw features (n_samples, n_features)
            k_values: List of K values for K-means clustering
            random_state: Random seed for reproducibility
            missingness_mask: Optional boolean mask (n_samples, n_cols) where True = missing.
                              If provided, enables context-aligned metrics.
            n_neighbors_for_preservation: K for k-NN neighbor preservation metric
        """
        self.raw_features = raw_features
        self.k_values = [k for k in k_values if k < len(raw_features)]
        self.random_state = random_state
        self.n_samples = len(raw_features)
        self.n_neighbors = n_neighbors_for_preservation

        # Pre-compute raw clustering for each K (doesn't change)
        self._raw_labels = {}
        self._raw_silhouettes = {}
        self._raw_cluster_sets = {}

        logger.info(f"🔍 ClusterCohesionTracker: Pre-computing raw clustering for K={self.k_values}")
        for k in self.k_values:
            kmeans = KMeans(n_clusters=k, random_state=random_state, n_init=10)
            labels = kmeans.fit_predict(raw_features)
            self._raw_labels[k] = labels
            self._raw_silhouettes[k] = silhouette_score(raw_features, labels)
            self._raw_cluster_sets[k] = {i: set(np.where(labels == i)[0]) for i in range(k)}

        # Pre-compute missingness clustering if mask provided
        self._missingness_labels = {}
        self._missingness_cluster_sets = {}
        if missingness_mask is not None:
            self.missingness_mask = missingness_mask
            logger.info(f"🔍 ClusterCohesionTracker: Pre-computing missingness pattern clustering")
            for k in self.k_values:
                # Cluster by missingness pattern (binary vectors)
                kmeans = KMeans(n_clusters=k, random_state=random_state, n_init=10)
                labels = kmeans.fit_predict(missingness_mask.astype(float))
                self._missingness_labels[k] = labels
                self._missingness_cluster_sets[k] = {i: set(np.where(labels == i)[0]) for i in range(k)}
        else:
            self.missingness_mask = None

        # Pre-compute raw space k-NN for neighbor preservation metric
        self._raw_knn = None
        if self.n_samples > self.n_neighbors:
            from sklearn.neighbors import NearestNeighbors
            nn = NearestNeighbors(n_neighbors=self.n_neighbors + 1, algorithm='auto')
            nn.fit(raw_features)
            # Get indices of k nearest neighbors (excluding self)
            _, indices = nn.kneighbors(raw_features)
            self._raw_knn = indices[:, 1:]  # Exclude self (first column)
            logger.info(f"🔍 ClusterCohesionTracker: Pre-computed {self.n_neighbors}-NN for neighbor preservation")

        # Initialize history
        self.history = ClusterCohesionHistory(
            k_values=self.k_values,
            n_samples=self.n_samples,
            raw_feature_dim=raw_features.shape[1],
            embedding_dim=0  # Set on first record
        )

        # Store jaccard matrices for movie generation
        self._jaccard_matrices = {}  # (epoch, k) -> matrix

    def record_epoch(self, epoch: int, embeddings: np.ndarray) -> Dict[int, EpochCohesionMetrics]:
        """
        Record cluster cohesion metrics for this epoch.

        Args:
            epoch: Current epoch number
            embeddings: ES embeddings for the same samples (n_samples, embedding_dim)

        Returns:
            Dict mapping K -> metrics for this epoch
        """
        if len(embeddings) != self.n_samples:
            logger.warning(f"⚠️  Sample count mismatch: expected {self.n_samples}, got {len(embeddings)}")
            return {}

        if self.history.embedding_dim == 0:
            self.history.embedding_dim = embeddings.shape[1]

        self.history.epochs.append(epoch)
        epoch_metrics = {}

        # Compute neighbor preservation once per epoch (not per K)
        neighbor_preservation = self._compute_neighbor_preservation(embeddings)

        for k in self.k_values:
            # Cluster embeddings
            es_kmeans = KMeans(n_clusters=k, random_state=self.random_state, n_init=10)
            es_labels = es_kmeans.fit_predict(embeddings)
            es_sil = silhouette_score(embeddings, es_labels)

            # Build ES cluster sets
            es_sets = {i: set(np.where(es_labels == i)[0]) for i in range(k)}

            # Compute Jaccard matrix (raw vs ES)
            jaccard_matrix = np.zeros((k, k))
            for i in range(k):
                for j in range(k):
                    raw_set = self._raw_cluster_sets[k][i]
                    es_set = es_sets[j]
                    intersection = len(raw_set & es_set)
                    union = len(raw_set | es_set)
                    jaccard_matrix[i, j] = intersection / union if union > 0 else 0

            # Store for movie
            self._jaccard_matrices[(epoch, k)] = jaccard_matrix.copy()

            # Optimal 1:1 matching
            row_ind, col_ind = linear_sum_assignment(-jaccard_matrix)
            matched_jaccards = [jaccard_matrix[i, j] for i, j in zip(row_ind, col_ind)]

            # Compute missingness-aligned Jaccard if available
            missingness_jaccard = None
            if self._missingness_cluster_sets:
                miss_jaccard_matrix = np.zeros((k, k))
                for i in range(k):
                    for j in range(k):
                        miss_set = self._missingness_cluster_sets[k][i]
                        es_set = es_sets[j]
                        intersection = len(miss_set & es_set)
                        union = len(miss_set | es_set)
                        miss_jaccard_matrix[i, j] = intersection / union if union > 0 else 0
                miss_row_ind, miss_col_ind = linear_sum_assignment(-miss_jaccard_matrix)
                miss_matched = [miss_jaccard_matrix[i, j] for i, j in zip(miss_row_ind, miss_col_ind)]
                missingness_jaccard = float(np.mean(miss_matched))

            metrics = EpochCohesionMetrics(
                epoch=epoch,
                k=k,
                raw_silhouette=self._raw_silhouettes[k],
                es_silhouette=es_sil,
                silhouette_improvement=es_sil - self._raw_silhouettes[k],
                jaccard_mean=np.mean(matched_jaccards),
                jaccard_std=np.std(matched_jaccards),
                jaccard_per_cluster=matched_jaccards,
                matched_pairs=list(zip(row_ind.tolist(), col_ind.tolist())),
                raw_cluster_sizes=[len(self._raw_cluster_sets[k][i]) for i in range(k)],
                es_cluster_sizes=[len(es_sets[i]) for i in range(k)],
                missingness_jaccard=missingness_jaccard,
                neighbor_preservation=neighbor_preservation
            )

            epoch_metrics[k] = metrics

            # Store in history
            if k not in self.history.metrics:
                self.history.metrics[k] = []
            self.history.metrics[k].append(metrics)

        return epoch_metrics

    def _compute_neighbor_preservation(self, embeddings: np.ndarray) -> Optional[float]:
        """
        Compute what fraction of raw-space k-NN are preserved in embedding space.

        This measures whether rows that were close in raw feature space remain
        close in embedding space - a proxy for structure preservation.

        Returns:
            Fraction of neighbors preserved (0 to 1), or None if not computable
        """
        if self._raw_knn is None:
            return None

        from sklearn.neighbors import NearestNeighbors

        # Find k-NN in embedding space
        nn = NearestNeighbors(n_neighbors=self.n_neighbors + 1, algorithm='auto')
        nn.fit(embeddings)
        _, es_indices = nn.kneighbors(embeddings)
        es_knn = es_indices[:, 1:]  # Exclude self

        # For each sample, count how many of its raw-space neighbors are also
        # among its embedding-space neighbors
        preserved_count = 0
        total_count = 0

        for i in range(self.n_samples):
            raw_neighbors = set(self._raw_knn[i])
            es_neighbors = set(es_knn[i])
            preserved_count += len(raw_neighbors & es_neighbors)
            total_count += len(raw_neighbors)

        return preserved_count / total_count if total_count > 0 else None

    def log_epoch_summary(self, epoch: int, epoch_metrics: Dict[int, EpochCohesionMetrics]):
        """Log a compact summary for this epoch."""
        if not epoch_metrics:
            return

        # Pick a representative K (middle value)
        k = self.k_values[len(self.k_values) // 2]
        m = epoch_metrics.get(k)
        if m:
            # Build context-aligned metrics string if available
            context_str = ""
            if m.neighbor_preservation is not None:
                context_str += f", kNN={m.neighbor_preservation:.3f}"
            if m.missingness_jaccard is not None:
                context_str += f", MissJac={m.missingness_jaccard:.3f}"

            logger.info(
                f"📊 Cluster cohesion [e={epoch:03d}] K={k}: "
                f"Sil={m.es_silhouette:.3f} (Δ{m.silhouette_improvement:+.3f}), "
                f"RawJac={m.jaccard_mean:.3f}{context_str}"
            )

    def get_summary_for_epoch(self, epoch: int) -> Optional[Dict]:
        """Get summary metrics for charting/logging."""
        summary = {}
        for k in self.k_values:
            if k in self.history.metrics:
                for m in self.history.metrics[k]:
                    if m.epoch == epoch:
                        summary[f'cluster_sil_k{k}'] = m.es_silhouette
                        summary[f'cluster_sil_improvement_k{k}'] = m.silhouette_improvement
                        summary[f'cluster_jaccard_k{k}'] = m.jaccard_mean
                        summary[f'cluster_jaccard_std_k{k}'] = m.jaccard_std
                        if m.neighbor_preservation is not None:
                            summary[f'neighbor_preservation_k{k}'] = m.neighbor_preservation
                        if m.missingness_jaccard is not None:
                            summary[f'missingness_jaccard_k{k}'] = m.missingness_jaccard
                        break
        return summary if summary else None

    def save_results(self, path: str):
        """Save full history to JSON."""
        with open(path, 'w') as f:
            json.dump(self.history.to_dict(), f, indent=2)
        logger.info(f"💾 Saved cluster cohesion history to {path}")

    def log_final_report(self):
        """Log a comprehensive final clustering report at end of training."""
        if not self.history.epochs:
            logger.info("📊 No cluster cohesion data recorded during training")
            return

        logger.info("")
        logger.info("=" * 100)
        logger.info("📊 CLUSTER COHESION FINAL REPORT")
        logger.info("=" * 100)
        logger.info(f"   Samples tracked: {self.n_samples}")
        logger.info(f"   Raw feature dim: {self.history.raw_feature_dim}")
        logger.info(f"   Embedding dim: {self.history.embedding_dim}")
        logger.info(f"   Epochs tracked: {len(self.history.epochs)} ({self.history.epochs[0]} to {self.history.epochs[-1]})")
        logger.info("")

        # Get final epoch metrics
        final_epoch = self.history.epochs[-1]

        # Table header - show Jaccard lift vs random (1/K baseline)
        logger.info("┌─────────┬─────────────┬─────────────┬─────────────┬─────────────┬─────────────┐")
        logger.info("│    K    │  Raw Sil.   │   ES Sil.   │  Sil. Δ     │ Jac vs Rand │   kNN Pres. │")
        logger.info("├─────────┼─────────────┼─────────────┼─────────────┼─────────────┼─────────────┤")

        for k in self.k_values:
            if k in self.history.metrics and self.history.metrics[k]:
                # Get final metrics for this K
                final_m = None
                for m in self.history.metrics[k]:
                    if m.epoch == final_epoch:
                        final_m = m
                        break

                if final_m:
                    knn_str = f"{final_m.neighbor_preservation:.3f}" if final_m.neighbor_preservation is not None else "N/A"
                    # Compute Jaccard lift vs random baseline (1/K)
                    random_baseline = 1.0 / k
                    jaccard_lift = final_m.jaccard_mean / random_baseline
                    logger.info(
                        f"│   {k:3d}   │    {final_m.raw_silhouette:+.3f}   │    {final_m.es_silhouette:+.3f}   │"
                        f"    {final_m.silhouette_improvement:+.3f}   │    {jaccard_lift:5.2f}×    │     {knn_str:>5}   │"
                    )

        logger.info("└─────────┴─────────────┴─────────────┴─────────────┴─────────────┴─────────────┘")

        # Summary interpretation
        logger.info("")

        # Calculate average improvements across K values
        sil_improvements = []
        knn_preservations = []
        for k in self.k_values:
            if k in self.history.metrics and self.history.metrics[k]:
                for m in self.history.metrics[k]:
                    if m.epoch == final_epoch:
                        sil_improvements.append(m.silhouette_improvement)
                        if m.neighbor_preservation is not None:
                            knn_preservations.append(m.neighbor_preservation)
                        break

        if sil_improvements:
            avg_sil_improvement = np.mean(sil_improvements)
            if avg_sil_improvement > 0.05:
                logger.info(f"   ✅ Embedding improves cluster separation (avg Δ={avg_sil_improvement:+.3f})")
            elif avg_sil_improvement < -0.05:
                logger.info(f"   ⚠️  Embedding reduces cluster separation (avg Δ={avg_sil_improvement:+.3f})")
            else:
                logger.info(f"   ℹ️  Embedding has similar cluster separation (avg Δ={avg_sil_improvement:+.3f})")

        if knn_preservations:
            avg_knn = np.mean(knn_preservations)
            if avg_knn > 0.3:
                logger.info(f"   ✅ Good neighbor preservation ({avg_knn:.1%} of k-NN preserved)")
            elif avg_knn > 0.15:
                logger.info(f"   ⚠️  Moderate neighbor preservation ({avg_knn:.1%} of k-NN preserved)")
            else:
                logger.info(f"   ⚠️  Low neighbor preservation ({avg_knn:.1%} of k-NN preserved)")
                logger.info(f"      Note: Low preservation is expected if embedding learns context-based relationships")

        logger.info("")
        logger.info("   Metric Explanations:")
        logger.info("   • Silhouette: Cluster separation quality (-1 to 1, higher = better separated)")
        logger.info("   • Sil. Δ: Change from raw features to embedding (positive = embedding improves clustering)")
        logger.info("   • Jac vs Rand: Jaccard similarity vs random baseline (>1× = better than random, <1× = worse)")
        logger.info("   • kNN Pres.: Fraction of k-nearest neighbors preserved in embedding space")
        logger.info("=" * 100)

    def generate_timeline_plot(self, output_path: str):
        """Generate a timeline plot showing metrics across epochs."""
        import matplotlib.pyplot as plt

        if not self.history.epochs:
            logger.warning("No epochs recorded yet")
            return

        fig, axes = plt.subplots(2, 2, figsize=(14, 10))

        epochs = self.history.epochs

        # Plot 1: Silhouette over time for each K
        ax = axes[0, 0]
        for k in self.k_values:
            if k in self.history.metrics:
                sils = [m.es_silhouette for m in self.history.metrics[k]]
                ax.plot(epochs[:len(sils)], sils, '-o', label=f'K={k}', markersize=3)
        ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
        ax.set_xlabel('Epoch')
        ax.set_ylabel('ES Silhouette Score')
        ax.set_title('Cluster Separation Quality Over Training')
        ax.legend()
        ax.grid(True, alpha=0.3)

        # Plot 2: Silhouette improvement over time
        ax = axes[0, 1]
        for k in self.k_values:
            if k in self.history.metrics:
                imps = [m.silhouette_improvement for m in self.history.metrics[k]]
                ax.plot(epochs[:len(imps)], imps, '-o', label=f'K={k}', markersize=3)
        ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
        ax.set_xlabel('Epoch')
        ax.set_ylabel('Silhouette Improvement (ES - Raw)')
        ax.set_title('Cluster Separation Improvement Over Training')
        ax.legend()
        ax.grid(True, alpha=0.3)

        # Plot 3: Jaccard mean over time
        ax = axes[1, 0]
        for k in self.k_values:
            if k in self.history.metrics:
                jacs = [m.jaccard_mean for m in self.history.metrics[k]]
                ax.plot(epochs[:len(jacs)], jacs, '-o', label=f'K={k}', markersize=3)
        ax.set_xlabel('Epoch')
        ax.set_ylabel('Jaccard Similarity (Mean)')
        ax.set_title('Cluster Membership Overlap Over Training')
        ax.set_ylim(0, 1)
        ax.legend()
        ax.grid(True, alpha=0.3)

        # Plot 4: Jaccard std over time (variance in matching quality)
        ax = axes[1, 1]
        for k in self.k_values:
            if k in self.history.metrics:
                stds = [m.jaccard_std for m in self.history.metrics[k]]
                ax.plot(epochs[:len(stds)], stds, '-o', label=f'K={k}', markersize=3)
        ax.set_xlabel('Epoch')
        ax.set_ylabel('Jaccard Std Dev')
        ax.set_title('Cluster Match Variance Over Training')
        ax.legend()
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        fig.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        logger.info(f"📈 Saved timeline plot to {output_path}")

    def dump_to_directory(self, output_dir: str):
        """
        Dump all cluster cohesion data to a directory.

        Creates:
            - cluster_cohesion.json: Full history data
            - timeline_plot.png: Metrics over epochs
            - jaccard_heatmap_k{K}.gif: Animated heatmaps for each K
            - per_epoch/epoch_{N}_k{K}.json: Individual epoch data

        Args:
            output_dir: Directory to save all outputs
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # 1. Save full JSON history
        json_path = output_path / "cluster_cohesion.json"
        self.save_results(str(json_path))

        # 2. Generate timeline plot
        timeline_path = output_path / "timeline_plot.png"
        self.generate_timeline_plot(str(timeline_path))

        # 3. Generate heatmap movies for each K
        for k in self.k_values:
            movie_path = output_path / f"jaccard_heatmap_k{k}.gif"
            self.generate_heatmap_movie(str(movie_path), k=k)

        # 4. Save per-epoch detailed data
        per_epoch_dir = output_path / "per_epoch"
        per_epoch_dir.mkdir(exist_ok=True)

        for epoch in self.history.epochs:
            for k in self.k_values:
                if (epoch, k) in self._jaccard_matrices:
                    epoch_data = {
                        'epoch': epoch,
                        'k': k,
                        'jaccard_matrix': self._jaccard_matrices[(epoch, k)].tolist()
                    }
                    # Add metrics if available
                    for m in self.history.metrics.get(k, []):
                        if m.epoch == epoch:
                            epoch_data.update(asdict(m))
                            break

                    epoch_file = per_epoch_dir / f"epoch_{epoch:04d}_k{k}.json"
                    with open(epoch_file, 'w') as f:
                        json.dump(epoch_data, f, indent=2)

        logger.info(f"📁 Dumped all cluster cohesion data to {output_dir}")
        logger.info(f"   - {json_path.name}")
        logger.info(f"   - {timeline_path.name}")
        logger.info(f"   - {len(self.k_values)} heatmap movies")
        logger.info(f"   - {len(list(per_epoch_dir.glob('*.json')))} per-epoch files")

    def generate_heatmap_movie(self, output_path: str, k: int = None, fps: float = 2.0):
        """
        Generate animated GIF of Jaccard heatmaps over epochs.

        Args:
            output_path: Output path for GIF
            k: K value to use (default: middle K)
            fps: Frames per second
        """
        import matplotlib.pyplot as plt
        import matplotlib.animation as animation

        if k is None:
            k = self.k_values[len(self.k_values) // 2]

        if k not in self.k_values:
            logger.warning(f"K={k} not in tracked values {self.k_values}")
            return

        # Get all epochs with this K
        epochs_with_k = [e for e in self.history.epochs if (e, k) in self._jaccard_matrices]
        if not epochs_with_k:
            logger.warning(f"No Jaccard matrices recorded for K={k}")
            return

        fig, ax = plt.subplots(figsize=(10, 8))

        def animate(frame_idx):
            ax.clear()
            epoch = epochs_with_k[frame_idx]
            jm = self._jaccard_matrices[(epoch, k)]

            # Get metrics for this epoch
            metrics = None
            for m in self.history.metrics.get(k, []):
                if m.epoch == epoch:
                    metrics = m
                    break

            im = ax.imshow(jm, cmap='YlOrRd', aspect='equal', vmin=0, vmax=1)

            # Add text annotations
            for i in range(k):
                for j in range(k):
                    val = jm[i, j]
                    color = 'white' if val > 0.5 else 'black'
                    ax.text(j, i, f'{val:.2f}', ha='center', va='center',
                           fontsize=max(8, 14 - k), color=color, fontweight='bold')

            ax.set_xticks(range(k))
            ax.set_yticks(range(k))

            if metrics:
                ax.set_xticklabels([f'ES[{j}]\n(n={metrics.es_cluster_sizes[j]})' for j in range(k)], fontsize=9)
                ax.set_yticklabels([f'Raw[{i}] (n={metrics.raw_cluster_sizes[i]})' for i in range(k)], fontsize=9)
                title = (f'Epoch {epoch}: Jaccard Matrix K={k}\n'
                        f'Mean: {metrics.jaccard_mean:.3f} ± {metrics.jaccard_std:.3f}  |  '
                        f'Sil Δ: {metrics.silhouette_improvement:+.3f}')
            else:
                ax.set_xticklabels([f'ES[{j}]' for j in range(k)], fontsize=9)
                ax.set_yticklabels([f'Raw[{i}]' for i in range(k)], fontsize=9)
                title = f'Epoch {epoch}: Jaccard Matrix K={k}'

            ax.set_xlabel('ES Embedding Clusters', fontsize=12)
            ax.set_ylabel('Raw Feature Clusters', fontsize=12)
            ax.set_title(title, fontsize=12, fontweight='bold')

            if frame_idx == 0 and not hasattr(animate, 'cbar'):
                animate.cbar = fig.colorbar(im, ax=ax, label='Jaccard Similarity')

            return [im]

        anim = animation.FuncAnimation(
            fig, animate,
            frames=len(epochs_with_k),
            interval=1000 / fps,
            blit=False
        )

        try:
            anim.save(output_path, writer='pillow', fps=fps)
            logger.info(f"🎬 Saved heatmap movie to {output_path}")
        except Exception as e:
            logger.warning(f"⚠️  Could not save GIF: {e}")

        plt.close(fig)


def prepare_raw_features(df, ignore_cols: List[str] = None) -> np.ndarray:
    """
    Prepare raw features from a DataFrame for cluster comparison.

    Handles numeric scaling and categorical one-hot encoding.

    Args:
        df: Input DataFrame
        ignore_cols: Columns to exclude (e.g., target column)

    Returns:
        Processed feature matrix (n_samples, n_features)
    """
    ignore_cols = ignore_cols or []
    df_features = df.drop(columns=[c for c in ignore_cols if c in df.columns], errors='ignore')

    # Identify column types
    numeric_cols = df_features.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df_features.select_dtypes(include=['object', 'category']).columns.tolist()

    processed_parts = []

    if numeric_cols:
        numeric_data = df_features[numeric_cols].fillna(0).values
        scaler = StandardScaler()
        numeric_data = scaler.fit_transform(numeric_data)
        processed_parts.append(numeric_data)

    if categorical_cols:
        categorical_data = df_features[categorical_cols].astype(str).fillna('__MISSING__')
        encoder = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
        categorical_encoded = encoder.fit_transform(categorical_data)
        processed_parts.append(categorical_encoded)

    if not processed_parts:
        raise ValueError("No features to process")

    return np.hstack(processed_parts)


def run_cohesion_check(
    es,
    df,
    epoch_idx: int,
    tracker: Optional[ClusterCohesionTracker] = None,
    sample_size: int = 2000,
    k_values: List[int] = None,
    ignore_cols: List[str] = None,
    random_state: int = 42
) -> Optional[ClusterCohesionTracker]:
    """
    Run cluster cohesion check during ES training.

    This is the main entry point for integrating cohesion tracking into training.
    Call this periodically (e.g., every 5 epochs) to track how cluster structure
    evolves during training.

    Args:
        es: EmbeddingSpace instance (must have encode_record method)
        df: DataFrame with training data
        epoch_idx: Current epoch number
        tracker: Existing tracker (None on first call, reuse on subsequent calls)
        sample_size: Max rows to sample for efficiency
        k_values: K values for clustering (default: [3, 5, 7, 9, 11, 13])
        ignore_cols: Columns to ignore (e.g., target column)
        random_state: Random seed

    Returns:
        ClusterCohesionTracker instance (pass back on next call)
    """
    import torch

    if k_values is None:
        k_values = [3, 5, 7, 9, 11, 13]

    ignore_cols = ignore_cols or []
    if hasattr(es, 'target_column') and es.target_column:
        ignore_cols = list(set(ignore_cols + [es.target_column]))

    try:
        # Sample if needed
        if len(df) > sample_size:
            df_sample = df.sample(n=sample_size, random_state=random_state)
            sample_indices = df_sample.index.tolist()
        else:
            df_sample = df
            sample_indices = list(range(len(df)))

        # Initialize tracker on first call
        if tracker is None:
            logger.info(f"🔍 Initializing ClusterCohesionTracker with {len(df_sample)} samples")

            # Prepare raw features
            raw_features = prepare_raw_features(df_sample, ignore_cols=ignore_cols)

            # Build missingness mask
            df_for_miss = df_sample.drop(columns=[c for c in ignore_cols if c in df_sample.columns], errors='ignore')
            missingness_mask = df_for_miss.isna().values

            tracker = ClusterCohesionTracker(
                raw_features=raw_features,
                k_values=k_values,
                random_state=random_state,
                missingness_mask=missingness_mask if missingness_mask.any() else None,
                n_neighbors_for_preservation=10
            )

            # Store sample indices for consistent encoding
            tracker._sample_indices = sample_indices
            tracker._df_sample = df_sample

        # Encode samples through ES (use context manager to restore training mode)
        from featrix.neural.training_context_manager import EncoderEvalMode
        embeddings = []
        records = tracker._df_sample.to_dict('records')

        with EncoderEvalMode(es.encoder), torch.no_grad():
            for record in records:
                # Remove ignored columns from record
                record_clean = {k: v for k, v in record.items() if k not in ignore_cols}
                try:
                    emb = es.encode_record(record_clean, squeeze=True, short=False)
                    if hasattr(emb, 'cpu'):
                        emb = emb.cpu().numpy()
                    embeddings.append(emb)
                except Exception:
                    # Use zeros for failed encodings
                    if embeddings:
                        embeddings.append(np.zeros_like(embeddings[0]))
                    else:
                        continue

        if len(embeddings) < 50:
            logger.warning(f"⚠️  Only {len(embeddings)} rows encoded, skipping cohesion check")
            return tracker

        embeddings_array = np.array(embeddings)

        # Ensure we have the right number of embeddings
        if len(embeddings_array) != tracker.n_samples:
            logger.warning(f"⚠️  Embedding count mismatch: {len(embeddings_array)} vs {tracker.n_samples}")
            return tracker

        # Record metrics for this epoch
        epoch_metrics = tracker.record_epoch(epoch_idx, embeddings_array)

        # Log summary
        tracker.log_epoch_summary(epoch_idx, epoch_metrics)

        return tracker

    except Exception as e:
        logger.warning(f"⚠️  Cohesion check failed: {e}")
        return tracker
