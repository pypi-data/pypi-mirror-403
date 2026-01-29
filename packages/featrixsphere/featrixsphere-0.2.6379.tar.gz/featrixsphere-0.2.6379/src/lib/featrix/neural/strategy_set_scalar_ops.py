#  -*- coding: utf-8 -*-
#
#  Copyright Featrix, Inc 2023-2025
#
#  Proprietary and Confidential. Unauthorized use, copying or dissemination
#  of these materials is strictly prohibited.
"""
Strategy-Aware Set × Scalar Relationship Operations

Learns which encoding strategy combination produces the best relationship signal
for set-scalar pairs. Instead of using blended embeddings for relationship
computation, this module:

1. Receives component encodings for set column (LEARNED, SEMANTIC, ORDINAL)
2. Receives all 20 strategy encodings for scalar column (LOG, ROBUST, etc.)
3. Learns a (3 × 20) score matrix for strategy pair preferences
4. Selects top-K combinations and computes relationships for each
5. Returns weighted blend of top-K relationship embeddings

Enable via SphereConfig:
    config.set("use_strategy_aware_relationships", True)
"""
import logging
from typing import List, Optional, Tuple, TYPE_CHECKING

import torch
import torch.nn as nn
import torch.nn.functional as F

if TYPE_CHECKING:
    from featrix.neural.type_aware_ops_config import TypeAwareOpsConfig

logger = logging.getLogger(__name__)


# Set encoder component names
SET_COMPONENT_NAMES = ['LEARNED', 'SEMANTIC', 'ORDINAL']
N_SET_COMPONENTS = 3

# Scalar encoder strategies (matches AdaptiveScalarEncoder)
N_SCALAR_STRATEGIES = 20


