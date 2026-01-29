#  -*- coding: utf-8 -*-
#
#  Copyright Featrix, Inc 2023-2025
#
#  Proprietary and Confidential. Unauthorized use, copying or dissemination
#  of these materials is strictly prohibited.
"""
Strategy-Aware Scalar × Scalar Relationship Operations

Learns which encoding strategy combination produces the best relationship signal
for each scalar-scalar pair. Instead of using blended embeddings for relationship
computation, this module:

1. Receives all 20 strategy encodings for each scalar column
2. Learns a (20, 20) score matrix for strategy pair preferences
3. Selects top-K combinations and computes relationships for each
4. Returns weighted blend of top-K relationship embeddings

This allows the model to learn:
- "Price/Quantity ratio works best with LOG encoding"
- "Age-Income relationship works best with ROBUST encoding"

Enable via SphereConfig:
    config.set("use_strategy_aware_relationships", True)

Or via environment variable:
    FEATRIX_STRATEGY_AWARE_RELATIONSHIPS=1
"""
import logging
import math
from typing import List, Optional, Tuple, TYPE_CHECKING

import torch
import torch.nn as nn
import torch.nn.functional as F

if TYPE_CHECKING:
    from featrix.neural.type_aware_ops_config import TypeAwareOpsConfig

logger = logging.getLogger(__name__)


# Strategy names in order (matches AdaptiveScalarEncoder encoding order)
STRATEGY_NAMES = [
    'linear', 'log', 'robust', 'rank', 'periodic', 'bucket',
    'is_positive', 'is_negative', 'is_outlier', 'zscore', 'minmax',
    'quantile', 'yeojohnson', 'winsor', 'sigmoid', 'inverse',
    'polynomial', 'frequency', 'target_bin', 'clipped_log'
]
N_STRATEGIES = 20


