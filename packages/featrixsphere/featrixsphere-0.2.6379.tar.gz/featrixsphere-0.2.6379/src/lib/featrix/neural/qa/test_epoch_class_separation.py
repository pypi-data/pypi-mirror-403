#!/usr/bin/env python3
"""
Epoch Class Separation Test

Loads each epoch checkpoint from a trained ES and runs test data through it
to find which epoch produces the best class separation.

Metrics computed:
- Fisher discriminant ratio: between-class variance / within-class variance
- Silhouette score: measures cluster quality (-1 to +1)
- Inter-class centroid distance: mean distance between class centroids
- Mean embedding std: spread of embeddings

Usage:
    python test_epoch_class_separation.py

Configuration:
    Set ES_DIR and DATA_DIR below to point to your checkpoint directory and test data.
"""
import sys
import os
import json
import sqlite3
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np
import torch

# Paths
test_dir = Path(__file__).parent
neural_dir = test_dir.parent
featrix_dir = neural_dir.parent
lib_dir = featrix_dir.parent
src_dir = lib_dir.parent

sys.path.insert(0, str(lib_dir))
sys.path.insert(0, str(src_dir))

from featrix.neural.gpu_utils import set_backend_cpu as set_device_cpu

set_device_cpu()

# ============================================================================
# CONFIGURATION - Update these paths for your environment
# ============================================================================

# ES checkpoint directory - local copy for testing
ES_DIR = "/tmp/epoch_test/checkpoints"

# Test data SQLite file (copied from taco)
DATA_FILE = "/tmp/epoch_test/dot_test_data.db"

# Target column for class labels
# This dataset uses 'label' with values '0' (294 samples) and '1' (96 samples)
TARGET_COLUMN = "label"

# ============================================================================


def load_checkpoint_as_es(checkpoint_path: str):
    """
    Load an inference checkpoint using the standard io_utils function.
    """
    from featrix.neural.io_utils import load_embedded_space

    print(f"   Loading checkpoint: {checkpoint_path}")
    es = load_embedded_space(checkpoint_path, force_cpu=True)
    return es


def load_test_data(data_file: str):
    """
    Load the test data from SQLite file.
    Returns DataFrame.
    """
    print(f"   Loading data from SQLite: {data_file}")
    conn = sqlite3.connect(str(data_file))
    # Try common table names
    for table_name in ['data', 'embedding_space', 'main']:
        try:
            df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
            conn.close()
            print(f"   Loaded {len(df)} rows from table '{table_name}'")
            return df
        except:
            continue
    conn.close()
    raise ValueError(f"No valid table found in {data_file}")


def prewarm_string_cache(es, df: pd.DataFrame):
    """
    Pre-warm the string cache with all unique string values from the dataframe.
    This batches all strings and sends them to the string server once, avoiding
    per-record network calls during embedding computation.
    """
    from featrix.neural.string_codec import get_global_string_cache

    print("   Pre-warming string cache...")

    # Collect all unique string values from columns that have StringCodecs
    all_strings = set()
    string_cols = []

    for col_name, codec in es.col_codecs.items():
        # Check if this codec is a StringCodec
        codec_type = type(codec).__name__
        if 'StringCodec' in codec_type:
            string_cols.append(col_name)
            if col_name in df.columns:
                # Get unique non-null string values
                col_values = df[col_name].dropna().astype(str).unique()
                all_strings.update(col_values)

    print(f"   Found {len(string_cols)} string columns: {string_cols[:5]}{'...' if len(string_cols) > 5 else ''}")
    print(f"   Collected {len(all_strings)} unique string values")

    if not all_strings:
        print("   No string values to pre-warm")
        return

    # Get the global string cache and pre-warm it
    cache = get_global_string_cache(
        cache_filename=None,
        initial_values=list(all_strings),
        debug_name="epoch_test_prewarm"
    )

    print(f"   ✅ String cache pre-warmed with {len(all_strings)} values")


def compute_embeddings(es, df: pd.DataFrame, batch_size: int = 64):
    """
    Compute embeddings for all rows in the DataFrame.
    Returns tensor of shape (n_rows, d_model).
    """
    embeddings = []

    with torch.no_grad():
        for i in range(0, len(df), batch_size):
            batch_df = df.iloc[i:i+batch_size]

            for _, row in batch_df.iterrows():
                # Convert row to dict, excluding internal columns for encoding
                row_dict = {k: v for k, v in row.to_dict().items()
                           if not k.startswith('__featrix')}

                try:
                    emb = es.encode_record(row_dict, squeeze=True, short=False)
                    embeddings.append(emb.cpu())
                except Exception as e:
                    print(f"   ⚠️  Failed to encode row: {e}")
                    embeddings.append(torch.zeros(es.d_model))

    return torch.stack(embeddings)


