#  -*- coding: utf-8 -*-
#
#  Copyright Featrix, Inc 2023-2025
#
#  Proprietary and Confidential.  Unauthorized use, copying or dissemination
#  of these materials is strictly prohibited.
"""
DynamicRelationshipExtractor: Relationship learning with type-aware operations.

GENERIC OPERATIONS:
- Only 1 generic operation: presence/null pattern correlation
- Captures which columns tend to be present/missing together
- Embedding arithmetic (multiply, add, divide, etc.) has been REMOVED
  because these operations on embeddings are semantically meaningless

TYPE-AWARE OPERATIONS:
- Replace generic tokens with semantically meaningful relationships
- Use actual RAW DATA (not embeddings) for operations:
  - ScalarScalarOps: ratio, difference on actual numeric values
  - SetSetOps: co-occurrence patterns using actual category values
  - SetTimestampOps: temporal patterns using actual datetime values
  - SetScalarOps: scalar-conditioned gating
  - EmailDomainOps, URLOps: domain-specific patterns
  - TemporalRelationshipOps: timestamp deltas, cyclical patterns

SCALABILITY FEATURES:
- Chunked computation: Process pairs in batches to avoid memory overflow
- Coarse exploration sampling: Sample subset of pairs for very large column counts
- History-aware prioritization: Use meta-learning API to prioritize known-good pairs
- Adaptive memory: Learn max safe pairs per host from experience
- Progressive pruning: Prune to top 25% relationships per column
"""
import logging
import math
import random
import time
from typing import Any, Dict, List, Optional, Tuple, Set, TYPE_CHECKING

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

if TYPE_CHECKING:
    from featrix.neural.type_aware_ops_config import TypeAwareOpsConfig

# Per-host GPU memory learning
from .host_memory_tracker import HostMemoryTracker, get_learned_max_pairs, record_success, record_oom_failure, get_pair_history

# Causal importance scoring and validation
from .causal_relationship_scorer import CausalRelationshipScorer
from .relationship_importance_validator import ImportanceScoringValidator

logger = logging.getLogger(__name__)


def smoothstep01(t: float) -> float:
    """0..1 -> 0..1 with zero slope at ends."""
    t = 0.0 if t < 0 else 1.0 if t > 1 else t
    return t * t * (3 - 2 * t)


def ramp_plateau(C: int, *, start: int, cap: int, C0: int, C1: int) -> int:
    """
    Start at/below C0, smoothly ramps, hits cap at/above C1.
    
    Args:
        C: Column count
        start: Value at/below C0
        cap: Value at/above C1
        C0: Column count where ramp begins
        C1: Column count where ramp reaches cap
    """
    if C <= C0:
        return start
    if C >= C1:
        return cap
    t = (C - C0) / (C1 - C0)
    s = smoothstep01(t)
    return int(round(start + (cap - start) * s))


def _get_gpu_memory_gb() -> Optional[float]:
    """
    Get total GPU memory in GB.
    
    Returns:
        Total GPU memory in GB, or None if no GPU available.
    """
    if not torch.cuda.is_available():
        return None
    try:
        device_idx = torch.cuda.current_device()
        total_bytes = torch.cuda.get_device_properties(device_idx).total_memory
        return total_bytes / (1024 ** 3)
    except Exception:
        return None


def _compute_max_pairs_for_gpu(
    gpu_memory_gb: Optional[float],
    n_cols: int,
    batch_size: int = 128,
    d_model: int = 128,
) -> int:
    """
    Compute safe max pairs based on GPU memory.

    Memory usage for relationship computation includes:
        1. Presence pattern (4 binary flags) + type-aware ops per pair
        2. PyTorch autograd keeping ALL intermediates for backprop
        3. Type-aware ops MLPs (SetSetOps, ScalarScalarOps, etc.)
        4. Memory fragmentation from many small allocations
    
    EMPIRICAL DATA (this is what actually matters):
        - 5000 pairs on 24GB GPU with batch=128, d_model=128, 149 cols = 22GB usage
        - That's 22GB / 5000 pairs = ~4.4 MB per pair (not KB!)
        - The autograd graph retention is the killer
    
    Safe limits based on empirical 4.4MB/pair at batch=128:
        - 24GB GPU, batch=128 → ~500 pairs (uses ~2.2GB, leaves headroom)
        - 48GB GPU, batch=128 → ~1000 pairs (uses ~4.4GB)
        - 80GB GPU, batch=128 → ~2000 pairs (uses ~8.8GB)
        - 95GB GPU, batch=256 → ~1000 pairs (batch doubles memory)
    
    Args:
        gpu_memory_gb: Total GPU memory in GB (None = no GPU)
        n_cols: Number of columns
        batch_size: Training batch size
        d_model: Model dimension
        
    Returns:
        Maximum number of pairs to compute at once.
    """
    if gpu_memory_gb is None:
        # CPU - be very conservative
        return 100
    
    # Reserve GPU memory for relationship pairs - more conservative for 24GB GPUs
    # The rest is for: model, column encodings, attention, gradients, optimizer, fragmentation
    if gpu_memory_gb <= 24:
        # 24GB GPUs: use only 5% (was 10%) to leave more headroom
        available_for_pairs_gb = gpu_memory_gb * 0.05
    else:
        # Larger GPUs: use 10% as before
        available_for_pairs_gb = gpu_memory_gb * 0.10
    
    # EMPIRICAL: ~4.4 MB per pair at batch=128, d_model=128
    # From: 22GB / 5000 pairs = 4.4MB
    mb_per_pair_base = 4.4  # MB per pair at batch=128, d_model=128
    
    # Scale by batch size (linear relationship with memory)
    batch_scale = batch_size / 128.0
    mb_per_pair = mb_per_pair_base * batch_scale
    
    # Scale by d_model (affects tensor sizes)
    dim_scale = d_model / 128.0
    mb_per_pair = mb_per_pair * dim_scale
    
    # Convert to pairs
    available_mb = available_for_pairs_gb * 1024
    max_pairs = int(available_mb / mb_per_pair)
    
    # Apply sensible bounds: at least 50, at most 1000
    # For 24GB GPUs, cap at 300 pairs (was ~550) to be more conservative
    # Even on huge GPUs, limit to 1000 to avoid fragmentation and ensure stability
    if gpu_memory_gb and gpu_memory_gb <= 24:
        max_pairs = max(50, min(max_pairs, 300))  # Cap at 300 for 24GB
    else:
        max_pairs = max(50, min(max_pairs, 1000))
    
    return max_pairs

# Try to import meta-learning client for relationship history
# Relationship pairs are stored as feature suggestions with type "relationship_pair"
try:
    from meta_learning_client import (
        push_feature_engineering_suggestions,
        retrieve_feature_engineering_suggestions,
        get_dataset_characteristics
    )
    _HAS_META_LEARNING = True
except ImportError:
    _HAS_META_LEARNING = False
    logger.debug("meta_learning_client not available - relationship history disabled")


class DynamicRelationshipExtractor(nn.Module):
    """
    Relationship extractor with type-aware operations and dynamic pruning.

    GENERIC OPERATION (computed for ALL pairs):
        Presence pattern (null-correlation):
          - 4 flags: both_present, only_a_present, only_b_present, neither_present
          - Captures which columns tend to be present/missing together

    TYPE-AWARE OPERATIONS (replace generic for matching column type pairs):
        - ScalarScalarOps: ratio, difference on actual numeric values
        - SetSetOps: co-occurrence patterns using actual category values
        - SetTimestampOps: temporal gating and cyclical patterns
        - SetScalarOps: scalar-conditioned category gating
        - ScalarTimestampOps: cyclical correlation with time
        - TemporalRelationshipOps: timestamp deltas between datetime columns
        - EmailDomainOps: free/corporate domain patterns
        - URLOps: protocol, TLD, path patterns

    NOTE: Embedding arithmetic operations (multiply, add, subtract, divide, cosine)
    have been REMOVED. These operations on learned embeddings are semantically
    meaningless. Type-aware ops use actual RAW DATA for semantic relationships.

    Pruning Strategy:
        - Epochs 1-N: Compute ALL N*(N-1)/2 pairs, track contributions
        - Epochs N+1 onwards: Each column keeps top 25% partners (~75% reduction)
    """
    
    def __init__(
        self,
        d_model: int,
        col_names_in_order: List[str],
        exploration_epochs: int = 10,
        top_k_fraction: float = 0.40,
        enable_operation_pruning: bool = False,  # Future: prune operations within pairs
        progressive_pruning: bool = True,  # Gradually disable relationships instead of hard cutoff
        pairs_to_prune_per_epoch: int = None,  # How many pairs to disable each epoch (None = auto-calculate)
        target_pruning_epochs: int = None,  # How many epochs to spread pruning over (None = auto from n_epochs)
        min_relationships_to_keep: int = None,  # Minimum relationships to always keep (None = auto: max(5, n_cols/2))
        ucb_alpha: float = 1.5,  # UCB exploration parameter for Phase 2 (default 1.5, typical range 1.0-2.0)
        use_ucb_selection: bool = True,  # Phase 2: Enable UCB selection instead of simple score sorting
        edge_dropout_prob: float = 0.2,  # Edge dropout probability (0.1-0.3 early, reduces hub dominance, free regularization)
        confidence_weight_n0: int = 40,  # Confidence weighting threshold: score = ema_lift × min(1, n_ij/n0) (default 40, range 30-50)
        max_column_fraction: float = 0.10,  # Max fraction of active pool any single column can occupy (prevents hub dominance)
        # ============================================================================
        # COARSE EXPLORATION: Evaluate relationships at lower resolution initially
        # ============================================================================
        # With 1000 columns: 499,500 pairs × type-aware ops need memory management
        # Coarse exploration at reduced dimension allows evaluating ALL pairs cheaply
        # This allows exploring ALL pairs cheaply, then focusing on top-K at full resolution
        coarse_exploration_dim: int = 32,  # Dimension for coarse exploration (None = full d_model)
        max_coarse_pairs: int = None,  # Max pairs to evaluate (None = auto based on GPU memory)
        # ============================================================================
        # GPU MEMORY AWARENESS: Limit pairs based on available GPU RAM
        # ============================================================================
        # Empirically, ~4.4MB per pair at batch=128 (autograd graph is huge!)
        # 24GB GPU @ batch=128 → ~550 pairs; 95GB @ batch=256 → ~1000 pairs
        gpu_memory_gb: float = None,  # GPU memory override (None = auto-detect)
        batch_size_hint: int = 128,  # Expected batch size for memory estimation
        # ============================================================================
        # FUSION MODE: (Legacy parameter - kept for API compatibility)
        # With embedding arithmetic removed, always 1 token per pair
        # ============================================================================
        use_fusion: bool = True,  # Legacy - always 1 token per pair now
        # ============================================================================
        # TYPE-AWARE OPERATIONS: Enable temporal ops for timestamp columns
        # ============================================================================
        col_types: Optional[Dict[str, Any]] = None,  # Column types for type-aware ops (ColumnType enum)
        type_aware_config: Optional["TypeAwareOpsConfig"] = None,  # Config for type-aware ops (None = default enabled)
        # ============================================================================
        # VISUALIZATION: Output directory for lift visualizations
        # ============================================================================
        viz_output_dir: Optional[str] = None,  # Directory for lift visualizations (None = disabled)
    ):
        super().__init__()
        
        self.d_model = d_model
        self.col_names = col_names_in_order
        self.n_cols = len(col_names_in_order)
        self.exploration_epochs = exploration_epochs
        self.top_k_fraction = top_k_fraction
        self.enable_operation_pruning = enable_operation_pruning
        self.progressive_pruning = progressive_pruning
        self.pairs_to_prune_per_epoch = pairs_to_prune_per_epoch
        self.ucb_alpha = ucb_alpha  # UCB exploration parameter
        self.use_ucb_selection = use_ucb_selection  # Phase 2: Enable UCB selection
        self.edge_dropout_prob = edge_dropout_prob  # Edge dropout probability (free regularization)
        self.confidence_weight_n0 = confidence_weight_n0  # Confidence weighting threshold for lift scores
        self.max_column_fraction = max_column_fraction  # Max fraction of active pool any single column can occupy
        self.viz_output_dir = viz_output_dir  # Directory for lift visualizations

        # ============================================================================
        # TYPE-AWARE OPERATIONS (temporal, set, scalar combinations)
        # ============================================================================
        self.col_types = col_types

        # Import TypeAwareOpsConfig and create default if not provided
        from featrix.neural.type_aware_ops_config import TypeAwareOpsConfig
        if type_aware_config is None:
            # Check for environment variable override
            self.type_aware_config = TypeAwareOpsConfig.from_env()
        else:
            self.type_aware_config = type_aware_config

        # Track type-aware ops usage statistics
        self._type_aware_stats = {
            'set_timestamp_pairs': 0,
            'scalar_timestamp_pairs': 0,
            'set_set_pairs': 0,
            'set_scalar_pairs': 0,
            'scalar_scalar_pairs': 0,
            'email_domain_pairs': 0,  # Email × Domain direct pairs
            'email_domain_set_pairs': 0,
            'email_domain_scalar_pairs': 0,
            'email_domain_timestamp_pairs': 0,
            'email_domain_string_pairs': 0,
            'url_set_pairs': 0,
            'url_scalar_pairs': 0,
            'url_timestamp_pairs': 0,
            'url_string_pairs': 0,
            'generic_pairs': 0,
            'total_forward_calls': 0,
        }
        # Track type-aware ops errors (graceful degradation)
        # When an op fails, we log once and fall back to generic token
        self._type_aware_errors: Dict[str, int] = {}  # op_name -> error count
        self._type_aware_errors_logged: Set[str] = set()  # ops that have been logged already
        # Expected counts (populated by _log_type_aware_summary)
        self._expected_type_aware_pairs = {}

        # Track output magnitude statistics for diagnostics
        # Helps identify if type-aware ops produce different scales than generic ops
        self._magnitude_stats = {
            'generic_fused': {'sum': 0.0, 'sum_sq': 0.0, 'count': 0, 'max': 0.0},
            'set_timestamp': {'sum': 0.0, 'sum_sq': 0.0, 'count': 0, 'max': 0.0},
            'scalar_timestamp': {'sum': 0.0, 'sum_sq': 0.0, 'count': 0, 'max': 0.0},
            'set_set': {'sum': 0.0, 'sum_sq': 0.0, 'count': 0, 'max': 0.0},
            'set_scalar': {'sum': 0.0, 'sum_sq': 0.0, 'count': 0, 'max': 0.0},
            'scalar_scalar': {'sum': 0.0, 'sum_sq': 0.0, 'count': 0, 'max': 0.0},
            'email_domain': {'sum': 0.0, 'sum_sq': 0.0, 'count': 0, 'max': 0.0},
            'email_domain_set': {'sum': 0.0, 'sum_sq': 0.0, 'count': 0, 'max': 0.0},
        }
        self._log_magnitude_every_n = 100  # Log every N forward calls

        # Track per-op-type gradient statistics (for measuring effectiveness)
        # Gradient magnitude indicates how much each op type contributes to learning
        self._op_type_gradient_stats = {
            'generic_fused': {'grad_sum': 0.0, 'grad_sum_sq': 0.0, 'grad_count': 0, 'grad_max': 0.0},
            'set_timestamp': {'grad_sum': 0.0, 'grad_sum_sq': 0.0, 'grad_count': 0, 'grad_max': 0.0},
            'scalar_timestamp': {'grad_sum': 0.0, 'grad_sum_sq': 0.0, 'grad_count': 0, 'grad_max': 0.0},
            'set_set': {'grad_sum': 0.0, 'grad_sum_sq': 0.0, 'grad_count': 0, 'grad_max': 0.0},
            'set_scalar': {'grad_sum': 0.0, 'grad_sum_sq': 0.0, 'grad_count': 0, 'grad_max': 0.0},
            'scalar_scalar': {'grad_sum': 0.0, 'grad_sum_sq': 0.0, 'grad_count': 0, 'grad_max': 0.0},
            'email_domain': {'grad_sum': 0.0, 'grad_sum_sq': 0.0, 'grad_count': 0, 'grad_max': 0.0},
            'email_domain_set': {'grad_sum': 0.0, 'grad_sum_sq': 0.0, 'grad_count': 0, 'grad_max': 0.0},
        }
        # Store tokens for gradient check by op type
        self._op_type_tokens_for_grad: Dict[str, List[torch.Tensor]] = {
            'generic_fused': [],
            'set_timestamp': [],
            'scalar_timestamp': [],
            'set_set': [],
            'set_scalar': [],
            'scalar_scalar': [],
            'email_domain': [],
            'email_domain_set': [],
        }

        # Build column index -> type mapping for type detection
        self.col_idx_to_type: Dict[int, Any] = {}
        if col_types is not None:
            from featrix.neural.model_config import ColumnType
            for idx, name in enumerate(col_names_in_order):
                self.col_idx_to_type[idx] = col_types.get(name, ColumnType.FREE_STRING)

        # Initialize type-aware ops (conditionally based on config)
        self.temporal_ops = None
        self.set_timestamp_ops = None
        self.scalar_timestamp_ops = None
        self.set_set_ops = None
        self.set_scalar_ops = None
        self.scalar_scalar_ops = None
        # Email/Domain ops (P3)
        self.email_domain_ops = None  # Email × Domain direct relationship
        self.email_domain_set_ops = None
        self.email_domain_scalar_ops = None
        self.email_domain_timestamp_ops = None
        self.email_domain_string_ops = None
        # URL ops (P4)
        self.url_set_ops = None
        self.url_scalar_ops = None
        self.url_timestamp_ops = None
        self.url_string_ops = None

        if col_types is not None and self.type_aware_config.enable_all_type_aware:
            from featrix.neural.model_config import ColumnType

            # Count column types for logging
            n_timestamps = sum(1 for ct in col_types.values() if ct == ColumnType.TIMESTAMP)
            n_sets = sum(1 for ct in col_types.values() if ct == ColumnType.SET)
            n_scalars = sum(1 for ct in col_types.values() if ct == ColumnType.SCALAR)
            n_emails = sum(1 for ct in col_types.values() if ct == ColumnType.EMAIL)
            n_domains = sum(1 for ct in col_types.values() if ct == ColumnType.DOMAIN)
            n_strings = sum(1 for ct in col_types.values() if ct == ColumnType.FREE_STRING)
            n_urls = sum(1 for ct in col_types.values() if ct == ColumnType.URL)
            n_email_domains = n_emails + n_domains  # Combined for ops

            # Temporal ops (existing)
            if self.type_aware_config.enable_timestamp_timestamp or self.type_aware_config.enable_string_timestamp:
                if n_timestamps > 0:
                    try:
                        from featrix.neural.temporal_relationship_ops import TemporalRelationshipOps
                        self.temporal_ops = TemporalRelationshipOps(
                            d_model=d_model,
                            col_types=col_types,
                            col_names_in_order=col_names_in_order,
                        )
                        logger.info(f"🕐 TemporalRelationshipOps enabled ({n_timestamps} timestamp cols)")
                    except ImportError as e:
                        logger.warning(f"⚠️  Could not import TemporalRelationshipOps: {e}")

            # Set × Timestamp ops (P0)
            if self.type_aware_config.enable_set_timestamp and n_sets > 0 and n_timestamps > 0:
                try:
                    from featrix.neural.set_timestamp_ops import SetTimestampOps
                    self.set_timestamp_ops = SetTimestampOps(
                        d_model=d_model,
                        config=self.type_aware_config,
                    )
                    logger.info(f"🕐 SetTimestampOps enabled ({n_sets} sets × {n_timestamps} timestamps)")
                except ImportError as e:
                    logger.warning(f"⚠️  Could not import SetTimestampOps: {e}")

            # Scalar × Timestamp ops (P0)
            if self.type_aware_config.enable_scalar_timestamp and n_scalars > 0 and n_timestamps > 0:
                try:
                    from featrix.neural.scalar_timestamp_ops import ScalarTimestampOps
                    self.scalar_timestamp_ops = ScalarTimestampOps(
                        d_model=d_model,
                        config=self.type_aware_config,
                    )
                    logger.info(f"🕐 ScalarTimestampOps enabled ({n_scalars} scalars × {n_timestamps} timestamps)")
                except ImportError as e:
                    logger.warning(f"⚠️  Could not import ScalarTimestampOps: {e}")

            # Set × Set ops (P1)
            if self.type_aware_config.enable_set_set and n_sets > 1:
                try:
                    from featrix.neural.set_set_ops import SetSetOps
                    self.set_set_ops = SetSetOps(
                        d_model=d_model,
                        config=self.type_aware_config,
                    )
                    logger.info(f"📊 SetSetOps enabled ({n_sets} sets)")
                except ImportError as e:
                    logger.warning(f"⚠️  Could not import SetSetOps: {e}")

            # Set × Scalar ops (P1)
            if self.type_aware_config.enable_set_scalar and n_sets > 0 and n_scalars > 0:
                try:
                    from featrix.neural.set_scalar_ops import SetScalarOps
                    self.set_scalar_ops = SetScalarOps(
                        d_model=d_model,
                        config=self.type_aware_config,
                    )
                    logger.info(f"📊 SetScalarOps enabled ({n_sets} sets × {n_scalars} scalars)")
                except ImportError as e:
                    logger.warning(f"⚠️  Could not import SetScalarOps: {e}")

            # Scalar × Scalar ops (P2)
            if self.type_aware_config.enable_scalar_scalar_enhanced and n_scalars > 1:
                try:
                    from featrix.neural.scalar_scalar_ops import ScalarScalarOps
                    self.scalar_scalar_ops = ScalarScalarOps(
                        d_model=d_model,
                        config=self.type_aware_config,
                    )
                    logger.info(f"📊 ScalarScalarOps enabled ({n_scalars} scalars)")
                except ImportError as e:
                    logger.warning(f"⚠️  Could not import ScalarScalarOps: {e}")

            # Strategy-aware Scalar × Scalar ops (experimental)
            # Check both type_aware_config flag AND global sphere_config flag
            from featrix.neural.sphere_config import get_config
            sphere_config = get_config()
            use_strategy_aware = (
                self.type_aware_config.enable_strategy_aware_scalar_scalar or
                sphere_config.get("use_strategy_aware_relationships", False)
            )
            if use_strategy_aware and n_scalars > 1:
                try:
                    from featrix.neural.strategy_scalar_scalar_ops import StrategyAwareScalarScalarOps
                    top_k = self.type_aware_config.strategy_aware_top_k
                    if top_k is None:
                        top_k = sphere_config.get("strategy_aware_top_k", 4)
                    self.strategy_scalar_scalar_ops = StrategyAwareScalarScalarOps(
                        d_model=d_model,
                        top_k=top_k,
                        config=self.type_aware_config,
                    )
                    logger.info(f"🎯 StrategyAwareScalarScalarOps enabled ({n_scalars} scalars, top_k={top_k})")
                except ImportError as e:
                    logger.warning(f"⚠️  Could not import StrategyAwareScalarScalarOps: {e}")

            # Strategy-Aware String × Scalar ops
            use_strategy_string_scalar = (
                self.type_aware_config.enable_strategy_aware_string_scalar or
                sphere_config.get("use_strategy_aware_relationships", False)
            )
            if use_strategy_string_scalar and n_strings > 0 and n_scalars > 0:
                try:
                    from featrix.neural.strategy_string_scalar_ops import StrategyAwareStringScalarOps
                    top_k = self.type_aware_config.strategy_aware_top_k
                    if top_k is None:
                        top_k = sphere_config.get("strategy_aware_top_k", 4)
                    self.strategy_string_scalar_ops = StrategyAwareStringScalarOps(
                        d_model=d_model,
                        top_k=top_k,
                        config=self.type_aware_config,
                    )
                    logger.info(f"🎯 StrategyAwareStringScalarOps enabled ({n_strings} strings × {n_scalars} scalars, top_k={top_k})")
                except ImportError as e:
                    logger.warning(f"⚠️  Could not import StrategyAwareStringScalarOps: {e}")

            # Strategy-Aware Set × Scalar ops
            use_strategy_set_scalar = (
                self.type_aware_config.enable_strategy_aware_set_scalar or
                sphere_config.get("use_strategy_aware_relationships", False)
            )
            if use_strategy_set_scalar and n_sets > 0 and n_scalars > 0:
                try:
                    from featrix.neural.strategy_set_scalar_ops import StrategyAwareSetScalarOps
                    top_k = self.type_aware_config.strategy_aware_top_k
                    if top_k is None:
                        top_k = sphere_config.get("strategy_aware_top_k", 4)
                    self.strategy_set_scalar_ops = StrategyAwareSetScalarOps(
                        d_model=d_model,
                        top_k=top_k,
                        config=self.type_aware_config,
                    )
                    logger.info(f"🎯 StrategyAwareSetScalarOps enabled ({n_sets} sets × {n_scalars} scalars, top_k={top_k})")
                except ImportError as e:
                    logger.warning(f"⚠️  Could not import StrategyAwareSetScalarOps: {e}")

            # Email × Domain ops (P3) - direct Email-to-Domain relationship
            if n_emails > 0 and n_domains > 0:
                try:
                    from featrix.neural.email_domain_ops import EmailDomainOps
                    self.email_domain_ops = EmailDomainOps(
                        d_model=d_model,
                        config=self.type_aware_config,
                    )
                    logger.info(f"📧 EmailDomainOps enabled ({n_emails} emails × {n_domains} domains)")
                except ImportError as e:
                    logger.warning(f"⚠️  Could not import EmailDomainOps: {e}")

            # Email/Domain × Set ops (P3)
            if self.type_aware_config.enable_email_domain_set and n_email_domains > 0 and n_sets > 0:
                try:
                    from featrix.neural.email_domain_ops import EmailDomainSetOps
                    self.email_domain_set_ops = EmailDomainSetOps(
                        d_model=d_model,
                        config=self.type_aware_config,
                    )
                    logger.info(f"📧 EmailDomainSetOps enabled ({n_email_domains} email/domain × {n_sets} sets)")
                except ImportError as e:
                    logger.warning(f"⚠️  Could not import EmailDomainSetOps: {e}")

            # Email/Domain × Scalar ops (P3)
            if self.type_aware_config.enable_email_domain_scalar and n_email_domains > 0 and n_scalars > 0:
                try:
                    from featrix.neural.email_domain_ops import EmailDomainScalarOps
                    self.email_domain_scalar_ops = EmailDomainScalarOps(
                        d_model=d_model,
                        config=self.type_aware_config,
                    )
                    logger.info(f"📧 EmailDomainScalarOps enabled ({n_email_domains} email/domain × {n_scalars} scalars)")
                except ImportError as e:
                    logger.warning(f"⚠️  Could not import EmailDomainScalarOps: {e}")

            # Email/Domain × Timestamp ops (P3)
            if self.type_aware_config.enable_email_domain_timestamp and n_email_domains > 0 and n_timestamps > 0:
                try:
                    from featrix.neural.email_domain_ops import EmailDomainTimestampOps
                    self.email_domain_timestamp_ops = EmailDomainTimestampOps(
                        d_model=d_model,
                        config=self.type_aware_config,
                    )
                    logger.info(f"📧 EmailDomainTimestampOps enabled ({n_email_domains} email/domain × {n_timestamps} timestamps)")
                except ImportError as e:
                    logger.warning(f"⚠️  Could not import EmailDomainTimestampOps: {e}")

            # Email/Domain × String ops (P3)
            if self.type_aware_config.enable_email_domain_string and n_email_domains > 0 and n_strings > 0:
                try:
                    from featrix.neural.email_domain_ops import EmailDomainStringOps
                    self.email_domain_string_ops = EmailDomainStringOps(
                        d_model=d_model,
                        config=self.type_aware_config,
                    )
                    logger.info(f"📧 EmailDomainStringOps enabled ({n_email_domains} email/domain × {n_strings} strings)")
                except ImportError as e:
                    logger.warning(f"⚠️  Could not import EmailDomainStringOps: {e}")

            # URL × Set ops (P4)
            if self.type_aware_config.enable_url_set and n_urls > 0 and n_sets > 0:
                try:
                    from featrix.neural.url_ops import URLSetOps
                    self.url_set_ops = URLSetOps(
                        d_model=d_model,
                        config=self.type_aware_config,
                    )
                    logger.info(f"🔗 URLSetOps enabled ({n_urls} URLs × {n_sets} sets)")
                except ImportError as e:
                    logger.warning(f"⚠️  Could not import URLSetOps: {e}")

            # URL × Scalar ops (P4)
            if self.type_aware_config.enable_url_scalar and n_urls > 0 and n_scalars > 0:
                try:
                    from featrix.neural.url_ops import URLScalarOps
                    self.url_scalar_ops = URLScalarOps(
                        d_model=d_model,
                        config=self.type_aware_config,
                    )
                    logger.info(f"🔗 URLScalarOps enabled ({n_urls} URLs × {n_scalars} scalars)")
                except ImportError as e:
                    logger.warning(f"⚠️  Could not import URLScalarOps: {e}")

            # URL × Timestamp ops (P4)
            if self.type_aware_config.enable_url_timestamp and n_urls > 0 and n_timestamps > 0:
                try:
                    from featrix.neural.url_ops import URLTimestampOps
                    self.url_timestamp_ops = URLTimestampOps(
                        d_model=d_model,
                        config=self.type_aware_config,
                    )
                    logger.info(f"🔗 URLTimestampOps enabled ({n_urls} URLs × {n_timestamps} timestamps)")
                except ImportError as e:
                    logger.warning(f"⚠️  Could not import URLTimestampOps: {e}")

            # URL × String ops (P4)
            if self.type_aware_config.enable_url_string and n_urls > 0 and n_strings > 0:
                try:
                    from featrix.neural.url_ops import URLStringOps
                    self.url_string_ops = URLStringOps(
                        d_model=d_model,
                        config=self.type_aware_config,
                    )
                    logger.info(f"🔗 URLStringOps enabled ({n_urls} URLs × {n_strings} strings)")
                except ImportError as e:
                    logger.warning(f"⚠️  Could not import URLStringOps: {e}")

            # Log config
            self.type_aware_config.log_config(prefix="   ")

            # ========================================================================
            # TYPE-AWARE PAIR SCORERS
            # ========================================================================
            # Create PairScorer instances for each type-aware op to track lift and prune
            from featrix.neural.pair_scorer import PairScorer

            self._type_aware_scorers: Dict[str, PairScorer] = {}

            # SetSet scorer
            if self.set_set_ops is not None and n_sets > 1:
                set_set_pairs = [
                    (i, j) for i in range(self.n_cols) for j in range(i + 1, self.n_cols)
                    if self.col_idx_to_type.get(i) == ColumnType.SET and self.col_idx_to_type.get(j) == ColumnType.SET
                ]
                self._type_aware_scorers['set_set'] = PairScorer(
                    name='set_set',
                    max_pairs=self.type_aware_config.max_set_set_pairs,
                    exploration_epochs=exploration_epochs,
                    top_k_fraction=top_k_fraction,
                )
                self._type_aware_scorers['set_set'].initialize_pairs(set_set_pairs)

            # ScalarScalar scorer
            if self.scalar_scalar_ops is not None and n_scalars > 1:
                scalar_scalar_pairs = [
                    (i, j) for i in range(self.n_cols) for j in range(i + 1, self.n_cols)
                    if self.col_idx_to_type.get(i) == ColumnType.SCALAR and self.col_idx_to_type.get(j) == ColumnType.SCALAR
                ]
                self._type_aware_scorers['scalar_scalar'] = PairScorer(
                    name='scalar_scalar',
                    max_pairs=self.type_aware_config.max_scalar_scalar_pairs,
                    exploration_epochs=exploration_epochs,
                    top_k_fraction=top_k_fraction,
                )
                self._type_aware_scorers['scalar_scalar'].initialize_pairs(scalar_scalar_pairs)

            # SetScalar scorer
            if self.set_scalar_ops is not None and n_sets > 0 and n_scalars > 0:
                set_scalar_pairs = []
                for i in range(self.n_cols):
                    for j in range(self.n_cols):
                        if i == j:
                            continue
                        ti, tj = self.col_idx_to_type.get(i), self.col_idx_to_type.get(j)
                        if (ti == ColumnType.SET and tj == ColumnType.SCALAR) or (ti == ColumnType.SCALAR and tj == ColumnType.SET):
                            pair = (min(i, j), max(i, j))
                            if pair not in set_scalar_pairs:
                                set_scalar_pairs.append(pair)
                self._type_aware_scorers['set_scalar'] = PairScorer(
                    name='set_scalar',
                    max_pairs=self.type_aware_config.max_set_scalar_pairs,
                    exploration_epochs=exploration_epochs,
                    top_k_fraction=top_k_fraction,
                )
                self._type_aware_scorers['set_scalar'].initialize_pairs(set_scalar_pairs)

            # SetTimestamp scorer
            if self.set_timestamp_ops is not None and n_sets > 0 and n_timestamps > 0:
                set_timestamp_pairs = []
                for i in range(self.n_cols):
                    for j in range(self.n_cols):
                        if i == j:
                            continue
                        ti, tj = self.col_idx_to_type.get(i), self.col_idx_to_type.get(j)
                        if (ti == ColumnType.SET and tj == ColumnType.TIMESTAMP) or (ti == ColumnType.TIMESTAMP and tj == ColumnType.SET):
                            pair = (min(i, j), max(i, j))
                            if pair not in set_timestamp_pairs:
                                set_timestamp_pairs.append(pair)
                self._type_aware_scorers['set_timestamp'] = PairScorer(
                    name='set_timestamp',
                    max_pairs=self.type_aware_config.max_set_timestamp_pairs,
                    exploration_epochs=exploration_epochs,
                    top_k_fraction=top_k_fraction,
                )
                self._type_aware_scorers['set_timestamp'].initialize_pairs(set_timestamp_pairs)

            # ScalarTimestamp scorer
            if self.scalar_timestamp_ops is not None and n_scalars > 0 and n_timestamps > 0:
                scalar_timestamp_pairs = []
                for i in range(self.n_cols):
                    for j in range(self.n_cols):
                        if i == j:
                            continue
                        ti, tj = self.col_idx_to_type.get(i), self.col_idx_to_type.get(j)
                        if (ti == ColumnType.SCALAR and tj == ColumnType.TIMESTAMP) or (ti == ColumnType.TIMESTAMP and tj == ColumnType.SCALAR):
                            pair = (min(i, j), max(i, j))
                            if pair not in scalar_timestamp_pairs:
                                scalar_timestamp_pairs.append(pair)
                self._type_aware_scorers['scalar_timestamp'] = PairScorer(
                    name='scalar_timestamp',
                    max_pairs=self.type_aware_config.max_scalar_timestamp_pairs,
                    exploration_epochs=exploration_epochs,
                    top_k_fraction=top_k_fraction,
                )
                self._type_aware_scorers['scalar_timestamp'].initialize_pairs(scalar_timestamp_pairs)

            # Email×Domain scorer (direct email-to-domain relationship)
            if self.email_domain_ops is not None and n_emails > 0 and n_domains > 0:
                email_domain_pairs = []
                for i in range(self.n_cols):
                    for j in range(self.n_cols):
                        if i == j:
                            continue
                        ti, tj = self.col_idx_to_type.get(i), self.col_idx_to_type.get(j)
                        # Email × Domain pairs (either direction)
                        if (ti == ColumnType.EMAIL and tj == ColumnType.DOMAIN) or (ti == ColumnType.DOMAIN and tj == ColumnType.EMAIL):
                            pair = (min(i, j), max(i, j))
                            if pair not in email_domain_pairs:
                                email_domain_pairs.append(pair)
                self._type_aware_scorers['email_domain'] = PairScorer(
                    name='email_domain',
                    max_pairs=100,  # Reasonable limit for email × domain pairs
                    exploration_epochs=exploration_epochs,
                    top_k_fraction=top_k_fraction,
                )
                self._type_aware_scorers['email_domain'].initialize_pairs(email_domain_pairs)

            # EmailDomain×Set scorer
            if self.email_domain_set_ops is not None and n_email_domains > 0 and n_sets > 0:
                email_domain_set_pairs = []
                for i in range(self.n_cols):
                    for j in range(self.n_cols):
                        if i == j:
                            continue
                        ti, tj = self.col_idx_to_type.get(i), self.col_idx_to_type.get(j)
                        is_email_domain_i = ti in (ColumnType.EMAIL, ColumnType.DOMAIN)
                        is_email_domain_j = tj in (ColumnType.EMAIL, ColumnType.DOMAIN)
                        if (is_email_domain_i and tj == ColumnType.SET) or (ti == ColumnType.SET and is_email_domain_j):
                            pair = (min(i, j), max(i, j))
                            if pair not in email_domain_set_pairs:
                                email_domain_set_pairs.append(pair)
                self._type_aware_scorers['email_domain_set'] = PairScorer(
                    name='email_domain_set',
                    max_pairs=self.type_aware_config.max_email_domain_set_pairs,
                    exploration_epochs=exploration_epochs,
                    top_k_fraction=top_k_fraction,
                )
                self._type_aware_scorers['email_domain_set'].initialize_pairs(email_domain_set_pairs)

            # EmailDomain×Scalar scorer
            if self.email_domain_scalar_ops is not None and n_email_domains > 0 and n_scalars > 0:
                email_domain_scalar_pairs = []
                for i in range(self.n_cols):
                    for j in range(self.n_cols):
                        if i == j:
                            continue
                        ti, tj = self.col_idx_to_type.get(i), self.col_idx_to_type.get(j)
                        is_email_domain_i = ti in (ColumnType.EMAIL, ColumnType.DOMAIN)
                        is_email_domain_j = tj in (ColumnType.EMAIL, ColumnType.DOMAIN)
                        if (is_email_domain_i and tj == ColumnType.SCALAR) or (ti == ColumnType.SCALAR and is_email_domain_j):
                            pair = (min(i, j), max(i, j))
                            if pair not in email_domain_scalar_pairs:
                                email_domain_scalar_pairs.append(pair)
                self._type_aware_scorers['email_domain_scalar'] = PairScorer(
                    name='email_domain_scalar',
                    max_pairs=self.type_aware_config.max_email_domain_scalar_pairs,
                    exploration_epochs=exploration_epochs,
                    top_k_fraction=top_k_fraction,
                )
                self._type_aware_scorers['email_domain_scalar'].initialize_pairs(email_domain_scalar_pairs)

            # EmailDomain×Timestamp scorer
            if self.email_domain_timestamp_ops is not None and n_email_domains > 0 and n_timestamps > 0:
                email_domain_timestamp_pairs = []
                for i in range(self.n_cols):
                    for j in range(self.n_cols):
                        if i == j:
                            continue
                        ti, tj = self.col_idx_to_type.get(i), self.col_idx_to_type.get(j)
                        is_email_domain_i = ti in (ColumnType.EMAIL, ColumnType.DOMAIN)
                        is_email_domain_j = tj in (ColumnType.EMAIL, ColumnType.DOMAIN)
                        if (is_email_domain_i and tj == ColumnType.TIMESTAMP) or (ti == ColumnType.TIMESTAMP and is_email_domain_j):
                            pair = (min(i, j), max(i, j))
                            if pair not in email_domain_timestamp_pairs:
                                email_domain_timestamp_pairs.append(pair)
                self._type_aware_scorers['email_domain_timestamp'] = PairScorer(
                    name='email_domain_timestamp',
                    max_pairs=self.type_aware_config.max_email_domain_timestamp_pairs,
                    exploration_epochs=exploration_epochs,
                    top_k_fraction=top_k_fraction,
                )
                self._type_aware_scorers['email_domain_timestamp'].initialize_pairs(email_domain_timestamp_pairs)

            # EmailDomain×String scorer
            if self.email_domain_string_ops is not None and n_email_domains > 0 and n_strings > 0:
                email_domain_string_pairs = []
                for i in range(self.n_cols):
                    for j in range(self.n_cols):
                        if i == j:
                            continue
                        ti, tj = self.col_idx_to_type.get(i), self.col_idx_to_type.get(j)
                        is_email_domain_i = ti in (ColumnType.EMAIL, ColumnType.DOMAIN)
                        is_email_domain_j = tj in (ColumnType.EMAIL, ColumnType.DOMAIN)
                        if (is_email_domain_i and tj == ColumnType.FREE_STRING) or (ti == ColumnType.FREE_STRING and is_email_domain_j):
                            pair = (min(i, j), max(i, j))
                            if pair not in email_domain_string_pairs:
                                email_domain_string_pairs.append(pair)
                self._type_aware_scorers['email_domain_string'] = PairScorer(
                    name='email_domain_string',
                    max_pairs=self.type_aware_config.max_email_domain_string_pairs,
                    exploration_epochs=exploration_epochs,
                    top_k_fraction=top_k_fraction,
                )
                self._type_aware_scorers['email_domain_string'].initialize_pairs(email_domain_string_pairs)

            # URL×Set scorer
            if self.url_set_ops is not None and n_urls > 0 and n_sets > 0:
                url_set_pairs = []
                for i in range(self.n_cols):
                    for j in range(self.n_cols):
                        if i == j:
                            continue
                        ti, tj = self.col_idx_to_type.get(i), self.col_idx_to_type.get(j)
                        if (ti == ColumnType.URL and tj == ColumnType.SET) or (ti == ColumnType.SET and tj == ColumnType.URL):
                            pair = (min(i, j), max(i, j))
                            if pair not in url_set_pairs:
                                url_set_pairs.append(pair)
                self._type_aware_scorers['url_set'] = PairScorer(
                    name='url_set',
                    max_pairs=self.type_aware_config.max_url_set_pairs,
                    exploration_epochs=exploration_epochs,
                    top_k_fraction=top_k_fraction,
                )
                self._type_aware_scorers['url_set'].initialize_pairs(url_set_pairs)

            # URL×Scalar scorer
            if self.url_scalar_ops is not None and n_urls > 0 and n_scalars > 0:
                url_scalar_pairs = []
                for i in range(self.n_cols):
                    for j in range(self.n_cols):
                        if i == j:
                            continue
                        ti, tj = self.col_idx_to_type.get(i), self.col_idx_to_type.get(j)
                        if (ti == ColumnType.URL and tj == ColumnType.SCALAR) or (ti == ColumnType.SCALAR and tj == ColumnType.URL):
                            pair = (min(i, j), max(i, j))
                            if pair not in url_scalar_pairs:
                                url_scalar_pairs.append(pair)
                self._type_aware_scorers['url_scalar'] = PairScorer(
                    name='url_scalar',
                    max_pairs=self.type_aware_config.max_url_scalar_pairs,
                    exploration_epochs=exploration_epochs,
                    top_k_fraction=top_k_fraction,
                )
                self._type_aware_scorers['url_scalar'].initialize_pairs(url_scalar_pairs)

            # URL×Timestamp scorer
            if self.url_timestamp_ops is not None and n_urls > 0 and n_timestamps > 0:
                url_timestamp_pairs = []
                for i in range(self.n_cols):
                    for j in range(self.n_cols):
                        if i == j:
                            continue
                        ti, tj = self.col_idx_to_type.get(i), self.col_idx_to_type.get(j)
                        if (ti == ColumnType.URL and tj == ColumnType.TIMESTAMP) or (ti == ColumnType.TIMESTAMP and tj == ColumnType.URL):
                            pair = (min(i, j), max(i, j))
                            if pair not in url_timestamp_pairs:
                                url_timestamp_pairs.append(pair)
                self._type_aware_scorers['url_timestamp'] = PairScorer(
                    name='url_timestamp',
                    max_pairs=self.type_aware_config.max_url_timestamp_pairs,
                    exploration_epochs=exploration_epochs,
                    top_k_fraction=top_k_fraction,
                )
                self._type_aware_scorers['url_timestamp'].initialize_pairs(url_timestamp_pairs)

            # URL×String scorer
            if self.url_string_ops is not None and n_urls > 0 and n_strings > 0:
                url_string_pairs = []
                for i in range(self.n_cols):
                    for j in range(self.n_cols):
                        if i == j:
                            continue
                        ti, tj = self.col_idx_to_type.get(i), self.col_idx_to_type.get(j)
                        if (ti == ColumnType.URL and tj == ColumnType.FREE_STRING) or (ti == ColumnType.FREE_STRING and tj == ColumnType.URL):
                            pair = (min(i, j), max(i, j))
                            if pair not in url_string_pairs:
                                url_string_pairs.append(pair)
                self._type_aware_scorers['url_string'] = PairScorer(
                    name='url_string',
                    max_pairs=self.type_aware_config.max_url_string_pairs,
                    exploration_epochs=exploration_epochs,
                    top_k_fraction=top_k_fraction,
                )
                self._type_aware_scorers['url_string'].initialize_pairs(url_string_pairs)

            logger.info(f"   🎯 Type-aware scorers: {list(self._type_aware_scorers.keys())}")

        # ============================================================================
        # GPU-AWARE PAIR LIMITING
        # ============================================================================
        # Auto-detect GPU memory if not provided
        if gpu_memory_gb is None:
            gpu_memory_gb = _get_gpu_memory_gb()
        
        # Compute safe max pairs based on GPU memory
        computed_max_pairs = _compute_max_pairs_for_gpu(
            gpu_memory_gb=gpu_memory_gb,
            n_cols=self.n_cols,
            batch_size=batch_size_hint,
            d_model=d_model,
        )
        
        # Use provided max_coarse_pairs if given, otherwise use computed limit
        if max_coarse_pairs is not None:
            self.max_coarse_pairs = max_coarse_pairs
        else:
            self.max_coarse_pairs = computed_max_pairs
        
        # Also limit chunk size for non-exploration (post-pruning) phases
        self.max_pairs_per_chunk = computed_max_pairs
        
        # Log GPU-aware settings
        gpu_str = f"{gpu_memory_gb:.1f}GB" if gpu_memory_gb else "CPU"
        logger.info(f"   🔧 GPU-aware limits ({gpu_str}): max_pairs_per_chunk={self.max_pairs_per_chunk}, "
                   f"max_coarse_pairs={self.max_coarse_pairs}")
        
        # Coarse exploration settings
        self.coarse_exploration_dim = coarse_exploration_dim
        
        # Legacy: fusion mode flag kept for API compatibility
        # With embedding arithmetic removed, always 1 token per pair
        self.use_fusion = use_fusion
        self.ops_per_pair = 1  # Always 1 (presence pattern only)
        
        # History-aware exploration (uses feature suggestion infrastructure)
        self._session_id: Optional[str] = None
        self._known_good_pairs: Set[Tuple[int, int]] = set()
        self._known_bad_pairs: Set[Tuple[int, int]] = set()
        self._history_loaded = False
        
        # Pair scoring system for meta-learning
        # Track scores: +1 when kept (significant), -1 when culled (worst performing)
        self._pair_scores: Dict[Tuple[int, int], int] = {}
        self._dataset_hash: Optional[str] = None
        
        # Track current epoch (updated externally)
        self.current_epoch = 0
        
        # Store gradient norms captured right after backward() (before zero_grad/step clears them)
        self._stored_grad_norms: Dict[str, float] = {}  # {op_name: grad_norm}
        
        # Track dropout stats per epoch (for coverage reporting)
        self._epoch_dropout_stats = {
            'total_edges_before': 0,
            'total_edges_after': 0,
            'total_dropped': 0,
            'steps_with_dropout': 0,
        }
        
        # Track active edges per step (for coverage reporting)
        self._epoch_active_edges = []  # List of active directed edge counts per step
        
        # Generate all unique pairs (i < j to avoid duplicates)
        # This gives us N*(N-1)/2 pairs, not N*N
        self.all_pairs = []
        for i in range(self.n_cols):
            for j in range(i + 1, self.n_cols):
                self.all_pairs.append((i, j))

        # ============================================================================
        # LOG TYPE-AWARE OPS SUMMARY (must be after all_pairs is populated)
        # ============================================================================
        self._log_type_aware_summary(col_types)

        # ============================================================================
        # DIRECTED PAIRS: Store as directed edges for proper lift tracking
        # ============================================================================
        # For lift calculation, we need to track (i->j) and (j->i) separately
        # since lift(i->j) measures effect on j when paired with i
        # This is different from the undirected pair (i,j) used for relationship tokens
        self._directed_pairs: Set[Tuple[int, int]] = set()
        for i in range(self.n_cols):
            for j in range(self.n_cols):
                if i != j:
                    self._directed_pairs.add((i, j))
        
        # Support thresholds (split by action type)
        # Scale based on expected observations per pair over a time window
        
        # Parameters:
        # N = n_cols (columns)
        # M = total possible undirected pairs = N*(N-1)/2
        # B = active pairs per batch (limited by GPU memory, ~500-1000)
        # W = time window in steps/batches (how many steps to consider "recent")
        # Expected observations per pair: E[n_ij] = (B * W) / M
        
        total_undirected_pairs = len(self.all_pairs)  # M = N*(N-1)/2
        active_pairs_per_batch = self.max_pairs_per_chunk  # B (limited by GPU memory)
        
        # Time window: consider last W steps/batches as "recent enough"
        # For embedding space training, ~2000 steps ≈ 1-2 epochs (depends on dataset size)
        # Use a conservative window that ensures pairs get observed if they're in active set
        time_window_steps = 2000  # W: steps over which we expect to see pairs
        
        # Compute expected observations per pair in this window
        # Formula: E[n_ij] = (B * W) / M
        # Where:
        #   B = active undirected pairs per batch (limited by GPU memory)
        #   W = time window in steps
        #   M = total possible undirected pairs = N*(N-1)/2
        
        if total_undirected_pairs > 0:
            # B is already undirected pairs per batch (from max_pairs_per_chunk)
            # This accounts for GPU memory limits, not per-column quotas
            # If per-column exploration floor is active, actual B might be higher,
            # but we use the GPU-limited B as the conservative estimate
            expected_obs_per_pair = (active_pairs_per_batch * time_window_steps) / total_undirected_pairs
        else:
            expected_obs_per_pair = float('inf')  # No pairs, thresholds don't matter

        # Scale thresholds based on expected observations, with clamps
        # Clamps prevent thresholds from exploding (small N) or going to zero (large N)

        # TRACK: small multiple of expected (but at least 2-3)
        # Handle infinity: if expected_obs_per_pair is inf, use default minimum
        if math.isinf(expected_obs_per_pair):
            track_from_expected = 2
        else:
            track_from_expected = max(2, int(0.3 * expected_obs_per_pair))
        # Clamp: [2, 20]
        self.MIN_SUPPORT_TRACK = max(2, min(20, track_from_expected))

        # RANK: enough samples to stabilize
        # Use smooth ramp based on column count - simple and predictable
        # For small column counts: start low (15) to allow relationships to be ranked early
        # For large column counts: ramp up to higher values (more pairs = need more samples)
        # Get GPU memory for cap calculation
        actual_gpu_memory = gpu_memory_gb if gpu_memory_gb else (_get_gpu_memory_gb() or 24.0)
        cap = 200 if actual_gpu_memory >= 96 else 200  # Same cap for now, can tune later
        self.MIN_SUPPORT_RANK = ramp_plateau(
            self.n_cols,
            start=15,  # Start value for small column counts
            cap=cap,   # Cap value for large column counts
            C0=20,     # Ramp begins at 20 columns
            C1=100,    # Ramp reaches cap at 100 columns
        )
        # Ensure minimum of 10
        self.MIN_SUPPORT_RANK = max(10, self.MIN_SUPPORT_RANK)

        # PRUNE: rank threshold + safety margin (2.5x expected, but at least 20)
        # Handle infinity: if expected_obs_per_pair is inf, use default minimum
        if math.isinf(expected_obs_per_pair):
            prune_from_expected = 20
        else:
            prune_from_expected = max(20, int(2.5 * expected_obs_per_pair))
        # Clamp: [20, 500] - will be adjusted adaptively based on actual observations
        self.MIN_SUPPORT_PRUNE = max(20, min(500, prune_from_expected))
        
        # Store initial values for reference
        self._initial_min_support_rank = self.MIN_SUPPORT_RANK
        
        # Track when we last checked for adaptive adjustment (to avoid doing it every step)
        self._last_adaptive_check_step = -1
        self._adaptive_check_interval = 100  # Check every 100 steps
        
        # Log scaling decision if significant
        if expected_obs_per_pair < 100 or expected_obs_per_pair > 1:
            logger.info(f"📊 Support thresholds scaled based on expected observations:")
            logger.info(f"   Total undirected pairs (M): {total_undirected_pairs}")
            logger.info(f"   Active pairs per batch (B): {active_pairs_per_batch}")
            logger.info(f"   Time window (W): {time_window_steps} steps")
            logger.info(f"   Expected obs per pair: E[n_ij] = (B*W)/M = {expected_obs_per_pair:.2f}")
            logger.info(f"   MIN_SUPPORT_TRACK: {self.MIN_SUPPORT_TRACK} (clamped from {track_from_expected})")
            logger.info(f"   MIN_SUPPORT_RANK: {self.MIN_SUPPORT_RANK} (from ramp_plateau: C0=20, C1=100)")
            logger.info(f"   MIN_SUPPORT_PRUNE: {self.MIN_SUPPORT_PRUNE} (clamped from {prune_from_expected})")
        
        # Pair statistics for directed edges (i -> j)
        # Track: n_ij (count), lift_ema (EMA of lift), source tracking
        # Structure: {(i,j): {'n': int, 'lift_ema': float, 'last_step': int, 'source_counts': {'null': int, 'bootstrap': int}}}
        self._pair_stats: Dict[Tuple[int, int], Dict] = {}
        self._pair_lift_alpha = 0.1  # EMA decay for lift (0.05-0.2 range, adjust based on noise)
        
        # Track active pairs per batch for lift computation
        # Reset each batch, accumulates pairs from all forward() calls in the batch
        self._active_pairs_this_batch: Set[Tuple[int, int]] = set()
        
        # Track last step's active pairs for exploit candidate fallback
        self._last_step_active_pairs: Optional[Set[Tuple[int, int]]] = None
        
        # Initialize scores for ALL pairs - persists throughout the entire run
        # Score meaning: positive = kept more often, negative = culled more often
        for pair in self.all_pairs:
            self._pair_scores[pair] = 0
        
        logger.info(f"🔗 DynamicRelationshipExtractor: {len(self.all_pairs)} unique pairs "
                   f"({self.n_cols}*({self.n_cols}-1)/2)")
        logger.info(f"   Exploration epochs: {exploration_epochs}")
        logger.info(f"   Top-k fraction: {top_k_fraction} ({int(self.n_cols * top_k_fraction)} partners per column)")
        logger.info(f"   Generic op: presence pattern only (type-aware ops handle semantics)")
        logger.info(f"   Tokens during exploration: {len(self.all_pairs)}")

        # Log scalability info
        if len(self.all_pairs) > self.max_pairs_per_chunk:
            logger.info(f"   ⚡ SCALABILITY MODE: Chunked computation (≤{self.max_pairs_per_chunk} pairs per chunk)")
            logger.info(f"      This allows training with {self.n_cols} columns ({len(self.all_pairs)} pairs)")

        # ============================================================================
        # GENERIC OP: Presence Pattern Only
        # ============================================================================
        # The ONLY generic operation is presence/null pattern correlation.
        # Semantic operations (arithmetic, attention, etc.) are handled by type-aware ops:
        #   - ScalarScalarOps: ratio, difference, product for numeric pairs
        #   - SetSetOps: co-occurrence attention for categorical pairs
        #   - SetScalarOps: scalar-conditioned gating for mixed pairs
        #   - Timestamp ops: temporal patterns
        #
        # This design is cleaner because:
        # 1. Embedding arithmetic (multiply, add, divide on embeddings) is meaningless
        # 2. Type-aware ops use actual data semantics (raw values, not embeddings)
        # 3. Presence pattern captures the universal signal: null correlation

        self.presence_mlp = nn.Sequential(
            nn.Linear(4, d_model // 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model // 2, d_model),
            nn.LayerNorm(d_model),  # Match type-aware ops output normalization
        )

        # NOTE: Embedding arithmetic MLPs (multiply, add, cosine, abs_diff, subtract, divide)
        # have been REMOVED. These operations on embeddings are semantically meaningless:
        # - Embedding dimensions don't correspond to interpretable features
        # - Adding/multiplying embeddings doesn't produce meaningful relationships
        # - Type-aware ops use actual RAW DATA (not embeddings) for semantic operations:
        #   - ScalarScalarOps: ratio, difference on actual numeric values
        #   - SetSetOps: co-occurrence patterns using actual category values
        #   - Timestamp ops: temporal deltas using actual datetime values
        #
        # The ONLY generic operation is presence/null pattern correlation, which captures
        # the universal signal of which columns tend to be present/missing together.
        
        # ============================================================================
        # NULL RELATIONSHIP TOKEN: Represents "no relationship" baseline
        # ============================================================================
        # Contextual NULL: base + column-specific context via MLP
        # This allows NULL to represent "no relationship for this column's context"
        # rather than a global bias vector
        self.null_relationship_base = nn.Parameter(torch.zeros(1, d_model))
        self.null_relationship_mlp = nn.Sequential(
            nn.Linear(d_model, d_model // 2),
            nn.ReLU(),
            nn.Linear(d_model // 2, d_model)
        )
        self.null_scale = 0.1  # Scale control to prevent NULL from dominating early (anneal later)
        self.null_layer_norm = nn.LayerNorm(d_model)  # Keep NULL comparable to relationship tokens
        
        # NULL baseline tracking (EMA per column)
        self._null_baseline_ema: Dict[str, float] = {}  # {col_name: EMA of NULL-only loss}
        self._null_baseline_source: Dict[str, str] = {}  # {col_name: "null" or "bootstrap"}
        self._null_baseline_n: Dict[str, int] = {}  # {col_name: count of observations}
        self._null_baseline_alpha = 0.1  # EMA decay rate
        if self.n_cols > 0:
            self._null_sample_rate = 20.0 / self.n_cols
        else:
            self._null_sample_rate = 1.0  # No columns, use 100%
        # Adaptive evaluation frequency (more frequent early in training)
        self._null_every_steps_early = 5   # Every 5 steps early (high LR)
        self._null_every_steps_late = 10   # Every 10 steps later (stable)
        self._null_early_epochs = 20       # Use early frequency for first N epochs
        self._step_counter = 0  # Track steps for NULL baseline evaluation
        self._null_evaluation_pending = False  # Flag to trigger NULL-only evaluation
        self._null_batch_mask_modes = []  # Track mode (True=null, False=normal) for each mask in current batch
        self._null_baseline_losses_this_batch: Dict[str, List[float]] = {}  # Accumulate losses across masks
        self._null_baseline_mask_count = 0  # Track how many masks processed this batch
        
        # Track contribution of each pair (for pruning)
        # Key: (i, j) where i < j -> contribution score
        self.pair_contributions = {}
        for pair in self.all_pairs:
            self.pair_contributions[pair] = 0.0
        
        # After exploration, store pruned pairs per column (old hard pruning method)
        self.pruned_pairs_per_column: Optional[Dict[int, List[int]]] = None
        self._pruned_pairs_list: Optional[List[Tuple[int, int]]] = None
        
        # Progressive pruning: track disabled pairs (set of (i,j) tuples)
        
        # LEARNING TRACKING: Track if operation MLPs are learning
        # Store weight snapshots to measure change over time
        self._weight_snapshots = {}  # {epoch: {op_name: weight_norm}}
        self._weight_deltas = {}  # {op_name: [delta_per_epoch]}
        
        self.disabled_pairs: set = set()
        
        # Calculate minimum relationships to always keep (safety floor)
        if min_relationships_to_keep is None:
            # Keep at least max(5, n_cols/2) most important relationships
            # This ensures each column keeps relationships with ~half of other columns at minimum
            # Prevents over-pruning asymmetric relationships where easy columns provide context for hard ones
            min_keep = max(5, self.n_cols // 2)
            self.min_relationships_to_keep = min(min_keep, self.n_cols)
        else:
            self.min_relationships_to_keep = min_relationships_to_keep
        
        # Calculate how many pairs to disable per epoch (auto-calculate if not specified)
        if self.progressive_pruning:
            total_pairs = len(self.all_pairs)
            
            # Edge case: 0 or 1 columns means no pairs to prune
            if total_pairs == 0:
                self.target_pruning_epochs = 0
                self.pairs_to_prune_per_epoch = 0
                logger.info("🔪 Progressive pruning: disabled (no pairs with < 2 columns)")
            else:
                # Auto-calculate target_pruning_epochs if not specified
                if target_pruning_epochs is None:
                    # Assume 15 epochs after exploration (conservative estimate)
                    target_pruning_epochs = 15
                self.target_pruning_epochs = target_pruning_epochs
                
                # Calculate target remaining pairs
                target_remaining = int(total_pairs * self.top_k_fraction)
                # But never go below the minimum floor
                target_remaining = max(target_remaining, self.min_relationships_to_keep)
                pairs_to_remove = total_pairs - target_remaining
                
                # Calculate pairs to prune per epoch: pairs_to_remove / target_epochs, min 1
                if self.pairs_to_prune_per_epoch is None:
                    self.pairs_to_prune_per_epoch = max(1, pairs_to_remove // target_pruning_epochs)
                
                logger.info(
                    f"🔪 Progressive pruning enabled:"
                )
                logger.info(
                    f"   Will disable ~{self.pairs_to_prune_per_epoch} pairs/epoch starting at epoch {exploration_epochs}"
                )
                logger.info(
                    f"   Target: {target_remaining}/{total_pairs} pairs ({100*target_remaining/total_pairs:.1f}%)"
                )
                logger.info(
                    f"   Minimum floor: {self.min_relationships_to_keep} most important pairs (always kept)"
                )
        
        # For gradient tracking during exploration
        self._contribution_ema_alpha = 0.1  # Exponential moving average factor
        
        # Store tokens with pair info for post-backward gradient checking
        # Format: [(pair, token), ...] - populated during forward, consumed after backward
        self._tokens_for_gradient_check: List[Tuple[Tuple[int, int], torch.Tensor]] = []
        
        # Batch counter for throttling logs (log every N batches)
        self._batch_counter = 0
        self._log_every_n_batches = 20  # Log gradient updates every 20 batches
        
        # Track operation-specific contributions (for analysis)
        # NOTE: Embedding arithmetic ops have been removed - only presence pattern remains
        self.operation_contributions = {
            'presence': 0.0,
        }
        
        # Track contribution history for stability analysis
        self.contribution_history: List[Dict[Tuple[int, int], float]] = []
        
        # Store mutual information estimates (for potential future use)
        self.col_mi_estimates: Dict[str, Optional[float]] = {}
        self.joint_mi_estimate: Optional[float] = None
        
        # CRITICAL: Store per-column marginal losses (NEW METRIC for importance)
        # This tells us which columns are HARD to predict
        # Relationships between hard columns are most valuable
        self.col_marginal_losses: Dict[str, float] = {}  # {col_name: avg_marginal_loss}
        
        # ============================================================================
        # STAGE 1: HISTORY TRACKING
        # ============================================================================
        # Track which pairs were active in which epochs
        self._pair_active_epochs: Dict[Tuple[int, int], Set[int]] = {}
        # Track per-column losses over time
        self._column_loss_history: Dict[str, List[float]] = {}
        # Track all epochs
        self._all_epochs: Set[int] = set()
        
        # ============================================================================
        # STAGE 2: CAUSAL IMPORTANCE SCORING
        # ============================================================================
        self.causal_scorer = CausalRelationshipScorer(
            col_names=col_names_in_order,
            window=5,              # Lookback window for improvement rate
            decay_rate=0.95,       # Exponential decay for recency
            lcb_confidence=1.96,   # 95% confidence interval
            min_observations=3,    # Minimum observations for trust
        )
        logger.info("   🧮 Causal relationship scorer initialized")
        logger.info(f"      Window={5}, Decay={0.95}, LCB confidence={1.96}")
        
        # ============================================================================
        # STAGE 3: VALIDATION
        # ============================================================================
        self.validator = ImportanceScoringValidator(col_names=col_names_in_order)
        logger.info("   ✅ Importance scoring validator initialized")
    
    # ============================================================================
    # TYPE-AWARE OPS LOGGING
    # ============================================================================

    def _log_type_aware_summary(self, col_types: Optional[Dict[str, Any]]) -> None:
        """Log comprehensive summary of type-aware ops configuration and expected usage."""
        from featrix.neural.sphere_config import get_config

        enabled = get_config().get_enable_type_aware_ops()

        if enabled:
            logger.info("🧠 TYPE-AWARE OPS: ENABLED")
        else:
            logger.info("🧠 TYPE-AWARE OPS: DISABLED (generic multiplication only)")
            return

        if col_types is None:
            logger.info("   ⚠️  No column types provided - all pairs will use generic ops")
            return

        from featrix.neural.model_config import ColumnType

        # Count column types
        n_sets = sum(1 for ct in col_types.values() if ct == ColumnType.SET)
        n_scalars = sum(1 for ct in col_types.values() if ct == ColumnType.SCALAR)
        n_timestamps = sum(1 for ct in col_types.values() if ct == ColumnType.TIMESTAMP)
        n_strings = sum(1 for ct in col_types.values() if ct == ColumnType.FREE_STRING)
        n_emails = sum(1 for ct in col_types.values() if ct == ColumnType.EMAIL)
        n_domains = sum(1 for ct in col_types.values() if ct == ColumnType.DOMAIN)
        n_urls = sum(1 for ct in col_types.values() if ct == ColumnType.URL)
        n_email_domains = n_emails + n_domains
        n_other = len(col_types) - n_sets - n_scalars - n_timestamps - n_strings - n_emails - n_domains - n_urls

        logger.info(f"   Column types: {n_sets} sets, {n_scalars} scalars, {n_timestamps} timestamps, {n_strings} strings, {n_email_domains} email/domain, {n_urls} URLs, {n_other} other")

        # Count potential pairs for each type-aware op
        n_set_ts_pairs = n_sets * n_timestamps
        n_scalar_ts_pairs = n_scalars * n_timestamps
        n_set_set_pairs = n_sets * (n_sets - 1) // 2 if n_sets > 1 else 0
        n_set_scalar_pairs = n_sets * n_scalars
        n_scalar_scalar_pairs = n_scalars * (n_scalars - 1) // 2 if n_scalars > 1 else 0
        n_email_domain_pairs = n_emails * n_domains  # Email × Domain direct pairs
        n_email_domain_set_pairs = n_email_domains * n_sets
        n_email_domain_scalar_pairs = n_email_domains * n_scalars
        n_email_domain_timestamp_pairs = n_email_domains * n_timestamps
        n_email_domain_string_pairs = n_email_domains * n_strings
        n_url_set_pairs = n_urls * n_sets
        n_url_scalar_pairs = n_urls * n_scalars
        n_url_timestamp_pairs = n_urls * n_timestamps
        n_url_string_pairs = n_urls * n_strings

        # Count which ops are actually enabled
        ops_summary = []
        if self.set_timestamp_ops is not None:
            ops_summary.append(f"SetTimestamp: {n_set_ts_pairs} pairs")
        if self.scalar_timestamp_ops is not None:
            ops_summary.append(f"ScalarTimestamp: {n_scalar_ts_pairs} pairs")
        if self.set_set_ops is not None:
            ops_summary.append(f"SetSet: {n_set_set_pairs} pairs")
        if self.set_scalar_ops is not None:
            ops_summary.append(f"SetScalar: {n_set_scalar_pairs} pairs")
        if self.scalar_scalar_ops is not None:
            ops_summary.append(f"ScalarScalar: {n_scalar_scalar_pairs} pairs")
        if self.email_domain_ops is not None:
            ops_summary.append(f"EmailDomain: {n_email_domain_pairs} pairs")
        if self.email_domain_set_ops is not None:
            ops_summary.append(f"EmailDomainSet: {n_email_domain_set_pairs} pairs")
        if self.email_domain_scalar_ops is not None:
            ops_summary.append(f"EmailDomainScalar: {n_email_domain_scalar_pairs} pairs")
        if self.email_domain_timestamp_ops is not None:
            ops_summary.append(f"EmailDomainTimestamp: {n_email_domain_timestamp_pairs} pairs")
        if self.email_domain_string_ops is not None:
            ops_summary.append(f"EmailDomainString: {n_email_domain_string_pairs} pairs")
        if self.url_set_ops is not None:
            ops_summary.append(f"URLSet: {n_url_set_pairs} pairs")
        if self.url_scalar_ops is not None:
            ops_summary.append(f"URLScalar: {n_url_scalar_pairs} pairs")
        if self.url_timestamp_ops is not None:
            ops_summary.append(f"URLTimestamp: {n_url_timestamp_pairs} pairs")
        if self.url_string_ops is not None:
            ops_summary.append(f"URLString: {n_url_string_pairs} pairs")

        total_type_aware = (
            (n_set_ts_pairs if self.set_timestamp_ops else 0) +
            (n_scalar_ts_pairs if self.scalar_timestamp_ops else 0) +
            (n_set_set_pairs if self.set_set_ops else 0) +
            (n_set_scalar_pairs if self.set_scalar_ops else 0) +
            (n_scalar_scalar_pairs if self.scalar_scalar_ops else 0) +
            (n_email_domain_pairs if self.email_domain_ops else 0) +
            (n_email_domain_set_pairs if self.email_domain_set_ops else 0) +
            (n_email_domain_scalar_pairs if self.email_domain_scalar_ops else 0) +
            (n_email_domain_timestamp_pairs if self.email_domain_timestamp_ops else 0) +
            (n_email_domain_string_pairs if self.email_domain_string_ops else 0) +
            (n_url_set_pairs if self.url_set_ops else 0) +
            (n_url_scalar_pairs if self.url_scalar_ops else 0) +
            (n_url_timestamp_pairs if self.url_timestamp_ops else 0) +
            (n_url_string_pairs if self.url_string_ops else 0)
        )
        total_pairs = len(self.all_pairs)
        generic_pairs = total_pairs - total_type_aware

        if ops_summary:
            logger.info(f"   Active type-aware ops: {', '.join(ops_summary)}")
        else:
            logger.info("   ⚠️  No type-aware ops active (missing column types or ops disabled)")

        pct = (total_type_aware / total_pairs * 100) if total_pairs > 0 else 0
        logger.info(f"   Type-aware pairs: {total_type_aware}/{total_pairs} ({pct:.1f}%)")
        logger.info(f"   Generic pairs: {generic_pairs}/{total_pairs} ({100-pct:.1f}%)")

        # Store expected counts for later validation
        self._expected_type_aware_pairs = {
            'set_timestamp': n_set_ts_pairs if self.set_timestamp_ops else 0,
            'scalar_timestamp': n_scalar_ts_pairs if self.scalar_timestamp_ops else 0,
            'set_set': n_set_set_pairs if self.set_set_ops else 0,
            'set_scalar': n_set_scalar_pairs if self.set_scalar_ops else 0,
            'scalar_scalar': n_scalar_scalar_pairs if self.scalar_scalar_ops else 0,
            'email_domain': n_email_domain_pairs if self.email_domain_ops else 0,
            'email_domain_set': n_email_domain_set_pairs if self.email_domain_set_ops else 0,
            'email_domain_scalar': n_email_domain_scalar_pairs if self.email_domain_scalar_ops else 0,
            'email_domain_timestamp': n_email_domain_timestamp_pairs if self.email_domain_timestamp_ops else 0,
            'email_domain_string': n_email_domain_string_pairs if self.email_domain_string_ops else 0,
            'url_set': n_url_set_pairs if self.url_set_ops else 0,
            'url_scalar': n_url_scalar_pairs if self.url_scalar_ops else 0,
            'url_timestamp': n_url_timestamp_pairs if self.url_timestamp_ops else 0,
            'url_string': n_url_string_pairs if self.url_string_ops else 0,
            'total_type_aware': total_type_aware,
            'generic': generic_pairs,
        }

    def log_lift_contribution_by_type(self) -> None:
        """
        Log aggregate statistics about lift contribution by operation type.
        Shows which type-aware ops are contributing the most to embedding quality.
        """
        if not hasattr(self, '_type_aware_scorers') or not self._type_aware_scorers:
            return

        # Collect lift data by type
        type_stats = {}  # type_name -> {'pairs': count, 'lifts': list[float], 'importances': list[float]}

        # Calculate importance scores for all active pairs
        active_pairs = [p for p in self.all_pairs if p not in self.disabled_pairs]
        importance_scores = self._compute_causal_importance(active_pairs)

        # Categorize each pair by type
        for (i, j), importance in importance_scores.items():
            type_op = self._get_type_aware_op_for_pair(i, j)

            if type_op not in type_stats:
                type_stats[type_op] = {'pairs': 0, 'lifts': [], 'importances': []}

            type_stats[type_op]['pairs'] += 1
            type_stats[type_op]['importances'].append(importance)

            # Get lift values
            stats_ij = self._pair_stats.get((i, j), {})
            stats_ji = self._pair_stats.get((j, i), {})
            lift_ij = stats_ij.get('lift_ema', 0.0) if stats_ij.get('lift_ema') is not None else 0.0
            lift_ji = stats_ji.get('lift_ema', 0.0) if stats_ji.get('lift_ema') is not None else 0.0
            max_lift = max(lift_ij, lift_ji)
            type_stats[type_op]['lifts'].append(max_lift)

        if not type_stats:
            return

        # Calculate totals for percentage
        total_importance = sum(sum(s['importances']) for s in type_stats.values())

        # Sort by total importance contribution (descending)
        sorted_types = sorted(
            type_stats.items(),
            key=lambda x: sum(x[1]['importances']),
            reverse=True
        )

        logger.info(f"📊 Lift Contribution by Operation Type:")
        logger.info(f"   {'Type':<16}  {'Pairs':>6}  {'Avg Lift':>9}  {'Max Lift':>9}  {'Avg Imp':>9}  {'% of Total':>10}")
        logger.info(f"   {'-'*16}  {'-'*6}  {'-'*9}  {'-'*9}  {'-'*9}  {'-'*10}")

        for type_name, stats in sorted_types:
            pairs = stats['pairs']
            lifts = stats['lifts']
            importances = stats['importances']

            avg_lift = sum(lifts) / len(lifts) if lifts else 0.0
            max_lift = max(lifts) if lifts else 0.0
            avg_imp = sum(importances) / len(importances) if importances else 0.0
            pct = (sum(importances) / total_importance * 100) if total_importance > 0 else 0.0

            logger.info(f"   {type_name:<16}  {pairs:>6}  {avg_lift:>9.4f}  {max_lift:>9.4f}  {avg_imp:>9.4f}  {pct:>9.1f}%")

    def log_type_aware_stats(self, reset: bool = True) -> None:
        """Log statistics about type-aware ops usage since last reset."""
        stats = self._type_aware_stats
        total = stats['total_forward_calls']

        if total == 0:
            logger.info("🧠 Type-aware stats: No forward calls recorded")
            return

        type_aware_total = (
            stats['set_timestamp_pairs'] +
            stats['scalar_timestamp_pairs'] +
            stats['set_set_pairs'] +
            stats['set_scalar_pairs'] +
            stats['scalar_scalar_pairs']
        )
        generic_total = stats['generic_pairs']
        all_pairs = type_aware_total + generic_total

        logger.info(f"🧠 Type-aware ops usage ({total} forward calls):")
        if stats['set_timestamp_pairs'] > 0:
            logger.info(f"   SetTimestamp: {stats['set_timestamp_pairs']} pairs")
        if stats['scalar_timestamp_pairs'] > 0:
            logger.info(f"   ScalarTimestamp: {stats['scalar_timestamp_pairs']} pairs")
        if stats['set_set_pairs'] > 0:
            logger.info(f"   SetSet: {stats['set_set_pairs']} pairs")
        if stats['set_scalar_pairs'] > 0:
            logger.info(f"   SetScalar: {stats['set_scalar_pairs']} pairs")
        if stats['scalar_scalar_pairs'] > 0:
            logger.info(f"   ScalarScalar: {stats['scalar_scalar_pairs']} pairs")

        if all_pairs > 0:
            pct = type_aware_total / all_pairs * 100
            logger.info(f"   Total: {type_aware_total} type-aware, {generic_total} generic ({pct:.1f}% type-aware)")

        if reset:
            for key in stats:
                stats[key] = 0

    def _track_magnitude(self, op_name: str, tensor: torch.Tensor) -> None:
        """Track magnitude statistics for a tensor (used for diagnostics).

        Tracks running statistics (mean, std, max) to identify if different
        operation types produce different output scales.

        Also retains gradient for type-aware ops to track their learning contribution.
        """
        with torch.no_grad():
            # Compute L2 norm of each sample in batch
            norms = tensor.norm(p=2, dim=-1)  # (batch,)
            batch_sum = norms.sum().item()
            batch_sum_sq = (norms ** 2).sum().item()
            batch_max = norms.max().item()
            batch_count = norms.numel()

            stats = self._magnitude_stats[op_name]
            stats['sum'] += batch_sum
            stats['sum_sq'] += batch_sum_sq
            stats['count'] += batch_count
            stats['max'] = max(stats['max'], batch_max)

        # Retain gradient for type-aware ops (sample 1 per batch to reduce memory)
        if op_name in self._op_type_tokens_for_grad and tensor.requires_grad:
            # Only keep a small sample to avoid memory issues
            if len(self._op_type_tokens_for_grad[op_name]) < 10:
                tensor.retain_grad()
                self._op_type_tokens_for_grad[op_name].append(tensor)

    def log_magnitude_stats(self, reset: bool = True) -> None:
        """Log magnitude statistics comparing type-aware vs generic ops.

        This helps diagnose if type-aware ops produce different scales,
        which could cause gradient instability.
        """
        logger.info("📊 Output Magnitude Statistics (L2 norm per sample):")

        results = []
        for op_name, stats in self._magnitude_stats.items():
            if stats['count'] > 0:
                mean = stats['sum'] / stats['count']
                variance = (stats['sum_sq'] / stats['count']) - (mean ** 2)
                std = max(0, variance) ** 0.5
                results.append((op_name, mean, std, stats['max'], stats['count']))

        if not results:
            logger.info("   No magnitude data collected")
            return

        # Sort by mean magnitude (descending) to highlight large ones
        results.sort(key=lambda x: x[1], reverse=True)

        for op_name, mean, std, max_val, count in results:
            logger.info(f"   {op_name:20s}: mean={mean:7.3f}, std={std:7.3f}, max={max_val:7.3f} (n={count})")

        # Compute ratio between type-aware and generic
        generic_mean = None
        type_aware_means = []
        for op_name, mean, std, max_val, count in results:
            if op_name == 'generic_fused':
                generic_mean = mean
            else:
                type_aware_means.append((op_name, mean))

        if generic_mean and generic_mean > 0 and type_aware_means:
            logger.info("   Magnitude ratios vs generic_fused:")
            for op_name, mean in type_aware_means:
                ratio = mean / generic_mean
                warning = " ⚠️ MISMATCH" if ratio > 2.0 or ratio < 0.5 else ""
                logger.info(f"      {op_name}: {ratio:.2f}x{warning}")

        if reset:
            for stats in self._magnitude_stats.values():
                stats['sum'] = 0.0
                stats['sum_sq'] = 0.0
                stats['count'] = 0
                stats['max'] = 0.0

    def update_op_type_gradients(self) -> None:
        """
        Update per-op-type gradient statistics after loss.backward().

        Call this AFTER loss.backward() but BEFORE optimizer.step()/zero_grad().
        This tracks how much each type-aware op contributes to learning.
        """
        for op_name, tokens in self._op_type_tokens_for_grad.items():
            for tensor in tokens:
                if tensor.grad is not None:
                    grad_mag = tensor.grad.abs().mean().item()
                    stats = self._op_type_gradient_stats[op_name]
                    stats['grad_sum'] += grad_mag
                    stats['grad_sum_sq'] += grad_mag ** 2
                    stats['grad_count'] += 1
                    stats['grad_max'] = max(stats['grad_max'], grad_mag)
            # Clear tokens for next batch
            tokens.clear()

    def log_type_aware_scorer_stats(self) -> None:
        """Log statistics from type-aware pair scorers."""
        if not hasattr(self, '_type_aware_scorers') or not self._type_aware_scorers:
            return

        logger.info("🎯 Type-Aware Pair Scorer Statistics:")
        for name, scorer in self._type_aware_scorers.items():
            stats = scorer.get_stats_summary()
            logger.info(
                f"   {name:20s}: {stats['active_pairs']}/{stats['total_pairs']} active "
                f"(max={scorer.max_pairs or 'unlimited'}), "
                f"lift: mean={stats['mean_lift']:.4f}, "
                f"range=[{stats['min_lift']:.4f}, {stats['max_lift']:.4f}]"
            )

        # DEBUG: Log routing stats
        if hasattr(self, '_debug_type_aware_routing'):
            r = self._debug_type_aware_routing
            logger.info(f"   🔍 DEBUG routing: calls={r['calls']}, routed={r['routed']}, "
                       f"no_op_type={r['no_op_type']}, no_scorer={r['no_scorer']}, not_in_pairs={r['not_in_pairs']}")

    def log_op_type_gradient_stats(self, reset: bool = True) -> None:
        """
        Log per-op-type gradient statistics to show which ops are learning effectively.

        Higher gradient magnitudes indicate the op is contributing more to learning.
        """
        logger.info("🎯 Type-Aware Op Gradient Statistics (contribution to learning):")

        results = []
        for op_name, stats in self._op_type_gradient_stats.items():
            if stats['grad_count'] > 0:
                mean = stats['grad_sum'] / stats['grad_count']
                variance = (stats['grad_sum_sq'] / stats['grad_count']) - (mean ** 2)
                std = max(0, variance) ** 0.5
                results.append((op_name, mean, std, stats['grad_max'], stats['grad_count']))

        if not results:
            logger.info("   No gradient data collected (call update_op_type_gradients() after backward)")
            return

        # Sort by mean gradient (descending) - higher = more contribution
        results.sort(key=lambda x: x[1], reverse=True)

        # Find generic baseline for comparison
        generic_mean = None
        for op_name, mean, std, max_val, count in results:
            if op_name == 'generic_fused':
                generic_mean = mean
                break

        for op_name, mean, std, max_val, count in results:
            # Comparison to generic baseline
            if generic_mean and generic_mean > 0 and op_name != 'generic_fused':
                ratio = mean / generic_mean
                if ratio > 1.2:
                    verdict = f"✅ +{(ratio-1)*100:.0f}% vs generic"
                elif ratio < 0.8:
                    verdict = f"⚠️ {(ratio-1)*100:.0f}% vs generic"
                else:
                    verdict = "≈ generic"
            else:
                verdict = "(baseline)" if op_name == 'generic_fused' else ""

            logger.info(f"   {op_name:20s}: grad_mean={mean:.6f}, std={std:.6f}, max={max_val:.6f} (n={count}) {verdict}")

        if reset:
            for stats in self._op_type_gradient_stats.values():
                stats['grad_sum'] = 0.0
                stats['grad_sum_sq'] = 0.0
                stats['grad_count'] = 0
                stats['grad_max'] = 0.0

    # ============================================================================
    # TYPE DETECTION HELPERS (for type-aware relationship ops)
    # ============================================================================

    def is_type_aware_pair_active(self, op_type: str, i: int, j: int) -> bool:
        """Check if a type-aware pair is active (not pruned by its scorer).

        Args:
            op_type: One of 'set_set', 'scalar_scalar', 'set_scalar', 'set_timestamp', 'scalar_timestamp'
            i, j: Column indices

        Returns:
            True if the pair is active (should be computed), False if pruned
        """
        if not hasattr(self, '_type_aware_scorers'):
            return True  # No scorers = all pairs active

        scorer = self._type_aware_scorers.get(op_type)
        if scorer is None:
            return True  # No scorer for this type = all pairs active

        # Normalize pair to (min, max) order
        pair = (min(i, j), max(i, j))

        # Check if pair is in the active set
        active_pairs = scorer.get_active_pairs()
        return pair in active_pairs

    def get_active_type_aware_pairs(self, op_type: str) -> Set[Tuple[int, int]]:
        """Get set of active pairs for a type-aware op.

        Args:
            op_type: One of 'set_set', 'scalar_scalar', 'set_scalar', 'set_timestamp', 'scalar_timestamp'

        Returns:
            Set of active (i, j) pairs
        """
        if not hasattr(self, '_type_aware_scorers'):
            return set()

        scorer = self._type_aware_scorers.get(op_type)
        if scorer is None:
            return set()

        return set(scorer.get_active_pairs())

    def get_op_type_for_pair(self, i: int, j: int) -> Optional[str]:
        """Get the operation type for a pair based on column types.

        Args:
            i, j: Column indices (order doesn't matter, will be canonicalized)

        Returns:
            Operation type string ('set_set', 'set_scalar', 'scalar_scalar', etc.)
            or None if no type-aware op applies (falls back to generic)
        """
        from featrix.neural.model_config import ColumnType

        ti = self.col_idx_to_type.get(i)
        tj = self.col_idx_to_type.get(j)

        if ti is None or tj is None:
            return None

        # Check each type combination
        # SetSet
        if ti == ColumnType.SET and tj == ColumnType.SET:
            return 'set_set' if 'set_set' in getattr(self, '_type_aware_scorers', {}) else None

        # ScalarScalar
        if ti == ColumnType.SCALAR and tj == ColumnType.SCALAR:
            return 'scalar_scalar' if 'scalar_scalar' in getattr(self, '_type_aware_scorers', {}) else None

        # SetScalar (either order)
        if (ti == ColumnType.SET and tj == ColumnType.SCALAR) or (ti == ColumnType.SCALAR and tj == ColumnType.SET):
            return 'set_scalar' if 'set_scalar' in getattr(self, '_type_aware_scorers', {}) else None

        # SetTimestamp (either order)
        if (ti == ColumnType.SET and tj == ColumnType.TIMESTAMP) or (ti == ColumnType.TIMESTAMP and tj == ColumnType.SET):
            return 'set_timestamp' if 'set_timestamp' in getattr(self, '_type_aware_scorers', {}) else None

        # ScalarTimestamp (either order)
        if (ti == ColumnType.SCALAR and tj == ColumnType.TIMESTAMP) or (ti == ColumnType.TIMESTAMP and tj == ColumnType.SCALAR):
            return 'scalar_timestamp' if 'scalar_timestamp' in getattr(self, '_type_aware_scorers', {}) else None

        # EmailDomain combinations (EMAIL or DOMAIN types)
        is_email_domain_i = ti in (ColumnType.EMAIL, ColumnType.DOMAIN)
        is_email_domain_j = tj in (ColumnType.EMAIL, ColumnType.DOMAIN)
        if is_email_domain_i or is_email_domain_j:
            other_type = tj if is_email_domain_i else ti
            if other_type == ColumnType.SET:
                return 'email_domain_set' if 'email_domain_set' in getattr(self, '_type_aware_scorers', {}) else None
            if other_type == ColumnType.SCALAR:
                return 'email_domain_scalar' if 'email_domain_scalar' in getattr(self, '_type_aware_scorers', {}) else None
            if other_type == ColumnType.TIMESTAMP:
                return 'email_domain_timestamp' if 'email_domain_timestamp' in getattr(self, '_type_aware_scorers', {}) else None
            if other_type == ColumnType.FREE_STRING:
                return 'email_domain_string' if 'email_domain_string' in getattr(self, '_type_aware_scorers', {}) else None

        # URL combinations
        if (ti == ColumnType.URL or tj == ColumnType.URL):
            other_type = tj if ti == ColumnType.URL else ti
            if other_type == ColumnType.SET:
                return 'url_set' if 'url_set' in getattr(self, '_type_aware_scorers', {}) else None
            if other_type == ColumnType.SCALAR:
                return 'url_scalar' if 'url_scalar' in getattr(self, '_type_aware_scorers', {}) else None
            if other_type == ColumnType.TIMESTAMP:
                return 'url_timestamp' if 'url_timestamp' in getattr(self, '_type_aware_scorers', {}) else None
            if other_type == ColumnType.FREE_STRING:
                return 'url_string' if 'url_string' in getattr(self, '_type_aware_scorers', {}) else None

        return None

    def is_set_timestamp_pair(self, i: int, j: int) -> Tuple[bool, Optional[int], Optional[int]]:
        """
        Check if one column is SET and other is TIMESTAMP.

        Returns:
            (is_set_ts_pair, set_col_idx, timestamp_col_idx)
        """
        from featrix.neural.model_config import ColumnType
        type_i = self.col_idx_to_type.get(i)
        type_j = self.col_idx_to_type.get(j)

        if type_i == ColumnType.SET and type_j == ColumnType.TIMESTAMP:
            return True, i, j
        elif type_i == ColumnType.TIMESTAMP and type_j == ColumnType.SET:
            return True, j, i
        return False, None, None

    def is_scalar_timestamp_pair(self, i: int, j: int) -> Tuple[bool, Optional[int], Optional[int]]:
        """
        Check if one column is SCALAR and other is TIMESTAMP.

        Returns:
            (is_scalar_ts_pair, scalar_col_idx, timestamp_col_idx)
        """
        from featrix.neural.model_config import ColumnType
        type_i = self.col_idx_to_type.get(i)
        type_j = self.col_idx_to_type.get(j)

        if type_i == ColumnType.SCALAR and type_j == ColumnType.TIMESTAMP:
            return True, i, j
        elif type_i == ColumnType.TIMESTAMP and type_j == ColumnType.SCALAR:
            return True, j, i
        return False, None, None

    def is_set_pair(self, i: int, j: int) -> bool:
        """Check if both columns are SET type."""
        from featrix.neural.model_config import ColumnType
        return (
            self.col_idx_to_type.get(i) == ColumnType.SET and
            self.col_idx_to_type.get(j) == ColumnType.SET
        )

    def is_set_scalar_pair(self, i: int, j: int) -> Tuple[bool, Optional[int], Optional[int]]:
        """
        Check if one column is SET and other is SCALAR.

        Returns:
            (is_set_scalar_pair, set_col_idx, scalar_col_idx)
        """
        from featrix.neural.model_config import ColumnType
        type_i = self.col_idx_to_type.get(i)
        type_j = self.col_idx_to_type.get(j)

        if type_i == ColumnType.SET and type_j == ColumnType.SCALAR:
            return True, i, j
        elif type_i == ColumnType.SCALAR and type_j == ColumnType.SET:
            return True, j, i
        return False, None, None

    def is_scalar_pair(self, i: int, j: int) -> bool:
        """Check if both columns are SCALAR type."""
        from featrix.neural.model_config import ColumnType
        return (
            self.col_idx_to_type.get(i) == ColumnType.SCALAR and
            self.col_idx_to_type.get(j) == ColumnType.SCALAR
        )

    def _scale_type_aware_token(self, token: torch.Tensor, generic_token: torch.Tensor) -> torch.Tensor:
        """
        Scale a type-aware token to match the magnitude of the generic token it replaces.

        Type-aware ops (SetSet, SetScalar, ScalarScalar) produce outputs with ~4.7x larger
        L2 norms than the generic presence_mlp. This causes type-aware tokens to dominate
        in attention/pooling operations simply due to magnitude, not informativeness.

        This method scales the type-aware token to have the same average L2 norm as the
        generic token, ensuring fair contribution based on learned representations.

        Args:
            token: Type-aware token of shape (batch, d_model)
            generic_token: The generic token being replaced (for magnitude reference)

        Returns:
            Scaled token with matched magnitude
        """
        with torch.no_grad():
            # Compute L2 norms per sample
            type_aware_norms = token.norm(p=2, dim=-1, keepdim=True)  # (batch, 1)
            generic_norms = generic_token.norm(p=2, dim=-1, keepdim=True)  # (batch, 1)

            # Avoid division by zero
            eps = 1e-8
            scale_factor = generic_norms / (type_aware_norms + eps)

            # Debug: log scaling stats periodically (first 3 calls only)
            if not hasattr(self, '_scale_debug_count'):
                self._scale_debug_count = 0
            self._scale_debug_count += 1
            if self._scale_debug_count <= 3:
                logger.info(
                    f"🔬 _scale_type_aware_token: type_aware_norm={type_aware_norms.mean().item():.3f}, "
                    f"generic_norm={generic_norms.mean().item():.3f}, "
                    f"scale_factor={scale_factor.mean().item():.3f}"
                )

        # Apply scaling (scale_factor is detached, so gradients flow through token)
        return token * scale_factor

    def _safe_type_aware_call(
        self,
        op_name: str,
        op_fn,
        generic_token: torch.Tensor,
        *args,
        **kwargs,
    ) -> Tuple[Optional[torch.Tensor], bool]:
        """
        Safely call a type-aware operation with graceful degradation.

        If the operation fails, logs a warning (once per op type), tracks the error,
        and returns None so the caller can fall back to the generic token.

        Args:
            op_name: Name of the operation (for logging/tracking)
            op_fn: The callable operation (e.g., self.set_timestamp_ops)
            generic_token: The generic token to scale against / fall back to
            *args, **kwargs: Arguments to pass to op_fn

        Returns:
            (token, success): The computed token (or None if failed), and success flag
        """
        try:
            token = op_fn(*args, **kwargs)
            # Scale to match generic token magnitude
            token = self._scale_type_aware_token(token, generic_token)
            return token, True
        except Exception as e:
            # Track error count
            self._type_aware_errors[op_name] = self._type_aware_errors.get(op_name, 0) + 1

            # Log only once per op type to avoid spam
            if op_name not in self._type_aware_errors_logged:
                self._type_aware_errors_logged.add(op_name)
                logger.warning(
                    f"⚠️  Type-aware op '{op_name}' failed (falling back to generic token): "
                    f"{type(e).__name__}: {e}"
                )

            return None, False

    def is_email_domain_col(self, col_idx: int) -> bool:
        """Check if column is EMAIL or DOMAIN type."""
        from featrix.neural.model_config import ColumnType
        col_type = self.col_idx_to_type.get(col_idx)
        return col_type in (ColumnType.EMAIL, ColumnType.DOMAIN)

    def is_email_domain_pair(self, i: int, j: int) -> Tuple[bool, Optional[int], Optional[int]]:
        """
        Check if one column is EMAIL and other is DOMAIN.

        Returns:
            (is_email_domain_pair, email_col_idx, domain_col_idx)
        """
        from featrix.neural.model_config import ColumnType
        type_i = self.col_idx_to_type.get(i)
        type_j = self.col_idx_to_type.get(j)

        if type_i == ColumnType.EMAIL and type_j == ColumnType.DOMAIN:
            return True, i, j
        elif type_i == ColumnType.DOMAIN and type_j == ColumnType.EMAIL:
            return True, j, i
        return False, None, None

    def is_email_domain_set_pair(self, i: int, j: int) -> Tuple[bool, Optional[int], Optional[int]]:
        """
        Check if one column is EMAIL/DOMAIN and other is SET.

        Returns:
            (is_email_domain_set_pair, email_domain_col_idx, set_col_idx)
        """
        from featrix.neural.model_config import ColumnType
        type_i = self.col_idx_to_type.get(i)
        type_j = self.col_idx_to_type.get(j)
        is_ed_i = type_i in (ColumnType.EMAIL, ColumnType.DOMAIN)
        is_ed_j = type_j in (ColumnType.EMAIL, ColumnType.DOMAIN)

        if is_ed_i and type_j == ColumnType.SET:
            return True, i, j
        elif type_i == ColumnType.SET and is_ed_j:
            return True, j, i
        return False, None, None

    def is_email_domain_scalar_pair(self, i: int, j: int) -> Tuple[bool, Optional[int], Optional[int]]:
        """
        Check if one column is EMAIL/DOMAIN and other is SCALAR.

        Returns:
            (is_email_domain_scalar_pair, email_domain_col_idx, scalar_col_idx)
        """
        from featrix.neural.model_config import ColumnType
        type_i = self.col_idx_to_type.get(i)
        type_j = self.col_idx_to_type.get(j)
        is_ed_i = type_i in (ColumnType.EMAIL, ColumnType.DOMAIN)
        is_ed_j = type_j in (ColumnType.EMAIL, ColumnType.DOMAIN)

        if is_ed_i and type_j == ColumnType.SCALAR:
            return True, i, j
        elif type_i == ColumnType.SCALAR and is_ed_j:
            return True, j, i
        return False, None, None

    def is_email_domain_timestamp_pair(self, i: int, j: int) -> Tuple[bool, Optional[int], Optional[int]]:
        """
        Check if one column is EMAIL/DOMAIN and other is TIMESTAMP.

        Returns:
            (is_email_domain_timestamp_pair, email_domain_col_idx, timestamp_col_idx)
        """
        from featrix.neural.model_config import ColumnType
        type_i = self.col_idx_to_type.get(i)
        type_j = self.col_idx_to_type.get(j)
        is_ed_i = type_i in (ColumnType.EMAIL, ColumnType.DOMAIN)
        is_ed_j = type_j in (ColumnType.EMAIL, ColumnType.DOMAIN)

        if is_ed_i and type_j == ColumnType.TIMESTAMP:
            return True, i, j
        elif type_i == ColumnType.TIMESTAMP and is_ed_j:
            return True, j, i
        return False, None, None

    def is_email_domain_string_pair(self, i: int, j: int) -> Tuple[bool, Optional[int], Optional[int]]:
        """
        Check if one column is EMAIL/DOMAIN and other is FREE_STRING.

        Returns:
            (is_email_domain_string_pair, email_domain_col_idx, string_col_idx)
        """
        from featrix.neural.model_config import ColumnType
        type_i = self.col_idx_to_type.get(i)
        type_j = self.col_idx_to_type.get(j)
        is_ed_i = type_i in (ColumnType.EMAIL, ColumnType.DOMAIN)
        is_ed_j = type_j in (ColumnType.EMAIL, ColumnType.DOMAIN)

        if is_ed_i and type_j == ColumnType.FREE_STRING:
            return True, i, j
        elif type_i == ColumnType.FREE_STRING and is_ed_j:
            return True, j, i
        return False, None, None

    def is_url_col(self, col_idx: int) -> bool:
        """Check if column is URL type."""
        from featrix.neural.model_config import ColumnType
        return self.col_idx_to_type.get(col_idx) == ColumnType.URL

    def is_url_set_pair(self, i: int, j: int) -> Tuple[bool, Optional[int], Optional[int]]:
        """
        Check if one column is URL and other is SET.

        Returns:
            (is_url_set_pair, url_col_idx, set_col_idx)
        """
        from featrix.neural.model_config import ColumnType
        type_i = self.col_idx_to_type.get(i)
        type_j = self.col_idx_to_type.get(j)

        if type_i == ColumnType.URL and type_j == ColumnType.SET:
            return True, i, j
        elif type_i == ColumnType.SET and type_j == ColumnType.URL:
            return True, j, i
        return False, None, None

    def is_url_scalar_pair(self, i: int, j: int) -> Tuple[bool, Optional[int], Optional[int]]:
        """
        Check if one column is URL and other is SCALAR.

        Returns:
            (is_url_scalar_pair, url_col_idx, scalar_col_idx)
        """
        from featrix.neural.model_config import ColumnType
        type_i = self.col_idx_to_type.get(i)
        type_j = self.col_idx_to_type.get(j)

        if type_i == ColumnType.URL and type_j == ColumnType.SCALAR:
            return True, i, j
        elif type_i == ColumnType.SCALAR and type_j == ColumnType.URL:
            return True, j, i
        return False, None, None

    def is_url_timestamp_pair(self, i: int, j: int) -> Tuple[bool, Optional[int], Optional[int]]:
        """
        Check if one column is URL and other is TIMESTAMP.

        Returns:
            (is_url_timestamp_pair, url_col_idx, timestamp_col_idx)
        """
        from featrix.neural.model_config import ColumnType
        type_i = self.col_idx_to_type.get(i)
        type_j = self.col_idx_to_type.get(j)

        if type_i == ColumnType.URL and type_j == ColumnType.TIMESTAMP:
            return True, i, j
        elif type_i == ColumnType.TIMESTAMP and type_j == ColumnType.URL:
            return True, j, i
        return False, None, None

    def is_url_string_pair(self, i: int, j: int) -> Tuple[bool, Optional[int], Optional[int]]:
        """
        Check if one column is URL and other is FREE_STRING.

        Returns:
            (is_url_string_pair, url_col_idx, string_col_idx)
        """
        from featrix.neural.model_config import ColumnType
        type_i = self.col_idx_to_type.get(i)
        type_j = self.col_idx_to_type.get(j)

        if type_i == ColumnType.URL and type_j == ColumnType.FREE_STRING:
            return True, i, j
        elif type_i == ColumnType.FREE_STRING and type_j == ColumnType.URL:
            return True, j, i
        return False, None, None

    # ============================================================================
    # RELATIONSHIP HISTORY (META-LEARNING)
    # ============================================================================

    def load_relationship_history(
        self,
        df,  # pandas DataFrame for dataset hash
        session_id: str,
    ) -> None:
        """
        Load historical relationship data using the feature suggestion infrastructure.
        
        Relationship pairs are stored as feature suggestions with type "relationship_pair".
        
        Args:
            df: pandas DataFrame (used to compute dataset hash)
            session_id: Current training session ID
        """
        self._session_id = session_id
        
        if not _HAS_META_LEARNING:
            logger.info("ℹ️  Meta-learning client not available - using default pair ordering")
            return
        
        try:
            # Get all feature suggestions for this dataset
            suggestions = retrieve_feature_engineering_suggestions(df, min_votes=1)
            
            # Filter for relationship_pair type
            pair_suggestions = [s for s in suggestions if s.get('suggestion_type') == 'relationship_pair']
            
            if not pair_suggestions:
                logger.info(f"ℹ️  No relationship history for this dataset - will build it during training")
                return
            
            # Build column name to index mapping
            col_to_idx = {name: i for i, name in enumerate(self.col_names)}
            
            # Categorize pairs based on history
            for suggestion in pair_suggestions:
                cols = suggestion.get('columns', [])
                if len(cols) != 2:
                    continue
                col_a, col_b = cols
                if col_a not in col_to_idx or col_b not in col_to_idx:
                    continue
                    
                i, j = col_to_idx[col_a], col_to_idx[col_b]
                if i > j:
                    i, j = j, i  # Ensure i < j
                pair = (i, j)
                
                contribution = suggestion.get('contribution', 0)
                was_pruned = suggestion.get('was_pruned', False)
                votes = suggestion.get('votes', 1)
                
                # Categorize based on history
                if not was_pruned and contribution > 0.1 and votes >= 2:
                    self._known_good_pairs.add(pair)
                elif was_pruned and votes >= 2:
                    self._known_bad_pairs.add(pair)
            
            # ============================================================================
            # CULL BAD PAIRS: Pre-disable known-bad pairs so we don't waste time on them
            # ============================================================================
            # These are pairs that were consistently pruned in previous runs.
            # Skip them entirely instead of wasting compute re-discovering they're bad.
            for pair in self._known_bad_pairs:
                self.disabled_pairs.add(pair)
            
            # Reorder remaining pairs: known-good first, unknown middle
            # (known-bad are already disabled, won't be computed)
            remaining_pairs = [p for p in self.all_pairs if p not in self._known_bad_pairs]
            
            def priority_key(pair):
                if pair in self._known_good_pairs:
                    return 0  # Known-good first
                else:
                    return 1  # Unknown second
            
            self.all_pairs = sorted(remaining_pairs, key=priority_key)
            self._history_loaded = True
            
            logger.info(f"📊 Relationship history loaded from feature suggestions:")
            logger.info(f"   ✅ Known-good pairs: {len(self._known_good_pairs)} (explore first)")
            logger.info(f"   ❌ Known-bad pairs: {len(self._known_bad_pairs)} (pre-disabled, skipped)")
            logger.info(f"   ❓ Unknown pairs: {len(self.all_pairs) - len(self._known_good_pairs)}")
                
        except Exception as e:
            logger.warning(f"⚠️  Failed to load relationship history: {e}")
            self._history_loaded = False
    
    def save_relationship_history(
        self,
        df,  # pandas DataFrame for dataset hash
        job_id: Optional[str] = None,
    ) -> bool:
        """
        Save relationship contribution data using the feature suggestion infrastructure.
        
        Relationship pairs are stored as feature suggestions with type "relationship_pair".
        
        Args:
            df: pandas DataFrame (used to compute dataset hash)
            job_id: Optional job ID
            
        Returns:
            True if successfully saved, False otherwise
        """
        if not _HAS_META_LEARNING:
            logger.info("ℹ️  Meta-learning client not available - relationship history not saved")
            return False
        
        try:
            # Convert pair contributions to feature suggestions format
            suggestions = []
            for (i, j), contribution in self.pair_contributions.items():
                if i < len(self.col_names) and j < len(self.col_names):
                    col_a, col_b = self.col_names[i], self.col_names[j]
                    was_pruned = (i, j) in self.disabled_pairs
                    
                    suggestions.append({
                        "suggestion_type": "relationship_pair",
                        "columns": [col_a, col_b],
                        "contribution": float(contribution),
                        "was_pruned": was_pruned,
                        "epoch": self.current_epoch,
                        "description": f"Relationship between {col_a} and {col_b}"
                    })
            
            if not suggestions:
                logger.warning("No relationship data to save")
                return False
            
            # Use the existing feature suggestion infrastructure
            success = push_feature_engineering_suggestions(
                df=df,
                suggestions=suggestions,
                session_id=self._session_id,
                job_id=job_id,
                epoch=self.current_epoch
            )
            
            if success:
                logger.info(f"✅ Relationship history saved ({len(suggestions)} pairs)")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Failed to save relationship history: {e}")
            return False
    
    def get_pair_priority(self, pair: Tuple[int, int]) -> int:
        """
        Get priority level for a pair based on history.
        
        Returns:
            0 = known-good (explore first)
            1 = unknown (normal priority)
            2 = known-bad (explore last)
        """
        if pair in self._known_good_pairs:
            return 0
        elif pair in self._known_bad_pairs:
            return 2
        else:
            return 1
    
    def get_null_token(self, col_embedding: torch.Tensor) -> torch.Tensor:
        """
        Get contextual NULL token for a column.
        
        Args:
            col_embedding: (batch_size, d_model) - column i's encoding
        
        Returns:
            null_token: (batch_size, d_model) - contextual NULL for this column
        """
        batch_size = col_embedding.shape[0]
        # Base NULL (global)
        base_null = self.null_relationship_base.expand(batch_size, -1)
        # Column-specific context (scaled to prevent early domination)
        contextual_null = self.null_scale * self.null_relationship_mlp(col_embedding)
        # Combine and normalize
        null_token = base_null + contextual_null
        null_token = self.null_layer_norm(null_token)
        return null_token

    def _apply_column_diversity_cap(
        self,
        pairs_with_scores: List[Tuple[Tuple[int, int], float]],
        pool_size: int,
    ) -> Tuple[List[Tuple[int, int]], Dict]:
        """
        Apply per-column diversity cap to prevent hub dominance in active pool.

        Any single column can appear in at most max_column_fraction of the pool.
        Uses two-pass selection:
        1. First pass: Fill up to quota per column (best pairs first)
        2. Second pass: Spillover - fill remaining slots with best available

        Args:
            pairs_with_scores: List of ((i, j), score) sorted by score descending
            pool_size: Target pool size

        Returns:
            (selected_pairs, diagnostics) where selected_pairs is list of (i, j) tuples
        """
        from collections import defaultdict

        max_per_column = max(1, int(pool_size * self.max_column_fraction))

        # Count appearances per column
        column_counts = defaultdict(int)
        selected = []
        deferred = []  # Pairs that exceeded quota (for spillover)
        capped_columns = set()  # Track which columns hit their cap

        # First pass: respect quotas
        for pair, score in pairs_with_scores:
            if len(selected) >= pool_size:
                break

            i, j = pair
            can_add_i = column_counts[i] < max_per_column
            can_add_j = column_counts[j] < max_per_column

            if can_add_i and can_add_j:
                selected.append(pair)
                column_counts[i] += 1
                column_counts[j] += 1
            else:
                # Track which columns are at capacity
                if not can_add_i:
                    capped_columns.add(i)
                if not can_add_j:
                    capped_columns.add(j)
                # Defer for potential spillover
                deferred.append((pair, score))

        # Second pass: spillover (fill remaining slots with best deferred)
        spillover_count = 0
        if len(selected) < pool_size and deferred:
            remaining_slots = pool_size - len(selected)
            for pair, score in deferred[:remaining_slots]:
                selected.append(pair)
                spillover_count += 1
                # Update counts for diagnostics (even though we're past quota)
                i, j = pair
                column_counts[i] += 1
                column_counts[j] += 1

        # Build diagnostics
        diagnostics = {
            'max_per_column': max_per_column,
            'capped_columns': len(capped_columns),
            'capped_column_names': [self.col_names[c] if c < len(self.col_names) else f"col_{c}"
                                    for c in sorted(capped_columns)],
            'spillover_count': spillover_count,
            'deferred_count': len(deferred),
            'final_pool_size': len(selected),
        }

        return selected, diagnostics

    def _select_active_directed_pairs_with_candidates(
        self,
        scores_dict: Optional[Dict[Tuple[int, int], float]] = None,
        last_step_actives: Optional[Set[Tuple[int, int]]] = None,
    ) -> Tuple[List[Tuple[int, int]], Dict]:
        """
        Two-stage per-column exploit/explore selection: candidates → scores → finalize.
        
        Stage 1: Build candidate pool per column (cheap, no scoring)
        Stage 2: Score only candidates (not all pairs - critical for large N)
        Stage 3: Finalize selection per column
        
        For each target column j:
        - Exploit candidates: top K_exploit from _pair_stats (if exist) or last step's actives
        - Explore candidates: E random incoming edges (i→j)
        - Score candidates only
        - Exploit: top K_exploit from candidates with valid scores (score = -inf if missing)
        - Explore: K_explore random from candidates (fills gaps even if scores missing)
        
        Args:
            scores_dict: Optional pre-computed scores {(i,j): score}
            last_step_actives: Optional set of pairs from last step (fallback for exploit)
        
        Returns:
            (final_active_pairs, diagnostics_dict)
        """
        N = self.n_cols
        
        # ============================================================================
        # EXPLICIT PARAMETERS: E, K_exploit, K_explore
        # ============================================================================
        # CRITICAL: Use same E computation as forward() to ensure consistency
        # This includes the reduction for large column counts to prevent OOM
        log2_N = np.log2(max(2, N))  # Avoid log(1) = 0
        base_E = max(1, min(32, int(np.ceil(log2_N))))
        # Scale down E for large column counts to prevent OOM (same logic as forward())
        if N > 100:
            # More aggressive reduction: reduce by 1 for every 25 columns above 100
            reduction = min(4, (N - 100) // 25)  # Max reduction of 4
            E = max(2, base_E - reduction)  # Minimum E=2 to preserve some exploration
        else:
            E = base_E
        K_exploit = E  # Initially same as E, but distinct for future tuning
        K_explore = E  # Initially same as E, but distinct for future tuning
        
        # Initialize random number generator (seed once per run, advance per step)
        # This ensures uniform sampling without bias toward hub columns
        if not hasattr(self, '_selection_rng'):
            # Seed once per run (not per step) to avoid fixed patterns
            self._selection_rng = np.random.RandomState(42)  # pylint: disable=no-member
        # RNG advances naturally with each call (no need to reseed per step)
        
        # ============================================================================
        # STAGE 1: BUILD CANDIDATE POOL PER COLUMN (cheap, no scoring)
        # ============================================================================
        selection_start_time = time.time()
        
        candidate_pool_per_column = {}  # {j: set of (i, j) candidates}
        exploit_candidates_per_column = {}  # {j: list of (i, j)} for diagnostics
        explore_candidates_per_column = {}  # {j: list of (i, j)} for diagnostics
        
        for j in range(N):
            exploit_candidates = []
            explore_candidates = []
            
            # Exploit candidates: top K_exploit from _pair_stats (if exist) or last step's actives
            # Get all incoming edges (i→j) with scores from _pair_stats
            # CRITICAL: Only incoming edges (i→j) for target j, not outgoing (j→i)
            incoming_with_stats = []
            for i in range(N):
                if i == j:
                    continue
                if (i, j) in self.disabled_pairs:
                    continue  # Respect disabled pairs
                
                # ASSERT: This must be an incoming edge (i→j) where j is the target
                # The lift definition is: baseline_null_ema[j] - loss_j, so we need (i→j)
                assert i != j, f"Invalid edge: source and target cannot be the same: ({i}, {j})"
                
                stats = self._pair_stats.get((i, j), {})
                lift_ema = stats.get('lift_ema')
                if lift_ema is not None and math.isfinite(lift_ema):
                    incoming_with_stats.append((i, j, lift_ema))
            
            # Sort by lift_ema descending and take top K_exploit
            incoming_with_stats.sort(key=lambda t: t[2], reverse=True)
            exploit_candidates = [(i, j) for (i, j, _) in incoming_with_stats[:K_exploit]]
            
            # Fallback: if no stats available, use last step's actives for this column
            if not exploit_candidates and last_step_actives:
                last_step_for_j = [(i, j_pair) for (i, j_pair) in last_step_actives if j_pair == j]
                exploit_candidates = last_step_for_j[:K_exploit]
            
            # Explore candidates: E random incoming edges (i→j) not disabled
            # Uniform sampling over all i != j to avoid hub bias
            all_incoming = [(i, j) for i in range(N) if i != j and (i, j) not in self.disabled_pairs]
            if len(all_incoming) > 0:
                n_explore = min(K_explore, len(all_incoming))
                if n_explore > 0:
                    # Uniform sampling without replacement (RNG advances naturally)
                    explore_indices = self._selection_rng.choice(len(all_incoming), n_explore, replace=False)
                    explore_candidates = [all_incoming[idx] for idx in explore_indices]
            
            # Combine into candidate pool
            candidate_pool = set(exploit_candidates) | set(explore_candidates)
            candidate_pool_per_column[j] = candidate_pool
            exploit_candidates_per_column[j] = exploit_candidates
            explore_candidates_per_column[j] = explore_candidates
            
            # ASSERT: All candidates must be incoming edges (i→j) for target j
            for edge in candidate_pool:
                assert edge[1] == j, f"Invalid candidate: edge[1]={edge[1]} != target j={j}. Edge must be incoming (i→j)"
        
        # ============================================================================
        # STAGE 2: SCORE ONLY CANDIDATES (not all pairs - critical for large N)
        # ============================================================================
        # Convert candidate pool to undirected pairs for scoring
        candidate_undirected = set()
        for j, candidates in candidate_pool_per_column.items():
            for (i, j) in candidates:
                if i < j:
                    candidate_undirected.add((i, j))
                else:
                    candidate_undirected.add((j, i))
        
        # Score candidates using _compute_pair_scores (only scores the candidate pool)
        if scores_dict is None:
            scores_dict, score_diagnostics = self._compute_pair_scores(list(candidate_undirected))
        else:
            # Use provided scores_dict, but only for candidates
            score_diagnostics = {}
        
        # ============================================================================
        # STAGE 3: FINALIZE SELECTION PER COLUMN
        # ============================================================================
        final_active = set()
        exploit_selected = set()
        explore_selected = set()
        
        for j in range(N):
            candidates = candidate_pool_per_column[j]
            
            # Exploit: top K_exploit from candidates with valid scores
            # Missing scores treated as -inf (not eligible for exploit)
            exploit_scores = []
            for (i, j_candidate) in candidates:
                # ASSERT: Candidate must be incoming edge (i→j) for target j
                assert j_candidate == j, f"Invalid candidate: edge[1]={j_candidate} != target j={j}"
                
                # Get score for undirected pair (i,j) or (j,i)
                undirected_pair = (i, j) if i < j else (j, i)
                score = scores_dict.get(undirected_pair, float('-inf'))
                if score != float('-inf'):
                    exploit_scores.append((i, j, score))
            
            # ========================================================================
            # PHASE 2: UCB SELECTION (design - ready to implement)
            # ========================================================================
            # UCB formula: score_ij^UCB = lift_ema + α * sqrt(log(1 + T) / (1 + n_ij))
            #
            # Where:
            #   - lift_ema: from _pair_stats[(i,j)]['lift_ema']
            #   - α: UCB exploration parameter (self.ucb_alpha, default 1.5)
            #   - T: total steps (self._step_counter)
            #   - n_ij: observation count from _pair_stats[(i,j)]['n']
            #
            # When use_ucb_selection=True, replace simple score with UCB score:
            # ========================================================================
            
            if self.use_ucb_selection:
                # PHASE 2: UCB selection - balances exploration vs exploitation
                exploit_scores_ucb = []
                T = getattr(self, '_step_counter', 1)  # Total steps
                
                for (i, j_candidate) in candidates:
                    assert j_candidate == j, f"Invalid candidate: edge[1]={j_candidate} != target j={j}"
                    
                    # Get lift_ema and n_ij from pair stats
                    stats = self._pair_stats.get((i, j), {})
                    lift_ema = stats.get('lift_ema', 0.0)
                    n_ij = stats.get('n', 0)
                    
                    # UCB bonus: uncertainty decreases with more observations
                    # Low n_ij → high bonus (explore more)
                    # High n_ij → low bonus (exploit lift_ema)
                    if n_ij > 0:
                        ucb_bonus = self.ucb_alpha * math.sqrt(math.log(1 + T) / (1 + n_ij))
                    else:
                        # Never observed: maximum exploration bonus
                        ucb_bonus = self.ucb_alpha * math.sqrt(math.log(1 + T))
                    
                    ucb_score = lift_ema + ucb_bonus
                    exploit_scores_ucb.append((i, j, ucb_score))
                
                # Sort by UCB score descending and take top K_exploit
                exploit_scores_ucb.sort(key=lambda t: t[2], reverse=True)
                exploit = [(i, j) for (i, j, _) in exploit_scores_ucb[:K_exploit]]
            else:
                # PHASE 1: Simple score sorting (current implementation)
                # Sort by score descending and take top K_exploit
                exploit_scores.sort(key=lambda t: t[2], reverse=True)
                exploit = [(i, j) for (i, j, _) in exploit_scores[:K_exploit]]
            
            # Explore: K_explore random from candidates (fills gaps even if scores missing)
            used = set(exploit)
            explore_candidates = [(i, j) for (i, j) in candidates if (i, j) not in used]
            n_explore = min(K_explore, len(explore_candidates))
            if n_explore > 0:
                explore_indices = self._selection_rng.choice(len(explore_candidates), n_explore, replace=False)
                explore = [explore_candidates[idx] for idx in explore_indices]
            else:
                explore = []
            
            # Add to final active set
            for pair in exploit + explore:
                # ASSERT: Final selected edge must be incoming (i→j) for target j
                assert pair[1] == j, f"Invalid final selection: edge[1]={pair[1]} != target j={j}"
                final_active.add(pair)
                if pair in exploit:
                    exploit_selected.add(pair)
                else:
                    explore_selected.add(pair)

        # ============================================================================
        # COLUMN DIVERSITY CAP: Prevent hub dominance in active pool
        # ============================================================================
        # After per-column selection, apply global diversity cap to ensure no single
        # column dominates the active pool (e.g., email appearing in 80% of pairs).
        # This promotes learning diverse relationships across all columns.
        # ============================================================================
        pre_cap_size = len(final_active)
        if self.max_column_fraction < 1.0 and pre_cap_size > 0:
            # Build list of (pair, score) for diversity cap
            # Use lift_ema as score (higher = more important to keep)
            pairs_with_scores = []
            for pair in final_active:
                i, j = pair
                stats_ij = self._pair_stats.get((i, j), {})
                lift_ema = stats_ij.get('lift_ema', 0.0)
                if lift_ema is None or not math.isfinite(lift_ema):
                    lift_ema = 0.0
                pairs_with_scores.append((pair, lift_ema))

            # Sort by score descending (best pairs first)
            pairs_with_scores.sort(key=lambda x: x[1], reverse=True)

            # Apply diversity cap
            capped_pairs, diversity_diagnostics = self._apply_column_diversity_cap(
                pairs_with_scores, pool_size=pre_cap_size
            )

            # Update final_active and exploit/explore sets
            capped_set = set(capped_pairs)
            removed_pairs = final_active - capped_set
            final_active = capped_set
            exploit_selected = exploit_selected & capped_set
            explore_selected = explore_selected & capped_set
        else:
            diversity_diagnostics = {'capped_columns': 0, 'spillover_count': 0}
            removed_pairs = set()

        selection_time_ms = (time.time() - selection_start_time) * 1000
        
        # ============================================================================
        # DIAGNOSTICS
        # ============================================================================
        # Count columns with NULL baseline available
        cols_with_baseline = 0
        for j in range(N):
            col_j_name = self.col_names[j] if j < len(self.col_names) else None
            if col_j_name and col_j_name in self._null_baseline_ema:
                baseline_val = self._null_baseline_ema[col_j_name]
                if baseline_val is not None and math.isfinite(baseline_val):
                    cols_with_baseline += 1
        
        # Count selected edges with valid scores (not -inf)
        edges_with_valid_score = 0
        for edge in final_active:
            i, j = edge
            undirected_pair = (i, j) if i < j else (j, i)
            score = scores_dict.get(undirected_pair, float('-inf'))
            if score != float('-inf') and math.isfinite(score):
                edges_with_valid_score += 1
        
        diagnostics = {
            'E': E,
            'K_exploit': K_exploit,
            'K_explore': K_explore,
            'total_candidates': sum(len(candidates) for candidates in candidate_pool_per_column.values()),
            'total_final': len(final_active),
            'exploit_count': len(exploit_selected),
            'explore_count': len(explore_selected),
            'exploit_selected': exploit_selected,  # Set of exploit edges (for dropout)
            'explore_selected': explore_selected,  # Set of explore edges (protected from dropout)
            'scored_count': len([p for p in final_active if (p[0] < p[1] and (p[0], p[1]) in scores_dict) or (p[1] < p[0] and (p[1], p[0]) in scores_dict)]),
            'edges_with_valid_score': edges_with_valid_score,  # Edges with valid score (not -inf)
            'cols_with_baseline': cols_with_baseline,  # Columns with NULL baseline available
            'selection_time_ms': selection_time_ms,  # CPU time for selection (diagnostic for large N)
            'score_diagnostics': score_diagnostics,
            # Column diversity cap diagnostics
            'pre_cap_size': pre_cap_size,
            'diversity_capped_columns': diversity_diagnostics.get('capped_columns', 0),
            'diversity_capped_names': diversity_diagnostics.get('capped_column_names', []),
            'diversity_spillover': diversity_diagnostics.get('spillover_count', 0),
            'diversity_removed': len(removed_pairs),
        }

        return list(final_active), diagnostics

    def forward_training(
        self,
        column_encodings: torch.Tensor,
        mask: Optional[torch.Tensor],
        n_cols: int,
    ) -> Tuple[List[Tuple[int, int]], bool]:
        """
        Training mode: full exploit+explore selection with dropout and tracking.
        
        Returns:
            (pairs_to_compute, is_exploration)
        """
        from featrix.neural.gpu_utils import get_gpu_memory_allocated, get_gpu_memory_reserved
        
        # Get last step's actives for fallback (if available)
        last_step_actives = getattr(self, '_last_step_active_pairs', None)
        
        # Two-stage selection: candidates → scores → finalize
        active_directed_pairs, selection_diagnostics = self._select_active_directed_pairs_with_candidates(
            scores_dict=None,  # Will be computed internally from candidates
            last_step_actives=last_step_actives,
        )
        
        # ========================================================================
        # HARD CAP: Prevent activating all pairs (sanity check)
        # ========================================================================
        log2_N = np.log2(max(2, n_cols))
        base_E = max(1, min(32, int(np.ceil(log2_N))))
        if n_cols > 100:
            reduction = min(4, (n_cols - 100) // 25)
            E = max(2, base_E - reduction)
        else:
            E = base_E
        K_exploit = E
        K_explore = E
        max_allowed_directed = n_cols * (K_exploit + K_explore)
        
        if len(active_directed_pairs) > max_allowed_directed:
            logger.warning(f"⚠️  Selection returned {len(active_directed_pairs)} edges, "
                         f"exceeds max {max_allowed_directed} (N={n_cols}, E={E}). "
                         f"This indicates a bug - selection should respect per-column quotas.")
            if not hasattr(self, '_selection_rng'):
                self._selection_rng = np.random.RandomState(42)  # pylint: disable=no-member
            indices = self._selection_rng.choice(len(active_directed_pairs), max_allowed_directed, replace=False)
            active_directed_pairs = [active_directed_pairs[i] for i in indices]
        
        # Convert directed pairs to undirected for pairs_to_compute
        undirected_set = set()
        for i, j in active_directed_pairs:
            if i < j:
                undirected_set.add((i, j))
            else:
                undirected_set.add((j, i))
        pairs_to_compute = [p for p in undirected_set if p not in self.disabled_pairs]
        
        # ========================================================================
        # ADAPTIVE MEMORY MANAGEMENT
        # ========================================================================
        total_pairs_requested = len(pairs_to_compute)
        memory_threshold = 0.60
        pairs_increment = 100
        
        tracker = HostMemoryTracker.get_instance()
        learned_max = tracker.get_learned_max_pairs()
        hostname = tracker.hostname
        
        if learned_max and learned_max > 0:
            base_safe_pairs = min(learned_max, total_pairs_requested)
            logger.debug(f"📊 Using learned max pairs for {hostname}: {learned_max}")
        else:
            base_safe_pairs = min(self.max_pairs_per_chunk, 200)
            logger.debug(f"📊 No pair history for {hostname}, starting with {base_safe_pairs}")
        
        max_safe_pairs = base_safe_pairs
        
        if total_pairs_requested > base_safe_pairs:
            total_gpu_memory = _get_gpu_memory_gb()
            
            if total_gpu_memory and total_gpu_memory > 0:
                current_allocated = get_gpu_memory_allocated()
                current_utilization = current_allocated / total_gpu_memory
                
                while max_safe_pairs < total_pairs_requested and current_utilization < memory_threshold:
                    remaining_headroom = memory_threshold - current_utilization
                    
                    if remaining_headroom > 0.10:
                        max_safe_pairs = min(max_safe_pairs + pairs_increment, total_pairs_requested)
                        if max_safe_pairs < total_pairs_requested:
                            logger.debug(f"   GPU at {current_utilization*100:.1f}% ({current_allocated:.2f}/{total_gpu_memory:.2f} GB), "
                                       f"expanding to {max_safe_pairs} pairs")
                    else:
                        break
                    
                    estimated_increase_per_100 = 0.005 * total_gpu_memory
                    current_utilization += (pairs_increment / 100) * (estimated_increase_per_100 / total_gpu_memory)
                
                if max_safe_pairs < total_pairs_requested:
                    logger.info(f"📊 Adaptive pair limit: {max_safe_pairs}/{total_pairs_requested} pairs "
                              f"(GPU: {current_allocated:.2f}/{total_gpu_memory:.2f} GB = {(current_allocated/total_gpu_memory)*100:.1f}%, "
                              f"host={hostname}, learned={learned_max or 'none'})")
            else:
                if not learned_max:
                    max_safe_pairs = min(self.max_pairs_per_chunk, 800)
                if total_pairs_requested > max_safe_pairs:
                    logger.warning(f"⚠️  Capping at {max_safe_pairs} pairs (no GPU info, learned={learned_max or 'none'})")
        
        self._current_pair_count = max_safe_pairs
        
        if total_pairs_requested > max_safe_pairs:
            if not hasattr(self, '_selection_rng'):
                self._selection_rng = np.random.RandomState(42)  # pylint: disable=no-member
            indices = self._selection_rng.choice(len(pairs_to_compute), max_safe_pairs, replace=False)
            pairs_to_compute = [pairs_to_compute[i] for i in indices]
        
        # ========================================================================
        # EDGE DROPOUT: Drop only exploit edges (preserves exploration floor)
        # ========================================================================
        if self.training and self.edge_dropout_prob > 0 and len(pairs_to_compute) > 0:
            exploit_selected = selection_diagnostics.get('exploit_selected', set())
            explore_selected = selection_diagnostics.get('explore_selected', set())
            
            exploit_undirected = set()
            explore_undirected = set()
            for (i, j) in exploit_selected:
                undirected = (i, j) if i < j else (j, i)
                exploit_undirected.add(undirected)
            for (i, j) in explore_selected:
                undirected = (i, j) if i < j else (j, i)
                explore_undirected.add(undirected)
            
            if not hasattr(self, '_selection_rng'):
                self._selection_rng = np.random.RandomState(42)  # pylint: disable=no-member
            
            pairs_before_dropout = len(pairs_to_compute)
            pairs_after_dropout = []
            dropped_count = 0
            
            for pair in pairs_to_compute:
                if pair in exploit_undirected:
                    keep = self._selection_rng.random() >= self.edge_dropout_prob
                    if keep:
                        pairs_after_dropout.append(pair)
                    else:
                        dropped_count += 1
                elif pair in explore_undirected:
                    pairs_after_dropout.append(pair)
                else:
                    pairs_after_dropout.append(pair)
            
            pairs_to_compute = pairs_after_dropout
            pairs_to_compute_set = set(pairs_to_compute)
            
            self._epoch_dropout_stats['total_edges_before'] += pairs_before_dropout
            self._epoch_dropout_stats['total_edges_after'] += len(pairs_to_compute)
            self._epoch_dropout_stats['total_dropped'] += dropped_count
            self._epoch_dropout_stats['steps_with_dropout'] += 1
            
            incoming_after_dropout = {}
            for j in range(n_cols):
                incoming_after_dropout[j] = set()
            
            for pair in pairs_to_compute_set:
                i, j = pair
                incoming_after_dropout[j].add((i, j))
                incoming_after_dropout[i].add((j, i))
            
            if hasattr(self, '_step_counter') and self._step_counter % 100 == 0:
                incoming_before = {}
                for j in range(n_cols):
                    incoming_before[j] = len([(i, j_edge) for (i, j_edge) in active_directed_pairs if j_edge == j])
                
                incoming_after = {}
                for j in range(n_cols):
                    incoming_after[j] = len(incoming_after_dropout[j])
                
                avg_before = np.mean(list(incoming_before.values())) if incoming_before else 0.0
                avg_after = np.mean(list(incoming_after.values())) if incoming_after else 0.0
                cols_with_zero = sum(1 for count in incoming_after.values() if count == 0)
                pct_zero = (cols_with_zero / n_cols * 100) if n_cols > 0 else 0.0
                
                exploit_dropped = sum(1 for p in exploit_undirected if p not in pairs_to_compute_set)
                explore_dropped = sum(1 for p in explore_undirected if p not in pairs_to_compute_set)
                
                logger.debug(f"🔗 Edge dropout (exploit-only): kept {len(pairs_to_compute_set)}/{pairs_before_dropout} pairs "
                           f"({dropped_count} dropped: {exploit_dropped} exploit, {explore_dropped} explore)")
                logger.debug(f"   Strategy: drop only exploit edges (explore floor preserved)")
                logger.debug(f"   Avg edges/col: {avg_before:.1f} → {avg_after:.1f} "
                           f"(expected: {avg_before - exploit_dropped/len(incoming_before) if incoming_before else avg_before:.1f})")
                logger.debug(f"   Columns with 0 edges: {cols_with_zero}/{n_cols} ({pct_zero:.1f}%) "
                           f"{'⚠️ INSTABILITY RISK' if pct_zero > 1.0 else '✅ OK'}")
        
        # ========================================================================
        # TRACK ACTIVE DIRECTED PAIRS FOR LIFT COMPUTATION
        # ========================================================================
        final_active_directed_pairs = set()
        for pair in pairs_to_compute:
            i, j = pair
            final_active_directed_pairs.add((i, j))
            final_active_directed_pairs.add((j, i))
        
        for directed_pair in final_active_directed_pairs:
            self._active_pairs_this_batch.add(directed_pair)
        
        self._epoch_active_edges.append(len(final_active_directed_pairs))
        self._last_step_active_pairs = final_active_directed_pairs
        self._last_pairs_to_compute = pairs_to_compute
        
        # ========================================================================
        # SANITY CHECK (every 50 steps)
        # ========================================================================
        step_counter = getattr(self, '_step_counter', 0)
        if step_counter % 50 == 0:
            edges_before_dropout = len(active_directed_pairs)
            edges_after_dropout = len(final_active_directed_pairs)
            
            null_baseline_cols = sum(1 for col_name in self.col_names 
                                    if col_name in self._null_baseline_ema 
                                    and self._null_baseline_ema[col_name] is not None 
                                    and math.isfinite(self._null_baseline_ema[col_name]))
            
            pair_stats_with_n = [stats for stats in self._pair_stats.values() if stats.get('n', 0) > 0]
            n_ij_values = [stats.get('n', 0) for stats in self._pair_stats.values() if stats.get('n', 0) > 0]
            
            max_n_ij = max(n_ij_values) if n_ij_values else 0
            median_n_ij = np.median(n_ij_values) if n_ij_values else 0
            
            logger.debug(f"🔍 SANITY CHECK (step {step_counter}):")
            logger.debug(f"   Selected edges: {edges_before_dropout} → {edges_after_dropout} (after dropout)")
            logger.debug(f"   Pair stats updated: {len(pair_stats_with_n)} pairs with n>0")
            logger.debug(f"   NULL baseline columns: {null_baseline_cols}/{len(self.col_names)}")
            logger.debug(f"   n_ij stats: max={max_n_ij}, median={median_n_ij:.1f}")
            logger.debug(f"   Status: {'✅ OK' if (edges_after_dropout > 0 and len(pair_stats_with_n) > 0 and null_baseline_cols > 0) else '⚠️ CHECK'}")
        
        is_exploration = (self.current_epoch < self.exploration_epochs)
        
        # ========================================================================
        # DIAGNOSTIC LOGGING (every ~50 steps)
        # ========================================================================
        if step_counter % 50 == 0 and selection_diagnostics:
            incoming_counts = []
            for j in range(n_cols):
                count = len([p for p in final_active_directed_pairs if p[1] == j])
                incoming_counts.append(count)
            
            if incoming_counts:
                min_incoming = min(incoming_counts)
                mean_incoming = np.mean(incoming_counts)
                max_incoming = max(incoming_counts)
            else:
                min_incoming = mean_incoming = max_incoming = 0
            
            exploit_count = selection_diagnostics.get('exploit_count', 0)
            explore_count = selection_diagnostics.get('explore_count', 0)
            total_final = selection_diagnostics.get('total_final', 0)
            
            scored_count = selection_diagnostics.get('scored_count', 0)
            edges_with_valid_score = selection_diagnostics.get('edges_with_valid_score', 0)
            cols_with_baseline = selection_diagnostics.get('cols_with_baseline', 0)
            
            logger.info(f"📊 Pair selection stats (step {step_counter}):")
            logger.info(f"   Incoming edges per column: min={min_incoming}, "
                       f"mean={mean_incoming:.1f}, max={max_incoming}")
            if total_final > 0:
                logger.info(f"   Selection breakdown: exploit={exploit_count} ({exploit_count/total_final*100:.1f}%), "
                           f"explore={explore_count} ({explore_count/total_final*100:.1f}%)")
                logger.info(f"   Score coverage: {scored_count}/{total_final} ({scored_count/total_final*100:.1f}%)")
                valid_score_pct = (edges_with_valid_score / total_final * 100) if total_final > 0 else 0.0
                logger.info(f"   Valid scores: {edges_with_valid_score}/{total_final} ({valid_score_pct:.1f}%) - {'learning' if valid_score_pct > 50 else 'exploring'}")
            baseline_pct = (cols_with_baseline / n_cols * 100) if n_cols > 0 else 0.0
            logger.info(f"   NULL baseline coverage: {cols_with_baseline}/{n_cols} columns ({baseline_pct:.1f}%)")
            logger.info(f"   Parameters: E={selection_diagnostics.get('E', 0)}, "
                       f"K_exploit={selection_diagnostics.get('K_exploit', 0)}, "
                       f"K_explore={selection_diagnostics.get('K_explore', 0)}")
            selection_time = selection_diagnostics.get('selection_time_ms', 0)
            if selection_time > 0:
                logger.info(f"   Selection time: {selection_time:.2f}ms")
        
        return pairs_to_compute, is_exploration

    def forward_inference(
        self,
        column_encodings: torch.Tensor,
        mask: Optional[torch.Tensor],
        n_cols: int,
    ) -> Tuple[List[Tuple[int, int]], bool]:
        """
        Inference mode: use learned pairs, no exploration.
        
        Returns:
            (pairs_to_compute, is_exploration)
        """
        # Get best pairs based on learned statistics
        pairs_to_compute = self._get_inference_pairs(n_cols)
        is_exploration = False
        
        # Store for Tier 3 local attention
        self._last_pairs_to_compute = pairs_to_compute
        self._last_step_active_pairs = set()
        for i, j in pairs_to_compute:
            self._last_step_active_pairs.add((i, j))
            self._last_step_active_pairs.add((j, i))
        
        logger.debug(f"🔍 Inference mode: using {len(pairs_to_compute)} learned pairs")
        return pairs_to_compute, is_exploration
    
    def _get_inference_pairs(self, n_cols: int) -> List[Tuple[int, int]]:
        """
        Get pairs to use during inference (eval mode).
        Uses learned pairs sorted by lift score.
        """
        # Check if we have learned pair statistics
        pair_stats = getattr(self, '_pair_stats', {})
        if not pair_stats:
            logger.debug("🔍 Inference: no pair stats available, skipping relationships")
            return []
        
        # Collect pairs with valid lift scores
        pairs_with_scores = []
        seen_undirected = set()
        
        for (i, j), stats in pair_stats.items():
            undirected = (i, j) if i < j else (j, i)
            if undirected in seen_undirected:
                continue
            seen_undirected.add(undirected)
            
            lift_ema = stats.get('lift_ema')
            n_obs = stats.get('n', 0)
            
            reverse_stats = pair_stats.get((j, i), {})
            reverse_lift = reverse_stats.get('lift_ema')
            reverse_n = reverse_stats.get('n', 0)
            
            best_lift = None
            total_n = n_obs + reverse_n
            if lift_ema is not None and math.isfinite(lift_ema):
                best_lift = lift_ema
            if reverse_lift is not None and math.isfinite(reverse_lift):
                if best_lift is None or reverse_lift > best_lift:
                    best_lift = reverse_lift
            
            if best_lift is not None and total_n > 0:
                pairs_with_scores.append((undirected, best_lift, total_n))
        
        if not pairs_with_scores:
            logger.debug("🔍 Inference: no pairs with valid scores, skipping relationships")
            return []
        
        # Sort by lift score (descending) and take top pairs
        pairs_with_scores.sort(key=lambda x: x[1], reverse=True)
        
        # For inference, use a generous limit
        max_inference_pairs = min(len(pairs_with_scores), n_cols * 10)
        
        selected_pairs = [p[0] for p in pairs_with_scores[:max_inference_pairs]]
        selected_pairs = [p for p in selected_pairs if p not in self.disabled_pairs]
        
        logger.debug(f"🔍 Inference: using {len(selected_pairs)} top pairs by lift score")
        return selected_pairs

    def forward(
        self,
        column_encodings: torch.Tensor,  # (batch_size, n_cols, d_model)
        mask: Optional[torch.Tensor] = None,  # (batch_size, n_cols)
        relationship_mode: str = "normal",  # "normal", "null_only", or "single_pair"
        single_pair: Optional[Tuple[int, int]] = None,  # For "single_pair" mode
        raw_timestamp_features: Optional[Dict[int, torch.Tensor]] = None,  # {col_idx: (batch, 12)} for temporal ops
        raw_domain_metadata: Optional[Dict[int, list]] = None,  # {col_idx: [batch metadata dicts]} for email/domain ops
        strategy_encodings: Optional[Dict[int, torch.Tensor]] = None,  # {col_idx: (batch, 20, d_model)} for strategy-aware scalar ops
        strategy_masks: Optional[Dict[int, torch.Tensor]] = None,  # {col_idx: (20,)} active strategy masks
    ) -> List[torch.Tensor]:
        """
        Extract relationship features from column encodings.
        
        Returns:
            List of relationship token tensors, each (batch_size, d_model)
        """
        # Ensure all attributes are initialized (for backward compatibility with old checkpoints)
        self._ensure_pair_stats_attributes()
        
        # Clear previous batch's tokens to avoid accumulation
        self._tokens_for_gradient_check.clear()
        
        batch_size, n_cols, d_model = column_encodings.shape
        
        # ============================================================================
        # RELATIONSHIP MODE HANDLING
        # ============================================================================
        if relationship_mode == "null_only":
            # NULL-only mode: return NULL tokens for all columns
            # These will be pooled and injected into CLS, giving us NULL baseline
            # CRITICAL: This runs in the same train/eval mode as normal forward
            # (inherited from the calling context), ensuring consistent dropout/training semantics
            null_tokens = []
            for col_idx in range(n_cols):
                col_embedding = column_encodings[:, col_idx, :]  # (batch_size, d_model)
                null_token = self.get_null_token(col_embedding)  # (batch_size, d_model)
                null_tokens.append(null_token)
            # Store empty pairs for Tier 3 (no relationships in null mode)
            self._last_pairs_to_compute = []
            self._last_step_active_pairs = set()
            return null_tokens
        elif relationship_mode == "single_pair":
            # Single pair mode: compute only one relationship (for debugging/targeted lift)
            if single_pair is None:
                raise ValueError("single_pair must be provided when relationship_mode='single_pair'")
            pairs_to_compute = [single_pair]
            is_exploration = False
            # Store for Tier 3
            self._last_pairs_to_compute = pairs_to_compute
            self._last_step_active_pairs = {single_pair, (single_pair[1], single_pair[0])}  # Both directions
        else:
            # Normal mode: dispatch to training or inference
            if self.training:
                pairs_to_compute, is_exploration = self.forward_training(
                    column_encodings, mask, n_cols
                )
            else:
                pairs_to_compute, is_exploration = self.forward_inference(
                    column_encodings, mask, n_cols
                )
        
        # ============================================================================
        # COARSE EXPLORATION SAMPLING (training only)
        # ============================================================================
        # For very large pair counts (e.g., 1000 columns = 499,500 pairs), sample a 
        # subset during exploration to get coarse signal. We don't need to evaluate
        # ALL pairs at full resolution - just enough to identify promising ones.
        # ============================================================================
        if is_exploration and len(pairs_to_compute) > self.max_coarse_pairs:
            # Sample a random subset for this batch
            # Use different samples each forward pass to eventually cover all pairs
            if not hasattr(self, '_sample_rng'):
                self._sample_rng = np.random.RandomState(42)  # pylint: disable=no-member

            # Sample indices (not pairs) to keep the list structure
            n_pairs = len(pairs_to_compute)
            sample_indices = self._sample_rng.choice(n_pairs, self.max_coarse_pairs, replace=False)
            pairs_to_compute = [pairs_to_compute[i] for i in sample_indices]

            # CRITICAL: Update _last_pairs_to_compute and _last_step_active_pairs to match
            # the ACTUAL sampled pairs that will be used to generate tokens.
            # This fixes the out-of-bounds index error in transformer_encoder.py Tier 3 code
            # where token indices are computed from _last_pairs_to_compute but rel_stack
            # only has tokens for the sampled pairs.
            self._last_pairs_to_compute = pairs_to_compute
            # Rebuild directed pairs from the sampled undirected pairs
            self._last_step_active_pairs = set()
            for (i, j) in pairs_to_compute:
                self._last_step_active_pairs.add((i, j))
                self._last_step_active_pairs.add((j, i))

            # Log once per training session (not every forward pass)
            if not hasattr(self, '_coarse_sample_logged'):
                logger.info(f"🎯 Coarse exploration: sampling {self.max_coarse_pairs}/{n_pairs} pairs "
                           f"({100*self.max_coarse_pairs/n_pairs:.1f}%)")
                self._coarse_sample_logged = True
        
        # ============================================================================
        # SCALABLE CHUNKED COMPUTATION
        # ============================================================================
        # Problem: With 200 columns, we have 19,900 pairs to compute.
        # Computing all at once can exceed memory limits on MPS/CUDA.
        # EMPIRICAL: Each pair uses ~4.4MB at batch=128 due to autograd graph!
        #
        # Solution: Chunk pairs into manageable batches based on GPU memory
        # GPU-aware max_pairs_per_chunk is computed in __init__ based on available RAM
        # 24GB GPU @ batch=128 → ~550 pairs; 95GB @ batch=256 → ~1000 pairs
        # ============================================================================
        max_chunk = self.max_pairs_per_chunk  # GPU-aware limit from __init__
        
        n_pairs = len(pairs_to_compute)
        
        if n_pairs <= max_chunk:
            # Small enough to compute in one go
            result = self._compute_operations_batched(
                column_encodings,
                mask,
                pairs_to_compute,
                is_exploration,
                raw_timestamp_features,
                raw_domain_metadata,
            )
            # Record success - we completed without OOM
            if hasattr(self, '_current_pair_count') and self._current_pair_count > 0:
                record_success(self._current_pair_count)
            return result
        else:
            # Chunk the pairs
            all_tokens = []
            n_chunks = (n_pairs + max_chunk - 1) // max_chunk
            
            # Log once per training session (not every forward pass)
            if not hasattr(self, '_chunking_logged'):
                logger.info(f"🔗 Relationship chunking: {n_pairs} pairs → {n_chunks} chunks of ≤{max_chunk}")
                self._chunking_logged = True
            
            for chunk_idx, chunk_start in enumerate(range(0, n_pairs, max_chunk)):
                chunk_end = min(chunk_start + max_chunk, n_pairs)
                chunk_pairs = pairs_to_compute[chunk_start:chunk_end]
                
                chunk_tokens = self._compute_operations_batched(
                    column_encodings,
                    mask,
                    chunk_pairs,
                    is_exploration,
                    raw_timestamp_features,
                    raw_domain_metadata,
                )
                
                # Extend all_tokens directly WITHOUT detaching
                # The original detach() was breaking gradient flow entirely, preventing
                # the operation MLPs from learning. PyTorch's autograd handles chunked
                # computations correctly without needing manual detach.
                # 
                # NOTE: Tokens MUST stay on GPU with autograd enabled because:
                # 1. They need gradients to flow back to the relationship MLPs (multiply_mlp, add_mlp, etc.)
                # 2. They're used in transformer attention which runs on GPU
                # 3. The transformer indexes into them: R[:, tgt, slot, :] = relationship_tokens[token_idx]
                #
                # The memory issue is that keeping many tokens in a Python list means each
                # tensor keeps its own autograd graph reference. The real solution is to:
                # - Reduce the number of pairs (already done with E scaling and hard cap)
                # - Use gradient checkpointing (already enabled in JointEncoder)
                # - Consider keeping tokens as a single stacked tensor (requires transformer changes)
                all_tokens.extend(chunk_tokens)
                
                # Clear references to allow garbage collection
                del chunk_tokens
                
                # Clear GPU cache between chunks
                if chunk_idx < n_chunks - 1:
                    try:
                        if column_encodings.is_cuda:
                            torch.cuda.empty_cache()
                    except Exception:
                        pass
            
            # Record success - we completed all chunks without OOM
            if hasattr(self, '_current_pair_count') and self._current_pair_count > 0:
                record_success(self._current_pair_count)
            return all_tokens
    
    def _compute_operations_batched(
        self,
        column_encodings: torch.Tensor,  # (batch_size, n_cols, d_model)
        mask: Optional[torch.Tensor],    # (batch_size, n_cols)
        pairs_to_compute: List[Tuple[int, int]],
        is_exploration: bool,
        raw_timestamp_features: Optional[Dict[int, torch.Tensor]] = None,  # {col_idx: (batch, 12)} for temporal ops
        raw_domain_metadata: Optional[Dict[int, list]] = None,  # {col_idx: [batch metadata dicts]} for email/domain ops
    ) -> List[torch.Tensor]:
        """
        Compute operations for all pairs in a batched way (MUCH faster than looping).
        
        Instead of:
          for (i, j) in pairs:
              multiply = emb_i * emb_j
              multiply_token = multiply_mlp(multiply)
        
        We do:
          all_multiplies = [emb_i * emb_j for all pairs]  # Shape: (n_pairs*batch, d_model)
          all_multiply_tokens = multiply_mlp(all_multiplies)  # Single MLP call
        
        This reduces Python loop overhead and improves GPU utilization.
        """
        batch_size, n_cols, d_model = column_encodings.shape
        n_pairs = len(pairs_to_compute)
        # CRITICAL: eps must be large enough to prevent division explosion
        # Embeddings are typically in [-0.5, 0.5] range after normalization
        # eps=1e-8 causes gradients to explode to 268M when dividing by near-zero values
        # eps=0.1 is ~20-50% of typical embedding magnitude, preventing extreme ratios
        eps = 0.1
        
        if n_pairs == 0:
            return []
        
        # Apply mask if provided
        if mask is not None:
            # Ensure mask is on the same device as column_encodings (MPS/CUDA/CPU)
            if mask.device != column_encodings.device:
                mask = mask.to(column_encodings.device)
            mask_expanded = mask.unsqueeze(-1)  # (batch_size, n_cols, 1)
            masked_encodings = column_encodings * mask_expanded
        else:
            masked_encodings = column_encodings
        
        # Extract all pairs at once
        indices_i = torch.tensor([i for i, j in pairs_to_compute], device=column_encodings.device)
        indices_j = torch.tensor([j for i, j in pairs_to_compute], device=column_encodings.device)
        
        # (n_pairs, batch_size, d_model) - gather all i and j embeddings
        emb_i_all = masked_encodings[:, indices_i, :].transpose(0, 1)  # (n_pairs, batch_size, d_model)
        emb_j_all = masked_encodings[:, indices_j, :].transpose(0, 1)
        
        # Compute pair masks and presence patterns
        if mask is not None:
            mask_i_all = mask[:, indices_i].transpose(0, 1).unsqueeze(-1)  # (n_pairs, batch_size, 1)
            mask_j_all = mask[:, indices_j].transpose(0, 1).unsqueeze(-1)
            pair_masks = mask_i_all * mask_j_all
            
            # Compute 4 mutually exclusive presence patterns for null-correlation learning
            # These capture structural relationships between column presence/absence
            both_present = mask_i_all * mask_j_all                    # A=1, B=1
            only_a_present = mask_i_all * (1 - mask_j_all)            # A=1, B=0
            only_b_present = (1 - mask_i_all) * mask_j_all            # A=0, B=1
            neither_present = (1 - mask_i_all) * (1 - mask_j_all)     # A=0, B=0
        else:
            pair_masks = torch.ones(n_pairs, batch_size, 1, device=column_encodings.device)
            # When no mask provided, assume all present
            both_present = torch.ones(n_pairs, batch_size, 1, device=column_encodings.device)
            only_a_present = torch.zeros(n_pairs, batch_size, 1, device=column_encodings.device)
            only_b_present = torch.zeros(n_pairs, batch_size, 1, device=column_encodings.device)
            neither_present = torch.zeros(n_pairs, batch_size, 1, device=column_encodings.device)
        
        # MEMORY FIX: Delete intermediate tensors no longer needed
        # NOTE: Embedding arithmetic has been REMOVED - we only compute presence patterns now
        # Type-aware ops handle semantic operations using raw data (not embeddings)
        del emb_i_all, emb_j_all, pair_masks
        if mask is not None:
            del mask_i_all, mask_j_all

        # Build presence pattern input: 4 binary flags concatenated
        # This is the ONLY generic operation - captures null-correlation structure
        # Shape: (n_pairs, batch_size, 4) -> flatten to (n_pairs * batch_size, 4)
        presence_patterns = torch.cat([
            both_present,       # (n_pairs, batch_size, 1)
            only_a_present,     # (n_pairs, batch_size, 1)
            only_b_present,     # (n_pairs, batch_size, 1)
            neither_present,    # (n_pairs, batch_size, 1)
        ], dim=-1)  # (n_pairs, batch_size, 4)
        presence_patterns_flat = presence_patterns.reshape(n_pairs * batch_size, 4)

        # Apply presence MLP - this is the ONLY generic operation
        # Outputs (n_pairs * batch_size, d_model) - already the right shape, no fusion needed
        presence_tokens = self.presence_mlp(presence_patterns_flat)
        del presence_patterns_flat

        if self.use_fusion:
            # PRESENCE-ONLY MODE: No fusion needed, presence_tokens is already d_model
            # Reshape to (n_pairs, batch_size, d_model)
            fused_tokens = presence_tokens.reshape(n_pairs, batch_size, d_model)
            
            # Build output list: 1 fused token per pair
            # Use contiguous() to ensure clean memory layout (avoids keeping parent tensor alive)
            relationship_tokens = []
            for pair_idx, (i, j) in enumerate(pairs_to_compute):
                token = fused_tokens[pair_idx].contiguous()  # (batch_size, d_model)
                relationship_tokens.append(token)
                # Track magnitude of generic fused tokens
                if self.training:
                    self._track_magnitude('generic_fused', token)

            # MEMORY FIX: Delete fused_tokens now that we've extracted the slices
            del fused_tokens

            # ============================================================================
            # TYPE-AWARE RELATIONSHIP OPERATIONS
            # ============================================================================
            # Add type-aware relationship tokens for specific column type combinations
            # Track usage statistics for logging
            n_set_ts = 0
            n_scalar_ts = 0
            n_set_set = 0
            n_set_scalar = 0
            n_scalar_scalar = 0
            n_email_domain = 0  # Email × Domain direct pairs
            n_email_domain_set = 0
            n_email_domain_scalar = 0
            n_email_domain_timestamp = 0
            n_email_domain_string = 0
            n_url_set = 0
            n_url_scalar = 0
            n_url_timestamp = 0
            n_url_string = 0

            if self.type_aware_config.enable_all_type_aware:
                # Precompute active type-aware pair sets for efficient lookup
                active_set_set = self.get_active_type_aware_pairs('set_set')
                active_scalar_scalar = self.get_active_type_aware_pairs('scalar_scalar')
                active_set_scalar = self.get_active_type_aware_pairs('set_scalar')
                active_set_timestamp = self.get_active_type_aware_pairs('set_timestamp')
                active_scalar_timestamp = self.get_active_type_aware_pairs('scalar_timestamp')
                # Email/Domain pair sets
                active_email_domain_set = self.get_active_type_aware_pairs('email_domain_set')
                active_email_domain_scalar = self.get_active_type_aware_pairs('email_domain_scalar')
                active_email_domain_timestamp = self.get_active_type_aware_pairs('email_domain_timestamp')
                active_email_domain_string = self.get_active_type_aware_pairs('email_domain_string')
                # URL pair sets
                active_url_set = self.get_active_type_aware_pairs('url_set')
                active_url_scalar = self.get_active_type_aware_pairs('url_scalar')
                active_url_timestamp = self.get_active_type_aware_pairs('url_timestamp')
                active_url_string = self.get_active_type_aware_pairs('url_string')

                for pair_idx, (i, j) in enumerate(pairs_to_compute):
                    # -----------------------------------------------------------------
                    # Timestamp × Timestamp: compute temporal deltas (existing)
                    # REPLACE generic token with type-aware token at same index
                    # -----------------------------------------------------------------
                    if self.temporal_ops is not None and raw_timestamp_features is not None:
                        if self.temporal_ops.is_timestamp_pair(i, j):
                            if i in raw_timestamp_features and j in raw_timestamp_features:
                                generic_token = relationship_tokens[pair_idx]
                                temporal_token, success = self._safe_type_aware_call(
                                    'timestamp_timestamp',
                                    self.temporal_ops.compute_timestamp_timestamp_relationship,
                                    generic_token,
                                    raw_timestamp_features[i],
                                    raw_timestamp_features[j],
                                )
                                if success:
                                    relationship_tokens[pair_idx] = temporal_token  # REPLACE, not append

                        # String × Timestamp: compute textual temporal relationships (existing)
                        # Note: This replaces AFTER timestamp×timestamp, so string×ts takes precedence
                        is_str_ts, str_idx, ts_idx = self.temporal_ops.is_string_timestamp_pair(i, j)
                        if is_str_ts and ts_idx in raw_timestamp_features:
                            string_emb = column_encodings[:, str_idx, :]  # (batch, d_model)
                            generic_token = relationship_tokens[pair_idx]
                            temporal_token, success = self._safe_type_aware_call(
                                'string_timestamp',
                                self.temporal_ops.compute_string_timestamp_relationship,
                                generic_token,
                                string_emb,
                                raw_timestamp_features[ts_idx],
                            )
                            if success:
                                relationship_tokens[pair_idx] = temporal_token  # REPLACE, not append

                    # -----------------------------------------------------------------
                    # Set × Timestamp: temporal distribution gating (NEW P0)
                    # REPLACE generic token with type-aware token at same index
                    # -----------------------------------------------------------------
                    if self.set_timestamp_ops is not None and raw_timestamp_features is not None:
                        is_set_ts, set_idx, ts_idx = self.is_set_timestamp_pair(i, j)
                        pair_key = (min(i, j), max(i, j))
                        if is_set_ts and ts_idx in raw_timestamp_features and (not active_set_timestamp or pair_key in active_set_timestamp):
                            set_emb = column_encodings[:, set_idx, :]
                            ts_emb = column_encodings[:, ts_idx, :]
                            generic_token = relationship_tokens[pair_idx]
                            set_ts_token, success = self._safe_type_aware_call(
                                'set_timestamp',
                                self.set_timestamp_ops,
                                generic_token,
                                set_emb,
                                ts_emb,
                                raw_timestamp_features[ts_idx],
                            )
                            if success:
                                relationship_tokens[pair_idx] = set_ts_token  # REPLACE, not append
                                n_set_ts += 1
                                if self.training:
                                    self._track_magnitude('set_timestamp', set_ts_token)

                    # -----------------------------------------------------------------
                    # Scalar × Timestamp: cyclical correlation (NEW P0)
                    # REPLACE generic token with type-aware token at same index
                    # -----------------------------------------------------------------
                    if self.scalar_timestamp_ops is not None and raw_timestamp_features is not None:
                        is_scalar_ts, scalar_idx, ts_idx = self.is_scalar_timestamp_pair(i, j)
                        pair_key = (min(i, j), max(i, j))
                        if is_scalar_ts and ts_idx in raw_timestamp_features and (not active_scalar_timestamp or pair_key in active_scalar_timestamp):
                            scalar_emb = column_encodings[:, scalar_idx, :]
                            ts_emb = column_encodings[:, ts_idx, :]
                            generic_token = relationship_tokens[pair_idx]
                            scalar_ts_token, success = self._safe_type_aware_call(
                                'scalar_timestamp',
                                self.scalar_timestamp_ops,
                                generic_token,
                                scalar_emb,
                                ts_emb,
                                raw_timestamp_features[ts_idx],
                            )
                            if success:
                                relationship_tokens[pair_idx] = scalar_ts_token  # REPLACE, not append
                                n_scalar_ts += 1
                                if self.training:
                                    self._track_magnitude('scalar_timestamp', scalar_ts_token)

                    # -----------------------------------------------------------------
                    # Set × Set: co-occurrence attention (NEW P1)
                    # REPLACE generic token with type-aware token at same index
                    # -----------------------------------------------------------------
                    if self.set_set_ops is not None:
                        pair_key = (min(i, j), max(i, j))
                        if self.is_set_pair(i, j) and (not active_set_set or pair_key in active_set_set):
                            set_a_emb = column_encodings[:, i, :]
                            set_b_emb = column_encodings[:, j, :]
                            generic_token = relationship_tokens[pair_idx]
                            set_set_token, success = self._safe_type_aware_call(
                                'set_set',
                                self.set_set_ops,
                                generic_token,
                                set_a_emb,
                                set_b_emb,
                            )
                            if success:
                                relationship_tokens[pair_idx] = set_set_token  # REPLACE, not append
                                n_set_set += 1
                                if self.training:
                                    self._track_magnitude('set_set', set_set_token)

                    # -----------------------------------------------------------------
                    # Set × Scalar: scalar-conditioned gating (NEW P1)
                    # REPLACE generic token with type-aware token at same index
                    # -----------------------------------------------------------------
                    if self.set_scalar_ops is not None:
                        is_set_scalar, set_idx, scalar_idx = self.is_set_scalar_pair(i, j)
                        pair_key = (min(i, j), max(i, j))
                        if is_set_scalar and (not active_set_scalar or pair_key in active_set_scalar):
                            set_emb = column_encodings[:, set_idx, :]
                            scalar_emb = column_encodings[:, scalar_idx, :]
                            generic_token = relationship_tokens[pair_idx]
                            set_scalar_token, success = self._safe_type_aware_call(
                                'set_scalar',
                                self.set_scalar_ops,
                                generic_token,
                                set_emb,
                                scalar_emb,
                            )
                            if success:
                                relationship_tokens[pair_idx] = set_scalar_token  # REPLACE, not append
                                n_set_scalar += 1
                                if self.training:
                                    self._track_magnitude('set_scalar', set_scalar_token)

                    # -----------------------------------------------------------------
                    # Scalar × Scalar: enhanced ratio encoding (NEW P2)
                    # REPLACE generic token with type-aware token at same index
                    # Supports strategy-aware ops when strategy_encodings are provided
                    # -----------------------------------------------------------------
                    if self.scalar_scalar_ops is not None:
                        pair_key = (min(i, j), max(i, j))
                        if self.is_scalar_pair(i, j) and (not active_scalar_scalar or pair_key in active_scalar_scalar):
                            # NOTE: strategy_scalar_scalar_ops is WIP - disabled until strategy_encodings is passed in
                            # Use blended embedding approach
                            scalar_a_emb = column_encodings[:, i, :]
                            scalar_b_emb = column_encodings[:, j, :]
                            generic_token = relationship_tokens[pair_idx]
                            scalar_scalar_token, success = self._safe_type_aware_call(
                                'scalar_scalar',
                                self.scalar_scalar_ops,
                                generic_token,
                                scalar_a_emb,
                                scalar_b_emb,
                            )
                            if success:
                                relationship_tokens[pair_idx] = scalar_scalar_token  # REPLACE, not append
                                n_scalar_scalar += 1
                                if self.training:
                                    self._track_magnitude('scalar_scalar', scalar_scalar_token)

                    # -----------------------------------------------------------------
                    # Email × Domain: direct email-to-domain relationship (NEW P3)
                    # REPLACE generic token with type-aware token at same index
                    # -----------------------------------------------------------------
                    if self.email_domain_ops is not None:
                        is_ed_pair, email_idx, domain_idx = self.is_email_domain_pair(i, j)
                        pair_key = (min(i, j), max(i, j))
                        active_email_domain = self.get_active_type_aware_pairs('email_domain')
                        if is_ed_pair and (not active_email_domain or pair_key in active_email_domain):
                            email_emb = column_encodings[:, email_idx, :]
                            domain_emb = column_encodings[:, domain_idx, :]
                            # Get metadata for both
                            email_meta = raw_domain_metadata.get(email_idx) if raw_domain_metadata else None
                            domain_meta = raw_domain_metadata.get(domain_idx) if raw_domain_metadata else None
                            generic_token = relationship_tokens[pair_idx]
                            ed_token, success = self._safe_type_aware_call(
                                'email_domain',
                                self.email_domain_ops,
                                generic_token,
                                email_emb,
                                domain_emb,
                                email_meta,
                                domain_meta,
                            )
                            if success:
                                relationship_tokens[pair_idx] = ed_token  # REPLACE, not append
                                n_email_domain += 1
                                if self.training:
                                    self._track_magnitude('email_domain', ed_token)

                    # -----------------------------------------------------------------
                    # Email/Domain × Set: free/corporate domain gating (NEW P3)
                    # REPLACE generic token with type-aware token at same index
                    # -----------------------------------------------------------------
                    if self.email_domain_set_ops is not None:
                        is_ed_set, ed_idx, set_idx = self.is_email_domain_set_pair(i, j)
                        pair_key = (min(i, j), max(i, j))
                        if is_ed_set and (not active_email_domain_set or pair_key in active_email_domain_set):
                            ed_emb = column_encodings[:, ed_idx, :]
                            set_emb = column_encodings[:, set_idx, :]
                            # Get domain metadata if available
                            domain_meta = raw_domain_metadata.get(ed_idx) if raw_domain_metadata else None
                            generic_token = relationship_tokens[pair_idx]
                            ed_set_token, success = self._safe_type_aware_call(
                                'email_domain_set',
                                self.email_domain_set_ops,
                                generic_token,
                                ed_emb,
                                set_emb,
                                domain_meta,
                            )
                            if success:
                                relationship_tokens[pair_idx] = ed_set_token  # REPLACE, not append
                                n_email_domain_set += 1

                    # -----------------------------------------------------------------
                    # Email/Domain × Scalar: domain effect on scalar values (NEW P3)
                    # REPLACE generic token with type-aware token at same index
                    # -----------------------------------------------------------------
                    if self.email_domain_scalar_ops is not None:
                        is_ed_scalar, ed_idx, scalar_idx = self.is_email_domain_scalar_pair(i, j)
                        pair_key = (min(i, j), max(i, j))
                        if is_ed_scalar and (not active_email_domain_scalar or pair_key in active_email_domain_scalar):
                            ed_emb = column_encodings[:, ed_idx, :]
                            scalar_emb = column_encodings[:, scalar_idx, :]
                            # Get domain metadata if available
                            domain_meta = raw_domain_metadata.get(ed_idx) if raw_domain_metadata else None
                            generic_token = relationship_tokens[pair_idx]
                            ed_scalar_token, success = self._safe_type_aware_call(
                                'email_domain_scalar',
                                self.email_domain_scalar_ops,
                                generic_token,
                                ed_emb,
                                scalar_emb,
                                domain_meta,
                            )
                            if success:
                                relationship_tokens[pair_idx] = ed_scalar_token  # REPLACE, not append
                                n_email_domain_scalar += 1

                    # -----------------------------------------------------------------
                    # Email/Domain × Timestamp: domain time patterns (NEW P3)
                    # REPLACE generic token with type-aware token at same index
                    # -----------------------------------------------------------------
                    if self.email_domain_timestamp_ops is not None and raw_timestamp_features is not None:
                        is_ed_ts, ed_idx, ts_idx = self.is_email_domain_timestamp_pair(i, j)
                        pair_key = (min(i, j), max(i, j))
                        if is_ed_ts and ts_idx in raw_timestamp_features and (not active_email_domain_timestamp or pair_key in active_email_domain_timestamp):
                            ed_emb = column_encodings[:, ed_idx, :]
                            ts_emb = column_encodings[:, ts_idx, :]
                            # Get domain metadata if available
                            domain_meta = raw_domain_metadata.get(ed_idx) if raw_domain_metadata else None
                            generic_token = relationship_tokens[pair_idx]
                            ed_ts_token, success = self._safe_type_aware_call(
                                'email_domain_timestamp',
                                self.email_domain_timestamp_ops,
                                generic_token,
                                ed_emb,
                                ts_emb,
                                raw_timestamp_features[ts_idx],
                                domain_meta,
                            )
                            if success:
                                relationship_tokens[pair_idx] = ed_ts_token  # REPLACE, not append
                                n_email_domain_timestamp += 1

                    # -----------------------------------------------------------------
                    # Email/Domain × String: domain main part semantics (NEW P3)
                    # REPLACE generic token with type-aware token at same index
                    # -----------------------------------------------------------------
                    if self.email_domain_string_ops is not None:
                        is_ed_str, ed_idx, str_idx = self.is_email_domain_string_pair(i, j)
                        pair_key = (min(i, j), max(i, j))
                        if is_ed_str and (not active_email_domain_string or pair_key in active_email_domain_string):
                            ed_emb = column_encodings[:, ed_idx, :]
                            str_emb = column_encodings[:, str_idx, :]
                            # Get domain metadata if available
                            domain_meta = raw_domain_metadata.get(ed_idx) if raw_domain_metadata else None
                            generic_token = relationship_tokens[pair_idx]
                            ed_str_token, success = self._safe_type_aware_call(
                                'email_domain_string',
                                self.email_domain_string_ops,
                                generic_token,
                                ed_emb,
                                str_emb,
                                domain_meta,
                            )
                            if success:
                                relationship_tokens[pair_idx] = ed_str_token  # REPLACE, not append
                                n_email_domain_string += 1

                    # -----------------------------------------------------------------
                    # URL × Set: URL presence/protocol/TLD gating (NEW P4)
                    # REPLACE generic token with type-aware token at same index
                    # -----------------------------------------------------------------
                    if self.url_set_ops is not None:
                        is_url_set, url_idx, set_idx = self.is_url_set_pair(i, j)
                        pair_key = (min(i, j), max(i, j))
                        if is_url_set and (not active_url_set or pair_key in active_url_set):
                            url_emb = column_encodings[:, url_idx, :]
                            set_emb = column_encodings[:, set_idx, :]
                            generic_token = relationship_tokens[pair_idx]
                            url_set_token, success = self._safe_type_aware_call(
                                'url_set',
                                self.url_set_ops,
                                generic_token,
                                url_emb,
                                set_emb,
                            )
                            if success:
                                relationship_tokens[pair_idx] = url_set_token  # REPLACE, not append
                                n_url_set += 1

                    # -----------------------------------------------------------------
                    # URL × Scalar: URL features × scalar correlation (NEW P4)
                    # REPLACE generic token with type-aware token at same index
                    # -----------------------------------------------------------------
                    if self.url_scalar_ops is not None:
                        is_url_scalar, url_idx, scalar_idx = self.is_url_scalar_pair(i, j)
                        pair_key = (min(i, j), max(i, j))
                        if is_url_scalar and (not active_url_scalar or pair_key in active_url_scalar):
                            url_emb = column_encodings[:, url_idx, :]
                            scalar_emb = column_encodings[:, scalar_idx, :]
                            generic_token = relationship_tokens[pair_idx]
                            url_scalar_token, success = self._safe_type_aware_call(
                                'url_scalar',
                                self.url_scalar_ops,
                                generic_token,
                                url_emb,
                                scalar_emb,
                            )
                            if success:
                                relationship_tokens[pair_idx] = url_scalar_token  # REPLACE, not append
                                n_url_scalar += 1

                    # -----------------------------------------------------------------
                    # URL × Timestamp: URL × time patterns (NEW P4)
                    # REPLACE generic token with type-aware token at same index
                    # -----------------------------------------------------------------
                    if self.url_timestamp_ops is not None and raw_timestamp_features is not None:
                        is_url_ts, url_idx, ts_idx = self.is_url_timestamp_pair(i, j)
                        pair_key = (min(i, j), max(i, j))
                        if is_url_ts and ts_idx in raw_timestamp_features and (not active_url_timestamp or pair_key in active_url_timestamp):
                            url_emb = column_encodings[:, url_idx, :]
                            ts_emb = column_encodings[:, ts_idx, :]
                            generic_token = relationship_tokens[pair_idx]
                            url_ts_token, success = self._safe_type_aware_call(
                                'url_timestamp',
                                self.url_timestamp_ops,
                                generic_token,
                                url_emb,
                                ts_emb,
                                raw_timestamp_features[ts_idx],
                            )
                            if success:
                                relationship_tokens[pair_idx] = url_ts_token  # REPLACE, not append
                                n_url_timestamp += 1

                    # -----------------------------------------------------------------
                    # URL × String: URL path/query × string semantics (NEW P4)
                    # REPLACE generic token with type-aware token at same index
                    # -----------------------------------------------------------------
                    if self.url_string_ops is not None:
                        is_url_str, url_idx, str_idx = self.is_url_string_pair(i, j)
                        pair_key = (min(i, j), max(i, j))
                        if is_url_str and (not active_url_string or pair_key in active_url_string):
                            url_emb = column_encodings[:, url_idx, :]
                            str_emb = column_encodings[:, str_idx, :]
                            generic_token = relationship_tokens[pair_idx]
                            url_str_token, success = self._safe_type_aware_call(
                                'url_string',
                                self.url_string_ops,
                                generic_token,
                                url_emb,
                                str_emb,
                            )
                            if success:
                                relationship_tokens[pair_idx] = url_str_token  # REPLACE, not append
                                n_url_string += 1

            # Update type-aware stats
            type_aware_total = (n_set_ts + n_scalar_ts + n_set_set + n_set_scalar + n_scalar_scalar +
                               n_email_domain_set + n_email_domain_scalar + n_email_domain_timestamp + n_email_domain_string +
                               n_url_set + n_url_scalar + n_url_timestamp + n_url_string)
            self._type_aware_stats['set_timestamp_pairs'] += n_set_ts
            self._type_aware_stats['scalar_timestamp_pairs'] += n_scalar_ts
            self._type_aware_stats['set_set_pairs'] += n_set_set
            self._type_aware_stats['set_scalar_pairs'] += n_set_scalar
            self._type_aware_stats['scalar_scalar_pairs'] += n_scalar_scalar
            self._type_aware_stats['email_domain_pairs'] += n_email_domain
            self._type_aware_stats['email_domain_set_pairs'] += n_email_domain_set
            self._type_aware_stats['email_domain_scalar_pairs'] += n_email_domain_scalar
            self._type_aware_stats['email_domain_timestamp_pairs'] += n_email_domain_timestamp
            self._type_aware_stats['email_domain_string_pairs'] += n_email_domain_string
            self._type_aware_stats['url_set_pairs'] += n_url_set
            self._type_aware_stats['url_scalar_pairs'] += n_url_scalar
            self._type_aware_stats['url_timestamp_pairs'] += n_url_timestamp
            self._type_aware_stats['url_string_pairs'] += n_url_string
            self._type_aware_stats['generic_pairs'] += (n_pairs - type_aware_total)
            self._type_aware_stats['total_forward_calls'] += 1

            # ========================================================================
            # DEBUG: Log relationship token stats (first few forward calls)
            # ========================================================================
            if not hasattr(self, '_rel_token_debug_count'):
                self._rel_token_debug_count = 0
            self._rel_token_debug_count += 1
            if self._rel_token_debug_count <= 3:
                with torch.no_grad():
                    # Stack all tokens for analysis
                    all_tokens = torch.stack(relationship_tokens, dim=0)  # (n_tokens, batch, d_model)
                    token_norms = all_tokens.norm(dim=-1)  # (n_tokens, batch)
                    token_vars = all_tokens.var(dim=-1)  # (n_tokens, batch)

                    logger.info(f"🔬 [RelTokens] Forward #{self._rel_token_debug_count}:")
                    logger.info(f"   n_tokens={len(relationship_tokens)}, batch={batch_size}, d_model={d_model}")
                    logger.info(f"   Token norms: mean={token_norms.mean():.3f}, std={token_norms.std():.3f}, min={token_norms.min():.3f}, max={token_norms.max():.3f}")
                    logger.info(f"   Token variance: mean={token_vars.mean():.4f}")

                    # Check token diversity - are all tokens the same?
                    token_mean = all_tokens.mean(dim=0)  # (batch, d_model) - average token
                    deviations = (all_tokens - token_mean.unsqueeze(0)).norm(dim=-1)  # How much each token differs from mean
                    logger.info(f"   Token diversity (deviation from mean): {deviations.mean():.3f} (0=all identical)")

                    # Pairwise cosine similarity between tokens
                    if len(relationship_tokens) >= 2:
                        t0 = all_tokens[0]  # (batch, d_model)
                        t1 = all_tokens[1]  # (batch, d_model)
                        cos_01 = F.cosine_similarity(t0, t1, dim=-1).mean().item()
                        logger.info(f"   Token[0] vs Token[1] cosine: {cos_01:.3f} (1.0=identical direction)")

            # NaN ASSERTION: Check all relationship tokens before returning
            for tok_idx, token in enumerate(relationship_tokens):
                assert not torch.isnan(token).any(), f"NaN in relationship_token[{tok_idx}]! Check type-aware ops."
                assert not torch.isinf(token).any(), f"Inf in relationship_token[{tok_idx}]! Check type-aware ops."

            return relationship_tokens
        else:
            # UNFUSED MODE: Return 1 presence token per pair (simplified - no embedding arithmetic)
            # Reshape back to (n_pairs, batch_size, d_model)
            presence_tokens = presence_tokens.reshape(n_pairs, batch_size, d_model)

            # Build output list: 1 presence token per pair
            # Use contiguous() to create clean copies instead of views
            relationship_tokens = []
            for pair_idx, (i, j) in enumerate(pairs_to_compute):
                relationship_tokens.append(presence_tokens[pair_idx].contiguous())

            # MEMORY FIX: Delete the reshaped tensor now that we've extracted slices
            del presence_tokens

            # ============================================================================
            # TYPE-AWARE RELATIONSHIP OPERATIONS - UNFUSED MODE
            # ============================================================================
            # TODO: In unfused mode, type-aware ops are appended as extra tokens rather
            # than replacing generic tokens. This works because unfused mode is rarely
            # used and the extra tokens still contribute to learning, but should ideally
            # replace one of the 9 generic tokens per pair (e.g., the multiply token).
            # Track usage statistics
            n_set_ts = 0
            n_scalar_ts = 0
            n_set_set = 0
            n_set_scalar = 0
            n_scalar_scalar = 0

            if self.type_aware_config.enable_all_type_aware:
                for pair_idx, (i, j) in enumerate(pairs_to_compute):
                    # Timestamp × Timestamp (existing)
                    if self.temporal_ops is not None and raw_timestamp_features is not None:
                        if self.temporal_ops.is_timestamp_pair(i, j):
                            if i in raw_timestamp_features and j in raw_timestamp_features:
                                temporal_token = self.temporal_ops.compute_timestamp_timestamp_relationship(
                                    raw_timestamp_features[i],
                                    raw_timestamp_features[j],
                                )
                                relationship_tokens.append(temporal_token)

                        is_str_ts, str_idx, ts_idx = self.temporal_ops.is_string_timestamp_pair(i, j)
                        if is_str_ts and ts_idx in raw_timestamp_features:
                            string_emb = column_encodings[:, str_idx, :]
                            temporal_token = self.temporal_ops.compute_string_timestamp_relationship(
                                string_emb,
                                raw_timestamp_features[ts_idx],
                            )
                            relationship_tokens.append(temporal_token)

                    # Set × Timestamp (NEW P0)
                    if self.set_timestamp_ops is not None and raw_timestamp_features is not None:
                        is_set_ts, set_idx, ts_idx = self.is_set_timestamp_pair(i, j)
                        if is_set_ts and ts_idx in raw_timestamp_features:
                            set_emb = column_encodings[:, set_idx, :]
                            ts_emb = column_encodings[:, ts_idx, :]
                            set_ts_token = self.set_timestamp_ops(
                                set_emb, ts_emb, raw_timestamp_features[ts_idx]
                            )
                            relationship_tokens.append(set_ts_token)
                            n_set_ts += 1

                    # Scalar × Timestamp (NEW P0)
                    if self.scalar_timestamp_ops is not None and raw_timestamp_features is not None:
                        is_scalar_ts, scalar_idx, ts_idx = self.is_scalar_timestamp_pair(i, j)
                        if is_scalar_ts and ts_idx in raw_timestamp_features:
                            scalar_emb = column_encodings[:, scalar_idx, :]
                            ts_emb = column_encodings[:, ts_idx, :]
                            scalar_ts_token = self.scalar_timestamp_ops(
                                scalar_emb, ts_emb, raw_timestamp_features[ts_idx]
                            )
                            relationship_tokens.append(scalar_ts_token)
                            n_scalar_ts += 1

                    # Set × Set (NEW P1)
                    if self.set_set_ops is not None and self.is_set_pair(i, j):
                        set_a_emb = column_encodings[:, i, :]
                        set_b_emb = column_encodings[:, j, :]
                        set_set_token = self.set_set_ops(set_a_emb, set_b_emb)
                        relationship_tokens.append(set_set_token)
                        n_set_set += 1

                    # Set × Scalar (NEW P1)
                    if self.set_scalar_ops is not None:
                        is_set_scalar, set_idx, scalar_idx = self.is_set_scalar_pair(i, j)
                        if is_set_scalar:
                            set_emb = column_encodings[:, set_idx, :]
                            scalar_emb = column_encodings[:, scalar_idx, :]
                            set_scalar_token = self.set_scalar_ops(set_emb, scalar_emb)
                            relationship_tokens.append(set_scalar_token)
                            n_set_scalar += 1

                    # Scalar × Scalar (NEW P2)
                    # NOTE: strategy_scalar_scalar_ops is WIP - disabled until strategy_encodings is passed in
                    if self.scalar_scalar_ops is not None and self.is_scalar_pair(i, j):
                        scalar_a_emb = column_encodings[:, i, :]
                        scalar_b_emb = column_encodings[:, j, :]
                        scalar_scalar_token = self.scalar_scalar_ops(scalar_a_emb, scalar_b_emb)
                        relationship_tokens.append(scalar_scalar_token)
                        n_scalar_scalar += 1

            # Update type-aware stats
            type_aware_total = n_set_ts + n_scalar_ts + n_set_set + n_set_scalar + n_scalar_scalar
            self._type_aware_stats['set_timestamp_pairs'] += n_set_ts
            self._type_aware_stats['scalar_timestamp_pairs'] += n_scalar_ts
            self._type_aware_stats['set_set_pairs'] += n_set_set
            self._type_aware_stats['set_scalar_pairs'] += n_set_scalar
            self._type_aware_stats['scalar_scalar_pairs'] += n_scalar_scalar
            self._type_aware_stats['generic_pairs'] += (n_pairs - type_aware_total)
            self._type_aware_stats['total_forward_calls'] += 1

            # NaN ASSERTION: Check all relationship tokens before returning (unfused mode)
            for tok_idx, token in enumerate(relationship_tokens):
                assert not torch.isnan(token).any(), f"NaN in relationship_token[{tok_idx}]! (unfused mode)"
                assert not torch.isinf(token).any(), f"Inf in relationship_token[{tok_idx}]! (unfused mode)"

            return relationship_tokens
    
    def _compute_operations(
        self,
        emb_a: torch.Tensor,  # (batch, d_model) - not used, kept for API compatibility
        emb_b: torch.Tensor,  # (batch, d_model) - not used, kept for API compatibility
        mask: torch.Tensor,   # (batch, 1) - pair mask (A*B present) - not used
        mask_a: Optional[torch.Tensor] = None,  # (batch, 1) - A present
        mask_b: Optional[torch.Tensor] = None,  # (batch, 1) - B present
        track_operations: bool = False,  # Unused - kept for API compatibility
    ) -> List[torch.Tensor]:
        """
        Compute presence pattern operation between two columns.

        NOTE: Embedding arithmetic operations have been REMOVED.
        Type-aware ops handle semantic operations using raw data (not embeddings).

        Returns:
            List with 1 token (batch, d_model) - presence pattern (null-correlation)
        """
        # Presence pattern: null-correlation structure (4 mutually exclusive patterns)
        # This is the ONLY generic operation - captures which columns are present/missing together
        if mask_a is not None and mask_b is not None:
            both_present = mask_a * mask_b                    # A=1, B=1
            only_a_present = mask_a * (1 - mask_b)            # A=1, B=0
            only_b_present = (1 - mask_a) * mask_b            # A=0, B=1
            neither_present = (1 - mask_a) * (1 - mask_b)     # A=0, B=0
        else:
            # When individual masks not provided, assume all present
            batch_size = emb_a.shape[0]
            device = emb_a.device
            both_present = torch.ones(batch_size, 1, device=device)
            only_a_present = torch.zeros(batch_size, 1, device=device)
            only_b_present = torch.zeros(batch_size, 1, device=device)
            neither_present = torch.zeros(batch_size, 1, device=device)

        presence_pattern = torch.cat([both_present, only_a_present, only_b_present, neither_present], dim=-1)
        presence_token = self.presence_mlp(presence_pattern)

        # Return as list for API compatibility (both fused and unfused modes)
        return [presence_token]
    
    def _update_contribution(self, pair: Tuple[int, int], gradient: torch.Tensor):
        """
        Update contribution score for a pair based on gradient magnitude.
        
        Called via backward hook during training.
        Uses exponential moving average to smooth contributions over batches.
        """
        if not self.training:
            return
        
        # Measure contribution as mean absolute gradient
        contribution = gradient.abs().mean().item()
        
        # Exponential moving average
        alpha = self._contribution_ema_alpha
        self.pair_contributions[pair] = (
            alpha * contribution + 
            (1 - alpha) * self.pair_contributions[pair]
        )
    
    def _update_operation_contribution(self, op_name: str, gradient: torch.Tensor):
        """
        Update contribution score for an operation type.
        
        Tracks which operations (multiply, add, subtract, divide) are most effective.
        """
        if not self.training:
            return
        
        # Measure contribution as mean absolute gradient
        contribution = gradient.abs().mean().item()
        
        # Exponential moving average
        alpha = self._contribution_ema_alpha
        self.operation_contributions[op_name] = (
            alpha * contribution + 
            (1 - alpha) * self.operation_contributions[op_name]
        )
    
    def track_contribution_snapshot(self):
        """Save contribution snapshot for stability analysis."""
        snapshot = self.pair_contributions.copy()
        self.contribution_history.append(snapshot)
    
    def update_contributions_from_gradients(self):
        """
        Update pair contributions by checking gradients on retained tokens.
        
        Call this AFTER loss.backward() in the training loop.
        The gradients tell us how much each relationship token contributed to the loss.
        """
        if not self._tokens_for_gradient_check:
            logger.warning("⚠️  DynamicRelationshipExtractor: No tokens to check gradients - retain_grad() may not be working!")
            return
        
        updates_made = 0
        grad_stats = []
        missing_grads = 0
        
        for (i, j), token in self._tokens_for_gradient_check:
            if token.grad is not None:
                grad_magnitude = token.grad.abs().mean().item()
                grad_stats.append(grad_magnitude)
                # Pass the raw gradient tensor to _update_contribution
                # It will compute abs().mean().item() and apply EMA smoothing
                self._update_contribution((i, j), token.grad)
                updates_made += 1
            else:
                missing_grads += 1
        
        # Clear the list for next batch
        self._tokens_for_gradient_check.clear()
        
        # Increment batch counter and log periodically
        self._batch_counter += 1
        should_log = (self._batch_counter % self._log_every_n_batches == 0) or self._batch_counter == 1
        
        # Log every N batches during exploration with detailed stats
        if (updates_made > 0 or missing_grads > 0) and should_log:
            nonzero = sum(1 for c in self.pair_contributions.values() if c > 1e-9)
            if grad_stats:
                avg_grad = sum(grad_stats) / len(grad_stats)
                max_grad = max(grad_stats)
                min_grad = min(grad_stats)
                logger.info(
                    f"🔗 [Epoch {self.current_epoch}, Batch {self._batch_counter}] Updated {updates_made} relationship contributions, "
                    f"{nonzero}/{len(self.pair_contributions)} non-zero pairs | "
                    f"Grad: avg={avg_grad:.6f}, max={max_grad:.6f}, min={min_grad:.6f}"
                )
            
            if missing_grads > 0:
                logger.warning(
                    f"⚠️  [Epoch {self.current_epoch}] {missing_grads}/{updates_made+missing_grads} tokens had NO gradient! "
                    f"This means retain_grad() isn't working properly."
                )
    
    def capture_gradient_norms(self):
        """
        Capture gradient norms right after loss.backward(), before optimizer.step()/zero_grad().

        Call this immediately after loss.backward() in the training loop.
        Stores the MAX gradient norm seen across batches (most representative of learning activity).
        """
        current_grad_norms = {}

        # Build list of all MLPs to track (generic + type-aware ops)
        mlps_to_track = [
            ('presence', self.presence_mlp),  # NULL-correlation pattern - the ONLY generic op
            ('null', self.null_relationship_mlp),  # Contextual NULL - no gradients are good on this one
        ]
        # Add type-aware ops if they exist
        if self.scalar_scalar_ops is not None:
            mlps_to_track.append(('scalar_scalar', self.scalar_scalar_ops))
        if self.set_set_ops is not None:
            mlps_to_track.append(('set_set', self.set_set_ops))
        if self.set_scalar_ops is not None:
            mlps_to_track.append(('set_scalar', self.set_scalar_ops))
        if self.temporal_ops is not None:
            mlps_to_track.append(('temporal', self.temporal_ops))

        for op_name, mlp in mlps_to_track:
            total_grad_norm = 0.0
            has_grad = False

            for param in mlp.parameters():
                if param.requires_grad and param.grad is not None:
                    grad_norm_sq = param.grad.norm().item() ** 2
                    total_grad_norm += grad_norm_sq
                    has_grad = True

            current_norm = (total_grad_norm ** 0.5) if has_grad else 0.0
            current_grad_norms[op_name] = current_norm

            # Store max across batches (most representative of learning activity)
            if op_name not in self._stored_grad_norms:
                self._stored_grad_norms[op_name] = current_norm
            else:
                self._stored_grad_norms[op_name] = max(self._stored_grad_norms[op_name], current_norm)
    
    def _compute_weight_stats(self) -> Dict[str, Dict[str, float]]:
        """
        Compute weight statistics for each operation MLP.

        Uses stored gradient norms if available (captured after backward()),
        otherwise tries to read from current gradients (may be 0 if already zeroed).
        """
        stats = {}

        # Build list of all MLPs to track (generic + type-aware ops)
        mlps_to_track = [
            ('presence', self.presence_mlp),  # NULL-correlation pattern - the ONLY generic op
            ('null', self.null_relationship_mlp),  # Contextual NULL - no gradients are good on this one
        ]
        # Add type-aware ops if they exist
        if self.scalar_scalar_ops is not None:
            mlps_to_track.append(('scalar_scalar', self.scalar_scalar_ops))
        if self.set_set_ops is not None:
            mlps_to_track.append(('set_set', self.set_set_ops))
        if self.set_scalar_ops is not None:
            mlps_to_track.append(('set_scalar', self.set_scalar_ops))
        if self.temporal_ops is not None:
            mlps_to_track.append(('temporal', self.temporal_ops))

        for op_name, mlp in mlps_to_track:
            total_params = 0
            total_norm = 0.0
            total_grad_norm = 0.0
            has_grad = False
            
            # Try to use stored gradient norm first (captured after backward())
            if op_name in self._stored_grad_norms:
                total_grad_norm = self._stored_grad_norms[op_name]
                has_grad = total_grad_norm > 0.0
            else:
                # Fallback: try to read from current gradients (may be 0 if already zeroed)
                for param in mlp.parameters():
                    if param.requires_grad:
                        if param.grad is not None:
                            total_grad_norm += param.grad.norm().item() ** 2
                            has_grad = True
            
            # Always compute weight norm from current weights
            for param in mlp.parameters():
                if param.requires_grad:
                    total_params += param.numel()
                    total_norm += param.data.norm().item() ** 2
            
            stats[op_name] = {
                'weight_norm': total_norm ** 0.5,
                'grad_norm': total_grad_norm if has_grad else 0.0,
                'n_params': total_params,
                'has_grad': has_grad,
            }
        return stats
    
    def _compute_operation_similarity(self) -> Dict[Tuple[str, str], float]:
        """
        Compute pairwise cosine similarity between operation MLPs.

        NOTE: Embedding arithmetic MLPs have been removed - only presence_mlp remains.
        This method now returns an empty dict since there's nothing to compare.

        Returns:
            Dict mapping (op1, op2) -> cosine_similarity (empty)
        """
        # With only presence_mlp remaining, there's no pairwise comparison to do
        similarities = {}
        
        return similarities
    
    def _track_weight_learning(self) -> Dict[str, float]:
        """Track weight changes since last epoch. Returns delta per operation."""
        current_stats = self._compute_weight_stats()
        
        # Save snapshot for this epoch
        self._weight_snapshots[self.current_epoch] = {
            op: stats['weight_norm'] for op, stats in current_stats.items()
        }
        
        # Compute deltas from previous epoch
        deltas = {}
        if self.current_epoch > 0 and (self.current_epoch - 1) in self._weight_snapshots:
            prev_snapshot = self._weight_snapshots[self.current_epoch - 1]
            for op, stats in current_stats.items():
                prev_norm = prev_snapshot.get(op, stats['weight_norm'])
                delta = abs(stats['weight_norm'] - prev_norm)
                deltas[op] = delta
                
                # Track history
                if op not in self._weight_deltas:
                    self._weight_deltas[op] = []
                self._weight_deltas[op].append(delta)
        
        return deltas

    def _get_type_aware_op_for_pair(self, i: int, j: int) -> str:
        """
        Determine which type-aware operation (if any) is used for a column pair.
        Returns full name like 'SetSet', 'SetScalar', 'ScalarScalar', or 'Generic'.
        """
        if not hasattr(self, '_type_aware_scorers') or not self._type_aware_scorers:
            return "Generic"

        # Check each type-aware scorer for this pair
        pair = (i, j)
        pair_rev = (j, i)

        # Map scorer names to readable display names
        name_map = {
            'set_set': 'SetSet',
            'set_scalar': 'SetScalar',
            'scalar_scalar': 'ScalarScalar',
            'set_timestamp': 'SetTimestamp',
            'scalar_timestamp': 'ScalarTimestamp',
            'email_domain_set': 'EmailSet',
            'email_domain_scalar': 'EmailScalar',
            'email_domain_timestamp': 'EmailTimestamp',
            'email_domain_string': 'EmailString',
            'url_set': 'UrlSet',
            'url_scalar': 'UrlScalar',
            'url_timestamp': 'UrlTimestamp',
            'url_string': 'UrlString',
        }

        for scorer_name, scorer in self._type_aware_scorers.items():
            if hasattr(scorer, 'all_pairs') and scorer.all_pairs:
                if pair in scorer.all_pairs or pair_rev in scorer.all_pairs:
                    return name_map.get(scorer_name, scorer_name)

        return "Generic"

    def log_epoch_summary(self):
        """
        Log detailed epoch summary showing what relationships are being learned.
        Call this at the END of each epoch.
        """
        # Reset batch counter for next epoch
        self._batch_counter = 0
        
        # CRITICAL: Record epoch history for causal importance calculation
        # This must be called every epoch, not just during pruning
        active_pairs = [p for p in self.all_pairs if p not in self.disabled_pairs]
        if self.col_marginal_losses:
            self._record_epoch_history(self.current_epoch, active_pairs, self.col_marginal_losses)
        
        logger.info("")
        logger.info("=" * 100)
        logger.info(f"🔗 DYNAMIC RELATIONSHIP EXTRACTOR - EPOCH {self.current_epoch} SUMMARY")
        logger.info("=" * 100)
        
        # LEARNING CHECK: Are the operation MLPs learning?
        # CRITICAL: Compute stats BEFORE resetting stored gradient norms (they're needed for logging)
        weight_stats = self._compute_weight_stats()
        weight_deltas = self._track_weight_learning()
        
        logger.info(f"")
        logger.info(f"📈 Operation MLP Learning Status:")
        logger.info(f"   {'Operation':<12} {'Weights':>10} {'Grad Norm':>12} {'Δ (epoch)':>12} {'Learning?':>12}")
        logger.info(f"   {'-'*12} {'-'*10} {'-'*12} {'-'*12} {'-'*12}")
        
        any_learning = False
        for op, stats in weight_stats.items():
            delta = weight_deltas.get(op, 0.0)
            is_learning = delta > 1e-6 or stats['grad_norm'] > 1e-6
            any_learning = any_learning or is_learning
            learning_str = "✓ YES" if is_learning else "✗ NO"
            
            # Format grad_norm in scientific notation if very small (to avoid showing 0.000000)
            grad_norm = stats['grad_norm']
            if grad_norm > 0 and grad_norm < 1e-3:
                grad_norm_str = f"{grad_norm:.3e}"
            else:
                grad_norm_str = f"{grad_norm:.6f}"
            
            logger.info(f"   {op:<12} {stats['weight_norm']:>10.4f} {grad_norm_str:>12} {delta:>12.6f} {learning_str:>12}")
        
        if not any_learning:
            logger.warning(f"   ⚠️  NO RELATIONSHIP OPERATIONS ARE LEARNING! Check gradient flow.")
        else:
            logger.info(f"   ✅ Relationships are actively learning")
        
        # OPERATION DIFFERENTIATION CHECK: Are MLPs learning distinct functions?
        similarities = self._compute_operation_similarity()
        if similarities:
            logger.info(f"")
            logger.info(f"🔀 Operation MLP Differentiation (cosine similarity: -1=opposite, 0=orthogonal, +1=same):")
            
            # Determine health status using absolute values (closer to 0 = more distinct)
            max_abs_sim = max(abs(s) for s in similarities.values())
            avg_sim = sum(similarities.values()) / len(similarities)
            
            for (op1, op2), sim in sorted(similarities.items()):
                # Color-code based on absolute similarity (closer to 0 = more distinct)
                abs_sim = abs(sim)
                if abs_sim > 0.95:
                    status = "⚠️  COLLAPSED"  # Almost identical/opposite - bad
                elif abs_sim > 0.80:
                    status = "⚡ similar"     # Concerning
                elif abs_sim > 0.50:
                    status = "✓ distinct"    # Good differentiation
                else:
                    status = "✓✓ very distinct"  # Excellent - near orthogonal
                
                logger.info(f"   {op1:>10} vs {op2:<10}: {sim:>6.3f} {status}")
            
            # Summary based on absolute similarity
            if max_abs_sim > 0.95:
                logger.warning(f"   ⚠️  Operations may be collapsing to same function (max |similarity|={max_abs_sim:.3f})")
            elif max_abs_sim > 0.80:
                logger.info(f"   ⚡ Operations are similar but differentiating (max |sim|={max_abs_sim:.3f})")
            else:
                logger.info(f"   ✅ Operations are learning distinct transformations (avg={avg_sim:.3f})")
        
        # 1. COLUMN MARGINAL LOSSES (which columns are hard to predict?)
        if self.col_marginal_losses:
            logger.info(f"📊 Column Marginal Losses (higher = harder to predict = more important):")
            sorted_cols = sorted(self.col_marginal_losses.items(), key=lambda x: x[1], reverse=True)
            for i, (col, loss) in enumerate(sorted_cols[:15], 1):
                logger.info(f"   {i:2d}. {col:<30}: {loss:.4f}")
            logger.info("")
        
        # ============================================================================
        # COVERAGE STATS: Track relationship learning progress
        # ============================================================================
        # Compute E, K_exploit, K_explore for this epoch
        log2_N = np.log2(max(2, self.n_cols))
        E = max(1, min(32, int(np.ceil(log2_N))))
        K_exploit = E
        K_explore = E
        
        # Count active directed edges (average per step this epoch)
        if self._epoch_active_edges:
            avg_active_edges_per_step = np.mean(self._epoch_active_edges)
            active_directed_count = int(avg_active_edges_per_step)
        else:
            # Fallback: estimate from active pairs (each undirected pair = 2 directed)
            active_directed_count = len(active_pairs) * 2
        
        # Count columns with baseline available (NULL baseline)
        # Baseline is per-column, not per-pair
        cols_with_baseline = 0
        for col_name in self.col_names:
            if col_name in self._null_baseline_ema and self._null_baseline_ema[col_name] is not None:
                cols_with_baseline += 1
        
        # Count pairs eligible for NULL-source lift (both columns have baseline)
        pairs_eligible_for_null = 0
        for pair in active_pairs:
            i, j = pair
            col_i = self.col_names[i] if i < len(self.col_names) else None
            col_j = self.col_names[j] if j < len(self.col_names) else None
            has_baseline_i = col_i and col_i in self._null_baseline_ema and self._null_baseline_ema[col_i] is not None
            has_baseline_j = col_j and col_j in self._null_baseline_ema and self._null_baseline_ema[col_j] is not None
            if has_baseline_i or has_baseline_j:
                pairs_eligible_for_null += 1
        
        # Collect n_ij statistics (directed edges)
        n_ij_values = []
        for directed_pair in self._pair_stats.keys():
            stats = self._pair_stats[directed_pair]
            n_ij = stats.get('n', 0)
            if n_ij > 0:
                n_ij_values.append(n_ij)
        
        # Compute n_ij statistics
        max_n_ij = max(n_ij_values) if n_ij_values else 0
        mean_n_ij = np.mean(n_ij_values) if n_ij_values else 0.0
        p95_n_ij = np.percentile(n_ij_values, 95) if n_ij_values else 0.0
        
        # Compute n_total statistics (n_ij + n_ji) for undirected pairs - this is what's used for ranking
        n_total_values = []
        for pair in active_pairs:
            i, j = pair
            stats_ij = self._pair_stats.get((i, j), {})
            stats_ji = self._pair_stats.get((j, i), {})
            n_ij = stats_ij.get('n', 0)
            n_ji = stats_ji.get('n', 0)
            n_total = n_ij + n_ji
            if n_total > 0:
                n_total_values.append(n_total)
        
        max_n_total = max(n_total_values) if n_total_values else 0
        
        # ============================================================================
        # ADAPTIVE THRESHOLDS: Adjust based on actual observed support statistics
        # ============================================================================
        # Use percentile-based approach: set thresholds so that a reasonable fraction
        # of pairs with actual observations can be rankable
        original_min_support_rank = self.MIN_SUPPORT_RANK
        if n_total_values and len(n_total_values) >= 10:  # Need enough data to compute percentiles
            # Compute percentiles of actual observed support
            p50_n_total = np.percentile(n_total_values, 50)
            p75_n_total = np.percentile(n_total_values, 75)
            
            # Adaptive MIN_SUPPORT_RANK: use 50th percentile so ~50% of observed pairs can be rankable
            # But ensure it's not too low (at least 2x tracking threshold) or too high (not above 75th percentile)
            adaptive_rank = max(int(p50_n_total), self.MIN_SUPPORT_TRACK * 2)
            adaptive_rank = min(adaptive_rank, int(p75_n_total))  # Don't go above 75th percentile
            adaptive_rank = max(10, min(adaptive_rank, self._initial_min_support_rank))  # Clamp to [10, initial_value]
            
            if adaptive_rank < self.MIN_SUPPORT_RANK:
                self.MIN_SUPPORT_RANK = adaptive_rank
                logger.info(f"   ⚠️  Adaptive MIN_SUPPORT_RANK: {original_min_support_rank} → {self.MIN_SUPPORT_RANK} "
                          f"(p50_n_total={p50_n_total:.1f}, p75_n_total={p75_n_total:.1f}, max_n_total={max_n_total})")

            # ALSO adapt MIN_SUPPORT_PRUNE: use 75th percentile so ~25% of pairs are prunable
            # This ensures pruning can happen on small datasets where no pair reaches 500
            original_min_support_prune = self.MIN_SUPPORT_PRUNE
            adaptive_prune = max(int(p75_n_total), self.MIN_SUPPORT_RANK)  # At least as high as rank threshold
            adaptive_prune = max(25, min(adaptive_prune, original_min_support_prune))  # Clamp to [25, initial]
            if adaptive_prune < self.MIN_SUPPORT_PRUNE:
                self.MIN_SUPPORT_PRUNE = adaptive_prune
                logger.info(f"   ⚠️  Adaptive MIN_SUPPORT_PRUNE: {original_min_support_prune} → {self.MIN_SUPPORT_PRUNE} "
                          f"(p75_n_total={p75_n_total:.1f})")

        elif max_n_total > 0 and max_n_total < self.MIN_SUPPORT_RANK * 0.5:
            # Fallback: if we don't have enough data for percentiles, use max-based adjustment
            # Actual support is less than 50% of expected - lower threshold adaptively
            adaptive_rank = max(int(max_n_total * 1.5), self.MIN_SUPPORT_TRACK * 2)
            adaptive_rank = max(10, min(adaptive_rank, self.MIN_SUPPORT_RANK))
            if adaptive_rank < self.MIN_SUPPORT_RANK:
                self.MIN_SUPPORT_RANK = adaptive_rank
                logger.info(f"   ⚠️  Adaptive MIN_SUPPORT_RANK (fallback): {original_min_support_rank} → {self.MIN_SUPPORT_RANK} "
                          f"(max_n_total={max_n_total}, max_n_ij={max_n_ij})")

            # Also adapt MIN_SUPPORT_PRUNE in fallback
            original_min_support_prune = self.MIN_SUPPORT_PRUNE
            adaptive_prune = max(int(max_n_total * 0.8), self.MIN_SUPPORT_RANK)  # 80% of max, at least rank threshold
            adaptive_prune = max(25, min(adaptive_prune, original_min_support_prune))
            if adaptive_prune < self.MIN_SUPPORT_PRUNE:
                self.MIN_SUPPORT_PRUNE = adaptive_prune
                logger.info(f"   ⚠️  Adaptive MIN_SUPPORT_PRUNE (fallback): {original_min_support_prune} → {self.MIN_SUPPORT_PRUNE} "
                          f"(max_n_total={max_n_total})")
        
        # Count pairs with lift computed (has lift_ema in _pair_stats) - UNDIRECTED
        pairs_with_lift_undirected = 0
        for pair in active_pairs:
            i, j = pair
            stats_ij = self._pair_stats.get((i, j), {})
            stats_ji = self._pair_stats.get((j, i), {})
            lift_ij = stats_ij.get('lift_ema')
            lift_ji = stats_ji.get('lift_ema')
            if (lift_ij is not None and math.isfinite(lift_ij)) or (lift_ji is not None and math.isfinite(lift_ji)):
                pairs_with_lift_undirected += 1
        
        # Count directed edges with lift computed
        directed_edges_with_lift = 0
        for directed_pair, stats in self._pair_stats.items():
            lift_ema = stats.get('lift_ema')
            if lift_ema is not None and math.isfinite(lift_ema):
                directed_edges_with_lift += 1
        
        # Count rankable pairs (n >= MIN_SUPPORT_RANK && has null source) - UNDIRECTED
        # CRITICAL: For consistency with candidate selection, use n_total = n_ij + n_ji
        # This matches _compute_pair_scores which uses n_total for ranking
        rankable_pairs_undirected = 0
        for pair in active_pairs:
            i, j = pair
            stats_ij = self._pair_stats.get((i, j), {})
            stats_ji = self._pair_stats.get((j, i), {})
            n_ij = stats_ij.get('n', 0)
            n_ji = stats_ji.get('n', 0)
            n_total = n_ij + n_ji  # Sum of both directions (consistent with _compute_pair_scores)
            
            # Check if has null baseline source (either direction)
            source_counts_ij = stats_ij.get('source_counts', {})
            source_counts_ji = stats_ji.get('source_counts', {})
            has_null_ij = source_counts_ij.get('null', 0) > 0
            has_null_ji = source_counts_ji.get('null', 0) > 0
            
            # Rankable if: n_total >= MIN_SUPPORT_RANK AND has null baseline in at least one direction
            # Note: n_total can be ≥ MIN_SUPPORT_RANK even if individual n_ij < MIN_SUPPORT_RANK
            # This is consistent with how _compute_pair_scores computes rankability
            if n_total >= self.MIN_SUPPORT_RANK and (has_null_ij or has_null_ji):
                rankable_pairs_undirected += 1
        
        # Count rankable directed edges (n >= MIN_SUPPORT_RANK && has null source)
        rankable_directed_edges = 0
        for directed_pair, stats in self._pair_stats.items():
            n_ij = stats.get('n', 0)
            source_counts = stats.get('source_counts', {})
            has_null = source_counts.get('null', 0) > 0
            if n_ij >= self.MIN_SUPPORT_RANK and has_null:
                rankable_directed_edges += 1
        
        # Compute dropout stats
        dropout_stats = self._epoch_dropout_stats
        if dropout_stats['steps_with_dropout'] > 0:
            avg_edges_before = dropout_stats['total_edges_before'] / dropout_stats['steps_with_dropout']
            avg_edges_after = dropout_stats['total_edges_after'] / dropout_stats['steps_with_dropout']
            avg_dropped = dropout_stats['total_dropped'] / dropout_stats['steps_with_dropout']
            # Correct formula: drop_rate = (before - after) / before, then convert to percent
            observed_drop_rate = ((dropout_stats['total_edges_before'] - dropout_stats['total_edges_after']) / dropout_stats['total_edges_before']) if dropout_stats['total_edges_before'] > 0 else 0.0
        else:
            avg_edges_before = avg_edges_after = avg_dropped = 0
            observed_drop_rate = 0.0
        
        # Total possible directed edges
        total_possible_directed = self.n_cols * (self.n_cols - 1)
        total_possible_undirected = len(self.all_pairs)
        
        logger.info(f"📈 Relationship Coverage Stats:")
        logger.info(f"   Active directed edges (avg per step): {active_directed_count}")
        logger.info(f"   Columns with baseline available: {cols_with_baseline}/{len(self.col_names)} ({cols_with_baseline/len(self.col_names)*100:.1f}%)")
        logger.info(f"   Pairs eligible for NULL-source lift: {pairs_eligible_for_null}/{len(active_pairs)} ({pairs_eligible_for_null/len(active_pairs)*100:.1f}%)")
        logger.info(f"")
        logger.info(f"   n_ij statistics (directed edges): max={max_n_ij}, p95={p95_n_ij:.1f}, mean={mean_n_ij:.1f}")
        logger.info(f"")
        logger.info(f"   DIRECTED EDGES (i→j):")
        logger.info(f"      Total possible: {total_possible_directed}")
        logger.info(f"      With lift computed: {directed_edges_with_lift}/{total_possible_directed} ({directed_edges_with_lift/total_possible_directed*100:.1f}%)")
        logger.info(f"      Rankable (n≥{self.MIN_SUPPORT_RANK} && null_source): {rankable_directed_edges}/{total_possible_directed} ({rankable_directed_edges/total_possible_directed*100:.1f}%)")
        logger.info(f"")
        logger.info(f"   UNDIRECTED PAIRS (i,j) collapsed:")
        logger.info(f"      Total possible: {total_possible_undirected}")
        logger.info(f"      With lift computed (either direction): {pairs_with_lift_undirected}/{total_possible_undirected} ({pairs_with_lift_undirected/total_possible_undirected*100:.1f}%)")
        logger.info(f"      Rankable (n_total≥{self.MIN_SUPPORT_RANK} && null_source): {rankable_pairs_undirected}/{total_possible_undirected} ({rankable_pairs_undirected/total_possible_undirected*100:.1f}%)")
        logger.info(f"         Note: n_total = n_ij + n_ji (sum of both directions), so pairs can be rankable even if max(n_ij) < MIN_SUPPORT_RANK")
        logger.info(f"")
        logger.info(f"   MIN_SUPPORT_RANK: {self.MIN_SUPPORT_RANK}")
        logger.info(f"   Selection params: E={E}, K_exploit={K_exploit}, K_explore={K_explore}")
        if self.edge_dropout_prob > 0:
            logger.info(f"   Edge dropout: p={self.edge_dropout_prob:.1%}, observed={observed_drop_rate:.1%} "
                       f"(avg {avg_edges_before:.1f} → {avg_edges_after:.1f} edges/step)")
        else:
            logger.info(f"   Edge dropout: disabled")
        logger.info("")
        
        # Reset stats for next epoch
        self._epoch_dropout_stats = {
            'total_edges_before': 0,
            'total_edges_after': 0,
            'total_dropped': 0,
            'steps_with_dropout': 0,
        }
        self._epoch_active_edges = []
        
        # 2. RELATIONSHIP IMPORTANCE (using lift-based causal importance)
        # UNIFIED: Always use lift-based scores, not old loss-based heuristic
        importance_scores = self._compute_causal_importance(active_pairs)
        
        # DEBUG: Check for saturation issue
        importance_values = list(importance_scores.values())
        if importance_values:
            unique_values = set(importance_values)
            all_same = len(unique_values) == 1
            min_imp = min(importance_values)
            max_imp = max(importance_values)
            mean_imp = np.mean(importance_values)
            std_imp = np.std(importance_values) if len(importance_values) > 1 else 0.0
            
            if all_same or (max_imp - min_imp < 1e-6):
                logger.warning(f"⚠️  IMPORTANCE SCORE SATURATION DETECTED!")
                logger.warning(f"   All scores are identical: {importance_values[0]:.6f}")
                logger.warning(f"   This indicates a bug in importance calculation or normalization")
            else:
                logger.debug(f"📊 Importance score stats: mean={mean_imp:.6f}, std={std_imp:.6f}, range=[{min_imp:.6f}, {max_imp:.6f}]")
        
        # Sort by importance DESCENDING (higher = more important)
        sorted_pairs = sorted(importance_scores.items(), key=lambda x: x[1], reverse=True)
        
        total_pairs = len(sorted_pairs)
        active_pairs_count = total_pairs - len(self.disabled_pairs)
        
        logger.info(f"🏆 Top 40 Most Important Relationships (by lift-based importance; Δ = |loss_i - loss_j| shows easy↔hard pairing):")
        logger.info(f"   Note: Relationships are directional (i→j). Display shows dominant direction or both if similar.")
        # Show detailed debug for first pair in top list
        if sorted_pairs:
            (i_first, j_first), importance_first = sorted_pairs[0]
            col_i_first = self.col_names[i_first] if i_first < len(self.col_names) else f"col_{i_first}"
            col_j_first = self.col_names[j_first] if j_first < len(self.col_names) else f"col_{j_first}"
            loss_i_first = self.col_marginal_losses.get(col_i_first, 0.0)
            loss_j_first = self.col_marginal_losses.get(col_j_first, 0.0)
            abs_diff_first = abs(loss_i_first - loss_j_first)
            
            # Get breakdown from causal scorer if available
            if hasattr(self, 'causal_scorer'):
                try:
                    _, breakdown = self.causal_scorer.compute_importance((i_first, j_first))
                    logger.info(f"   🔍 DEBUG (first pair):")
                    logger.info(f"      pair=({col_i_first},{col_j_first})")
                    logger.info(f"      loss_i={loss_i_first:.4f} loss_j={loss_j_first:.4f} abs_diff={abs_diff_first:.4f}")
                    logger.info(f"      raw_importance={importance_first:.6f}")
                    logger.info(f"      breakdown: lcb_score={breakdown.get('lcb_score', 'N/A'):.6f}, "
                              f"lift_ij_mean={breakdown.get('lift_ij_mean', 'N/A'):.6f}, "
                              f"lift_ji_mean={breakdown.get('lift_ji_mean', 'N/A'):.6f}")
                except Exception as e:
                    logger.debug(f"   Could not get breakdown: {e}")
        
        # Build table rows
        table_rows = []
        for rank, ((i, j), importance) in enumerate(sorted_pairs[:40], 1):
            col_i = self.col_names[i] if i < len(self.col_names) else f"col_{i}"
            col_j = self.col_names[j] if j < len(self.col_names) else f"col_{j}"
            loss_i = self.col_marginal_losses.get(col_i, 0.0)
            loss_j = self.col_marginal_losses.get(col_j, 0.0)
            # Compute actual Δ = |loss_i - loss_j| (easy↔hard pairing difference)
            delta_loss = abs(loss_i - loss_j)
            is_active = (i, j) not in self.disabled_pairs
            status = "✓" if is_active else "✗"

            # Get directional lift information
            stats_ij = self._pair_stats.get((i, j), {})
            stats_ji = self._pair_stats.get((j, i), {})
            lift_ij = stats_ij.get('lift_ema', 0.0) if stats_ij.get('lift_ema') is not None else 0.0
            lift_ji = stats_ji.get('lift_ema', 0.0) if stats_ji.get('lift_ema') is not None else 0.0
            # Get peak lift and cumulative lift mass (captures historical contribution)
            lift_max_ij = stats_ij.get('lift_max') or 0.0
            lift_max_ji = stats_ji.get('lift_max') or 0.0
            lift_max = max(lift_max_ij, lift_max_ji)  # Peak across both directions
            lift_mass_ij = stats_ij.get('lift_mass', 0.0)
            lift_mass_ji = stats_ji.get('lift_mass', 0.0)
            lift_mass = lift_mass_ij + lift_mass_ji  # Total mass across both directions

            # Format relationship (show dominant direction or bidirectional)
            # Store columns separately for table display
            if abs(lift_ij - lift_ji) > 0.01:  # Significant difference
                if lift_ij > lift_ji:
                    # i→j is stronger
                    col1 = col_i
                    col2 = col_j
                    direction = "→"
                else:
                    # j→i is stronger
                    col1 = col_j
                    col2 = col_i
                    direction = "→"
            else:
                # Both directions similar - show as bidirectional
                col1 = col_i
                col2 = col_j
                direction = "↔"

            # Get type-aware op for this pair
            type_op = self._get_type_aware_op_for_pair(i, j)

            table_rows.append({
                'rank': rank,
                'col1': col1,
                'col2': col2,
                'direction': direction,
                'type_op': type_op,
                'delta': delta_loss,
                'importance': importance,
                'lift_ij': lift_ij,
                'lift_ji': lift_ji,
                'lift_max': lift_max,
                'lift_mass': lift_mass,
                'status': status
            })

        # Print table
        if table_rows:
            # Calculate column widths
            max_col1_len = max(len(row['col1']) for row in table_rows)
            max_col1_len = max(max_col1_len, len('Col 1'))
            max_col2_len = max(len(row['col2']) for row in table_rows)
            max_col2_len = max(max_col2_len, len('Col 2'))
            max_type_len = max(len(row['type_op']) for row in table_rows)
            max_type_len = max(max_type_len, len('Type'))

            # Header - 4 spaces between columns
            # Peak = max lift ever observed (captures "teaching" value)
            # Mass = cumulative positive lift (total contribution over training)
            header = f"   {'Rank':<6}    {'Col 1':<{max_col1_len}}    {'Col 2':<{max_col2_len}}    {'Type':<{max_type_len}}    {'Δ':<9}    {'Imp':<9}    {'Lift i→j':<10}    {'Lift j→i':<10}    {'Peak':<8}    {'Mass':<8}    {'Status':<8}"
            logger.info(header)
            # Separator line (same length as header, but with dashes)
            separator_len = len(header) - 3  # Subtract leading "   "
            logger.info("   " + "-" * separator_len)

            # Rows - 4 spaces between columns
            for row in table_rows:
                logger.info(f"   {row['rank']:<6}    {row['col1']:<{max_col1_len}}    {row['col2']:<{max_col2_len}}    {row['type_op']:<{max_type_len}}    {row['delta']:<9.4f}    {row['importance']:<9.4f}    {row['lift_ij']:<10.4f}    {row['lift_ji']:<10.4f}    {row['lift_max']:<8.4f}    {row['lift_mass']:<8.2f}    {row['status']:<8}")

        # Bottom 20 relationships (lowest importance = both columns at similar difficulty = prune candidates)
        logger.info(f"")
        logger.info(f"📉 Bottom 20 Least Important Relationships (by lift-based importance; low Δ = same-tier pairing):")
        logger.info(f"   Note: Relationships are directional (i→j). Display shows dominant direction or both if similar.")
        # Show detailed debug for first pair in bottom list
        if sorted_pairs:
            (i_last, j_last), importance_last = sorted_pairs[-1]
            col_i_last = self.col_names[i_last] if i_last < len(self.col_names) else f"col_{i_last}"
            col_j_last = self.col_names[j_last] if j_last < len(self.col_names) else f"col_{j_last}"
            loss_i_last = self.col_marginal_losses.get(col_i_last, 0.0)
            loss_j_last = self.col_marginal_losses.get(col_j_last, 0.0)
            abs_diff_last = abs(loss_i_last - loss_j_last)
            
            # Get breakdown from causal scorer if available
            if hasattr(self, 'causal_scorer'):
                try:
                    _, breakdown = self.causal_scorer.compute_importance((i_last, j_last))
                    logger.info(f"   🔍 DEBUG (last pair):")
                    logger.info(f"      pair=({col_i_last},{col_j_last})")
                    logger.info(f"      loss_i={loss_i_last:.4f} loss_j={loss_j_last:.4f} abs_diff={abs_diff_last:.4f}")
                    logger.info(f"      raw_importance={importance_last:.6f}")
                    logger.info(f"      breakdown: lcb_score={breakdown.get('lcb_score', 'N/A'):.6f}, "
                              f"lift_ij_mean={breakdown.get('lift_ij_mean', 'N/A'):.6f}, "
                              f"lift_ji_mean={breakdown.get('lift_ji_mean', 'N/A'):.6f}")
                except Exception as e:
                    logger.debug(f"   Could not get breakdown: {e}")
        
        # Build table rows
        table_rows = []
        for rank, ((i, j), importance) in enumerate(reversed(sorted_pairs[-20:]), 1):
            col_i = self.col_names[i] if i < len(self.col_names) else f"col_{i}"
            col_j = self.col_names[j] if j < len(self.col_names) else f"col_{j}"
            loss_i = self.col_marginal_losses.get(col_i, 0.0)
            loss_j = self.col_marginal_losses.get(col_j, 0.0)
            # Compute actual Δ = |loss_i - loss_j| (easy↔hard pairing difference)
            delta_loss = abs(loss_i - loss_j)
            is_active = (i, j) not in self.disabled_pairs
            status = "✓" if is_active else "✗"

            # Get directional lift information
            stats_ij = self._pair_stats.get((i, j), {})
            stats_ji = self._pair_stats.get((j, i), {})
            lift_ij = stats_ij.get('lift_ema', 0.0) if stats_ij.get('lift_ema') is not None else 0.0
            lift_ji = stats_ji.get('lift_ema', 0.0) if stats_ji.get('lift_ema') is not None else 0.0
            # Get peak lift and cumulative lift mass (captures historical contribution)
            lift_max_ij = stats_ij.get('lift_max') or 0.0
            lift_max_ji = stats_ji.get('lift_max') or 0.0
            lift_max = max(lift_max_ij, lift_max_ji)  # Peak across both directions
            lift_mass_ij = stats_ij.get('lift_mass', 0.0)
            lift_mass_ji = stats_ji.get('lift_mass', 0.0)
            lift_mass = lift_mass_ij + lift_mass_ji  # Total mass across both directions

            # Format relationship (show dominant direction or bidirectional)
            # Store columns separately for table display
            if abs(lift_ij - lift_ji) > 0.01:  # Significant difference
                if lift_ij > lift_ji:
                    # i→j is stronger
                    col1 = col_i
                    col2 = col_j
                    direction = "→"
                else:
                    # j→i is stronger
                    col1 = col_j
                    col2 = col_i
                    direction = "→"
            else:
                # Both directions similar - show as bidirectional
                col1 = col_i
                col2 = col_j
                direction = "↔"

            # Get type-aware op for this pair
            type_op = self._get_type_aware_op_for_pair(i, j)

            table_rows.append({
                'rank': rank,
                'col1': col1,
                'col2': col2,
                'direction': direction,
                'type_op': type_op,
                'delta': delta_loss,
                'importance': importance,
                'lift_ij': lift_ij,
                'lift_ji': lift_ji,
                'lift_max': lift_max,
                'lift_mass': lift_mass,
                'status': status
            })

        # Print table
        if table_rows:
            # Calculate column widths
            max_col1_len = max(len(row['col1']) for row in table_rows)
            max_col1_len = max(max_col1_len, len('Col 1'))
            max_col2_len = max(len(row['col2']) for row in table_rows)
            max_col2_len = max(max_col2_len, len('Col 2'))
            max_type_len = max(len(row['type_op']) for row in table_rows)
            max_type_len = max(max_type_len, len('Type'))

            # Header - 4 spaces between columns
            # Peak = max lift ever observed (captures "teaching" value)
            # Mass = cumulative positive lift (total contribution over training)
            header = f"   {'Rank':<6}    {'Col 1':<{max_col1_len}}    {'Col 2':<{max_col2_len}}    {'Type':<{max_type_len}}    {'Δ':<9}    {'Imp':<9}    {'Lift i→j':<10}    {'Lift j→i':<10}    {'Peak':<8}    {'Mass':<8}    {'Status':<8}"
            logger.info(header)
            # Separator line (same length as header, but with dashes)
            separator_len = len(header) - 3  # Subtract leading "   "
            logger.info("   " + "-" * separator_len)

            # Rows - 4 spaces between columns
            for row in table_rows:
                logger.info(f"   {row['rank']:<6}    {row['col1']:<{max_col1_len}}    {row['col2']:<{max_col2_len}}    {row['type_op']:<{max_type_len}}    {row['delta']:<9.4f}    {row['importance']:<9.4f}    {row['lift_ij']:<10.4f}    {row['lift_ji']:<10.4f}    {row['lift_max']:<8.4f}    {row['lift_mass']:<8.2f}    {row['status']:<8}")

        # Pruning status
        logger.info(f"")
        if self.progressive_pruning:
            total_pairs = len(self.all_pairs)
            active_pairs = total_pairs - len(self.disabled_pairs)
            target_remaining = int(total_pairs * self.top_k_fraction)
            
            if self.current_epoch < self.exploration_epochs:
                epochs_until_pruning = self.exploration_epochs - self.current_epoch
                logger.info(f"")
                logger.info(f"⏳ Exploration Phase: {epochs_until_pruning} epochs until progressive pruning starts")
            else:
                logger.info(f"")
                logger.info(f"🔪 Progressive Pruning Active:")
                logger.info(f"   Active pairs: {active_pairs}/{total_pairs} ({100*active_pairs/total_pairs:.1f}%)")
                logger.info(f"   Disabled: {len(self.disabled_pairs)} pairs")
                logger.info(f"   Target: {target_remaining} pairs ({self.top_k_fraction*100:.0f}%)")
                if active_pairs > target_remaining:
                    remaining_to_disable = active_pairs - target_remaining
                    logger.info(f"   Still need to disable: {remaining_to_disable} pairs")
                else:
                    logger.info(f"   ✅ Target reached!")
        elif self.pruned_pairs_per_column is None:
            epochs_until_pruning = max(0, self.exploration_epochs - self.current_epoch)
            logger.info(f"")
            logger.info(f"⏳ Exploration Phase: {epochs_until_pruning} epochs until pruning")
        else:
            # Show pruning statistics (old hard pruning method)
            total_active_pairs = sum(len(partners) for partners in self.pruned_pairs_per_column.values())
            pruning_ratio = total_active_pairs / total_pairs if total_pairs > 0 else 0
            logger.info(f"")
            logger.info(f"✂️  Pruning Active: {total_active_pairs}/{total_pairs} pairs ({100*pruning_ratio:.1f}%)")
        
        # Reset stored gradient norms for next epoch (AFTER logging, so we can use them above)
        # They will be captured during training in the next epoch
        self._stored_grad_norms = {}

        # Log type-aware ops usage statistics
        self.log_type_aware_stats(reset=True)

        # Log magnitude statistics (helps diagnose scale mismatches)
        self.log_magnitude_stats(reset=True)

        # Log per-op-type gradient statistics (shows which type-aware ops are learning)
        self.log_op_type_gradient_stats(reset=True)

        # Log type-aware pair scorer statistics
        self.log_type_aware_scorer_stats()

        # Log lift contribution by operation type (Option 3 - aggregate view)
        self.log_lift_contribution_by_type()

        # Generate lift visualizations if output directory is configured
        if self.viz_output_dir:
            try:
                self.save_all_lift_visualizations(
                    output_dir=self.viz_output_dir,
                    epoch=self.current_epoch,
                )
            except Exception as e:
                logger.warning(f"Failed to generate lift visualizations: {e}")

        logger.info("=" * 100)
        logger.info("")

    def log_exploration_progress(self):
        """
        DEPRECATED: This method is kept for backward compatibility but now uses
        the unified lift-based causal importance system instead of the old
        loss-based heuristic.
        
        The unified system is always active (from epoch 0), so this is just
        a logging wrapper that shows the same information as log_epoch_summary().
        """
        if not self.training:
            return
        
        logger.info("")
        logger.info(f"🔍 RELATIONSHIP EXPLORATION (epoch {self.current_epoch})")
        
        # Use unified lift-based causal importance (same as normal phase)
        active_pairs = [p for p in self.all_pairs if p not in self.disabled_pairs]
        if not active_pairs:
            logger.info("   ⏳ No active pairs to analyze...")
            return
        
        # Calculate importance scores using lift-based system
        importance_scores = self._compute_causal_importance(active_pairs)
        
        # Calculate statistics
        importance_values = list(importance_scores.values())
        if len(importance_values) == 0:
            mean_importance = 0.0
            std_importance = 0.0
            max_importance = 0.0
            min_importance = 0.0
        else:
            mean_importance = np.mean(importance_values)
            std_importance = np.std(importance_values) if len(importance_values) > 1 else 0.0
            max_importance = np.max(importance_values)
            min_importance = np.min(importance_values)
        
        active_pairs_count = len(active_pairs)
        
        logger.info(f"   Lift-based importance (causal lift from NULL baseline):")
        logger.info(f"   Mean: {mean_importance:.4f} ± {std_importance:.4f}")
        logger.info(f"   Range: [{min_importance:.4f}, {max_importance:.4f}]")
        logger.info(f"   Active pairs: {active_pairs_count}/{len(self.all_pairs)}")
        
        # Top 5 pairs by importance
        sorted_pairs = sorted(importance_scores.items(), key=lambda x: x[1], reverse=True)
        
        logger.info(f"   Top 5 pairs:")
        for (i, j), importance in sorted_pairs[:5]:
            col_i = self.col_names[i] if i < len(self.col_names) else f"col_{i}"
            col_j = self.col_names[j] if j < len(self.col_names) else f"col_{j}"
            logger.info(f"      {col_i:<20} ↔ {col_j:<20}: lift={importance:.4f}")
    
    def log_operation_statistics(self):
        """Log which operations are most effective."""
        logger.info("")
        logger.info("📊 OPERATION EFFECTIVENESS:")
        
        total = sum(self.operation_contributions.values())
        if total == 0:
            logger.info("   ⚠️  No operation contributions tracked yet")
            return
        
        for op, contrib in sorted(self.operation_contributions.items(), key=lambda x: x[1], reverse=True):
            pct = (contrib / total * 100) if total > 0 else 0
            logger.info(f"   {op:12s}: {contrib:.6f} ({pct:.1f}%)")
    
    def log_column_importance(self):
        """Log which columns have the most important relationships."""
        # Calculate total contribution for each column
        col_importance = {i: 0.0 for i in range(self.n_cols)}

        for (i, j), contrib in self.pair_contributions.items():
            col_importance[i] += contrib
            col_importance[j] += contrib

        # Sort by importance
        sorted_cols = sorted(
            col_importance.items(),
            key=lambda x: x[1],
            reverse=True
        )

        logger.info("")
        logger.info("📊 COLUMN IMPORTANCE (by relationship strength):")
        logger.info(f"   {'Rank':<6} {'Column':<30} {'Total Contribution':<20} {'Rel %'}")
        logger.info(f"   {'-'*6} {'-'*30} {'-'*20} {'-'*6}")

        total_contrib = sum(col_importance.values())
        for rank, (col_idx, importance) in enumerate(sorted_cols[:20], 1):  # Top 20
            rel_pct = (importance / total_contrib * 100) if total_contrib > 0 else 0
            col_name = self.col_names[col_idx]
            # Truncate long column names
            if len(col_name) > 30:
                col_name = col_name[:27] + "..."
            logger.info(f"   {rank:<6} {col_name:<30} {importance:<20.6f} {rel_pct:>5.1f}%")

    def get_per_column_lift_stats(self) -> Dict:
        """
        Aggregate lift statistics by column.

        For each column j, compute:
        - As target: mean lift when j is the target (i→j) - "how much do relationships help predict j?"
        - As source: mean lift when j is the source (j→i) - "how much does j help predict others?"
        - Best source: which column provides the best lift for predicting j
        - n_pairs: number of relationship pairs involving j

        Returns:
            Dict with:
                - 'as_target': {col_name: {'mean_lift': float, 'max_lift': float, 'n_pairs': int, 'best_source': str}}
                - 'as_source': {col_name: {'mean_lift': float, 'max_lift': float, 'n_pairs': int, 'best_target': str}}
                - 'summary': overall statistics
        """
        # Aggregate by target column (i→j: what helps predict j?)
        target_stats = {}  # col_j -> list of (lift, source_col)
        # Aggregate by source column (j→i: what does j help predict?)
        source_stats = {}  # col_j -> list of (lift, target_col)

        for directed_pair, stats in self._pair_stats.items():
            i, j = directed_pair
            lift_ema = stats.get('lift_ema')
            if lift_ema is None or not math.isfinite(lift_ema):
                continue

            col_i_name = self.col_names[i] if i < len(self.col_names) else f"col_{i}"
            col_j_name = self.col_names[j] if j < len(self.col_names) else f"col_{j}"

            # j is target, i is source
            if col_j_name not in target_stats:
                target_stats[col_j_name] = []
            target_stats[col_j_name].append((lift_ema, col_i_name))

            # i is source, j is target (same pair, different perspective)
            if col_i_name not in source_stats:
                source_stats[col_i_name] = []
            source_stats[col_i_name].append((lift_ema, col_j_name))

        # Compute aggregates for targets
        as_target = {}
        for col_name, lifts in target_stats.items():
            lift_values = [l for l, _ in lifts]
            if not lift_values:
                continue
            best_idx = max(range(len(lifts)), key=lambda i: lifts[i][0])
            as_target[col_name] = {
                'mean_lift': sum(lift_values) / len(lift_values),
                'max_lift': max(lift_values),
                'min_lift': min(lift_values),
                'n_pairs': len(lift_values),
                'best_source': lifts[best_idx][1],
                'best_source_lift': lifts[best_idx][0],
            }

        # Compute aggregates for sources
        as_source = {}
        for col_name, lifts in source_stats.items():
            lift_values = [l for l, _ in lifts]
            if not lift_values:
                continue
            best_idx = max(range(len(lifts)), key=lambda i: lifts[i][0])
            as_source[col_name] = {
                'mean_lift': sum(lift_values) / len(lift_values),
                'max_lift': max(lift_values),
                'min_lift': min(lift_values),
                'n_pairs': len(lift_values),
                'best_target': lifts[best_idx][1],
                'best_target_lift': lifts[best_idx][0],
            }

        # Overall summary
        all_lifts = [stats.get('lift_ema', 0) for stats in self._pair_stats.values()
                     if stats.get('lift_ema') is not None and math.isfinite(stats.get('lift_ema', 0))]
        summary = {
            'total_pairs': len(all_lifts),
            'mean_lift': sum(all_lifts) / len(all_lifts) if all_lifts else 0,
            'positive_lift_pct': sum(1 for l in all_lifts if l > 0) / len(all_lifts) * 100 if all_lifts else 0,
        }

        return {
            'as_target': as_target,
            'as_source': as_source,
            'summary': summary,
        }

    def log_per_column_lift(self, epoch: int = 0, top_k: int = 20):
        """
        Log per-column lift statistics.

        Shows which columns benefit most from relationships (as targets)
        and which columns are most useful as relationship sources.
        """
        stats = self.get_per_column_lift_stats()

        logger.info(f"")
        logger.info(f"📊 PER-COLUMN LIFT ANALYSIS [epoch={epoch}]:")
        logger.info(f"   Summary: {stats['summary']['total_pairs']} pairs, "
                   f"mean_lift={stats['summary']['mean_lift']:.6f}, "
                   f"{stats['summary']['positive_lift_pct']:.1f}% positive")

        # Columns that benefit most FROM relationships (as targets)
        logger.info(f"")
        logger.info(f"   🎯 COLUMNS THAT BENEFIT MOST FROM RELATIONSHIPS (as prediction targets):")
        logger.info(f"   {'Column':<30} {'Mean Lift':>12} {'Max Lift':>12} {'N Pairs':>8} {'Best Source':<25}")
        logger.info(f"   {'-'*30} {'-'*12} {'-'*12} {'-'*8} {'-'*25}")

        sorted_targets = sorted(stats['as_target'].items(), key=lambda x: x[1]['mean_lift'], reverse=True)
        for col_name, col_stats in sorted_targets[:top_k]:
            col_display = col_name[:30] if len(col_name) <= 30 else col_name[:27] + "..."
            best_src = col_stats['best_source']
            best_src_display = best_src[:25] if len(best_src) <= 25 else best_src[:22] + "..."
            logger.info(f"   {col_display:<30} {col_stats['mean_lift']:>12.6f} {col_stats['max_lift']:>12.6f} "
                       f"{col_stats['n_pairs']:>8} {best_src_display:<25}")

        # Columns that help others most (as sources)
        logger.info(f"")
        logger.info(f"   💡 COLUMNS THAT HELP PREDICT OTHERS MOST (as relationship sources):")
        logger.info(f"   {'Column':<30} {'Mean Lift':>12} {'Max Lift':>12} {'N Pairs':>8} {'Best Target':<25}")
        logger.info(f"   {'-'*30} {'-'*12} {'-'*12} {'-'*8} {'-'*25}")

        sorted_sources = sorted(stats['as_source'].items(), key=lambda x: x[1]['mean_lift'], reverse=True)
        for col_name, col_stats in sorted_sources[:top_k]:
            col_display = col_name[:30] if len(col_name) <= 30 else col_name[:27] + "..."
            best_tgt = col_stats['best_target']
            best_tgt_display = best_tgt[:25] if len(best_tgt) <= 25 else best_tgt[:22] + "..."
            logger.info(f"   {col_display:<30} {col_stats['mean_lift']:>12.6f} {col_stats['max_lift']:>12.6f} "
                       f"{col_stats['n_pairs']:>8} {best_tgt_display:<25}")

        # Columns with negative lift (relationships hurt prediction)
        negative_targets = [(name, s) for name, s in stats['as_target'].items() if s['mean_lift'] < 0]
        if negative_targets:
            logger.info(f"")
            logger.info(f"   ⚠️  COLUMNS WHERE RELATIONSHIPS HURT (negative mean lift):")
            sorted_neg = sorted(negative_targets, key=lambda x: x[1]['mean_lift'])
            for col_name, col_stats in sorted_neg[:10]:
                col_display = col_name[:30] if len(col_name) <= 30 else col_name[:27] + "..."
                logger.info(f"   {col_display:<30} mean_lift={col_stats['mean_lift']:>12.6f}")

    def get_lift_matrix(self) -> Tuple[np.ndarray, List[str]]:
        """
        Build NxN lift matrix from pair statistics.

        Returns:
            (matrix, col_names) where matrix[i,j] = L(i→j) (lift of i predicting j)
            NaN values indicate no data for that pair.
        """
        N = self.n_cols
        matrix = np.full((N, N), np.nan)

        for (i, j), stats in self._pair_stats.items():
            lift_ema = stats.get('lift_ema')
            if lift_ema is not None and math.isfinite(lift_ema):
                matrix[i, j] = lift_ema

        return matrix, list(self.col_names)

    def save_lift_heatmap(
        self,
        output_path: str,
        epoch: int = 0,
        figsize: Tuple[int, int] = None,
        max_cols_display: int = 50,
        show_values: bool = False,
        title: str = None,
    ) -> str:
        """
        Generate and save a lift heatmap visualization.

        The heatmap shows L(i→j) where:
        - Row i = source column (predictor)
        - Column j = target column (what's being predicted)
        - Color: green = positive lift (helps), red = negative lift (hurts), white = zero

        Args:
            output_path: Path to save the image (PNG/PDF)
            epoch: Current epoch (for title)
            figsize: Figure size as (width, height). Auto-calculated if None.
            max_cols_display: If more columns than this, show top N by activity
            show_values: Whether to annotate cells with numeric values
            title: Custom title (default: auto-generated)

        Returns:
            Path to saved file
        """
        try:
            import matplotlib
            matplotlib.use('Agg')  # Non-interactive backend
            import matplotlib.pyplot as plt
            from matplotlib.colors import TwoSlopeNorm
        except ImportError:
            logger.warning("matplotlib not available - cannot generate lift heatmap")
            return None

        matrix, col_names = self.get_lift_matrix()
        N = len(col_names)

        # If too many columns, select most active ones
        if N > max_cols_display:
            # Score each column by total activity (sum of non-NaN entries)
            col_activity = []
            for idx in range(N):
                # Count non-NaN in row (as source) and column (as target)
                row_activity = np.sum(~np.isnan(matrix[idx, :]))
                col_activity_val = np.sum(~np.isnan(matrix[:, idx]))
                col_activity.append((idx, row_activity + col_activity_val))

            # Sort by activity and take top max_cols_display
            col_activity.sort(key=lambda x: x[1], reverse=True)
            selected_indices = [idx for idx, _ in col_activity[:max_cols_display]]
            selected_indices.sort()  # Keep original order for readability

            # Subset matrix and names
            matrix = matrix[np.ix_(selected_indices, selected_indices)]
            col_names = [col_names[i] for i in selected_indices]
            N = len(col_names)
            logger.info(f"Lift heatmap: showing top {N} columns by activity (of {self.n_cols} total)")

        # Truncate long column names for display
        display_names = []
        for name in col_names:
            if len(name) > 20:
                display_names.append(name[:17] + "...")
            else:
                display_names.append(name)

        # Calculate figure size if not provided
        if figsize is None:
            # Scale with number of columns, but cap at reasonable size
            size = max(10, min(24, N * 0.4))
            figsize = (size, size)

        fig, ax = plt.subplots(figsize=figsize)

        # Create diverging colormap centered at 0
        # Find the range for normalization
        valid_values = matrix[~np.isnan(matrix)]
        if len(valid_values) == 0:
            logger.warning("No lift data available for heatmap")
            plt.close(fig)
            return None

        vmin = np.nanmin(matrix)
        vmax = np.nanmax(matrix)

        # Handle case where all values are same sign
        if vmin >= 0:
            vmin = -0.001  # Small negative to anchor colormap
        if vmax <= 0:
            vmax = 0.001  # Small positive to anchor colormap

        # Use TwoSlopeNorm to center colormap at 0
        norm = TwoSlopeNorm(vmin=vmin, vcenter=0, vmax=vmax)

        # Create heatmap with RdYlGn colormap (red=negative, yellow=zero, green=positive)
        im = ax.imshow(matrix, cmap='RdYlGn', norm=norm, aspect='equal')

        # Add colorbar
        cbar = plt.colorbar(im, ax=ax, shrink=0.8)
        cbar.set_label('Lift (loss reduction)', rotation=270, labelpad=20)

        # Set ticks and labels
        ax.set_xticks(np.arange(N))
        ax.set_yticks(np.arange(N))
        ax.set_xticklabels(display_names, rotation=45, ha='right', fontsize=max(6, 10 - N//10))
        ax.set_yticklabels(display_names, fontsize=max(6, 10 - N//10))

        # Labels
        ax.set_xlabel('Target Column (j) - being predicted', fontsize=12)
        ax.set_ylabel('Source Column (i) - predictor', fontsize=12)

        # Title
        if title is None:
            title = f'Lift Matrix L(i→j) [epoch {epoch}]\nGreen=helps, Red=hurts, White=neutral'
        ax.set_title(title, fontsize=14, pad=20)

        # Optionally annotate cells with values
        if show_values and N <= 20:
            for i in range(N):
                for j in range(N):
                    val = matrix[i, j]
                    if not np.isnan(val):
                        text_color = 'white' if abs(val) > (vmax - vmin) * 0.3 else 'black'
                        ax.text(j, i, f'{val:.2f}', ha='center', va='center',
                               color=text_color, fontsize=7)

        # Add summary statistics as text
        positive_count = np.sum(valid_values > 0)
        negative_count = np.sum(valid_values < 0)
        total_count = len(valid_values)
        mean_lift = np.mean(valid_values)
        stats_text = (f'Total pairs: {total_count} | '
                     f'Positive: {positive_count} ({100*positive_count/total_count:.1f}%) | '
                     f'Negative: {negative_count} ({100*negative_count/total_count:.1f}%) | '
                     f'Mean: {mean_lift:.4f}')
        fig.text(0.5, 0.02, stats_text, ha='center', fontsize=10, style='italic')

        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close(fig)

        logger.info(f"📊 Saved lift heatmap to {output_path}")
        return output_path

    def save_influence_scatter(
        self,
        output_path: str,
        epoch: int = 0,
        figsize: Tuple[int, int] = (12, 10),
        top_n_labels: int = 15,
        title: str = None,
    ) -> str:
        """
        Generate "Influence vs Predictability" scatter plot for columns.

        For each column:
        - X = mean outgoing lift (how much this column helps predict others)
        - Y = mean incoming lift (how predictable this column is from others)

        Quadrants reveal column roles:
        - Top-right: Hub columns (help others AND are predictable)
        - Top-left: "Dependent" columns (predictable but don't help others)
        - Bottom-right: "Informative" columns (help others but hard to predict)
        - Bottom-left: Isolated/problematic columns

        Args:
            output_path: Path to save the image (PNG/PDF)
            epoch: Current epoch (for title)
            figsize: Figure size
            top_n_labels: Number of extreme points to label
            title: Custom title

        Returns:
            Path to saved file
        """
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
        except ImportError:
            logger.warning("matplotlib not available - cannot generate scatter plot")
            return None

        matrix, col_names = self.get_lift_matrix()
        N = len(col_names)

        # Compute per-column statistics
        col_stats = []
        for idx in range(N):
            # Outgoing lift: mean of row idx (this column as source)
            outgoing = matrix[idx, :]
            outgoing_valid = outgoing[~np.isnan(outgoing)]
            mean_outgoing = np.mean(outgoing_valid) if len(outgoing_valid) > 0 else 0.0
            n_outgoing = len(outgoing_valid)

            # Incoming lift: mean of column idx (this column as target)
            incoming = matrix[:, idx]
            incoming_valid = incoming[~np.isnan(incoming)]
            mean_incoming = np.mean(incoming_valid) if len(incoming_valid) > 0 else 0.0
            n_incoming = len(incoming_valid)

            col_stats.append({
                'name': col_names[idx],
                'idx': idx,
                'mean_outgoing': mean_outgoing,
                'mean_incoming': mean_incoming,
                'n_outgoing': n_outgoing,
                'n_incoming': n_incoming,
                'total_pairs': n_outgoing + n_incoming,
            })

        # Filter columns with at least some data
        col_stats = [c for c in col_stats if c['total_pairs'] > 0]
        if not col_stats:
            logger.warning("No lift data available for scatter plot")
            return None

        # Extract coordinates
        x = np.array([c['mean_outgoing'] for c in col_stats])
        y = np.array([c['mean_incoming'] for c in col_stats])
        sizes = np.array([c['total_pairs'] for c in col_stats])
        names = [c['name'] for c in col_stats]

        # Normalize sizes for plotting
        size_min, size_max = 30, 300
        if sizes.max() > sizes.min():
            sizes_norm = size_min + (sizes - sizes.min()) / (sizes.max() - sizes.min()) * (size_max - size_min)
        else:
            sizes_norm = np.full_like(sizes, (size_min + size_max) / 2, dtype=float)

        fig, ax = plt.subplots(figsize=figsize)

        # Color by quadrant
        colors = []
        for xi, yi in zip(x, y):
            if xi >= 0 and yi >= 0:
                colors.append('#2ecc71')  # Green - hub (top-right)
            elif xi < 0 and yi >= 0:
                colors.append('#3498db')  # Blue - dependent (top-left)
            elif xi >= 0 and yi < 0:
                colors.append('#f39c12')  # Orange - informative (bottom-right)
            else:
                colors.append('#e74c3c')  # Red - problematic (bottom-left)

        # Scatter plot
        scatter = ax.scatter(x, y, s=sizes_norm, c=colors, alpha=0.6, edgecolors='black', linewidth=0.5)

        # Add quadrant lines and labels
        ax.axhline(y=0, color='gray', linestyle='--', linewidth=1, alpha=0.5)
        ax.axvline(x=0, color='gray', linestyle='--', linewidth=1, alpha=0.5)

        # Quadrant labels
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        offset_x = (xlim[1] - xlim[0]) * 0.02
        offset_y = (ylim[1] - ylim[0]) * 0.02

        ax.text(xlim[1] - offset_x, ylim[1] - offset_y, 'HUB\n(helps & predictable)',
               ha='right', va='top', fontsize=9, color='#2ecc71', weight='bold', alpha=0.8)
        ax.text(xlim[0] + offset_x, ylim[1] - offset_y, 'DEPENDENT\n(predictable only)',
               ha='left', va='top', fontsize=9, color='#3498db', weight='bold', alpha=0.8)
        ax.text(xlim[1] - offset_x, ylim[0] + offset_y, 'INFORMATIVE\n(helps others)',
               ha='right', va='bottom', fontsize=9, color='#f39c12', weight='bold', alpha=0.8)
        ax.text(xlim[0] + offset_x, ylim[0] + offset_y, 'ISOLATED\n(neither)',
               ha='left', va='bottom', fontsize=9, color='#e74c3c', weight='bold', alpha=0.8)

        # Label top N extreme points
        # Find points furthest from origin or at extremes
        distances = np.sqrt(x**2 + y**2)
        extremes = []
        # Add furthest points
        extreme_indices = np.argsort(distances)[-top_n_labels//2:]
        extremes.extend(extreme_indices)
        # Add most negative incoming (hardest to predict)
        extremes.extend(np.argsort(y)[:top_n_labels//4])
        # Add most positive outgoing (most helpful)
        extremes.extend(np.argsort(x)[-top_n_labels//4:])
        extremes = list(set(extremes))[:top_n_labels]

        for idx in extremes:
            name = names[idx]
            if len(name) > 20:
                name = name[:17] + "..."
            ax.annotate(name, (x[idx], y[idx]),
                       xytext=(5, 5), textcoords='offset points',
                       fontsize=8, alpha=0.8,
                       arrowprops=dict(arrowstyle='-', color='gray', alpha=0.3))

        # Labels and title
        ax.set_xlabel('Mean Outgoing Lift (how much this column helps others)', fontsize=11)
        ax.set_ylabel('Mean Incoming Lift (how predictable from others)', fontsize=11)
        if title is None:
            title = f'Column Influence vs Predictability [epoch {epoch}]'
        ax.set_title(title, fontsize=13, pad=15)

        # Add summary legend
        legend_text = (f'N={len(col_stats)} columns | '
                      f'Hub: {sum(1 for c in colors if c == "#2ecc71")} | '
                      f'Dependent: {sum(1 for c in colors if c == "#3498db")} | '
                      f'Informative: {sum(1 for c in colors if c == "#f39c12")} | '
                      f'Isolated: {sum(1 for c in colors if c == "#e74c3c")}')
        fig.text(0.5, 0.02, legend_text, ha='center', fontsize=10, style='italic')

        # Size legend
        ax.text(0.98, 0.02, 'Point size = # of pairs',
               transform=ax.transAxes, ha='right', va='bottom', fontsize=8, alpha=0.6)

        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close(fig)

        logger.info(f"📊 Saved influence scatter plot to {output_path}")
        return output_path

    def compute_transitive_lift(
        self,
        source_col: int,
        target_col: int,
        max_hops: int = 3,
    ) -> Dict:
        """
        Compute direct vs transitive (multi-hop) lift between two columns.

        Analyzes how well information "flows" from source to target through
        intermediate columns, compared to the direct relationship.

        Args:
            source_col: Index of source column
            target_col: Index of target column
            max_hops: Maximum path length to consider

        Returns:
            Dict with direct lift, best paths, and analysis
        """
        matrix, col_names = self.get_lift_matrix()
        N = len(col_names)

        if source_col >= N or target_col >= N:
            return {'error': 'Invalid column indices'}

        # Direct lift
        direct_lift = matrix[source_col, target_col]
        if np.isnan(direct_lift):
            direct_lift = None

        # Find paths of length 2 (A → B → C)
        paths_2hop = []
        for mid in range(N):
            if mid == source_col or mid == target_col:
                continue
            lift_ab = matrix[source_col, mid]
            lift_bc = matrix[mid, target_col]
            if not np.isnan(lift_ab) and not np.isnan(lift_bc):
                # Multiplicative model: treat lift as "fraction of baseline preserved"
                # If baseline is B0, and lift_ab means loss goes from B0 to B0-lift_ab,
                # then "retention" = (B0 - lift_ab) / B0 = 1 - lift_ab/B0
                # This is tricky because lift is absolute, not relative...
                #
                # Simpler: just use min (bottleneck) or product of normalized lifts
                # For now, use geometric mean as a heuristic for "path strength"
                if lift_ab > 0 and lift_bc > 0:
                    path_strength = math.sqrt(lift_ab * lift_bc)
                else:
                    # If either is negative, path is weak/harmful
                    path_strength = min(lift_ab, lift_bc)

                paths_2hop.append({
                    'path': [source_col, mid, target_col],
                    'path_names': [col_names[source_col], col_names[mid], col_names[target_col]],
                    'lifts': [lift_ab, lift_bc],
                    'path_strength': path_strength,
                    'bottleneck': min(lift_ab, lift_bc),
                })

        # Sort by path strength
        paths_2hop.sort(key=lambda p: p['path_strength'], reverse=True)

        # Find paths of length 3 (A → B → C → D) if requested
        paths_3hop = []
        if max_hops >= 3:
            for mid1 in range(N):
                if mid1 == source_col or mid1 == target_col:
                    continue
                lift_ab = matrix[source_col, mid1]
                if np.isnan(lift_ab):
                    continue

                for mid2 in range(N):
                    if mid2 == source_col or mid2 == target_col or mid2 == mid1:
                        continue
                    lift_bc = matrix[mid1, mid2]
                    lift_cd = matrix[mid2, target_col]
                    if np.isnan(lift_bc) or np.isnan(lift_cd):
                        continue

                    lifts = [lift_ab, lift_bc, lift_cd]
                    if all(l > 0 for l in lifts):
                        path_strength = (lift_ab * lift_bc * lift_cd) ** (1/3)  # Geometric mean
                    else:
                        path_strength = min(lifts)

                    paths_3hop.append({
                        'path': [source_col, mid1, mid2, target_col],
                        'path_names': [col_names[source_col], col_names[mid1],
                                      col_names[mid2], col_names[target_col]],
                        'lifts': lifts,
                        'path_strength': path_strength,
                        'bottleneck': min(lifts),
                    })

            paths_3hop.sort(key=lambda p: p['path_strength'], reverse=True)

        # Analysis
        best_2hop = paths_2hop[0] if paths_2hop else None
        best_3hop = paths_3hop[0] if paths_3hop else None

        return {
            'source': col_names[source_col],
            'target': col_names[target_col],
            'direct_lift': direct_lift,
            'best_2hop_path': best_2hop,
            'best_3hop_path': best_3hop,
            'all_2hop_paths': paths_2hop[:10],  # Top 10
            'all_3hop_paths': paths_3hop[:10],  # Top 10
            'analysis': {
                'has_direct': direct_lift is not None,
                'n_2hop_paths': len(paths_2hop),
                'n_3hop_paths': len(paths_3hop),
            }
        }

    def save_information_flow_diagram(
        self,
        output_path: str,
        source_cols: List[int] = None,
        target_cols: List[int] = None,
        epoch: int = 0,
        figsize: Tuple[int, int] = (14, 10),
        top_n_paths: int = 20,
        title: str = None,
    ) -> str:
        """
        Visualize information flow paths showing transitive predictability decay.

        Shows how prediction accuracy compounds/decays through chains of columns.
        Converts lift to a pseudo-accuracy metric for intuitive visualization.

        Args:
            output_path: Path to save the image
            source_cols: Source column indices to analyze (None = auto-select most informative)
            target_cols: Target column indices (None = auto-select hardest to predict)
            epoch: Current epoch
            figsize: Figure size
            top_n_paths: Number of top paths to show
            title: Custom title

        Returns:
            Path to saved file
        """
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            import matplotlib.patches as mpatches
        except ImportError:
            logger.warning("matplotlib not available - cannot generate flow diagram")
            return None

        matrix, col_names = self.get_lift_matrix()
        N = len(col_names)

        # Convert lift to pseudo-accuracy for intuitive display
        # Use sigmoid-like transformation: accuracy = 0.5 + 0.5 * tanh(lift * scale)
        # This maps: lift=0 -> 50%, large positive -> ~100%, large negative -> ~0%
        def lift_to_accuracy(lift, scale=5.0):
            if lift is None or np.isnan(lift):
                return None
            return 0.5 + 0.5 * np.tanh(lift * scale)

        # Auto-select source columns (most informative = highest mean outgoing lift)
        if source_cols is None:
            outgoing_means = []
            for i in range(N):
                row = matrix[i, :]
                valid = row[~np.isnan(row)]
                if len(valid) > 0:
                    outgoing_means.append((i, np.mean(valid)))
            outgoing_means.sort(key=lambda x: x[1], reverse=True)
            source_cols = [idx for idx, _ in outgoing_means[:3]]

        # Auto-select target columns (hardest to predict = lowest mean incoming lift)
        if target_cols is None:
            incoming_means = []
            for j in range(N):
                col = matrix[:, j]
                valid = col[~np.isnan(col)]
                if len(valid) > 0:
                    incoming_means.append((j, np.mean(valid)))
            incoming_means.sort(key=lambda x: x[1])
            target_cols = [idx for idx, _ in incoming_means[:3]]

        # Collect all interesting paths
        all_paths = []
        for src in source_cols:
            for tgt in target_cols:
                if src == tgt:
                    continue
                result = self.compute_transitive_lift(src, tgt, max_hops=2)

                # Add direct path
                if result['direct_lift'] is not None:
                    acc = lift_to_accuracy(result['direct_lift'])
                    all_paths.append({
                        'type': 'direct',
                        'path_names': [result['source'], result['target']],
                        'accuracies': [acc],
                        'compound_accuracy': acc,
                        'lifts': [result['direct_lift']],
                    })

                # Add best 2-hop path
                if result['best_2hop_path']:
                    p = result['best_2hop_path']
                    accs = [lift_to_accuracy(l) for l in p['lifts']]
                    compound = accs[0] * accs[1] if all(a is not None for a in accs) else None
                    all_paths.append({
                        'type': '2-hop',
                        'path_names': p['path_names'],
                        'accuracies': accs,
                        'compound_accuracy': compound,
                        'lifts': p['lifts'],
                    })

        # Sort by compound accuracy
        all_paths = [p for p in all_paths if p['compound_accuracy'] is not None]
        all_paths.sort(key=lambda p: p['compound_accuracy'], reverse=True)
        all_paths = all_paths[:top_n_paths]

        if not all_paths:
            logger.warning("No valid paths found for flow diagram")
            return None

        # Create visualization
        fig, ax = plt.subplots(figsize=figsize)

        y_positions = list(range(len(all_paths)))
        y_positions.reverse()  # Best at top

        bar_height = 0.6
        colors_direct = '#3498db'
        colors_2hop = '#e74c3c'

        for y, path in zip(y_positions, all_paths):
            color = colors_direct if path['type'] == 'direct' else colors_2hop

            # Draw compound accuracy bar
            compound = path['compound_accuracy']
            ax.barh(y, compound, height=bar_height, color=color, alpha=0.7, edgecolor='black')

            # Build path label with accuracies
            names = path['path_names']
            accs = path['accuracies']

            # Truncate names
            def trunc(s, n=12):
                return s[:n-2] + '..' if len(s) > n else s

            if path['type'] == 'direct':
                label = f"{trunc(names[0])} →({accs[0]*100:.0f}%)→ {trunc(names[1])}"
            else:
                label = f"{trunc(names[0])} →({accs[0]*100:.0f}%)→ {trunc(names[1])} →({accs[1]*100:.0f}%)→ {trunc(names[2])}"

            # Add label
            ax.text(0.01, y, label, va='center', ha='left', fontsize=9,
                   fontfamily='monospace', color='white' if compound > 0.3 else 'black')

            # Add compound accuracy text on right
            ax.text(compound + 0.01, y, f'{compound*100:.1f}%', va='center', ha='left', fontsize=9)

        ax.set_xlim(0, 1.15)
        ax.set_ylim(-0.5, len(all_paths) - 0.5)
        ax.set_xlabel('Compound Pseudo-Accuracy (multiplicative through chain)', fontsize=11)
        ax.set_ylabel('Information Flow Paths', fontsize=11)
        ax.set_yticks([])

        # Legend
        direct_patch = mpatches.Patch(color=colors_direct, alpha=0.7, label='Direct (A→C)')
        hop2_patch = mpatches.Patch(color=colors_2hop, alpha=0.7, label='2-hop (A→B→C)')
        ax.legend(handles=[direct_patch, hop2_patch], loc='lower right')

        # Title
        if title is None:
            title = f'Information Flow: Transitive Predictability [epoch {epoch}]\n' \
                   f'Shows how prediction "accuracy" compounds through column chains'
        ax.set_title(title, fontsize=12, pad=15)

        # Add note about pseudo-accuracy
        fig.text(0.5, 0.02,
                'Note: "Accuracy" is pseudo-metric derived from lift via sigmoid transform. '
                'Compound = product of step accuracies.',
                ha='center', fontsize=9, style='italic', alpha=0.7)

        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close(fig)

        logger.info(f"📊 Saved information flow diagram to {output_path}")
        return output_path

    def save_lift_surface(
        self,
        output_path: str,
        epoch: int = 0,
        figsize: Tuple[int, int] = (14, 10),
        max_cols: int = 40,
        view_angle: Tuple[int, int] = (25, 45),
        title: str = None,
    ) -> str:
        """
        Generate 3D surface visualization of the lift matrix.

        Creates a terrain-like view where:
        - X axis = source column index
        - Y axis = target column index
        - Z axis (height) = lift value
        - Color = lift value (green peaks = strong positive, red valleys = negative)

        This reveals the "topology" of column relationships - which pairs form
        peaks of mutual information vs valleys of interference.

        Args:
            output_path: Path to save the image
            epoch: Current epoch
            figsize: Figure size
            max_cols: Maximum columns to display (subsamples if more)
            view_angle: (elevation, azimuth) for 3D view
            title: Custom title

        Returns:
            Path to saved file
        """
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            from mpl_toolkits.mplot3d import Axes3D
            from matplotlib.colors import TwoSlopeNorm
        except ImportError:
            logger.warning("matplotlib not available - cannot generate surface plot")
            return None

        matrix, col_names = self.get_lift_matrix()
        N = len(col_names)

        # Subsample if too many columns
        if N > max_cols:
            # Select most active columns
            col_activity = []
            for idx in range(N):
                row_valid = np.sum(~np.isnan(matrix[idx, :]))
                col_valid = np.sum(~np.isnan(matrix[:, idx]))
                col_activity.append((idx, row_valid + col_valid))
            col_activity.sort(key=lambda x: x[1], reverse=True)
            selected = sorted([idx for idx, _ in col_activity[:max_cols]])

            matrix = matrix[np.ix_(selected, selected)]
            col_names = [col_names[i] for i in selected]
            N = len(col_names)
            logger.info(f"Lift surface: subsampled to {N} most active columns")

        # Replace NaN with 0 for surface plotting (or interpolate)
        matrix_filled = np.nan_to_num(matrix, nan=0.0)

        # Create meshgrid for surface
        X, Y = np.meshgrid(np.arange(N), np.arange(N))

        fig = plt.figure(figsize=figsize)
        ax = fig.add_subplot(111, projection='3d')

        # Color normalization centered at 0
        vmin = np.nanmin(matrix)
        vmax = np.nanmax(matrix)
        if vmin >= 0:
            vmin = -0.01
        if vmax <= 0:
            vmax = 0.01
        norm = TwoSlopeNorm(vmin=vmin, vcenter=0, vmax=vmax)

        # Plot surface
        surf = ax.plot_surface(
            X, Y, matrix_filled,
            cmap='RdYlGn',
            norm=norm,
            alpha=0.8,
            edgecolor='none',
            antialiased=True,
        )

        # Add wireframe for structure visibility
        ax.plot_wireframe(
            X, Y, matrix_filled,
            color='black',
            alpha=0.1,
            linewidth=0.3,
            rstride=max(1, N//20),
            cstride=max(1, N//20),
        )

        # Colorbar
        cbar = fig.colorbar(surf, ax=ax, shrink=0.5, aspect=10, pad=0.1)
        cbar.set_label('Lift (loss reduction)', rotation=270, labelpad=15)

        # Labels
        ax.set_xlabel('Source Column (i)', fontsize=10, labelpad=10)
        ax.set_ylabel('Target Column (j)', fontsize=10, labelpad=10)
        ax.set_zlabel('Lift L(i→j)', fontsize=10, labelpad=10)

        # Set view angle
        ax.view_init(elev=view_angle[0], azim=view_angle[1])

        # Title
        if title is None:
            title = f'Lift Surface L(i→j) [epoch {epoch}]\n' \
                   f'Green peaks = strong positive lift, Red valleys = negative lift'
        ax.set_title(title, fontsize=12, pad=20)

        # Add tick labels for smaller matrices
        if N <= 20:
            truncated_names = [n[:8] + '..' if len(n) > 10 else n for n in col_names]
            ax.set_xticks(np.arange(N))
            ax.set_xticklabels(truncated_names, rotation=45, ha='right', fontsize=7)
            ax.set_yticks(np.arange(N))
            ax.set_yticklabels(truncated_names, rotation=-45, ha='left', fontsize=7)

        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close(fig)

        logger.info(f"📊 Saved lift surface plot to {output_path}")
        return output_path

    def save_column_embedding_landscape(
        self,
        output_path: str,
        epoch: int = 0,
        figsize: Tuple[int, int] = (12, 10),
        method: str = 'tsne',
        title: str = None,
    ) -> str:
        """
        Generate 2D embedding of columns with predictability as height/color.

        Uses dimensionality reduction on the lift matrix to position columns
        in 2D space, then overlays predictability information.

        Columns that have similar lift profiles (help/hurt similar targets)
        will cluster together.

        Args:
            output_path: Path to save the image
            epoch: Current epoch
            figsize: Figure size
            method: Dimensionality reduction method ('tsne', 'mds', 'pca')
            title: Custom title

        Returns:
            Path to saved file
        """
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            from sklearn.manifold import TSNE, MDS
            from sklearn.decomposition import PCA
            from sklearn.preprocessing import StandardScaler
        except ImportError as e:
            logger.warning(f"Required library not available: {e}")
            return None

        matrix, col_names = self.get_lift_matrix()
        N = len(col_names)

        # Create feature matrix: each column's lift profile (as source and target)
        # Fill NaN with 0 for dimensionality reduction
        matrix_filled = np.nan_to_num(matrix, nan=0.0)

        # Feature for each column: concatenate its row (as source) and column (as target)
        features = np.hstack([matrix_filled, matrix_filled.T])

        # Standardize
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(features)

        # Dimensionality reduction
        if method == 'tsne':
            perplexity = min(30, N - 1) if N > 30 else max(5, N // 2)
            reducer = TSNE(n_components=2, perplexity=perplexity, random_state=42)
        elif method == 'mds':
            reducer = MDS(n_components=2, random_state=42)
        else:  # pca
            reducer = PCA(n_components=2)

        try:
            embedding = reducer.fit_transform(features_scaled)
        except Exception as e:
            logger.warning(f"Dimensionality reduction failed: {e}")
            return None

        # Compute column "importance" scores for coloring
        # Use mean outgoing lift (how much this column helps others)
        mean_outgoing = np.nanmean(matrix, axis=1)
        mean_outgoing = np.nan_to_num(mean_outgoing, nan=0.0)

        # Compute column "predictability" for sizing
        # Use mean incoming lift (how predictable this column is)
        mean_incoming = np.nanmean(matrix, axis=0)
        mean_incoming = np.nan_to_num(mean_incoming, nan=0.0)

        # Normalize for visualization
        size_min, size_max = 50, 400
        if mean_incoming.max() > mean_incoming.min():
            sizes = size_min + (mean_incoming - mean_incoming.min()) / \
                   (mean_incoming.max() - mean_incoming.min()) * (size_max - size_min)
        else:
            sizes = np.full(N, (size_min + size_max) / 2)

        fig, ax = plt.subplots(figsize=figsize)

        # Scatter plot with color = outgoing influence, size = predictability
        scatter = ax.scatter(
            embedding[:, 0], embedding[:, 1],
            c=mean_outgoing,
            s=sizes,
            cmap='RdYlGn',
            alpha=0.7,
            edgecolors='black',
            linewidth=0.5,
        )

        # Colorbar
        cbar = plt.colorbar(scatter, ax=ax)
        cbar.set_label('Mean Outgoing Lift (influence on others)', rotation=270, labelpad=20)

        # Label points
        for idx, (x, y) in enumerate(embedding):
            name = col_names[idx]
            if len(name) > 15:
                name = name[:12] + '...'
            ax.annotate(name, (x, y), xytext=(3, 3), textcoords='offset points',
                       fontsize=7, alpha=0.8)

        ax.set_xlabel(f'{method.upper()} Dimension 1', fontsize=11)
        ax.set_ylabel(f'{method.upper()} Dimension 2', fontsize=11)

        if title is None:
            title = f'Column Embedding Landscape [epoch {epoch}]\n' \
                   f'Position: lift profile similarity | Color: influence | Size: predictability'
        ax.set_title(title, fontsize=12, pad=15)

        # Legend for size
        ax.text(0.02, 0.02, 'Larger = more predictable',
               transform=ax.transAxes, fontsize=9, alpha=0.6)

        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close(fig)

        logger.info(f"📊 Saved column embedding landscape to {output_path}")
        return output_path

    def save_all_lift_visualizations(
        self,
        output_dir: str,
        epoch: int = 0,
        prefix: str = "lift",
    ) -> Dict[str, str]:
        """
        Generate all lift visualizations for this epoch.

        Creates a comprehensive set of visualizations showing column relationships
        from multiple perspectives. Each visualization is wrapped in try/except
        to ensure one failure doesn't crash training.

        Args:
            output_dir: Directory to save visualizations
            epoch: Current epoch number (used in filenames and titles)
            prefix: Filename prefix (default: "lift")

        Returns:
            Dict mapping visualization name to saved file path (or None if failed)
        """
        import os

        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)

        results = {}

        # 1. Lift Heatmap (2D matrix view)
        try:
            path = os.path.join(output_dir, f"{prefix}_heatmap_epoch{epoch:04d}.png")
            results['heatmap'] = self.save_lift_heatmap(
                output_path=path,
                epoch=epoch,
            )
        except Exception as e:
            logger.warning(f"Failed to generate lift heatmap: {e}")
            results['heatmap'] = None

        # 2. Influence vs Predictability Scatter
        try:
            path = os.path.join(output_dir, f"{prefix}_scatter_epoch{epoch:04d}.png")
            results['scatter'] = self.save_influence_scatter(
                output_path=path,
                epoch=epoch,
            )
        except Exception as e:
            logger.warning(f"Failed to generate influence scatter: {e}")
            results['scatter'] = None

        # 3. Information Flow Diagram (transitive paths)
        try:
            path = os.path.join(output_dir, f"{prefix}_flow_epoch{epoch:04d}.png")
            results['flow'] = self.save_information_flow_diagram(
                output_path=path,
                epoch=epoch,
            )
        except Exception as e:
            logger.warning(f"Failed to generate information flow diagram: {e}")
            results['flow'] = None

        # 4. 3D Lift Surface
        try:
            path = os.path.join(output_dir, f"{prefix}_surface_epoch{epoch:04d}.png")
            results['surface'] = self.save_lift_surface(
                output_path=path,
                epoch=epoch,
            )
        except Exception as e:
            logger.warning(f"Failed to generate lift surface: {e}")
            results['surface'] = None

        # 5. Column Embedding Landscape (t-SNE)
        try:
            path = os.path.join(output_dir, f"{prefix}_embedding_epoch{epoch:04d}.png")
            results['embedding'] = self.save_column_embedding_landscape(
                output_path=path,
                epoch=epoch,
                method='tsne',
            )
        except Exception as e:
            logger.warning(f"Failed to generate column embedding landscape: {e}")
            results['embedding'] = None

        # Summary
        succeeded = sum(1 for v in results.values() if v is not None)
        total = len(results)
        logger.info(f"📊 Lift visualizations: {succeeded}/{total} generated for epoch {epoch}")

        return results

    def set_viz_output_dir(self, output_dir: str):
        """
        Set or update the visualization output directory.

        Call this to enable/change visualizations after construction.
        Visualizations will be generated at the end of each epoch.

        Args:
            output_dir: Directory path, or None to disable visualizations
        """
        self.viz_output_dir = output_dir
        if output_dir:
            import os
            os.makedirs(output_dir, exist_ok=True)
            logger.info(f"📊 Lift visualizations enabled: {output_dir}")

    def log_pruning_analysis(self):
        """Detailed analysis of pruning decisions."""
        if self.pruned_pairs_per_column is None:
            return
        
        # Analyze kept vs dropped pairs
        kept_pairs = set(self._pruned_pairs_list)
        dropped_pairs = set(self.all_pairs) - kept_pairs
        
        kept_contribs = [self.pair_contributions[p] for p in kept_pairs]
        dropped_contribs = [self.pair_contributions[p] for p in dropped_pairs]
        
        logger.info("")
        logger.info("📊 PRUNING DECISION ANALYSIS:")
        logger.info(f"   Kept pairs ({len(kept_pairs)}):")
        if kept_contribs:
            logger.info(f"      Mean contribution: {np.mean(kept_contribs):.6f}")
            logger.info(f"      Min contribution:  {np.min(kept_contribs):.6f}")
            logger.info(f"      Max contribution:  {np.max(kept_contribs):.6f}")
        else:
            logger.info(f"      (no kept pairs)")
        
        if dropped_contribs:
            logger.info(f"   Dropped pairs ({len(dropped_pairs)}):")
            logger.info(f"      Mean contribution: {np.mean(dropped_contribs):.6f}")
            logger.info(f"      Min contribution:  {np.min(dropped_contribs):.6f}")
            logger.info(f"      Max contribution:  {np.max(dropped_contribs):.6f}")
        
        # Calculate effectiveness of pruning
        kept_contrib_sum = sum(kept_contribs)
        total_contrib_sum = sum(self.pair_contributions.values())
        retained_signal = (kept_contrib_sum / total_contrib_sum * 100) if total_contrib_sum > 0 else 0
        
        logger.info(f"   📈 Signal retention: {retained_signal:.1f}% of total contribution")
        logger.info(f"   ⚡ Efficiency gain: {len(dropped_pairs) / len(self.all_pairs) * 100:.1f}% fewer pairs")
    
    def log_relationship_stability(self):
        """Analyze how stable relationships are over epochs."""
        if len(self.contribution_history) < 2:
            logger.info("   ⚠️  Need at least 2 epochs to analyze stability")
            return
        
        # Calculate correlation between consecutive epochs
        correlations = []
        for i in range(1, len(self.contribution_history)):
            prev = self.contribution_history[i-1]
            curr = self.contribution_history[i]
            
            # Pearson correlation
            prev_vals = [prev[p] for p in self.all_pairs]
            curr_vals = [curr[p] for p in self.all_pairs]
            
            # Handle edge cases: empty arrays or zero variance
            if len(prev_vals) == 0 or len(curr_vals) == 0:
                corr = 0.0
            elif len(prev_vals) == 1 or len(curr_vals) == 1:
                corr = 0.0  # Can't compute correlation with single value
            elif np.std(prev_vals) == 0 or np.std(curr_vals) == 0:
                corr = 0.0
            else:
                corr = np.corrcoef(prev_vals, curr_vals)[0, 1]
                if np.isnan(corr):
                    corr = 0.0
            correlations.append(corr)
        
        logger.info("")
        logger.info("📊 RELATIONSHIP STABILITY:")
        if correlations:
            logger.info(f"   Mean epoch-to-epoch correlation: {np.mean(correlations):.3f}")
        else:
            logger.info(f"   Mean epoch-to-epoch correlation: N/A (need at least 2 epochs)")
        logger.info(f"   Stability trend:")
        for epoch, corr in enumerate(correlations, 2):
            logger.info(f"      Epoch {epoch-1} → {epoch}: {corr:.3f}")
    
    def prune_to_top_relationships(self):
        """
        Prune to top k% relationships per column after exploration phase.
        
        Each column keeps only its top k% partners (by contribution).
        This is done PER COLUMN, so different columns can focus on different partners.
        """
        # Log pre-pruning analysis
        self.log_relationship_stability()
        self.log_operation_statistics()
        self.log_column_importance()
        
        logger.info("")
        logger.info("=" * 80)
        logger.info(f"🔪 PRUNING RELATIONSHIPS (epoch {self.current_epoch})")
        logger.info("=" * 80)
        
        # Calculate top_k per column
        top_k = max(1, int(self.n_cols * self.top_k_fraction))
        logger.info(f"   Each column will keep top {top_k} partners ({self.top_k_fraction*100:.0f}%)")
        
        # Build dict: col_idx -> list of (partner_idx, contribution) tuples
        col_to_partners = {i: [] for i in range(self.n_cols)}
        
        for (i, j), contribution in self.pair_contributions.items():
            # Add j as partner of i
            col_to_partners[i].append((j, contribution))
            # Add i as partner of j (symmetric)
            col_to_partners[j].append((i, contribution))
        
        # Sort and select top_k for each column
        self.pruned_pairs_per_column = {}
        pruned_pairs_set = set()
        
        logger.info("")
        logger.info("   Top partners per column (keeping smallest gradients = most important):")
        for col_idx in range(self.n_cols):
            partners = col_to_partners[col_idx]
            
            # Sort by contribution (SMALLEST first = most important = already optimized)
            partners_sorted = sorted(partners, key=lambda x: x[1], reverse=False)
            
            # Select top_k
            top_partners = [partner_idx for partner_idx, _ in partners_sorted[:top_k]]
            self.pruned_pairs_per_column[col_idx] = top_partners
            
            # Add to pruned set (ensure i < j for uniqueness)
            for partner_idx in top_partners:
                pair = tuple(sorted([col_idx, partner_idx]))
                pruned_pairs_set.add(pair)
            
            # Log top 3 partners for this column
            col_name = self.col_names[col_idx]
            # Truncate long column names
            if len(col_name) > 25:
                col_name = col_name[:22] + "..."
            
            top_3_info = ", ".join([
                f"{self.col_names[p_idx][:20]}({contrib:.4f})"
                for p_idx, contrib in partners_sorted[:3]
            ])
            logger.info(f"   {col_name:<25}: {top_3_info}")
        
        # Convert to list for forward pass
        self._pruned_pairs_list = list(pruned_pairs_set)
        
        total_pairs_before = len(self.all_pairs)
        total_pairs_after = len(pruned_pairs_set)
        reduction = (1 - total_pairs_after / total_pairs_before) * 100
        
        logger.info("")
        logger.info(f"📊 PRUNING SUMMARY:")
        logger.info(f"   Pairs before: {total_pairs_before}")
        logger.info(f"   Pairs after:  {total_pairs_after}")
        logger.info(f"   Reduction:    {reduction:.1f}%")
        logger.info(f"   Tokens before: {total_pairs_before * 6}")
        logger.info(f"   Tokens after:  {total_pairs_after * 6}")

        # Log the KEPT pairs explicitly (what survived pruning)
        logger.info("")
        logger.info(f"✅ AUTO-CRAFTED FEATURES RETAINED ({total_pairs_after} pairs):")
        for idx, (i, j) in enumerate(sorted(self._pruned_pairs_list)):
            col_a = self.col_names[i] if i < len(self.col_names) else f"col_{i}"
            col_b = self.col_names[j] if j < len(self.col_names) else f"col_{j}"
            contrib = self.pair_contributions.get((i, j), 0.0)
            # Truncate long names
            if len(col_a) > 20:
                col_a = col_a[:17] + "..."
            if len(col_b) > 20:
                col_b = col_b[:17] + "..."
            logger.info(f"   [{idx+1:2}] {col_a} × {col_b}  (contribution={contrib:.6f})")
        logger.info("=" * 80)
        logger.info("")

        # Log post-pruning analysis
        self.log_pruning_analysis()
    
    def update_mi_estimates(
        self,
        col_mi_estimates: Dict[str, Optional[float]],
        joint_mi_estimate: Optional[float] = None,
    ):
        """
        Update mutual information estimates from encoder.
        
        Note: DynamicRelationshipExtractor uses contribution-based pruning rather than
        MI-based pair selection, so this method primarily stores the estimates for
        potential future use (e.g., logging, analysis, or hybrid pruning strategies).
        """
        # Store MI estimates for potential future use
        self.col_mi_estimates = col_mi_estimates.copy() if col_mi_estimates else {}
        self.joint_mi_estimate = joint_mi_estimate
        
        # Log MI estimates if available (useful for debugging)
        if logger.isEnabledFor(logging.DEBUG) and col_mi_estimates:
            mi_values = [f"{k}={v:.4f}" for k, v in col_mi_estimates.items() if v is not None]
            if mi_values:
                logger.debug(f"📊 DynamicRelationshipExtractor: Updated MI estimates: {', '.join(mi_values[:5])}{'...' if len(mi_values) > 5 else ''}")
    
    def update_column_losses(
        self, 
        col_losses_dict: Dict[str, float],
        is_null_baseline: bool = False,
    ):
        """
        Update per-column marginal losses from encoder.
        
        This is the CRITICAL metric for relationship importance!
        
        Args:
            col_losses_dict: {col_name: avg_marginal_loss_for_column}
                Higher loss = harder to predict = more important column
            is_null_baseline: If True, these losses are from NULL-only forward pass
                and should update NULL baseline EMA instead of normal losses
        
        Relationships between high-loss (hard) columns are most valuable.
        Relationships between low-loss (easy) columns can be pruned.
        """
        if is_null_baseline:
            # The aggregated_col_losses already aggregates across all 4 masks
            # So we can use it directly (no need to accumulate across multiple calls)
            # But we need to track that we've processed this batch
            self._null_baseline_mask_count += 1
            
            # Store aggregated losses (already averaged across masks)
            # This matches the normal loss aggregation regime
            for col_name, aggregated_loss in col_losses_dict.items():
                if col_name not in self._null_baseline_losses_this_batch:
                    self._null_baseline_losses_this_batch[col_name] = []
                # Store the aggregated loss (already averaged across masks)
                self._null_baseline_losses_this_batch[col_name].append(aggregated_loss)
            
            # Note: _finalize_null_baseline_batch() will be called after all processing
            # It will average across any multiple calls and update EMA
        else:
            # Normal loss update
            self.col_marginal_losses = col_losses_dict.copy() if col_losses_dict else {}
            
            # Compute lift for active pairs in this batch
            # Lift = baseline_null_ema[i] - loss_i_with_pair
            # This is the core metric for ranking pairs
            self._update_pair_lift_stats(col_losses_dict)
            
            # Log column losses if available (useful for debugging)
            if logger.isEnabledFor(logging.DEBUG) and col_losses_dict:
                loss_items = sorted(col_losses_dict.items(), key=lambda x: x[1], reverse=True)[:5]
                loss_strs = [f"{k}={v:.4f}" for k, v in loss_items]
                logger.debug(f"📊 DynamicRelationshipExtractor: Updated column losses (top 5 hardest): {', '.join(loss_strs)}")
            
            # Clear active pairs after processing (reset for next batch)
            self._active_pairs_this_batch.clear()
    
    def _ensure_null_baseline_attributes(self):
        """
        Ensure NULL baseline evaluation attributes are initialized.
        This is needed when models are loaded from older checkpoints that don't have these attributes.
        """
        if not hasattr(self, '_null_evaluation_pending'):
            self._null_evaluation_pending = False
        if not hasattr(self, '_step_counter'):
            self._step_counter = 0
        if not hasattr(self, '_null_every_steps_early'):
            self._null_every_steps_early = 5
        if not hasattr(self, '_null_every_steps_late'):
            self._null_every_steps_late = 10
        if not hasattr(self, '_null_early_epochs'):
            self._null_early_epochs = 20
        if not hasattr(self, '_null_batch_mask_modes'):
            self._null_batch_mask_modes = []
        if not hasattr(self, '_null_baseline_losses_this_batch'):
            self._null_baseline_losses_this_batch = {}
        if not hasattr(self, '_null_baseline_mask_count'):
            self._null_baseline_mask_count = 0
        if not hasattr(self, 'current_epoch'):
            # Default to a high epoch number so we use late frequency during prediction
            self.current_epoch = 999
        if not hasattr(self, '_null_baseline_alpha'):
            self._null_baseline_alpha = 0.1  # EMA decay rate
        if not hasattr(self, '_null_sample_rate'):
            # Default based on column count if available
            if hasattr(self, 'n_cols') and self.n_cols > 0:
                self._null_sample_rate = 20.0 / self.n_cols
            else:
                self._null_sample_rate = 1.0
    
    def _ensure_pair_stats_attributes(self):
        """
        Ensure pair statistics attributes are initialized.
        This is needed when models are loaded from older checkpoints that don't have these attributes.
        """
        if not hasattr(self, '_pair_stats'):
            self._pair_stats: Dict[Tuple[int, int], Dict] = {}
        if not hasattr(self, '_pair_lift_alpha'):
            self._pair_lift_alpha = 0.1
        if not hasattr(self, '_active_pairs_this_batch'):
            self._active_pairs_this_batch: Set[Tuple[int, int]] = set()
        if not hasattr(self, 'pair_contributions'):
            self.pair_contributions = {}
            # Initialize for all pairs if all_pairs exists
            if hasattr(self, 'all_pairs'):
                for pair in self.all_pairs:
                    self.pair_contributions[pair] = 0.0
        if not hasattr(self, '_pair_scores'):
            self._pair_scores: Dict[Tuple[int, int], int] = {}
            # Initialize scores for all pairs if all_pairs exists
            if hasattr(self, 'all_pairs'):
                for pair in self.all_pairs:
                    self._pair_scores[pair] = 0
        if not hasattr(self, 'col_marginal_losses'):
            self.col_marginal_losses: Dict[str, float] = {}
        if not hasattr(self, 'col_mi_estimates'):
            self.col_mi_estimates: Dict[str, Optional[float]] = {}
        if not hasattr(self, '_null_baseline_ema'):
            self._null_baseline_ema: Dict[str, float] = {}
        if not hasattr(self, '_null_baseline_source'):
            self._null_baseline_source: Dict[str, str] = {}
        if not hasattr(self, '_null_baseline_n'):
            self._null_baseline_n: Dict[str, int] = {}
        if not hasattr(self, '_last_step_active_pairs'):
            self._last_step_active_pairs: Optional[Set[Tuple[int, int]]] = None
        if not hasattr(self, 'MIN_SUPPORT_TRACK'):
            self.MIN_SUPPORT_TRACK = 10  # Default: reasonable minimum for tracking
        if not hasattr(self, 'MIN_SUPPORT_RANK'):
            self.MIN_SUPPORT_RANK = 20  # Default: reasonable minimum for ranking
        if not hasattr(self, 'MIN_SUPPORT_PRUNE'):
            self.MIN_SUPPORT_PRUNE = 50  # Default: reasonable minimum for pruning
        if not hasattr(self, '_initial_min_support_rank'):
            self._initial_min_support_rank = self.MIN_SUPPORT_RANK
        if not hasattr(self, 'use_ucb_selection'):
            self.use_ucb_selection = True  # Default: enable UCB selection
        if not hasattr(self, 'ucb_alpha'):
            self.ucb_alpha = 1.5  # Default UCB exploration parameter
        if not hasattr(self, 'edge_dropout_prob'):
            self.edge_dropout_prob = 0.2  # Default edge dropout probability
        if not hasattr(self, 'confidence_weight_n0'):
            self.confidence_weight_n0 = 40  # Default confidence weighting threshold
        if not hasattr(self, 'exploration_epochs'):
            self.exploration_epochs = 10  # Default exploration epochs
        if not hasattr(self, '_epoch_dropout_stats'):
            self._epoch_dropout_stats = {
                'total_edges_before': 0,
                'total_edges_after': 0,
                'total_dropped': 0,
                'steps_with_dropout': 0,
            }
        if not hasattr(self, '_epoch_active_edges'):
            self._epoch_active_edges = []  # List of active directed edge counts per step
        if not hasattr(self, 'top_k_fraction'):
            self.top_k_fraction = 0.40  # Default top-k fraction
        if not hasattr(self, 'progressive_pruning'):
            self.progressive_pruning = True  # Default: enable progressive pruning
        if not hasattr(self, 'current_epoch'):
            self.current_epoch = 0
        if not hasattr(self, '_stored_grad_norms'):
            self._stored_grad_norms: Dict[str, float] = {}
        if not hasattr(self, 'all_pairs'):
            # Generate all unique pairs if not exists
            if hasattr(self, 'n_cols'):
                self.all_pairs = []
                for i in range(self.n_cols):
                    for j in range(i + 1, self.n_cols):
                        self.all_pairs.append((i, j))
            else:
                self.all_pairs = []
        if not hasattr(self, '_directed_pairs'):
            self._directed_pairs: Set[Tuple[int, int]] = set()
            if hasattr(self, 'n_cols'):
                for i in range(self.n_cols):
                    for j in range(self.n_cols):
                        if i != j:
                            self._directed_pairs.add((i, j))
        if not hasattr(self, '_last_adaptive_check_step'):
            self._last_adaptive_check_step = -1
        if not hasattr(self, '_adaptive_check_interval'):
            self._adaptive_check_interval = 100
        if not hasattr(self, 'disabled_pairs'):
            self.disabled_pairs: set = set()
        if not hasattr(self, 'min_relationships_to_keep'):
            # Default: keep at least max(5, n_cols/2)
            if hasattr(self, 'n_cols'):
                min_keep = max(5, self.n_cols // 2)
                self.min_relationships_to_keep = min(min_keep, self.n_cols) if self.n_cols > 0 else 5
            else:
                self.min_relationships_to_keep = 5
        if not hasattr(self, 'target_pruning_epochs'):
            self.target_pruning_epochs = 15  # Default
        if not hasattr(self, 'pairs_to_prune_per_epoch'):
            self.pairs_to_prune_per_epoch = 0  # Will be calculated if progressive_pruning is enabled
        if not hasattr(self, '_contribution_ema_alpha'):
            self._contribution_ema_alpha = 0.1
        if not hasattr(self, 'max_column_fraction'):
            self.max_column_fraction = 0.10  # Default: 10% cap per column
        if not hasattr(self, 'viz_output_dir'):
            self.viz_output_dir = None  # Default: visualizations disabled
        if not hasattr(self, '_tokens_for_gradient_check'):
            self._tokens_for_gradient_check: List[Tuple[Tuple[int, int], torch.Tensor]] = []
        if not hasattr(self, '_batch_counter'):
            self._batch_counter = 0
        if not hasattr(self, '_log_every_n_batches'):
            self._log_every_n_batches = 20
        if not hasattr(self, 'operation_contributions'):
            # NOTE: Embedding arithmetic ops have been removed - only presence pattern remains
            self.operation_contributions = {
                'presence': 0.0,
            }
        if not hasattr(self, 'contribution_history'):
            self.contribution_history: List[Dict[Tuple[int, int], float]] = []
        if not hasattr(self, 'joint_mi_estimate'):
            self.joint_mi_estimate: Optional[float] = None
        if not hasattr(self, '_pair_active_epochs'):
            self._pair_active_epochs: Dict[Tuple[int, int], Set[int]] = {}
        if not hasattr(self, '_column_loss_history'):
            self._column_loss_history: Dict[str, List[float]] = {}
        if not hasattr(self, '_all_epochs'):
            self._all_epochs: Set[int] = set()
        if not hasattr(self, 'pruned_pairs_per_column'):
            self.pruned_pairs_per_column: Optional[Dict[int, List[int]]] = None
        if not hasattr(self, '_pruned_pairs_list'):
            self._pruned_pairs_list: Optional[List[Tuple[int, int]]] = None
        if not hasattr(self, '_weight_snapshots'):
            self._weight_snapshots = {}  # {epoch: {op_name: weight_norm}}
        if not hasattr(self, '_weight_deltas'):
            self._weight_deltas = {}  # {op_name: [delta_per_epoch]}
        if not hasattr(self, '_session_id'):
            self._session_id: Optional[str] = None
        if not hasattr(self, '_known_good_pairs'):
            self._known_good_pairs: Set[Tuple[int, int]] = set()
        if not hasattr(self, '_known_bad_pairs'):
            self._known_bad_pairs: Set[Tuple[int, int]] = set()
        if not hasattr(self, '_history_loaded'):
            self._history_loaded = False
        if not hasattr(self, '_dataset_hash'):
            self._dataset_hash: Optional[str] = None
        if not hasattr(self, 'use_fusion'):
            self.use_fusion = True  # Default: use fusion mode
        if not hasattr(self, 'ops_per_pair'):
            # NOTE: With embedding arithmetic removed, always 1 op per pair (presence pattern)
            self.ops_per_pair = 1
        if not hasattr(self, 'max_pairs_per_chunk'):
            # Default: conservative limit
            self.max_pairs_per_chunk = 300
        if not hasattr(self, 'max_coarse_pairs'):
            self.max_coarse_pairs = 300
        if not hasattr(self, 'coarse_exploration_dim'):
            self.coarse_exploration_dim = 32
        if not hasattr(self, '_median_abs_lift'):
            self._median_abs_lift: Optional[float] = None
        if not hasattr(self, '_last_pairs_to_compute'):
            self._last_pairs_to_compute: Optional[List[Tuple[int, int]]] = None
        if not hasattr(self, '_selection_rng'):
            # Will be created on demand when needed
            pass  # Don't create here, created lazily
        if not hasattr(self, '_sample_rng'):
            # Will be created on demand when needed
            pass  # Don't create here, created lazily
        if not hasattr(self, '_coarse_sample_logged'):
            self._coarse_sample_logged = False
        if not hasattr(self, '_chunking_logged'):
            self._chunking_logged = False
        # Per-op-type gradient tracking (for type-aware ops effectiveness)
        if not hasattr(self, '_op_type_gradient_stats'):
            self._op_type_gradient_stats = {
                'generic_fused': {'grad_sum': 0.0, 'grad_sum_sq': 0.0, 'grad_count': 0, 'grad_max': 0.0},
                'set_timestamp': {'grad_sum': 0.0, 'grad_sum_sq': 0.0, 'grad_count': 0, 'grad_max': 0.0},
                'scalar_timestamp': {'grad_sum': 0.0, 'grad_sum_sq': 0.0, 'grad_count': 0, 'grad_max': 0.0},
                'set_set': {'grad_sum': 0.0, 'grad_sum_sq': 0.0, 'grad_count': 0, 'grad_max': 0.0},
                'set_scalar': {'grad_sum': 0.0, 'grad_sum_sq': 0.0, 'grad_count': 0, 'grad_max': 0.0},
                'scalar_scalar': {'grad_sum': 0.0, 'grad_sum_sq': 0.0, 'grad_count': 0, 'grad_max': 0.0},
            }
        if not hasattr(self, '_op_type_tokens_for_grad'):
            self._op_type_tokens_for_grad = {
                'generic_fused': [],
                'set_timestamp': [],
                'scalar_timestamp': [],
                'set_set': [],
                'set_scalar': [],
                'scalar_scalar': [],
            }
        # Type-aware pair scorers (for limiting/pruning type-aware pairs)
        if not hasattr(self, '_type_aware_scorers'):
            self._type_aware_scorers: Dict[str, Any] = {}

    def should_evaluate_null_baseline(self, is_first_mask: bool = True) -> bool:
        """
        Check if we should evaluate NULL baseline this step.
        
        Note: This is called multiple times per batch (for mask_1, mask_2, short_1, short_2).
        We evaluate on ALL masks in the batch to match the aggregation regime.
        
        Args:
            is_first_mask: True if this is the first mask call (mask_1), False for subsequent masks
        
        Returns:
            True if NULL-only evaluation should be run for this mask
        """
        # Ensure attributes are initialized (for backward compatibility with old checkpoints)
        self._ensure_null_baseline_attributes()

        # During prediction/inference, never evaluate NULL baseline
        # Also clear any stale pending flag from previous training
        if not self.training:
            if self._null_evaluation_pending:
                self._null_evaluation_pending = False
            return False
        
        # On first mask call, check if we should start evaluation
        if is_first_mask:
            # Check if already evaluating this batch
            if self._null_evaluation_pending:
                return True  # Continue evaluating for remaining masks
            
            # Increment counter (once per batch)
            self._step_counter += 1
            
            # Adaptive frequency: more frequent early in training
            if self.current_epoch < self._null_early_epochs:
                every_steps = self._null_every_steps_early
            else:
                every_steps = self._null_every_steps_late
            
            # Check if we should start evaluation
            should_start = (self._step_counter % every_steps == 0)
            
            if should_start:
                self._null_evaluation_pending = True
                self._null_baseline_losses_this_batch = {}  # Reset accumulator
                self._null_baseline_mask_count = 0  # Reset counter
                self._null_batch_mask_modes = []  # Reset mode tracking for invariant check
                return True
            else:
                return False
        else:
            # For subsequent masks, continue evaluation if pending
            return self._null_evaluation_pending
    
    def _finalize_null_baseline_batch(self):
        """
        Finalize NULL baseline EMA update after batch is processed.

        The losses passed to update_column_losses() are already aggregated
        across all 4 masks (matching normal loss aggregation), so we use them directly.
        """
        # Ensure attributes are initialized (for backward compatibility with old checkpoints)
        self._ensure_null_baseline_attributes()

        if not self._null_baseline_losses_this_batch:
            # CRITICAL: Still need to clear the pending flag even if no losses accumulated!
            # Otherwise the flag stays True forever and blocks normal training.
            self._null_evaluation_pending = False
            self._null_baseline_mask_count = 0
            self._null_batch_mask_modes = []
            logger.debug("[NULL_FINALIZE] No losses accumulated, but clearing pending flag")
            return
        
        # The losses are already aggregated per mask call
        # If we got multiple calls (shouldn't happen, but be safe), average them
        aggregated_losses = {}
        for col_name, losses in self._null_baseline_losses_this_batch.items():
            if losses:
                # Average across calls (should be 1, but handle multiple gracefully)
                aggregated_losses[col_name] = sum(losses) / len(losses)
        
        # Update EMA with aggregated losses
        for col_name, aggregated_loss in aggregated_losses.items():
            if col_name not in self._null_baseline_ema:
                # Initialize on first observation
                self._null_baseline_ema[col_name] = aggregated_loss
                self._null_baseline_n[col_name] = 1
                self._null_baseline_source[col_name] = "null"
            else:
                # Update EMA
                # Use adaptive alpha: higher early (0.2) for fast adaptation, lower later (0.1)
                if self.current_epoch < self._null_early_epochs:
                    alpha = 0.2  # Faster adaptation early
                else:
                    alpha = self._null_baseline_alpha  # Slower adaptation later
                
                self._null_baseline_ema[col_name] = (
                    (1 - alpha) * self._null_baseline_ema[col_name] + alpha * aggregated_loss
                )
                self._null_baseline_n[col_name] += 1
                self._null_baseline_source[col_name] = "null"
        
        # CRITICAL INVARIANT CHECK: All 4 masks (full_1, full_2, short_1, short_2) must use the same mode
        # 
        # Expected structure:
        # - modes[0] = mask_1 mode (generates full_1 and short_1 from same joint_encoder() call)
        # - modes[1] = mask_2 mode (generates full_2 and short_2 from same joint_encoder() call)
        # - modes[2] = unmasked mode (if present, doesn't contribute to marginal losses)
        #
        # Since short and full come from the same joint_encoder() call, checking mask_1 == mask_2
        # is sufficient to ensure all 4 masks are consistent, AS LONG AS we verify:
        # 1. We have at least 2 entries (mask_1 and mask_2)
        # 2. The first two entries correspond to mask_1 and mask_2 (not reordered)
        # 3. They match each other
        #
        # ASSUMPTION: The unmasked call (if present) doesn't affect masked calls through cached state.
        # This is safe because:
        # - Relationship extractor forward() is stateless (no caching between calls)
        # - Joint encoder uses a transformer (stateless by design)
        # - All state updates happen via update_column_losses(), not during forward()
        
        # NOTE: Mode tracking validation is disabled because the tracking code was never implemented.
        # The _null_batch_mask_modes list is reset but never populated during forward passes.
        # The NULL baseline EMA update still works correctly without this validation.
        
        # Clear accumulator, flag, and mode tracking
        self._null_baseline_losses_this_batch = {}
        self._null_evaluation_pending = False
        self._null_baseline_mask_count = 0
        self._null_batch_mask_modes = []
        
        # Log coverage (DEBUG level, more frequent for debugging)
        # Also log at INFO level every 10 steps for visibility
        coverage = self.get_null_baseline_coverage()
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"📊 NULL Baseline updated: {coverage['cols_with_baseline']}/{coverage['total_cols']} cols ({coverage['coverage_pct']:.1f}%)")
        
        # INFO level logging every 10 steps (more frequent than epoch-based)
        if self._step_counter % 50 == 0:  # Every 50 steps = ~5 batches at 10 steps/batch
            logger.info(f"📊 NULL Baseline Coverage (step {self._step_counter}):")
            logger.info(f"   Columns with baseline: {coverage['cols_with_baseline']}/{coverage['total_cols']} ({coverage['coverage_pct']:.1f}%)")
            logger.info(f"   Source: {coverage['null_source']} NULL-only, {coverage['bootstrap_source']} bootstrap")
            
            if coverage['coverage_pct'] < 50:
                logger.warning(f"⚠️  Low NULL baseline coverage ({coverage['coverage_pct']:.1f}%) - lift calculations may be unreliable")
    
    def get_null_baseline_coverage(self) -> Dict[str, float]:
        """
        Get NULL baseline coverage metrics.
        
        Returns:
            Dict with coverage statistics
        """
        total_cols = len(self.col_names)
        cols_with_baseline = len(self._null_baseline_ema)
        coverage_pct = (cols_with_baseline / total_cols * 100) if total_cols > 0 else 0
        
        # Get baseline sources
        null_count = sum(1 for src in self._null_baseline_source.values() if src == "null")
        bootstrap_count = sum(1 for src in self._null_baseline_source.values() if src == "bootstrap")
        
        return {
            'total_cols': total_cols,
            'cols_with_baseline': cols_with_baseline,
            'coverage_pct': coverage_pct,
            'null_source': null_count,
            'bootstrap_source': bootstrap_count,
        }
    
    def _record_epoch_history(
        self,
        epoch_idx: int,
        active_pairs: List[Tuple[int, int]],
        col_losses: Dict[str, float],
    ):
        """
        STAGE 1: Record epoch history for causal inference and validation.
        
        Tracks:
        - Which pairs were active this epoch
        - Per-column losses over time
        - All epochs seen
        
        This data enables:
        - Causal lift calculation (paired vs unpaired improvement)
        - Validation (does importance predict actual lift?)
        """
        self._all_epochs.add(epoch_idx)
        
        # Store column losses
        for col_name, loss in col_losses.items():
            if col_name not in self._column_loss_history:
                self._column_loss_history[col_name] = []
            self._column_loss_history[col_name].append(loss)
        
        # Track which pairs were active (undirected)
        for pair in active_pairs:
            if pair not in self._pair_active_epochs:
                self._pair_active_epochs[pair] = set()
            self._pair_active_epochs[pair].add(epoch_idx)
        
        # Update pair stats counts (directed)
        # When pair (i,j) is active, increment counts for both (i->j) and (j->i)
        for pair in active_pairs:
            i, j = pair
            # Initialize if needed
            if (i, j) not in self._pair_stats:
                self._pair_stats[(i, j)] = {'n': 0, 'lift_ema': 0.0}
            if (j, i) not in self._pair_stats:
                self._pair_stats[(j, i)] = {'n': 0, 'lift_ema': 0.0}
            
            # Note: We don't increment 'n' here - that happens when we compute lift
            # This just ensures the stats dict exists
        
        # Also record in causal scorer and validator
        self.causal_scorer.record_epoch(epoch_idx, active_pairs, col_losses)
        self.validator.record_epoch(epoch_idx, active_pairs, col_losses)
    
    def _compute_lift_from_null_baseline(
        self,
        directed_pair: Tuple[int, int],  # (i -> j): effect of i on j
    ) -> Optional[float]:
        """
        Phase 1 lift calculation: lift = NULL_baseline - current_loss
        
        Args:
            directed_pair: (i, j) where we measure effect on j when paired with i
        
        Returns:
            lift value (positive = helps, negative = hurts) or None if baseline missing
        """
        i, j = directed_pair
        col_j_name = self.col_names[j] if j < len(self.col_names) else f"col_{j}"
        
        # Get NULL baseline for target column
        if col_j_name not in self._null_baseline_ema:
            return None  # No baseline yet
        
        null_baseline = self._null_baseline_ema[col_j_name]
        
        # Get current loss for target column
        current_loss = self.col_marginal_losses.get(col_j_name)
        if current_loss is None:
            return None  # No current loss
        
        # Lift = improvement from NULL baseline
        lift = null_baseline - current_loss
        
        return lift
    
    def _update_pair_lift_stats(
        self,
        col_losses_dict: Dict[str, float],
    ):
        """
        Update lift statistics for all active pairs in this batch.
        
        For each directed pair (i->j) that was active:
        - Compute lift = baseline_null_ema[j] - loss_j_with_pair
        - Update _pair_stats with EMA of lift
        
        Args:
            col_losses_dict: {col_name: aggregated_marginal_loss} from this batch
                These losses are already aggregated across all 4 masks, matching NULL baseline regime
        """
        if not self._active_pairs_this_batch:
            return  # No active pairs this batch
        
        # Increment step counter (once per batch)
        self._step_counter += 1
        
        # Track lift statistics for diagnostics
        lift_values = []  # Track all lift values for this batch
        negative_lifts = 0
        
        # Initialize median absolute lift if not already set (for outlier clipping)
        if not hasattr(self, '_median_abs_lift'):
            self._median_abs_lift = None
        
        # For each active directed pair (i->j), compute lift
        # NOTE: Relationships are symmetric (pooled and injected into CLS, affecting all columns),
        # so tracking both (i,j) and (j,i) is correct. All columns receive information from all relationships.
        # Lift measures: how much does the relationship help predict j?
        for directed_pair in self._active_pairs_this_batch:
            i, j = directed_pair
            
            # Get column name for target column j
            if j >= len(self.col_names):
                continue  # Invalid column index
            col_j_name = self.col_names[j]
            
            # Get loss for column j (when paired with i)
            loss_j_with_pair = col_losses_dict.get(col_j_name)
            if loss_j_with_pair is None:
                continue  # No loss for this column
            
            # Sanity check: loss should be finite
            if not (math.isfinite(loss_j_with_pair) and loss_j_with_pair >= 0):
                logger.warning(
                    f"⚠️ Invalid loss for {col_j_name} in pair ({i}->{j}): {loss_j_with_pair}"
                )
                continue
            
            # Get NULL baseline for column j
            null_baseline = self._null_baseline_ema.get(col_j_name)
            
            if null_baseline is None:
                # No baseline yet - can't compute lift
                # This is OK during early training, but we won't rank/prune without baseline
                continue
            
            # Sanity check: baseline should be finite
            if not (math.isfinite(null_baseline) and null_baseline >= 0):
                logger.warning(
                    f"⚠️ Invalid NULL baseline for {col_j_name}: {null_baseline}"
                )
                continue
            
            # CRITICAL: Detect training divergence - if current loss is >> baseline, training may have exploded
            # Skip lift updates in this case to avoid corrupting statistics
            if loss_j_with_pair > null_baseline * 10:
                # Loss is 10x+ higher than baseline - likely training divergence
                if logger.isEnabledFor(logging.DEBUG) or self._step_counter % 50 == 0:
                    logger.warning(
                        f"⚠️ Training divergence detected for {col_j_name}: "
                        f"current_loss={loss_j_with_pair:.2f} >> baseline={null_baseline:.2f} "
                        f"(ratio={loss_j_with_pair/null_baseline:.1f}x). "
                        f"Skipping lift update to avoid corrupting statistics."
                    )
                continue
            
            # Compute lift: improvement from NULL baseline
            # Positive lift = relationship helps (reduces loss)
            # Negative lift = relationship hurts (increases loss) - THIS IS VALID SIGNAL
            lift = null_baseline - loss_j_with_pair
            
            # Sanity check: lift should be finite (but can be negative!)
            if not math.isfinite(lift):
                logger.warning(
                    f"⚠️ Invalid lift for pair ({i}->{j}): {lift} "
                    f"(baseline={null_baseline}, loss={loss_j_with_pair})"
                )
                continue
            
            # Optional: Clip extreme outliers (but preserve negative signal)
            # Use median absolute lift as reference for clipping
            if self._median_abs_lift is not None and self._median_abs_lift > 0:
                clip_range = 10.0 * self._median_abs_lift
                if abs(lift) > clip_range:
                    lift = math.copysign(clip_range, lift)  # Preserve sign
            
            # Track for diagnostics
            lift_values.append(lift)
            if lift < 0:
                negative_lifts += 1
            
            # Update pair stats with lift (source is always "null" when we have baseline)
            self._update_pair_lift_ema(directed_pair, lift, source="null")
            
            # DEBUG: Log occasionally for sanity checking
            if logger.isEnabledFor(logging.DEBUG) and self._step_counter % 50 == 0:
                logger.debug(
                    f"Lift update: ({i}->{j}) lift={lift:.4f} "
                    f"(baseline={null_baseline:.4f}, loss={loss_j_with_pair:.4f})"
                )
        
        # Update median absolute lift for outlier clipping (EMA)
        if lift_values:
            median_abs_lift = sorted([abs(l) for l in lift_values])[len(lift_values) // 2]
            if self._median_abs_lift is None:
                self._median_abs_lift = median_abs_lift
            else:
                # EMA update
                self._median_abs_lift = 0.9 * self._median_abs_lift + 0.1 * median_abs_lift
            
            # Log negative lift percentage (great diagnostic)
            negative_pct = (negative_lifts / len(lift_values)) * 100 if lift_values else 0
            if logger.isEnabledFor(logging.DEBUG) or (self._step_counter % 100 == 0 and negative_pct > 10):
                logger.info(
                    f"📊 Lift stats (step {self._step_counter}): "
                    f"{len(lift_values)} updates, {negative_pct:.1f}% negative lifts "
                    f"(median_abs={self._median_abs_lift:.4f})"
                )
    
    def _update_pair_lift_ema(
        self,
        directed_pair: Tuple[int, int],
        lift: float,
        source: str = "null",  # "null" or "bootstrap"
    ):
        """
        Update EMA of lift for a directed pair.
        
        Args:
            directed_pair: (i, j) directed pair
            lift: Lift value (baseline - current_loss)
            source: "null" if from NULL baseline, "bootstrap" if from unpaired fallback
        """
        if directed_pair not in self._pair_stats:
            self._pair_stats[directed_pair] = {
                'n': 0,
                'lift_ema': 0.0,
                'lift_max': None,  # Peak lift ever observed (captures "teaching" value)
                'lift_mass': 0.0,  # Cumulative positive lift (total contribution)
                'last_step': 0,
                'source_counts': {'null': 0, 'bootstrap': 0}
            }

        stats = self._pair_stats[directed_pair]

        # Ensure source_counts exists (backward compatibility for old entries)
        if 'source_counts' not in stats:
            stats['source_counts'] = {'null': 0, 'bootstrap': 0}
        # Ensure lift_max and lift_mass exist (backward compatibility)
        if 'lift_max' not in stats:
            stats['lift_max'] = None
        if 'lift_mass' not in stats:
            stats['lift_mass'] = 0.0

        stats['n'] += 1
        stats['last_step'] = self._step_counter

        # Track source
        if source in stats['source_counts']:
            stats['source_counts'][source] += 1

        # Update EMA
        if stats['n'] == 1:
            stats['lift_ema'] = lift
        else:
            alpha = self._pair_lift_alpha
            stats['lift_ema'] = (1 - alpha) * stats['lift_ema'] + alpha * lift

        # Track peak lift (max ever observed)
        if stats['lift_max'] is None or lift > stats['lift_max']:
            stats['lift_max'] = lift

        # Track cumulative positive lift ("lift mass" = total value delivered)
        if lift > 0:
            stats['lift_mass'] += lift

        # Route lift update to type-aware scorer if applicable
        # Use undirected pair (min, max) for scorer lookup
        i, j = directed_pair
        undirected_pair = (min(i, j), max(i, j))
        op_type = self.get_op_type_for_pair(i, j)

        # DEBUG: Track routing to type-aware scorers
        if not hasattr(self, '_debug_type_aware_routing'):
            self._debug_type_aware_routing = {'calls': 0, 'routed': 0, 'no_op_type': 0, 'no_scorer': 0, 'not_in_pairs': 0}
        self._debug_type_aware_routing['calls'] += 1

        if op_type is not None and hasattr(self, '_type_aware_scorers'):
            scorer = self._type_aware_scorers.get(op_type)
            if scorer is not None and undirected_pair in scorer.all_pairs:
                scorer.update_lift(undirected_pair, lift, self.current_epoch)
                self._debug_type_aware_routing['routed'] += 1
            elif scorer is None:
                self._debug_type_aware_routing['no_scorer'] += 1
            else:
                self._debug_type_aware_routing['not_in_pairs'] += 1
        else:
            self._debug_type_aware_routing['no_op_type'] += 1

    def _compute_pair_scores(
        self,
        active_pairs: List[Tuple[int, int]],
    ) -> Tuple[Dict[Tuple[int, int], float], Dict]:
        """
        Phase 1: Compute pair scores using NULL baseline lift.
        
        Returns:
            (scores_dict, diagnostics_dict)
            scores_dict: {(i,j): score} for rankable pairs only
            diagnostics: coverage metrics and skip counts
        """
        scores = {}
        diagnostics = {
            'total_pairs': len(active_pairs),
            'observed_pairs': 0,  # Pairs with at least 1 observation
            'trackable_pairs': 0,  # Pairs with n_total >= MIN_SUPPORT_TRACK
            'skipped_track': 0,
            'skipped_no_baseline': 0,
            'skipped_rank': 0,
            'rankable': 0,  # Pairs with n_total >= MIN_SUPPORT_RANK and has baseline
            'prunable': 0,  # Pairs with n_total >= MIN_SUPPORT_PRUNE and has baseline
        }
        
        # For each undirected pair (i,j), compute scores for both directions
        # CRITICAL: Use n_total = n_ij + n_ji (undirected pair support) for all support gating
        # This is consistent with sparse sampling where individual directions may have low counts
        # but the undirected pair accumulates enough observations across both directions
        for pair in active_pairs:
            i, j = pair
            
            # Get pair stats for both directions
            stats_ij = self._pair_stats.get((i, j), {})
            stats_ji = self._pair_stats.get((j, i), {})
            
            n_ij = stats_ij.get('n', 0)
            n_ji = stats_ji.get('n', 0)
            n_total = n_ij + n_ji  # Undirected pair support (sum of both directions)
            
            # Track observed pairs (at least 1 observation)
            if n_total > 0:
                diagnostics['observed_pairs'] += 1
            
            # Skip if insufficient support for tracking (using n_total)
            if n_total < self.MIN_SUPPORT_TRACK:
                diagnostics['skipped_track'] += 1
                continue
            
            # Track trackable pairs (n_total >= MIN_SUPPORT_TRACK)
            diagnostics['trackable_pairs'] += 1
            
            # Get lift EMA for both directions
            lift_ema_ij = stats_ij.get('lift_ema')
            lift_ema_ji = stats_ji.get('lift_ema')
            
            # Check source: only use NULL baseline, block bootstrap
            source_counts_ij = stats_ij.get('source_counts', {})
            source_counts_ji = stats_ji.get('source_counts', {})
            
            # CRITICAL: Block bootstrap from ranking/pruning
            # Only use pairs where we have NULL baseline (not bootstrap fallback)
            has_null_baseline_ij = (
                lift_ema_ij is not None and 
                source_counts_ij.get('null', 0) > 0
            )
            has_null_baseline_ji = (
                lift_ema_ji is not None and 
                source_counts_ji.get('null', 0) > 0
            )
            
            # Skip if no NULL baseline for either direction
            if not has_null_baseline_ij and not has_null_baseline_ji:
                diagnostics['skipped_no_baseline'] += 1
                continue
            
            # Skip if insufficient support for ranking (using n_total)
            if n_total < self.MIN_SUPPORT_RANK:
                diagnostics['skipped_rank'] += 1
                continue
            
            # Skip if lift_ema is not finite (sanity check)
            if (lift_ema_ij is not None and not math.isfinite(lift_ema_ij)) or \
               (lift_ema_ji is not None and not math.isfinite(lift_ema_ji)):
                continue  # Invalid lift, skip

            # Compute confidence weights based on observation counts
            # More observations = higher confidence in the lift estimate
            confidence_weight_ij = min(1.0, n_ij / self.MIN_SUPPORT_RANK) if n_ij > 0 else 0.0
            confidence_weight_ji = min(1.0, n_ji / self.MIN_SUPPORT_RANK) if n_ji > 0 else 0.0

            # Use EMA-based scoring for pair selection
            # This captures current utility - pairs that are actively helping
            lift_ema_ij_val = lift_ema_ij if lift_ema_ij is not None else 0.0
            lift_ema_ji_val = lift_ema_ji if lift_ema_ji is not None else 0.0

            # Score = weighted sum of both directions' lift EMA
            score = (lift_ema_ij_val * confidence_weight_ij) + (lift_ema_ji_val * confidence_weight_ji)

            # Store score (use undirected pair as key for compatibility)
            scores[pair] = score
            diagnostics['rankable'] += 1
            
            # Track prunable pairs (n_total >= MIN_SUPPORT_PRUNE)
            if n_total >= self.MIN_SUPPORT_PRUNE:
                diagnostics['prunable'] += 1
        
        return scores, diagnostics
    
    def _compute_causal_importance(
        self,
        active_pairs: List[Tuple[int, int]],
    ) -> Dict[Tuple[int, int], float]:
        """
        Phase 1: Compute pair importance using NULL baseline lift.
        
        This replaces the old heuristic with controlled lift calculation.
        Uses NULL baseline EMA instead of unpaired epochs for stability.
        
        Returns:
            {(col_i, col_j): importance_score} for rankable pairs only
        """
        # Use Phase 1 scoring (NULL baseline lift)
        scores, diagnostics = self._compute_pair_scores(active_pairs)
        
        # Log comprehensive coverage metrics
        total = diagnostics['total_pairs']
        observed = diagnostics['observed_pairs']
        trackable = diagnostics['trackable_pairs']
        rankable = diagnostics['rankable']
        prunable = diagnostics['prunable']
        
        # Calculate percentages
        observed_pct = (observed / total * 100) if total > 0 else 0
        trackable_pct = (trackable / total * 100) if total > 0 else 0
        rankable_pct = (rankable / total * 100) if total > 0 else 0
        prunable_pct = (prunable / total * 100) if total > 0 else 0
        
        if self.current_epoch % 10 == 0:  # Log every 10 epochs
            logger.info(f"📊 Relationship coverage (epoch {self.current_epoch}):")
            logger.info(f"   Total directed pairs possible: {self.n_cols * (self.n_cols - 1)}")
            logger.info(f"   Total undirected pairs: {total}")
            logger.info(f"   Observed pairs (n≥1): {observed} ({observed_pct:.1f}%)")
            logger.info(f"   Trackable pairs (n_total≥{self.MIN_SUPPORT_TRACK}): {trackable} ({trackable_pct:.1f}%)")
            logger.info(f"   Rankable pairs (n_total≥{self.MIN_SUPPORT_RANK}, has baseline): {rankable} ({rankable_pct:.1f}%)")
            logger.info(f"   Prunable pairs (n_total≥{self.MIN_SUPPORT_PRUNE}, has baseline): {prunable} ({prunable_pct:.1f}%)")
            logger.info(f"   Skipped (tracking): {diagnostics['skipped_track']}")
            logger.info(f"   Skipped (no baseline): {diagnostics['skipped_no_baseline']}")
            logger.info(f"   Skipped (ranking): {diagnostics['skipped_rank']}")
            
            # Only warn after epoch 5 - early training naturally has low coverage
            if self.current_epoch >= 5:
                if rankable_pct < 20:
                    logger.warning(f"⚠️  Low rankable coverage ({rankable_pct:.1f}%) - most pairs have insufficient data or missing NULL baseline")
                if prunable_pct < 10:
                    logger.warning(f"⚠️  Low prunable coverage ({prunable_pct:.1f}%) - pruning decisions may be limited")
        
        return scores
    
    def _compute_relationship_importance(self) -> Dict[Tuple[int, int], float]:
        """
        DEPRECATED: Old heuristic-based importance.
        
        This method is kept for backward compatibility but now delegates
        to _compute_causal_importance. The old heuristic (|loss_i - loss_j|)
        is replaced with causal lift calculation.
        
        Returns:
            {(col_i, col_j): importance_score}
        """
        active_pairs = [p for p in self.all_pairs if p not in self.disabled_pairs]
        return self._compute_causal_importance(active_pairs)
    
    def should_prune(self) -> bool:
        """Check if we should prune now (at end of exploration phase)."""
        # If progressive pruning is enabled, use progressive_prune_relationships() instead
        if self.progressive_pruning:
            return False  # Don't trigger hard prune
        
        return (
            self.pruned_pairs_per_column is None and 
            self.current_epoch >= self.exploration_epochs
        )
    
    def should_progressive_prune(self) -> bool:
        """Check if we should progressively disable some relationships this epoch."""
        if not self.progressive_pruning:
            return False
        
        # Start pruning after exploration phase
        if self.current_epoch < self.exploration_epochs:
            return False
        
        # Continue pruning until we reach target
        total_pairs = len(self.all_pairs)
        target_remaining = int(total_pairs * self.top_k_fraction)
        current_active = total_pairs - len(self.disabled_pairs)
        
        return current_active > target_remaining
    
    def progressive_prune_relationships(self):
        """
        Progressively disable the least important relationships based on CAUSAL LIFT.
        Called once per epoch after exploration phase.
        
        METRIC: LCB(lift(i→j) + lift(j→i)) - complexity_penalty
        
        lift(i→j) = improvement_rate(j | paired) - improvement_rate(j | unpaired)
          
        Higher lift = relationship ACTUALLY HELPS learning
        Negative lift = relationship HURTS learning (prune immediately)
        
        Causal approach with counterfactual reasoning:
        - Compares improvement when paired vs unpaired (not just static difference)
        - Uses lower confidence bounds (LCB) to penalize uncertain estimates
        - Recency-weighted (recent epochs matter more as model evolves)
        - Complexity penalty for under-explored pairs
        
        Rules:
        1. Sort all pairs by causal importance (HIGHEST LCB = most benefit)
        2. Always keep top min_relationships_to_keep pairs (safety floor)
        3. From remaining pairs, disable pairs_to_prune_per_epoch with LOWEST LCB
        """
        if not self.should_progressive_prune():
            return
        
        # Get currently active pairs
        active_pairs = [p for p in self.all_pairs if p not in self.disabled_pairs]
        
        if not active_pairs:
            return
        
        # ============================================================================
        # STAGE 1: RECORD HISTORY (for causal inference and validation)
        # ============================================================================
        self._record_epoch_history(self.current_epoch, active_pairs, self.col_marginal_losses)
        
        # ============================================================================
        # STAGE 2: COMPUTE CAUSAL IMPORTANCE (replaces heuristic)
        # ============================================================================
        importance_scores = self._compute_causal_importance(active_pairs)
        
        # ============================================================================
        # LOG IMPORTANCE SCORE DISTRIBUTION - Are pairs differentiated or all the same?
        # ============================================================================
        # Only include pairs that have scores (rankable pairs)
        active_importance_values = [importance_scores[p] for p in active_pairs if p in importance_scores]
        
        # AGGRESSIVE PRUNING: When lift is flat (low CV), relationships are not adding
        # meaningful signal - they're just noise. Prune more aggressively to reduce burden.
        # Normal: pairs_to_prune_per_epoch (typically 9)
        # Flat lift (CV < 0.1): disable 10-20 per epoch until we hit target
        base_prune_count = self.pairs_to_prune_per_epoch
        num_to_disable_target = base_prune_count  # Default to base count
        
        if active_importance_values and len(active_importance_values) > 1:
            mean_imp = np.mean(active_importance_values)
            std_imp = np.std(active_importance_values)
            min_imp = np.min(active_importance_values)
            max_imp = np.max(active_importance_values)
            # Coefficient of variation: std/mean - if low, scores are undifferentiated
            cv = std_imp / mean_imp if mean_imp > 1e-8 else 0.0
            
            logger.info(f"📊 Importance score distribution (n={len(active_pairs)} active pairs):")
            logger.info(f"   Mean: {mean_imp:.6f}  Std: {std_imp:.6f}  CV: {cv:.2f}")
            logger.info(f"   Range: [{min_imp:.6f}, {max_imp:.6f}]")
            
            if cv < 0.1:
                logger.warning(f"   ⚠️  LOW DIFFERENTIATION (CV={cv:.2f} < 0.1) - pairs look similar, pruning may be random!")
                
                # Very flat lift - prune aggressively (10-20 per epoch)
                # Scale based on how far we are from target
                current_active = len(active_pairs)
                target_remaining = getattr(self, 'target_relationships', self.min_relationships_to_keep)
                excess = current_active - target_remaining
                
                if excess > 0:
                    # Prune min(20, excess/2) per epoch to make progress
                    aggressive_prune = min(20, max(10, excess // 2))
                    logger.warning(f"🔪 FLAT LIFT DETECTED (CV={cv:.2f}): Aggressive pruning {aggressive_prune} pairs/epoch (target: {target_remaining}, current: {current_active})")
                    num_to_disable_target = aggressive_prune
            elif cv < 0.3:
                logger.info(f"   ⚡ Moderate differentiation (CV={cv:.2f}) - some signal for pruning")
            else:
                logger.info(f"   ✅ Good differentiation (CV={cv:.2f}) - clear signal for pruning")
        
        # Sort all active pairs by importance (HIGHEST first = most important first)
        # Only include pairs that have scores (rankable pairs)
        # Pairs without scores get default score of -inf (lowest priority)
        pairs_by_importance = [
            (p, importance_scores.get(p, float('-inf'))) 
            for p in active_pairs
        ]
        pairs_by_importance.sort(key=lambda x: x[1], reverse=True)  # HIGHEST first
        
        # ============================================================================
        # PROTECTED FLOOR: Per-column protection to avoid hub lock-in
        # ============================================================================
        # Instead of "top N globally" (which creates hub lock-in), protect:
        # - Top 1-2 pairs per column (ensures each column has some relationships)
        # - With degree cap: max 4 protected edges per column (prevents hub dominance)
        # ============================================================================
        protected_set = set()
        protected_pairs = []
        max_protected_per_column = 4  # Degree cap to prevent hub lock-in
        min_protected_per_column = 1  # Ensure each column has at least 1 protected edge
        
        # Count protected edges per column
        protected_count_per_column = {j: 0 for j in range(self.n_cols)}
        
        # First pass: protect top pairs per column (up to degree cap)
        for pair, importance in pairs_by_importance:
            if len(protected_set) >= self.min_relationships_to_keep:
                break  # Reached global minimum
            
            i, j = pair
            # Check if we can protect this pair without exceeding degree caps
            can_protect_i = protected_count_per_column[i] < max_protected_per_column
            can_protect_j = protected_count_per_column[j] < max_protected_per_column
            
            if can_protect_i and can_protect_j:
                protected_set.add(pair)
                protected_pairs.append((pair, importance))
                protected_count_per_column[i] += 1
                protected_count_per_column[j] += 1
        
        # Second pass: ensure minimum per column (if we haven't hit global cap)
        if len(protected_set) < self.min_relationships_to_keep:
            for pair, importance in pairs_by_importance:
                if len(protected_set) >= self.min_relationships_to_keep:
                    break
                
                if pair in protected_set:
                    continue  # Already protected
                
                i, j = pair
                needs_protection_i = protected_count_per_column[i] < min_protected_per_column
                needs_protection_j = protected_count_per_column[j] < min_protected_per_column
                
                if needs_protection_i or needs_protection_j:
                    protected_set.add(pair)
                    protected_pairs.append((pair, importance))
                    protected_count_per_column[i] += 1
                    protected_count_per_column[j] += 1
        
        # CRITICAL FIX: Eligible for disabling = active pairs that are NOT protected
        # This ensures we're selecting from the right set (active + eligible)
        # NOT from all pairs, NOT only pairs with lift, but active pairs excluding protected
        eligible_pairs = [p for p in active_pairs if p not in protected_set]
        
        # DIAGNOSTIC: Log eligible pairs breakdown
        eligible_with_lift = [p for p in eligible_pairs if p in importance_scores]
        eligible_without_lift = [p for p in eligible_pairs if p not in importance_scores]
        logger.info(f"🔪 Pruning eligibility: {len(eligible_pairs)} eligible (active - protected)")
        logger.info(f"   Eligible with lift: {len(eligible_with_lift)}/{len(eligible_pairs)}")
        logger.info(f"   Eligible without lift: {len(eligible_without_lift)}/{len(eligible_pairs)}")
        
        if not eligible_pairs:
            logger.info(f"🔪 Progressive pruning: All {len(active_pairs)} active pairs are protected (below minimum floor)")
            return
        
        # Filter eligible pairs: only allow pruning if n_total >= MIN_SUPPORT_PRUNE
        # CRITICAL: Use n_total = n_ij + n_ji (undirected pair support) for all support gating
        # This is consistent with sparse sampling where individual directions may have low counts
        # but the undirected pair accumulates enough observations across both directions
        prunable_pairs = []
        prunable_with_lift = 0
        prunable_without_lift = 0
        for pair in eligible_pairs:
            i, j = pair
            stats_ij = self._pair_stats.get((i, j), {})
            stats_ji = self._pair_stats.get((j, i), {})
            n_ij = stats_ij.get('n', 0)
            n_ji = stats_ji.get('n', 0)
            n_total = n_ij + n_ji  # Undirected pair support (sum of both directions)
            
            # CRITICAL: Only allow pruning if we have sufficient support (using n_total)
            if n_total >= self.MIN_SUPPORT_PRUNE:
                # Use score if available, otherwise use -inf (lowest priority)
                score = importance_scores.get(pair, float('-inf'))
                prunable_pairs.append((pair, score))
                if pair in importance_scores:
                    prunable_with_lift += 1
                else:
                    prunable_without_lift += 1
            else:
                # Pair doesn't have enough data yet - skip pruning
                continue
        
        # DIAGNOSTIC: Log prunable pairs breakdown
        logger.info(f"🔪 Prunable pairs: {len(prunable_pairs)}/{len(eligible_pairs)} (n_total≥{self.MIN_SUPPORT_PRUNE})")
        logger.info(f"   Prunable with lift: {prunable_with_lift}/{len(prunable_pairs)}")
        logger.info(f"   Prunable without lift: {prunable_without_lift}/{len(prunable_pairs)}")
        
        if not prunable_pairs:
            logger.info(f"🔪 Progressive pruning: No pairs have sufficient support (n_total≥{self.MIN_SUPPORT_PRUNE}) for pruning")
            logger.info(f"   Eligible pairs: {len(eligible_pairs)}, but none meet support threshold")
            # Show why pairs aren't prunable
            insufficient_support = 0
            for pair in eligible_pairs[:10]:  # Check first 10
                i, j = pair
                stats_ij = self._pair_stats.get((i, j), {})
                stats_ji = self._pair_stats.get((j, i), {})
                n_total = stats_ij.get('n', 0) + stats_ji.get('n', 0)
                if n_total < self.MIN_SUPPORT_PRUNE:
                    insufficient_support += 1
            if insufficient_support > 0:
                logger.info(f"   Example: {insufficient_support}/10 checked pairs have n_total < {self.MIN_SUPPORT_PRUNE}")
            return
        
        # Sort prunable pairs by importance (LOWEST = least important = disable first)
        prunable_pairs.sort(key=lambda x: x[1], reverse=False)  # LOWEST first
        
        # Disable the N least important prunable pairs
        # Use aggressive target if lift is flat, otherwise use base count
        num_to_disable = min(num_to_disable_target, len(prunable_pairs))
        newly_disabled = []
        
        for pair, importance in prunable_pairs[:num_to_disable]:
            self.disabled_pairs.add(pair)
            newly_disabled.append((pair, importance))
            
            # Score tracking: -1 when culled (worst performing)
            if pair not in self._pair_scores:
                self._pair_scores[pair] = 0
            self._pair_scores[pair] -= 1
        
        # ============================================================================
        # SWAP: Bring in fresh pairs from disabled pool to maintain exploration
        # ============================================================================
        # CRITICAL: Always reactivate at least K_explore pairs per epoch to maintain exploration
        # This ensures the selector can explore alternatives, not just shrink the graph
        # ============================================================================
        newly_reactivated = []
        
        # Calculate K_explore for this run
        log2_N = np.log2(max(2, self.n_cols))
        E = max(1, min(32, int(np.ceil(log2_N))))
        K_explore = E
        
        # Minimum reactivation: K_explore pairs per epoch (ensures exploration continues)
        # Also reactivate up to num_to_disable to maintain pool size (if we're not at target yet)
        min_reactivate = K_explore
        max_reactivate = max(num_to_disable, min_reactivate)  # At least match what we disabled
        
        if self.disabled_pairs:
            # Exclude the ones we JUST disabled - give them at least one epoch off
            just_disabled_set = set(p for p, _ in newly_disabled)
            reactivation_pool = list(self.disabled_pairs - just_disabled_set)
            
            if reactivation_pool:
                # CRITICAL: Reactivate pairs from disabled pool REGARDLESS of lift status
                # - Pairs without lift (never computed, or lost lift when disabled) are eligible
                # - When reactivated, they become active and will regain lift tracking automatically
                # - Lift tracking resumes when they're selected and computed in future batches
                # - This ensures exploration continues even if lift coverage drops
                
                # Reactivate at least K_explore (if available), up to max_reactivate, but never more than pool size
                # Order matters: first cap to pool size, then enforce minimum (but not above pool)
                num_to_reactivate = min(max_reactivate, len(reactivation_pool))
                num_to_reactivate = max(min(min_reactivate, len(reactivation_pool)), num_to_reactivate)
                
                # Sample randomly from disabled pool (no filtering by lift)
                # CRITICAL: Ensure we don't try to sample more than available
                if num_to_reactivate <= 0:
                    logger.warning(f"⚠️  Cannot reactivate: pool size={len(reactivation_pool)}, min_reactivate={min_reactivate}, max_reactivate={max_reactivate}")
                    pairs_to_reactivate = []
                else:
                    pairs_to_reactivate = random.sample(reactivation_pool, num_to_reactivate)
                
                # Track which reactivated pairs have lift vs don't (for diagnostics)
                reactivated_with_lift = 0
                reactivated_without_lift = 0
                
                for pair in pairs_to_reactivate:
                    self.disabled_pairs.remove(pair)
                    newly_reactivated.append(pair)
                    
                    # Check if pair has lift (for diagnostics)
                    i, j = pair
                    stats_ij = self._pair_stats.get((i, j), {})
                    stats_ji = self._pair_stats.get((j, i), {})
                    has_lift_ij = stats_ij.get('lift_ema') is not None
                    has_lift_ji = stats_ji.get('lift_ema') is not None
                    if has_lift_ij or has_lift_ji:
                        reactivated_with_lift += 1
                    else:
                        reactivated_without_lift += 1
                    
                    # Score tracking: +1 when reactivated (exploration)
                    if pair not in self._pair_scores:
                        self._pair_scores[pair] = 0
                    self._pair_scores[pair] += 1  # Increment for being selected/explored
                
                # Log reactivation diagnostics
                if reactivated_without_lift > 0:
                    logger.info(f"   🔄 Reactivation: {reactivated_without_lift}/{len(pairs_to_reactivate)} pairs without lift (will regain tracking when computed)")
        
        # Log what we disabled
        total_pairs = len(self.all_pairs)
        active_after = total_pairs - len(self.disabled_pairs)
        target_remaining = int(total_pairs * self.top_k_fraction)
        target_remaining = max(target_remaining, self.min_relationships_to_keep)
        
        logger.info("")
        logger.info("🔄" * 40)
        logger.info(f"🔄 RELATIONSHIP SWAP - Epoch {self.current_epoch}")
        logger.info(f"   Strategy: Swap out weak pairs, bring in fresh ones to explore")
        logger.info(f"   Metric: Lift-based importance (EMA of causal lift from NULL baseline)")
        logger.info(f"   Disabled {num_to_disable} relationships (lowest lift = least helpful)")
        logger.info(f"   Reactivated {len(newly_reactivated)} relationships (min {K_explore} for exploration)")
        logger.info(f"   Net change: {len(newly_reactivated) - num_to_disable:+d} active pairs")
        logger.info(f"   Active: {active_after}/{total_pairs} ({100*active_after/total_pairs:.1f}%)")
        logger.info(f"   Protected floor: {len(protected_set)} pairs (per-column, degree-capped, max {max_protected_per_column}/col)")
        logger.info(f"   Target: {target_remaining} pairs ({self.top_k_fraction*100:.0f}%)")
        
        if newly_disabled:
            logger.info(f"")
            logger.info(f"   Newly disabled (worst {len(newly_disabled[:5])} of {len(newly_disabled)}):")
            for pair, importance in newly_disabled[:5]:  # Show first 5
                i, j = pair
                col_i = self.col_names[i] if i < len(self.col_names) else f"col_{i}"
                col_j = self.col_names[j] if j < len(self.col_names) else f"col_{j}"
                # Show lift-based importance (not Δ)
                stats_ij = self._pair_stats.get((i, j), {})
                stats_ji = self._pair_stats.get((j, i), {})
                lift_ij = stats_ij.get('lift_ema', 0.0)
                lift_ji = stats_ji.get('lift_ema', 0.0)
                lift_total = lift_ij + lift_ji
                logger.info(f"      ({col_i} ↔ {col_j}): lift={lift_total:.4f} (i→j={lift_ij:.4f}, j→i={lift_ji:.4f})")
            if len(newly_disabled) > 5:
                logger.info(f"      ... and {len(newly_disabled)-5} more")
        
        # Show reactivated pairs
        if newly_reactivated:
            logger.info(f"")
            logger.info(f"   🔄 Reactivated (random from disabled pool, first {min(5, len(newly_reactivated))} of {len(newly_reactivated)}):")
            logger.info(f"   NOTE: Reactivated pairs will regain lift tracking when computed in future batches")
            for pair in newly_reactivated[:5]:
                i, j = pair
                col_i = self.col_names[i] if i < len(self.col_names) else f"col_{i}"
                col_j = self.col_names[j] if j < len(self.col_names) else f"col_{j}"
                # Check if pair has lift (may have been computed before being disabled)
                stats_ij = self._pair_stats.get((i, j), {})
                stats_ji = self._pair_stats.get((j, i), {})
                has_lift = stats_ij.get('lift_ema') is not None or stats_ji.get('lift_ema') is not None
                lift_status = "has lift" if has_lift else "no lift (will regain when computed)"
                # These pairs haven't been evaluated recently, so no loss info
                prev_score = self._pair_scores.get(pair, 0)
                logger.info(f"      ({col_i} ↔ {col_j}): prev_score={prev_score} [{lift_status}]")
            if len(newly_reactivated) > 5:
                logger.info(f"      ... and {len(newly_reactivated)-5} more")
        
        # Show top 5 protected relationships
        if protected_set:
            logger.info(f"")
            logger.info(f"   Top 5 protected relationships (will NEVER be disabled):")
            for pair, importance in protected_pairs[:5]:
                i, j = pair
                col_i = self.col_names[i] if i < len(self.col_names) else f"col_{i}"
                col_j = self.col_names[j] if j < len(self.col_names) else f"col_{j}"
                # Show lift-based importance (not Δ)
                stats_ij = self._pair_stats.get((i, j), {})
                stats_ji = self._pair_stats.get((j, i), {})
                lift_ij = stats_ij.get('lift_ema', 0.0)
                lift_ji = stats_ji.get('lift_ema', 0.0)
                lift_total = lift_ij + lift_ji
                logger.info(f"      ({col_i} ↔ {col_j}): lift={lift_total:.4f} (i→j={lift_ij:.4f}, j→i={lift_ji:.4f})")
        
        # Log score distribution across ALL pairs (not just active)
        all_scores = list(self._pair_scores.values())
        if all_scores:
            score_mean = np.mean(all_scores)
            score_std = np.std(all_scores) if len(all_scores) > 1 else 0.0
            score_min = np.min(all_scores)
            score_max = np.max(all_scores)
            n_positive = sum(1 for s in all_scores if s > 0)
            n_negative = sum(1 for s in all_scores if s < 0)
            n_zero = sum(1 for s in all_scores if s == 0)
            logger.info(f"")
            logger.info(f"   📈 Cumulative scores across ALL {len(all_scores)} pairs:")
            logger.info(f"      Mean: {score_mean:.2f}  Std: {score_std:.2f}  Range: [{score_min}, {score_max}]")
            logger.info(f"      Positive (kept often): {n_positive}  Negative (culled often): {n_negative}  Zero (neutral): {n_zero}")
        
        # ============================================================================
        # DIAGNOSTIC A: Lift quantiles (to see tail mass shrinking)
        # ============================================================================
        # Get active pairs AFTER pruning (for accurate diagnostics)
        active_pairs_after = [p for p in self.all_pairs if p not in self.disabled_pairs]
        
        active_lift_values = []
        for pair in active_pairs_after:
            i, j = pair
            stats_ij = self._pair_stats.get((i, j), {})
            stats_ji = self._pair_stats.get((j, i), {})
            lift_ij = stats_ij.get('lift_ema')
            lift_ji = stats_ji.get('lift_ema')
            
            # Use total lift if both directions available, otherwise use available one
            if lift_ij is not None and lift_ji is not None:
                lift_total = lift_ij + lift_ji
                if math.isfinite(lift_total):
                    active_lift_values.append(lift_total)
            elif lift_ij is not None and math.isfinite(lift_ij):
                active_lift_values.append(lift_ij)
            elif lift_ji is not None and math.isfinite(lift_ji):
                active_lift_values.append(lift_ji)
        
        if active_lift_values:
            quantiles = np.percentile(active_lift_values, [10, 25, 50, 75, 90])
            logger.info(f"")
            logger.info(f"   📊 Lift quantiles (active pairs, n={len(active_lift_values)}):")
            logger.info(f"      p10: {quantiles[0]:.4f}  p25: {quantiles[1]:.4f}  p50: {quantiles[2]:.4f}  p75: {quantiles[3]:.4f}  p90: {quantiles[4]:.4f}")
        
        # ============================================================================
        # DIAGNOSTIC B: Pruning gain proxy (active_mean - disabled_mean)
        # ============================================================================
        # Compute mean lift of active pairs
        if active_lift_values:
            active_mean_lift = np.mean(active_lift_values)
        else:
            active_mean_lift = None
        
        # Compute mean lift of disabled pairs (if they still have cached lift)
        disabled_lift_values = []
        for pair in self.disabled_pairs:
            i, j = pair
            stats_ij = self._pair_stats.get((i, j), {})
            stats_ji = self._pair_stats.get((j, i), {})
            lift_ij = stats_ij.get('lift_ema')
            lift_ji = stats_ji.get('lift_ema')
            
            # Use total lift if both directions available, otherwise use available one
            if lift_ij is not None and lift_ji is not None:
                lift_total = lift_ij + lift_ji
                if math.isfinite(lift_total):
                    disabled_lift_values.append(lift_total)
            elif lift_ij is not None and math.isfinite(lift_ij):
                disabled_lift_values.append(lift_ij)
            elif lift_ji is not None and math.isfinite(lift_ji):
                disabled_lift_values.append(lift_ji)
        
        if disabled_lift_values:
            disabled_mean_lift = np.mean(disabled_lift_values)
        else:
            disabled_mean_lift = None
        
        # Print pruning gain proxy
        if active_mean_lift is not None and disabled_mean_lift is not None:
            pruning_gap = active_mean_lift - disabled_mean_lift
            logger.info(f"")
            logger.info(f"   🎯 Pruning gain proxy:")
            logger.info(f"      Active mean lift: {active_mean_lift:.4f} (n={len(active_lift_values)})")
            logger.info(f"      Disabled mean lift: {disabled_mean_lift:.4f} (n={len(disabled_lift_values)})")
            logger.info(f"      Gap (active - disabled): {pruning_gap:+.4f} {'✅' if pruning_gap > 0 else '⚠️'}")
        elif active_mean_lift is not None:
            logger.info(f"")
            logger.info(f"   🎯 Pruning gain proxy:")
            logger.info(f"      Active mean lift: {active_mean_lift:.4f} (n={len(active_lift_values)})")
            logger.info(f"      Disabled mean lift: N/A (no cached lift in disabled pairs)")
        elif disabled_mean_lift is not None:
            logger.info(f"")
            logger.info(f"   🎯 Pruning gain proxy:")
            logger.info(f"      Active mean lift: N/A (no lift in active pairs)")
            logger.info(f"      Disabled mean lift: {disabled_mean_lift:.4f} (n={len(disabled_lift_values)})")
        
        logger.info("🔄" * 40)
        logger.info("")
        
        # Score tracking and batch update to monitor
        # Only update pairs that were EVALUATED this epoch (eligible + protected)
        # Don't send all active pairs - only the ones we considered for pruning
        
        # Keeps: Eligible pairs that SURVIVED this pruning (were at risk but kept)
        # These are the pairs that were evaluated and decided to keep for now
        surviving_eligible = [p for p in eligible_pairs if p not in self.disabled_pairs]
        
        # ============================================================================
        # CUMULATIVE SCORE TRACKING: Track selection frequency for UCB/exploration
        # ============================================================================
        # CRITICAL: Increment scores for ALL pairs that are ACTIVE this epoch
        # This ensures "kept often" reflects actual selection frequency, not just
        # "never disabled" (which would be all pairs initially)
        # ============================================================================
        # All pairs that are currently active (after pruning) were selected/kept
        final_active_pairs = [p for p in self.all_pairs if p not in self.disabled_pairs]
        for pair in final_active_pairs:
            if pair not in self._pair_scores:
                self._pair_scores[pair] = 0
            self._pair_scores[pair] += 1  # Increment for being selected/kept this epoch
        
        # Post scores to featrix-monitor if we have a dataset hash
        if self._dataset_hash and (newly_disabled or surviving_eligible):
            try:
                from featrix_monitor import create_client
                client = create_client()
                
                # Build keeps list (eligible pairs that survived this pruning)
                keeps = []
                for pair in surviving_eligible:
                    i, j = pair
                    col_i = self.col_names[i] if i < len(self.col_names) else f"col_{i}"
                    col_j = self.col_names[j] if j < len(self.col_names) else f"col_{j}"
                    keeps.append({
                        "columns": [col_i, col_j],
                        "difficulty_scores": {
                            col_i: self.col_marginal_losses.get(col_i, 0.0),
                            col_j: self.col_marginal_losses.get(col_j, 0.0)
                        },
                        "epoch_idx": self.current_epoch,
                        "metadata": {
                            "session_id": self._session_id or "unknown",
                            "importance": importance_scores.get(pair, 0.0)
                        }
                    })
                
                # Build culls list (pairs that were just disabled)
                culls = []
                for pair, importance in newly_disabled:
                    i, j = pair
                    col_i = self.col_names[i] if i < len(self.col_names) else f"col_{i}"
                    col_j = self.col_names[j] if j < len(self.col_names) else f"col_{j}"
                    culls.append({
                        "columns": [col_i, col_j],
                        "difficulty_scores": {
                            col_i: self.col_marginal_losses.get(col_i, 0.0),
                            col_j: self.col_marginal_losses.get(col_j, 0.0)
                        },
                        "epoch_idx": self.current_epoch,
                        "metadata": {
                            "session_id": self._session_id or "unknown",
                            "importance": importance,
                            "reason": "lowest importance (easiest columns)"
                        }
                    })
                
                # Batch update all at once (async, non-blocking)
                result = client.batch_update_pair_scores(
                    dataset_hash=self._dataset_hash,
                    keeps=keeps,
                    culls=culls
                )
                
                logger.info(f"📊 Batch updated pair scores: {result['keeps_updated']} keeps, {result['culls_updated']} culls")
                if result.get('errors'):
                    logger.warning(f"   ⚠️  {len(result['errors'])} pairs failed to update")
                
            except Exception as e:
                logger.debug(f"Failed to post relationship scores to monitor: {e}")
                # Don't fail training if monitor posting fails
    
    def finalize_training_and_validate(self):
        """
        STAGE 3: Validate importance scoring at end of training.
        
        This validates that our causal importance scores actually predict
        which pairs help vs hurt. Reports:
        - Rank correlation (high importance → high actual lift?)
        - Top 20% pairs: Do they actually help? (mean lift > 0)
        - Bottom 20% pairs: Do they hurt/neutral? (mean lift ≤ 0)
        - False positives: High importance but negative lift
        - False negatives: Low importance but positive lift
        
        This is FREE validation - uses data we're already tracking.
        """
        logger.info("")
        logger.info("="*80)
        logger.info("🔍 VALIDATING IMPORTANCE SCORING")
        logger.info("="*80)
        
        try:
            # Get final importance scores
            importance_scores = self._compute_relationship_importance()
            
            # Validate against actual observed lift
            report = self.validator.validate_importance_scoring(importance_scores)
            
            # Print detailed report
            self.validator.print_validation_report(report)
            
            # Save to file for analysis
            try:
                import json
                import os
                
                validation_path = 'importance_validation.json'
                with open(validation_path, 'w') as f:
                    json.dump({
                        'grade': report.grade(),
                        'valid': report.is_valid(),
                        'rank_correlation': report.rank_correlation,
                        'rank_correlation_pvalue': report.rank_correlation_pvalue,
                        'top_20_mean_lift': report.top_20_mean_lift,
                        'top_20_pct_positive': report.top_20_pct_positive,
                        'bottom_20_mean_lift': report.bottom_20_mean_lift,
                        'bottom_20_pct_positive': report.bottom_20_pct_positive,
                        'n_false_positives': len(report.false_positives),
                        'n_false_negatives': len(report.false_negatives),
                        'n_pairs_total': report.n_pairs_total,
                    }, f, indent=2)
                
                logger.info(f"📄 Validation report saved to: {validation_path}")
            except Exception as e:
                logger.warning(f"Failed to save validation report: {e}")
            
            # Return validation result
            return report
            
        except Exception as e:
            logger.error(f"❌ Validation failed: {e}")
            import traceback
            traceback.print_exc()
            return None

    def __getstate__(self):
        """
        Custom pickle state - save all instance attributes that aren't automatically saved by nn.Module.
        nn.Module's default __getstate__ only saves parameters and buffers, not regular instance attributes.

        Clear temporary tensors that may be part of autograd graph to avoid deepcopy errors.
        """
        # Get the default state (parameters, buffers, etc.)
        state = self.__dict__.copy()

        # Clear temporary tensors that may be part of computation graph
        # These are populated during forward pass and fail deepcopy
        state['_tokens_for_gradient_check'] = []

        return state
    
    def __setstate__(self, state):
        """
        Custom unpickle state - restore all instance attributes.
        After restoring, ensure any missing attributes are initialized for backward compatibility.
        """
        # Restore all attributes
        self.__dict__.update(state)

        # Ensure all required attributes are initialized (for backward compatibility)
        # This handles cases where old checkpoints don't have newer attributes
        self._ensure_pair_stats_attributes()
        self._ensure_null_baseline_attributes()

        # Ensure type_aware_config exists (for old checkpoints without it)
        if not hasattr(self, 'type_aware_config') or self.type_aware_config is None:
            from featrix.neural.type_aware_ops_config import TypeAwareOpsConfig
            self.type_aware_config = TypeAwareOpsConfig.from_env()

        # Ensure email/domain ops attributes exist (for old checkpoints)
        if not hasattr(self, 'email_domain_ops'):
            self.email_domain_ops = None
        if not hasattr(self, 'email_domain_set_ops'):
            self.email_domain_set_ops = None
        if not hasattr(self, 'email_domain_scalar_ops'):
            self.email_domain_scalar_ops = None
        if not hasattr(self, 'email_domain_timestamp_ops'):
            self.email_domain_timestamp_ops = None
        if not hasattr(self, 'email_domain_string_ops'):
            self.email_domain_string_ops = None

        # Ensure _type_aware_stats has all required keys (for old checkpoints)
        if not hasattr(self, '_type_aware_stats'):
            self._type_aware_stats = {}
        default_stats = {
            'set_timestamp_pairs': 0,
            'scalar_timestamp_pairs': 0,
            'set_set_pairs': 0,
            'set_scalar_pairs': 0,
            'scalar_scalar_pairs': 0,
            'email_domain_pairs': 0,
            'email_domain_set_pairs': 0,
            'email_domain_scalar_pairs': 0,
            'email_domain_timestamp_pairs': 0,
            'email_domain_string_pairs': 0,
            'url_set_pairs': 0,
            'url_scalar_pairs': 0,
            'url_timestamp_pairs': 0,
            'url_string_pairs': 0,
            'generic_pairs': 0,
            'total_forward_calls': 0,
        }
        for key, val in default_stats.items():
            if key not in self._type_aware_stats:
                self._type_aware_stats[key] = val

