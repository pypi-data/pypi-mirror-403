#  -*- coding: utf-8 -*-
#
#  Copyright Featrix, Inc 2023-2025
#
#  Proprietary and Confidential.  Unauthorized use, copying or dissemination
#  of these materials is strictly prohibited.
#
import logging
import math
import os
import random
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
from pydantic import BaseModel
from torch import nn

from featrix.neural.gpu_utils import (
    get_device,
    is_gpu_available,
    aggressive_clear_gpu_cache,
    get_gpu_memory_allocated,
    get_gpu_memory_reserved,
    get_max_gpu_memory_allocated,
    empty_gpu_cache,
)

def _log_gpu_memory_encoders(context: str = ""):
    """Quick GPU memory logging for tracing memory usage in encoders."""
    try:
        if not is_gpu_available():
            return
        allocated = get_gpu_memory_allocated()
        reserved = get_gpu_memory_reserved()
        logger.info(f"📊 GPU [{context}]: Alloc={allocated:.2f}GB Reserved={reserved:.2f}GB")
    except Exception:
        pass
from featrix.neural.featrix_token import TokenStatus
from featrix.neural.featrix_module_dict import FeatrixModuleDict
from featrix.neural.model_config import ColumnEncoderConfigType
from featrix.neural.model_config import ColumnType
from featrix.neural.model_config import FeatrixTableEncoderConfig
from featrix.neural.model_config import JointEncoderConfig
from featrix.neural.model_config import SimpleMLPConfig
from featrix.neural.scalar_codec import ScalarCodec
from featrix.neural.scalar_codec import ScalarEncoder
from featrix.neural.set_codec import SetCodec
from featrix.neural.set_codec import SetEncoder
from featrix.neural.setlist_codec import ListOfASetEncoder
from featrix.neural.setlist_codec import ListsOfASetCodec
from featrix.neural.simple_mlp import SimpleMLP
# from featrix.neural.stopwatch import StopWatch
from featrix.neural.string_codec import StringCodec
from featrix.neural.string_codec import StringEncoder
from featrix.neural.transformer_encoder import JointEncoder
from featrix.neural.vector_codec import VectorCodec
from featrix.neural.vector_codec import VectorEncoder
from featrix.neural.utils import is_internal_column

# Import hybrid encoders for type checking in parameter counts
try:
    from featrix.neural.hybrid_encoders import AddressHybridEncoder, CoordinateHybridEncoder
    HYBRID_ENCODERS_AVAILABLE = True
except ImportError:
    HYBRID_ENCODERS_AVAILABLE = False
    AddressHybridEncoder = None
    CoordinateHybridEncoder = None

logger = logging.getLogger(__name__)


def compute_ranking_metrics(logits: torch.Tensor) -> Dict[str, float]:
    """
    Compute three ranking-aligned metrics from InfoNCE logits.
    
    Args:
        logits: (batch_size, batch_size) similarity matrix where logits[i, j] is the
                similarity between row i (context) and row j (sample).
                Diagonal elements (logits[i, i]) are positive pairs.
                Off-diagonal elements are negative pairs.
    
    Returns:
        Dictionary with:
        - 'positive_rank_mean': Mean rank of positive logit (1 = best, batch_size = worst)
        - 'positive_rank_median': Median rank of positive logit
        - 'recall_at_1': Fraction of rows where positive is top-1
        - 'recall_at_5': Fraction of rows where positive is in top-5
        - 'margin_mean': Mean margin (positive_logit - max_negative_logit) per row
        - 'margin_pct_positive': Fraction of rows where margin > 0
        - 'auc': AUC score (probability that random positive > random negative)
    """
    batch_size = logits.shape[0]
    device = logits.device
    
    # Extract diagonal (positive logits) and off-diagonal (negatives)
    positive_logits = logits.diag()  # (batch_size,)
    
    # Diagonal cosine: mean cos(pred[i], target[i])
    # This is the cleanest "is it aligning" signal - directly measures prediction quality
    diagonal_cosine_mean = float(positive_logits.mean().item())
    diagonal_cosine_std = float(positive_logits.std().item())

    # For each row, get the rank of the positive logit
    # Rank 1 = best, rank batch_size = worst
    ranks = []
    recall_at_1_count = 0
    recall_at_5_count = 0
    recall_at_10_count = 0
    margins = []
    margin_positive_count = 0

    for i in range(batch_size):
        row_logits = logits[i, :]  # (batch_size,)

        # Rank: how many negatives have higher logit than positive?
        # Use argsort to get sorted indices, then find position of diagonal element
        sorted_indices = torch.argsort(row_logits, descending=True)
        rank = (sorted_indices == i).nonzero(as_tuple=True)[0].item() + 1  # 1-indexed
        ranks.append(rank)

        # Recall@k: is positive in top-k?
        if rank == 1:
            recall_at_1_count += 1
        if rank <= 5:
            recall_at_5_count += 1
        if rank <= 10:
            recall_at_10_count += 1

        # Margin: positive - max(negatives)
        # Get all logits except the diagonal
        mask_off_diag = torch.arange(batch_size, device=device) != i
        negative_logits = row_logits[mask_off_diag]
        if len(negative_logits) > 0:
            max_negative = negative_logits.max().item()
            margin = positive_logits[i].item() - max_negative
            margins.append(margin)
            if margin > 0:
                margin_positive_count += 1
    
    # Compute metrics
    ranks_array = np.array(ranks)
    positive_rank_mean = float(ranks_array.mean())
    positive_rank_median = float(np.median(ranks_array))
    recall_at_1 = recall_at_1_count / batch_size
    recall_at_5 = recall_at_5_count / batch_size
    recall_at_10 = recall_at_10_count / batch_size
    
    margins_array = np.array(margins) if margins else np.array([0.0])
    margin_mean = float(margins_array.mean())
    margin_pct_positive = margin_positive_count / batch_size if batch_size > 0 else 0.0
    
    # AUC: Flatten all positives and negatives, compute AUC
    # This is equivalent to: P(positive > negative) when sampling randomly
    positive_flat = positive_logits.detach().cpu().numpy()
    
    # Sample negatives (all off-diagonal elements, but sample if too many)
    mask_off_diag_full = ~torch.eye(batch_size, dtype=torch.bool, device=device)
    negative_flat = logits[mask_off_diag_full].detach().cpu().numpy()
    
    # If too many negatives, sample for efficiency
    if len(negative_flat) > 10000:
        indices = np.random.choice(len(negative_flat), size=10000, replace=False)
        negative_flat = negative_flat[indices]
    
    # Compute AUC: fraction of (positive, negative) pairs where positive > negative
    # This is a simple approximation: count how many negatives each positive beats
    auc_sum = 0.0
    for pos_val in positive_flat:
        auc_sum += (negative_flat < pos_val).sum() / len(negative_flat)
    auc = auc_sum / len(positive_flat)

    # Compute entropy of softmax predictions (per row, then average)
    # High entropy = uniform/uncertain predictions (close to log(N) = random)
    # Low entropy = confident predictions (model is learning)
    softmax_probs = torch.softmax(logits, dim=1)  # (batch_size, batch_size)
    # Entropy: H = -sum(p * log(p)), but avoid log(0) with small epsilon
    eps = 1e-10
    row_entropies = -(softmax_probs * torch.log(softmax_probs + eps)).sum(dim=1)  # (batch_size,)
    entropy_mean = float(row_entropies.mean().item())
    entropy_std = float(row_entropies.std().item())

    # Maximum entropy for reference: log(N) when uniform
    max_entropy = float(np.log(batch_size))
    # Normalized entropy: 1.0 = random/uniform, 0.0 = perfectly confident
    entropy_normalized = entropy_mean / max_entropy if max_entropy > 0 else 1.0

    return {
        'batch_size': batch_size,  # For computing random baseline (1/batch_size)
        'diagonal_cosine_mean': diagonal_cosine_mean,  # Mean cos(pred[i], target[i]) - cleanest alignment signal
        'diagonal_cosine_std': diagonal_cosine_std,
        'positive_rank_mean': positive_rank_mean,
        'positive_rank_median': positive_rank_median,
        'recall_at_1': recall_at_1,
        'recall_at_5': recall_at_5,
        'recall_at_10': recall_at_10,  # If R@1 low but R@10 high = close but crowded
        'margin_mean': margin_mean,  # cos(pred[i], target[i]) - max(cos(pred[i], target[j!=i]))
        'margin_pct_positive': margin_pct_positive,
        'auc': auc,
        'entropy_mean': entropy_mean,
        'entropy_std': entropy_std,
        'entropy_max': max_entropy,
        'entropy_normalized': entropy_normalized,  # 1.0 = random, 0.0 = confident
    }


def _token_status_to_binary_mask(token_status_mask: torch.Tensor) -> torch.Tensor:
    """
    Convert TokenStatus mask to binary mask for relationship extractor.
    
    Args:
        token_status_mask: (batch_size, n_cols) tensor of TokenStatus values
            - TokenStatus.OK (2) or TokenStatus.MARGINAL (3) → 1 (present)
            - TokenStatus.NOT_PRESENT (0) or TokenStatus.UNKNOWN (1) → 0 (masked)
    
    Returns:
        Binary mask (batch_size, n_cols) where 1 = present, 0 = masked
    """
    # OK (2) and MARGINAL (3) are considered present
    # NOT_PRESENT (0) and UNKNOWN (1) are masked
    binary_mask = (token_status_mask >= TokenStatus.OK).float()
    return binary_mask


# FIXME: I think these functions can all go away by standardizing the Codec
# FIXME: constructor to (df_col, detector) and let the codec ask the detector
# FIXME: for whatever it needs--uniques, metadata will have been calculated by
# FIXME: the detector. [MH 27 Sep 2023]
def create_set_codec(df_col, embed_dim, loss_type="cross_entropy", detector=None, string_cache=None, vocabulary_override=None):
    """
    Create a SetCodec for a column.
    
    Args:
        df_col: DataFrame column to extract vocabulary from
        embed_dim: Embedding dimension
        loss_type: Loss type for training
        detector: Column detector (for sparsity info)
        string_cache: String cache path for semantic initialization
        vocabulary_override: Optional set of vocabulary members to use instead of extracting from df_col.
                            This is used when reconstructing from checkpoint to ensure vocabulary matches.
    """
    # If vocabulary override is provided, use it directly (for checkpoint reconstruction)
    if vocabulary_override is not None:
        uniques = set(vocabulary_override)
        logger.debug(f"   Using vocabulary override: {len(uniques)} members")
    else:
        # Convert all values in the column to strings.
        # TODO: how will this affect encoding values from other dataframes
        # that have the same column? We will need to make sure the same pre-processing
        # is applied to both.
        df_col = df_col.astype(str)
        
        # CRITICAL: Normalize numeric strings to prevent "1" vs "1.0" from being different classes
        # This ensures that 1, 1.0, "1", "1.0" all become "1"
        def normalize_numeric_string(val):
            if pd.isna(val) or val in ['nan', 'NaN', 'None', '', ' ']:
                return val
            try:
                # Try to convert to float, then back to int if it's a whole number
                float_val = float(val)
                if float_val.is_integer():
                    return str(int(float_val))
                return str(float_val)
            except (ValueError, TypeError):
                # Not numeric, return as-is
                return str(val)
        
        df_col_normalized = df_col.apply(normalize_numeric_string)
        uniques = set(df_col_normalized.unique())
    
    # Calculate sparsity ratio from detector (if available) or from data
    sparsity_ratio = 0.0
    if detector is not None and hasattr(detector, '_numNulls'):
        # Use pre-calculated null counts from detector
        total_count = detector._numNulls + detector._numNotNulls
        if total_count > 0:
            sparsity_ratio = float(detector._numNulls) / float(total_count)
    else:
        # Fallback: calculate from data (for backward compatibility)
        null_values = {"nan", "NaN", "Nan", "NAN", "None", "none", "NONE", "", " "}
        null_count = df_col.isin(null_values).sum()
        total_count = len(df_col)
        sparsity_ratio = float(null_count / total_count) if total_count > 0 else 0.0
    
    # print("@@@@@@@ uniques = ", uniques)
    return SetCodec(uniques, embed_dim, loss_type=loss_type, sparsity_ratio=sparsity_ratio, string_cache=string_cache)


def create_scalar_codec(df_col, embed_dim):
    # Convert scalar columns to floats.
    # This converts nan values to float("nan").
    df_col = df_col.astype(float, errors="ignore")
    
    # Compute rich statistics for adaptive encoding
    df_clean = df_col.dropna()
    
    if len(df_clean) == 0:
        # All NaN column - use dummy stats
        stats = {
            'mean': 0.0,
            'std': 1.0,
            'median': 0.0,
            'q10': 0.0,
            'q90': 1.0,
            'q25': 0.0,
            'q75': 1.0,
            'min': 0.0,
            'max': 1.0,
        }
    else:
        stats = {
            'mean': float(df_clean.mean()),
            'std': float(df_clean.std()) if len(df_clean) > 1 else 1.0,
            'median': float(df_clean.median()),
            'q10': float(df_clean.quantile(0.10)),
            'q90': float(df_clean.quantile(0.90)),
            'q25': float(df_clean.quantile(0.25)),
            'q75': float(df_clean.quantile(0.75)),
            'min': float(df_clean.min()),
            'max': float(df_clean.max()),
        }
    
    return ScalarCodec(stats, embed_dim)


def create_timestamp_codec(df_col, embed_dim):
    """
    Create a TimestampCodec for timestamp columns.
    
    Args:
        df_col: DataFrame column with datetime values
        embed_dim: Embedding dimension
        
    Returns:
        TimestampCodec instance
    """
    from featrix.neural.timestamp_codec import TimestampCodec
    return TimestampCodec(enc_dim=embed_dim)


# def create_lists_of_a_set_codec(df_col, detector, embed_dim):
#     df_col = df_col.astype(str)
#     uniques = set(df_col.unique())
#     return ListsOfASetCodec(uniques, detector.get_delimiter(), embed_dim)


def create_string_codec(df_col, detector, embed_dim, string_cache, sentence_model=None, validation_df_col=None):
    """
    Create StringCodec with adaptive string analysis.
    
    Analyzes the column to detect:
    - Random strings (UUIDs, hashes) → mark as random
    - Delimited fields ("a,b,c") → preprocess with newlines
    - Null variants ("N/A", "none") → handled by semantic similarity
    
    Args:
        df_col: DataFrame column from training data
        detector: Column detector
        embed_dim: Embedding dimension
        string_cache: Path to string cache
        sentence_model: BERT model for analysis (optional)
        validation_df_col: Optional DataFrame column from validation data (to ensure all values are cached)
    """
    from featrix.neural.string_analysis import (
        precompute_string_properties,
        detect_random_strings,
        detect_delimiter
    )
    
    col_name = detector._debugColName
    
    # Precompute all expensive operations once
    logger.info(f"🔍 Analyzing string column: '{col_name}'")
    precomputed = precompute_string_properties(df_col, col_name, sentence_model)
    
    # Check if random (UUIDs, hashes, transaction IDs)
    random_result = detect_random_strings(precomputed)
    is_random = random_result["is_random"]
    
    if is_random:
        logger.warning(f"   🚫 RANDOM STRING DETECTED (confidence: {random_result['confidence']:.2f})")
        logger.warning(f"      Signals: {', '.join(random_result['signals'][:3])}")
        logger.warning(f"      → Creating codec with ZERO contribution")
    
    # Check for delimiters - controlled by config.json
    from featrix.neural.sphere_config import get_config
    if get_config().use_delimiter_preprocessing():
        delimiter_result = detect_delimiter(precomputed)
        delimiter = delimiter_result["delimiter"] if delimiter_result["has_delimiter"] else None
        
        if delimiter:
            logger.info(f"   🔧 DELIMITER DETECTED: '{delimiter}' → will preprocess strings before BERT encoding")
    else:
        delimiter = None
        logger.debug(f"   Delimiter preprocessing disabled (config.json: use_delimiter_preprocessing=false)")
    
    # Collect unique values from BOTH training and validation data
    # This ensures all values encountered during training are cached
    train_unique_values = df_col.dropna().astype(str).unique().tolist()
    
    # Also collect from validation data if provided
    if validation_df_col is not None:
        val_unique_values = validation_df_col.dropna().astype(str).unique().tolist()
        # Combine and deduplicate
        all_unique_values = list(set(train_unique_values + val_unique_values))
        train_count = len(train_unique_values)
        val_count = len(val_unique_values)
        logger.info(f"   📊 Collected {train_count} unique values from training, {val_count} from validation")
        logger.info(f"   📊 Total unique values: {len(all_unique_values)} (after deduplication)")
    else:
        all_unique_values = train_unique_values
        logger.info(f"   📊 Collected {len(all_unique_values)} unique values from training data")
    
    # Apply delimiter preprocessing to cache keys (must match tokenize() behavior)
    if delimiter:
        from featrix.neural.string_analysis import preprocess_delimited_string
        preprocessed_values = [preprocess_delimited_string(v, delimiter) for v in all_unique_values]
        logger.info(f"   📊 Caching {len(preprocessed_values)} unique values (delimiter-preprocessed)")
    else:
        preprocessed_values = all_unique_values
        logger.info(f"   📊 Caching {len(preprocessed_values)} unique values (no delimiter preprocessing)")
    
    # Create codec with preprocessed initial values for cache
    codec = StringCodec(
        enc_dim=embed_dim,
        debugName=col_name,
        initial_values=preprocessed_values,  # Preprocessed to match tokenize() lookup keys
        string_cache=string_cache,
        delimiter=delimiter,  # Codec will apply same preprocessing during tokenize()
        is_random_column=is_random
    )
    
    # Store adaptive analysis for encoder config selection
    codec._adaptive_analysis = {
        "precomputed": precomputed,
        "is_random": is_random,
        "delimiter": delimiter,
    }
    
    return codec


def create_vector_codec(df_col, detector, embed_dim):
    in_dim_len = detector.get_input_embedding_length()
    return VectorCodec(
        in_dim=in_dim_len,
        enc_dim=embed_dim,
        # bert_encoding_length=bl,
        debugName=detector._debugColName,
    )


def create_url_codec(df_col, detector, embed_dim, string_cache):
    """
    Create URLCodec for URL/domain columns.
    
    Args:
        df_col: DataFrame column containing URLs
        detector: Column detector
        embed_dim: Embedding dimension
        string_cache: StringCache for encoding domain/path components
    """
    from featrix.neural.url_codec import URLCodec
    
    col_name = detector._debugColName
    logger.info(f"🌐 Creating URL codec for column: '{col_name}'")
    
    codec = URLCodec(
        embed_dim=embed_dim,
        string_cache=string_cache,
        debugName=col_name
    )
    
    return codec


def create_domain_codec(df_col, detector, embed_dim, string_cache):
    """
    Create DomainCodec for domain name columns.
    
    Args:
        df_col: DataFrame column containing domain names
        detector: Column detector
        embed_dim: Embedding dimension
        string_cache: StringCache for encoding domain components
    """
    from featrix.neural.domain_codec import DomainCodec
    
    col_name = detector._debugColName
    logger.info(f"🌐 Creating domain codec for column: '{col_name}'")
    
    # DomainCodec needs a StringCache instance, not just a filename
    # If string_cache is a string (filename), we need to create a StringCache
    if isinstance(string_cache, str):
        from featrix.neural.simple_string_cache import SimpleStringCache as StringCache
        cache_instance = StringCache(string_cache_filename=string_cache, readonly=False)
    else:
        cache_instance = string_cache
    
    codec = DomainCodec(
        enc_dim=embed_dim,
        string_cache=cache_instance,
        debugName=col_name
    )
    
    return codec


def create_json_codec(df_col, detector, embed_dim, json_cache_filename=None, child_es_session_id: str = None):
    """
    Create JsonCodec with ES lookup for JSON columns.
    
    Extracts schema fields from JSON values, queries API for matching ES,
    and creates JsonCodec with the ES if found.
    
    Args:
        df_col: DataFrame column with JSON values
        detector: Column detector
        embed_dim: Embedding dimension
        json_cache_filename: Path to JSON cache file
        child_es_session_id: Session ID of child ES to use for encoding (via API)
        
    Returns:
        JsonCodec instance
    """
    from featrix.neural.json_codec import JsonCodec
    import json
    import ast
    from collections import Counter
    
    col_name = detector._debugColName if hasattr(detector, '_debugColName') else "json_col"
    
    # Extract schema fields from JSON values
    schema_fields = set()
    sample_values = df_col.dropna().head(100)  # Sample first 100 non-null values
    
    for value in sample_values:
        try:
            # Parse JSON value
            if isinstance(value, str):
                value = value.strip()
                if value.startswith('{'):
                    try:
                        parsed = json.loads(value)
                    except:
                        try:
                            parsed = ast.literal_eval(value)
                        except:
                            continue
                elif value.startswith('['):
                    try:
                        parsed = json.loads(value)
                        if isinstance(parsed, list) and len(parsed) > 0:
                            parsed = parsed[0]  # Use first dict
                    except:
                        try:
                            parsed = ast.literal_eval(value)
                            if isinstance(parsed, list) and len(parsed) > 0:
                                parsed = parsed[0]
                        except:
                            continue
                else:
                    continue
            elif isinstance(value, dict):
                parsed = value
            elif isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
                parsed = value[0]
            else:
                continue
            
            # Extract keys from dict
            if isinstance(parsed, dict):
                schema_fields.update(parsed.keys())
        except Exception:
            continue
    
    schema_fields = sorted(list(schema_fields))
    logger.info(f"🔍 JsonCodec '{col_name}': Extracted {len(schema_fields)} schema fields: {schema_fields[:10]}{'...' if len(schema_fields) > 10 else ''}")
    
    # Query API for matching ES
    embedding_space = None
    if schema_fields:
        try:
            import requests
            from config import config as app_config
            
            # Build API URL
            api_base = getattr(app_config, 'api_base_url', 'http://localhost:8000')
            if not api_base.startswith('http'):
                api_base = f"http://{api_base}"
            
            # Query endpoint
            schema_fields_str = ','.join(schema_fields)
            url = f"{api_base}/api-sphere/json-encoders"
            params = {"schema_fields": schema_fields_str}
            
            logger.info(f"🔍 Querying JSON encoder API: {url} with fields: {schema_fields_str}")
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                matched_es = result.get("matched_es")
                
                if matched_es:
                    es_path = matched_es.get("embedding_space_path")
                    logger.info(f"✅ Found matching ES: {matched_es.get('name')} at {es_path}")
                    
                    # Load embedding space using io_utils to handle CUDA->CPU mapping properly
                    try:
                        from featrix.neural.io_utils import load_embedded_space as load_es_from_io_utils
                        embedding_space = load_es_from_io_utils(es_path)
                        logger.info(f"✅ Loaded embedding space for JsonCodec '{col_name}'")
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to load ES from {es_path}: {e}")
                else:
                    logger.info(f"ℹ️ No matching ES found for schema: {schema_fields}")
            else:
                logger.warning(f"⚠️ API query failed with status {response.status_code}: {response.text}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to query JSON encoder API: {e}")
            import traceback
            logger.debug(traceback.format_exc())
    
    # Get initial values for caching
    initial_values = df_col.dropna().tolist()[:1000]  # Limit to first 1000 for caching
    
    # Create JsonCodec
    # Prefer child_es_session_id over embedding_space (for API calls)
    codec = JsonCodec(
        enc_dim=embed_dim,
        debugName=col_name,
        initial_values=initial_values,
        json_cache_filename=json_cache_filename,
        embedding_space=embedding_space if not child_es_session_id else None,  # Only use local ES if no child ES session
        schema_fields=schema_fields,
        child_es_session_id=child_es_session_id
    )
    
    return codec


class LayerEncoder(nn.Module):
    def __init__(self, segments):
        super().__init__()

        modules, input_lengths = list(zip(*segments))
        self.layer_modules = nn.ModuleList(modules)
        self.input_lengths = input_lengths

        self.total_length = sum(self.input_lengths)

    def forward(self, input):
        assert input.shape[1] == self.total_length, (
            "input.shape = %s; total_length = %s; input_lengths = %s"
            % (
                input.shape,
                self.total_length,
                self.input_lengths,
            )
        )

        segments = torch.split(input, self.input_lengths, dim=1)
        encodings = [
            module(segment) for module, segment in zip(self.layer_modules, segments)
        ]

        return torch.cat(encodings, dim=1)


