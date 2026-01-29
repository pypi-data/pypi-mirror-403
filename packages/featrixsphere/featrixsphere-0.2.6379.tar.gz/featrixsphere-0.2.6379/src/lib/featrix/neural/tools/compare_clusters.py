#!/usr/bin/env python3
#  -*- coding: utf-8 -*-
#
#  Copyright Featrix, Inc 2023-2025
#
#  Proprietary and Confidential.  Unauthorized use, copying or dissemination
#  of these materials is strictly prohibited.
#
"""
Cluster Comparison Tool

Compares K-Means clustering between original feature space and ES embedding space
to diagnose whether the embedding space is learning meaningful structure.

Usage:
    python -m featrix.neural.tools.compare_clusters \\
        --csv /path/to/data.csv \\
        --pickle /path/to/embedding_space.pickle \\
        --output-dir /path/to/output \\
        --drop-columns Transported,PassengerId \\
        --sample 5000 \\
        --seed 42
"""

import argparse
import json
import logging
import sys
import warnings
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set

# Setup paths before other imports
_tools_dir = Path(__file__).parent
_neural_dir = _tools_dir.parent
_featrix_dir = _neural_dir.parent
_lib_dir = _featrix_dir.parent
_src_dir = _lib_dir.parent

if str(_lib_dir) not in sys.path:
    sys.path.insert(0, str(_lib_dir))
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from scipy.optimize import linear_sum_assignment

# Featrix imports
from featrix.neural.io_utils import CPUUnpickler
from featrix.neural.input_data_file import FeatrixInputDataFile

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# Suppress sklearn warnings
warnings.filterwarnings('ignore', category=FutureWarning)


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class ClusterMatch:
    """A single cluster match from original to embedding space."""
    original_cluster: int
    embedding_cluster: int
    jaccard: float
    original_size: int
    embedding_size: int
    intersection_size: int


@dataclass
class KResult:
    """Results for a single K value."""
    k: int
    input_silhouette: float
    embedding_silhouette: float
    jaccard_matrix: List[List[float]]
    greedy_matches: List[ClusterMatch]
    greedy_avg_jaccard: float
    optimal_matches: List[ClusterMatch]
    optimal_avg_jaccard: float
    input_cluster_sizes: List[int]
    embedding_cluster_sizes: List[int]


@dataclass
class ComparisonResult:
    """Full comparison results across all K values."""
    csv_path: str
    pickle_path: str
    n_rows: int
    n_rows_encoded: int
    n_input_features: int
    embedding_dim: int
    columns_dropped: List[str]
    columns_used: List[str]
    timestamp: str
    k_results: Dict[int, KResult] = field(default_factory=dict)
    best_k_by_silhouette_input: int = 0
    best_k_by_silhouette_embedding: int = 0
    best_k_by_jaccard_greedy: int = 0
    best_k_by_jaccard_optimal: int = 0


# =============================================================================
# Core Functions
# =============================================================================

def load_embedding_space(pickle_path: str):
    """Load embedding space from pickle file using CPUUnpickler."""
    logger.info(f"Loading embedding space from: {pickle_path}")
    with open(pickle_path, 'rb') as f:
        es = CPUUnpickler(f).load()
    logger.info(f"  Loaded ES with d_model={es.d_model}, columns={len(es.col_codecs)}")
    return es