def compute_separation_metrics(embeddings: torch.Tensor, labels: np.ndarray):
    """
    Compute class separation metrics.

    Returns dict with:
    - fisher_ratio: between-class variance / within-class variance
    - silhouette_score: sklearn silhouette score (-1 to +1)
    - mean_inter_class_dist: mean distance between class centroids
    - mean_std: mean standard deviation across embedding dimensions
    """
    results = {}

    # Convert to numpy for some operations
    emb_np = embeddings.numpy()

    # Basic stats
    results['mean_std'] = embeddings.std(dim=0).mean().item()
    results['mean_norm'] = torch.norm(embeddings, dim=1).mean().item()

    # Get unique classes
    unique_labels = np.unique(labels)
    if len(unique_labels) < 2:
        print("   ⚠️  Only one class found - cannot compute separation metrics")
        return results

    # Group embeddings by class
    class_embeddings = {}
    class_centroids = {}

    for label in unique_labels:
        mask = labels == label
        class_emb = embeddings[mask]
        class_embeddings[label] = class_emb
        class_centroids[label] = class_emb.mean(dim=0)

    # Fisher discriminant ratio
    try:
        within_class_vars = []
        for label, class_emb in class_embeddings.items():
            if len(class_emb) > 1:
                class_var = class_emb.var(dim=0).mean().item()
                within_class_vars.append(class_var)

        if within_class_vars:
            mean_within_class_var = np.mean(within_class_vars)

            # Between-class variance
            global_centroid = embeddings.mean(dim=0)
            centroid_diffs = []
            for centroid in class_centroids.values():
                diff = (centroid - global_centroid).pow(2).mean().item()
                centroid_diffs.append(diff)
            between_class_var = np.mean(centroid_diffs)

            if mean_within_class_var > 1e-10:
                results['fisher_ratio'] = between_class_var / mean_within_class_var
            else:
                results['fisher_ratio'] = 0.0

            results['between_class_var'] = between_class_var
            results['within_class_var'] = mean_within_class_var
    except Exception as e:
        print(f"   ⚠️  Failed to compute Fisher ratio: {e}")

    # Silhouette score
    try:
        from sklearn.metrics import silhouette_score
        if all(len(emb) >= 2 for emb in class_embeddings.values()):
            results['silhouette_score'] = silhouette_score(emb_np, labels)
    except Exception as e:
        print(f"   ⚠️  Failed to compute silhouette score: {e}")

    # Inter-class centroid distances
    try:
        centroid_list = list(class_centroids.values())
        distances = []
        for i in range(len(centroid_list)):
            for j in range(i + 1, len(centroid_list)):
                dist = torch.norm(centroid_list[i] - centroid_list[j]).item()
                distances.append(dist)
        if distances:
            results['mean_inter_class_dist'] = np.mean(distances)
            results['min_inter_class_dist'] = np.min(distances)
            results['max_inter_class_dist'] = np.max(distances)
    except Exception as e:
        print(f"   ⚠️  Failed to compute inter-class distances: {e}")

    return results


def find_checkpoints(es_dir: str):
    """
    Find all inference checkpoint files and return sorted by epoch.
    """
    es_path = Path(es_dir)
    checkpoints = list(es_path.glob("checkpoint_inference_e-*.pt"))

    # Sort by epoch number
    def get_epoch(path):
        name = path.stem  # e.g., "checkpoint_inference_e-42"
        try:
            return int(name.split('-')[-1])
        except ValueError:
            return -1

    checkpoints = sorted(checkpoints, key=get_epoch)
    return [(get_epoch(cp), str(cp)) for cp in checkpoints]


