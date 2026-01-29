#!/usr/bin/env python3
"""
Async movie frame generation task - runs on dedicated movie_generation queue.

This module generates movie frames (3D projections) asynchronously on CPU
so training never blocks. Frames are generated every epoch.
Uses dedicated movie_generation queue with concurrency=1 to avoid competing
with critical training tasks.
"""

import json
import logging
import os
import pickle
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
import torch
import numpy as np

logger = logging.getLogger(__name__)


class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


def _encode_record_direct(encoder, col_codecs, record: dict, short: bool = True):
    """
    Encode a record directly using encoder and codecs without full EmbeddingSpace.

    This is a lightweight version of EmbeddingSpace.encode_record() that works
    with just the encoder and codecs from a checkpoint.

    Args:
        encoder: The FeatrixTableEncoder model
        col_codecs: Dict mapping column names to codecs
        record: Dict of field name -> value
        short: If True, return 3D embedding; if False, return full embedding

    Returns:
        Tensor with the embedding (3D if short=True, full otherwise)
    """
    from featrix.neural.featrix_token import create_token_batch, set_marginal

    # Step 1: Create base token dict with NOT_PRESENT tokens for all columns
    batch_tokens = {}
    for col, codec in col_codecs.items():
        batch_tokens[col] = create_token_batch([set_marginal(codec.get_not_present_token())])

    # Step 2: Tokenize each field from the record and replace in batch_tokens
    record_tokens = {}
    for field, value in record.items():
        field = field.strip()

        # Skip internal columns
        if field.startswith('__featrix'):
            continue

        # Skip fields without codecs
        if field not in col_codecs:
            continue

        codec = col_codecs[field]
        token = codec.tokenize(value)
        record_tokens[field] = token

    if not record_tokens:
        raise ValueError("No fields could be tokenized - check that record contains fields with codecs")

    # Step 3: Replace NOT_PRESENT tokens with actual tokens for fields we have
    for field, token in record_tokens.items():
        batch_tokens[field] = create_token_batch([token])

    # Step 4: Encode using the encoder
    with torch.no_grad():
        short_encoding, full_encoding = encoder.encode(batch_tokens)

    return short_encoding if short else full_encoding