def load_and_preprocess_csv(
    csv_path: str,
    drop_columns: List[str],
    sample_size: Optional[int],
    seed: int
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Load CSV and prepare for clustering.

    Returns:
        Tuple of (dataframe, list of columns used)
    """
    logger.info(f"Loading CSV from: {csv_path}")

    # Use FeatrixInputDataFile for consistent loading
    input_file = FeatrixInputDataFile(csv_path)
    df = input_file.df.copy()

    logger.info(f"  Loaded {len(df)} rows, {len(df.columns)} columns")

    # Drop specified columns
    columns_to_drop = [c for c in drop_columns if c in df.columns]
    if columns_to_drop:
        logger.info(f"  Dropping columns: {columns_to_drop}")
        df = df.drop(columns=columns_to_drop)

    # Sample if requested
    if sample_size and len(df) > sample_size:
        logger.info(f"  Sampling {sample_size} rows from {len(df)}")
        df = df.sample(n=sample_size, random_state=seed)

    columns_used = list(df.columns)
    logger.info(f"  Using {len(columns_used)} columns: {columns_used[:5]}{'...' if len(columns_used) > 5 else ''}")

    return df, columns_used


def prepare_input_features(df: pd.DataFrame) -> np.ndarray:
    """
    Prepare input features for clustering.

    - One-hot encode categoricals
    - Scale numerics
    - Impute missing values

    Returns:
        numpy array of shape (n_rows, n_features)
    """
    logger.info("Preparing input features for clustering...")

    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category', 'bool']).columns.tolist()

    logger.info(f"  Numeric columns: {len(numeric_cols)}, Categorical columns: {len(categorical_cols)}")

    processed_parts = []

    # Process numeric columns
    if numeric_cols:
        numeric_data = df[numeric_cols].values.astype(float)

        # Impute missing values with median
        imputer = SimpleImputer(strategy='median')
        numeric_data = imputer.fit_transform(numeric_data)

        # Scale
        scaler = StandardScaler()
        numeric_data = scaler.fit_transform(numeric_data)

        processed_parts.append(numeric_data)
        logger.info(f"  Processed numeric: {numeric_data.shape}")

    # Process categorical columns
    if categorical_cols:
        categorical_data = df[categorical_cols].astype(str).fillna('__MISSING__')

        # One-hot encode
        encoder = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
        categorical_encoded = encoder.fit_transform(categorical_data)

        processed_parts.append(categorical_encoded)
        logger.info(f"  Processed categorical: {categorical_encoded.shape}")

    if not processed_parts:
        raise ValueError("No features to process - dataframe has no numeric or categorical columns")

    # Combine
    features = np.hstack(processed_parts)
    logger.info(f"  Final input features shape: {features.shape}")

    return features


def encode_rows_through_es(
    es,
    df: pd.DataFrame,
    batch_size: int = 256
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Encode rows through the embedding space.

    Returns:
        Tuple of (embeddings array, valid_mask boolean array)
    """
    logger.info(f"Encoding {len(df)} rows through embedding space...")

    # Convert dataframe rows to list of dicts
    records = df.to_dict('records')

    # Track which rows encode successfully
    embeddings = []
    valid_indices = []
    failed_count = 0

    for i, record in enumerate(records):
        try:
            # Use encode_record for single records
            embedding = es.encode_record(record, squeeze=True, short=False)

            # Convert to numpy if tensor
            if hasattr(embedding, 'cpu'):
                embedding = embedding.cpu().detach().numpy()

            embeddings.append(embedding)
            valid_indices.append(i)

        except Exception as e:
            failed_count += 1
            if failed_count <= 3:
                logger.warning(f"  Failed to encode row {i}: {e}")
            elif failed_count == 4:
                logger.warning("  (suppressing further encoding errors)")

    if failed_count > 0:
        logger.warning(f"  {failed_count}/{len(records)} rows failed to encode")

    if not embeddings:
        raise ValueError("No rows could be encoded through the embedding space")

    embeddings_array = np.array(embeddings)
    valid_mask = np.zeros(len(df), dtype=bool)
    valid_mask[valid_indices] = True

    logger.info(f"  Successfully encoded {len(embeddings)} rows, embedding dim={embeddings_array.shape[1]}")

    return embeddings_array, valid_mask


def build_cluster_sets(labels: np.ndarray) -> Dict[int, Set[int]]:
    """Build sets of row indices for each cluster."""
    cluster_sets = {}
    for idx, label in enumerate(labels):
        if label not in cluster_sets:
            cluster_sets[label] = set()
        cluster_sets[label].add(idx)
    return cluster_sets


def compute_jaccard(set_a: Set[int], set_b: Set[int]) -> float:
    """Compute Jaccard similarity between two sets."""
    if not set_a and not set_b:
        return 1.0
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union > 0 else 0.0


def compute_jaccard_matrix(
    input_sets: Dict[int, Set[int]],
    embed_sets: Dict[int, Set[int]]
) -> np.ndarray:
    """
    Compute Jaccard similarity matrix between input and embedding clusters.

    Returns:
        Matrix of shape (n_input_clusters, n_embed_clusters)
    """
    n_input = len(input_sets)
    n_embed = len(embed_sets)

    matrix = np.zeros((n_input, n_embed))

    for i, input_set in input_sets.items():
        for j, embed_set in embed_sets.items():
            matrix[i, j] = compute_jaccard(input_set, embed_set)

    return matrix


def greedy_match(
    jaccard_matrix: np.ndarray,
    input_sets: Dict[int, Set[int]],
    embed_sets: Dict[int, Set[int]]
) -> Tuple[List[ClusterMatch], float]:
    """
    Greedy matching: each input cluster picks its best embedding cluster.

    Allows many-to-one matching (multiple input clusters can match same embedding cluster).
    """
    matches = []

    for i in range(jaccard_matrix.shape[0]):
        best_j = int(np.argmax(jaccard_matrix[i, :]))
        best_jaccard = jaccard_matrix[i, best_j]

        input_set = input_sets[i]
        embed_set = embed_sets[best_j]

        match = ClusterMatch(
            original_cluster=i,
            embedding_cluster=best_j,
            jaccard=best_jaccard,
            original_size=len(input_set),
            embedding_size=len(embed_set),
            intersection_size=len(input_set & embed_set)
        )
        matches.append(match)

    avg_jaccard = np.mean([m.jaccard for m in matches])
    return matches, avg_jaccard


def optimal_match(
    jaccard_matrix: np.ndarray,
    input_sets: Dict[int, Set[int]],
    embed_sets: Dict[int, Set[int]]
) -> Tuple[List[ClusterMatch], float]:
    """
    Optimal 1:1 matching using Hungarian algorithm.

    Finds the assignment that maximizes total Jaccard similarity.
    """
    # Hungarian algorithm minimizes cost, so negate Jaccard for maximization
    cost_matrix = -jaccard_matrix

    # Handle non-square matrices by padding
    n_input, n_embed = cost_matrix.shape
    if n_input != n_embed:
        max_dim = max(n_input, n_embed)
        padded = np.zeros((max_dim, max_dim))
        padded[:n_input, :n_embed] = cost_matrix
        cost_matrix = padded

    row_ind, col_ind = linear_sum_assignment(cost_matrix)

    matches = []
    for i, j in zip(row_ind, col_ind):
        if i < len(input_sets) and j < len(embed_sets):
            jaccard = jaccard_matrix[i, j]
            input_set = input_sets[i]
            embed_set = embed_sets[j]

            match = ClusterMatch(
                original_cluster=i,
                embedding_cluster=j,
                jaccard=jaccard,
                original_size=len(input_set),
                embedding_size=len(embed_set),
                intersection_size=len(input_set & embed_set)
            )
            matches.append(match)

    avg_jaccard = np.mean([m.jaccard for m in matches]) if matches else 0.0
    return matches, avg_jaccard


def analyze_k(
    input_features: np.ndarray,
    embeddings: np.ndarray,
    k: int,
    seed: int
) -> KResult:
    """Run clustering analysis for a specific K value."""
    logger.info(f"  Analyzing K={k}...")

    # K-Means on input features
    input_kmeans = KMeans(n_clusters=k, random_state=seed, n_init=10)
    input_labels = input_kmeans.fit_predict(input_features)

    # K-Means on embeddings
    embed_kmeans = KMeans(n_clusters=k, random_state=seed, n_init=10)
    embed_labels = embed_kmeans.fit_predict(embeddings)

    # Silhouette scores
    input_sil = silhouette_score(input_features, input_labels) if k < len(input_features) else 0.0
    embed_sil = silhouette_score(embeddings, embed_labels) if k < len(embeddings) else 0.0

    # Build cluster sets
    input_sets = build_cluster_sets(input_labels)
    embed_sets = build_cluster_sets(embed_labels)

    # Compute Jaccard matrix
    jaccard_matrix = compute_jaccard_matrix(input_sets, embed_sets)

    # Greedy matching
    greedy_matches, greedy_avg = greedy_match(jaccard_matrix, input_sets, embed_sets)

    # Optimal 1:1 matching
    optimal_matches, optimal_avg = optimal_match(jaccard_matrix, input_sets, embed_sets)

    # Cluster sizes
    input_sizes = [len(input_sets[i]) for i in range(k)]
    embed_sizes = [len(embed_sets[i]) for i in range(k)]

    return KResult(
        k=k,
        input_silhouette=input_sil,
        embedding_silhouette=embed_sil,
        jaccard_matrix=jaccard_matrix.tolist(),
        greedy_matches=greedy_matches,
        greedy_avg_jaccard=greedy_avg,
        optimal_matches=optimal_matches,
        optimal_avg_jaccard=optimal_avg,
        input_cluster_sizes=input_sizes,
        embedding_cluster_sizes=embed_sizes
    )


# =============================================================================
# Visualization Functions
# =============================================================================

def generate_visualizations(
    input_features: np.ndarray,
    embeddings: np.ndarray,
    results: ComparisonResult,
    output_dir: Path,
    seed: int
) -> Dict[str, Path]:
    """Generate all visualization images."""
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt

    images_dir = output_dir / "images"
    images_dir.mkdir(exist_ok=True)

    image_paths = {}

    # 1. Silhouette scores by K
    logger.info("  Generating silhouette plot...")
    fig, ax = plt.subplots(figsize=(10, 6))
    ks = sorted(results.k_results.keys())
    input_sils = [results.k_results[k].input_silhouette for k in ks]
    embed_sils = [results.k_results[k].embedding_silhouette for k in ks]

    ax.plot(ks, input_sils, 'b-o', label='Input Space', linewidth=2, markersize=8)
    ax.plot(ks, embed_sils, 'r-s', label='Embedding Space', linewidth=2, markersize=8)
    ax.set_xlabel('K (number of clusters)', fontsize=12)
    ax.set_ylabel('Silhouette Score', fontsize=12)
    ax.set_title('Silhouette Scores by K', fontsize=14)
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)
    ax.set_xticks(ks)

    path = images_dir / "silhouette_by_k.png"
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    image_paths['silhouette_by_k'] = path

    # 2. Jaccard scores by K (greedy vs optimal)
    logger.info("  Generating Jaccard plot...")
    fig, ax = plt.subplots(figsize=(10, 6))
    greedy_jaccards = [results.k_results[k].greedy_avg_jaccard for k in ks]
    optimal_jaccards = [results.k_results[k].optimal_avg_jaccard for k in ks]

    ax.plot(ks, greedy_jaccards, 'g-o', label='Greedy Match (many-to-one)', linewidth=2, markersize=8)
    ax.plot(ks, optimal_jaccards, 'm-s', label='Optimal Match (1:1 Hungarian)', linewidth=2, markersize=8)
    ax.set_xlabel('K (number of clusters)', fontsize=12)
    ax.set_ylabel('Average Jaccard Similarity', fontsize=12)
    ax.set_title('Cluster Alignment: Input Space vs Embedding Space', fontsize=14)
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)
    ax.set_xticks(ks)
    ax.set_ylim(0, 1)

    path = images_dir / "jaccard_by_k.png"
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    image_paths['jaccard_by_k'] = path

    # 3. Jaccard heatmaps for each K
    for k in ks:
        logger.info(f"  Generating Jaccard heatmap for K={k}...")
        k_result = results.k_results[k]
        matrix = np.array(k_result.jaccard_matrix)

        fig, ax = plt.subplots(figsize=(8, 6))
        im = ax.imshow(matrix, cmap='YlOrRd', aspect='auto', vmin=0, vmax=1)

        # Add colorbar
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('Jaccard Similarity', fontsize=11)

        # Add text annotations
        for i in range(matrix.shape[0]):
            for j in range(matrix.shape[1]):
                text = ax.text(j, i, f'{matrix[i, j]:.2f}',
                              ha='center', va='center', fontsize=10,
                              color='white' if matrix[i, j] > 0.5 else 'black')

        ax.set_xlabel('Embedding Cluster', fontsize=12)
        ax.set_ylabel('Input Cluster', fontsize=12)
        ax.set_title(f'Jaccard Similarity Matrix (K={k})', fontsize=14)
        ax.set_xticks(range(k))
        ax.set_yticks(range(k))

        path = images_dir / f"jaccard_heatmap_k{k}.png"
        fig.savefig(path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        image_paths[f'jaccard_heatmap_k{k}'] = path

    # 4. UMAP visualizations for best K (by optimal Jaccard)
    best_k = results.best_k_by_jaccard_optimal
    logger.info(f"  Generating UMAP plots for best K={best_k}...")

    try:
        from umap import UMAP
        reducer_class = UMAP
        reducer_name = "UMAP"
        use_umap = True
    except ImportError:
        logger.warning("  UMAP not available, using t-SNE (slower)")
        from sklearn.manifold import TSNE
        reducer_class = TSNE
        reducer_name = "t-SNE"
        use_umap = False

    # Subsample for dimensionality reduction if needed
    max_points = 5000
    if len(input_features) > max_points:
        indices = np.random.RandomState(seed).choice(len(input_features), max_points, replace=False)
        input_sub = input_features[indices]
        embed_sub = embeddings[indices]
    else:
        indices = np.arange(len(input_features))
        input_sub = input_features
        embed_sub = embeddings

    # Re-cluster on subsampled data for visualization
    input_kmeans = KMeans(n_clusters=best_k, random_state=seed, n_init=10)
    input_labels = input_kmeans.fit_predict(input_sub)

    embed_kmeans = KMeans(n_clusters=best_k, random_state=seed, n_init=10)
    embed_labels = embed_kmeans.fit_predict(embed_sub)

    # Reduce dimensions
    if use_umap:
        input_2d = reducer_class(n_components=2, random_state=seed, n_neighbors=15, min_dist=0.1).fit_transform(input_sub)
        embed_2d = reducer_class(n_components=2, random_state=seed, n_neighbors=15, min_dist=0.1).fit_transform(embed_sub)
    else:
        input_2d = reducer_class(n_components=2, random_state=seed, perplexity=30).fit_transform(input_sub)
        embed_2d = reducer_class(n_components=2, random_state=seed, perplexity=30).fit_transform(embed_sub)

    # Plot input space
    fig, ax = plt.subplots(figsize=(10, 8))
    scatter = ax.scatter(input_2d[:, 0], input_2d[:, 1], c=input_labels, cmap='tab10', alpha=0.6, s=10)
    ax.set_title(f'Input Space Clusters (K={best_k}, {reducer_name})', fontsize=14)
    ax.set_xlabel(f'{reducer_name} 1')
    ax.set_ylabel(f'{reducer_name} 2')
    plt.colorbar(scatter, ax=ax, label='Cluster')

    path = images_dir / f"input_space_k{best_k}.png"
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    image_paths[f'input_space_k{best_k}'] = path

    # Plot embedding space
    fig, ax = plt.subplots(figsize=(10, 8))
    scatter = ax.scatter(embed_2d[:, 0], embed_2d[:, 1], c=embed_labels, cmap='tab10', alpha=0.6, s=10)
    ax.set_title(f'Embedding Space Clusters (K={best_k}, {reducer_name})', fontsize=14)
    ax.set_xlabel(f'{reducer_name} 1')
    ax.set_ylabel(f'{reducer_name} 2')
    plt.colorbar(scatter, ax=ax, label='Cluster')

    path = images_dir / f"embedding_space_k{best_k}.png"
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    image_paths[f'embedding_space_k{best_k}'] = path

    # Side-by-side comparison
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))

    scatter1 = axes[0].scatter(input_2d[:, 0], input_2d[:, 1], c=input_labels, cmap='tab10', alpha=0.6, s=10)
    axes[0].set_title(f'Input Space (K={best_k})', fontsize=14)
    axes[0].set_xlabel(f'{reducer_name} 1')
    axes[0].set_ylabel(f'{reducer_name} 2')

    scatter2 = axes[1].scatter(embed_2d[:, 0], embed_2d[:, 1], c=embed_labels, cmap='tab10', alpha=0.6, s=10)
    axes[1].set_title(f'Embedding Space (K={best_k})', fontsize=14)
    axes[1].set_xlabel(f'{reducer_name} 1')
    axes[1].set_ylabel(f'{reducer_name} 2')

    plt.suptitle(f'Cluster Comparison: Input vs Embedding Space', fontsize=16, y=1.02)
    plt.tight_layout()

    path = images_dir / f"comparison_k{best_k}.png"
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    image_paths[f'comparison_k{best_k}'] = path

    logger.info(f"  Generated {len(image_paths)} images")
    return image_paths