class ColumnEncoders(nn.Module):
    # This is the first layer that takes in a dictionary-like batch, and
    # returns a completely vectorized batch.

    # NOTE: col_order can contain duplicates, e.g. when the same columns is
    # fed into multiple encoders.

    def __init__(self, col_configs, col_order, col_types, col_codecs, hybrid_groups=None):
        super().__init__()

        self.col_order = col_order
        # CRITICAL: Store col_codecs so they can be extracted during checkpoint reconstruction
        # When loading old checkpoints or reconstructing from .pth files, we need access to codecs
        self.col_codecs = col_codecs
        self.col_types = col_types or {}  # Store col_types for raw timestamp feature extraction
        self.hybrid_groups = hybrid_groups or {}

        # Track which columns are merged into hybrid encoders
        self.merged_columns = set()
        self.hybrid_encoder_map = {}  # Maps column names to their hybrid group name
        
        self.encoders = FeatrixModuleDict()
        
        # Step 1: Create hybrid encoders for MERGE strategy
        if self.hybrid_groups:
            logger.info(f"🔗 HYBRID ENCODERS: Processing {len(self.hybrid_groups)} detected groups")
            
            for group_name, group_info in self.hybrid_groups.items():
                strategy = group_info.get('strategy')
                group_type = group_info.get('type')
                columns = group_info.get('columns', [])
                
                logger.info(f"   📦 {group_name}: type={group_type}, strategy={strategy}, columns={columns}")
                
                if strategy == 'merge':
                    # Create composite encoder
                    try:
                        if group_type == 'address' and HYBRID_ENCODERS_AVAILABLE:
                            # Get string cache from one of the column codecs
                            string_cache = None
                            for col in columns:
                                codec = col_codecs.get(col)
                                if hasattr(codec, 'string_cache') and codec.string_cache:
                                    from featrix.neural.string_codec import get_global_string_cache
                                    string_cache = get_global_string_cache(
                                        cache_filename=codec.string_cache,
                                        initial_values=None,
                                        debug_name=group_name
                                    )
                                    break
                            
                            # Create address encoder with same config as first column
                            first_col = columns[0]
                            col_config = col_configs[first_col]
                            
                            encoder = AddressHybridEncoder(
                                config=col_config,
                                string_cache=string_cache,
                                column_names=columns,
                                column_name=group_name
                            )
                            self.encoders[group_name] = encoder
                            self.merged_columns.update(columns)
                            
                            # Map each column to its hybrid group
                            for col in columns:
                                self.hybrid_encoder_map[col] = group_name
                            
                            logger.info(f"      ✅ Created AddressHybridEncoder: {group_name}")
                            logger.info(f"         Merged columns: {columns}")
                        
                        elif group_type == 'coordinates' and HYBRID_ENCODERS_AVAILABLE:
                            if len(columns) >= 2:
                                lat_col = columns[0]
                                long_col = columns[1]
                                
                                # Use config from first column
                                col_config = col_configs[lat_col]
                                
                                encoder = CoordinateHybridEncoder(
                                    config=col_config,
                                    lat_col=lat_col,
                                    long_col=long_col,
                                    column_name=group_name
                                )
                                self.encoders[group_name] = encoder
                                self.merged_columns.update(columns)
                                
                                # Map each column to its hybrid group
                                for col in columns:
                                    self.hybrid_encoder_map[col] = group_name
                                
                                logger.info(f"      ✅ Created CoordinateHybridEncoder: {group_name}")
                                logger.info(f"         Merged columns: {columns}")
                            else:
                                logger.warning(f"      ⚠️  Coordinates group needs 2 columns, got {len(columns)}")
                        
                        else:
                            if not HYBRID_ENCODERS_AVAILABLE:
                                logger.warning(f"      ⚠️  Hybrid encoders not available - falling back to individual encoding")
                            else:
                                logger.warning(f"      ⚠️  Unknown group type '{group_type}' - skipping")
                    
                    except Exception as e:
                        logger.error(f"      ❌ Failed to create hybrid encoder for {group_name}: {e}")
                        logger.error(f"         Falling back to individual column encoding")
                
                elif strategy == 'relationship':
                    logger.info(f"      ℹ️  RELATIONSHIP strategy - handled by JointEncoder, not ColumnEncoders")
                
                else:
                    logger.warning(f"      ⚠️  Unknown strategy '{strategy}' - skipping")
            
            if self.merged_columns:
                logger.info(f"   ✅ Total columns merged: {len(self.merged_columns)}")
                logger.info(f"      Merged: {sorted(self.merged_columns)}")
            else:
                logger.info(f"   ℹ️  No columns merged (all groups use RELATIONSHIP strategy or failed)")
        
        # Step 2: Create individual encoders for non-merged columns
        logger.info(f"🔧 Creating individual encoders for {len([c for c in col_types if c not in self.merged_columns])} columns")
        
        for col_name, col_type in col_types.items():
            # Skip columns that were merged into hybrid encoders
            if col_name in self.merged_columns:
                logger.debug(f"   ⏭️  Skipping {col_name} (merged into {self.hybrid_encoder_map[col_name]})")
                continue
            
            col_config = col_configs[col_name]
            if col_type == ColumnType.SET:
                # Pass column_name for semantic initialization
                codec = col_codecs.get(col_name)
                member_names = codec.member_names if hasattr(codec, 'member_names') else None
                # ALWAYS get string cache for semantic initialization (make all SetEncoders adaptive)
                from featrix.neural.string_codec import get_global_string_cache
                # Try to get string cache from codec, or use default global cache
                cache_filename = None
                if hasattr(codec, 'string_cache') and codec.string_cache:
                    cache_filename = codec.string_cache
                # Always get the global string cache object (will use default if filename is None)
                string_cache_obj = get_global_string_cache(
                    cache_filename=cache_filename,
                    initial_values=None,  # Values already cached during codec creation
                    debug_name=col_name
                )
                
                # ORDINAL DETECTION: Check if this SET column has ordinal semantics
                # PRIORITY: 1) config already has it, 2) codec has it (from previous save), 3) detect fresh
                ordinal_info = getattr(col_config, 'ordinal_info', None)
                if ordinal_info:
                    logger.debug(f"   📊 {col_name}: Using ordinal_info from config")
                elif getattr(codec, 'ordinal_info', None):
                    ordinal_info = codec.ordinal_info
                    logger.info(f"   📊 {col_name}: Using ordinal_info from codec (preserved from previous training)")
                elif member_names and len(member_names) >= 2 and len(member_names) <= 20:
                    # Only detect ordinal for reasonable cardinality (2-20 categories)
                    try:
                        from featrix.neural.llm.schema_analyzer import detect_ordinal_categories
                        ordinal_result = detect_ordinal_categories(col_name, member_names)
                        if ordinal_result.get('is_ordinal', False):
                            ordinal_info = ordinal_result
                            logger.info(f"   📊 {col_name}: ORDINAL detected (confidence={ordinal_result.get('confidence', 0):.2f})")
                            logger.info(f"      Order: {ordinal_result.get('ordered_values', [])[:5]}{'...' if len(ordinal_result.get('ordered_values', [])) > 5 else ''}")
                    except Exception as e:
                        logger.debug(f"   ⚠️  Ordinal detection failed for {col_name}: {e}")
                
                # Update config with ordinal info if detected
                if ordinal_info:
                    # Create a new config with ordinal_info added
                    config_dict = col_config.model_dump() if hasattr(col_config, 'model_dump') else col_config.__dict__.copy()
                    config_dict['ordinal_info'] = ordinal_info
                    from featrix.neural.model_config import SetEncoderConfig
                    col_config = SetEncoderConfig(**config_dict)
                    # CRITICAL: Store ordinal_info in codec for persistence across save/load
                    # Without this, ordinal embeddings are lost when model is reloaded!
                    codec.ordinal_info = ordinal_info
                
                encoder = SetEncoder(col_config, string_cache=string_cache_obj, column_name=col_name, member_names=member_names)
            elif col_type == ColumnType.SCALAR:
                # Use AdaptiveScalarEncoder with stats from codec
                codec = col_codecs[col_name]
                from featrix.neural.scalar_codec import AdaptiveScalarEncoder
                # Pass normalize flag from config to prevent double normalization
                normalize = col_config.normalize if hasattr(col_config, 'normalize') else True
                encoder = AdaptiveScalarEncoder(codec.stats, col_config.d_out, column_name=col_name, normalize=normalize)
            elif col_type == ColumnType.TIMESTAMP:
                # Use TimestampEncoder
                from featrix.neural.timestamp_codec import TimestampEncoder
                encoder = TimestampEncoder(col_config, column_name=col_name)
            elif col_type == ColumnType.FREE_STRING:
                encoder = StringEncoder(col_config, column_name=col_name)
            elif col_type == ColumnType.LIST_OF_A_SET:
                encoder = ListOfASetEncoder(col_config)
            elif col_type == ColumnType.VECTOR:
                encoder = VectorEncoder(col_config)
            elif col_type == ColumnType.URL:
                # URL codec handles its own encoding, just pass through
                codec = col_codecs[col_name]
                encoder = codec.encoder
            elif col_type == ColumnType.JSON:
                # JSON codec handles its own encoding via embedding space
                # The codec's tokenize() already produces the final embedding
                # We just need a pass-through encoder
                from featrix.neural.json_codec import JsonEncoder
                codec = col_codecs[col_name]
                encoder = JsonEncoder(col_config, codec)
            elif col_type == ColumnType.DOMAIN:
                # Domain codec uses DomainEncoder
                from featrix.neural.domain_codec import DomainEncoder
                codec = col_codecs[col_name]
                domain_config = DomainEncoder.get_default_config(col_config.d_out, col_config.dropout if hasattr(col_config, 'dropout') else 0.2)
                encoder = DomainEncoder(domain_config, codec.string_cache, column_name=col_name)
            elif col_type == ColumnType.EMAIL:
                # Email codec uses EmailEncoder
                from featrix.neural.email_codec import EmailEncoder, get_email_encoder_config
                codec = col_codecs[col_name]
                email_config = get_email_encoder_config(col_config.d_out)
                encoder = EmailEncoder(email_config, codec.string_cache, column_name=col_name)

            self.encoders[col_name] = encoder
    
    def __setstate__(self, state):
        """
        Restore state and validate/fix col_order if it's empty.
        This handles cases where col_order might be lost during unpickling.
        """
        logger = logging.getLogger(__name__)

        # DIAGNOSTIC: Log what's in the state before restoring
        col_order_in_state = state.get('col_order', 'NOT_IN_STATE')
        encoders_in_state = 'encoders' in state
        codecs_in_state = 'col_codecs' in state

        if col_order_in_state == 'NOT_IN_STATE':
            logger.error(f"🚨 ColumnEncoders.__setstate__: col_order is NOT IN STATE DICT!")
        elif isinstance(col_order_in_state, list) and len(col_order_in_state) == 0:
            logger.error(f"🚨 ColumnEncoders.__setstate__: col_order is EMPTY LIST in state dict!")
        else:
            logger.debug(f"✅ ColumnEncoders.__setstate__: col_order found in state: {len(col_order_in_state) if isinstance(col_order_in_state, list) else 'not a list'}")
        
        logger.info(f"   State has encoders: {encoders_in_state}, codecs: {codecs_in_state}")
        if encoders_in_state and state.get('encoders'):
            encoder_count = len(state['encoders']) if hasattr(state['encoders'], '__len__') else 'unknown'
            logger.info(f"   Encoders in state: {encoder_count}")
        
        # Restore state first
        self.__dict__.update(state)
        
        # CRITICAL: Validate and fix col_order after unpickling
        # This handles cases where col_order might be empty in the pickle file
        # or lost during unpickling
        if not hasattr(self, 'col_order') or len(self.col_order) == 0:
            logger.warning(f"⚠️  ColumnEncoders.__setstate__: col_order is empty after unpickling - attempting recovery")
            
            # Try to recover from encoders (most reliable)
            if hasattr(self, 'encoders') and self.encoders and len(self.encoders) > 0:
                encoder_keys = list(self.encoders.keys())
                self.col_order = encoder_keys.copy()
                logger.warning(f"   ✅ Recovered col_order from {len(encoder_keys)} encoders during unpickling")
            # Try to recover from codecs
            elif hasattr(self, 'col_codecs') and self.col_codecs:
                codec_keys = list(self.col_codecs.keys())
                self.col_order = codec_keys.copy()
                logger.warning(f"   ✅ Recovered col_order from {len(codec_keys)} codecs during unpickling")
            else:
                raise RuntimeError(
                    "ColumnEncoders.col_order is empty and cannot be recovered. "
                    "No encoders or codecs available to recover from. "
                    "Model pickle is corrupted."
                )

        # Backward compatibility: add col_types if missing (for old checkpoints)
        if not hasattr(self, 'col_types'):
            self.col_types = {}

    def get_effective_column_order(self):
        """
        Get column order with hybrid group names replacing merged columns.
        
        Example:
            Original: ['id', 'shipping_addr1', 'shipping_city', 'shipping_state', 'price']
            Effective: ['id', 'hybrid_group_1', 'price']
        
        Returns:
            List of column/group names in order
        """
        # Defensive check: ensure hybrid_groups exists (for backward compatibility with old checkpoints)
        if not hasattr(self, 'hybrid_groups'):
            self.hybrid_groups = {}
        if not hasattr(self, 'merged_columns'):
            self.merged_columns = set()
        if not hasattr(self, 'hybrid_encoder_map'):
            self.hybrid_encoder_map = {}
        
        if not self.hybrid_groups or not self.merged_columns:
            return self.col_order
        
        effective_order = []
        seen_groups = set()
        
        for col in self.col_order:
            if col in self.merged_columns:
                # This column is part of a hybrid group
                group_name = self.hybrid_encoder_map[col]
                if group_name not in seen_groups:
                    # Add the group name at the position of the first column in the group
                    effective_order.append(group_name)
                    seen_groups.add(group_name)
                # Skip the individual column
            else:
                # Regular column, keep it
                effective_order.append(col)
        
        return effective_order

    def forward(self, batch_data):
        # Defensive check: ensure hybrid-related attributes exist (for backward compatibility with old checkpoints)
        if not hasattr(self, 'hybrid_groups'):
            self.hybrid_groups = {}
        if not hasattr(self, 'merged_columns'):
            self.merged_columns = set()
        if not hasattr(self, 'hybrid_encoder_map'):
            self.hybrid_encoder_map = {}
        
        short_encoding_list = []
        full_encoding_list = []
        
        # CRITICAL: Check if col_order is empty - try to recover from encoders or codecs
        if len(self.col_order) == 0:
            logger.error(f"💥 CRITICAL: col_order is EMPTY! No columns to encode!")
            logger.error(f"   Available encoders: {list(self.encoders.keys())}")
            logger.error(f"   Batch data columns: {list(batch_data.keys())}")
            logger.error(f"   Available codecs: {list(self.col_codecs.keys()) if hasattr(self, 'col_codecs') and self.col_codecs else 'None'}")
            
            # Try to recover col_order from encoders or codecs
            recovered_col_order = None
            
            # First, try to recover from encoders (most reliable - these are the actual encoders that exist)
            if self.encoders and len(self.encoders) > 0:
                # Use encoder keys directly as col_order
                # These keys may be individual column names or hybrid group names (for MERGE strategy)
                # The get_effective_column_order() method will handle any transformations needed
                encoder_keys = list(self.encoders.keys())
                recovered_col_order = encoder_keys.copy()
                
                if recovered_col_order:
                    logger.warning(f"   ⚠️  RECOVERY: Reconstructed col_order from {len(self.encoders)} encoders")
                    logger.warning(f"   Recovered {len(recovered_col_order)} columns: {recovered_col_order[:20]}{'...' if len(recovered_col_order) > 20 else ''}")
                    self.col_order = recovered_col_order
                    logger.warning(f"   ✅ Successfully recovered col_order - continuing with encoding")
            
            # Fallback: try to recover from codecs if encoders didn't work
            if not recovered_col_order and hasattr(self, 'col_codecs') and self.col_codecs:
                codec_keys = list(self.col_codecs.keys())
                if codec_keys:
                    logger.warning(f"   ⚠️  RECOVERY: Attempting to reconstruct col_order from {len(self.col_codecs)} codecs")
                    logger.warning(f"   Codec keys: {codec_keys[:20]}{'...' if len(codec_keys) > 20 else ''}")
                    # Use codec keys as col_order (may not match encoder order exactly, but better than nothing)
                    recovered_col_order = codec_keys
                    self.col_order = recovered_col_order
                    logger.warning(f"   ⚠️  Recovered col_order from codecs - order may not match encoder order exactly")
            
            # If recovery failed, raise error
            if not recovered_col_order or len(self.col_order) == 0:
                logger.error(f"   ❌ RECOVERY FAILED: Could not reconstruct col_order from encoders or codecs")
                raise RuntimeError(
                    f"Encoder has empty col_order - cannot encode any columns. "
                    f"This indicates the encoder was saved incorrectly or the model is corrupted. "
                    f"Available encoders: {list(self.encoders.keys())}, "
                    f"Available codecs: {list(self.col_codecs.keys()) if hasattr(self, 'col_codecs') and self.col_codecs else 'None'}"
                )
        
        # Handle missing columns gracefully for fine-tuning on different datasets
        from featrix.neural.featrix_token import TokenBatch, Token
        batch_columns = set(batch_data.keys())
        missing_columns = [col for col in self.col_order if col not in batch_columns]
        
        if missing_columns:
            # Log once per column encoder instance (not every batch)
            if not hasattr(self, '_missing_columns_logged'):
                logger.warning(f"⚠️  Fine-tuning: {len(missing_columns)} columns from ES not in current data - using NULL values. Missing: {missing_columns}")
                self._missing_columns_logged = True
            
            # Create empty TokenBatch for missing columns (will use NOT_PRESENT tokens)
            # Get batch size from first available column
            batch_size = None
            for col_name in self.col_order:
                if col_name in batch_data:
                    batch_size = len(batch_data[col_name].value) if hasattr(batch_data[col_name], 'value') else len(batch_data[col_name])
                    break
            
            if batch_size is None:
                logger.error(f"💥 CRITICAL: All columns missing from batch data!")
                raise ValueError("Cannot encode: all expected columns are missing from batch data")
            
            # Create NOT_PRESENT token batches for missing columns
            for col_name in missing_columns:
                # Get the codec for this column to create proper NOT_PRESENT tokens
                encoder = self.encoders.get(col_name)
                if encoder and hasattr(encoder, 'codec') and hasattr(encoder.codec, 'get_not_present_token'):
                    # Use codec's proper NOT_PRESENT token (preserves correct dimensionality for each type)
                    not_present_token = encoder.codec.get_not_present_token()
                    null_tokens = [not_present_token] * batch_size
                else:
                    # Fallback: Create generic NOT_PRESENT tokens (None values that TokenBatch converts to NOT_PRESENT)
                    # This will create scalar tokens which may cause dimension issues for some encoder types
                    null_tokens = [None] * batch_size
                batch_data[col_name] = TokenBatch(null_tokens)
            
        # Use effective column order (which includes hybrid group names)
        effective_col_order = self.get_effective_column_order()
        
        for col_or_group_name in effective_col_order:
            encoder = self.encoders[col_or_group_name]
            
            # Check if this is a hybrid encoder
            if col_or_group_name in self.hybrid_groups:
                # This is a hybrid group - collect data from all merged columns
                group_info = self.hybrid_groups[col_or_group_name]
                columns = group_info.get('columns', [])
                
                # Create dict of column data for hybrid encoder
                group_batch_data = {col: batch_data[col] for col in columns if col in batch_data}
                
                # Call hybrid encoder with dict of column data
                short_col_encoding, full_col_encoding = encoder(group_batch_data)
            else:
                # Regular column encoder
                col_data = batch_data[col_or_group_name]
                short_col_encoding, full_col_encoding = encoder(col_data)
            
            # CRITICAL: Ensure encodings are 2D [batch_size, d_model]
            # Some encoders might accidentally return 3D tensors [batch_size, seq_len, d_model]
            if len(full_col_encoding.shape) == 3:
                logger.error(f"💥 ENCODER BUG: Column '{col_or_group_name}' encoder returned 3D tensor: {full_col_encoding.shape}")
                logger.error(f"   Encoder type: {type(encoder).__name__}")
                logger.error(f"   Expected 2D [batch_size, d_model], got 3D [batch_size, seq_len, d_model]")
                logger.error(f"   Auto-fixing by averaging over sequence dimension")
                # Fix by averaging over sequence dimension
                full_col_encoding = full_col_encoding.mean(dim=1)
                if len(short_col_encoding.shape) == 3:
                    short_col_encoding = short_col_encoding.mean(dim=1)

            # NaN ASSERTION: Fail fast if column encoder produces NaN
            assert not torch.isnan(full_col_encoding).any(), f"NaN in column encoding output [{col_or_group_name}], encoder={type(encoder).__name__}"
            assert not torch.isinf(full_col_encoding).any(), f"Inf in column encoding output [{col_or_group_name}], encoder={type(encoder).__name__}"

            short_encoding_list.append(short_col_encoding)
            full_encoding_list.append(full_col_encoding)

        # Create a tensor with all the token statuses
        # For hybrid groups, use status from first column in group
        status_list = []
        for col_or_group_name in effective_col_order:
            if col_or_group_name in self.hybrid_groups:
                # Use status from first column in hybrid group
                group_info = self.hybrid_groups[col_or_group_name]
                first_col = group_info['columns'][0]
                status_list.append(batch_data[first_col].status)
            else:
                status_list.append(batch_data[col_or_group_name].status)

        # Extract raw timestamp features for temporal relationship operations
        # These are the 12-feature vectors from TimestampCodec before encoding
        # Used by DynamicRelationshipExtractor for type-aware temporal ops
        raw_timestamp_features = {}
        from featrix.neural.model_config import ColumnType
        for col_idx, col_or_group_name in enumerate(effective_col_order):
            # Skip hybrid groups (they don't have raw timestamp features)
            if col_or_group_name in self.hybrid_groups:
                continue

            col_type = self.col_types.get(col_or_group_name)
            if col_type == ColumnType.TIMESTAMP:
                col_data = batch_data.get(col_or_group_name)
                if col_data is not None and hasattr(col_data, 'value'):
                    # TokenBatch.value contains the raw 12-feature tensor for timestamps
                    raw_features = col_data.value
                    if raw_features is not None and raw_features.shape[-1] == 12:
                        # CRITICAL: Sanitize NaN/Inf values at the source
                        # NaN in raw_timestamp_features causes gradient explosions in temporal ops
                        raw_features = torch.nan_to_num(raw_features.float(), nan=0.0, posinf=0.0, neginf=0.0)
                        raw_timestamp_features[col_idx] = raw_features

        # Store strategy encodings for scalar/string/set columns (if strategy-aware relationships enabled)
        # These are retrieved by DynamicRelationshipExtractor when needed
        # Check if strategy-aware relationships are enabled via config
        from featrix.neural.sphere_config import get_config
        sphere_config = get_config()
        if sphere_config.get("use_strategy_aware_relationships", False):
            self._strategy_encodings = {}
            self._strategy_masks = {}
            for col_idx, col_or_group_name in enumerate(effective_col_order):
                if col_or_group_name in self.hybrid_groups:
                    continue
                col_type = self.col_types.get(col_or_group_name)
                encoder = self.encoders.get(col_or_group_name)
                col_data = batch_data.get(col_or_group_name)

                if col_data is None or encoder is None:
                    continue

                # SCALAR columns: AdaptiveScalarEncoder with 20 strategies
                if col_type == ColumnType.SCALAR:
                    if hasattr(encoder, 'strategy_logits'):
                        result = encoder(col_data, return_strategy_encodings=True)
                        if len(result) == 3:
                            _, _, strategy_encs = result
                            self._strategy_encodings[col_idx] = strategy_encs
                            if hasattr(encoder, '_strategy_mask'):
                                self._strategy_masks[col_idx] = encoder._strategy_mask

                # STRING columns: StringEncoder with compression strategies
                elif col_type == ColumnType.FREE_STRING:
                    if hasattr(encoder, 'compression_levels'):
                        result = encoder(col_data, return_strategy_encodings=True)
                        if len(result) == 3:
                            _, _, strategy_encs = result
                            self._strategy_encodings[col_idx] = strategy_encs
                            # String encoder uses _pruned_mask for active strategies
                            if hasattr(encoder, '_pruned_mask'):
                                self._strategy_masks[col_idx] = encoder._pruned_mask

                # SET columns: SetEncoder with learned/semantic/ordinal components
                elif col_type == ColumnType.SET:
                    if hasattr(encoder, 'use_semantic_mixture'):
                        result = encoder(col_data, return_strategy_encodings=True)
                        if len(result) == 3:
                            _, _, component_encs = result
                            self._strategy_encodings[col_idx] = component_encs
                            # No mask needed for set components (all always active)
        else:
            self._strategy_encodings = None
            self._strategy_masks = None

        # return torch.stack(encoding_list, dim=1), torch.stack(status_list, dim=1)
        return short_encoding_list, full_encoding_list, status_list, raw_timestamp_features


class NormalizedPoolJointEncoder(nn.Module):
    """Simplest possible joint encoder."""

    def forward(self, batch):
        # Batch is a tensor of dimensions (b, n, d)
        # use keepdim=True to retain the fact that the output is a sequence of length 1
        # CRITICAL FIX: Add eps=1e-8 to prevent NaN gradients when norm is near zero
        return nn.functional.normalize(torch.sum(batch, dim=1, keepdim=True), dim=-1, eps=1e-8)


class PassThroughJointEncoder(nn.Module):
    def forward(self, batch):
        return batch


# def sample_marginal_masks(batch_mask):
#     new_mask_A = batch_mask.clone()  # Clone the original mask to create a new mask
#     new_mask_B = batch_mask.clone()

#     for i in range(batch_mask.size(0)):  # Iterate over rows
#         # Find indices where mask is not NOT_PRESENT
#         # The output looks something like
#         # This gives the indices in the row that are NOT equal to NOT_PRESENT
#         # This means that these are the indices that CAN be masked out
#         # For a row equal to [TokenStatus.NOT_PRESENT, TokenStatus.OK, TokenStatus.OK, TokenStatus.NOT_PRESENT],
#         # present will be torch.tensor([1, 2])
#         present = torch.nonzero(
#             batch_mask[i] != TokenStatus.NOT_PRESENT, as_tuple=True
#         )[0]

#         # If there is only one present token (or zero), leave the mask row as-is.
#         if len(present) > 1:
#             # Make sure at least one present token is left unmasked
#             max_selected = len(present) - 1
#             # Randomly choose number of elements to select for masking in one of the returned masks.
#             # we want to select at least one token to mask because otherwise the second mask will have no unmasked tokens.
#             min_selected = 1
#             num_to_select = random.randint(min_selected, max_selected)

#             # Randomly select indices
#             # Make sure that masks A and B are complimentary - i.e. a token that is masked in one is not masked in the other.
#             permutation = torch.randperm(len(present))
#             selected_indices_A = present[permutation[:num_to_select]]
#             selected_indices_B = present[permutation[num_to_select:]]

#             # Set the status for the selected token to MARGINAL
#             new_mask_A[i, selected_indices_A] = TokenStatus.MARGINAL
#             new_mask_B[i, selected_indices_B] = TokenStatus.MARGINAL

#     return new_mask_A, new_mask_B

# Feature flag: Set to True to use ratio-limited masking strategy
# Old strategy: Random split anywhere from 1 to n-1 columns
# New strategy: Limit masking to configurable range (default: 40-60% for balanced complementary)
TRY_NEW_MASKING = True

# Import mask bias tracker
from featrix.neural.mask_bias_tracker import get_mask_bias_tracker


def sample_marginal_masks(batch_mask, min_mask_ratio=0.40, max_mask_ratio=0.60, mean_nulls_per_row=None, col_names=None, track_bias=True, unmasked_fraction=0.0):
    """
    Sample two complementary masks for marginal reconstruction.

    Args:
        batch_mask: Input mask tensor
        min_mask_ratio: Minimum fraction of columns to mask (default: 0.40)
        max_mask_ratio: Maximum fraction of columns to mask (default: 0.60)
        mean_nulls_per_row: Mean number of NULL columns per row (for masking constraint)
        col_names: Optional column names for bias tracking
        track_bias: Whether to track mask bias statistics
        unmasked_fraction: Fraction of rows to keep completely unmasked (default: 0.0)
                          This helps align training with inference by having some rows
                          see their full input without any masking.

    Returns:
        (new_mask_A, new_mask_B, rows_skipped): Two complementary masks + count of skipped rows

    Masking strategies:
        - Balanced (min=0.40, max=0.60): ~50/50 split, symmetric difficulty
        - Asymmetric (min=0.10, max=0.30): 10-30% vs 70-90%, imbalanced
        - Extreme (min=0.01, max=0.99): Old strategy, very imbalanced

    Masking constraint:
        - If mean_nulls_per_row is provided, will NOT mask more than mean_nulls/3 columns
        - Rows with >66% nulls are SKIPPED from masking entirely (kept in batch but no marginal loss)
        - This prevents over-masking when data is already sparse

    Mixed-masking (unmasked_fraction > 0):
        - A fraction of rows are kept completely unmasked (no MARGINAL tokens)
        - These rows see their full input, similar to inference behavior
        - Helps the model learn consistent embeddings for masked vs unmasked inputs
    """
    # Move the batch mask to the cpu, so we can iterate over rows on the cpu,
    # which eliminates the need to shuffle data back and forth.
    # We move all masks back to the GPU at the end of this function.
    batch_mask = batch_mask.to(torch.device("cpu"))

    # Clone the original mask to create new masks
    new_mask_A = batch_mask.clone()
    new_mask_B = batch_mask.clone()
    
    # Find indices where each row has tokens present
    # present_indices is a tensor, where each row corresponds to an INDIVIDUAL ENTRY
    # in batch_mask that does NOT correspond to a NOT_PRESENT token, and has two elements
    # that represent the index of that element in batch_mask.
    present_indices = (batch_mask != TokenStatus.NOT_PRESENT).nonzero(as_tuple=False)
    rows, cols = present_indices[:, 0], present_indices[:, 1]
    
    # Count how many columns are NOT_PRESENT (null) per row to skip sparse rows
    batch_size, n_cols = batch_mask.shape
    # CRITICAL: Create NOT_PRESENT value as tensor on same device
    not_present_value = torch.tensor(TokenStatus.NOT_PRESENT, device=batch_mask.device, dtype=batch_mask.dtype)
    null_counts_per_row = (batch_mask == not_present_value).sum(dim=1)
    
    # Skip masking threshold: rows with >66% nulls
    max_null_ratio = 0.66
    max_nulls_allowed = int(n_cols * max_null_ratio)
    
    # Track how many rows we skip
    rows_skipped = 0

    # Group by row index and perform vectorized selection of tokens to mask
    unique_rows = torch.unique(rows)

    # MIXED-MASKING: Select which rows will be kept completely unmasked
    # This helps align training with inference by having some rows see full input
    unmasked_rows_set = set()
    if unmasked_fraction > 0:
        num_unmasked = max(1, int(len(unique_rows) * unmasked_fraction))
        # Randomly select rows to keep unmasked
        unmasked_indices = torch.randperm(len(unique_rows))[:num_unmasked]
        unmasked_rows_set = set(unique_rows[unmasked_indices].tolist())
        if not hasattr(sample_marginal_masks, '_logged_unmasked'):
            sample_marginal_masks._logged_unmasked = True
            logger.info(f"🎯 Mixed-masking enabled: {unmasked_fraction*100:.0f}% of rows ({num_unmasked}/{len(unique_rows)}) kept unmasked per batch")

    for row in unique_rows:
        # MIXED-MASKING: Skip masking for rows designated as unmasked
        row_int = row.item()
        if row_int in unmasked_rows_set:
            # Keep this row completely unmasked - no MARGINAL tokens
            # This row will see its full input, like during inference
            continue

        # CRITICAL: Skip masking if this row has too many nulls
        row_null_count = null_counts_per_row[row].item()
        if row_null_count > max_nulls_allowed:
            # Skip masking for this row - leave masks unchanged (all OK)
            # Row will be in the batch but won't contribute to marginal loss
            rows_skipped += 1
            continue
        
        # Get the column indices where tokens are present in the current row
        present = cols[rows == row]
        
        if len(present) > 1:
            # Ensure at least one token is left unmasked in one of the masks
            max_selected = len(present) - 1
            
            if TRY_NEW_MASKING:
                # NEW STRATEGY: Configurable masking ratio
                # Default 40-60% creates balanced complementary masks (~50/50 split)
                # This ensures both prediction tasks have similar difficulty
                # NOTE: Allow 0 masking when min_mask_ratio=0 (for curriculum warmup)
                min_to_mask = max(0, int(len(present) * min_mask_ratio))
                max_to_mask = max(0, min(max_selected, int(len(present) * max_mask_ratio)))
                
                # CRITICAL: Apply null constraint ONLY if data is actually sparse
                # AND only if it doesn't violate the min_mask_ratio
                # This prevents over-masking when data has lots of nulls,
                # but doesn't break masking for dense datasets with few nulls
                if mean_nulls_per_row is not None and mean_nulls_per_row > 0:
                    max_mask_from_nulls = int(mean_nulls_per_row / 3.0)
                    
                    # Only apply constraint if:
                    # 1. It gives us at least min_to_mask columns (respects min_mask_ratio)
                    # 2. OR data is very sparse (>33% nulls) - then we MUST respect it
                    n_cols_total = len(present) + int(mean_nulls_per_row)  # Approximate total columns
                    null_ratio = mean_nulls_per_row / n_cols_total if n_cols_total > 0 else 0
                    
                    if max_mask_from_nulls >= min_to_mask:
                        # Constraint is reasonable, apply it
                        max_to_mask = min(max_to_mask, max_mask_from_nulls)
                    elif null_ratio > 0.33:
                        # Data is VERY sparse (>33% nulls), must respect constraint even if imbalanced
                        max_to_mask = max_mask_from_nulls
                        if min_to_mask > max_to_mask:
                            min_to_mask = max_to_mask  # Adjust min down to avoid invalid range
                    # else: Data is dense, null constraint too restrictive, ignore it
                
                # Ensure valid range
                if min_to_mask > max_to_mask:
                    # Fallback for very small column counts
                    num_to_select = random.randint(0, max_to_mask) if max_to_mask >= 0 else 0
                else:
                    num_to_select = random.randint(min_to_mask, max_to_mask)
            else:
                # OLD STRATEGY: Random split anywhere from 1 to n-1
                # Can result in very imbalanced masks (e.g., 1:199 or 100:100)
                num_to_select = random.randint(1, max_selected)

            # SYMMETRIC MASKING with SHARED VISIBLE COLUMNS
            # OLD behavior: complementary masks (A masks X%, B masks (100-X)%)
            # This caused severe view asymmetry - if A is 80% visible, B is only 20% visible!
            #
            # NEW behavior: Both views have similar visibility with guaranteed overlap
            # - Both mask ~15-30% of columns (70-85% visible in each)
            # - At least 50% of columns are visible in BOTH views (shared context)
            # - This enables meaningful contrastive comparison between views
            #
            # Strategy: Partition columns into 3 groups:
            # 1. SHARED (visible in both): ~50% of columns
            # 2. A_ONLY (visible only in A, masked in B): ~25% of columns
            # 3. B_ONLY (visible only in B, masked in A): ~25% of columns

            n_present = len(present)
            # Ensure at least 50% overlap (shared visible columns)
            n_shared = max(1, int(n_present * 0.5))
            n_remaining = n_present - n_shared
            # Split remaining columns between A_only and B_only
            n_a_only = n_remaining // 2
            n_b_only = n_remaining - n_a_only

            # Shuffle and partition
            permutation = torch.randperm(n_present)
            shared_indices = present[permutation[:n_shared]]
            a_only_indices = present[permutation[n_shared:n_shared + n_a_only]]
            b_only_indices = present[permutation[n_shared + n_a_only:]]

            # A sees: shared + a_only (masks b_only)
            # B sees: shared + b_only (masks a_only)
            new_mask_A[row, b_only_indices] = TokenStatus.MARGINAL
            new_mask_B[row, a_only_indices] = TokenStatus.MARGINAL

    # Move everything back to the GPU (or CPU if forced)
    force_cpu = os.environ.get('FEATRIX_FORCE_CPU_SINGLE_PREDICTOR') == '1'
    target_device = torch.device('cpu') if force_cpu else get_device()
    batch_mask = batch_mask.to(target_device)
    new_mask_A = new_mask_A.to(target_device)
    new_mask_B = new_mask_B.to(target_device)
    
    # Track mask patterns for bias analysis (if enabled)
    if track_bias:
        try:
            tracker = get_mask_bias_tracker()
            # Record masks before moving to GPU (tracker handles CPU conversion)
            tracker.record_batch(new_mask_A, new_mask_B, col_names=col_names)
        except Exception as e:
            # Don't fail masking if tracking fails
            logger.debug(f"Mask bias tracking failed: {e}")
    
    # Log if we skipped any rows (debug level to avoid spam)
    if rows_skipped > 0:
        logger.debug(f"Skipped masking on {rows_skipped}/{batch_size} rows (>{max_null_ratio:.0%} nulls)")

    # Log ACTUAL masking percentage (once per epoch)
    # NOTE: When min=max=0%, zero_masking mode bypasses these masks entirely
    if not hasattr(sample_marginal_masks, '_last_log_epoch'):
        sample_marginal_masks._last_log_epoch = -1
    current_epoch = getattr(sample_marginal_masks, '_current_epoch', 0)
    if current_epoch != sample_marginal_masks._last_log_epoch:
        sample_marginal_masks._last_log_epoch = current_epoch

        # If target is 0-0%, note that zero_masking mode will bypass these masks
        if min_mask_ratio == 0 and max_mask_ratio == 0:
            logger.info(f"[MASK_DEBUG] epoch={current_epoch} | ZERO_MASKING mode: "
                       f"target=0%-0% (masks generated but NOT APPLIED)")
        else:
            # Count actual MARGINAL tokens
            marginal_value = TokenStatus.MARGINAL
            marginal_count_A = (new_mask_A == marginal_value).sum().item()
            marginal_count_B = (new_mask_B == marginal_value).sum().item()
            total_tokens = new_mask_A.numel()
            n_cols = new_mask_A.shape[1] if len(new_mask_A.shape) > 1 else 1
            actual_pct_A = marginal_count_A / total_tokens * 100
            actual_pct_B = marginal_count_B / total_tokens * 100
            logger.info(f"[MASK_DEBUG] epoch={current_epoch} | ACTUAL masking: "
                       f"A={actual_pct_A:.1f}% ({marginal_count_A}/{total_tokens}) "
                       f"B={actual_pct_B:.1f}% ({marginal_count_B}/{total_tokens}) "
                       f"n_cols={n_cols} target={min_mask_ratio:.0%}-{max_mask_ratio:.0%}")

    return new_mask_A, new_mask_B, rows_skipped


def apply_replacement_mask(base_tensor, replacement_tensor, replacement_mask):
    # Replaces the entires in base tensor with the corresponding entries in replacement tensor.
    # Which entries are replaced is controlled by the replacement_mask tensor.

    # replacement vectors must be a (B, N, D) tensor
    # that carries replacement vectors for each column in the batch.

    batch_size, n_elements, d_features = base_tensor.shape

    assert replacement_tensor.shape == (batch_size, n_elements, d_features)
    assert replacement_mask.shape == (batch_size, n_elements, 1)

    # CRITICAL: Ensure remain_mask stays on same device as replacement_mask
    # torch.logical_not() should preserve device, but be explicit to be safe
    remain_mask = replacement_mask.logical_not()
    
    # CRITICAL: Ensure all tensors are on the same device before operations
    # Move remain_mask to base_tensor's device if needed
    if remain_mask.device != base_tensor.device:
        remain_mask = remain_mask.to(base_tensor.device)
    if replacement_mask.device != replacement_tensor.device:
        replacement_mask = replacement_mask.to(replacement_tensor.device)

    remain = base_tensor * remain_mask
    replace = replacement_tensor * replacement_mask

    return remain + replace


