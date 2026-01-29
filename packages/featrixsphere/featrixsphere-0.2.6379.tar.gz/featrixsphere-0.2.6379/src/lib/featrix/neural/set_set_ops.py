#  -*- coding: utf-8 -*-
#
#  Copyright Featrix, Inc 2023-2025
#
#  Proprietary and Confidential. Unauthorized use, copying or dissemination
#  of these materials is strictly prohibited.
"""
Set × Set Relationship Operations

Type-aware relationship operations for Set × Set column pairs.
Learns associations like:
- "category='electronics' often co-occurs with payment_method='credit_card'"
- "region='west' correlates with customer_segment='premium'"
- "status='active' predicts subscription_type='annual'"

Features:
1. Co-occurrence Attention - cross-attention between set embeddings
2. Bilinear Interaction - learned bilinear map between sets
3. Symmetric/Asymmetric - separate symmetric and asymmetric relationships
"""
import logging
import math
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from featrix.neural.type_aware_ops_config import TypeAwareOpsConfig

logger = logging.getLogger(__name__)


class SetSetOps(nn.Module):
    """
    Type-aware operations for Set × Set column pairs.

    Computes relationship embeddings that capture co-occurrence patterns:
    - Which set values tend to occur together?
    - Are there asymmetric dependencies (A predicts B but not vice versa)?
    - What's the bilinear interaction between the two set spaces?
    """

    def __init__(
        self,
        d_model: int,
        config: Optional["TypeAwareOpsConfig"] = None,
        n_attention_heads: int = 4,
    ):
        """
        Args:
            d_model: Model dimension
            config: TypeAwareOpsConfig for granular feature control
            n_attention_heads: Number of attention heads for cross-attention
        """
        super().__init__()
        self.d_model = d_model
        self.config = config
        self.n_attention_heads = n_attention_heads
        self.d_head = d_model // n_attention_heads

        # ============================================================================
        # Feature 1: Co-occurrence Attention
        # ============================================================================
        # Cross-attention: how much does set A "attend to" set B?
        self.set_a_to_query = nn.Linear(d_model, n_attention_heads * self.d_head)
        self.set_b_to_key = nn.Linear(d_model, n_attention_heads * self.d_head)
        self.set_b_to_value = nn.Linear(d_model, n_attention_heads * self.d_head)
        self.cross_attn_out = nn.Linear(n_attention_heads * self.d_head, d_model)

        # Attention in the other direction (B attends to A)
        self.set_b_to_query = nn.Linear(d_model, n_attention_heads * self.d_head)
        self.set_a_to_key = nn.Linear(d_model, n_attention_heads * self.d_head)
        self.set_a_to_value = nn.Linear(d_model, n_attention_heads * self.d_head)
        self.cross_attn_out_ba = nn.Linear(n_attention_heads * self.d_head, d_model)

        # ============================================================================
        # Feature 2: Bilinear Interaction
        # ============================================================================
        # Learn a bilinear map: a^T W b
        # Use low-rank factorization for efficiency: W = U V^T where U, V are (d_model, rank)
        self.bilinear_rank = d_model // 4
        self.bilinear_U = nn.Linear(d_model, self.bilinear_rank, bias=False)
        self.bilinear_V = nn.Linear(d_model, self.bilinear_rank, bias=False)
        # Project bilinear output back to d_model
        self.bilinear_out = nn.Linear(self.bilinear_rank, d_model)

        # ============================================================================
        # Feature 3: Asymmetric Relationships
        # ============================================================================
        # Some set×set relationships are asymmetric (A predicts B but not vice versa)
        self.asymmetric_ab = nn.Sequential(
            nn.Linear(d_model * 2, d_model),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model, d_model),
        )
        self.asymmetric_ba = nn.Sequential(
            nn.Linear(d_model * 2, d_model),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model, d_model),
        )

        # ============================================================================
        # Fusion: Combine all features
        # ============================================================================
        # Input: cross_attn_ab + cross_attn_ba + bilinear + symmetric + asym_ab + asym_ba
        # = 6 * d_model
        self.fusion_mlp = nn.Sequential(
            nn.Linear(6 * d_model, d_model * 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model * 2, d_model),
        )

        # Output normalization to stabilize training
        self.output_norm = nn.LayerNorm(d_model)

        logger.debug(f"   SetSetOps initialized: d_model={d_model}, heads={n_attention_heads}")

    def _compute_cross_attention(
        self,
        query_emb: torch.Tensor,  # (batch, d_model)
        key_emb: torch.Tensor,    # (batch, d_model)
        value_emb: torch.Tensor,  # (batch, d_model)
        q_proj: nn.Linear,
        k_proj: nn.Linear,
        v_proj: nn.Linear,
        out_proj: nn.Linear,
    ) -> torch.Tensor:
        """
        Compute cross-attention from query to key/value.

        For set×set, we compute per-sample attention where each sample's
        query attends to that same sample's key/value. This captures
        "given this value of A, how relevant is the value of B?"
        """
        batch_size = query_emb.shape[0]

        # Project to multi-head format: (batch, n_heads, d_head)
        Q = q_proj(query_emb).view(batch_size, self.n_attention_heads, self.d_head)
        K = k_proj(key_emb).view(batch_size, self.n_attention_heads, self.d_head)
        V = v_proj(value_emb).view(batch_size, self.n_attention_heads, self.d_head)

        # Compute attention scores: Q @ K^T / sqrt(d_head)
        # For per-sample: (batch, n_heads, d_head) @ (batch, n_heads, d_head)^T
        # Sum over d_head dimension to get scalar per head
        # (batch, n_heads)
        attn_scores = (Q * K).sum(dim=-1) / math.sqrt(self.d_head)

        # Apply softmax over heads (or could skip since we just use the weighted V)
        # Actually for set×set we don't need softmax since there's only one key per query
        # We use the attention score as a gating weight instead
        attn_weights = torch.sigmoid(attn_scores)  # (batch, n_heads)

        # Weight the values
        # V: (batch, n_heads, d_head), weights: (batch, n_heads)
        weighted_V = V * attn_weights.unsqueeze(-1)  # (batch, n_heads, d_head)

        # Flatten and project
        weighted_flat = weighted_V.reshape(batch_size, -1)  # (batch, n_heads * d_head)
        return out_proj(weighted_flat)

    def forward(
        self,
        set_a_embedding: torch.Tensor,  # (batch, d_model) - encoded set column A
        set_b_embedding: torch.Tensor,  # (batch, d_model) - encoded set column B
    ) -> torch.Tensor:
        """
        Compute relationship embedding for Set × Set pair.

        Args:
            set_a_embedding: Embedding from SetEncoder for column A (batch, d_model)
            set_b_embedding: Embedding from SetEncoder for column B (batch, d_model)

        Returns:
            Relationship embedding of shape (batch, d_model)
        """
        # Check config for which features to compute
        use_cross_attn = self.config is None or self.config.enable_cross_attention

        # ============================================================================
        # Feature 1: Co-occurrence Attention (bidirectional)
        # ============================================================================
        if use_cross_attn:
            # A attends to B
            cross_attn_ab = self._compute_cross_attention(
                set_a_embedding, set_b_embedding, set_b_embedding,
                self.set_a_to_query, self.set_b_to_key, self.set_b_to_value,
                self.cross_attn_out,
            )
            # B attends to A
            cross_attn_ba = self._compute_cross_attention(
                set_b_embedding, set_a_embedding, set_a_embedding,
                self.set_b_to_query, self.set_a_to_key, self.set_a_to_value,
                self.cross_attn_out_ba,
            )
        else:
            cross_attn_ab = torch.zeros_like(set_a_embedding)
            cross_attn_ba = torch.zeros_like(set_a_embedding)

        # ============================================================================
        # Feature 2: Bilinear Interaction
        # ============================================================================
        # Low-rank bilinear: (U @ a) * (V @ b) element-wise, then project
        # This captures multiplicative interactions between the two sets
        proj_a = self.bilinear_U(set_a_embedding)  # (batch, rank)
        proj_b = self.bilinear_V(set_b_embedding)  # (batch, rank)
        bilinear = self.bilinear_out(proj_a * proj_b)  # (batch, d_model)

        # ============================================================================
        # Feature 3: Symmetric (element-wise product)
        # ============================================================================
        symmetric = set_a_embedding * set_b_embedding

        # ============================================================================
        # Feature 4: Asymmetric Relationships
        # ============================================================================
        # A -> B direction
        asym_ab = self.asymmetric_ab(torch.cat([set_a_embedding, set_b_embedding], dim=-1))
        # B -> A direction
        asym_ba = self.asymmetric_ba(torch.cat([set_b_embedding, set_a_embedding], dim=-1))

        # ============================================================================
        # Fusion: Combine all features
        # ============================================================================
        combined = torch.cat([
            cross_attn_ab,
            cross_attn_ba,
            bilinear,
            symmetric,
            asym_ab,
            asym_ba,
        ], dim=-1)  # (batch, 6 * d_model)

        return self.output_norm(self.fusion_mlp(combined))