# =============================================================================
# HTML Report Generation
# =============================================================================

def generate_html_report(
    results: ComparisonResult,
    image_paths: Dict[str, Path],
    output_dir: Path
):
    """Generate the HTML report."""
    logger.info("Generating HTML report...")

    html_parts = []

    # Header
    html_parts.append(f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cluster Comparison Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
            color: #333;
        }}
        h1, h2, h3 {{
            color: #2c3e50;
        }}
        h1 {{
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        .summary-box {{
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .metric-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 15px 0;
        }}
        .metric-card {{
            background: #ecf0f1;
            padding: 15px;
            border-radius: 6px;
            text-align: center;
        }}
        .metric-value {{
            font-size: 24px;
            font-weight: bold;
            color: #2980b9;
        }}
        .metric-label {{
            font-size: 12px;
            color: #7f8c8d;
            margin-top: 5px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
            background: white;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background: #3498db;
            color: white;
        }}
        tr:hover {{
            background: #f5f5f5;
        }}
        .image-container {{
            text-align: center;
            margin: 20px 0;
        }}
        .image-container img {{
            max-width: 100%;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        }}
        .interpretation {{
            background: #e8f6ff;
            border-left: 4px solid #3498db;
            padding: 15px;
            margin: 15px 0;
            border-radius: 0 8px 8px 0;
        }}
        .warning {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
        }}
        .good {{
            background: #d4edda;
            border-left: 4px solid #28a745;
        }}
        .bad {{
            background: #f8d7da;
            border-left: 4px solid #dc3545;
        }}
        .k-section {{
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .match-table td:first-child {{
            font-weight: bold;
        }}
        code {{
            background: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: monospace;
        }}
    </style>
</head>
<body>
    <h1>Cluster Comparison Report</h1>
    <p><em>Generated: {results.timestamp}</em></p>
""")

    # Summary section
    html_parts.append(f"""
    <div class="summary-box">
        <h2>Summary</h2>
        <div class="metric-grid">
            <div class="metric-card">
                <div class="metric-value">{results.n_rows_encoded}</div>
                <div class="metric-label">Rows Analyzed</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{results.n_input_features}</div>
                <div class="metric-label">Input Features</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{results.embedding_dim}</div>
                <div class="metric-label">Embedding Dim</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{results.best_k_by_jaccard_optimal}</div>
                <div class="metric-label">Best K (by Jaccard)</div>
            </div>
        </div>

        <h3>Data Sources</h3>
        <ul>
            <li><strong>CSV:</strong> <code>{results.csv_path}</code></li>
            <li><strong>Pickle:</strong> <code>{results.pickle_path}</code></li>
            <li><strong>Columns dropped:</strong> {', '.join(results.columns_dropped) if results.columns_dropped else 'None'}</li>
            <li><strong>Columns used:</strong> {len(results.columns_used)} columns</li>
        </ul>
    </div>
""")

    # Best K summary
    best_k = results.best_k_by_jaccard_optimal
    best_result = results.k_results[best_k]
    jaccard_gap = best_result.greedy_avg_jaccard - best_result.optimal_avg_jaccard

    interpretation_class = "good" if best_result.optimal_avg_jaccard > 0.5 else ("warning" if best_result.optimal_avg_jaccard > 0.3 else "bad")

    html_parts.append(f"""
    <div class="summary-box">
        <h2>Key Finding: Best Alignment at K={best_k}</h2>

        <div class="metric-grid">
            <div class="metric-card">
                <div class="metric-value">{best_result.greedy_avg_jaccard:.3f}</div>
                <div class="metric-label">Greedy Jaccard</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{best_result.optimal_avg_jaccard:.3f}</div>
                <div class="metric-label">Optimal (1:1) Jaccard</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{jaccard_gap:.3f}</div>
                <div class="metric-label">Gap (merge indicator)</div>
            </div>
        </div>

        <div class="interpretation {interpretation_class}">
            <strong>Interpretation:</strong><br>
""")

    if best_result.optimal_avg_jaccard > 0.6:
        html_parts.append("The embedding space preserves the cluster structure from the input space well. Clusters in both spaces largely overlap.")
    elif best_result.optimal_avg_jaccard > 0.4:
        html_parts.append("Moderate alignment between input and embedding clusters. The ES captures some but not all of the original structure.")
    elif best_result.optimal_avg_jaccard > 0.2:
        html_parts.append("Weak alignment. The embedding space has learned different groupings than exist in the raw feature space.")
    else:
        html_parts.append("Very low alignment. The ES clusters are essentially independent of input space clusters - the ES may be learning different (possibly more useful) structure, or may not be learning meaningful patterns.")

    if jaccard_gap > 0.1:
        html_parts.append(f"<br><br>The gap of {jaccard_gap:.3f} between greedy and optimal matching suggests the ES is merging some input clusters together.")

    html_parts.append("""
        </div>
    </div>
""")

    # Overview plots
    html_parts.append("""
    <div class="summary-box">
        <h2>Overview Plots</h2>
""")

    if 'silhouette_by_k' in image_paths:
        html_parts.append(f"""
        <div class="image-container">
            <h3>Silhouette Scores by K</h3>
            <img src="images/{image_paths['silhouette_by_k'].name}" alt="Silhouette by K">
            <p><em>Higher silhouette scores indicate better-defined clusters.</em></p>
        </div>
""")

    if 'jaccard_by_k' in image_paths:
        html_parts.append(f"""
        <div class="image-container">
            <h3>Jaccard Alignment by K</h3>
            <img src="images/{image_paths['jaccard_by_k'].name}" alt="Jaccard by K">
            <p><em>Higher Jaccard = better alignment between input and embedding clusters.</em></p>
        </div>
""")

    if f'comparison_k{best_k}' in image_paths:
        html_parts.append(f"""
        <div class="image-container">
            <h3>Side-by-Side Cluster Visualization (K={best_k})</h3>
            <img src="images/{image_paths[f'comparison_k{best_k}'].name}" alt="Side by side comparison">
        </div>
""")

    html_parts.append("</div>")

    # Per-K results table
    html_parts.append("""
    <div class="summary-box">
        <h2>Results by K</h2>
        <table>
            <tr>
                <th>K</th>
                <th>Input Silhouette</th>
                <th>Embed Silhouette</th>
                <th>Greedy Jaccard</th>
                <th>Optimal Jaccard</th>
                <th>Gap</th>
            </tr>
""")

    for k in sorted(results.k_results.keys()):
        kr = results.k_results[k]
        gap = kr.greedy_avg_jaccard - kr.optimal_avg_jaccard
        highlight = ' style="background: #d4edda;"' if k == best_k else ''
        html_parts.append(f"""
            <tr{highlight}>
                <td>{k}</td>
                <td>{kr.input_silhouette:.3f}</td>
                <td>{kr.embedding_silhouette:.3f}</td>
                <td>{kr.greedy_avg_jaccard:.3f}</td>
                <td>{kr.optimal_avg_jaccard:.3f}</td>
                <td>{gap:.3f}</td>
            </tr>
""")

    html_parts.append("""
        </table>
    </div>
""")

    # Detailed per-K sections
    html_parts.append("<h2>Detailed Results by K</h2>")

    for k in sorted(results.k_results.keys()):
        kr = results.k_results[k]

        html_parts.append(f"""
    <div class="k-section">
        <h3>K = {k}</h3>

        <h4>Cluster Sizes</h4>
        <table>
            <tr>
                <th>Cluster</th>
                <th>Input Space Size</th>
                <th>Embedding Space Size</th>
            </tr>
""")

        for i in range(k):
            html_parts.append(f"""
            <tr>
                <td>{i}</td>
                <td>{kr.input_cluster_sizes[i]}</td>
                <td>{kr.embedding_cluster_sizes[i]}</td>
            </tr>
""")

        html_parts.append("""
        </table>

        <h4>Greedy Matching (many-to-one)</h4>
        <table class="match-table">
            <tr>
                <th>Input Cluster</th>
                <th>→ Best Embed Cluster</th>
                <th>Jaccard</th>
                <th>Intersection</th>
            </tr>
""")

        for m in kr.greedy_matches:
            html_parts.append(f"""
            <tr>
                <td>Cluster {m.original_cluster} (n={m.original_size})</td>
                <td>Cluster {m.embedding_cluster} (n={m.embedding_size})</td>
                <td>{m.jaccard:.3f}</td>
                <td>{m.intersection_size}</td>
            </tr>
""")

        html_parts.append(f"""
        </table>
        <p><strong>Average Greedy Jaccard: {kr.greedy_avg_jaccard:.3f}</strong></p>

        <h4>Optimal 1:1 Matching (Hungarian)</h4>
        <table class="match-table">
            <tr>
                <th>Input Cluster</th>
                <th>→ Embed Cluster</th>
                <th>Jaccard</th>
                <th>Intersection</th>
            </tr>
""")

        for m in kr.optimal_matches:
            html_parts.append(f"""
            <tr>
                <td>Cluster {m.original_cluster} (n={m.original_size})</td>
                <td>Cluster {m.embedding_cluster} (n={m.embedding_size})</td>
                <td>{m.jaccard:.3f}</td>
                <td>{m.intersection_size}</td>
            </tr>
""")

        html_parts.append(f"""
        </table>
        <p><strong>Average Optimal Jaccard: {kr.optimal_avg_jaccard:.3f}</strong></p>
""")

        # Jaccard heatmap
        if f'jaccard_heatmap_k{k}' in image_paths:
            html_parts.append(f"""
        <div class="image-container">
            <h4>Jaccard Similarity Matrix</h4>
            <img src="images/{image_paths[f'jaccard_heatmap_k{k}'].name}" alt="Jaccard heatmap K={k}">
        </div>
""")

        html_parts.append("</div>")

    # Interpretation guide
    html_parts.append("""
    <div class="summary-box">
        <h2>Interpretation Guide</h2>

        <h3>What does Jaccard similarity mean?</h3>
        <p>Jaccard similarity measures overlap between two sets: J(A,B) = |A ∩ B| / |A ∪ B|</p>
        <ul>
            <li><strong>1.0</strong>: Perfect overlap - the clusters contain exactly the same rows</li>
            <li><strong>0.5</strong>: Moderate overlap - half the rows are shared</li>
            <li><strong>0.0</strong>: No overlap - completely different rows</li>
        </ul>

        <h3>Greedy vs Optimal Matching</h3>
        <ul>
            <li><strong>Greedy:</strong> Each input cluster picks its best embedding cluster (allows many-to-one)</li>
            <li><strong>Optimal:</strong> Hungarian algorithm finds best 1:1 assignment (no sharing)</li>
        </ul>
        <p>A large gap between greedy and optimal suggests the ES is merging multiple input clusters into fewer embedding clusters.</p>

        <h3>What do the results mean for my model?</h3>
        <ul>
            <li><strong>High alignment (Jaccard > 0.5):</strong> ES preserves input structure - good for tasks that depend on original feature groupings</li>
            <li><strong>Low alignment (Jaccard < 0.3):</strong> ES learned different structure - could be better (found hidden patterns) or worse (lost important information)</li>
            <li><strong>Check target correlation:</strong> If your downstream task (e.g., classification) depends on the original clusters, low alignment may hurt performance</li>
        </ul>
    </div>
""")

    # Footer
    html_parts.append("""
    <hr>
    <p style="text-align: center; color: #7f8c8d;">
        Generated by Featrix Cluster Comparison Tool
    </p>
</body>
</html>
""")

    # Write HTML file
    html_content = ''.join(html_parts)
    html_path = output_dir / "index.html"
    html_path.write_text(html_content)
    logger.info(f"  Wrote HTML report to {html_path}")

    return html_path


def save_json_results(results: ComparisonResult, output_dir: Path):
    """Save results as JSON for programmatic access."""

    def serialize(obj):
        if isinstance(obj, ClusterMatch):
            return asdict(obj)
        if isinstance(obj, KResult):
            d = asdict(obj)
            d['greedy_matches'] = [asdict(m) for m in obj.greedy_matches]
            d['optimal_matches'] = [asdict(m) for m in obj.optimal_matches]
            return d
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, (np.integer, np.floating)):
            return float(obj)
        return obj

    data = {
        'csv_path': results.csv_path,
        'pickle_path': results.pickle_path,
        'n_rows': results.n_rows,
        'n_rows_encoded': results.n_rows_encoded,
        'n_input_features': results.n_input_features,
        'embedding_dim': results.embedding_dim,
        'columns_dropped': results.columns_dropped,
        'columns_used': results.columns_used,
        'timestamp': results.timestamp,
        'best_k_by_silhouette_input': results.best_k_by_silhouette_input,
        'best_k_by_silhouette_embedding': results.best_k_by_silhouette_embedding,
        'best_k_by_jaccard_greedy': results.best_k_by_jaccard_greedy,
        'best_k_by_jaccard_optimal': results.best_k_by_jaccard_optimal,
        'k_results': {str(k): serialize(v) for k, v in results.k_results.items()}
    }

    json_path = output_dir / "data.json"
    with open(json_path, 'w') as f:
        json.dump(data, f, indent=2, default=serialize)

    logger.info(f"  Wrote JSON data to {json_path}")
    return json_path


# =============================================================================
# Main Entry Point
# =============================================================================

def parse_args():
    parser = argparse.ArgumentParser(
        description='Compare K-Means clustering between input feature space and ES embedding space.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m featrix.neural.tools.compare_clusters \\
      --csv data.csv --pickle embedding_space.pickle --output-dir ./report

  python -m featrix.neural.tools.compare_clusters \\
      --csv titanic.csv --pickle es_epoch_3.pickle \\
      --drop-columns Transported,PassengerId \\
      --sample 5000 --output-dir ./cluster_analysis
"""
    )

    parser.add_argument('--csv', required=True, help='Path to input CSV file')
    parser.add_argument('--pickle', required=True, help='Path to embedding space pickle file')
    parser.add_argument('--output-dir', required=True, help='Directory to write report and images')
    parser.add_argument('--drop-columns', default='', help='Comma-separated list of columns to drop')
    parser.add_argument('--sample', type=int, default=None, help='Subsample to this many rows (for large datasets)')
    parser.add_argument('--seed', type=int, default=42, help='Random seed for reproducibility')
    parser.add_argument('--min-k', type=int, default=2, help='Minimum K to test (default: 2)')
    parser.add_argument('--max-k', type=int, default=10, help='Maximum K to test (default: 10)')

    return parser.parse_args()


def main():
    args = parse_args()

    # Parse drop columns
    drop_columns = [c.strip() for c in args.drop_columns.split(',') if c.strip()]

    # Setup output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("=" * 60)
    logger.info("CLUSTER COMPARISON TOOL")
    logger.info("=" * 60)

    # Load data
    df, columns_used = load_and_preprocess_csv(
        args.csv, drop_columns, args.sample, args.seed
    )

    # Load embedding space
    es = load_embedding_space(args.pickle)

    # Prepare input features
    input_features = prepare_input_features(df)

    # Encode through ES
    embeddings, valid_mask = encode_rows_through_es(es, df)

    # Filter input features to match valid embeddings
    input_features = input_features[valid_mask]

    # Initialize results
    results = ComparisonResult(
        csv_path=args.csv,
        pickle_path=args.pickle,
        n_rows=len(df),
        n_rows_encoded=int(valid_mask.sum()),
        n_input_features=input_features.shape[1],
        embedding_dim=embeddings.shape[1],
        columns_dropped=drop_columns,
        columns_used=columns_used,
        timestamp=datetime.now().isoformat()
    )

    # Analyze for each K
    logger.info(f"Analyzing K={args.min_k}..{args.max_k}...")
    for k in range(args.min_k, args.max_k + 1):
        results.k_results[k] = analyze_k(input_features, embeddings, k, args.seed)

    # Find best K values
    results.best_k_by_silhouette_input = max(
        results.k_results.keys(),
        key=lambda k: results.k_results[k].input_silhouette
    )
    results.best_k_by_silhouette_embedding = max(
        results.k_results.keys(),
        key=lambda k: results.k_results[k].embedding_silhouette
    )
    results.best_k_by_jaccard_greedy = max(
        results.k_results.keys(),
        key=lambda k: results.k_results[k].greedy_avg_jaccard
    )
    results.best_k_by_jaccard_optimal = max(
        results.k_results.keys(),
        key=lambda k: results.k_results[k].optimal_avg_jaccard
    )

    logger.info(f"Best K by input silhouette: {results.best_k_by_silhouette_input}")
    logger.info(f"Best K by embedding silhouette: {results.best_k_by_silhouette_embedding}")
    logger.info(f"Best K by Jaccard (greedy): {results.best_k_by_jaccard_greedy}")
    logger.info(f"Best K by Jaccard (optimal): {results.best_k_by_jaccard_optimal}")

    # Generate visualizations
    logger.info("Generating visualizations...")
    image_paths = generate_visualizations(
        input_features, embeddings, results, output_dir, args.seed
    )

    # Generate HTML report
    generate_html_report(results, image_paths, output_dir)

    # Save JSON
    save_json_results(results, output_dir)

    # Print summary
    best_k = results.best_k_by_jaccard_optimal
    best_result = results.k_results[best_k]

    logger.info("=" * 60)
    logger.info("SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Best alignment at K={best_k}:")
    logger.info(f"  Greedy Jaccard:  {best_result.greedy_avg_jaccard:.3f}")
    logger.info(f"  Optimal Jaccard: {best_result.optimal_avg_jaccard:.3f}")
    logger.info(f"  Gap:             {best_result.greedy_avg_jaccard - best_result.optimal_avg_jaccard:.3f}")
    logger.info("")
    logger.info(f"Report written to: {output_dir / 'index.html'}")
    logger.info("=" * 60)

    return 0


if __name__ == '__main__':
    sys.exit(main())