class StrategyAwareScalarScalarOps(nn.Module):
    """
    Encoding-strategy-aware relationship features for scalar pairs.

    Instead of computing relationships on blended embeddings, learns which
    strategy combinations produce the best relationships for each pair.

    Architecture:
    1. Score matrix (20x20) learned globally across all scalar-scalar pairs
    2. At forward: select top-K combinations by score
    3. Compute relationships only for K combinations (using standard ScalarScalarOps logic)
    4. Blend with softmax-normalized scores

    This is ~K× more expensive per scalar-scalar pair than the original approach,
    but since scalar-scalar pairs are limited (default: max 15), the total impact
    is manageable.
    """

    def __init__(
        self,
        d_model: int,
        top_k: int = 4,
        config: Optional["TypeAwareOpsConfig"] = None,
    ):
        """
        Args:
            d_model: Model embedding dimension
            top_k: Number of strategy combinations to evaluate per relationship
            config: TypeAwareOpsConfig for feature control
        """
        super().__init__()
        self.d_model = d_model
        self.top_k = top_k
        self.config = config

        # Learnable score matrix: score[i,j] = quality of (strategy_i for A, strategy_j for B)
        # Initialize with:
        # - Small random noise for symmetry breaking
        # - Diagonal bias: same strategy for both columns often works well
        init_scores = torch.randn(N_STRATEGIES, N_STRATEGIES) * 0.1
        init_scores += torch.eye(N_STRATEGIES) * 0.5  # Diagonal bonus
        self.strategy_pair_scores = nn.Parameter(init_scores)

        # Temperature for softmax over top-K scores
        # Learnable but starts at 1.0, will become sharper or softer with training
        self.score_temperature = nn.Parameter(torch.tensor(1.0))

        # Learned epsilon for safe division (same as ScalarScalarOps)
        self.register_buffer('epsilon', torch.tensor(0.1))

        # ============================================================================
        # Relationship computation MLPs (same architecture as ScalarScalarOps)
        # Shared across all strategy combinations for efficiency
        # ============================================================================

        # Feature 1: Ratio Encoding
        # Input: ratio_ab, ratio_ba, log_ratio (3 * d_model)
        self.ratio_mlp = nn.Sequential(
            nn.Linear(3 * d_model, d_model),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model, d_model),
        )

        # Feature 2: Relative Magnitude
        # Input: diff, abs_diff, sign_diff (3 * d_model)
        self.relative_mlp = nn.Sequential(
            nn.Linear(3 * d_model, d_model),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model, d_model),
        )

        # Feature 3: Correlation Hint
        # Input: product, anti_product (2 * d_model)
        self.correlation_mlp = nn.Sequential(
            nn.Linear(2 * d_model, d_model),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model, d_model),
        )

        # Feature 4: Quadratic Interaction
        # Input: a², b², a*b (3 * d_model)
        self.quadratic_mlp = nn.Sequential(
            nn.Linear(3 * d_model, d_model),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model, d_model),
        )

        # Fusion: Combine all features
        # Input: ratio + relative + correlation + quadratic + symmetric (5 * d_model)
        self.fusion_mlp = nn.Sequential(
            nn.Linear(5 * d_model, d_model * 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model * 2, d_model),
        )

        # Output normalization to stabilize training
        self.output_norm = nn.LayerNorm(d_model)

        # Debug counter
        self._debug_count = 0

        logger.debug(f"   StrategyAwareScalarScalarOps initialized: d_model={d_model}, top_k={top_k}")

    def _safe_divide(self, numerator: torch.Tensor, denominator: torch.Tensor) -> torch.Tensor:
        """Safe division with learned epsilon to prevent explosion."""
        sign = torch.sign(denominator)
        sign = torch.where(sign == 0, torch.ones_like(sign), sign)
        safe_denom = sign * (torch.abs(denominator) + self.epsilon)
        return numerator / safe_denom

    def _compute_relationship(
        self,
        emb_a: torch.Tensor,  # (batch, d_model)
        emb_b: torch.Tensor,  # (batch, d_model)
    ) -> torch.Tensor:
        """
        Compute relationship embedding for a single strategy combination.

        This is the same computation as ScalarScalarOps but without the config checks
        since we're always computing all features.

        Args:
            emb_a: Strategy encoding for column A (batch, d_model)
            emb_b: Strategy encoding for column B (batch, d_model)

        Returns:
            Relationship embedding (batch, d_model)
        """
        # Feature 1: Ratio Encoding
        ratio_ab = self._safe_divide(emb_a, emb_b)
        ratio_ba = self._safe_divide(emb_b, emb_a)
        log_ratio = torch.sign(ratio_ab) * torch.log1p(torch.abs(ratio_ab))
        ratio_input = torch.cat([ratio_ab, ratio_ba, log_ratio], dim=-1)
        ratio_features = self.ratio_mlp(ratio_input)

        # Feature 2: Relative Magnitude
        diff = emb_a - emb_b
        abs_diff = torch.abs(diff)
        sign_diff = torch.sign(diff)
        relative_input = torch.cat([diff, abs_diff, sign_diff], dim=-1)
        relative_features = self.relative_mlp(relative_input)

        # Feature 3: Correlation Hint
        product = emb_a * emb_b
        anti_product = emb_a * (-emb_b)
        correlation_input = torch.cat([product, anti_product], dim=-1)
        correlation_features = self.correlation_mlp(correlation_input)

        # Feature 4: Quadratic Interaction
        a_squared = emb_a * emb_a
        b_squared = emb_b * emb_b
        a_times_b = emb_a * emb_b
        quadratic_input = torch.cat([a_squared, b_squared, a_times_b], dim=-1)
        quadratic_features = self.quadratic_mlp(quadratic_input)

        # Feature 5: Symmetric (element-wise product)
        symmetric = emb_a * emb_b

        # Fusion
        combined = torch.cat([
            ratio_features,
            relative_features,
            correlation_features,
            quadratic_features,
            symmetric,
        ], dim=-1)  # (batch, 5 * d_model)

        output = self.output_norm(self.fusion_mlp(combined))
        return output

    def forward(
        self,
        strategy_encodings_a: torch.Tensor,  # (batch, 20, d_model)
        strategy_encodings_b: torch.Tensor,  # (batch, 20, d_model)
        strategy_mask_a: Optional[torch.Tensor] = None,  # (20,) active strategy mask
        strategy_mask_b: Optional[torch.Tensor] = None,  # (20,) active strategy mask
    ) -> torch.Tensor:
        """
        Compute strategy-aware relationship embedding.

        Args:
            strategy_encodings_a: All 20 strategy encodings for column A (batch, 20, d_model)
            strategy_encodings_b: All 20 strategy encodings for column B (batch, 20, d_model)
            strategy_mask_a: Optional mask of active strategies for A (from pruning)
            strategy_mask_b: Optional mask of active strategies for B (from pruning)

        Returns:
            Relationship embedding of shape (batch, d_model)
        """
        batch_size = strategy_encodings_a.shape[0]
        device = strategy_encodings_a.device

        # Apply strategy masks if provided (zero out pruned strategies in score matrix)
        scores = self.strategy_pair_scores.clone()
        if strategy_mask_a is not None:
            # Zero out rows for pruned source strategies
            scores = scores * strategy_mask_a.unsqueeze(1).to(device)
        if strategy_mask_b is not None:
            # Zero out columns for pruned target strategies
            scores = scores * strategy_mask_b.unsqueeze(0).to(device)

        # Select top-K strategy combinations by score
        flat_scores = scores.view(-1)  # (400,)
        topk_values, topk_indices = torch.topk(flat_scores, min(self.top_k, flat_scores.numel()))

        # Convert flat indices to (i, j) pairs
        topk_i = topk_indices // N_STRATEGIES  # Source strategy indices
        topk_j = topk_indices % N_STRATEGIES   # Target strategy indices

        # Compute softmax weights over top-K scores
        # Clamp temperature to avoid division by zero
        temperature = self.score_temperature.clamp(min=0.1)
        weights = F.softmax(topk_values / temperature, dim=0)  # (top_k,)

        # Compute relationship for each top-K combination and accumulate weighted sum
        output = torch.zeros(batch_size, self.d_model, device=device)

        for k in range(len(topk_indices)):
            strat_a_idx = topk_i[k].item()
            strat_b_idx = topk_j[k].item()

            # Get strategy encodings
            emb_a = strategy_encodings_a[:, strat_a_idx, :]  # (batch, d_model)
            emb_b = strategy_encodings_b[:, strat_b_idx, :]  # (batch, d_model)

            # Compute relationship
            rel_emb = self._compute_relationship(emb_a, emb_b)

            # Accumulate weighted contribution
            output = output + weights[k] * rel_emb

        # Debug logging (first few calls)
        self._debug_count += 1
        if self._debug_count <= 3:
            with torch.no_grad():
                top_pairs = self.get_top_strategy_pairs(3)
                pairs_str = ", ".join([f"{a}×{b}={s:.2f}" for a, b, s in top_pairs])
                logger.info(f"🔬 StrategyAwareScalarScalarOps forward #{self._debug_count}:")
                logger.info(f"   Top strategy pairs: {pairs_str}")
                logger.info(f"   Temperature: {temperature.item():.3f}")
                logger.info(f"   Output norm: {output.norm(dim=-1).mean():.3f}")

        return output

    def get_top_strategy_pairs(self, k: int = 10) -> List[Tuple[str, str, float]]:
        """
        Return top-K strategy combinations by learned score (for debugging/logging).

        Args:
            k: Number of top pairs to return

        Returns:
            List of (strategy_a_name, strategy_b_name, score) tuples
        """
        with torch.no_grad():
            scores = self.strategy_pair_scores.cpu()
            flat = scores.view(-1)
            topk_vals, topk_idx = torch.topk(flat, min(k, flat.numel()))

            results = []
            for val, idx in zip(topk_vals, topk_idx):
                i, j = idx.item() // N_STRATEGIES, idx.item() % N_STRATEGIES
                results.append((
                    STRATEGY_NAMES[i],
                    STRATEGY_NAMES[j],
                    val.item()
                ))
            return results

    def get_strategy_scores_matrix(self) -> torch.Tensor:
        """Return the full strategy pair scores matrix for visualization."""
        return self.strategy_pair_scores.detach().cpu()

    def log_strategy_preferences(self) -> None:
        """Log current strategy pair preferences for debugging."""
        top_pairs = self.get_top_strategy_pairs(10)
        logger.info("=" * 60)
        logger.info("STRATEGY-AWARE SCALAR-SCALAR OPS: Learned Preferences")
        logger.info("-" * 60)
        logger.info(f"Temperature: {self.score_temperature.item():.3f}")
        logger.info(f"Top {len(top_pairs)} strategy pairs:")
        for i, (strat_a, strat_b, score) in enumerate(top_pairs, 1):
            logger.info(f"  {i:2d}. {strat_a:12s} × {strat_b:12s} = {score:+.3f}")
        logger.info("=" * 60)