class StrategyAwareSetScalarOps(nn.Module):
    """
    Encoding-strategy-aware relationship features for set × scalar pairs.

    Instead of computing relationships on blended embeddings, learns which
    component/strategy combinations produce the best relationships.

    The key insight is that:
    - LEARNED embeddings might correlate differently with scalar encodings
    - SEMANTIC (BERT) embeddings capture meaning that might relate to LOG/ROBUST
    - ORDINAL embeddings (for ordered sets like "low/med/high") might best
      correlate with specific scalar encodings

    Architecture:
    1. Score matrix (3×20) learned globally across all set-scalar pairs
    2. At forward: select top-K combinations by score
    3. Compute relationships only for K combinations
    4. Blend with softmax-normalized scores
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
            top_k: Number of component/strategy combinations to evaluate
            config: TypeAwareOpsConfig for feature control
        """
        super().__init__()
        self.d_model = d_model
        self.top_k = top_k
        self.config = config

        # Learnable score matrix: score[i,j] = quality of (set_component_i, scalar_strategy_j)
        # Initialize with small random noise, slight bias toward LEARNED×diagonal
        init_scores = torch.randn(N_SET_COMPONENTS, N_SCALAR_STRATEGIES) * 0.1
        # Give slight preference to SEMANTIC component (often captures useful structure)
        init_scores[1, :] += 0.2
        self.strategy_pair_scores = nn.Parameter(init_scores)

        # Temperature for softmax over top-K scores
        self.score_temperature = nn.Parameter(torch.tensor(1.0))

        # ============================================================================
        # Relationship computation (for set × scalar relationships)
        # ============================================================================

        # Cross-modal interaction: set embedding × scalar embedding
        self.cross_modal_mlp = nn.Sequential(
            nn.Linear(3 * d_model, d_model),  # [set, scalar, set*scalar]
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model, d_model),
        )

        # Gating: learn how much of scalar to condition on set
        self.gating_mlp = nn.Sequential(
            nn.Linear(2 * d_model, d_model),  # [set, scalar]
            nn.Sigmoid(),  # Gate values in [0, 1]
        )

        # Fusion layer
        self.fusion_mlp = nn.Sequential(
            nn.Linear(3 * d_model, d_model * 2),  # [cross_modal, gated, product]
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model * 2, d_model),
        )

        # Output normalization
        self.output_norm = nn.LayerNorm(d_model)

        # Debug counter
        self._debug_count = 0

        logger.debug(f"   StrategyAwareSetScalarOps initialized: d_model={d_model}, top_k={top_k}")

    def _compute_relationship(
        self,
        set_emb: torch.Tensor,    # (batch, d_model)
        scalar_emb: torch.Tensor,  # (batch, d_model)
    ) -> torch.Tensor:
        """
        Compute relationship embedding for a single component/strategy combination.

        Args:
            set_emb: Component encoding for set column (batch, d_model)
            scalar_emb: Strategy encoding for scalar column (batch, d_model)

        Returns:
            Relationship embedding (batch, d_model)
        """
        # Feature 1: Cross-modal interaction
        product = set_emb * scalar_emb
        cross_input = torch.cat([set_emb, scalar_emb, product], dim=-1)
        cross_features = self.cross_modal_mlp(cross_input)

        # Feature 2: Set-conditioned scalar gating
        gate_input = torch.cat([set_emb, scalar_emb], dim=-1)
        gate = self.gating_mlp(gate_input)
        gated_scalar = gate * scalar_emb

        # Feature 3: Simple product (symmetric)
        symmetric = set_emb * scalar_emb

        # Fusion
        combined = torch.cat([cross_features, gated_scalar, symmetric], dim=-1)
        output = self.output_norm(self.fusion_mlp(combined))

        return output

    def forward(
        self,
        set_component_encodings: torch.Tensor,     # (batch, 3, d_model)
        scalar_strategy_encodings: torch.Tensor,   # (batch, 20, d_model)
        set_component_mask: Optional[torch.Tensor] = None,    # (3,) active mask
        scalar_strategy_mask: Optional[torch.Tensor] = None,  # (20,) active mask
    ) -> torch.Tensor:
        """
        Compute strategy-aware relationship embedding for set × scalar pair.

        Args:
            set_component_encodings: All component encodings for set column
            scalar_strategy_encodings: All 20 strategy encodings for scalar column
            set_component_mask: Optional mask of active components for set
            scalar_strategy_mask: Optional mask of active strategies for scalar

        Returns:
            Relationship embedding of shape (batch, d_model)
        """
        batch_size = set_component_encodings.shape[0]
        n_set = set_component_encodings.shape[1]
        device = set_component_encodings.device

        # Apply masks if provided
        scores = self.strategy_pair_scores[:n_set, :].clone()
        if set_component_mask is not None:
            scores = scores * set_component_mask[:n_set].unsqueeze(1).to(device)
        if scalar_strategy_mask is not None:
            scores = scores * scalar_strategy_mask.unsqueeze(0).to(device)

        # Select top-K combinations by score
        flat_scores = scores.view(-1)
        topk_values, topk_indices = torch.topk(flat_scores, min(self.top_k, flat_scores.numel()))

        # Convert flat indices to (i, j) pairs
        n_scalar = N_SCALAR_STRATEGIES
        topk_i = topk_indices // n_scalar  # Set component indices
        topk_j = topk_indices % n_scalar   # Scalar strategy indices

        # Compute softmax weights over top-K scores
        temperature = self.score_temperature.clamp(min=0.1)
        weights = F.softmax(topk_values / temperature, dim=0)

        # Compute relationship for each top-K combination and accumulate
        output = torch.zeros(batch_size, self.d_model, device=device)

        for k in range(len(topk_indices)):
            comp_set_idx = topk_i[k].item()
            strat_scalar_idx = topk_j[k].item()

            # Get encodings
            set_emb = set_component_encodings[:, comp_set_idx, :]
            scalar_emb = scalar_strategy_encodings[:, strat_scalar_idx, :]

            # Compute relationship
            rel_emb = self._compute_relationship(set_emb, scalar_emb)

            # Accumulate weighted contribution
            output = output + weights[k] * rel_emb

        # Debug logging (first few calls)
        self._debug_count += 1
        if self._debug_count <= 3:
            with torch.no_grad():
                top_pairs = self.get_top_strategy_pairs(3)
                pairs_str = ", ".join([f"{a}×{b}={s:.2f}" for a, b, s in top_pairs])
                logger.info(f"🔬 StrategyAwareSetScalarOps forward #{self._debug_count}:")
                logger.info(f"   Top component×strategy pairs: {pairs_str}")
                logger.info(f"   Temperature: {temperature.item():.3f}")

        return output

    def get_top_strategy_pairs(self, k: int = 10) -> List[Tuple[str, str, float]]:
        """Return top-K component×strategy combinations by learned score."""
        with torch.no_grad():
            scores = self.strategy_pair_scores.cpu()
            flat = scores.view(-1)
            topk_vals, topk_idx = torch.topk(flat, min(k, flat.numel()))

            results = []
            for val, idx in zip(topk_vals, topk_idx):
                i, j = idx.item() // N_SCALAR_STRATEGIES, idx.item() % N_SCALAR_STRATEGIES
                set_name = SET_COMPONENT_NAMES[i] if i < len(SET_COMPONENT_NAMES) else f"SET{i}"
                # Import scalar strategy names
                try:
                    from featrix.neural.strategy_scalar_scalar_ops import STRATEGY_NAMES
                    scalar_name = STRATEGY_NAMES[j]
                except:
                    scalar_name = f"SCALAR{j}"
                results.append((set_name, scalar_name, val.item()))
            return results