class ColumnPredictor(nn.Module):
    def __init__(self, cols_in_order, col_configs, col_types=None, col_codecs=None, enable_reconstruction=False):
        super().__init__()

        self.cols_in_order = cols_in_order
        self.col_predictors = FeatrixModuleDict()
        for col_name, col_config in col_configs.items():
            self.col_predictors[col_name] = SimpleMLP(col_config)

        # Value heads for direct reconstruction loss (optional, controlled by feature flag)
        self.enable_reconstruction = enable_reconstruction
        self.value_heads = None
        self.col_types = col_types or {}

        if enable_reconstruction and col_types and col_codecs:
            self.value_heads = FeatrixModuleDict()
            d_model = col_configs[cols_in_order[0]].d_out if cols_in_order else 128

            for col_name in cols_in_order:
                col_type = col_types.get(col_name)
                codec = col_codecs.get(col_name)

                if col_type == ColumnType.SCALAR:
                    # Scalar: predict normalized value (single output)
                    self.value_heads[col_name] = nn.Linear(d_model, 1)
                elif col_type == ColumnType.SET and codec is not None:
                    # Set/Categorical: predict class logits
                    n_classes = getattr(codec, 'n_members', None) or len(getattr(codec, 'members', []))
                    if n_classes > 0:
                        self.value_heads[col_name] = nn.Linear(d_model, n_classes)
                # Skip other types for now (timestamps, free strings)

            n_heads = len(self.value_heads) if self.value_heads else 0
            logger.info(f"🎯 RECONSTRUCTION HEADS: Created {n_heads} value heads for direct reconstruction loss")

    def forward(self, joint_embeddings):
        predictions = []
        for col_name in self.cols_in_order:
            prediction = self.col_predictors[col_name](joint_embeddings)
            predictions.append(prediction)

        return predictions

    def predict_values(self, column_predictions):
        """
        Predict actual values from column prediction embeddings.

        Args:
            column_predictions: List of tensors [batch, d_model], one per column

        Returns:
            Dict of {col_name: predicted_values} where:
            - Scalars: [batch, 1] normalized values
            - Sets: [batch, n_classes] logits
            Returns None if reconstruction is not enabled.
        """
        if not self.enable_reconstruction or self.value_heads is None:
            return None

        value_predictions = {}
        for i, col_name in enumerate(self.cols_in_order):
            if col_name in self.value_heads:
                col_pred = column_predictions[i]  # [batch, d_model]
                value_predictions[col_name] = self.value_heads[col_name](col_pred)

        return value_predictions


class ShortColumnPredictor(nn.Module):
    """Same as ColumnPredictor, but shares a single config across all columns."""

    def __init__(self, cols_in_order, config):
        super().__init__()

        self.cols_in_order = cols_in_order
        self.col_predictors = FeatrixModuleDict()
        for col_name in cols_in_order:
            # This is just for UI and display, so we hard-code the same
            # parameters for all column.
            self.col_predictors[col_name] = SimpleMLP(config)

    def forward(self, joint_embeddings):
        predictions = []
        for col_name in self.cols_in_order:
            prediction = self.col_predictors[col_name](joint_embeddings)
            predictions.append(prediction)

        return predictions


# Should there be different objects for data-space batches (which are per-column, whether tokens or actual data),
# and encoding batches, which are just tensors?
# each tensor batch, as opposed to a column batch, would have values and status_masks, which would be 2D tensors, not
# dictionaries of elements.
# The "collate" function in DataLoader could handle much of the complexity of constructing the batch.


def get_infoNCE_targets(batch_size, shuffle_n=0):
    force_cpu = os.environ.get('FEATRIX_FORCE_CPU_SINGLE_PREDICTOR') == '1'
    target_device = torch.device('cpu') if force_cpu else get_device()
    
    N = batch_size

    tensor = torch.arange(N).to(target_device)  # Tensor: [1, 2, 3, ..., N]

    if shuffle_n < 1:
        return tensor

    # # Set K, the number of elements to shuffle
    K = shuffle_n

    # # Ensure K is not greater than N
    K = min(K, N)

    # # Indices of the last K elements
    last_k_indices = torch.arange(N - K, N).to(target_device)

    # # Generate a random permutation of these indices
    shuffled_indices = last_k_indices[torch.randperm(K)]

    # # Shuffle the last K elements
    tensor[N - K :] = tensor[shuffled_indices]

    return tensor


