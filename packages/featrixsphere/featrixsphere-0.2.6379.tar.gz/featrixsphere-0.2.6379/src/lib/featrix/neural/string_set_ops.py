#  -*- coding: utf-8 -*-
#
#  Copyright Featrix, Inc 2023-2025
#
#  Proprietary and Confidential. Unauthorized use, copying or dissemination
#  of these materials is strictly prohibited.
"""
String × Set Relationship Operations

Type-aware relationship operations for String × Set column pairs.
Learns associations like:
- "premium leather" in description → category='luxury'
- "urgent" in notes → priority='high'
- "free shipping" in title → is_promoted=True

Features:
1. Semantic Gating - string content gates set interpretation
2. Category Prediction - string features predict likely categories
3. Text-Category Interaction - how does text relate to this category
4. Keyword Presence - does text contain category-related keywords
"""
import logging
import torch
import torch.nn as nn
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from featrix.neural.type_aware_ops_config import TypeAwareOpsConfig

logger = logging.getLogger(__name__)


class StringSetOps(nn.Module):
    """
    Type-aware operations for String × Set column pairs.

    Computes relationship embeddings that capture how text content
    correlates with categorical values:
    - Does the text content predict the category?
    - How does the category context modify text interpretation?
    - Are there semantic overlaps between text and category names?
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
        # Feature 1: String-Conditioned Set Gating
        # ============================================================================
        # Text content gates which aspects of the set embedding are relevant
        # "premium leather" activates luxury-related set dimensions
        self.string_gate_mlp = nn.Sequential(
            nn.Linear(d_model, d_model // 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model // 2, d_model),
        )

        # ============================================================================
        # Feature 2: Set-Conditioned String Interpretation
        # ============================================================================
        # Category context modifies how we interpret the text
        # "fast" means different things for category='shipping' vs 'performance'
        self.set_context_mlp = nn.Sequential(
            nn.Linear(d_model, d_model // 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model // 2, d_model),
        )

        # ============================================================================
        # Feature 3: Category Prediction from Text
        # ============================================================================
        # Learn to predict category characteristics from text features
        # This is critical for SP where string should predict set target
        self.category_predictor = nn.Sequential(
            nn.Linear(d_model, d_model),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model, d_model),
        )

        # ============================================================================
        # Feature 4: Semantic Similarity
        # ============================================================================
        # Compute semantic alignment between text and category
        # Projects both to shared space for comparison
        self.text_projection = nn.Linear(d_model, d_model // 2)
        self.set_projection = nn.Linear(d_model, d_model // 2)
        self.similarity_mlp = nn.Sequential(
            nn.Linear(d_model // 2, d_model),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model, d_model),
        )

        # ============================================================================
        # Feature 5: Bidirectional Attention
        # ============================================================================
        # Cross-attention between text and set embeddings
        self.cross_attention = nn.MultiheadAttention(
            embed_dim=d_model,
            num_heads=4,
            dropout=0.1,
            batch_first=True,
        )

        # ============================================================================
        # Fusion: Combine all features
        # ============================================================================
        # Input: gated_set + contextualized_string + category_pred + similarity + attention + product = 6 * d_model
        self.fusion_mlp = nn.Sequential(
            nn.Linear(6 * d_model, d_model * 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model * 2, d_model),
        )

        # Output normalization to stabilize training
        self.output_norm = nn.LayerNorm(d_model)

        logger.debug(f"   StringSetOps initialized: d_model={d_model}")

    def forward(
        self,
        string_embedding: torch.Tensor,  # (batch, d_model) - encoded string column
        set_embedding: torch.Tensor,     # (batch, d_model) - encoded set column
    ) -> torch.Tensor:
        """
        Compute relationship embedding for String × Set pair.

        Captures BIDIRECTIONAL relationships:
        - String→Set: "does this text predict that category?" (description→category)
        - Set→String: "how does category context modify text interpretation?"

        Args:
            string_embedding: Embedding from StringEncoder (batch, d_model)
            set_embedding: Embedding from SetEncoder (batch, d_model)

        Returns:
            Relationship embedding of shape (batch, d_model)
        """
        # ============================================================================
        # Feature 1: String-Conditioned Set Gating (String→Set)
        # ============================================================================
        # Text content gates which category dimensions are relevant
        string_gate = torch.sigmoid(self.string_gate_mlp(string_embedding))
        gated_set = set_embedding * string_gate

        # ============================================================================
        # Feature 2: Set-Conditioned String (Set→String)
        # ============================================================================
        # Category context modifies string interpretation
        set_context = self.set_context_mlp(set_embedding)
        contextualized_string = string_embedding * set_context

        # ============================================================================
        # Feature 3: Category Prediction (String→Set)
        # ============================================================================
        # Predict category characteristics from text
        category_pred = self.category_predictor(string_embedding)

        # ============================================================================
        # Feature 4: Semantic Similarity (Bidirectional)
        # ============================================================================
        # Project both to shared space and compute similarity-based features
        text_proj = self.text_projection(string_embedding)  # (batch, d_model//2)
        set_proj = self.set_projection(set_embedding)       # (batch, d_model//2)

        # Element-wise similarity in projected space
        similarity_features = text_proj * set_proj  # (batch, d_model//2)
        similarity_embedding = self.similarity_mlp(similarity_features)

        # ============================================================================
        # Feature 5: Cross-Attention (Bidirectional)
        # ============================================================================
        # Reshape for attention: (batch, 1, d_model)
        string_seq = string_embedding.unsqueeze(1)
        set_seq = set_embedding.unsqueeze(1)

        # String attends to set (what category info is relevant to this text?)
        attention_out, _ = self.cross_attention(
            query=string_seq,
            key=set_seq,
            value=set_seq,
        )
        attention_embedding = attention_out.squeeze(1)  # (batch, d_model)

        # ============================================================================
        # Feature 6: Element-wise Product (Symmetric)
        # ============================================================================
        product = string_embedding * set_embedding

        # ============================================================================
        # Fusion: Combine all features
        # ============================================================================
        combined = torch.cat([
            gated_set,              # String→Set: text gates category
            contextualized_string,  # Set→String: category contextualizes text
            category_pred,          # String→Set: text predicts category
            similarity_embedding,   # Bidirectional: semantic alignment
            attention_embedding,    # Bidirectional: cross-attention
            product,                # Symmetric: direct interaction
        ], dim=-1)  # (batch, 6 * d_model)

        return self.output_norm(self.fusion_mlp(combined))
