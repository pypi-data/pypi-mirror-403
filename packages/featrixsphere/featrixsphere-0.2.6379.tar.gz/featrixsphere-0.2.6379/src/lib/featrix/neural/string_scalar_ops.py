#  -*- coding: utf-8 -*-
#
#  Copyright Featrix, Inc 2023-2025
#
#  Proprietary and Confidential. Unauthorized use, copying or dissemination
#  of these materials is strictly prohibited.
"""
String × Scalar Relationship Operations

Type-aware relationship operations for String × Scalar column pairs.
Learns associations like:
- Longer descriptions → higher price
- "urgent" in notes → shorter time_to_close
- Positive sentiment → higher rating
- Technical jargon → higher complexity_score

Features:
1. Text Complexity Features - length, vocabulary richness, structure
2. Scalar-Conditioned Text Gating - scalar magnitude modulates text interpretation
3. Text→Scalar Prediction - text features predict scalar patterns
4. Scalar→Text Context - scalar value provides context for text interpretation
"""
import logging
import torch
import torch.nn as nn
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from featrix.neural.type_aware_ops_config import TypeAwareOpsConfig

logger = logging.getLogger(__name__)


class StringScalarOps(nn.Module):
    """
    Type-aware operations for String × Scalar column pairs.

    Computes relationship embeddings that capture how text content
    correlates with numeric values:
    - Does text length/complexity predict the scalar?
    - How does the scalar magnitude modify text interpretation?
    - Are there semantic patterns that correlate with high/low values?
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
        # Feature 1: Scalar-Conditioned Text Gating
        # ============================================================================
        # Scalar magnitude gates which text features are relevant
        # High price → emphasize "luxury" aspects of description
        self.scalar_gate_mlp = nn.Sequential(
            nn.Linear(d_model, d_model // 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model // 2, d_model),
        )

        # ============================================================================
        # Feature 2: Text-Conditioned Scalar Scaling
        # ============================================================================
        # Text content modifies scalar interpretation
        # "discount" in description → different price interpretation
        self.text_scale_mlp = nn.Sequential(
            nn.Linear(d_model, d_model // 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model // 2, d_model),
        )

        # ============================================================================
        # Feature 3: Text→Scalar Prediction
        # ============================================================================
        # Predict scalar characteristics from text features
        # Critical for SP where string should predict scalar target
        self.scalar_predictor = nn.Sequential(
            nn.Linear(d_model, d_model),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model, d_model),
        )

        # ============================================================================
        # Feature 4: Magnitude Context
        # ============================================================================
        # Learn relationship between text semantics and scalar magnitude
        self.magnitude_context_mlp = nn.Sequential(
            nn.Linear(d_model * 2, d_model),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model, d_model),
        )

        # ============================================================================
        # Feature 5: Correlation Learning
        # ============================================================================
        # Learn text-scalar correlation patterns
        # Projects both to shared space for correlation analysis
        self.text_projection = nn.Linear(d_model, d_model // 2)
        self.scalar_projection = nn.Linear(d_model, d_model // 2)
        self.correlation_mlp = nn.Sequential(
            nn.Linear(d_model, d_model),  # d_model//2 * 2 = d_model (concat)
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model, d_model),
        )

        # ============================================================================
        # Fusion: Combine all features
        # ============================================================================
        # Input: gated_text + scaled_scalar + scalar_pred + magnitude + correlation + product = 6 * d_model
        self.fusion_mlp = nn.Sequential(
            nn.Linear(6 * d_model, d_model * 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model * 2, d_model),
        )

        # Output normalization to stabilize training
        self.output_norm = nn.LayerNorm(d_model)

        logger.debug(f"   StringScalarOps initialized: d_model={d_model}")

    def forward(
        self,
        string_embedding: torch.Tensor,   # (batch, d_model) - encoded string column
        scalar_embedding: torch.Tensor,   # (batch, d_model) - encoded scalar column
    ) -> torch.Tensor:
        """
        Compute relationship embedding for String × Scalar pair.

        Captures BIDIRECTIONAL relationships:
        - String→Scalar: "does this text predict that value?" (description→price)
        - Scalar→String: "how does value context modify text interpretation?"

        Args:
            string_embedding: Embedding from StringEncoder (batch, d_model)
            scalar_embedding: Embedding from ScalarEncoder (batch, d_model)

        Returns:
            Relationship embedding of shape (batch, d_model)
        """
        # ============================================================================
        # Feature 1: Scalar-Conditioned Text Gating (Scalar→String)
        # ============================================================================
        # Scalar magnitude gates which text dimensions are emphasized
        scalar_gate = torch.sigmoid(self.scalar_gate_mlp(scalar_embedding))
        gated_text = string_embedding * scalar_gate

        # ============================================================================
        # Feature 2: Text-Conditioned Scalar Scaling (String→Scalar)
        # ============================================================================
        # Text content modifies scalar embedding interpretation
        text_scale = self.text_scale_mlp(string_embedding)
        scaled_scalar = scalar_embedding * text_scale

        # ============================================================================
        # Feature 3: Scalar Prediction (String→Scalar)
        # ============================================================================
        # Predict scalar characteristics from text
        scalar_pred = self.scalar_predictor(string_embedding)

        # ============================================================================
        # Feature 4: Magnitude Context (Bidirectional)
        # ============================================================================
        # Learn relationship between text and scalar magnitude
        magnitude_context = self.magnitude_context_mlp(
            torch.cat([string_embedding, scalar_embedding], dim=-1)
        )

        # ============================================================================
        # Feature 5: Correlation Learning (Bidirectional)
        # ============================================================================
        # Project both to shared space for correlation analysis
        text_proj = self.text_projection(string_embedding)     # (batch, d_model//2)
        scalar_proj = self.scalar_projection(scalar_embedding) # (batch, d_model//2)

        # Concatenate projections and learn correlation
        correlation_input = torch.cat([text_proj, scalar_proj], dim=-1)
        correlation = self.correlation_mlp(correlation_input)

        # ============================================================================
        # Feature 6: Element-wise Product (Symmetric)
        # ============================================================================
        product = string_embedding * scalar_embedding

        # ============================================================================
        # Fusion: Combine all features
        # ============================================================================
        combined = torch.cat([
            gated_text,        # Scalar→String: scalar gates text
            scaled_scalar,     # String→Scalar: text scales scalar
            scalar_pred,       # String→Scalar: text predicts scalar
            magnitude_context, # Bidirectional: magnitude relationship
            correlation,       # Bidirectional: correlation patterns
            product,           # Symmetric: direct interaction
        ], dim=-1)  # (batch, 6 * d_model)

        return self.output_norm(self.fusion_mlp(combined))