def main():
    print("=" * 80)
    print("🔍 EPOCH CLASS SEPARATION TEST")
    print("=" * 80)
    print(f"Started: {datetime.now()}")
    print()

    print(f"ES Directory: {ES_DIR}")
    print(f"Data File: {DATA_FILE}")
    print()

    # Find checkpoints
    print("Finding checkpoints...")
    checkpoints = find_checkpoints(ES_DIR)
    print(f"   Found {len(checkpoints)} checkpoints")

    if not checkpoints:
        print("❌ No checkpoints found!")
        return

    print(f"   Will test all {len(checkpoints)} checkpoints")
    print()

    # Load test data
    print("Loading test data...")
    try:
        df = load_test_data(DATA_FILE)
        print(f"   Loaded {len(df)} rows x {len(df.columns)} columns")
    except Exception as e:
        print(f"❌ Failed to load data: {e}")
        return

    # Find target column
    target_col = None
    for col in ['__featrix_label', 'target', 'label', 'class']:
        if col in df.columns:
            target_col = col
            break

    if target_col is None:
        print("❌ No target column found in data!")
        print(f"   Available columns: {list(df.columns)[:20]}...")
        return

    labels = df[target_col].values
    unique_labels = np.unique(labels)
    print(f"   Target column: {target_col}")
    print(f"   Classes: {unique_labels} ({len(unique_labels)} classes)")
    for label in unique_labels:
        count = (labels == label).sum()
        print(f"      '{label}': {count} samples ({100*count/len(labels):.1f}%)")
    print()

    # Test each epoch
    results = []
    best_fisher = {'epoch': -1, 'value': -float('inf')}
    best_silhouette = {'epoch': -1, 'value': -float('inf')}
    best_inter_dist = {'epoch': -1, 'value': -float('inf')}

    print("=" * 80)
    print("TESTING EPOCHS")
    print("=" * 80)

    # Pre-warm string cache once using the first checkpoint's ES
    # This batches all string values and caches them for all subsequent epochs
    first_epoch, first_checkpoint = checkpoints[0]
    print(f"\n🔥 Pre-warming string cache using epoch {first_epoch} checkpoint...")
    first_es = load_checkpoint_as_es(first_checkpoint)
    prewarm_string_cache(first_es, df)
    del first_es  # Free memory, we'll reload it in the loop

    for epoch, checkpoint_path in checkpoints:
        print(f"\n📊 Epoch {epoch}:")

        try:
            # Load ES from checkpoint
            es = load_checkpoint_as_es(checkpoint_path)

            # Compute embeddings
            print(f"   Computing embeddings for {len(df)} rows...")
            embeddings = compute_embeddings(es, df)
            print(f"   Embeddings shape: {embeddings.shape}")

            # Compute metrics
            metrics = compute_separation_metrics(embeddings, labels)
            metrics['epoch'] = epoch
            metrics['checkpoint'] = checkpoint_path

            # Print results
            fisher = metrics.get('fisher_ratio', 0)
            silhouette = metrics.get('silhouette_score', 0)
            inter_dist = metrics.get('mean_inter_class_dist', 0)

            print(f"   Fisher ratio: {fisher:.4f}")
            print(f"   Silhouette score: {silhouette:.4f}")
            print(f"   Mean inter-class dist: {inter_dist:.4f}")
            print(f"   Mean std: {metrics.get('mean_std', 0):.4f}")

            # Track best
            if fisher > best_fisher['value']:
                best_fisher = {'epoch': epoch, 'value': fisher}
            if silhouette > best_silhouette['value']:
                best_silhouette = {'epoch': epoch, 'value': silhouette}
            if inter_dist > best_inter_dist['value']:
                best_inter_dist = {'epoch': epoch, 'value': inter_dist}

            results.append(metrics)

            # Clean up to free memory
            del es, embeddings

        except Exception as e:
            print(f"   ❌ Failed: {e}")
            import traceback
            traceback.print_exc()

    # Summary
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()

    print(f"{'Epoch':<10} {'Fisher':<12} {'Silhouette':<12} {'Inter-Dist':<12} {'Std':<10}")
    print("-" * 60)
    for r in results:
        print(f"{r['epoch']:<10} {r.get('fisher_ratio', 0):<12.4f} {r.get('silhouette_score', 0):<12.4f} {r.get('mean_inter_class_dist', 0):<12.4f} {r.get('mean_std', 0):<10.4f}")

    print()
    print("🏆 BEST EPOCHS:")
    print(f"   Best Fisher ratio:      Epoch {best_fisher['epoch']} ({best_fisher['value']:.4f})")
    print(f"   Best Silhouette score:  Epoch {best_silhouette['epoch']} ({best_silhouette['value']:.4f})")
    print(f"   Best Inter-class dist:  Epoch {best_inter_dist['epoch']} ({best_inter_dist['value']:.4f})")

    # Save results
    output_file = test_dir / "epoch_class_separation_results.json"
    with open(output_file, 'w') as f:
        # Convert numpy types for JSON serialization
        json_results = []
        for r in results:
            jr = {}
            for k, v in r.items():
                if isinstance(v, (np.float32, np.float64)):
                    jr[k] = float(v)
                elif isinstance(v, (np.int32, np.int64)):
                    jr[k] = int(v)
                else:
                    jr[k] = v
            json_results.append(jr)

        json.dump({
            'results': json_results,
            'best_fisher': best_fisher,
            'best_silhouette': best_silhouette,
            'best_inter_dist': best_inter_dist,
            'config': {
                'es_dir': ES_DIR,
                'data_file': DATA_FILE,
                'target_column': target_col,
                'n_rows': len(df),
                'n_classes': len(unique_labels),
            }
        }, f, indent=2)

    print()
    print(f"Results saved to: {output_file}")
    print()
    print("=" * 80)
    print(f"Completed: {datetime.now()}")
    print("=" * 80)


if __name__ == "__main__":
    main()
