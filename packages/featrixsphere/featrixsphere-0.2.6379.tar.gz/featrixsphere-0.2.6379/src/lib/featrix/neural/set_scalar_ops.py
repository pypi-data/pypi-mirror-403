#  -*- coding: utf-8 -*-
#
#  Copyright Featrix, Inc 2023-2025
#
#  Proprietary and Confidential. Unauthorized use, copying or dissemination
#  of these materials is strictly prohibited.
"""
Set × Scalar Relationship Operations

Type-aware relationship operations for Set × Scalar column pairs.
Learns associations like:
- "category='luxury' has mean_price 5x higher"
- "status='churned' correlates with low engagement_score"
- "region='urban' has higher population_density"

Features:
1. Scalar-Conditioned Set Gating - use scalar to gate set embedding
2. Set-Conditioned Scalar Scaling - use set to scale scalar embedding
3. Magnitude Context - encode relative magnitude for this set value
"""
import logging
import torch
import torch.nn as nn
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from featrix.neural.type_aware_ops_config import TypeAwareOpsConfig

logger = logging.getLogger(__name__)


class SetScalarOps(nn.Module):
    """
    Type-aware operations for Set × Scalar column pairs.

    Computes relationship embeddings that capture how categorical values
    correlate with numeric values:
    - What's the typical scalar value for each category?
    - How does the category modulate the scalar interpretation?
    - Are there categories associated with extreme values?
    """

    def __init__(
        self,
        d_model: int,
        config: Optional["TypeAwareOpsConfig"] = None,
    ):
        """
        Args:
            d_model: Model dimension
            config: TypeAwareOpsConfig for granular feature control
        """
        super().__init__()
        self.d_model = d_model
        self.config = config

        # ============================================================================
        # Feature 1: Scalar-Conditioned Set Gating
        # ============================================================================
        # Use scalar to gate/modulate the set embedding
        self.scalar_gate_mlp = nn.Sequential(
            nn.Linear(d_model, d_model // 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model // 2, d_model),
        )

        # ============================================================================
        # Feature 2: Set-Conditioned Scalar Scaling
        # ============================================================================
        # Use set to scale/transform the scalar embedding
        self.set_scale_mlp = nn.Sequential(
            nn.Linear(d_model, d_model // 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model // 2, d_model),
        )

        # ============================================================================
        # Feature 3: Magnitude Context
        # ============================================================================
        # Learn a "relative magnitude" embedding that captures how the scalar
        # relates to typical values for this set category
        self.magnitude_mlp = nn.Sequential(
            nn.Linear(d_model * 2, d_model),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model, d_model),
        )

        # ============================================================================
        # Feature 4: Interaction MLP
        # ============================================================================
        # Additional learned interaction between set and scalar
        self.interaction_mlp = nn.Sequential(
            nn.Linear(d_model * 3, d_model),  # concat + product
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model, d_model),
        )

        # ============================================================================
        # Fusion: Combine all features
        # ============================================================================
        # Input: gated_set + scaled_scalar + magnitude + interaction + symmetric = 5 * d_model
        self.fusion_mlp = nn.Sequential(
            nn.Linear(5 * d_model, d_model * 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model * 2, d_model),
        )

        # Output normalization to stabilize training
        self.output_norm = nn.LayerNorm(d_model)

        logger.debug(f"   SetScalarOps initialized: d_model={d_model}")

    def forward(
        self,
        set_embedding: torch.Tensor,    # (batch, d_model) - encoded set column
        scalar_embedding: torch.Tensor,  # (batch, d_model) - encoded scalar column
    ) -> torch.Tensor:
        """
        Compute relationship embedding for Set × Scalar pair.

        Args:
            set_embedding: Embedding from SetEncoder (batch, d_model)
            scalar_embedding: Embedding from ScalarEncoder (batch, d_model)

        Returns:
            Relationship embedding of shape (batch, d_model)
        """
        # ============================================================================
        # Feature 1: Scalar-Conditioned Set Gating
        # ============================================================================
        # The scalar value gates which aspects of the set embedding are relevant
        scalar_gate = torch.sigmoid(self.scalar_gate_mlp(scalar_embedding))  # (batch, d_model)
        gated_set = set_embedding * scalar_gate

        # ============================================================================
        # Feature 2: Set-Conditioned Scalar Scaling
        # ============================================================================
        # The set category determines how to interpret/scale the scalar
        set_scale = self.set_scale_mlp(set_embedding)  # (batch, d_model)
        scaled_scalar = scalar_embedding * set_scale

        # ============================================================================
        # Feature 3: Magnitude Context
        # ============================================================================
        # Encode the relative relationship between set and scalar
        magnitude_context = self.magnitude_mlp(
            torch.cat([set_embedding, scalar_embedding], dim=-1)
        )

        # ============================================================================
        # Feature 4: Interaction
        # ============================================================================
        # Concatenate both embeddings and their product
        interaction_input = torch.cat([
            set_embedding,
            scalar_embedding,
            set_embedding * scalar_embedding,
        ], dim=-1)
        interaction = self.interaction_mlp(interaction_input)

        # ============================================================================
        # Feature 5: Symmetric (element-wise product)
        # ============================================================================
        symmetric = set_embedding * scalar_embedding

        # ============================================================================
        # Fusion: Combine all features
        # ============================================================================
        combined = torch.cat([
            gated_set,
            scaled_scalar,
            magnitude_context,
            interaction,
            symmetric,
        ], dim=-1)  # (batch, 5 * d_model)

        return self.output_norm(self.fusion_mlp(combined))