class FeatrixTableEncoder(nn.Module):
    def __init__(self, col_codecs, config: FeatrixTableEncoderConfig, min_mask_ratio=0.0, max_mask_ratio=0.0, mean_nulls_per_row=None, hybrid_groups=None, enable_hybrid_encoders=True, unmasked_fraction=0.0):
        super().__init__()

        self.config = config
        self.d_model = config.d_model

        # Adaptive masking: start with ZERO masking, ramp up gradually
        # Initial: 0% masking (identity task - masked == unmasked)
        # Target: 20-35% masking (moderate challenge)
        #
        # With 0% masking, identity baseline should be perfect (separation≈1, rank1≈100%)
        # This lets predictor learn the basic mapping while encoders are also training.
        # As masking increases, predictor learns to handle missing columns.
        self.min_mask_ratio = min_mask_ratio
        self.max_mask_ratio = max_mask_ratio
        self.target_min_mask_ratio = 0.20
        self.target_max_mask_ratio = 0.35
        self.mask_ramp_epochs = 15  # Ramp from 0% to target over 15 epochs
        self._current_epoch = 0

        # Mixed-masking: keep a fraction of rows completely unmasked per batch
        # This helps align training with inference behavior by having some rows
        # see their full input (no masked columns) during training.
        # Default 20% means 1 in 5 rows will have no masking applied.
        self.unmasked_fraction = unmasked_fraction
        self._logged_marginal_debug: Optional[int] = None  # For once-per-epoch debug logging
        self._joint_predictability_history = []  # Track for adaptive backoff

        # Once-per-epoch logging flags (initialized here to satisfy pylint)
        self._marginal_diag_epoch = -1
        self._balanced_loss_logged_epoch = -1
        self._masked_variance_debug_epoch = -1

        # Soft masking: blend (1-α)*actual + α*marginal instead of hard replacement
        # α (soft_mask_alpha) ramps from 0→1 during warmup so marginals can learn
        self.soft_mask_alpha = 0.0  # Start with 0 = no marginal influence
        self._marginals_initialized = False  # Track if marginals have been initialized from data

        # Negative memory bank for contrastive loss
        # Stores past joint encodings to provide more negatives than current batch
        # This helps with small batch sizes where in-batch negatives are limited
        self.negative_bank_size = 1024  # Store up to 1024 past encodings
        self.register_buffer('_negative_bank', None)  # Will be initialized on first use
        self.register_buffer('_negative_bank_ptr', torch.zeros(1, dtype=torch.long))
        self._negative_bank_initialized = False

        self.mean_nulls_per_row = mean_nulls_per_row  # For masking constraint (don't mask more than mean_nulls/3)
        self.hybrid_groups = hybrid_groups or {}
        self.enable_hybrid_encoders = enable_hybrid_encoders
        
        # Filter hybrid groups if feature is disabled
        active_hybrid_groups = self.hybrid_groups if enable_hybrid_encoders else {}
        if not enable_hybrid_encoders and self.hybrid_groups:
            logger.info(f"🔗 HYBRID ENCODERS: Feature disabled (enable_hybrid_encoders=False)")
            logger.info(f"   Detected {len(self.hybrid_groups)} groups but not using them")

        self.column_encoder = ColumnEncoders(
            config.column_encoders_config, config.cols_in_order, config.col_types, col_codecs,
            hybrid_groups=active_hybrid_groups
        )
        
        # Get effective column order (with hybrid groups replacing merged columns)
        self.effective_col_order = self.column_encoder.get_effective_column_order()
        
        # Log the transformation
        if self.effective_col_order != config.cols_in_order:
            logger.info(f"🔗 HYBRID ENCODERS: Column order transformed")
            logger.info(f"   Original columns: {len(config.cols_in_order)}")
            logger.info(f"   Effective columns: {len(self.effective_col_order)}")
            logger.info(f"   Reduction: {len(config.cols_in_order) - len(self.effective_col_order)} columns merged")
            
            # Show which columns were replaced by which groups (first few examples)
            for group_name in active_hybrid_groups.keys():
                if group_name in self.effective_col_order:
                    group_info = active_hybrid_groups[group_name]
                    if group_info.get('strategy') == 'merge':
                        logger.info(f"   {group_name} ← {group_info['columns']}")
        else:
            logger.info(f"🔗 HYBRID ENCODERS: No column order changes (no MERGE groups active)")

        # Check if reconstruction loss is enabled via feature flag
        from featrix.neural.sphere_config import SphereConfig
        sphere_config = SphereConfig.get_instance()
        enable_reconstruction = sphere_config.get_enable_reconstruction_loss()

        self.column_predictor = ColumnPredictor(
            cols_in_order=config.cols_in_order,
            col_configs=config.column_predictors_config,
            col_types=config.col_types,
            col_codecs=col_codecs,
            enable_reconstruction=enable_reconstruction,
        )
        self.short_column_predictor = ShortColumnPredictor(
            cols_in_order=config.cols_in_order,
            config=config.column_predictors_short_config,
        )

        # Use effective column order for joint encoder (includes hybrid group names)
        self.joint_encoder = JointEncoder(
            d_embed=self.d_model,
            col_names_in_order=self.effective_col_order,  # Use effective order with hybrid groups
            config=config.joint_encoder_config,
            hybrid_groups=active_hybrid_groups,  # Pass active hybrid groups to joint encoder
            enable_gradient_checkpointing=True,  # Always enable to save GPU memory
            col_types=config.col_types,  # Pass column types for temporal relationship ops
        )

        # Initialize encoder weights for uniform hypersphere distribution
        # This ensures embeddings start uniformly spread on the unit sphere,
        # which helps the separation loss maintain spread during training.
        # DISABLED: Testing if this hurts AUC (was added in 618770da when AUC dropped 0.712->0.604)
        # self.joint_encoder.init_for_uniform_hypersphere()

        self.joint_predictor = SimpleMLP(config.joint_predictor_config)
        # This is just for UI and display, so we hard-code the parameters here.
        self.joint_predictor_short = SimpleMLP(config.joint_predictor_short_config)

        # Log joint predictor architecture for debugging
        jp_cfg = config.joint_predictor_config
        n_params = sum(p.numel() for p in self.joint_predictor.parameters())
        logger.info(f"[JOINT_DEBUG] ARCHITECTURE: d_in={jp_cfg.d_in} d_out={jp_cfg.d_out} "
                   f"d_hidden={jp_cfg.d_hidden} n_layers={jp_cfg.n_hidden_layers} "
                   f"residual={jp_cfg.residual} n_params={n_params:,}")

        # DEBUG: Store initial weight snapshot for tracking changes
        self._joint_predictor_initial_weights = None
        self._joint_predictor_last_weights = None
        self._debug_joint_predictor_epoch = -1

        self.idx_to_col_name = {
            i: col_name for i, col_name in enumerate(config.cols_in_order)
        }
        self.col_mi_estimates = {col_name: None for col_name in config.cols_in_order}
        self.col_loss_estimates = {col_name: None for col_name in config.cols_in_order}  # Track raw losses
        self.joint_mi_estimate = None

        # Column prediction accuracy tracker
        # Tracks how often we correctly predict each column from context
        # Buckets based on rank of correct answer:
        #   top1:     rank = 1 (perfect prediction)
        #   top5:     rank 2-5
        #   top20:    rank 6-20
        #   top50:    rank 21-50
        #   miss:     rank 51+ (essentially random)
        self.col_prediction_stats = {
            col_name: {
                'attempts': 0,
                'top1': 0,       # rank = 1 (perfect)
                'top5': 0,       # rank 2-5
                'top20': 0,      # rank 6-20
                'top50': 0,      # rank 21-50
                'miss': 0,       # rank 51+
            }
            for col_name in config.cols_in_order
        }

        # TODO: create "column encoders" and "column predictors" as separate models here.
        # That's pretty much the only place they are needed I think.
        # TODO: look into what's being done in SinglePredictor - I think they use the encoders
        self.n_codecs = config.n_cols
        self.column_order = config.cols_in_order
        self.col_codecs_in_order = [
            col_codecs[col_name] for col_name in self.column_order
        ]

        # defines how much noise is applied to the sample embeddings for CPC
        # self.latent_noise = 0.01
        self.latent_noise = 0
        # We do not reduce the loss so that we can mask out loss associated with fields
        # that are NOT_PRESENT (or not in schema).
        self.ce_loss = nn.CrossEntropyLoss(reduction="none")

        # We use separate stopwatches for the encoder and loss computation becase we don't want
        # to have to synchronize the start/stop of stopwatches between encoder and loss
        # computation to retain the flexibility to use them independently, e.g. in testing.
        self.encoder_stopwatch = None #StopWatch()
        self.loss_stopwatch = None #StopWatch()
        
        # SCALAR RECONSTRUCTION: Decoders are now inside AdaptiveScalarEncoder
        # Count how many scalar columns have reconstruction enabled
        from featrix.neural.model_config import ColumnType
        scalar_decoder_count = 0
        for col_name in config.cols_in_order:
            col_type = config.col_types.get(col_name)
            if col_type == ColumnType.SCALAR:
                encoder = self.column_encoder.encoders.get(col_name)
                if encoder and hasattr(encoder, 'enable_reconstruction') and encoder.enable_reconstruction:
                    scalar_decoder_count += 1
        
        if scalar_decoder_count > 0:
            logger.info(f"🔢 SCALAR RECONSTRUCTION: {scalar_decoder_count} numeric columns have decoders enabled")

        # Log reconstruction loss feature status
        if enable_reconstruction:
            recon_weight = sphere_config.get_reconstruction_loss_weight()
            logger.info(f"🎯 RECONSTRUCTION LOSS: ENABLED (weight={recon_weight})")
            logger.info(f"   Direct value prediction will be added to marginal loss")
            logger.info(f"   Set FEATRIX_ENABLE_RECONSTRUCTION_LOSS=0 to disable")

    def __setstate__(self, state):
        """Force CPU during unpickling to prevent GPU allocation."""
        logger = logging.getLogger(__name__)
        
        # Log GPU memory before unpickling
        if is_gpu_available():
            allocated_before = get_gpu_memory_allocated()
            logger.info(f"📊 FeatrixTableEncoder.__setstate__: GPU memory BEFORE: Allocated={allocated_before:.3f} GB")
        
        # Restore state
        self.__dict__.update(state)
        
        # Log GPU memory after unpickling
        if is_gpu_available():
            allocated_after = get_gpu_memory_allocated()
            logger.info(f"📊 FeatrixTableEncoder.__setstate__: GPU memory AFTER dict.update: Allocated={allocated_after:.3f} GB")
        
        # CRITICAL: Move everything to CPU if in CPU mode
        force_cpu = os.environ.get('FEATRIX_FORCE_CPU_SINGLE_PREDICTOR') == '1'
        if force_cpu:
            logger.info(f"📊 FeatrixTableEncoder.__setstate__: Moving all components to CPU")
            self.cpu()
            
            # AGGRESSIVE GPU MEMORY CLEANUP
            # Use gpu_utils function - handles all GPU type checking internally
            logger.info(f"📊 FeatrixTableEncoder.__setstate__: Aggressively freeing GPU memory...")
            memory_stats = aggressive_clear_gpu_cache(iterations=3, do_gc=True)
            
            if memory_stats:
                # Log memory stats after clearing
                final = memory_stats.get('final', {})
                allocated = final.get('allocated_gb', 0)
                reserved = final.get('reserved_gb', 0)
                logger.info(f"📊 FeatrixTableEncoder.__setstate__: GPU memory FINAL: Allocated={allocated:.3f} GB, Reserved={reserved:.3f} GB")
            else:
                logger.info(f"📊 FeatrixTableEncoder.__setstate__: GPU not available, skipped cache clearing")

    def count_model_parameters(self):
        total_params = sum(p.numel() for p in self.parameters())
        trainable_params = sum(p.numel() for p in self.parameters() if p.requires_grad)

        # Column and joint encoders are the parts of the model involved in inference.
        # "predictors" and encoders for "short" embeddings are not counted because they're
        # not used in inference in production.
        column_encoders_params = sum(
            p.numel() for p in self.column_encoder.parameters()
        )
        column_encoders_trainable_params = sum(
            p.numel() for p in self.column_encoder.parameters() if p.requires_grad
        )

        # Break down column encoders into regular vs hybrid
        regular_col_params = 0
        regular_col_trainable_params = 0
        hybrid_merge_params = 0
        hybrid_merge_trainable_params = 0
        hybrid_merge_count = 0
        
        if hasattr(self.column_encoder, 'encoders'):
            for col_name, encoder in self.column_encoder.encoders.items():
                encoder_params = sum(p.numel() for p in encoder.parameters())
                encoder_trainable_params = sum(p.numel() for p in encoder.parameters() if p.requires_grad)
                
                # Check if this is a hybrid encoder
                is_hybrid = False
                if HYBRID_ENCODERS_AVAILABLE and (
                    isinstance(encoder, AddressHybridEncoder) or 
                    isinstance(encoder, CoordinateHybridEncoder)
                ):
                    is_hybrid = True
                    hybrid_merge_count += 1
                
                if is_hybrid:
                    hybrid_merge_params += encoder_params
                    hybrid_merge_trainable_params += encoder_trainable_params
                else:
                    regular_col_params += encoder_params
                    regular_col_trainable_params += encoder_trainable_params

        joint_encoder_params = sum(
            p.numel() for p in self.joint_encoder.parameters()
        )
        joint_encoder_trainable_params = sum(
            p.numel() for p in self.joint_encoder.parameters() if p.requires_grad
        )

        # Break out relationship extractor params (sub-module of joint_encoder)
        relationship_extractor_params = 0
        relationship_extractor_trainable_params = 0
        if hasattr(self.joint_encoder, 'relationship_extractor') and self.joint_encoder.relationship_extractor is not None:
            relationship_extractor_params = sum(
                p.numel() for p in self.joint_encoder.relationship_extractor.parameters()
            )
            relationship_extractor_trainable_params = sum(
                p.numel() for p in self.joint_encoder.relationship_extractor.parameters() if p.requires_grad
            )

        # Also count local_attention (used for relationship selection in transformer)
        local_attention_params = 0
        local_attention_trainable_params = 0
        if hasattr(self.joint_encoder, 'local_attention') and self.joint_encoder.local_attention is not None:
            local_attention_params = sum(
                p.numel() for p in self.joint_encoder.local_attention.parameters()
            )
            local_attention_trainable_params = sum(
                p.numel() for p in self.joint_encoder.local_attention.parameters() if p.requires_grad
            )

        # Transformer params = joint_encoder - relationship_extractor - local_attention
        transformer_params = joint_encoder_params - relationship_extractor_params - local_attention_params
        transformer_trainable_params = joint_encoder_trainable_params - relationship_extractor_trainable_params - local_attention_trainable_params

        # Column predictors (one per column, used for reconstruction during training)
        column_predictor_params = 0
        column_predictor_trainable_params = 0
        if hasattr(self, 'column_predictor') and self.column_predictor is not None:
            column_predictor_params = sum(p.numel() for p in self.column_predictor.parameters())
            column_predictor_trainable_params = sum(
                p.numel() for p in self.column_predictor.parameters() if p.requires_grad
            )

        # Joint predictor (single MLP for joint embedding reconstruction)
        joint_predictor_params = 0
        joint_predictor_trainable_params = 0
        if hasattr(self, 'joint_predictor') and self.joint_predictor is not None:
            joint_predictor_params = sum(p.numel() for p in self.joint_predictor.parameters())
            joint_predictor_trainable_params = sum(
                p.numel() for p in self.joint_predictor.parameters() if p.requires_grad
            )

        result = {
            "total_params": total_params,
            "total_trainable_params": trainable_params,
            "column_encoders_params": column_encoders_params,
            "column_encoders_trainable_params": column_encoders_trainable_params,
            "transformer_params": transformer_params,
            "transformer_trainable_params": transformer_trainable_params,
            "relationship_extractor_params": relationship_extractor_params,
            "relationship_extractor_trainable_params": relationship_extractor_trainable_params,
            "column_predictor_params": column_predictor_params,
            "column_predictor_trainable_params": column_predictor_trainable_params,
            "joint_predictor_params": joint_predictor_params,
            "joint_predictor_trainable_params": joint_predictor_trainable_params,
        }

        return result

    def freeze_joint_encoder(self):
        """
        Freeze the joint encoder (transformer) to prevent gradient updates.

        Used during early training epochs to let column encoders learn
        before the transformer starts adapting. This prevents the transformer
        from overwhelming the column encoders early in training.
        """
        frozen_count = 0
        for param in self.joint_encoder.parameters():
            param.requires_grad = False
            frozen_count += 1
        logger.info(f"🧊 Froze joint_encoder ({frozen_count} params)")
        return frozen_count

    def unfreeze_joint_encoder(self):
        """
        Unfreeze the joint encoder (transformer) to allow gradient updates.

        Called after warmup epochs to let the transformer start learning.
        """
        unfrozen_count = 0
        for param in self.joint_encoder.parameters():
            param.requires_grad = True
            unfrozen_count += 1
        logger.info(f"🔥 Unfroze joint_encoder ({unfrozen_count} params)")
        return unfrozen_count

    def is_joint_encoder_frozen(self) -> bool:
        """Check if the joint encoder is currently frozen."""
        # Check if any param has requires_grad=True
        for param in self.joint_encoder.parameters():
            if param.requires_grad:
                return False
        return True

    def get_marginal_tensor(self, batch_size):
        # Create columns of marginal embeddings, one for each codec.
        column_marginal_embeddings_list = [
            # codec.marginal_embedding.repeat(batch_size, 1)
            self.column_encoder.encoders[col_name].marginal_embedding.repeat(
                batch_size, 1
            )
            # for codec in self.col_codecs_in_order
            for col_name in self.column_order
        ]

        # Combine the columns of embeddings into a single tensor.
        # The columns are stacked side-by-side, i.e. along the first dimension.
        column_marginal_embeddings = torch.stack(column_marginal_embeddings_list, dim=1)

        return column_marginal_embeddings

    def initialize_marginals_from_data(self, column_encodings: torch.Tensor, noise_scale: float = 0.5):
        """
        Initialize marginal embeddings from the mean of actual column encodings + noise.

        This should be called after epoch 0 to give marginals a reasonable starting point
        instead of random vectors. Noise is added to break collinearity with actuals -
        without noise, marginals would be perfectly aligned with column means (cosine=1.0),
        making the masked prediction objective trivial.

        Args:
            column_encodings: (B, n_cols, d_model) tensor of actual column encodings
            noise_scale: Std of Gaussian noise relative to embedding norm (default 0.5).
                        This gives ~0.3-0.5 cosine similarity with original mean.
        """
        if self._marginals_initialized:
            return

        with torch.no_grad():
            # Compute mean encoding per column across the batch
            # column_encodings: (B, n_cols, d_model)
            column_means = column_encodings.mean(dim=0)  # (n_cols, d_model)

            # Update each codec's marginal embedding
            for i, col_name in enumerate(self.column_order):
                encoder = self.column_encoder.encoders.get(col_name)
                if encoder is not None and hasattr(encoder, '_replacement_embedding'):
                    # Start from column mean
                    mean_vec = column_means[i]
                    mean_norm = mean_vec.norm().item()

                    # Add noise to break collinearity
                    # noise_scale=0.5 means noise std is 50% of the embedding norm
                    noise = torch.randn_like(mean_vec) * (noise_scale * mean_norm)
                    noisy_marginal = mean_vec + noise

                    encoder._replacement_embedding.data.copy_(noisy_marginal)

            self._marginals_initialized = True

            # Compute new similarity after initialization (should be ~0.3-0.5 with noise_scale=0.5)
            new_marginals = self.get_marginal_tensor(1)[0]  # (n_cols, d_model)
            # Normalize column_means for fair cosine comparison (marginal_embedding normalizes)
            column_means_normed = F.normalize(column_means, dim=1)
            cos_sim = F.cosine_similarity(column_means_normed, new_marginals, dim=1)

            logger.info(f"[MARGINAL_INIT] Initialized marginals from column means + noise (scale={noise_scale})")
            logger.info(f"[MARGINAL_INIT] Post-init cosine_sim: mean={cos_sim.mean():.4f} "
                       f"min={cos_sim.min():.4f} max={cos_sim.max():.4f}")

    def update_marginals_toward_data(self, column_encodings: torch.Tensor, momentum: float = 0.1,
                                       noise_scale: float = 0.1):
        """
        Update marginal embeddings toward current column encoding means (EMA style) + noise.

        During warmup (0% masking), we can't train marginals via gradients because they're
        not used. This method updates them via exponential moving average toward the
        current column means, so they track the evolving encoder representations.

        Noise is added to maintain diversity and prevent marginals from becoming
        perfectly collinear with column means.

        Args:
            column_encodings: (B, n_cols, d_model) tensor of actual column encodings
            momentum: How much to move toward current mean (0.1 = 10% of the way)
            noise_scale: Std of noise relative to update magnitude (default 0.1)
        """
        with torch.no_grad():
            # Compute mean encoding per column across the batch
            column_means = column_encodings.mean(dim=0)  # (n_cols, d_model)

            # Update each codec's marginal embedding via EMA + noise
            for i, col_name in enumerate(self.column_order):
                encoder = self.column_encoder.encoders.get(col_name)
                if encoder is not None and hasattr(encoder, '_replacement_embedding'):
                    # Compute the update direction
                    current = encoder._replacement_embedding.data
                    target = column_means[i]
                    update = momentum * (target - current)

                    # Add noise proportional to update magnitude to maintain diversity
                    noise = torch.randn_like(update) * (noise_scale * update.norm())

                    # Apply update with noise
                    encoder._replacement_embedding.data.add_(update + noise)

    def apply_marginal_mask(self, tensor, marginal_tensor, mask, soft_alpha=None):
        """
        Apply marginal mask with optional soft blending.

        Args:
            tensor: Original column encodings (B, n_cols, d_model)
            marginal_tensor: Marginal embeddings (B, n_cols, d_model)
            mask: Token status mask (B, n_cols)
            soft_alpha: Blending factor (0=all original, 1=all marginal). If None, uses self.soft_mask_alpha

        Returns:
            Masked tensor where MARGINAL positions are replaced/blended with marginal_tensor
        """
        if soft_alpha is None:
            soft_alpha = self.soft_mask_alpha

        # CRITICAL: Create comparison on same device as mask tensor
        # If we compare with Python int directly, PyTorch creates result on CPU!
        marginal_value = torch.tensor(TokenStatus.MARGINAL, device=mask.device, dtype=mask.dtype)
        replacement_mask = (mask == marginal_value).unsqueeze(dim=-1)  # (B, n_cols, 1)

        if soft_alpha >= 1.0:
            # Hard masking: full replacement
            return apply_replacement_mask(tensor, marginal_tensor, replacement_mask)
        elif soft_alpha <= 0.0:
            # No masking: return original
            return tensor
        else:
            # Soft masking: blend (1-α)*actual + α*marginal for masked positions
            # Non-masked positions remain unchanged (keep original norms!)
            #
            # For masked positions: scale marginal to match actual norm, then blend
            # This avoids the norm mismatch (marginal=1.0, actual=~1.6) while
            # preserving original norms for unmasked positions.

            # Scale marginals to match actual column norms (per-column scaling)
            actual_norms = tensor.norm(dim=-1, keepdim=True).clamp(min=1e-6)  # (B, n_cols, 1)
            marginal_scaled = F.normalize(marginal_tensor, dim=-1) * actual_norms

            # Blend: (1-α)*actual + α*scaled_marginal
            blended = (1 - soft_alpha) * tensor + soft_alpha * marginal_scaled

            # Only apply blending where mask is MARGINAL
            # remain_mask is inverse of replacement_mask
            remain_mask = replacement_mask.logical_not()
            if remain_mask.device != tensor.device:
                remain_mask = remain_mask.to(tensor.device)
            if replacement_mask.device != blended.device:
                replacement_mask = replacement_mask.to(blended.device)

            # CRITICAL: Keep original tensor for unmasked positions (preserve norms!)
            return tensor * remain_mask + blended * replacement_mask

    @torch.no_grad()
    def update_negative_bank(self, encodings: torch.Tensor):
        """
        Add new encodings to the negative memory bank (FIFO queue).

        Args:
            encodings: (batch_size, d_model) tensor of joint encodings to store
        """
        batch_size, d_model = encodings.shape

        # Initialize bank on first use
        negative_bank = getattr(self, '_negative_bank', None)
        if negative_bank is None or not self._negative_bank_initialized:
            self._negative_bank = torch.zeros(self.negative_bank_size, d_model, device=encodings.device)
            self._negative_bank_initialized = True
            logger.info(f"[NEGATIVE_BANK] Initialized: size={self.negative_bank_size}, d_model={d_model}")

        # Ensure bank is on same device
        if self._negative_bank.device != encodings.device:
            self._negative_bank = self._negative_bank.to(encodings.device)
            self._negative_bank_ptr = self._negative_bank_ptr.to(encodings.device)

        # Get current pointer position
        ptr = int(self._negative_bank_ptr.item())

        # Handle case where batch is larger than remaining space
        if ptr + batch_size <= self.negative_bank_size:
            # Simple case: enough space
            self._negative_bank[ptr:ptr + batch_size] = encodings.detach()
            self._negative_bank_ptr[0] = (ptr + batch_size) % self.negative_bank_size
        else:
            # Wrap around: split the batch
            first_part = self.negative_bank_size - ptr
            self._negative_bank[ptr:] = encodings[:first_part].detach()
            self._negative_bank[:batch_size - first_part] = encodings[first_part:].detach()
            self._negative_bank_ptr[0] = batch_size - first_part

    def get_negative_bank(self) -> torch.Tensor:
        """
        Get the current negative bank contents.

        Returns:
            (bank_size, d_model) tensor of stored encodings, or None if not initialized
        """
        negative_bank = getattr(self, '_negative_bank', None)
        if negative_bank is None or not self._negative_bank_initialized:
            return None
        return negative_bank

    def infoNCE_loss_with_bank(
        self,
        predictions: torch.Tensor,
        targets: torch.Tensor,
        temperature: float = 0.1,
    ):
        """
        Compute InfoNCE loss using negative memory bank for more negatives.

        Instead of only using in-batch samples as negatives (which fails with small batches),
        this uses the accumulated negative bank to provide many more negatives.

        Args:
            predictions: (batch_size, d_model) predicted encodings
            targets: (batch_size, d_model) target encodings
            temperature: Temperature for softmax scaling

        Returns:
            loss: Scalar loss tensor
            diagnostics: Dict with similarity statistics
        """
        batch_size = predictions.shape[0]

        # Normalize
        predictions = F.normalize(predictions, dim=1)
        targets = F.normalize(targets, dim=1)

        # Get negative bank
        neg_bank = self.get_negative_bank()

        if neg_bank is None or neg_bank.shape[0] < batch_size:
            # Fall back to in-batch negatives if bank not ready
            logits = predictions @ targets.T / temperature
            labels = torch.arange(batch_size, device=predictions.device)
            loss = F.cross_entropy(logits, labels)

            # Diagnostics
            with torch.no_grad():
                diag_sim = (predictions * targets).sum(dim=1).mean()
                off_diag_sim = (logits.sum() - logits.diag().sum()) / (batch_size * (batch_size - 1))

            return loss, {
                'diag_sim': diag_sim.item(),
                'off_diag_sim': off_diag_sim.item(),
                'n_negatives': batch_size - 1,
                'bank_used': False,
            }

        # Use bank: positive is target[i], negatives are everything in bank
        # Similarity to positive targets: (batch_size,)
        pos_sim = (predictions * targets).sum(dim=1, keepdim=True) / temperature  # (B, 1)

        # Similarity to all negatives in bank: (batch_size, bank_size)
        neg_sim = predictions @ neg_bank.T / temperature  # (B, bank_size)

        # Concatenate: [positive, negatives]
        # logits shape: (batch_size, 1 + bank_size)
        logits = torch.cat([pos_sim, neg_sim], dim=1)

        # Labels: positive is always at index 0
        labels = torch.zeros(batch_size, dtype=torch.long, device=predictions.device)

        loss = F.cross_entropy(logits, labels)

        # Update bank with current targets (they become negatives for future batches)
        self.update_negative_bank(targets)

        # Diagnostics
        with torch.no_grad():
            diag_sim = pos_sim.mean()
            off_diag_sim = neg_sim.mean()

        return loss, {
            'diag_sim': diag_sim.item(),
            'off_diag_sim': off_diag_sim.item(),
            'n_negatives': neg_bank.shape[0],
            'bank_used': True,
        }

    def update_adaptive_masking(self, epoch: int, joint_predictability: float = None, n_epochs: int = 100) -> dict:
        """
        Update masking ratios based on training progress and joint predictability.

        Curriculum for masking (triangle wave oscillation):
        - Oscillates between 30/70 and 40/60 masking ratios
        - 10 epoch cycle: 5 epochs up (30→40), 5 epochs down (40→30)
        - Both asymmetric and balanced tasks get practiced throughout training

        Also handles:
        - Soft masking alpha ramping (0→1 over first 10 epochs)
        - Marginal initialization from data (epoch 1)
        - Marginal EMA updates during early training

        Args:
            epoch: Current training epoch (0-indexed)
            joint_predictability: Current joint predictability % (0-100), or None
            n_epochs: Total number of training epochs (for computing ramp schedule)

        Returns:
            dict with current masking config and any adjustments made
        """
        self._current_epoch = epoch

        # Track predictability history for adaptive backoff
        if joint_predictability is not None:
            self._joint_predictability_history.append(joint_predictability)

        # TRIANGLE WAVE CURRICULUM: Oscillate between 30/70 and 40/60
        # - 10 epoch cycle (5 up, 5 down)
        # - At trough (epoch 0, 10, 20...): 30/70 (more asymmetric)
        # - At peak (epoch 5, 15, 25...): 40/60 (more balanced)
        cycle_length = 10
        half_cycle = cycle_length // 2

        # Position within current cycle (0 to cycle_length-1)
        cycle_pos = epoch % cycle_length

        # Triangle wave: 0→1 for first half, 1→0 for second half
        if cycle_pos < half_cycle:
            # Rising: 0 at start, 1 at half_cycle
            wave_progress = cycle_pos / half_cycle
        else:
            # Falling: 1 at half_cycle, 0 at end
            wave_progress = 1.0 - (cycle_pos - half_cycle) / half_cycle

        alpha_ramp_epochs = 10  # Ramp soft_mask_alpha from 0→1 over 10 epochs

        # Soft masking alpha ramp: 0 to 1 over first alpha_ramp_epochs
        alpha_progress = min(1.0, epoch / max(1, alpha_ramp_epochs))

        old_alpha = self.soft_mask_alpha
        self.soft_mask_alpha = alpha_progress

        # Log alpha changes
        if abs(self.soft_mask_alpha - old_alpha) > 0.05:
            logger.info(f"🎭 Soft mask alpha [epoch={epoch}]: {old_alpha:.2f} → {self.soft_mask_alpha:.2f}")

        # BERT-style low masking: 10-20% range
        # With 50% complementary masking, identity_rank1 starts at ~15% and drops to ~1%
        # The contrastive task is impossible when masked/unmasked share no visible columns
        # With 10-20% masking, ~80-90% of columns are shared → task is feasible
        trough_min, trough_max = 0.10, 0.20  # Light masking - shares 80-90% of columns
        peak_min, peak_max = 0.15, 0.25      # Slightly more challenging

        # Interpolate based on wave progress
        ramped_min = trough_min + wave_progress * (peak_min - trough_min)
        ramped_max = trough_max + wave_progress * (peak_max - trough_max)

        # Check for stuck joint predictability (0% for 5+ consecutive epochs)
        backoff_applied = False
        if len(self._joint_predictability_history) >= 5:
            recent = self._joint_predictability_history[-5:]
            if all(p <= 0.0 for p in recent) and epoch > 10:
                # Joint predictor stuck - back off to easier masking
                backoff_factor = 0.7  # Reduce masking by 30%
                ramped_min *= backoff_factor
                ramped_max *= backoff_factor
                backoff_applied = True
                logger.info(f"🎭 Adaptive masking BACKOFF: joint stuck at 0% for 5 epochs, "
                           f"reducing to {ramped_min:.0%}-{ramped_max:.0%}")

        # Update current masking ratios
        old_min, old_max = self.min_mask_ratio, self.max_mask_ratio
        self.min_mask_ratio = ramped_min
        self.max_mask_ratio = ramped_max

        # Log changes at cycle boundaries
        if epoch % half_cycle == 0:
            cycle_num = epoch // cycle_length
            phase = "trough (30/70)" if cycle_pos == 0 else "peak (40/60)"
            logger.info(f"🎭 Adaptive masking [epoch={epoch}]: cycle {cycle_num}, {phase}, "
                       f"{ramped_min:.0%}-{ramped_max:.0%}")

        return {
            'epoch': epoch,
            'min_mask_ratio': self.min_mask_ratio,
            'max_mask_ratio': self.max_mask_ratio,
            'soft_mask_alpha': self.soft_mask_alpha,
            'ramp_progress': wave_progress,  # Now represents position in triangle wave (0=trough, 1=peak)
            'backoff_applied': backoff_applied,
            'joint_predictability': joint_predictability,
        }

    def infoNCE_loss(
        self,
        context_enc,
        sample_enc,
        mask=None,
        unknown_targets=False,
        random_fraction=0,
        temperature=None,
        return_logits=False,
    ):
        sample_enc = sample_enc + torch.randn_like(sample_enc) * self.latent_noise
        # Add eps=1e-8 to prevent NaN gradients if any sample has near-zero norm
        sample_enc = nn.functional.normalize(sample_enc, dim=1, eps=1e-8)

        # CRITICAL: Normalize context_enc (predictions) too!
        # Without this, predictor outputs with large norms cause extreme logits,
        # leading to loss >> log(N) even at random initialization (5x worse than random).
        # With both normalized, logits are in range [-1/temp, 1/temp] → well-behaved loss.
        # Add eps=1e-8 to prevent NaN gradients if any sample has near-zero norm
        context_enc = nn.functional.normalize(context_enc, dim=1, eps=1e-8)

        # DEBUG: Log cosine similarity diagnostics once per epoch (first batch only)
        # Uses _current_epoch to track which epoch we're in
        if not hasattr(self, '_cosine_debug_last_epoch'):
            self._cosine_debug_last_epoch = -1
        current_epoch = getattr(self, '_current_epoch', 0)
        if current_epoch != self._cosine_debug_last_epoch:
            self._cosine_debug_last_epoch = current_epoch
            with torch.no_grad():
                # Diagonal = similarity between prediction[i] and target[i] (should be high)
                # Off-diagonal = similarity to wrong targets (should be low)
                sim_matrix = context_enc @ sample_enc.T  # (batch, batch)
                diag_sim = sim_matrix.diag()  # Correct pairs
                # Off-diagonal mean (exclude diagonal)
                mask_diag = ~torch.eye(sim_matrix.shape[0], dtype=torch.bool, device=sim_matrix.device)
                off_diag_sim = sim_matrix[mask_diag]
                logger.info(f"🔍 [epoch={current_epoch}] Cosine sim: diag={diag_sim.mean():.4f}±{diag_sim.std():.4f}, "
                           f"off_diag={off_diag_sim.mean():.4f}±{off_diag_sim.std():.4f}, "
                           f"SEPARATION={diag_sim.mean() - off_diag_sim.mean():.4f}")

        # Apply temperature scaling to logits (if provided)
        if temperature is not None and temperature > 0:
            logits = context_enc @ sample_enc.T / temperature
        else:
            logits = context_enc @ sample_enc.T

        batch_size = context_enc.shape[0]
        shuffle_n = int(batch_size * random_fraction)
        targets = get_infoNCE_targets(batch_size, shuffle_n=shuffle_n)

        # If the mask indicatest that the token is not present, set
        # the corresponding logit to -inf so it does not affect the loss.
        # The columns in the logits tensor correspond to individual tokens
        # in the column for which we're computing the loss
        if mask is not None:
            # do NOT mask MARGINAL tokens becasuse marginal encodings are not
            # at all related to MARGINAL tokens because these are only
            # created for the joint encoder.

            # select all rows, but only the columns where we did not
            # CRITICAL: Create NOT_PRESENT value as tensor on same device as mask
            # Comparing tensor with Python int creates result on CPU!
            not_present_value = torch.tensor(TokenStatus.NOT_PRESENT, device=mask.device, dtype=mask.dtype)
            logits[:, mask == not_present_value] = float("-inf")

        # NOTE: for columns where ALL the elements are NOT_PRESENT, e.g.
        # because the particular column does not exist in the segment
        # that the batch came from, all the entries in the `logits`
        # tensor will be float("-inf"), and therefore the loss
        # below will be torch.tensor([nan, ..., nan]) where there will
        # be as many `nan`s as there are rows in the batch.

        loss = self.ce_loss(logits, targets)

        # CRITICAL FIX: Replace NaN losses with 0.0 to prevent gradient explosions
        # NaN occurs when all logits are -inf (all elements NOT_PRESENT)
        # Using 0.0 means these columns don't contribute to training signal
        # rather than corrupting the entire gradient flow
        nan_mask = torch.isnan(loss)
        if nan_mask.any():
            loss = torch.where(nan_mask, torch.zeros_like(loss), loss)

        # DEBUG: Log loss statistics
        if not hasattr(self, '_loss_debug_count'):
            self._loss_debug_count = 0
        if self._loss_debug_count < 10:
            with torch.no_grad():
                logger.info(f"🔍 Loss debug: loss.mean()={loss.mean():.4f}, logits range=[{logits.min():.2f}, {logits.max():.2f}], "
                           f"logits.diag().mean()={logits.diag().mean():.4f}, log(N)={math.log(batch_size):.4f}")
            self._loss_debug_count += 1

        if return_logits:
            return loss, logits
        return loss

    def compute_spread_loss(
        self, unmasked_encoding, joint_encoding_1, joint_encoding_2, temp=None, temp_multiplier=1.0
    ):
        """
        Compute spread loss with adaptive temperature.
        
        Temperature controls the sharpness of the contrastive learning objective:
        - Lower temp (e.g., 0.01) = sharper, more aggressive separation
        - Higher temp (e.g., 0.1) = softer, more forgiving of nearby embeddings
        
        Args:
            temp: Temperature value. If None, computed adaptively based on batch size and n_columns
            temp_multiplier: Multiplier applied to temperature during NO_LEARNING recovery (default 1.0)
        """
        force_cpu = os.environ.get('FEATRIX_FORCE_CPU_SINGLE_PREDICTOR') == '1'
        target_device = torch.device('cpu') if force_cpu else get_device()
        
        batch_size = unmasked_encoding.shape[0]
        targets = torch.arange(batch_size).to(target_device)
        
        # Compute adaptive temperature if not provided
        if temp is None:
            # Get number of columns from the encoder config
            n_columns = len(self.col_codecs_in_order)
            
            # Adaptive temperature formula:
            # - Scales with batch size: larger batches can handle sharper temp
            # - Scales with data richness: more columns = more discriminative power
            # Base temp of 0.2 (increased from 0.05 to make task harder)
            base_temp = 0.2
            
            # Batch size factor: normalize to batch_size=128
            # Larger batches → lower temp (sharper)
            batch_factor = max(0.5, min(2.0, batch_size / 128.0))
            
            # Column factor: normalize to 20 columns
            # More columns → lower temp (sharper) because embeddings are more discriminative
            column_factor = max(0.5, min(1.5, n_columns / 20.0))
            
            # Compute adaptive temp
            temp = base_temp / (batch_factor * column_factor)
        
        # Apply temp multiplier for NO_LEARNING recovery
        temp = temp * temp_multiplier
        
        # Clamp to reasonable range
        temp = max(0.01, min(0.4, temp))  # Increased max to 0.4 for multiplier support
        
        # Store temperature for logging (convert to float for JSON serialization)
        self._last_spread_temp = float(temp)

        logits_joint = unmasked_encoding @ unmasked_encoding.T / temp
        spread_loss_joint = F.cross_entropy(logits_joint, targets)

        logits_1 = joint_encoding_1 @ joint_encoding_1.T / temp
        spread_loss_1 = F.cross_entropy(logits_1, targets)

        logits_2 = joint_encoding_2 @ joint_encoding_2.T / temp
        spread_loss_2 = F.cross_entropy(logits_2, targets)

        loss_config = self.config.loss_config.spread_loss_config

        total = (
            loss_config.joint_weight * spread_loss_joint
            + loss_config.marginal_weight * spread_loss_1
            + loss_config.marginal_weight * spread_loss_2
        )

        dict = {
            "joint": spread_loss_joint.item(),
            "mask_1": spread_loss_1.item(),
            "mask_2": spread_loss_2.item(),
            "temperature": self._last_spread_temp,
        }

        return total, dict

    def compute_per_row_ranks(
        self, unmasked_encoding, joint_encoding_1, joint_encoding_2, temp=None
    ) -> Tuple[List[int], List[float]]:
        """
        Compute per-row ranks and losses for validation tracking.

        For each row, computes where the correct match (diagonal) ranks when
        sorted by similarity. Rank 1 = perfect, higher = worse.

        Args:
            unmasked_encoding: Joint encoding from unmasked columns
            joint_encoding_1: Joint encoding from mask 1
            joint_encoding_2: Joint encoding from mask 2
            temp: Temperature for similarity computation

        Returns:
            (row_ranks, row_losses):
                row_ranks: List of ints, rank of correct match per row (1-indexed)
                row_losses: List of floats, per-row cross-entropy loss
        """
        batch_size = unmasked_encoding.shape[0]

        # Use stored temperature or compute
        if temp is None:
            temp = getattr(self, '_last_spread_temp', 0.1)

        # Compute similarity matrix (same as spread loss)
        logits = unmasked_encoding @ unmasked_encoding.T / temp

        row_ranks = []
        row_losses = []

        # For each row, compute rank and loss
        for i in range(batch_size):
            row_logits = logits[i, :]  # (batch_size,)

            # Rank: where does the diagonal element (correct match) rank?
            # Sort descending, find position of correct answer
            sorted_indices = torch.argsort(row_logits, descending=True)
            rank = (sorted_indices == i).nonzero(as_tuple=True)[0].item() + 1  # 1-indexed
            row_ranks.append(rank)

            # Per-row cross-entropy loss (how confident is the model about this row?)
            target = torch.tensor([i], device=logits.device)
            row_loss = F.cross_entropy(row_logits.unsqueeze(0), target).item()
            row_losses.append(row_loss)

        return row_ranks, row_losses

    def compute_diversity_loss(self, embeddings):
        """
        Compute embedding diversity loss to prevent collapse.
        
        This loss encourages embeddings to spread out across the embedding space
        by penalizing low variance in each dimension. It helps prevent the
        pathological case where all embeddings become nearly identical despite
        good contrastive loss.
        
        The loss is computed as:
        1. Calculate per-dimension std across the batch
        2. Target std is 1/sqrt(d_model) (expected for normalized random vectors)
        3. Loss = mean((target_std - actual_std)^2) for dimensions below target
        
        Args:
            embeddings: (batch_size, d_model) tensor of L2-normalized embeddings
        
        Returns:
            diversity_loss: Scalar tensor
            diversity_dict: Dict with diagnostic info (mean_std, min_std, target_std)
        """
        # embeddings shape: (batch_size, d_model)
        batch_size, d_model = embeddings.shape
        
        # Compute per-dimension statistics
        mean_per_dim = embeddings.mean(dim=0)  # (d_model,)
        std_per_dim = embeddings.std(dim=0)    # (d_model,)
        
        # Target std for normalized random vectors on unit sphere
        # For uniformly distributed points on unit sphere: std ≈ 1/sqrt(d_model)
        target_std = 1.0 / (d_model ** 0.5)
        
        # Penalize dimensions with std below target (collapsed dimensions)
        # Only penalize low std, not high std (we want spreading, not uniformity)
        std_deficit = torch.clamp(target_std - std_per_dim, min=0.0)
        
        # Mean squared deficit
        diversity_loss = (std_deficit ** 2).mean()
        
        # Diagnostics
        diversity_dict = {
            "mean_std": std_per_dim.mean().item(),
            "min_std": std_per_dim.min().item(),
            "max_std": std_per_dim.max().item(),
            "target_std": target_std,
            "pct_below_target": (std_per_dim < target_std).float().mean().item() * 100.0,
        }
        
        return diversity_loss, diversity_dict

    def update_col_prediction_stats(self, col_name: str, logits: torch.Tensor, prediction_mask: torch.Tensor):
        """
        Update column prediction accuracy stats from logits.

        Args:
            col_name: Column name
            logits: (batch_size, batch_size) similarity matrix
            prediction_mask: (batch_size,) boolean mask of which rows had this column masked
        """
        if col_name not in self.col_prediction_stats:
            return

        with torch.no_grad():
            # Only look at rows where this column was masked (being predicted)
            masked_indices = prediction_mask.nonzero(as_tuple=True)[0]
            if len(masked_indices) == 0:
                return

            batch_size = logits.shape[0]
            stats = self.col_prediction_stats[col_name]

            for idx in masked_indices:
                i = idx.item()
                row_logits = logits[i, :]  # (batch_size,)

                # Rank: position of correct answer (diagonal element) when sorted descending
                sorted_indices = torch.argsort(row_logits, descending=True)
                rank = (sorted_indices == i).nonzero(as_tuple=True)[0].item() + 1  # 1-indexed

                stats['attempts'] += 1

                if rank == 1:
                    stats['top1'] += 1
                elif rank <= 5:
                    stats['top5'] += 1
                elif rank <= 20:
                    stats['top20'] += 1
                elif rank <= 50:
                    stats['top50'] += 1
                else:
                    stats['miss'] += 1

    def get_col_prediction_summary(self, col_name: str) -> dict:
        """Get prediction accuracy summary for a column."""
        if col_name not in self.col_prediction_stats:
            return None
        stats = self.col_prediction_stats[col_name]
        attempts = stats['attempts']
        if attempts == 0:
            return {'attempts': 0, 'accuracy': None}

        return {
            'attempts': attempts,
            'top1_pct': 100.0 * stats['top1'] / attempts,
            'top5_pct': 100.0 * stats['top5'] / attempts,
            'top20_pct': 100.0 * stats['top20'] / attempts,
            'top50_pct': 100.0 * stats['top50'] / attempts,
            'miss_pct': 100.0 * stats['miss'] / attempts,
            # Cumulative: top1 + top5 = "good" predictions (rank <= 5)
            'top5_cumul_pct': 100.0 * (stats['top1'] + stats['top5']) / attempts,
        }

    def get_all_col_prediction_summaries(self) -> dict:
        """Get prediction accuracy summaries for all columns, sorted by top5_cumul_pct."""
        summaries = {}
        for col_name in self.col_prediction_stats:
            summary = self.get_col_prediction_summary(col_name)
            if summary and summary['attempts'] > 0:
                summaries[col_name] = summary
        # Sort by top5_cumul_pct descending (best predictable columns first)
        return dict(sorted(summaries.items(), key=lambda x: x[1].get('top5_cumul_pct', 0), reverse=True))

    def log_col_prediction_stats(self):
        """Log column importance stats based on embedding stability under masking."""
        summaries = self.get_all_col_prediction_summaries()
        if not summaries:
            logger.info("📊 Column importance stats: No data yet")
            return

        # Sort by miss% descending (highest miss = most important)
        summaries_by_importance = dict(sorted(summaries.items(), key=lambda x: x[1].get('miss_pct', 0), reverse=True))

        logger.info("📊 Column Importance (embedding stability when masked):")
        logger.info("   Low retrieval = column is unique/important (masking it destroys embedding identity)")
        logger.info("   High retrieval = column is redundant (other columns capture same info)")
        logger.info("")
        logger.info("   Column                           | Attempts | Retain | Importance")
        logger.info("   " + "-" * 60)

        for col_name, stats in summaries_by_importance.items():
            # Truncate long column names
            display_name = col_name[:33] + "..." if len(col_name) > 33 else col_name
            # Retain% = how often embedding still finds itself (low = important)
            retain_pct = stats['top5_cumul_pct']
            # Importance = inverse of retain (high miss = high importance)
            importance = "★★★" if stats['miss_pct'] > 90 else "★★" if stats['miss_pct'] > 70 else "★" if stats['miss_pct'] > 50 else "·"
            logger.info(
                f"   {display_name:36} | {stats['attempts']:8} | {retain_pct:5.1f}% | {importance} ({stats['miss_pct']:.0f}% unique)"
            )

        # Summary stats
        total_attempts = sum(s['attempts'] for s in summaries.values())
        avg_miss = sum(s['miss_pct'] for s in summaries.values()) / len(summaries) if summaries else 0

        logger.info("   " + "-" * 60)
        logger.info(f"   {len(summaries)} columns, {total_attempts} total masks, avg {avg_miss:.0f}% unique info per column")

    def reset_col_prediction_stats(self):
        """Reset all column prediction stats (e.g., at start of epoch)."""
        for col_name in self.col_prediction_stats:
            self.col_prediction_stats[col_name] = {
                'attempts': 0,
                'top1': 0,
                'top5': 0,
                'top20': 0,
                'top50': 0,
                'miss': 0,
            }

    def debug_joint_predictor_weights(self, epoch: int) -> dict:
        """
        Log joint predictor weight statistics and changes between epochs.
        Returns metrics dict for timeline.

        Grep keyword: [JOINT_DEBUG]
        """
        metrics = {}

        with torch.no_grad():
            # Get current weights as flat vector
            current_weights = torch.cat([
                p.detach().flatten() for p in self.joint_predictor.parameters()
            ])

            # Weight statistics
            weight_norm = current_weights.norm().item()
            weight_mean = current_weights.mean().item()
            weight_std = current_weights.std().item()
            weight_max = current_weights.abs().max().item()

            metrics['weight_norm'] = weight_norm
            metrics['weight_std'] = weight_std

            # Store initial weights on first call
            if self._joint_predictor_initial_weights is None:
                self._joint_predictor_initial_weights = current_weights.clone()
                logger.info(f"[JOINT_DEBUG] epoch={epoch} | INIT weights: norm={weight_norm:.4f} std={weight_std:.4f} max={weight_max:.4f}")
                metrics['weight_change_from_init'] = 0.0
                metrics['weight_change_from_last'] = 0.0
            else:
                # Change from initial
                change_from_init = (current_weights - self._joint_predictor_initial_weights).norm().item()
                change_from_init_pct = change_from_init / (self._joint_predictor_initial_weights.norm().item() + 1e-8) * 100

                # Change from last epoch
                if self._joint_predictor_last_weights is not None:
                    change_from_last = (current_weights - self._joint_predictor_last_weights).norm().item()
                    change_from_last_pct = change_from_last / (self._joint_predictor_last_weights.norm().item() + 1e-8) * 100
                else:
                    change_from_last = 0.0
                    change_from_last_pct = 0.0

                metrics['weight_change_from_init'] = change_from_init
                metrics['weight_change_from_last'] = change_from_last

                logger.info(f"[JOINT_DEBUG] epoch={epoch} | weights: norm={weight_norm:.4f} std={weight_std:.4f} | "
                           f"Δ_init={change_from_init:.4f} ({change_from_init_pct:.2f}%) | "
                           f"Δ_last={change_from_last:.4f} ({change_from_last_pct:.2f}%)")

                # ALERT if weights aren't changing
                if epoch > 2 and change_from_init_pct < 0.1:
                    logger.warning(f"[JOINT_DEBUG] ⚠️  WEIGHTS BARELY CHANGED! Only {change_from_init_pct:.2f}% from init after {epoch} epochs")

            # Store for next epoch
            self._joint_predictor_last_weights = current_weights.clone()

            # Also check gradient statistics if available
            grad_norms = []
            for name, p in self.joint_predictor.named_parameters():
                if p.grad is not None:
                    grad_norms.append(p.grad.norm().item())

            if grad_norms:
                total_grad_norm = sum(g**2 for g in grad_norms) ** 0.5
                metrics['grad_norm'] = total_grad_norm
                logger.info(f"[JOINT_DEBUG] epoch={epoch} | grad_norm={total_grad_norm:.6f} (n_params_with_grad={len(grad_norms)})")
                if total_grad_norm < 1e-6:
                    logger.warning(f"[JOINT_DEBUG] ⚠️  VANISHING GRADIENTS! grad_norm={total_grad_norm:.6f}")
            else:
                logger.info(f"[JOINT_DEBUG] epoch={epoch} | No gradients computed yet this epoch")

            # Include separation metric (computed in compute_joint_infoNCE_loss)
            if hasattr(self, '_joint_separation'):
                metrics['separation'] = self._joint_separation

            # Aggregate per-batch rank metrics collected during training
            if hasattr(self, '_rank_batch_data') and self._rank_batch_data:
                import numpy as np
                batch_data = self._rank_batch_data

                pred_rank1_values = [b['pred_rank1'] for b in batch_data]
                identity_rank1_values = [b['identity_rank1'] for b in batch_data]
                identity_diff_values = [b['identity_diff'] for b in batch_data]

                metrics['rank_stats'] = {
                    'pred_rank1_mean': float(np.mean(pred_rank1_values)),
                    'pred_rank1_std': float(np.std(pred_rank1_values)),
                    'identity_rank1_mean': float(np.mean(identity_rank1_values)),
                    'identity_rank1_std': float(np.std(identity_rank1_values)),
                    'identity_diff_mean': float(np.mean(identity_diff_values)),
                    'identity_diff_std': float(np.std(identity_diff_values)),
                    'n_batches': len(batch_data),
                }

                logger.info(f"[JOINT_DEBUG] epoch={epoch} | RANK_STATS: "
                           f"pred_rank1={metrics['rank_stats']['pred_rank1_mean']*100:.1f}%±{metrics['rank_stats']['pred_rank1_std']*100:.1f}% "
                           f"identity_rank1={metrics['rank_stats']['identity_rank1_mean']*100:.1f}%±{metrics['rank_stats']['identity_rank1_std']*100:.1f}% "
                           f"identity_diff={metrics['rank_stats']['identity_diff_mean']:.4f}±{metrics['rank_stats']['identity_diff_std']:.4f} "
                           f"(n={metrics['rank_stats']['n_batches']} batches)")

        return metrics

    def update_col_mi(self, col_name, update_value):
        ema_coeff = 0.99

        old_value = self.col_mi_estimates[col_name]
        if old_value is None:
            new_value = update_value
        else:
            new_value = (1 - ema_coeff) * update_value + ema_coeff * old_value

        self.col_mi_estimates[col_name] = new_value
        
        # Update MI estimates in relationship extractor
        if hasattr(self.joint_encoder, 'update_mi_estimates'):
            self.joint_encoder.update_mi_estimates(
                self.col_mi_estimates, self.joint_mi_estimate
            )

    def update_joint_mi(self, update_value):
        ema_coeff = 0.99

        if self.joint_mi_estimate is None:
            self.joint_mi_estimate = update_value
        else:
            self.joint_mi_estimate = (
                1 - ema_coeff
            ) * update_value + ema_coeff * self.joint_mi_estimate
        
        # Update MI estimates in relationship extractor
        if hasattr(self.joint_encoder, 'update_mi_estimates'):
            self.joint_encoder.update_mi_estimates(
                self.col_mi_estimates, self.joint_mi_estimate
            )

    def compute_marginal_infoNCE_loss(
        self,
        batch_size,
        column_predictions,
        column_encodings,
        status_mask,
        update_mi=False,
        column_batches=None,  # Optional: raw token batches for reconstruction loss
    ):
        # def compute_marginal_infoNCE_loss(self, marginal_encodings, column_encodings, status_mask):
        """
        column_encodings: a 3D tensor (batch_size, n_cols, d_model)
        column_predictions: list of tensors, each tensor is of shape (batch_size, d_model)
                            There's one tensor per column in the dataset.
        column_batches: Optional dict of {col_name: TokenBatch} for reconstruction loss
        """
        # We ONLY want to focus on predicting marginals that have been replaced in the
        # status mask.
        # CRITICAL: Create MARGINAL value as tensor on same device
        marginal_value = torch.tensor(TokenStatus.MARGINAL, device=status_mask.device, dtype=status_mask.dtype)
        prediction_mask = status_mask == marginal_value

        # CRITICAL: Compute adaptive temperature for all marginal predictions
        # Use same formula as joint loss for consistency
        temperature = self._compute_adaptive_temperature(batch_size)

        # DIAGNOSTIC: Comprehensive marginal loss diagnostics
        current_epoch = getattr(self, '_current_epoch', 0)
        if not hasattr(self, '_marginal_diag_epoch') or self._marginal_diag_epoch != current_epoch:
            self._marginal_diag_epoch = current_epoch
            with torch.no_grad():
                # Stack predictions: (B, n_cols, d_model)
                pred_stack = torch.stack(column_predictions, dim=1)

                # Normalize for cosine similarity
                pred_norm = F.normalize(pred_stack, dim=2)
                target_norm = F.normalize(column_encodings, dim=2)

                # Per-position cosine similarity: (B, n_cols)
                cos_sim = (pred_norm * target_norm).sum(dim=2)

                # Separate by masked vs unmasked
                masked_sims = cos_sim[prediction_mask]
                unmasked_sims = cos_sim[~prediction_mask]

                masked_mean = masked_sims.mean().item() if len(masked_sims) > 0 else 0.0
                masked_std = masked_sims.std().item() if len(masked_sims) > 1 else 0.0
                unmasked_mean = unmasked_sims.mean().item() if len(unmasked_sims) > 0 else 0.0
                unmasked_std = unmasked_sims.std().item() if len(unmasked_sims) > 1 else 0.0

                logger.info(f"🎯 [epoch={current_epoch}] MARGINAL PREDICTION QUALITY:")
                logger.info(f"   Pred-Target cosine: masked={masked_mean:.4f}±{masked_std:.4f} ({len(masked_sims)} samples), "
                           f"unmasked={unmasked_mean:.4f}±{unmasked_std:.4f}")

                # ================================================================
                # DIAGNOSTIC 1: Target diversity per column
                # If targets are all similar, InfoNCE can't work
                # ================================================================
                n_cols = column_encodings.shape[1]
                off_diag_mask = ~torch.eye(batch_size, dtype=torch.bool, device=pred_norm.device)
                target_diversity_info = []
                for col_i in range(min(n_cols, 5)):  # First 5 columns
                    col_tgt = target_norm[:, col_i, :]  # (B, d_model)
                    tgt_sim_matrix = col_tgt @ col_tgt.T  # (B, B)
                    tgt_off_diag = tgt_sim_matrix[off_diag_mask].mean().item() if batch_size > 1 else 0.0
                    col_name = self.idx_to_col_name.get(col_i, f"col_{col_i}")
                    target_diversity_info.append(f"{col_name}={tgt_off_diag:.3f}")
                logger.info(f"   TARGET DIVERSITY (avg pairwise cos, low=diverse): {', '.join(target_diversity_info)}")

                # ================================================================
                # DIAGNOSTIC 2: Column predictor output diversity
                # Does MLP collapse the joint embedding diversity?
                # ================================================================
                pred_diversity_info = []
                for col_i in range(min(n_cols, 5)):  # First 5 columns
                    col_pred = pred_norm[:, col_i, :]  # (B, d_model)
                    pred_sim_matrix = col_pred @ col_pred.T  # (B, B)
                    pred_off_diag = pred_sim_matrix[off_diag_mask].mean().item() if batch_size > 1 else 0.0
                    col_name = self.idx_to_col_name.get(col_i, f"col_{col_i}")
                    pred_diversity_info.append(f"{col_name}={pred_off_diag:.3f}")
                logger.info(f"   PRED DIVERSITY (avg pairwise cos, low=diverse): {', '.join(pred_diversity_info)}")

                # ================================================================
                # DIAGNOSTIC 3: Per-column SEPARATION (not just first column)
                # ================================================================
                masked_cols = prediction_mask.any(dim=0).nonzero(as_tuple=True)[0]
                sep_info = []
                for col_idx in masked_cols[:5]:  # First 5 masked columns
                    col_idx = col_idx.item()
                    col_pred = pred_norm[:, col_idx, :]
                    col_tgt = target_norm[:, col_idx, :]
                    sim_matrix = col_pred @ col_tgt.T
                    diag_sim = sim_matrix.diag().mean().item()
                    off_diag_sim = sim_matrix[off_diag_mask].mean().item()
                    separation = diag_sim - off_diag_sim
                    col_name = self.idx_to_col_name.get(col_idx, f"col_{col_idx}")
                    sep_info.append(f"{col_name}={separation:.4f}")
                if sep_info:
                    logger.info(f"   PER-COL SEPARATION: {', '.join(sep_info)}")

                # ================================================================
                # DIAGNOSTIC 4: Gradient check - are column predictors getting grads?
                # ================================================================
                if self.training and hasattr(self, 'column_predictor'):
                    first_col = list(self.column_predictor.col_predictors.keys())[0]
                    first_mlp = self.column_predictor.col_predictors[first_col]
                    # Check if weights have grad from previous backward
                    has_grad = False
                    grad_norm = 0.0
                    for param in first_mlp.parameters():
                        if param.grad is not None:
                            has_grad = True
                            grad_norm = param.grad.norm().item()
                            break
                    logger.info(f"   COL_PREDICTOR GRAD: has_grad={has_grad}, norm={grad_norm:.6f}")

                # ================================================================
                # DIAGNOSTIC 5: MSE baseline - what would perfect prediction look like?
                # ================================================================
                if prediction_mask.any():
                    # MSE between targets (self-MSE should be 0)
                    # MSE between random pairs of targets
                    tgt_masked = target_norm[prediction_mask]
                    if len(tgt_masked) > 1:
                        # Random pair MSE (shuffle and compare)
                        perm = torch.randperm(len(tgt_masked))
                        random_mse = F.mse_loss(tgt_masked, tgt_masked[perm]).item()
                        # Current pred MSE
                        pred_masked = pred_norm[prediction_mask]
                        current_mse = F.mse_loss(pred_masked, tgt_masked).item()
                        logger.info(f"   MSE: current={current_mse:.4f}, random_baseline={random_mse:.4f} (should be < random)")

                # Overall summary with warning
                if len(masked_cols) > 0:
                    col_idx = masked_cols[0].item()
                    col_pred = pred_norm[:, col_idx, :]
                    col_tgt = target_norm[:, col_idx, :]
                    sim_matrix = col_pred @ col_tgt.T
                    diag_sim = sim_matrix.diag().mean().item()
                    off_diag_sim = sim_matrix[off_diag_mask].mean().item()
                    separation = diag_sim - off_diag_sim
                    if separation < 0.05:
                        logger.warning(f"   ⚠️  LOW SEPARATION: {separation:.4f} < 0.05 - predictions can't distinguish rows!")

        # Compute the infoNCE loss for each marginal distribution.
        # This requries matching predictions and encodings for each column.
        mean_loss_per_column = []

        # We iterate over the codecs, extrac the relevant predictions and column encodigns, and
        # compute the average loss over the MARGINAL tokens, which signify the predictions we
        # actually need to make
        # for i, codec in enumerate(self.col_codecs_in_order):
        col_losses_dict = dict()
        for i, col_prediction in enumerate(column_predictions):
            # the shape of column_encodings is (batch_size, n_cols, model_dim)
            col_target = column_encodings[:, i, :]
            # mask shape is (batch_size, n_col). The third dimension is not present because
            # the mask is a boolean
            col_status_mask = status_mask[:, i]

            # col_losses is a 1D tensor of losses for each row
            # CRITICAL: Pass temperature to infoNCE_loss (was missing before!)
            # Get logits back for prediction accuracy tracking
            col_losses, col_logits = self.infoNCE_loss(
                col_prediction, col_target, col_status_mask, unknown_targets=False,
                temperature=temperature, return_logits=True
            )

            # pick out the losses corresponding to the MARGINAL tokens
            col_prediction_mask = prediction_mask[:, i]
            col_prediction_losses = col_losses[col_prediction_mask]

            col_name = self.idx_to_col_name[i]

            # Update prediction accuracy stats (only during training, sample periodically)
            if self.training and hasattr(self, 'col_prediction_stats'):
                # Sample 10% of batches to avoid overhead
                if not hasattr(self, '_pred_stats_sample_counter'):
                    self._pred_stats_sample_counter = 0
                self._pred_stats_sample_counter += 1
                if self._pred_stats_sample_counter % 10 == 0:
                    self.update_col_prediction_stats(col_name, col_logits, col_prediction_mask)

            if len(col_prediction_losses) == 0:
                # Make this a tensor for consistency - using a bare float causes issues
                # if we e.g. want to call .item() on it.
                col_loss_avg = torch.tensor(0.0, device=status_mask.device)

                # If there are no predictions, which can happen e.g. for columns that are
                # not present in a particular data segment (for multi-segment datasets),
                # we do not update MI because col_loss_avg=0 is just a neural component
                # when it comes to computing gradients, but it does NOT fit in with the
                # formula used to compute mutual information.
            else:
                # CRITICAL FIX: Filter out any remaining NaN values before computing mean
                # NaN can occur if infoNCE_loss produces NaN for certain edge cases
                valid_losses = col_prediction_losses[~torch.isnan(col_prediction_losses)]
                if len(valid_losses) == 0:
                    # All losses were NaN - use zero to avoid gradient corruption
                    col_loss_avg = torch.tensor(0.0, device=status_mask.device)
                else:
                    # This is where we average the loss across all the MARGINAL tokens,
                    # i.e. across all the valid predictions.
                    col_loss_avg = torch.mean(valid_losses)
                
                # Store raw loss (more interpretable than derived MI score!)
                raw_loss = col_loss_avg.detach().item()
                ema_coeff = 0.99
                old_loss = self.col_loss_estimates[col_name]
                if old_loss is None:
                    self.col_loss_estimates[col_name] = raw_loss
                else:
                    self.col_loss_estimates[col_name] = (1 - ema_coeff) * raw_loss + ema_coeff * old_loss

                # Compute predictability score: how well can we predict this column from context?
                # 
                # We use a simple percentage-based score derived from loss vs random baseline:
                # - log(N) is the theoretical maximum loss for random predictions (all negatives equally likely)
                # - loss < log(N) means better than random (positive predictability)
                # - loss > log(N) means worse than random (can happen with poor temperature or model failure)
                #
                # Score formula: predictability = (log(N) - loss) / log(N) * 100
                # - 0% = random baseline (loss = log(N))
                # - 100% = perfect prediction (loss = 0)
                # - Negative = worse than random (clamped to 0 for display)
                #
                # NOTE: Temperature scaling is already applied in infoNCE_loss(), so the raw_loss
                # values are computed with the correct temperature. The theoretical maximum log(N) is
                # temperature-independent (random baseline is always log(N) regardless of temperature).
                # With proper temperature (e.g., 0.1), good learning produces losses well below log(N).
                log_n = math.log(batch_size)
                
                # Compute percentage predictability (0-100 scale, clamped)
                # Higher = more predictable from other columns
                predictability_pct = ((log_n - raw_loss) / log_n) * 100 if log_n > 0 else 0
                predictability_pct = max(0, min(100, predictability_pct))
                
                if update_mi:
                    self.update_col_mi(col_name, predictability_pct)

            col_losses_dict[col_name] = col_loss_avg.detach().item()
            mean_loss_per_column.append(col_loss_avg)

        total_infoNCE = sum(mean_loss_per_column)

        # RECONSTRUCTION LOSS: Direct value prediction (optional, controlled by feature flag)
        reconstruction_loss = torch.tensor(0.0, device=status_mask.device)
        reconstruction_loss_dict = {}

        if (self.column_predictor.enable_reconstruction and
            self.column_predictor.value_heads is not None and
            column_batches is not None):

            # Get reconstruction weight from config
            from featrix.neural.sphere_config import SphereConfig
            sphere_config = SphereConfig.get_instance()
            recon_weight = sphere_config.get_reconstruction_loss_weight()

            # Get value predictions from the column predictor
            value_predictions = self.column_predictor.predict_values(column_predictions)

            if value_predictions:
                recon_losses = []

                for i, col_name in enumerate(self.column_predictor.cols_in_order):
                    # CRITICAL: Skip internal __featrix_ columns - they should never have reconstruction loss
                    if is_internal_column(col_name):
                        continue
                    if col_name not in value_predictions:
                        continue
                    if col_name not in column_batches:
                        continue

                    col_type = self.column_predictor.col_types.get(col_name)
                    pred = value_predictions[col_name]  # [batch, 1] for scalar, [batch, n_classes] for set
                    token_batch = column_batches[col_name]
                    target_values = token_batch["values"]  # [batch] or [batch, ...]
                    target_status = token_batch["status"]  # [batch]

                    # Only compute loss for MARGINAL tokens (the ones we're trying to predict)
                    col_prediction_mask = prediction_mask[:, i]

                    if col_prediction_mask.sum() == 0:
                        continue

                    # Ensure tensors are on same device
                    if target_values.device != pred.device:
                        target_values = target_values.to(pred.device)
                    if col_prediction_mask.device != pred.device:
                        col_prediction_mask = col_prediction_mask.to(pred.device)

                    if col_type == ColumnType.SCALAR:
                        # MSE loss for scalars (normalized values)
                        pred_masked = pred[col_prediction_mask].squeeze(-1)  # [n_marginal]
                        target_masked = target_values[col_prediction_mask]  # [n_marginal]

                        if len(pred_masked) > 0 and len(target_masked) > 0:
                            # Handle NaN in both targets AND predictions
                            valid_mask = ~torch.isnan(target_masked) & ~torch.isnan(pred_masked)
                            if valid_mask.sum() > 0:
                                col_recon_loss = F.mse_loss(
                                    pred_masked[valid_mask],
                                    target_masked[valid_mask]
                                )
                                # CRITICAL: Skip NaN/Inf losses to prevent gradient corruption
                                if not (torch.isnan(col_recon_loss) or torch.isinf(col_recon_loss)):
                                    recon_losses.append(col_recon_loss)
                                    reconstruction_loss_dict[col_name] = col_recon_loss.detach().item()

                    elif col_type == ColumnType.SET:
                        # CrossEntropy loss for sets/categoricals
                        pred_masked = pred[col_prediction_mask]  # [n_marginal, n_classes]
                        target_masked = target_values[col_prediction_mask].long()  # [n_marginal] class indices

                        if len(pred_masked) > 0 and len(target_masked) > 0:
                            # Clamp target indices to valid range
                            n_classes = pred_masked.shape[-1]
                            target_masked = torch.clamp(target_masked, 0, n_classes - 1)

                            # CRITICAL: Check for -inf in predictions which causes NaN loss
                            # Replace -inf with large negative value to avoid NaN
                            if torch.isinf(pred_masked).any():
                                pred_masked = torch.clamp(pred_masked, min=-100.0, max=100.0)

                            col_recon_loss = F.cross_entropy(pred_masked, target_masked)
                            # CRITICAL: Skip NaN/Inf losses to prevent gradient corruption
                            if not (torch.isnan(col_recon_loss) or torch.isinf(col_recon_loss)):
                                recon_losses.append(col_recon_loss)
                                reconstruction_loss_dict[col_name] = col_recon_loss.detach().item()

                if recon_losses:
                    reconstruction_loss = sum(recon_losses) * recon_weight

        # ============================================================================
        # MSE LOSS: Direct embedding matching (helps when InfoNCE isn't working)
        # ============================================================================
        # InfoNCE alone isn't providing enough gradient signal - predictions have
        # near-zero SEPARATION (can't distinguish rows). Add MSE to force direct
        # alignment between predictions and targets for masked columns.
        # ============================================================================
        mse_loss = torch.tensor(0.0, device=status_mask.device)
        mse_weight = 0.1  # Start small, can tune

        if prediction_mask.any():
            # Stack predictions: (B, n_cols, d_model)
            pred_stack = torch.stack(column_predictions, dim=1)

            # MSE only on masked positions
            pred_masked = pred_stack[prediction_mask]  # (n_masked, d_model)
            target_masked = column_encodings[prediction_mask]  # (n_masked, d_model)

            # CRITICAL: Filter out NaN values before MSE computation
            valid_mask = ~(torch.isnan(pred_masked).any(dim=1) | torch.isnan(target_masked).any(dim=1))
            if valid_mask.sum() > 0:
                pred_valid = pred_masked[valid_mask]
                target_valid = target_masked[valid_mask]

                # Normalize before MSE so we're comparing directions, not magnitudes
                pred_masked_norm = F.normalize(pred_valid, dim=1)
                target_masked_norm = F.normalize(target_valid, dim=1)

                mse_loss = F.mse_loss(pred_masked_norm, target_masked_norm)

                # CRITICAL: Skip NaN/Inf MSE loss
                if torch.isnan(mse_loss) or torch.isinf(mse_loss):
                    mse_loss = torch.tensor(0.0, device=status_mask.device)
                else:
                    col_losses_dict['__featrix_mse_loss'] = mse_loss.detach().item()

        # ============================================================================
        # METRIC LEARNING LOSS: Preserve ordinal relationships for scalar columns
        # ============================================================================
        # For scalar columns, teach the encoder that embedding distances should be
        # proportional to value differences: |embed(x) - embed(y)| ∝ |x - y|
        # This directly addresses the "linearity" issue in embedding quality metrics.
        # ============================================================================
        metric_loss = torch.tensor(0.0, device=status_mask.device)
        metric_weight = 1.0  # Strong weight since this is critical for scalar quality
        metric_loss_count = 0

        if column_batches is not None and hasattr(self, 'column_predictor'):
            # Iterate over scalar columns
            for i, col_name in enumerate(self.column_predictor.cols_in_order):
                # Skip internal columns
                if is_internal_column(col_name):
                    continue

                col_type = self.column_predictor.col_types.get(col_name)
                if col_type != ColumnType.SCALAR:
                    continue

                if col_name not in column_batches:
                    continue

                token_batch = column_batches[col_name]
                values = token_batch["values"]  # [batch] - normalized scalar values

                # Get the column encodings for this column
                col_encodings = column_encodings[:, i, :]  # [batch, d_model]

                # Ensure tensors are on same device
                if values.device != col_encodings.device:
                    values = values.to(col_encodings.device)

                # Filter out NaN values
                valid_mask = ~torch.isnan(values)
                if valid_mask.sum() < 4:  # Need at least 4 samples for meaningful pairs
                    continue

                valid_values = values[valid_mask]
                valid_encodings = col_encodings[valid_mask]
                n_valid = len(valid_values)

                # Sample pairs for efficiency (avoid O(n^2) for large batches)
                max_pairs = 256
                if n_valid * (n_valid - 1) // 2 > max_pairs:
                    # Random sampling of pairs
                    idx1 = torch.randint(0, n_valid, (max_pairs,), device=values.device)
                    idx2 = torch.randint(0, n_valid, (max_pairs,), device=values.device)
                    # Ensure idx1 != idx2
                    same_mask = idx1 == idx2
                    idx2[same_mask] = (idx2[same_mask] + 1) % n_valid
                else:
                    # All pairs for small batches
                    idx1, idx2 = torch.triu_indices(n_valid, n_valid, offset=1, device=values.device)

                # Compute value differences (target distances, normalized to [0, 1])
                value_diffs = torch.abs(valid_values[idx1] - valid_values[idx2])
                # Normalize by the value range in this batch
                value_range = valid_values.max() - valid_values.min()
                if value_range > 1e-6:
                    value_diffs_norm = value_diffs / value_range
                else:
                    continue  # Skip if all values are the same

                # Compute embedding distances
                emb_diffs = torch.norm(valid_encodings[idx1] - valid_encodings[idx2], dim=1)
                # Normalize by the max embedding distance in this batch
                emb_range = emb_diffs.max()
                if emb_range > 1e-6:
                    emb_diffs_norm = emb_diffs / emb_range
                else:
                    continue  # Skip if all embeddings are the same

                # Metric learning loss: MSE between normalized distances
                # This teaches: embedding distance ∝ value distance
                col_metric_loss = F.mse_loss(emb_diffs_norm, value_diffs_norm)

                if not (torch.isnan(col_metric_loss) or torch.isinf(col_metric_loss)):
                    metric_loss = metric_loss + col_metric_loss
                    metric_loss_count += 1
                    col_losses_dict[f'__featrix_metric_{col_name}'] = col_metric_loss.detach().item()

            # Average over columns
            if metric_loss_count > 0:
                metric_loss = metric_loss / metric_loss_count
                col_losses_dict['__featrix_metric_total'] = metric_loss.detach().item()

        # Combined total loss
        total = total_infoNCE + reconstruction_loss + mse_weight * mse_loss + metric_weight * metric_loss

        # Return reconstruction loss info in col_losses_dict for logging
        if reconstruction_loss_dict:
            col_losses_dict['__featrix_reconstruction_total'] = reconstruction_loss.detach().item()
            for col_name, loss_val in reconstruction_loss_dict.items():
                col_losses_dict[f'__featrix_recon_{col_name}'] = loss_val

        return total, col_losses_dict

    def _compute_adaptive_temperature(self, batch_size, temp_override=None):
        """
        Compute adaptive temperature for InfoNCE loss.
        
        Temperature controls sharpness of contrastive learning:
        - Lower temp (e.g., 0.01) = sharper, more aggressive separation
        - Higher temp (e.g., 0.2) = softer, more forgiving
        
        Args:
            batch_size: Current batch size
            temp_override: If provided, use this temperature instead of computing
            
        Returns:
            Temperature value (float)
        """
        if temp_override is not None:
            return temp_override
        
        n_columns = len(self.col_codecs_in_order)
        
        # Base temperature: reasonable default for most datasets
        base_temp = 0.1
        
        # Batch size factor: larger batches can handle sharper temp
        # Normalize to batch_size=256 (more common for real training)
        # Larger batches → more negatives → can use lower temp (sharper)
        batch_factor = max(0.7, min(1.5, batch_size / 256.0))
        
        # Column factor: more columns = more discriminative embeddings
        # Use log scaling so it doesn't blow up for large datasets
        # log(10) ≈ 1.0, log(100) ≈ 2.0, log(200) ≈ 2.3
        # This provides gentle scaling: 10 cols → 1.0×, 100 cols → 1.15×, 200 cols → 1.25×
        column_factor = 1.0 + (math.log10(max(10, n_columns)) - 1.0) * 0.15
        column_factor = max(0.8, min(1.5, column_factor))
        
        # Compute adaptive temp
        temp = base_temp / (batch_factor * column_factor)
        
        # Clamp to reasonable range
        # Lower bound: 0.05 (sharp but not too extreme)
        # Upper bound: 0.3 (soft but still learning)
        temp = max(0.05, min(0.3, temp))
        
        # Log temperature computation (only first few times to avoid spam)
        if not hasattr(self, '_temp_log_count'):
            self._temp_log_count = 0
        
        if self._temp_log_count < 10:  # Log first 10 calls
            logger.info(f"🌡️  InfoNCE Temperature: {temp:.4f} (batch={batch_size}, cols={n_columns}, "
                       f"batch_factor={batch_factor:.3f}, col_factor={column_factor:.3f})")
            self._temp_log_count += 1
        
        return temp

    def compute_joint_infoNCE_loss(
        self, joint_encoding, unmasked_encoding, short=False, temp=None, return_logits=False
    ):
        # Calculate adaptive temperature
        batch_size = joint_encoding.shape[0]
        temp = self._compute_adaptive_temperature(batch_size, temp_override=temp)

        if short:
            prediction = self.joint_predictor_short(joint_encoding)
        else:
            prediction = self.joint_predictor(joint_encoding)

        # [JOINT_DEBUG] Log input/output statistics once per epoch
        # This is the JOINT predictor path (different from ContrastiveLoss in loss_framework.py):
        # - Input: joint_encoding (masked view from joint encoder)
        # - Output: prediction (joint predictor output)
        # - Target: unmasked_encoding (unmasked view from joint encoder)
        # - The joint predictor transforms masked→predicted, compared against unmasked target
        current_epoch = getattr(self, '_current_epoch', 0)
        if not hasattr(self, '_joint_debug_last_epoch'):
            self._joint_debug_last_epoch = -1
        if current_epoch != self._joint_debug_last_epoch and not short:
            self._joint_debug_last_epoch = current_epoch
            with torch.no_grad():
                # Input stats (what goes into joint predictor)
                je_norm = joint_encoding.norm(dim=1).mean()
                je_std = joint_encoding.std()
                # Output stats (what comes out of joint predictor)
                pred_norm = prediction.norm(dim=1).mean()
                pred_std = prediction.std()
                # Target stats (what we're trying to match)
                target_norm = unmasked_encoding.norm(dim=1).mean()
                target_std = unmasked_encoding.std()

                # After normalization (what actually gets compared)
                pred_normalized = nn.functional.normalize(prediction, dim=1)
                target_normalized = nn.functional.normalize(unmasked_encoding, dim=1)

                # Cosine similarity between prediction and target
                sim_matrix = pred_normalized @ target_normalized.T
                diag_sim = sim_matrix.diag().mean()
                off_diag_sim = sim_matrix[~torch.eye(batch_size, dtype=torch.bool, device=sim_matrix.device)].mean()
                separation = diag_sim - off_diag_sim

                # Check INPUT diversity: are all joint_encoding rows similar to each other?
                # High input_self_sim means collapsed/uniform inputs
                je_normalized = nn.functional.normalize(joint_encoding, dim=1)
                input_self_sim = (je_normalized @ je_normalized.T)
                input_self_sim_offdiag = input_self_sim[~torch.eye(batch_size, dtype=torch.bool, device=input_self_sim.device)].mean()

                # Check TARGET diversity: are all unmasked_encoding rows similar?
                target_self_sim = (target_normalized @ target_normalized.T)
                target_self_sim_offdiag = target_self_sim[~torch.eye(batch_size, dtype=torch.bool, device=target_self_sim.device)].mean()

                # Check PREDICTION diversity: are all predictions similar?
                pred_self_sim = (pred_normalized @ pred_normalized.T)
                pred_self_sim_offdiag = pred_self_sim[~torch.eye(batch_size, dtype=torch.bool, device=pred_self_sim.device)].mean()

                # Store for timeline (used by debug_joint_predictor_weights)
                self._joint_separation = separation.item()

                logger.info(f"[JOINT_DEBUG] epoch={current_epoch} | "
                           f"input: norm={je_norm:.4f} std={je_std:.4f} | "
                           f"pred: norm={pred_norm:.4f} std={pred_std:.4f} | "
                           f"target: norm={target_norm:.4f} std={target_std:.4f} | "
                           f"SEPARATION={separation:.4f}")
                # Log diversity (self-similarity) - high values = collapsed
                logger.info(f"[JOINT_DEBUG] epoch={current_epoch} | DIVERSITY: "
                           f"input_self_sim={input_self_sim_offdiag:.4f} "
                           f"target_self_sim={target_self_sim_offdiag:.4f} "
                           f"pred_self_sim={pred_self_sim_offdiag:.4f} "
                           f"(1.0=collapsed, 0.0=orthogonal)")

                # Detailed similarity matrix analysis
                diag_sims = sim_matrix.diag()
                off_diag_mask = ~torch.eye(batch_size, dtype=torch.bool, device=sim_matrix.device)
                off_diag_sims = sim_matrix[off_diag_mask]

                # Per-row: is the diagonal the max in each row? (ideal = 100%)
                row_max_is_diag = (sim_matrix.argmax(dim=1) == torch.arange(batch_size, device=sim_matrix.device)).float().mean()

                logger.info(f"[JOINT_DEBUG] epoch={current_epoch} | SIM_MATRIX: "
                           f"diag={diag_sims.mean():.4f}±{diag_sims.std():.4f} "
                           f"off_diag={off_diag_sims.mean():.4f}±{off_diag_sims.std():.4f} "
                           f"correct_rank1={row_max_is_diag*100:.1f}%")

                # Compute and log the actual loss value
                temp_loss = self.infoNCE_loss(prediction, unmasked_encoding, temperature=temp)
                logger.info(f"[JOINT_DEBUG] epoch={current_epoch} | LOSS: "
                           f"joint_loss={temp_loss.mean().item():.4f} "
                           f"random_baseline={math.log(batch_size):.4f} "
                           f"(loss < baseline = learning)")

                # SANITY CHECK: What if we just used input directly (no predictor)?
                # This tests whether the task is even possible
                input_normalized = nn.functional.normalize(joint_encoding, dim=1)
                identity_sim = input_normalized @ target_normalized.T
                identity_diag = identity_sim.diag().mean()
                identity_offdiag = identity_sim[~torch.eye(batch_size, dtype=torch.bool, device=identity_sim.device)].mean()
                identity_rank1 = (identity_sim.argmax(dim=1) == torch.arange(batch_size, device=identity_sim.device)).float().mean()

                # Check if input and target are actually the same (they should be with 0% masking)
                input_target_diff = (joint_encoding - unmasked_encoding).abs().mean()
                input_eq_target = torch.allclose(joint_encoding, unmasked_encoding, atol=1e-5)

                logger.info(f"[JOINT_DEBUG] epoch={current_epoch} | IDENTITY_BASELINE: "
                           f"diag={identity_diag:.4f} off_diag={identity_offdiag:.4f} "
                           f"separation={identity_diag - identity_offdiag:.4f} rank1={identity_rank1*100:.1f}% "
                           f"input==target:{input_eq_target} diff={input_target_diff:.6f}")

        # ========================================================================
        # PER-BATCH RANK TRACKING: Collect rank1 and identity_diff for each batch
        # Aggregated at end of epoch by debug_joint_predictor_weights()
        # ========================================================================
        if not short:
            with torch.no_grad():
                # Initialize batch tracking for this epoch
                if not hasattr(self, '_rank_batch_epoch'):
                    self._rank_batch_epoch = -1
                    self._rank_batch_data = []

                # Reset on new epoch
                if self._rank_batch_epoch != current_epoch:
                    self._rank_batch_epoch = current_epoch
                    self._rank_batch_data = []

                # Compute rank1 and identity_diff for this batch
                pred_normalized = F.normalize(prediction, dim=1)
                target_normalized = F.normalize(unmasked_encoding, dim=1)

                # Similarity matrix for predictor output
                sim_matrix = pred_normalized @ target_normalized.T
                # rank1 = fraction where diagonal is max in each row
                pred_rank1 = (sim_matrix.argmax(dim=1) == torch.arange(batch_size, device=sim_matrix.device)).float().mean().item()

                # Identity baseline: input vs target similarity
                input_normalized = F.normalize(joint_encoding, dim=1)
                identity_sim = input_normalized @ target_normalized.T
                identity_rank1 = (identity_sim.argmax(dim=1) == torch.arange(batch_size, device=identity_sim.device)).float().mean().item()
                identity_diff = (joint_encoding - unmasked_encoding).abs().mean().item()

                # Store batch metrics
                self._rank_batch_data.append({
                    'pred_rank1': pred_rank1,
                    'identity_rank1': identity_rank1,
                    'identity_diff': identity_diff,
                })

        # CRITICAL: Pass temperature to infoNCE_loss
        base_loss = self.infoNCE_loss(prediction, unmasked_encoding, temperature=temp, return_logits=return_logits)

        if return_logits:
            base_loss, logits = base_loss

        # ANTI-COLLAPSE REGULARIZATION:
        # 1. Norm penalty: keep predictor output norms close to 1.0
        # 2. Diversity penalty: prevent all predictions from collapsing to same direction
        pred_norms = prediction.norm(dim=1)
        norm_penalty = ((pred_norms - 1.0) ** 2).mean()

        # Diversity: penalize high self-similarity (collapsed predictions)
        pred_normalized = F.normalize(prediction, dim=1)
        self_sim = pred_normalized @ pred_normalized.T
        # Exclude diagonal (self-similarity = 1.0 is expected)
        off_diag_mask = ~torch.eye(batch_size, dtype=torch.bool, device=self_sim.device)
        pred_self_sim = self_sim[off_diag_mask].mean()
        # We want pred_self_sim close to 0 (orthogonal), penalize high values
        diversity_penalty = pred_self_sim ** 2

        # Combine losses (small weights to not dominate main loss)
        total_loss = base_loss.mean() + 0.1 * norm_penalty + 0.1 * diversity_penalty

        # Log once per epoch
        if current_epoch != getattr(self, '_collapse_debug_epoch', -1):
            self._collapse_debug_epoch = current_epoch
            logger.info(f"[ANTI_COLLAPSE] epoch={current_epoch} | "
                       f"norm_penalty={norm_penalty:.4f} (mean_norm={pred_norms.mean():.2f}) "
                       f"diversity_penalty={diversity_penalty:.4f} (self_sim={pred_self_sim:.4f})")

        if return_logits:
            return total_loss, logits
        return total_loss

    def compute_total_loss(
        self,
        batch_size,
        #
        full_joint_encodings_unmasked,
        full_joint_encodings_1,
        full_joint_encodings_2,
        #
        full_column_encodings,
        short_column_encodings,
        #
        short_joint_encodings_unmasked,
        short_joint_encodings_1,
        short_joint_encodings_2,
        #
        mask_1,
        mask_2,
        #
        full_column_predictions_1,
        full_column_predictions_2,
        full_column_predictions_unmasked,
        #
        short_column_predictions_1,
        short_column_predictions_2,
        short_column_predictions_unmasked,
        #
        rows_skipped,  # Number of rows skipped from masking (not used in loss, but matches encoder output)
        #
        temp_multiplier=1.0,
        column_batches=None,  # Optional: raw token batches for reconstruction loss
    ):
        # Check if we should use the new modular loss framework
        if getattr(self.config.loss_config, 'use_loss_framework_v2', False):
            return self.compute_total_loss_v2(
                batch_size=batch_size,
                full_joint_encodings_unmasked=full_joint_encodings_unmasked,
                full_joint_encodings_1=full_joint_encodings_1,
                full_joint_encodings_2=full_joint_encodings_2,
                full_column_encodings=full_column_encodings,
                short_column_encodings=short_column_encodings,
                short_joint_encodings_unmasked=short_joint_encodings_unmasked,
                short_joint_encodings_1=short_joint_encodings_1,
                short_joint_encodings_2=short_joint_encodings_2,
                mask_1=mask_1,
                mask_2=mask_2,
                full_column_predictions_1=full_column_predictions_1,
                full_column_predictions_2=full_column_predictions_2,
                full_column_predictions_unmasked=full_column_predictions_unmasked,
                short_column_predictions_1=short_column_predictions_1,
                short_column_predictions_2=short_column_predictions_2,
                short_column_predictions_unmasked=short_column_predictions_unmasked,
                rows_skipped=rows_skipped,
                temp_multiplier=temp_multiplier,
                column_batches=column_batches,
            )

        # Get column_batches from stored value if not provided
        # (stored during forward() to avoid changing return signature)
        if column_batches is None:
            column_batches = getattr(self, '_last_column_batches', None)

        # MARGINAL LOSS
        (
            marginal_cpc_loss_1_total,
            marginal_cpc_loss_1_col_dict,
        ) = self.compute_marginal_infoNCE_loss(
            batch_size,
            full_column_predictions_1,
            full_column_encodings,
            mask_1,
            update_mi=True,
            column_batches=column_batches,  # Pass for reconstruction loss
        )
        (
            marginal_cpc_loss_2_total,
            marginal_cpc_loss_2_col_dict,
        ) = self.compute_marginal_infoNCE_loss(
            batch_size,
            full_column_predictions_2,
            full_column_encodings,
            mask_2,
            update_mi=True,
            column_batches=column_batches,  # Pass for reconstruction loss
        )
        # marginal_cpc_loss_unmasked = self.compute_marginal_infoNCE_loss(
        #     batch_size, full_column_predictions_unmasked, full_column_encodings, torch.ones_like(mask_2) * TokenStatus.OK,
        # )
        (
            short_marginal_cpc_loss_1_total,
            short_marginal_cpc_loss_1_col_dict,
        ) = self.compute_marginal_infoNCE_loss(
            batch_size, short_column_predictions_1, short_column_encodings, mask_1
        )
        (
            short_marginal_cpc_loss_2_total,
            short_marginal_cpc_loss_2_col_dict,
        ) = self.compute_marginal_infoNCE_loss(
            batch_size, short_column_predictions_2, short_column_encodings, mask_2
        )
        # short_marginal_cpc_loss_unmasked = self.compute_marginal_infoNCE_loss(
        #     batch_size, short_column_predictions_unmasked, short_column_encodings, torch.ones_like(mask_2) * TokenStatus.OK,
        # )

        # CRITICAL: Update relationship extractor with per-column losses (for importance calculation)
        # Average losses across all 4 views for more stable estimates
        # NOTE: Only update if training (not during validation/test)
        aggregated_col_losses = {}  # Initialize outside if block for anti-collapse loss calculation
        if self.training:
            try:
                for col_name in self.idx_to_col_name.values():
                    losses = []
                    if col_name in marginal_cpc_loss_1_col_dict:
                        loss_val = marginal_cpc_loss_1_col_dict[col_name]
                        if not (math.isnan(loss_val) or math.isinf(loss_val)):
                            losses.append(loss_val)
                    if col_name in marginal_cpc_loss_2_col_dict:
                        loss_val = marginal_cpc_loss_2_col_dict[col_name]
                        if not (math.isnan(loss_val) or math.isinf(loss_val)):
                            losses.append(loss_val)
                    if col_name in short_marginal_cpc_loss_1_col_dict:
                        loss_val = short_marginal_cpc_loss_1_col_dict[col_name]
                        if not (math.isnan(loss_val) or math.isinf(loss_val)):
                            losses.append(loss_val)
                    if col_name in short_marginal_cpc_loss_2_col_dict:
                        loss_val = short_marginal_cpc_loss_2_col_dict[col_name]
                        if not (math.isnan(loss_val) or math.isinf(loss_val)):
                            losses.append(loss_val)
                    
                    if losses:
                        aggregated_col_losses[col_name] = sum(losses) / len(losses)
                
                # Forward to joint encoder (which forwards to relationship extractor)
                # Only update if we have valid losses
                if aggregated_col_losses and hasattr(self.joint_encoder, 'update_column_losses'):
                    # Check if this was a NULL-only evaluation
                    relationship_extractor = getattr(self.joint_encoder, 'relationship_extractor', None)
                    is_null_baseline = (
                        relationship_extractor is not None and
                        getattr(relationship_extractor, '_null_evaluation_pending', False)
                    )

                    # DEBUG: Track NULL baseline evaluation frequency
                    if relationship_extractor is not None:
                        step = getattr(relationship_extractor, '_step_counter', 0)
                        if step % 50 == 0:
                            logger.info(f"[NULL_DEBUG] step={step} is_null_baseline={is_null_baseline} "
                                       f"pending={getattr(relationship_extractor, '_null_evaluation_pending', 'N/A')}")

                    self.joint_encoder.update_column_losses(aggregated_col_losses)
                    
                    # If NULL-only, update NULL baseline EMA
                    # Note: aggregated_col_losses already aggregates across all 4 masks
                    # (full_1, full_2, short_1, short_2), matching normal loss aggregation regime.
                    # This ensures NULL baseline and normal losses use the same masking/computation,
                    # preventing systematic bias in lift calculations.
                    # CRITICAL: Both NULL baseline and normal losses run in the same train/eval mode
                    # (inherited from encoder.training), ensuring consistent dropout/training semantics.
                    if is_null_baseline and relationship_extractor is not None:
                        logger.info(f"[NULL_DEBUG] Calling update_column_losses with is_null_baseline=True, "
                                   f"{len(aggregated_col_losses)} columns")
                        relationship_extractor.update_column_losses(aggregated_col_losses, is_null_baseline=True)
                        # Finalize after processing (aggregates and updates EMA)
                        relationship_extractor._finalize_null_baseline_batch()
                        logger.info(f"[NULL_DEBUG] After finalize: {len(relationship_extractor._null_baseline_ema)} cols have baseline")
            except Exception as e:
                # Don't break training if column loss update fails
                logger.warning(f"Failed to update column losses: {e}")

        # --- NEW: normalize over 4 views * number of active columns ---
        # each *_total is a SUM over columns of per-column mean InfoNCE.
        # we want an average over views and columns so the magnitude
        # is ~log(batch_size) instead of ~4 * n_cols * log(batch_size)
        # Count active columns in this batch (columns with at least one OK token)
        # This is more precise than using total n_cols when some columns are completely masked out
        n_cols_total = len(self.idx_to_col_name) if hasattr(self, "idx_to_col_name") else full_column_encodings.shape[1]
        
        # Count columns that have at least one OK token in any of the masks
        # mask_1 and mask_2 have shape (batch_size, n_cols)
        # A column is "active" if it has at least one OK token across all rows
        effective_n_cols = n_cols_total
        try:
            if mask_1 is not None and mask_2 is not None:
                # CRITICAL: Create OK value as tensor on same device
                ok_value = torch.tensor(TokenStatus.OK, device=mask_1.device, dtype=mask_1.dtype)
                # Check mask_1: columns with at least one OK token
                has_ok_mask1 = (mask_1 == ok_value).any(dim=0)  # (n_cols,)
                # Check mask_2: columns with at least one OK token
                has_ok_mask2 = (mask_2 == ok_value).any(dim=0)  # (n_cols,)
                # A column is active if it has OK tokens in either mask
                active_cols = (has_ok_mask1 | has_ok_mask2)
                effective_n_cols = active_cols.sum().item()
                # Ensure at least 1 column (safety check)
                if effective_n_cols == 0:
                    effective_n_cols = n_cols_total
        except Exception:
            # If counting fails for any reason, fall back to total columns
            effective_n_cols = n_cols_total
        
        # CRITICAL FIX: REMOVED MARGINAL LOSS NORMALIZER
        # The normalizer was dividing by 4*n_cols (e.g., 328 for 82 columns)
        # This divided GRADIENTS by 328 during backprop, preventing marginal loss from improving
        # Now we use raw loss and let the curriculum weight handle relative importance
        normalizer = 4.0 * max(1, effective_n_cols)  # Keep for logging/debugging

        # BALANCED MASK LOSS COMPUTATION
        # When masks are imbalanced (e.g., 2%/98%), the heavily-masked side produces
        # disproportionately large loss. Instead of adding both, use 2x the minimum
        # when either mask ratio falls below 40%.
        #
        # Calculate actual mask ratios (fraction of columns marked MARGINAL)
        marginal_value = torch.tensor(TokenStatus.MARGINAL, device=mask_1.device, dtype=mask_1.dtype)
        mask_1_ratio = (mask_1 == marginal_value).float().mean().item()
        mask_2_ratio = (mask_2 == marginal_value).float().mean().item()

        # Full predictor losses
        full_loss_1 = marginal_cpc_loss_1_total
        full_loss_2 = marginal_cpc_loss_2_total
        # Short predictor losses
        short_loss_1 = short_marginal_cpc_loss_1_total
        short_loss_2 = short_marginal_cpc_loss_2_total

        # Handle edge case: when one mask has essentially no signal (< 5% masked),
        # use only the mask that has meaningful signal. Otherwise, just sum both.
        # The curriculum will ramp up to balanced masks anyway.
        MASK_MINIMUM_THRESHOLD = 0.05  # Below this, one side has essentially no signal

        mask_1_too_low = mask_1_ratio < MASK_MINIMUM_THRESHOLD
        mask_2_too_low = mask_2_ratio < MASK_MINIMUM_THRESHOLD

        if mask_1_too_low and not mask_2_too_low:
            # Mask 1 has no signal, use mask 2 doubled to maintain gradient scale
            full_marginal = 2.0 * full_loss_2
            short_marginal = 2.0 * short_loss_2
            marginal_loss_raw = full_marginal + short_marginal
            balance_mode = "mask1_low_use_mask2"
        elif mask_2_too_low and not mask_1_too_low:
            # Mask 2 has no signal, use mask 1 doubled
            full_marginal = 2.0 * full_loss_1
            short_marginal = 2.0 * short_loss_1
            marginal_loss_raw = full_marginal + short_marginal
            balance_mode = "mask2_low_use_mask1"
        else:
            # Standard sum - both have signal (or both don't, which shouldn't happen)
            full_marginal = full_loss_1 + full_loss_2
            short_marginal = short_loss_1 + short_loss_2
            marginal_loss_raw = full_marginal + short_marginal
            balance_mode = "standard_sum"

        # Log when special handling is applied (once per epoch)
        _bal_epoch = getattr(self, '_current_epoch', 0)
        if not hasattr(self, '_balanced_loss_logged_epoch') or self._balanced_loss_logged_epoch != _bal_epoch:
            self._balanced_loss_logged_epoch = _bal_epoch
            if balance_mode != "standard_sum":
                logger.info(f"[BALANCED_LOSS] epoch={_bal_epoch} mask_ratios=({mask_1_ratio:.1%}, {mask_2_ratio:.1%}) "
                           f"mode={balance_mode}: full={full_marginal.item():.2f} short={short_marginal.item():.2f} "
                           f"(raw sum would be: full={full_loss_1.item()+full_loss_2.item():.2f} short={short_loss_1.item()+short_loss_2.item():.2f})")

        # NO NORMALIZATION - use raw loss (curriculum weight adjusted to compensate)
        marginal_loss = marginal_loss_raw
        
        # Store raw and normalizer in loss dict for debugging

        # marginal_loss = (
        #     marginal_cpc_loss_1_total
        #     + marginal_cpc_loss_2_total
        #     # + marginal_cpc_loss_unmasked
        #     + short_marginal_cpc_loss_1_total
        #     + short_marginal_cpc_loss_2_total
        #     # + short_marginal_cpc_loss_unmasked
        # )

        # COMPUTE SCALAR RECONSTRUCTION LOSS
        # For masked scalar columns, decode predictions and compare to actual values
        # This provides explicit training signal for numeric feature encoding
        reconstruction_loss = None
        reconstruction_col_losses = {}
        
        if self.training:
            reconstruction_losses = []
            
            # Only compute reconstruction for MARGINAL (masked) columns
            # mask_1 and mask_2 have shape (batch_size, n_cols)
            # CRITICAL: Create MARGINAL value as tensor on same device
            marginal_value = torch.tensor(TokenStatus.MARGINAL, device=mask_1.device, dtype=mask_1.dtype)
            prediction_mask_1 = mask_1 == marginal_value
            prediction_mask_2 = mask_2 == marginal_value
            
            # Iterate through encoders to find those with decoders
            for col_name, encoder in self.column_encoder.encoders.items():
                # Check if this encoder has reconstruction enabled
                if not (hasattr(encoder, 'enable_reconstruction') and 
                       encoder.enable_reconstruction and 
                       encoder.decoder is not None):
                    continue
                
                # Handle featrix_ prefix mismatch between encoder keys and column_order
                # The encoder dict keys sometimes have featrix_ prefix, but column_order doesn't
                actual_col_name = col_name
                if col_name not in self.column_order:
                    # Try without featrix_ prefix if it has one
                    if col_name.startswith("featrix_") and col_name[8:] in self.column_order:
                        actual_col_name = col_name[8:]
                    # Try with featrix_ prefix if it doesn't have one
                    elif f"featrix_{col_name}" in self.column_order:
                        actual_col_name = f"featrix_{col_name}"
                    else:
                        # Column not in column_order at all (e.g., synthetic columns)
                        continue
                
                # Get decoder from encoder
                decoder = encoder.decoder
                
                # Get column index using the actual name in column_order
                col_idx = self.column_order.index(actual_col_name)
                
                # Check if this column was masked in either mask
                col_mask_1 = prediction_mask_1[:, col_idx]  # (batch_size,)
                col_mask_2 = prediction_mask_2[:, col_idx]  # (batch_size,)
                
                # Get actual column encodings (ground truth)
                col_encoding = full_column_encodings[:, col_idx, :]  # (batch_size, d_model)
                
                # Get predictions for this column
                col_prediction_1 = full_column_predictions_1[col_idx]  # (batch_size, d_model)
                col_prediction_2 = full_column_predictions_2[col_idx]  # (batch_size, d_model)
                
                # Decode predictions to normalized values
                decoded_1 = decoder(col_prediction_1)  # (batch_size, 1)
                decoded_2 = decoder(col_prediction_2)  # (batch_size, 1)
                
                # Also decode actual encodings to get target values
                # This is more stable than trying to extract from tokenized batch
                with torch.no_grad():
                    target_normalized = decoder(col_encoding)  # (batch_size, 1)
                
                # Compute MSE loss only for masked positions
                # Initialize per-column losses for logging
                loss_1_val = None
                loss_2_val = None

                if col_mask_1.any():
                    masked_decoded_1 = decoded_1[col_mask_1]
                    masked_target_1 = target_normalized[col_mask_1]
                    # CRITICAL: Filter out NaN values
                    valid_1 = ~(torch.isnan(masked_decoded_1).any(dim=-1) | torch.isnan(masked_target_1).any(dim=-1))
                    if valid_1.sum() > 0:
                        loss_1 = F.mse_loss(masked_decoded_1[valid_1], masked_target_1[valid_1])
                        if not (torch.isnan(loss_1) or torch.isinf(loss_1)):
                            reconstruction_losses.append(loss_1)
                            loss_1_val = loss_1.detach().item()

                if col_mask_2.any():
                    masked_decoded_2 = decoded_2[col_mask_2]
                    masked_target_2 = target_normalized[col_mask_2]
                    # CRITICAL: Filter out NaN values
                    valid_2 = ~(torch.isnan(masked_decoded_2).any(dim=-1) | torch.isnan(masked_target_2).any(dim=-1))
                    if valid_2.sum() > 0:
                        loss_2 = F.mse_loss(masked_decoded_2[valid_2], masked_target_2[valid_2])
                        if not (torch.isnan(loss_2) or torch.isinf(loss_2)):
                            reconstruction_losses.append(loss_2)
                            loss_2_val = loss_2.detach().item()

                # Store per-column loss for logging
                col_loss_total = 0.0
                if loss_1_val is not None:
                    col_loss_total += loss_1_val
                if loss_2_val is not None:
                    col_loss_total += loss_2_val
                if col_loss_total > 0:
                    reconstruction_col_losses[col_name] = col_loss_total
            
            if reconstruction_losses:
                reconstruction_loss = sum(reconstruction_losses) / len(reconstruction_losses)
            else:
                reconstruction_loss = torch.tensor(0.0, device=marginal_loss.device, requires_grad=False)
        else:
            # Not training
            reconstruction_loss = torch.tensor(0.0, device=marginal_loss.device, requires_grad=False)

        # COMPUTRE JOINT LOSS
        # The mask for joint embedding_space loss is not necessary because there's
        # no NOT_PRESENT tokens to worry about because all tokens are guaranteed present
        # because we created the joint encodings ourselves.
        joint_loss_1 = self.compute_joint_infoNCE_loss(
            full_joint_encodings_1, full_joint_encodings_unmasked
        )
        joint_loss_2 = self.compute_joint_infoNCE_loss(
            full_joint_encodings_2, full_joint_encodings_unmasked
        )
        # Short predictor takes FULL joint encoding and predicts 3D short embedding
        # This allows using all available information to predict the 3D target
        short_joint_loss_1 = self.compute_joint_infoNCE_loss(
            full_joint_encodings_1,      # Input: full encoding (predictor compresses to 3D)
            short_joint_encodings_unmasked,  # Target: 3D short embedding
            short=True,
        )
        short_joint_loss_2 = self.compute_joint_infoNCE_loss(
            full_joint_encodings_2,      # Input: full encoding (predictor compresses to 3D)
            short_joint_encodings_unmasked,  # Target: 3D short embedding
            short=True,
        )
        joint_loss = (
            joint_loss_1 + joint_loss_2 + short_joint_loss_1 + short_joint_loss_2
        )
        
        # Capture logits from one of the joint losses for ranking metrics
        # Use the first full joint loss as representative (all should be similar)
        joint_logits_for_metrics = None
        try:
            _, joint_logits_for_metrics = self.compute_joint_infoNCE_loss(
                full_joint_encodings_1, full_joint_encodings_unmasked, return_logits=True
            )
        except Exception as e:
            logger.debug(f"Failed to capture joint logits for metrics: {e}")

        # COMPUTE SPREAD LOSS (optional, controlled by feature flag)
        # Check if spread loss is enabled
        enable_spread_loss = True
        try:
            from lib.featrix.neural.sphere_config import get_config
            spread_config = get_config()
            enable_spread_loss = spread_config.get_enable_spread_loss()
        except Exception:
            pass  # Default to enabled

        if enable_spread_loss:
            spread_loss_full_total, spread_loss_full_dict = self.compute_spread_loss(
                full_joint_encodings_unmasked,
                full_joint_encodings_1,
                full_joint_encodings_2,
                temp_multiplier=temp_multiplier
            )
            spread_loss_short_total, spread_loss_short_dict = self.compute_spread_loss(
                short_joint_encodings_unmasked,
                short_joint_encodings_1,
                short_joint_encodings_2,
                temp_multiplier=temp_multiplier
            )
            spread_loss = spread_loss_full_total + spread_loss_short_total
        else:
            # Spread loss disabled - set to 0
            spread_loss = torch.tensor(0.0, device=joint_loss.device, requires_grad=False)
            spread_loss_full_total = torch.tensor(0.0, device=joint_loss.device, requires_grad=False)
            spread_loss_short_total = torch.tensor(0.0, device=joint_loss.device, requires_grad=False)
            spread_loss_full_dict = {'total': 0.0, 'joint': 0.0, 'mask_1': 0.0, 'mask_2': 0.0}
            spread_loss_short_dict = {'total': 0.0, 'joint': 0.0, 'mask_1': 0.0, 'mask_2': 0.0}
            # Log once when disabled
            if not hasattr(self, '_spread_disabled_logged'):
                logger.info("📊 Spread loss DISABLED via feature flag (enable_spread_loss=False)")
                self._spread_disabled_logged = True

        # SHORT EMBEDDING UNIFORMITY LOSS
        # The learned short projection maps d_model -> 3 dimensions.
        # We add a uniformity loss that encourages short embeddings to spread
        # uniformly on the unit 2-sphere (surface of 3D ball).
        # This uses the log-sum-exp of pairwise distances (Wang & Isola 2020).
        short_uniformity_loss = torch.tensor(0.0, device=spread_loss.device)
        short_uniformity_weight = 2.0  # Increased from 0.5 - 3D embeddings need stronger regularization
        if self.training and short_joint_encodings_unmasked is not None:
            try:
                # Ensure normalized (should already be, but double-check)
                short_emb = F.normalize(short_joint_encodings_unmasked, dim=1)  # (B, 3)

                # Pairwise squared Euclidean distances
                # ||a - b||^2 = ||a||^2 + ||b||^2 - 2*a.b = 2 - 2*a.b (for unit vectors)
                pairwise_sim = short_emb @ short_emb.T  # (B, B)
                pairwise_dist_sq = 2.0 - 2.0 * pairwise_sim  # (B, B)

                # Uniformity loss: log of average exp(-t * dist^2) for t=2
                # Lower loss = more uniform distribution on sphere
                t = 2.0  # Temperature parameter

                # Mask out diagonal (self-similarity)
                B = pairwise_dist_sq.shape[0]
                mask = ~torch.eye(B, dtype=torch.bool, device=pairwise_dist_sq.device)
                pairwise_dist_sq_offdiag = pairwise_dist_sq[mask].view(B, B - 1)

                # Log-sum-exp for numerical stability
                short_uniformity_loss = torch.logsumexp(-t * pairwise_dist_sq_offdiag, dim=1).mean()

            except Exception as e:
                logger.debug(f"Failed to compute short uniformity loss: {e}")
                short_uniformity_loss = torch.tensor(0.0, device=spread_loss.device)

        # SHORT EMBEDDING ANTI-COLLAPSE LOSSES (modular, feature-flagged)
        # Uses loss_short_embedding.py for uniformity, diversity, and repulsion
        # Controlled by sphere_config: enable_short_uniformity_loss, enable_short_diversity_loss, enable_short_repulsion_loss
        short_embedding_loss = torch.tensor(0.0, device=spread_loss.device)
        short_embedding_loss_weight = 1.0  # Overall weight for combined short embedding loss
        short_diversity_dict = {}
        if self.training and short_joint_encodings_unmasked is not None:
            try:
                from featrix.neural.loss_short_embedding import compute_combined_short_embedding_loss
                short_embedding_loss, short_diversity_dict = compute_combined_short_embedding_loss(
                    short_joint_encodings_unmasked
                )

            except Exception as e:
                logger.debug(f"Failed to compute short embedding loss: {e}")
                short_embedding_loss = torch.tensor(0.0, device=spread_loss.device)

        # COVERAGE LOSS (128D) - push embeddings apart using cosine-based repulsion
        coverage_loss = torch.tensor(0.0, device=spread_loss.device)
        coverage_weight = 1.0  # Increase weight - 0.1 wasn't moving the needle
        coverage_metrics = {}
        d128_ratio = 0.0
        d128_mean_sim = 0.0
        d128_max_sim = 0.0
        if self.training and full_joint_encodings_unmasked is not None:
            try:
                from featrix.neural.loss_short_embedding import compute_coverage_loss
                coverage_loss, coverage_metrics = compute_coverage_loss(
                    full_joint_encodings_unmasked,
                )
                d128_ratio = coverage_metrics.get('diagonal_ratio', 0)
                d128_mean_sim = coverage_metrics.get('mean_cos_sim', 0)
                d128_max_sim = coverage_metrics.get('max_cos_sim', 0)
            except Exception as e:
                logger.debug(f"Failed to compute coverage loss: {e}")

        # Log bbox on one line
        if self.training and short_joint_encodings_unmasked is not None:
            d3_ratio = short_diversity_dict.get('spread', {}).get('diagonal_ratio', 0)
            cov_loss = coverage_loss.item() if isinstance(coverage_loss, torch.Tensor) else 0
            logger.info(f"📦 BBOX 3D ratio={d3_ratio:.2f} | 128D ratio={d128_ratio:.2f} mean_sim={d128_mean_sim:.3f} max_sim={d128_max_sim:.3f} cov_loss={cov_loss:.4f}")

        # EMBEDDING DIVERSITY LOSS (optional, controlled by feature flag)
        # Prevents embedding collapse by encouraging variance across dimensions
        diversity_loss = None
        diversity_dict = {}
        diversity_weight = 0.0

        # Check feature flag from sphere_config
        try:
            from featrix.neural.sphere_config import get_config
            sphere_config = get_config()
            enable_diversity = sphere_config.get_enable_embedding_diversity_loss()
            
            if enable_diversity and self.training:
                diversity_weight = sphere_config.get_embedding_diversity_weight()
                
                # Compute diversity loss on joint embeddings (unmasked view for stability)
                diversity_loss, diversity_dict = self.compute_diversity_loss(full_joint_encodings_unmasked)
                
                # Log diversity metrics periodically
                if not hasattr(self, '_diversity_log_counter'):
                    self._diversity_log_counter = 0
                if self._diversity_log_counter < 5:  # Log first 5 times
                    logger.info(f"📊 Diversity: mean_std={diversity_dict['mean_std']:.4f}, "
                               f"min_std={diversity_dict['min_std']:.4f}, "
                               f"target_std={diversity_dict['target_std']:.4f}, "
                               f"pct_below={diversity_dict['pct_below_target']:.1f}%, "
                               f"loss={diversity_loss.item():.4f}, weight={diversity_weight}")
                    self._diversity_log_counter += 1
            else:
                diversity_loss = torch.tensor(0.0, device=spread_loss.device, requires_grad=False)
                diversity_weight = 0.0
        except Exception as e:
            logger.debug(f"Failed to compute diversity loss: {e}")
            diversity_loss = torch.tensor(0.0, device=spread_loss.device, requires_grad=False)
            diversity_weight = 0.0

        # ============================================================================
        # SEPARATION LOSS: Directly penalize collapsed embeddings (high off-diagonal similarity)
        # ============================================================================
        # The diversity loss only checks per-dimension std. Embeddings can have good std
        # but still be highly correlated (pointing in similar directions). Separation loss
        # directly penalizes high pairwise similarity between different samples.
        #
        # separation = diag_sim - off_diag_sim (want high, ~0.3-0.5)
        # If off_diag_sim is high (>0.8), embeddings are collapsed even with good std.
        #
        # Weight schedule (from WeightTimeline):
        # - First 10% of epochs: high weight (5.0) for strong anti-collapse
        # - Then cosine decay to floor (0.5) to allow fine-tuning
        # ============================================================================
        separation_loss = torch.tensor(0.0, device=spread_loss.device, requires_grad=False)
        # Get separation weight from loss config (set by WeightTimeline warmup schedule)
        separation_weight = getattr(self.config.loss_config, 'separation_weight', 1.0)
        separation_dict = {}

        try:
            # Use unmasked joint embeddings (the actual row representations)
            embeddings = full_joint_encodings_unmasked  # (batch_size, d_model)

            # Normalize for cosine similarity
            emb_normalized = F.normalize(embeddings, dim=1)

            # Compute pairwise cosine similarity
            sim_matrix = emb_normalized @ emb_normalized.T  # (batch_size, batch_size)

            # Diagonal = self-similarity (always 1.0 for normalized vectors)
            # Off-diagonal = similarity between different samples (want low, ~0.0)
            off_diag_mask = ~torch.eye(batch_size, dtype=torch.bool, device=sim_matrix.device)
            off_diag_sim = sim_matrix[off_diag_mask]

            # Mean off-diagonal similarity (0.0 = orthogonal, 1.0 = identical)
            mean_off_diag = off_diag_sim.mean()

            # Separation loss: penalize high off-diagonal similarity
            # We want mean_off_diag close to 0, so loss = mean_off_diag^2
            # Using squared loss to penalize high values more aggressively
            separation_loss = mean_off_diag ** 2

            # Also compute separation for diagnostics
            diag_sim = sim_matrix.diag().mean()
            separation_value = diag_sim - mean_off_diag

            separation_dict = {
                'mean_off_diag_sim': mean_off_diag.item(),
                'separation': separation_value.item(),
                'loss': separation_loss.item(),
            }

            # Log once per epoch
            if not hasattr(self, '_separation_log_epoch'):
                self._separation_log_epoch = -1
            current_epoch = getattr(self, '_current_epoch', 0)
            if current_epoch != self._separation_log_epoch:
                self._separation_log_epoch = current_epoch
                status = "✅" if mean_off_diag.item() < 0.3 else ("⚠️" if mean_off_diag.item() < 0.6 else "❌")
                logger.info(f"📏 SEPARATION LOSS [e={current_epoch}]: "
                           f"off_diag_sim={mean_off_diag.item():.4f} {status} "
                           f"separation={separation_value.item():.4f} "
                           f"loss={separation_loss.item():.6f} "
                           f"weight={separation_weight:.2f}")

        except Exception as e:
            logger.debug(f"Failed to compute separation loss: {e}")
            separation_loss = torch.tensor(0.0, device=spread_loss.device, requires_grad=False)

        # Compute a "mutual information-like" joint score for the two masks.
        # This measures how well we can predict joint representations, not true MI.
        # Formula: predictability = (log(N) - loss) / log(N) * 100
        # - 0% = random baseline (loss = log(N))
        # - 100% = perfect prediction (loss = 0)
        # - Negative = worse than random (clamped to 0 for display)
        #
        # NOTE: Temperature scaling is already applied in compute_joint_infoNCE_loss(),
        # so the joint_loss values are computed with the correct temperature. The theoretical
        # maximum log(N) is temperature-independent (random baseline is always log(N)).
        log_n = math.log(batch_size)

        # Compute percentage predictability (0-100 scale, same as column MI)
        # Use the BEST (lowest loss) of the FULL joint losses only
        # Short losses excluded: 3D embeddings can't distinguish 200 samples (loss ~10 vs log(200)=5.3)
        joint_loss_1_val = joint_loss_1.detach().item()
        joint_loss_2_val = joint_loss_2.detach().item()

        # Best = minimum of full losses only
        best_joint_loss = min(joint_loss_1_val, joint_loss_2_val)

        # Use best full loss for predictability
        best_predictability_pct = ((log_n - best_joint_loss) / log_n) * 100 if log_n > 0 else 0

        # DEBUG: Log joint losses once per epoch (every 4 batches for typical 4-batch epochs)
        if not hasattr(self, '_joint_loss_debug_count'):
            self._joint_loss_debug_count = 0
        self._joint_loss_debug_count += 1
        if self._joint_loss_debug_count % 4 == 1:  # Log first batch of each epoch
            short_joint_loss_1_val = short_joint_loss_1.detach().item()
            short_joint_loss_2_val = short_joint_loss_2.detach().item()
            logger.info(f"🔍 Joint loss: full=[{joint_loss_1_val:.4f}, {joint_loss_2_val:.4f}], "
                       f"short=[{short_joint_loss_1_val:.4f}, {short_joint_loss_2_val:.4f}], "
                       f"best={best_joint_loss:.4f}, log(N)={log_n:.4f}, pred={best_predictability_pct:.1f}%")

        # Clamp to 0-100% range (negative values mean worse than random, show as 0%)
        best_predictability_pct = max(0, min(100, best_predictability_pct))

        # Update joint MI with best predictability (single update, not 2)
        self.update_joint_mi(best_predictability_pct)

        # Collect entropy regularization losses from adaptive encoders
        # This encourages sharper strategy selection (one strategy dominates)
        entropy_regularization_loss = None
        if self.training:
            entropy_losses = []
            for col_name, encoder in self.column_encoder.encoders.items():
                if hasattr(encoder, '_current_entropy_loss'):
                    entropy_loss = encoder._current_entropy_loss
                    if entropy_loss is not None and entropy_loss.requires_grad:
                        entropy_losses.append(entropy_loss)
            
            if entropy_losses:
                # Sum all entropy losses from adaptive encoders
                entropy_regularization_loss = sum(entropy_losses)
            else:
                # No entropy losses - create zero tensor on correct device
                entropy_regularization_loss = torch.tensor(0.0, device=joint_loss.device, requires_grad=False)
        else:
            # Not training - no entropy regularization
            entropy_regularization_loss = torch.tensor(0.0, device=joint_loss.device, requires_grad=False)

        loss_config = self.config.loss_config
        # CRITICAL: NO SCALING COEFFICIENT - marginal weight handles relative importance
        # The scaling coefficient was multiplying by ~0.017 (another 60× reduction!)
        # Combined with the old /normalizer, marginal gradients were 20,000× too small!
        # Now we use raw marginal loss and let the curriculum weight (0.005-0.03) handle it
        marginal_loss_scaled = marginal_loss  # No scaling - use raw loss
        
        # Add entropy regularization to encourage sharper strategy selection
        # Weight it relatively low (0.01) so it guides but doesn't dominate
        entropy_weight = 0.01
        
        # Add scalar reconstruction loss weight
        # Start low (0.05) to guide without dominating - can be increased if needed
        reconstruction_weight = getattr(loss_config, 'reconstruction_loss_weight', 0.05)
        
        # ANTI-COLLAPSE DIVERSITY FLOOR: Prevent column loss equalization
        # When column losses collapse to near-constant, the model stops differentiating
        # "what's hard" vs "what's easy", making relationship ranking signal junk.
        # This term rewards spread in per-column losses (variance above minimum threshold).
        # 
        # NOTE: We compute this from aggregated_col_losses which are detached floats.
        # While this doesn't provide direct gradients, the penalty encourages the model
        # to maintain diversity in per-column losses through the overall loss signal.
        # The gradients still flow through the marginal_loss computation itself.
        anti_collapse_loss = None
        if self.training and aggregated_col_losses and len(aggregated_col_losses) > 1:
            # Compute std from aggregated values (detached, but still informative)
            col_loss_values_list = list(aggregated_col_losses.values())
            col_loss_mean = sum(col_loss_values_list) / len(col_loss_values_list)
            col_loss_var = sum((v - col_loss_mean) ** 2 for v in col_loss_values_list) / len(col_loss_values_list)
            col_loss_std = math.sqrt(col_loss_var + 1e-8)  # Add small epsilon for numerical stability
            
            # Target minimum std: 0.1 early training, anneal down to 0.01 later
            # This ensures columns maintain meaningful differentiation
            # We track epoch via a simple counter (approximate)
            if not hasattr(self, '_anti_collapse_epoch_counter'):
                self._anti_collapse_epoch_counter = 0
            self._anti_collapse_epoch_counter += 1
            
            # Anneal threshold: 0.1 → 0.01 over ~100 epochs
            # Use a simple linear decay (can be made more sophisticated)
            progress = min(1.0, self._anti_collapse_epoch_counter / 100.0)
            target_std = 0.1 * (1.0 - progress) + 0.01 * progress
            
            # Penalty: max(0, target_std - actual_std)^2
            # This encourages std to stay above target_std
            # Convert to tensor for loss computation (no gradients, but adds to loss signal)
            std_deficit = target_std - col_loss_std
            if std_deficit > 0:
                anti_collapse_loss = torch.tensor(
                    (std_deficit ** 2),
                    device=marginal_loss.device,
                    dtype=marginal_loss.dtype,
                    requires_grad=False  # No direct gradients, but loss signal still guides training
                )
            else:
                anti_collapse_loss = torch.tensor(0.0, device=marginal_loss.device, requires_grad=False)
            
            # Weight: start at 0.1, can be tuned
            # This should be strong enough to prevent collapse but not dominate other losses
            anti_collapse_weight = 0.1
        else:
            anti_collapse_loss = torch.tensor(0.0, device=marginal_loss.device, requires_grad=False)
            anti_collapse_weight = 0.0

        # =================================================================
        # VICReg-style PER-COLUMN VARIANCE + COVARIANCE PENALTY
        # Prevents individual column encodings from collapsing to constant vectors
        # This is critical because the diversity penalty on joint embeddings doesn't
        # prevent individual scalar codecs from collapsing (other columns can carry variance)
        #
        # Two components:
        # 1. VARIANCE: std(E[:,k]) >= target_std for each dimension k
        # 2. COVARIANCE: Decorrelate dimensions (off-diagonal covariance -> 0)
        # =================================================================
        column_variance_loss = torch.tensor(0.0, device=marginal_loss.device)
        column_covariance_loss = torch.tensor(0.0, device=marginal_loss.device)
        column_variance_weight = 0.5  # Increased from 0.1 - scalar collapse is severe
        column_covariance_weight = 0.1  # Decorrelation weight
        if self.training and full_column_encodings is not None:
            # full_column_encodings: (B, n_cols, d_model)
            B, n_cols, d_model = full_column_encodings.shape
            if B > 1:
                # VICReg variance term: std(E[:,k]) >= target_std for each dimension k
                # Use lower target_std since embeddings may be normalized
                target_std = 0.5  # Reduced from 1.0 - more realistic for normalized embeddings
                gamma = 1.0  # VICReg gamma parameter

                # Compute per-column penalties
                col_var_penalties = []
                col_cov_penalties = []
                col_avg_cos_list = []  # Track collapse metric

                for c in range(n_cols):
                    col_emb = full_column_encodings[:, c, :]  # (B, d_model)

                    # VARIANCE: Std over batch for each dimension
                    col_std = col_emb.std(dim=0)  # (d_model,)
                    std_deficit = F.relu(target_std - col_std)
                    col_var_penalties.append((std_deficit ** 2).mean())

                    # COVARIANCE: Off-diagonal covariance penalty
                    # Center the embeddings
                    col_emb_centered = col_emb - col_emb.mean(dim=0, keepdim=True)
                    # Covariance matrix: (d_model, d_model)
                    cov = (col_emb_centered.T @ col_emb_centered) / (B - 1)
                    # Off-diagonal penalty (squared, to penalize large covariances)
                    off_diag_mask = ~torch.eye(d_model, dtype=torch.bool, device=cov.device)
                    off_diag_cov = cov[off_diag_mask]
                    col_cov_penalties.append((off_diag_cov ** 2).mean())

                    # Track avg pairwise cosine for logging
                    col_emb_norm = F.normalize(col_emb, dim=1)
                    sim_matrix = col_emb_norm @ col_emb_norm.T
                    batch_off_diag = ~torch.eye(B, dtype=torch.bool, device=sim_matrix.device)
                    avg_cos = sim_matrix[batch_off_diag].mean().item()
                    col_avg_cos_list.append(avg_cos)

                if col_var_penalties:
                    column_variance_loss = gamma * torch.stack(col_var_penalties).mean()
                if col_cov_penalties:
                    column_covariance_loss = torch.stack(col_cov_penalties).mean()

                # Log detailed per-column collapse metrics (first batch per epoch)
                if not hasattr(self, '_var_loss_log_count'):
                    self._var_loss_log_count = 0
                self._var_loss_log_count += 1

                # Log every epoch (first batch) + first 3 batches
                should_log = (self._var_loss_log_count <= 3) or (self._var_loss_log_count % (n_cols * 10) < 1)
                if should_log and col_avg_cos_list:
                    # Find worst (highest avg_cos) columns
                    cos_with_idx = [(cos, i) for i, cos in enumerate(col_avg_cos_list)]
                    cos_with_idx.sort(reverse=True)
                    worst_3 = cos_with_idx[:3]
                    col_names = list(self.column_order) if hasattr(self, 'column_order') else [str(i) for i in range(n_cols)]
                    worst_info = [f"{col_names[i]}={cos:.3f}" for cos, i in worst_3]
                    mean_cos = sum(col_avg_cos_list) / len(col_avg_cos_list)
                    logger.info(f"📊 PER-COLUMN COLLAPSE: mean_avg_cos={mean_cos:.3f}, worst: {', '.join(worst_info)}")
                    logger.info(f"   VICReg losses: var={column_variance_loss.item():.4f} (w={column_variance_weight}), "
                               f"cov={column_covariance_loss.item():.4f} (w={column_covariance_weight})")

        # DEBUG: Log loss components on first few batches (simplified, readable format)
        if not hasattr(self, '_loss_debug_counter'):
            self._loss_debug_counter = 0

        total = (
            loss_config.joint_loss_weight * joint_loss
            + loss_config.marginal_loss_weight * marginal_loss_scaled
            + loss_config.spread_loss_weight * spread_loss
            + diversity_weight * diversity_loss
            + separation_weight * separation_loss  # Direct anti-collapse: penalize high pairwise similarity
            + entropy_weight * entropy_regularization_loss
            + reconstruction_weight * reconstruction_loss
            + anti_collapse_weight * anti_collapse_loss
            + short_uniformity_weight * short_uniformity_loss  # 3D sphere uniformity (legacy, still used)
            + short_embedding_loss_weight * short_embedding_loss  # 3D anti-collapse (combined: uniformity + diversity + repulsion)
            + coverage_weight * coverage_loss  # 128D hypersphere coverage
            + column_variance_weight * column_variance_loss  # Per-column variance (VICReg-style)
            + column_covariance_weight * column_covariance_loss  # Per-column covariance (VICReg-style decorrelation)
        )

        # CRITICAL: Final NaN check - if total is NaN, use a safe fallback loss
        # This prevents catastrophic gradient corruption from any remaining edge cases
        if torch.isnan(total) or torch.isinf(total):
            logger.warning(f"⚠️  Total loss is NaN/Inf (spread={spread_loss.item()}, joint={joint_loss.item()}, "
                          f"marginal={marginal_loss_scaled.item()}) - using spread loss only as fallback")
            total = loss_config.spread_loss_weight * spread_loss

        # Only log loss breakdown for first batch of first epoch (minimal verbosity)
        if self._loss_debug_counter < 1:
            batch_num = getattr(self, '_debug_mps_batch_count', 0)
            spread_val = (loss_config.spread_loss_weight * spread_loss).item()
            joint_val = (loss_config.joint_loss_weight * joint_loss).item()
            marginal_val = (loss_config.marginal_loss_weight * marginal_loss_scaled).item()
            recon_val = (reconstruction_weight * reconstruction_loss).item()
            total_val = total.item()
            
            # Single compact line showing only essential info
            logger.info(f"📊 Loss (b={batch_num}): spread={spread_val:.1f}  joint={joint_val:.1f}  marginal={marginal_val:.1f}  recon={recon_val:.3f}  → total={total_val:.1f}")
            self._loss_debug_counter += 1

        # COLLAPSE DIAGNOSTICS: Compute metrics to distinguish real collapse from metric artifacts
        collapse_diagnostics = {}
        if self.training:
            try:
                # 1. Joint embedding norms and std
                # Compute ||joint embedding|| for each sample
                joint_norms = torch.norm(full_joint_encodings_unmasked, dim=1)  # (batch_size,)
                joint_norm_mean = joint_norms.mean().item()
                joint_norm_std = joint_norms.std().item()
                
                # Compute std of joint embeddings per dimension
                joint_std_per_dim = full_joint_encodings_unmasked.std(dim=0)  # (d_model,)
                joint_std_mean = joint_std_per_dim.mean().item()
                joint_std_std = joint_std_per_dim.std().item()
                
                collapse_diagnostics['joint_embedding'] = {
                    'norm_mean': joint_norm_mean,
                    'norm_std': joint_norm_std,
                    'std_per_dim_mean': joint_std_mean,
                    'std_per_dim_std': joint_std_std,
                    'std_per_dim_full': joint_std_per_dim.detach().cpu().tolist(),  # Full (d_model,) for heatmap
                }
                
                # 2. Mask entropy (entropy of masking distribution)
                # Compute entropy of mask distribution: how uniform/random is the masking?
                # For each mask, compute the fraction of MARGINAL tokens per column
                if mask_1 is not None and mask_2 is not None:
                    # Count MARGINAL tokens per column across batch
                    # CRITICAL: Create MARGINAL value as tensor on same device
                    marginal_value = torch.tensor(TokenStatus.MARGINAL, device=mask_1.device, dtype=mask_1.dtype)
                    mask_1_marginal = (mask_1 == marginal_value).float()  # (batch_size, n_cols)
                    mask_2_marginal = (mask_2 == marginal_value).float()
                    
                    # Average masking probability per column (across batch)
                    mask_1_probs = mask_1_marginal.mean(dim=0)  # (n_cols,)
                    mask_2_probs = mask_2_marginal.mean(dim=0)
                    
                    # Compute entropy: H = -sum(p * log(p) + (1-p) * log(1-p))
                    # High entropy = uniform masking (good), low entropy = biased masking (bad)
                    eps = 1e-10
                    mask_1_entropy = -(mask_1_probs * torch.log(mask_1_probs + eps) + 
                                      (1 - mask_1_probs) * torch.log(1 - mask_1_probs + eps)).mean().item()
                    mask_2_entropy = -(mask_2_probs * torch.log(mask_2_probs + eps) + 
                                      (1 - mask_2_probs) * torch.log(1 - mask_2_probs + eps)).mean().item()
                    
                    collapse_diagnostics['mask_entropy'] = {
                        'mask_1': mask_1_entropy,
                        'mask_2': mask_2_entropy,
                        'mean': (mask_1_entropy + mask_2_entropy) / 2.0,
                    }
                
                # 3. Logit distribution per column (from marginal predictions)
                # Compute logits from marginal predictions for a sample of columns
                # This shows if predictions are collapsing to similar values
                if aggregated_col_losses and len(aggregated_col_losses) > 0:
                    # Sample a few columns to compute logit stats
                    sample_cols = list(aggregated_col_losses.keys())[:min(5, len(aggregated_col_losses))]
                    logit_stats_per_col = {}
                    
                    for col_idx, col_name in enumerate(self.idx_to_col_name.values()):
                        if col_name not in sample_cols:
                            continue
                        
                        # Get predictions and targets for this column from one of the masks
                        # Use mask_1 predictions as sample
                        if col_idx < len(full_column_predictions_1):
                            col_pred = full_column_predictions_1[col_idx]  # (batch_size, d_model)
                            col_target = full_column_encodings[:, col_idx, :]  # (batch_size, d_model)
                            
                            # Normalize for logit computation
                            col_pred_norm = F.normalize(col_pred, dim=1)
                            col_target_norm = F.normalize(col_target, dim=1)
                            
                            # Compute logits (similarity matrix)
                            temperature = self._compute_adaptive_temperature(batch_size)
                            logits = col_pred_norm @ col_target_norm.T / temperature  # (batch_size, batch_size)
                            
                            # Get diagonal (correct predictions) and off-diagonal (negatives)
                            logits_diag = logits.diag()  # (batch_size,)
                            # Get off-diagonal (sample a subset to avoid O(n²))
                            mask_off_diag = ~torch.eye(batch_size, dtype=torch.bool, device=logits.device)
                            logits_off_diag = logits[mask_off_diag]
                            if len(logits_off_diag) > 1000:
                                logits_off_diag = logits_off_diag[::len(logits_off_diag)//1000]  # Sample
                            
                            logit_stats_per_col[col_name] = {
                                'diag_mean': logits_diag.mean().item(),
                                'diag_std': logits_diag.std().item(),
                                'off_diag_mean': logits_off_diag.mean().item(),
                                'off_diag_std': logits_off_diag.std().item(),
                                'separation': (logits_diag.mean() - logits_off_diag.mean()).item(),  # Higher = better separation
                            }
                    
                    collapse_diagnostics['logit_distribution'] = logit_stats_per_col
                    
            except Exception as e:
                # Don't break training if diagnostics fail
                logger.debug(f"Failed to compute collapse diagnostics: {e}")
                collapse_diagnostics = {'error': str(e)}
        
        # Compute ranking metrics from joint loss logits
        ranking_metrics = None
        if joint_logits_for_metrics is not None:
            try:
                with torch.no_grad():
                    ranking_metrics = compute_ranking_metrics(joint_logits_for_metrics)
                    collapse_diagnostics['ranking_metrics'] = ranking_metrics
            except Exception as e:
                logger.debug(f"Failed to compute ranking metrics: {e}")
                # Don't fail if ranking metrics computation fails
        
        loss_dict = {
            "total": total.item(),
            "batch_size": batch_size,
            "collapse_diagnostics": collapse_diagnostics,
            "reconstruction_loss": {
                "total": reconstruction_loss.item() if hasattr(reconstruction_loss, 'item') else 0.0,
                "cols": reconstruction_col_losses,
            },
            "entropy_regularization": {
                "total": entropy_regularization_loss.item() if hasattr(entropy_regularization_loss, 'item') else 0.0,
            },
            "diversity_loss": {
                "total": diversity_loss.item() if hasattr(diversity_loss, 'item') else 0.0,
                "weight": diversity_weight,
                "enabled": diversity_weight > 0,
                **diversity_dict,
            },
            "spread_loss": {
                "total": spread_loss.item(),
                "full": {
                    "total": spread_loss_full_total.item(),
                    **spread_loss_full_dict,
                },
                "short": {
                    "total": spread_loss_short_total.item(),
                    **spread_loss_short_dict,
                },
            },
            "short_uniformity_loss": {
                "total": short_uniformity_loss.item() if hasattr(short_uniformity_loss, 'item') else 0.0,
                "weight": short_uniformity_weight,
            },
            "short_embedding_loss": {
                "total": short_embedding_loss.item() if hasattr(short_embedding_loss, 'item') else 0.0,
                "weight": short_embedding_loss_weight,
                **short_diversity_dict,  # Contains uniformity, diversity, repulsion components
            },
            "metric_loss": {
                # Metric learning loss: teaches |embed(x) - embed(y)| ∝ |x - y| for scalars
                # Extracted from marginal loss col_dict where it's computed
                "total": marginal_cpc_loss_1_col_dict.get('__featrix_metric_total', 0.0),
                "weight": 1.0,  # Currently hardcoded in compute_marginal_infoNCE_loss
            },
            "separation_loss": {
                # Separation loss: penalizes high off-diagonal cosine similarity (collapse)
                "total": separation_loss.item() if hasattr(separation_loss, 'item') else 0.0,
                "weight": separation_weight,
                **separation_dict,  # Contains mean_off_diag_sim, separation value
            },
            "joint_loss": {
                "total": joint_loss.item(),
                "joint_loss_full_1": joint_loss_1.item(),
                "joint_loss_full_2": joint_loss_2.item(),
                "joint_loss_short_1": short_joint_loss_1.item(),
                "joint_loss_short_2": short_joint_loss_2.item(),
            },
            "marginal_loss": {
                "total": marginal_loss.item(),
                "raw": marginal_loss_raw.item(),  # Before normalization
                "normalizer": normalizer,  # Divisor used for normalization
                "marginal_loss_full_1": {
                    "total": marginal_cpc_loss_1_total.item(),
                    "cols": marginal_cpc_loss_1_col_dict,
                },
                "marginal_loss_full_2": {
                    "total": marginal_cpc_loss_2_total.item(),
                    "cols": marginal_cpc_loss_2_col_dict,
                },
                "marginal_loss_short_1": {
                    "total": short_marginal_cpc_loss_1_total.item(),
                    "cols": short_marginal_cpc_loss_1_col_dict,
                },
                "marginal_loss_short_2": {
                    "total": short_marginal_cpc_loss_2_total.item(),
                    "cols": short_marginal_cpc_loss_2_col_dict,
                },
            },
        }

        return total, loss_dict

    def compute_total_loss_v2(
        self,
        batch_size,
        full_joint_encodings_unmasked,
        full_joint_encodings_1,
        full_joint_encodings_2,
        full_column_encodings,
        short_column_encodings,
        short_joint_encodings_unmasked,
        short_joint_encodings_1,
        short_joint_encodings_2,
        mask_1,
        mask_2,
        full_column_predictions_1,
        full_column_predictions_2,
        full_column_predictions_unmasked,
        short_column_predictions_1,
        short_column_predictions_2,
        short_column_predictions_unmasked,
        rows_skipped,
        temp_multiplier=1.0,
        column_batches=None,
    ):
        """
        Simplified loss computation using the new LossFramework.

        This is a cleaner alternative to compute_total_loss that uses
        the modular loss framework for easier experimentation.
        """
        # Initialize framework on first call
        if not hasattr(self, '_loss_framework'):
            loss_version = getattr(self.config.loss_config, 'loss_functions_version', None)

            if loss_version:
                # Use versioned loss functions from loss_functions/ directory
                try:
                    import importlib
                    loss_module = importlib.import_module(f"featrix.neural.loss_functions.{loss_version}")
                    self._loss_framework = loss_module.create_default_framework()
                    logger.info(f"Initialized LossFramework from {loss_version}")
                except ImportError as e:
                    logger.warning(f"Could not import {loss_version}: {e}. Falling back to default.")
                    from featrix.neural.loss_framework import (
                        DualEmbeddingLossFramework,
                        DualFrameworkConfig
                    )
                    self._loss_framework = DualEmbeddingLossFramework(DualFrameworkConfig.default())
                    logger.info("Initialized DualEmbeddingLossFramework (default)")
            else:
                # Use default loss framework
                from featrix.neural.loss_framework import (
                    DualEmbeddingLossFramework,
                    DualFrameworkConfig
                )
                self._loss_framework = DualEmbeddingLossFramework(DualFrameworkConfig.default())
                logger.info("Initialized DualEmbeddingLossFramework (default)")

        # Update curriculum (cosine→InfoNCE blend) based on current epoch
        current_epoch = getattr(self, '_current_epoch', 0)
        total_epochs = getattr(self, '_total_epochs', 25)  # Default if not set
        self._loss_framework.set_epoch(current_epoch, total_epochs)

        # Stack column predictions from list to 3D tensor (B, n_cols, D)
        # full_column_predictions_1 is a list of (B, D) tensors
        stacked_predictions = torch.stack(full_column_predictions_1, dim=1) if full_column_predictions_1 else None

        # CRITICAL: Pass embeddings through predictors before computing loss
        # The joint_predictor learns to transform masked embeddings to match unmasked targets.
        # Without this, the predictors have NO GRADIENTS and don't learn!
        #
        # The contrastive task is: joint_predictor(masked_embedding) should match unmasked_embedding
        # This trains BOTH the encoder (to produce useful embeddings) AND the predictor (to transform them)
        full_predictions_1 = self.joint_predictor(full_joint_encodings_1)
        full_predictions_2 = self.joint_predictor(full_joint_encodings_2)

        # DIAGNOSTIC: Check if masked and unmasked embeddings are actually different
        # If training=False (eval mode) or zero_masking, they might be identical
        current_batch = getattr(self, '_batch_counter', 0)
        if current_batch == 0:  # Log once per epoch (first batch)
            with torch.no_grad():
                # Check raw encoder outputs (before predictor)
                enc_diff = (full_joint_encodings_1 - full_joint_encodings_unmasked).abs().mean().item()
                enc1_vs_enc2 = (full_joint_encodings_1 - full_joint_encodings_2).abs().mean().item()
                # Check predictor outputs
                pred1_norm = F.normalize(full_predictions_1, dim=1, eps=1e-8)
                unmasked_norm = F.normalize(full_joint_encodings_unmasked, dim=1, eps=1e-8)
                pred_vs_target_sim = (pred1_norm * unmasked_norm).sum(dim=1).mean().item()
                # Check if training or eval mode
                is_training = self.training
                logger.info(f"🔬 CONTRASTIVE DIAGNOSTIC [epoch={current_epoch}, training={is_training}]:")
                logger.info(f"   Raw encoder: masked_1 vs unmasked diff={enc_diff:.6f}, masked_1 vs masked_2 diff={enc1_vs_enc2:.6f}")
                logger.info(f"   Predictor output vs target: cosine_sim={pred_vs_target_sim:.4f}")
                if enc_diff < 1e-6:
                    logger.warning(f"   ⚠️  MASKED AND UNMASKED ARE IDENTICAL! (zero_masking or bug)")

        # Short predictor: full joint encoding -> 3D short embedding target
        short_predictions_1 = self.joint_predictor_short(full_joint_encodings_1)
        short_predictions_2 = self.joint_predictor_short(full_joint_encodings_2)

        # Compute loss using framework
        # Pass PREDICTED embeddings (through joint_predictor) so gradients flow to predictors
        total_loss, framework_metrics = self._loss_framework.compute_total(
            full_embeddings_1=full_predictions_1,  # predicted masked view 1
            full_embeddings_2=full_predictions_2,  # predicted masked view 2
            full_embeddings_unmasked=full_joint_encodings_unmasked,  # target (unmasked, no predictor)
            short_embeddings_1=short_predictions_1,  # predicted short view 1
            short_embeddings_2=short_predictions_2,  # predicted short view 2
            short_embeddings_unmasked=short_joint_encodings_unmasked,  # target (unmasked short)
            # Column prediction inputs (for marginal loss)
            column_predictions=stacked_predictions,  # (B, n_cols, D)
            column_targets=full_column_encodings,  # (B, n_cols, D)
            # CRITICAL: Pass mask so marginal loss only computes on MASKED columns
            # Without this, the loss is diluted by easy unmasked column predictions
            column_mask=mask_1,  # (B, n_cols) - TokenStatus mask indicating which columns are masked
        )

        # Log detailed metrics (pos_sim, neg_sim, mean_cosine, n_masked) periodically
        # The full_framework has the detailed component metrics
        current_batch = getattr(self, '_batch_counter', 0)
        self._batch_counter = current_batch + 1
        current_epoch = getattr(self, '_current_epoch', 0)

        # Log once per epoch (first batch) - detailed marginal prediction diagnostics
        if current_batch == 0 or (current_batch % 50 == 0):
            full_metrics = framework_metrics.get("full", {})
            if full_metrics:
                self._loss_framework.full_framework._log_batch_metrics(full_metrics)

            # Additional marginal prediction diagnostics (like legacy compute_marginal_infoNCE_loss)
            if stacked_predictions is not None and full_column_encodings is not None:
                with torch.no_grad():
                    # Compute pred-target cosine similarity
                    pred_norm = F.normalize(stacked_predictions, dim=-1)  # (B, n_cols, D)
                    target_norm = F.normalize(full_column_encodings, dim=-1)  # (B, n_cols, D)
                    cos_sim = (pred_norm * target_norm).sum(dim=-1)  # (B, n_cols)

                    # Separate by masked vs unmasked using mask_1
                    marginal_value = torch.tensor(TokenStatus.MARGINAL, device=mask_1.device, dtype=mask_1.dtype)
                    is_masked = (mask_1 == marginal_value)  # (B, n_cols)

                    masked_sims = cos_sim[is_masked]
                    unmasked_sims = cos_sim[~is_masked]

                    masked_mean = masked_sims.mean().item() if len(masked_sims) > 0 else 0.0
                    masked_std = masked_sims.std().item() if len(masked_sims) > 1 else 0.0
                    unmasked_mean = unmasked_sims.mean().item() if len(unmasked_sims) > 0 else 0.0

                    logger.info(f"🎯 [epoch={current_epoch}] MARGINAL PREDICTION QUALITY (v2):")
                    logger.info(f"   Pred-Target cosine: masked={masked_mean:.4f}±{masked_std:.4f} ({len(masked_sims)} positions), "
                               f"unmasked={unmasked_mean:.4f} ({len(unmasked_sims)} positions)")

        # Return framework metrics directly - no legacy format conversion
        # The framework metrics contain all loss components dynamically
        #
        # Structure:
        # {
        #   "total": float,  # Combined loss value
        #   "full": {        # 128D embedding metrics
        #     "total": float,
        #     "components": {
        #       "contrastive": {"loss": float, "pos_sim": float, ...},
        #       "column_prediction": {"loss": float, "mean_cosine_sim": float, ...},
        #       ...
        #     }
        #   },
        #   "short": {       # 3D embedding metrics (same structure)
        #     ...
        #   }
        # }
        #
        # Logging code should walk framework_metrics["full"]["components"] and
        # framework_metrics["short"]["components"] dynamically instead of
        # hardcoding specific loss names.

        # Build loss_dict dynamically from framework_metrics
        # DualEmbeddingLossFramework returns: {"total": float, "full": {"components": {...}}, "short": {...}}
        # We need to get components from the "full" framework (128D embeddings)
        full_metrics = framework_metrics.get("full", {})
        components = full_metrics.get("components", {})

        loss_dict = {
            # Framework v2 marker - logging code checks this
            "_framework_v2": True,
            # Full framework metrics - pass through for any consumer that needs raw access
            "framework": framework_metrics,
            # Total loss value
            "total": framework_metrics.get("total", 0.0),
            # All components accessible by name
            "components": components,
        }

        # Also add each component at top level for easy access: loss_dict["contrastive"], etc.
        for name, comp_metrics in components.items():
            if isinstance(comp_metrics, dict):
                loss_dict[name] = comp_metrics

        # Legacy compatibility - map common component names to old expected keys
        # Only add if not already present
        if "spread_loss" not in loss_dict:
            spread = components.get("spread", {})
            loss_dict["spread_loss"] = {"total": spread.get("loss", 0.0)}
        if "joint_loss" not in loss_dict:
            # Try contrastive first, then joint_infonce
            joint = components.get("contrastive", components.get("joint_infonce", {}))
            loss_dict["joint_loss"] = {"total": joint.get("loss", 0.0)}
        if "marginal_loss" not in loss_dict:
            # Try column_prediction first, then marginal_infonce
            marginal = components.get("column_prediction", components.get("marginal_infonce", {}))
            loss_dict["marginal_loss"] = {"total": marginal.get("loss", 0.0)}

        # CRITICAL: Handle NULL baseline evaluation and column loss tracking for relationship extractor
        if self.training:
            try:
                relationship_extractor = getattr(self.joint_encoder, 'relationship_extractor', None)
                if relationship_extractor is not None:
                    # Compute per-column losses for relationship importance tracking
                    # Use cosine distance between predictions and targets per column
                    aggregated_col_losses = {}
                    if full_column_predictions_1 and full_column_encodings is not None:
                        # full_column_predictions_1 is list of (B, D), full_column_encodings is (B, n_cols, D)
                        for col_idx, col_name in self.idx_to_col_name.items():
                            if col_idx < len(full_column_predictions_1):
                                pred = full_column_predictions_1[col_idx]  # (B, D)
                                target = full_column_encodings[:, col_idx, :]  # (B, D)
                                # Cosine distance: 1 - cosine_similarity
                                cos_sim = torch.nn.functional.cosine_similarity(pred, target, dim=-1)  # (B,)
                                col_loss = (1 - cos_sim).mean().item()
                                if math.isfinite(col_loss):
                                    aggregated_col_losses[col_name] = col_loss

                    is_null_baseline = getattr(relationship_extractor, '_null_evaluation_pending', False)

                    # Always update column losses (for lift tracking on normal steps)
                    if aggregated_col_losses:
                        self.joint_encoder.update_column_losses(aggregated_col_losses)

                    if is_null_baseline:
                        # NULL baseline evaluation - update baseline EMA and finalize
                        relationship_extractor.update_column_losses(aggregated_col_losses, is_null_baseline=True)
                        relationship_extractor._finalize_null_baseline_batch()
                        logger.debug(f"[NULL_V2] Finalized NULL baseline with {len(aggregated_col_losses)} columns")
            except Exception as e:
                logger.warning(f"Failed to handle NULL baseline in v2: {e}")

        # COLLAPSE DIAGNOSTICS & RANKING METRICS: Compute for parity with compute_total_loss
        # These metrics are used for monitoring embedding quality and Recall@1/AUC
        collapse_diagnostics = {}
        if self.training:
            try:
                # 1. Joint embedding norms and std
                joint_norms = torch.norm(full_joint_encodings_unmasked, dim=1)  # (batch_size,)
                joint_norm_mean = joint_norms.mean().item()
                joint_norm_std = joint_norms.std().item()

                # Compute std of joint embeddings per dimension
                joint_std_per_dim = full_joint_encodings_unmasked.std(dim=0)  # (d_model,)
                joint_std_mean = joint_std_per_dim.mean().item()
                joint_std_std = joint_std_per_dim.std().item()

                collapse_diagnostics['joint_embedding'] = {
                    'norm_mean': joint_norm_mean,
                    'norm_std': joint_norm_std,
                    'std_per_dim_mean': joint_std_mean,
                    'std_per_dim_std': joint_std_std,
                }

                # 2. Ranking metrics from contrastive logits
                # Compute similarity matrix between predicted (masked) and target (unmasked) embeddings
                # This gives us Recall@1, AUC, etc.
                with torch.no_grad():
                    pred_norm = F.normalize(full_predictions_1, dim=1)  # (B, D)
                    target_norm = F.normalize(full_joint_encodings_unmasked, dim=1)  # (B, D)
                    # Logits: how similar is each predicted embedding to each target?
                    joint_logits = pred_norm @ target_norm.T  # (B, B)
                    # Scale by temperature used in contrastive loss
                    joint_logits = joint_logits / 0.1  # temperature

                    ranking_metrics = compute_ranking_metrics(joint_logits)
                    collapse_diagnostics['ranking_metrics'] = ranking_metrics

                    # =================================================================
                    # SCALAR-ONLY PROBE: Compute Recall@1 using ONLY scalar column encodings
                    # This validates whether scalar encodings carry useful information,
                    # or if the model is relying entirely on categoricals/relationships.
                    # If scalar_recall@1 >> random, scalars are useful despite high avg_cos.
                    # If scalar_recall@1 ≈ random, scalars are being ignored (Possibility B).
                    # =================================================================
                    try:
                        # Identify scalar column indices
                        scalar_col_indices = []
                        for i, col_name in enumerate(self.column_order):
                            col_type = self.config.col_types.get(col_name)
                            if col_type == ColumnType.SCALAR:
                                scalar_col_indices.append(i)

                        if scalar_col_indices and full_column_encodings is not None:
                            # Extract scalar column encodings: (B, n_scalar_cols, d_model)
                            scalar_encodings = full_column_encodings[:, scalar_col_indices, :]
                            # Pool across scalar columns: mean pooling -> (B, d_model)
                            scalar_pooled = scalar_encodings.mean(dim=1)
                            # Normalize and compute similarity matrix
                            scalar_pooled_norm = F.normalize(scalar_pooled, dim=1)
                            scalar_logits = scalar_pooled_norm @ scalar_pooled_norm.T / 0.1

                            scalar_ranking = compute_ranking_metrics(scalar_logits)
                            collapse_diagnostics['scalar_only_ranking'] = scalar_ranking

                            # Log periodically (first few batches + every 100 batches)
                            # SCALAR PROBE: Tests if scalar columns alone can identify rows
                            # - Embeddings: mean-pooled scalar column encodings (self-similarity)
                            # - Positives: diagonal (scalar[i] vs scalar[i])
                            # - Negatives: off-diagonal (scalar[i] vs scalar[j])
                            # - joint_R@1: full joint embedding retrieval (for comparison)
                            # - scalar_R@1: scalar-only retrieval (if ≈ random, scalars are not distinctive)
                            if not hasattr(self, '_scalar_probe_log_count'):
                                self._scalar_probe_log_count = 0
                            self._scalar_probe_log_count += 1
                            if self._scalar_probe_log_count <= 3 or self._scalar_probe_log_count % 100 == 0:
                                joint_r1 = ranking_metrics.get('recall_at_1', 0)
                                scalar_r1 = scalar_ranking.get('recall_at_1', 0)
                                random_r1 = 1.0 / batch_size if batch_size > 0 else 0
                                logger.info(f"📊 SCALAR PROBE (scalar-only self-sim): n_scalar_cols={len(scalar_col_indices)}, "
                                           f"joint_R@1={joint_r1:.3f}, scalar_R@1={scalar_r1:.3f}, "
                                           f"random={random_r1:.3f}")
                                if scalar_r1 < random_r1 * 2:
                                    logger.warning(f"   ⚠️  SCALAR ENCODINGS MAY BE USELESS: "
                                                  f"scalar_R@1={scalar_r1:.3f} ≈ random={random_r1:.3f}")
                    except Exception as e:
                        logger.debug(f"Scalar probe failed: {e}")

            except Exception as e:
                logger.debug(f"Failed to compute collapse diagnostics in v2: {e}")
                collapse_diagnostics = {'error': str(e)}

        loss_dict['collapse_diagnostics'] = collapse_diagnostics

        return total_loss, loss_dict

    def compute_proportionality_loss(self, batch, n_samples=8, perturbation_scale=0.1):
        """
        Compute proportionality loss for scalar (numeric) columns.
        
        This loss encourages the embedding distance to be proportional to the 
        input distance for numeric columns. Without this, discrete encoding 
        strategies (buckets, ranks) can dominate and cause small input changes 
        to produce zero embedding change.
        
        Args:
            batch: Dict of column_name -> TokenBatch
            n_samples: Number of rows to sample for perturbation test
            perturbation_scale: Scale of perturbation as fraction of column std
            
        Returns:
            Tuple of (loss tensor, loss_dict with details)
        """
        from featrix.neural.featrix_token import TokenBatch
        
        device = next(self.parameters()).device
        
        # Find scalar columns
        scalar_cols = []
        for col_name in self.config.cols_in_order:
            col_type = self.config.col_types.get(col_name)
            if col_type == ColumnType.SCALAR and col_name in batch:
                scalar_cols.append(col_name)
        
        if not scalar_cols:
            # No scalar columns to test
            return torch.tensor(0.0, device=device, requires_grad=True), {'total': 0.0, 'n_cols': 0}
        
        total_loss = torch.tensor(0.0, device=device, requires_grad=True)
        col_losses = {}
        
        # Sample indices from batch
        batch_size = len(next(iter(batch.values())).value)
        sample_indices = torch.randperm(batch_size, device=device)[:min(n_samples, batch_size)]
        
        for col_name in scalar_cols[:5]:  # Limit to 5 columns for efficiency
            try:
                token_batch = batch[col_name]
                original_values = token_batch.value[sample_indices].clone()
                
                # Skip if all values are the same (no variation to learn)
                if original_values.std() < 1e-6:
                    continue
                
                # Create perturbed values (add random noise proportional to column std)
                col_std = original_values.std().clamp(min=1e-6)
                perturbation = torch.randn_like(original_values) * perturbation_scale * col_std
                perturbed_values = original_values + perturbation
                
                # Create perturbed batch - clone the token batch structure
                perturbed_batch = {}
                for c_name, tb in batch.items():
                    if c_name == col_name:
                        # Create modified token batch for this column
                        new_values = tb.value.clone()
                        new_values[sample_indices] = perturbed_values
                        perturbed_batch[c_name] = TokenBatch.__new__(TokenBatch)
                        perturbed_batch[c_name].value = new_values
                        perturbed_batch[c_name].status = tb.status.clone()
                        perturbed_batch[c_name].attention_mask = tb.attention_mask.clone() if tb.attention_mask is not None else None
                    else:
                        # Keep other columns unchanged
                        perturbed_batch[c_name] = tb
                
                # Encode both original and perturbed
                with torch.no_grad():
                    # Get original embeddings for sampled rows
                    orig_short, orig_full, _, _ = self.column_encoder(batch)
                    pert_short, pert_full, _, _ = self.column_encoder(perturbed_batch)
                
                # We need gradients through the forward pass for training
                # Re-encode with gradients enabled
                orig_short_grad, orig_full_grad, _, _ = self.column_encoder(batch)
                pert_short_grad, pert_full_grad, _, _ = self.column_encoder(perturbed_batch)
                
                # Get column index
                col_idx = self.config.cols_in_order.index(col_name)
                
                # Extract embeddings for this column
                orig_emb = orig_full_grad[sample_indices, col_idx, :]  # [n_samples, d_model]
                pert_emb = pert_full_grad[sample_indices, col_idx, :]  # [n_samples, d_model]
                
                # Compute embedding distances
                emb_distances = torch.norm(orig_emb - pert_emb, dim=1)  # [n_samples]
                
                # Compute expected distances (normalized input change)
                input_distances = torch.abs(perturbation) / col_std  # [n_samples]
                
                # Target: embedding distance should scale with input distance
                # Loss: penalize when they don't match (squared difference)
                # We use a soft target: emb_dist should be roughly proportional to input_dist
                # scaled by some learned factor. For now, just minimize variance of ratio.
                ratio = emb_distances / (input_distances + 1e-6)
                
                # Loss: variance of ratio (ideally all ratios should be similar = proportional)
                # Plus: penalize if mean ratio is too small (embedding not responding)
                ratio_mean = ratio.mean()
                ratio_var = ratio.var()
                
                # Proportionality loss: high variance = bad proportionality
                # Also penalize if mean ratio is < 0.01 (embedding barely moves)
                min_response_penalty = F.relu(0.01 - ratio_mean) * 10.0
                
                col_loss = ratio_var + min_response_penalty
                total_loss = total_loss + col_loss
                
                col_losses[col_name] = {
                    'loss': col_loss.item(),
                    'ratio_mean': ratio_mean.item(),
                    'ratio_var': ratio_var.item(),
                    'min_response_penalty': min_response_penalty.item(),
                }
                
            except Exception as e:
                # Don't crash training if proportionality loss fails for one column
                logger.debug(f"Proportionality loss failed for {col_name}: {e}")
                continue
        
        # Average over columns
        n_cols = len(col_losses)
        if n_cols > 0:
            total_loss = total_loss / n_cols
        
        loss_dict = {
            'total': total_loss.item() if hasattr(total_loss, 'item') else 0.0,
            'n_cols': n_cols,
            'cols': col_losses,
        }
        
        return total_loss, loss_dict

    def encode(self, column_batches, apply_noise=False):
        """This is the method that should be called at query time."""
        
        # Get logger from the current module
        
        # CRITICAL: Force CPU mode for single predictor training
        force_cpu_env = os.environ.get('FEATRIX_FORCE_CPU_SINGLE_PREDICTOR')
        if force_cpu_env == '1':
            # Ensure encoder and all submodules are on CPU
            if list(self.parameters()):
                encoder_device = next(self.parameters()).device
                if encoder_device.type != 'cpu':
                    self.cpu()
                    if is_gpu_available():
                        empty_gpu_cache()
            
            # CRITICAL: Move all input TokenBatch objects to CPU
            cpu_device = torch.device('cpu')
            for col_name, token_batch in column_batches.items():
                if hasattr(token_batch, 'to'):
                    token_batch.to(cpu_device)
        
        # Debug counter for tracking problematic batches
        # debug_count = getattr(self, '_encode_debug_count', 0)
        # should_debug = debug_count < 3  # Debug first 3 batches
        
        # CRITICAL: Check if column_encoder has empty col_order before attempting encoding
        if hasattr(self.column_encoder, 'col_order') and len(self.column_encoder.col_order) == 0:
            logger.error(f"💥 CRITICAL: column_encoder.col_order is EMPTY before encoding!")
            logger.error(f"   Input column_batches keys: {list(column_batches.keys()) if column_batches else 'None'}")
            logger.error(f"   Column encoder encoders: {list(self.column_encoder.encoders.keys()) if hasattr(self.column_encoder, 'encoders') else 'None'}")
            logger.error(f"   Column encoder codecs: {list(self.column_encoder.col_codecs.keys()) if hasattr(self.column_encoder, 'col_codecs') and self.column_encoder.col_codecs else 'None'}")
            raise RuntimeError(
                f"Column encoder has empty col_order - cannot encode. "
                f"This indicates the encoder was saved incorrectly or the model is corrupted. "
                f"Input had {len(column_batches) if column_batches else 0} columns: {list(column_batches.keys())[:10] if column_batches else []}"
            )
        
        # if should_debug:
        #     logger.info(f"🔍 ENCODER DEBUG #{debug_count}: Starting encoder.encode")
        #     logger.info(f"   Input columns: {list(column_batches.keys())}")
        #     logger.info(f"   Apply noise: {apply_noise}")
        
        (
            short_column_encoding_list,
            full_column_encoding_list,
            token_status_list,
            raw_timestamp_features,  # Raw 12-feature vectors for timestamp columns
        ) = self.column_encoder(column_batches)

        # CRITICAL: Check for empty encoding lists before stacking
        # This prevents "stack expects a non-empty TensorList" errors
        if len(full_column_encoding_list) == 0:
            logger.error(f"💥 CRITICAL: full_column_encoding_list is EMPTY!")
            logger.error(f"   This causes 'stack expects a non-empty TensorList' error")
            logger.error(f"   Column encoder returned no encodings")
            logger.error(f"   Input columns: {list(column_batches.keys()) if column_batches else 'None'}")
            logger.error(f"   Number of input columns: {len(column_batches) if column_batches else 0}")
            raise RuntimeError("No columns were encoded - check column setup and codec creation. This usually means the query record has no fields that match the trained codecs.")
        
        if len(short_column_encoding_list) == 0:
            logger.error(f"💥 CRITICAL: short_column_encoding_list is EMPTY!")
            logger.error(f"   This causes 'stack expects a non-empty TensorList' error")
            logger.error(f"   Column encoder returned no short encodings")
            logger.error(f"   Input columns: {list(column_batches.keys()) if column_batches else 'None'}")
            raise RuntimeError("No columns were encoded (short) - check column setup and codec creation")
        
        # if should_debug:
        #     logger.info(f"   Column encoder output - lists length: {len(short_column_encoding_list)}")
        #     for i, (short_enc, full_enc) in enumerate(zip(short_column_encoding_list, full_column_encoding_list)):
        #         if torch.isnan(short_enc).any() or torch.isnan(full_enc).any():
        #             col_name = list(column_batches.keys())[i] if i < len(column_batches) else f"col_{i}"
        #             logger.error(f"🚨 COLUMN ENCODER OUTPUT HAS NaN: {col_name}")
        #             if torch.isnan(short_enc).any():
        #                 logger.error(f"   Short encoding NaN count: {torch.isnan(short_enc).sum()}/{short_enc.numel()}")
        #             if torch.isnan(full_enc).any():
        #                 logger.error(f"   Full encoding NaN count: {torch.isnan(full_enc).sum()}/{full_enc.numel()}")
        
        # CRITICAL: Check tensor shapes before stacking to provide better error messages
        try:
            column_encodings, token_status_mask = (
                torch.stack(full_column_encoding_list, dim=1),
                torch.stack(token_status_list, dim=1),
            )
        except RuntimeError as e:
            if "stack expects each tensor to be equal size" in str(e):
                logger.error(f"💥 TENSOR SHAPE MISMATCH in column encoding stacking:")
                logger.error(f"   Error: {e}")
                logger.error(f"   Number of columns: {len(full_column_encoding_list)}")
                for i, enc in enumerate(full_column_encoding_list):
                    logger.error(f"   Column {i} shape: {enc.shape}")
                logger.error(f"   This usually means an encoder is returning 3D instead of 2D tensors")
                logger.error(f"   Check hybrid column encoders or text/sequence encoders")
            raise

        # if should_debug:
        #     if torch.isnan(column_encodings).any():
        #         logger.error(f"🚨 STACKED COLUMN ENCODINGS HAVE NaN: {torch.isnan(column_encodings).sum()}/{column_encodings.numel()}")
        #     logger.info(f"   Stacked encodings shape: {column_encodings.shape}")

        self.column_encodings = column_encodings
        self.token_status_mask = token_status_mask

        if apply_noise is True:
            batch_size = column_encodings.shape[0]
            column_marginal_embeddings = self.get_marginal_tensor(batch_size)
            column_encodings = self.apply_marginal_mask(
                column_encodings, column_marginal_embeddings, token_status_mask
            )
            
            # if should_debug:
            #     if torch.isnan(column_encodings).any():
            #         logger.error(f"🚨 AFTER MARGINAL MASK ENCODINGS HAVE NaN: {torch.isnan(column_encodings).sum()}/{column_encodings.numel()}")

        # ROOT CAUSE DEBUGGING: Check for zero vectors before joint encoder
        # if should_debug:
        #     # Check for zero vectors that could cause NaN during normalization
        #     zero_tensor = torch.zeros_like(column_encodings)
        #     zero_vectors = torch.allclose(column_encodings, zero_tensor, atol=1e-8)
        #     if zero_vectors:
        #         logger.error(f"🚨 ZERO VECTORS DETECTED before joint encoder!")
        #         logger.error(f"   column_encodings contains all zeros: {column_encodings}")
            
        #     # Check for individual zero rows/columns
        #     for i in range(column_encodings.shape[0]):  # batch dimension
        #         for j in range(column_encodings.shape[1]):  # column dimension
        #             vec = column_encodings[i, j, :]
        #             zero_vec = torch.zeros_like(vec)
        #             if torch.allclose(vec, zero_vec, atol=1e-8):
        #                 col_name = list(column_batches.keys())[j] if j < len(column_batches) else f"col_{j}"
        #                 logger.error(f"🚨 Zero vector for batch {i}, column '{col_name}': {vec}")

        # Convert token_status_mask to binary mask for relationship extractor
        binary_mask = _token_status_to_binary_mask(token_status_mask) if token_status_mask is not None else None
        
        # CRITICAL: Ensure column_encodings is on the same device as joint_encoder
        # This prevents device mismatch errors when column encodings are on CPU but joint_encoder is on CUDA
        # This can happen when string encodings come from CPU or DataLoader creates tensors on CPU
        joint_encoder_device = None  # Default if we can't determine device
        try:
            joint_encoder_device = next(self.joint_encoder.parameters()).device
            if column_encodings.device != joint_encoder_device:
                column_encodings = column_encodings.to(device=joint_encoder_device)
                if binary_mask is not None and binary_mask.device != joint_encoder_device:
                    binary_mask = binary_mask.to(device=joint_encoder_device)
                # Move raw timestamp features to correct device
                if raw_timestamp_features:
                    raw_timestamp_features = {
                        k: v.to(device=joint_encoder_device) for k, v in raw_timestamp_features.items()
                    }
        except (StopIteration, AttributeError):
            # Joint encoder has no parameters or can't determine device - skip device placement
            pass

        # Get strategy encodings from column encoder (if strategy-aware relationships enabled)
        strategy_encodings = getattr(self.column_encoder, '_strategy_encodings', None)
        strategy_masks = getattr(self.column_encoder, '_strategy_masks', None)

        # Move strategy encodings to correct device if needed
        if strategy_encodings and joint_encoder_device is not None:
            strategy_encodings = {
                k: v.to(device=joint_encoder_device) for k, v in strategy_encodings.items()
            }
        if strategy_masks and joint_encoder_device is not None:
            strategy_masks = {
                k: v.to(device=joint_encoder_device) for k, v in strategy_masks.items()
            }

        short_joint_encodings, full_joint_encodings = self.joint_encoder(
            column_encodings, mask=binary_mask, raw_timestamp_features=raw_timestamp_features,
            strategy_encodings=strategy_encodings, strategy_masks=strategy_masks
        )

        # if should_debug:
        #     if torch.isnan(short_joint_encodings).any():
        #         logger.error(f"🚨 JOINT ENCODER SHORT OUTPUT HAS NaN: {torch.isnan(short_joint_encodings).sum()}/{short_joint_encodings.numel()}")
        #     if torch.isnan(full_joint_encodings).any():
        #         logger.error(f"🚨 JOINT ENCODER FULL OUTPUT HAS NaN: {torch.isnan(full_joint_encodings).sum()}/{full_joint_encodings.numel()}")
        #     logger.info(f"   Joint encoder output shapes: short={short_joint_encodings.shape}, full={full_joint_encodings.shape}")
        #     self._encode_debug_count = debug_count + 1

        return short_joint_encodings, full_joint_encodings

    def forward(self, column_batches):
        # Store column_batches for reconstruction loss (used by compute_total_loss)
        # This avoids changing the return signature which would break many callers
        self._last_column_batches = column_batches

        # DEBUG: MPS INT_MAX - Track batch for debugging
        _debug_mps = getattr(self, '_debug_mps_batch_count', 0)
        self._debug_mps_batch_count = _debug_mps + 1
        
        # Debug on first 3 batches, OR on pruning epochs (every 5th epoch starting at 5)
        # Get current epoch from any scalar codec that has it
        _current_epoch = 0
        try:
            for codec in self.column_encoder.column_codecs.values():
                if hasattr(codec, '_current_epoch'):
                    _current_epoch = codec._current_epoch.item() if hasattr(codec._current_epoch, 'item') else codec._current_epoch
                    break
        except Exception:
            pass
        
        _is_prune_epoch = _current_epoch >= 5 and _current_epoch % 5 == 0
        _should_debug = _debug_mps < 3 or (_is_prune_epoch and _debug_mps % 33 == 0)  # First batch of prune epochs
        
        if _should_debug:
            logger.info(f"[DEBUG] FeatrixTableEncoder.forward() - batch #{_debug_mps}, epoch={_current_epoch}")
            logger.info(f"[DEBUG]   Input column_batches: {len(column_batches)} columns")
            _log_gpu_memory_encoders("BEFORE column_encoder (start of forward)")

        # Encode the columns invidividually
        (
            short_column_encoding_list,
            full_column_encoding_list,
            token_status_list,
            raw_timestamp_features,  # Raw 12-feature vectors for timestamp columns
        ) = self.column_encoder(column_batches)
        
        if _should_debug:
            _log_gpu_memory_encoders("After column_encoder")
            logger.info(f"[DEBUG]   After column_encoder: {len(full_column_encoding_list)} encodings")

        # Combine the individual column encodings and masks into tensors for easier handling
        # the resulting tensors have shapes (batch_size, n_cols, d_model) and (batch_size, n_cols), respectively
        # The ease of handling is mostly related to masking - it's much easier to carry out the masking procedure
        # on a single tensor object that contains the embeddings for all the columns because that makes
        # the coordination of how many columns to mask out much easier.
        
        # DEBUG: Check for empty encoding lists before stacking
        if len(short_column_encoding_list) == 0:
            logger.error(f"💥 CRITICAL: short_column_encoding_list is EMPTY!")
            logger.error(f"   This causes 'stack expects a non-empty TensorList' error")
            logger.error(f"   Column encoder returned no encodings")
            raise RuntimeError("No columns were encoded - check column setup and codec creation")
            
        short_column_encodings, full_column_encodings, token_status_mask = (
            torch.stack(short_column_encoding_list, dim=1),
            torch.stack(full_column_encoding_list, dim=1),
            torch.stack(token_status_list, dim=1),
        )

        batch_size = full_column_encodings.shape[0]

        if _should_debug:
            _log_gpu_memory_encoders("After stacking")
            logger.info(f"[DEBUG]   After stacking: full_column_encodings shape = {full_column_encodings.shape}")
            logger.info(f"[DEBUG]   batch_size = {batch_size}, numel = {full_column_encodings.numel()}")

        # MARGINAL INITIALIZATION & EMA UPDATE
        # During warmup (epochs 0-4), marginals aren't used via gradients, so we:
        # 1. Initialize them from column means after epoch 0 (once)
        # 2. Update them via EMA to track evolving column distributions
        current_epoch = getattr(self, '_current_epoch', 0)
        zero_masking_phase = (self.min_mask_ratio == 0 and self.max_mask_ratio == 0)

        if current_epoch >= 1 and not self._marginals_initialized:
            # Initialize marginals from data after epoch 0
            self.initialize_marginals_from_data(full_column_encodings)

        if zero_masking_phase and self._marginals_initialized:
            # During warmup, update marginals via EMA to track evolving encoders
            # Use momentum=0.1 (10% toward current mean per batch)
            self.update_marginals_toward_data(full_column_encodings, momentum=0.1)

        # with stopwatch.interval("sample_marginal_masks"):
        # Each row is randomly split into two non-overlapping parts. We do that so we
        # can embed each part separately and then use it to predict the other part.
        # We take in the batch status mask, and return two mask that are complimentary.
        mask_1, mask_2, rows_skipped = sample_marginal_masks(
            token_status_mask,
            self.min_mask_ratio,
            self.max_mask_ratio,
            self.mean_nulls_per_row,
            col_names=self.config.cols_in_order,
            track_bias=True,
            unmasked_fraction=self.unmasked_fraction
        )

        # with stopwatch.interval("get_marginal_tensor"):
        full_column_marginal_embeddings = self.get_marginal_tensor(batch_size)

        # with stopwatch.interval("joint_encoding"):
        # Convert token_status_mask to binary mask for relationship extractor
        binary_mask = _token_status_to_binary_mask(token_status_mask) if token_status_mask is not None else None

        # Check if we're in 0% masking mode (curriculum warmup)
        # In this case, skip masking entirely to ensure masked == unmasked
        zero_masking = (self.min_mask_ratio == 0 and self.max_mask_ratio == 0)

        # Log once when zero_masking is active (helps confirm the curriculum is working)
        if zero_masking and not getattr(self, '_logged_zero_masking', False):
            current_epoch = getattr(self, '_current_epoch', 0)
            logger.info(f"[JOINT_DEBUG] epoch={current_epoch} | ZERO_MASKING active: "
                       f"min={self.min_mask_ratio:.0%} max={self.max_mask_ratio:.0%} "
                       f"(calling joint_encoder ONCE to ensure input==target)")
            self._logged_zero_masking = True
        elif not zero_masking and getattr(self, '_logged_zero_masking', False):
            # Reset when transitioning out of zero_masking
            self._logged_zero_masking = False
            current_epoch = getattr(self, '_current_epoch', 0)
            logger.info(f"[JOINT_DEBUG] epoch={current_epoch} | ZERO_MASKING off: "
                       f"masking now {self.min_mask_ratio:.0%}-{self.max_mask_ratio:.0%}")

        if zero_masking:
            # No masking - use same encodings and masks for everything
            # This ensures identity baseline is perfect during warmup
            masked_column_encodings_1 = full_column_encodings
            masked_column_encodings_2 = full_column_encodings
            mask_1_binary = binary_mask
            mask_2_binary = binary_mask
        else:
            # with stopwatch.interval("apply_marginal_masks"):
            masked_column_encodings_1 = self.apply_marginal_mask(
                full_column_encodings, full_column_marginal_embeddings, mask_1
            )
            masked_column_encodings_2 = self.apply_marginal_mask(
                full_column_encodings, full_column_marginal_embeddings, mask_2
            )
            # For masked encodings, use the corresponding mask (mask_1 or mask_2)
            # These masks indicate which columns are masked for marginal prediction
            mask_1_binary = _token_status_to_binary_mask(mask_1) if mask_1 is not None else binary_mask
            mask_2_binary = _token_status_to_binary_mask(mask_2) if mask_2 is not None else binary_mask

            # DEBUG: Compare marginal embeddings vs actual column encodings
            current_epoch = getattr(self, '_current_epoch', 0)
            if not hasattr(self, '_logged_marginal_debug') or self._logged_marginal_debug != current_epoch:
                self._logged_marginal_debug = current_epoch
                with torch.no_grad():
                    # full_column_encodings: (B, n_cols, d_model)
                    # full_column_marginal_embeddings: (B, n_cols, d_model)
                    # Compute cosine similarity between marginals and actual encodings per column
                    actual_mean = full_column_encodings.mean(dim=0)  # (n_cols, d_model)
                    marginal_mean = full_column_marginal_embeddings[0]  # (n_cols, d_model) - same for all batch

                    # Per-column cosine similarity
                    cos_sim = F.cosine_similarity(actual_mean, marginal_mean, dim=1)  # (n_cols,)

                    # Also check norms
                    actual_norms = actual_mean.norm(dim=1)
                    marginal_norms = marginal_mean.norm(dim=1)

                    logger.info(f"[MARGINAL_DEBUG] epoch={current_epoch} | "
                               f"marginal vs actual cosine_sim: mean={cos_sim.mean():.4f} min={cos_sim.min():.4f} max={cos_sim.max():.4f}")
                    logger.info(f"[MARGINAL_DEBUG] epoch={current_epoch} | "
                               f"actual_norms: mean={actual_norms.mean():.4f} | "
                               f"marginal_norms: mean={marginal_norms.mean():.4f}")
                    logger.info(f"[MARGINAL_DEBUG] epoch={current_epoch} | "
                               f"soft_mask_alpha={self.soft_mask_alpha:.3f} "
                               f"(0=all actual, 1=all marginal)")

                    # Compare masked_column_encodings_1 vs full_column_encodings
                    # Compute diff ONLY on masked positions to verify soft masking
                    marginal_value = torch.tensor(TokenStatus.MARGINAL, device=mask_1.device, dtype=mask_1.dtype)
                    marginal_mask = (mask_1 == marginal_value)  # (B, n_cols)
                    n_marginal = marginal_mask.sum().item()

                    if n_marginal > 0:
                        # Diff on masked positions only
                        masked_positions = marginal_mask.unsqueeze(-1).expand_as(masked_column_encodings_1)
                        diff_on_masked = (masked_column_encodings_1 - full_column_encodings).abs()
                        diff_masked_only = diff_on_masked[masked_positions].mean()
                        diff_all = diff_on_masked.mean()

                        # Expected diff: α * |marginal - actual| on masked positions
                        marginal_diff = (full_column_marginal_embeddings - full_column_encodings).abs()
                        expected_diff = self.soft_mask_alpha * marginal_diff[masked_positions].mean()

                        logger.info(f"[MARGINAL_DEBUG] epoch={current_epoch} | "
                                   f"n_marginal={n_marginal} ({n_marginal/mask_1.numel()*100:.1f}%) "
                                   f"diff_masked_only={diff_masked_only:.4f} "
                                   f"expected={expected_diff:.4f} "
                                   f"diff_all={diff_all:.6f}")

        if _should_debug:
            _log_gpu_memory_encoders("Before joint_encoder")
            logger.info(f"[DEBUG]   Before joint_encoder calls:")
            logger.info(f"[DEBUG]     masked_column_encodings_1 shape: {masked_column_encodings_1.shape}")
            logger.info(f"[DEBUG]     zero_masking={zero_masking}")
            logger.info(f"[DEBUG]     About to call joint_encoder...")

        if zero_masking:
            # With 0% masking, all three joint encoder calls would use the same input
            # But dropout causes different outputs each call. To ensure input==target,
            # call joint_encoder ONCE and reuse the output for all three.
            short_joint_encodings_1, full_joint_encodings_1 = self.joint_encoder(
                full_column_encodings, mask=binary_mask, raw_timestamp_features=raw_timestamp_features
            )
            short_joint_encodings_2 = short_joint_encodings_1
            full_joint_encodings_2 = full_joint_encodings_1
            short_joint_encodings_unmasked = short_joint_encodings_1
            full_joint_encodings_unmasked = full_joint_encodings_1
        else:
            # Masked view 1: dropout ON (regularization for predictor)
            short_joint_encodings_1, full_joint_encodings_1 = self.joint_encoder(
                masked_column_encodings_1, mask=mask_1_binary, raw_timestamp_features=raw_timestamp_features
            )

            if _should_debug:
                _log_gpu_memory_encoders("After joint_encoder #1")
                logger.info(f"[DEBUG]   After joint_encoder #1: full_joint_encodings_1 shape = {full_joint_encodings_1.shape}")

            # Masked view 2: different mask, different dropout
            short_joint_encodings_2, full_joint_encodings_2 = self.joint_encoder(
                masked_column_encodings_2, mask=mask_2_binary, raw_timestamp_features=raw_timestamp_features
            )

            if _should_debug:
                logger.info(f"[DEBUG]   After joint_encoder #2: full_joint_encodings_2 shape = {full_joint_encodings_2.shape}")

            # Unmasked target: compute WITHOUT gradients
            # This is standard contrastive learning - the target is clean, the inputs are noisy
            # Dropout differences between masked and unmasked are fine (part of augmentation)
            with torch.no_grad():
                (
                    short_joint_encodings_unmasked,
                    full_joint_encodings_unmasked,
                ) = self.joint_encoder(full_column_encodings, mask=binary_mask, raw_timestamp_features=raw_timestamp_features)

        if _should_debug:
            logger.info(f"[DEBUG]   After joint_encoder #3: full_joint_encodings_unmasked shape = {full_joint_encodings_unmasked.shape}")

        # Column predictions are a list of torch.tensors. Each element of the list
        # corresponds to the predictions made for the corresponding column.
        # The list elements are ordered by config.cols_in_order.
        # The list elements all have shape (batch_size, model_dim)
        # with stopwatch.interval("column_predictors"):
        full_column_predictions_unmasked = self.column_predictor(
            full_joint_encodings_unmasked
        )
        full_column_predictions_1 = self.column_predictor(full_joint_encodings_1)
        full_column_predictions_2 = self.column_predictor(full_joint_encodings_2)

        # with stopwatch.interval("column_predictors_short"):
        short_column_predictions_1 = self.short_column_predictor(
            short_joint_encodings_1
        )
        short_column_predictions_2 = self.short_column_predictor(
            short_joint_encodings_2
        )
        short_column_predictions_unmasked = self.short_column_predictor(
            short_joint_encodings_unmasked
            )

        # DIAGNOSTIC: Check variance of column predictions at masked vs unmasked positions
        # If predictions for masked columns don't vary across rows, infoNCE can't learn
        current_epoch = getattr(self, '_current_epoch', 0)
        if not hasattr(self, '_masked_variance_debug_epoch') or self._masked_variance_debug_epoch != current_epoch:
            self._masked_variance_debug_epoch = current_epoch
            if not zero_masking:
                with torch.no_grad():
                    # mask_1 has TokenStatus.MARGINAL where columns are masked
                    marginal_value = torch.tensor(TokenStatus.MARGINAL, device=mask_1.device, dtype=mask_1.dtype)
                    masked_positions = (mask_1 == marginal_value)  # (B, n_cols)
                    unmasked_positions = (mask_1 == torch.tensor(TokenStatus.OK, device=mask_1.device, dtype=mask_1.dtype))

                    # Identify which columns are masked vs unmasked
                    col_is_masked = masked_positions.any(dim=0)  # (n_cols,)
                    col_is_unmasked = unmasked_positions.all(dim=0)  # (n_cols,)

                    # Check predictions variance - this is what matters for infoNCE
                    # full_column_predictions_1 is list of (B, d_model) tensors
                    pred_stack = torch.stack(full_column_predictions_1, dim=1)  # (B, n_cols, d_model)
                    pred_var = pred_stack.var(dim=0).mean(dim=1)  # (n_cols,) - variance across batch, avg over d_model

                    masked_pred_var = pred_var[col_is_masked].mean().item() if col_is_masked.any() else 0.0
                    unmasked_pred_var = pred_var[col_is_unmasked].mean().item() if col_is_unmasked.any() else 0.0

                    n_masked = col_is_masked.sum().item()
                    n_unmasked = col_is_unmasked.sum().item()

                    pred_ratio = masked_pred_var / unmasked_pred_var if unmasked_pred_var > 0 else 0.0

                    # Also check joint encoder output variance (single embedding per row)
                    # full_joint_encodings_1: (B, d_model)
                    joint_var = full_joint_encodings_1.var(dim=0).mean().item()  # scalar - avg variance across d_model

                    # Check INPUT variance - are the column encodings varying across rows?
                    # full_column_encodings: (B, n_cols, d_model)
                    input_var = full_column_encodings.var(dim=0).mean().item()  # variance across batch

                    logger.info(f"🔬 [epoch={current_epoch}] PREDICTION VARIANCE:")
                    logger.info(f"   Input column encodings: var={input_var:.6f}")
                    logger.info(f"   Joint encoder output:   var={joint_var:.6f}")
                    logger.info(f"   Ratio (output/input):   {joint_var/input_var:.4f}" if input_var > 0 else "   Ratio: N/A")
                    if joint_var < input_var * 0.1:
                        logger.warning(f"   ⚠️  VARIANCE COLLAPSE: joint output ({joint_var:.6f}) << input ({input_var:.6f})")

        # stopwatch.stop()

        return (
            batch_size,
            #
            full_joint_encodings_unmasked,
            full_joint_encodings_1,
            full_joint_encodings_2,
            #
            full_column_encodings,
            short_column_encodings,
            #
            short_joint_encodings_unmasked,
            short_joint_encodings_1,
            short_joint_encodings_2,
            #
            mask_1,
            mask_2,
            #
            full_column_predictions_1,
            full_column_predictions_2,
            full_column_predictions_unmasked,
            #
            short_column_predictions_1,
            short_column_predictions_2,
            short_column_predictions_unmasked,
            #
            rows_skipped,  # Number of rows skipped from masking (too many nulls)
        )