def generate_movie_frame_on_cpu(
    checkpoint_path: str,
    data_snapshot_path: str,
    epoch: int,
    output_dir: str,
    session_id: str
) -> Optional[str]:
    """
    Generate a single movie frame on CPU from a model checkpoint.

    Args:
        checkpoint_path: Path to model checkpoint (.pt or .pickle file)
        data_snapshot_path: Path to saved data sample (.json)
        epoch: Epoch number
        output_dir: Where to save the projection
        session_id: Session ID for logging

    Returns:
        Path to saved projection file, or None if failed
    """

    start_time = time.time()

    # CRITICAL: Prevent concurrent loads of the same checkpoint
    # Multiple movie frame tasks may try to load the same checkpoint simultaneously
    # which can cause torch.load() to hang or corrupt memory
    import fcntl
    lock_file_path = f"{checkpoint_path}.lock"
    lock_file = None

    try:
        logger.info(f"🎬 [Session {session_id}] Generating movie frame for epoch {epoch} on CPU...")

        # Acquire exclusive lock on checkpoint file
        try:
            lock_file = open(lock_file_path, 'w')
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            logger.debug(f"   ✅ Acquired lock on {lock_file_path}")
        except (IOError, OSError) as e:
            logger.warning(f"   ⚠️  Another process is loading this checkpoint - waiting for lock...")
            if lock_file:
                lock_file.close()
            lock_file = open(lock_file_path, 'w')
            # Wait for lock (blocking)
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            logger.info(f"   ✅ Acquired lock after waiting")

        # Load checkpoint on CPU with timeout protection
        logger.info(f"   Loading checkpoint from {checkpoint_path}")
        checkpoint_size_mb = os.path.getsize(checkpoint_path) / (1024*1024)
        logger.info(f"   Checkpoint size: {checkpoint_size_mb:.1f} MB")

        # Use signal-based timeout to prevent hanging forever on torch.load()
        import signal

        def timeout_handler(signum, frame):
            raise TimeoutError(f"Checkpoint load timed out after 120 seconds")

        # Set alarm for 120 seconds (pickle files can be larger)
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(120)

        checkpoint_ext = Path(checkpoint_path).suffix.lower()
        embedding_space = None
        encoder = None
        col_codecs = {}
        column_spec = {}

        try:
            if checkpoint_ext == '.pickle':
                # Load full embedding space from pickle
                logger.info(f"   Loading pickle checkpoint...")
                with open(checkpoint_path, 'rb') as f:
                    embedding_space = pickle.load(f)
                signal.alarm(0)  # Cancel alarm

                # Extract what we need
                encoder = embedding_space.encoder
                col_codecs = getattr(embedding_space, 'col_codecs', {})
                column_spec = getattr(embedding_space, 'column_spec', {})
                logger.info(f"   ✅ Pickle loaded: {len(col_codecs)} codecs")

            else:
                # Load lightweight .pt checkpoint
                logger.info(f"   Loading torch checkpoint...")
                checkpoint = torch.load(checkpoint_path, map_location='cpu', weights_only=False)
                signal.alarm(0)  # Cancel alarm

                # Check if this is an old-style checkpoint with embedding_space
                if "embedding_space" in checkpoint:
                    embedding_space = checkpoint["embedding_space"]
                    encoder = embedding_space.encoder
                    col_codecs = getattr(embedding_space, 'col_codecs', {})
                    column_spec = getattr(embedding_space, 'column_spec', {})
                else:
                    # Lightweight format - extract components directly
                    encoder = checkpoint.get("encoder")
                    if encoder is None:
                        raise ValueError("Checkpoint must contain 'embedding_space' or 'encoder'")
                    col_codecs = checkpoint.get("col_codecs", {})
                    column_spec = checkpoint.get("column_spec", {})

                logger.info(f"   ✅ Checkpoint loaded: {len(checkpoint) if isinstance(checkpoint, dict) else 'N/A'} keys, {len(col_codecs)} codecs")

        except TimeoutError as e:
            signal.alarm(0)  # Cancel alarm
            logger.error(f"❌ Checkpoint load TIMEOUT: {e}")
            logger.error(f"   Checkpoint may be corrupted or too large to load")
            return None
        except Exception as e:
            signal.alarm(0)  # Cancel alarm
            raise

        # Move encoder to CPU and eval mode
        encoder.cpu()
        encoder.eval()

        logger.info(f"   ✅ Encoder ready on CPU (eval mode)")

        # Load data snapshot
        logger.info(f"   Loading data snapshot from {data_snapshot_path}")
        with open(data_snapshot_path, 'r') as f:
            data_snapshot = json.load(f)

        # Load the DataFrame from snapshot
        df = pd.DataFrame(data_snapshot['records'])
        sample_indices = data_snapshot.get('sample_indices')

        logger.info(f"   Processing {len(df)} records on CPU...")

        # Determine column types from column_spec
        # column_spec values can be ColumnType enums (IntEnum) or dicts
        set_columns_names = set()
        scalar_columns_names = set()
        string_columns_names = set()

        for col_name, spec in column_spec.items():
            # Handle both enum and dict formats
            if hasattr(spec, 'name'):
                # It's a ColumnType enum - use .name for comparison
                col_type = spec.name.lower()
            elif hasattr(spec, 'get'):
                # It's a dict
                col_type = spec.get('type', 'unknown')
            else:
                col_type = str(spec).lower()

            if col_type in ('set', 'list_of_sets', 'list_of_a_set'):
                set_columns_names.add(col_name)
            elif col_type in ('scalar', 'numeric', 'float', 'int'):
                scalar_columns_names.add(col_name)
            elif col_type in ('string', 'text', 'free_string'):
                string_columns_names.add(col_name)

        # Generate 3D embeddings on CPU using short embeddings
        coords_3d = []
        rowids = []
        row_offsets = []
        set_columns_matrix = []
        scalar_columns_matrix = []
        string_columns_matrix = []
        failed_records = 0

        for idx, row in df.iterrows():
            try:
                rowids.append(row.get('__featrix_row_id', idx))
                row_offsets.append(idx)

                # Encode on CPU using short (3D) embedding
                # Use EmbeddingSpace.encode_record if available, otherwise direct encoding
                with torch.no_grad():
                    if embedding_space is not None and hasattr(embedding_space, 'encode_record'):
                        embedding_short = embedding_space.encode_record(
                            row.to_dict(),
                            short=True,
                            output_device=torch.device("cpu")
                        )
                    else:
                        embedding_short = _encode_record_direct(
                            encoder, col_codecs, row.to_dict(), short=True
                        )

                # Convert to 3D coordinates
                # Squeeze in case encoder returns [1, 3] instead of [3]
                if embedding_short.dim() > 1:
                    embedding_short = embedding_short.squeeze(0)
                coords_3d.append([
                    embedding_short[0].item(),
                    embedding_short[1].item(),
                    embedding_short[2].item()
                ])

                # Extract column data for metadata
                orig_set_data = {}
                orig_scalar_data = {}
                orig_string_data = {}

                for k, v in row.items():
                    if k in set_columns_names:
                        orig_set_data[k] = v
                    elif k in scalar_columns_names:
                        orig_scalar_data[k] = v
                    elif k in string_columns_names:
                        orig_string_data[k] = v

                set_columns_matrix.append(orig_set_data)
                scalar_columns_matrix.append(orig_scalar_data)
                string_columns_matrix.append(orig_string_data)

            except Exception as e:
                failed_records += 1
                if failed_records <= 3:
                    logger.warning(f"Failed to encode record {idx} in epoch {epoch}: {e}")
                elif failed_records == 4:
                    logger.warning(f"... suppressing further encoding warnings")
                continue

        if failed_records > 0:
            logger.warning(f"   ⚠️  {failed_records}/{len(df)} records failed to encode")

        if len(coords_3d) == 0:
            logger.error(f"❌ No records could be encoded - all {len(df)} failed")
            return None

        # Create projection DataFrame
        projection_df = pd.DataFrame(coords_3d, columns=['0', '1', '2'])
        projection_df['__featrix_row_id'] = rowids
        projection_df['__featrix_row_offset'] = row_offsets
        projection_df['set_columns'] = set_columns_matrix
        projection_df['scalar_columns'] = scalar_columns_matrix
        projection_df['string_columns'] = string_columns_matrix
        projection_df['cluster_pre'] = 0  # No clustering
        projection_df = projection_df.rename(columns={"0": "x", "1": "y", "2": "z"})

        # Create projection data
        duration = time.time() - start_time
        projection_data = {
            'coords': json.loads(projection_df.to_json(orient='records')),
            'epoch': epoch,
            'timestamp': datetime.utcnow().isoformat(),
            'sample_size': len(coords_3d),
            'total_records': data_snapshot['total_records'],
            'encoding_duration_seconds': duration,
            'cluster_messages': {},
            'is_epoch_projection': True,
            'entire_cluster_results': {},
            'consistent_sampling': True,
            'row_ids_for_tracking': rowids,
            'generated_on_cpu_worker': True,
            'session_id': session_id,
            'failed_records': failed_records,
        }

        # Save projection
        output_file = Path(output_dir) / "epoch_projections" / f"projections_epoch_{epoch:03d}.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)

        from lib.utils import atomic_write_json
        atomic_write_json(output_file, projection_data, cls=NumpyEncoder, indent=2)

        logger.info(f"✅ [Session {session_id}] Saved movie frame for epoch {epoch} to {output_file} ({duration:.1f}s on CPU, {len(coords_3d)} points)")

        return str(output_file)

    except Exception as e:
        logger.error(f"❌ [Session {session_id}] Failed to generate movie frame for epoch {epoch}: {e}")
        traceback.print_exc()
        return None

    finally:
        # Release file lock
        if lock_file:
            try:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                lock_file.close()
                logger.debug(f"   ✅ Released lock on {lock_file_path}")
            except Exception as e:
                logger.debug(f"   Could not release lock: {e}")

        # Keep checkpoint files - we have plenty of disk space now
        # These are needed if movie generation fails and needs to retry
        checkpoint_file = Path(checkpoint_path)
        if checkpoint_file.exists():
            logger.debug(f"📦 Keeping checkpoint for future use: {checkpoint_path}")
