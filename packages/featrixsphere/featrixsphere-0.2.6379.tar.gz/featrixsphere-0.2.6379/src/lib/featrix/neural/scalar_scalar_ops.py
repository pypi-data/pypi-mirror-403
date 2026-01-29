#  -*- coding: utf-8 -*-
#
#  Copyright Featrix, Inc 2023-2025
#
#  Proprietary and Confidential. Unauthorized use, copying or dissemination
#  of these materials is strictly prohibited.
"""
Scalar × Scalar Enhanced Relationship Operations

Type-aware relationship operations for Scalar × Scalar column pairs.
Extends the generic ×, +, −, / operations with semantic features:
- Ratio encoding (A/B meaningful, e.g., price/quantity = unit_price)
- Relative magnitude (which is larger, by how much)
- Correlation hints (positive/negative correlation patterns)

Features:
1. Ratio Encoding - safe ratio with learned epsilon
2. Relative Magnitude - signed difference and relative scale
3. Correlation Hint - capture positive and negative correlations
"""
import logging
import torch
import torch.nn as nn
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from featrix.neural.type_aware_ops_config import TypeAwareOpsConfig

logger = logging.getLogger(__name__)


class ScalarScalarOps(nn.Module):
    """
    Enhanced operations for Scalar × Scalar column pairs.

    Goes beyond generic ×, +, −, / to capture:
    - Meaningful ratios (unit prices, rates, percentages)
    - Relative comparisons (which is larger, by how much)
    - Correlation patterns (do they move together or opposite)
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

        # Learned epsilon for safe division (starts small, can be adjusted)
        self.register_buffer('epsilon', torch.tensor(0.1))

        # ============================================================================
        # Feature 1: Ratio Encoding
        # ============================================================================
        # Input: ratio_ab, ratio_ba, log_ratio (3 values per d_model dimension)
        # We compute ratios element-wise on embeddings, so input is 3 * d_model
        self.ratio_mlp = nn.Sequential(
            nn.Linear(3 * d_model, d_model),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model, d_model),
        )

        # ============================================================================
        # Feature 2: Relative Magnitude
        # ============================================================================
        # Captures: which is larger, by how much (absolute and signed)
        # Input: diff (a-b), abs_diff, sign = 3 * d_model
        self.relative_mlp = nn.Sequential(
            nn.Linear(3 * d_model, d_model),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model, d_model),
        )

        # ============================================================================
        # Feature 3: Correlation Hint
        # ============================================================================
        # Multiplicative interaction captures positive correlation
        # We also capture negative correlation with anti-product
        # Input: product (a*b), anti_product (a*-b) = 2 * d_model
        self.correlation_mlp = nn.Sequential(
            nn.Linear(2 * d_model, d_model),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model, d_model),
        )

        # ============================================================================
        # Feature 4: Quadratic Interaction
        # ============================================================================
        # Capture non-linear relationships: a², b², a*b
        self.quadratic_mlp = nn.Sequential(
            nn.Linear(3 * d_model, d_model),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model, d_model),
        )

        # ============================================================================
        # Fusion: Combine all features
        # ============================================================================
        # Input: ratio + relative + correlation + quadratic + symmetric = 5 * d_model
        self.fusion_mlp = nn.Sequential(
            nn.Linear(5 * d_model, d_model * 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model * 2, d_model),
        )

        # Output normalization to stabilize training
        self.output_norm = nn.LayerNorm(d_model)

        logger.debug(f"   ScalarScalarOps initialized: d_model={d_model}")

    def _safe_divide(self, numerator: torch.Tensor, denominator: torch.Tensor) -> torch.Tensor:
        """
        Safe division with learned epsilon to prevent explosion.

        Uses sign-preserving epsilon: sign(x) * (|x| + eps) ensures
        denominator is always at least eps from zero.
        """
        sign = torch.sign(denominator)
        sign = torch.where(sign == 0, torch.ones_like(sign), sign)
        safe_denom = sign * (torch.abs(denominator) + self.epsilon)
        return numerator / safe_denom

    def forward(
        self,
        scalar_a_embedding: torch.Tensor,  # (batch, d_model) - encoded scalar column A
        scalar_b_embedding: torch.Tensor,  # (batch, d_model) - encoded scalar column B
    ) -> torch.Tensor:
        """
        Compute enhanced relationship embedding for Scalar × Scalar pair.

        Args:
            scalar_a_embedding: Embedding from ScalarEncoder for column A (batch, d_model)
            scalar_b_embedding: Embedding from ScalarEncoder for column B (batch, d_model)

        Returns:
            Relationship embedding of shape (batch, d_model)
        """
        # Check config for which features to compute
        use_ratio = self.config is None or self.config.enable_ratio_encoding

        # ============================================================================
        # Feature 1: Ratio Encoding
        # ============================================================================
        if use_ratio:
            # Compute ratios element-wise on embeddings
            ratio_ab = self._safe_divide(scalar_a_embedding, scalar_b_embedding)
            ratio_ba = self._safe_divide(scalar_b_embedding, scalar_a_embedding)
            # Log ratio for better gradient properties
            log_ratio = torch.sign(ratio_ab) * torch.log1p(torch.abs(ratio_ab))

            ratio_input = torch.cat([ratio_ab, ratio_ba, log_ratio], dim=-1)
            ratio_features = self.ratio_mlp(ratio_input)
        else:
            ratio_features = torch.zeros_like(scalar_a_embedding)

        # ============================================================================
        # Feature 2: Relative Magnitude
        # ============================================================================
        diff = scalar_a_embedding - scalar_b_embedding
        abs_diff = torch.abs(diff)
        sign_diff = torch.sign(diff)

        relative_input = torch.cat([diff, abs_diff, sign_diff], dim=-1)
        relative_features = self.relative_mlp(relative_input)

        # ============================================================================
        # Feature 3: Correlation Hint
        # ============================================================================
        # Positive correlation: a*b (both high -> high, both low -> low)
        product = scalar_a_embedding * scalar_b_embedding
        # Negative correlation: a*(-b) (a high, b low -> high)
        anti_product = scalar_a_embedding * (-scalar_b_embedding)

        correlation_input = torch.cat([product, anti_product], dim=-1)
        correlation_features = self.correlation_mlp(correlation_input)

        # ============================================================================
        # Feature 4: Quadratic Interaction
        # ============================================================================
        a_squared = scalar_a_embedding * scalar_a_embedding
        b_squared = scalar_b_embedding * scalar_b_embedding
        a_times_b = scalar_a_embedding * scalar_b_embedding

        quadratic_input = torch.cat([a_squared, b_squared, a_times_b], dim=-1)
        quadratic_features = self.quadratic_mlp(quadratic_input)

        # ============================================================================
        # Feature 5: Symmetric (element-wise product) - always included
        # ============================================================================
        symmetric = scalar_a_embedding * scalar_b_embedding

        # ============================================================================
        # Fusion: Combine all features
        # ============================================================================
        combined = torch.cat([
            ratio_features,
            relative_features,
            correlation_features,
            quadratic_features,
            symmetric,
        ], dim=-1)  # (batch, 5 * d_model)

        output = self.output_norm(self.fusion_mlp(combined))

        # Debug logging (first few calls per training run)
        if not hasattr(self, '_debug_count'):
            self._debug_count = 0
        self._debug_count += 1
        if self._debug_count <= 3:
            with torch.no_grad():
                logger.info(f"🔬 ScalarScalarOps forward #{self._debug_count}:")
                logger.info(f"   Input embeddings: a_norm={scalar_a_embedding.norm(dim=-1).mean():.3f}, b_norm={scalar_b_embedding.norm(dim=-1).mean():.3f}")
                logger.info(f"   Feature norms: ratio={ratio_features.norm(dim=-1).mean():.3f}, relative={relative_features.norm(dim=-1).mean():.3f}, "
                           f"corr={correlation_features.norm(dim=-1).mean():.3f}, quad={quadratic_features.norm(dim=-1).mean():.3f}")
                logger.info(f"   Output norm: {output.norm(dim=-1).mean():.3f}")
                # Check if features are diverse or collapsed
                ratio_var = ratio_features.var(dim=0).mean().item()
                rel_var = relative_features.var(dim=0).mean().item()
                out_var = output.var(dim=0).mean().item()
                logger.info(f"   Feature variance: ratio={ratio_var:.4f}, relative={rel_var:.4f}, output={out_var:.4f}")

        return output
