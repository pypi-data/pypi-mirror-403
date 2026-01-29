#  -*- coding: utf-8 -*-
#
#  Copyright Featrix, Inc 2023-2025
#
#  Proprietary and Confidential. Unauthorized use, copying or dissemination
#  of these materials is strictly prohibited.
"""
Set × Timestamp Relationship Operations

Type-aware relationship operations for Set × Timestamp column pairs.
Learns associations like:
- "event_type='cleaning' correlates with day_of_week='Monday'"
- "category='electronics' peaks in Q4"
- "status='urgent' happens more on weekday mornings"

Features:
1. Temporal Distribution Gating - gate set embeddings by temporal context
2. Cross-Attention - set attends to temporal aspects
3. Temporal Embedding Modulation - modulate set by temporal position
"""
import logging
import math
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from featrix.neural.type_aware_ops_config import TypeAwareOpsConfig

logger = logging.getLogger(__name__)

# Feature indices in timestamp token (from TimestampCodec._extract_features)
# [seconds, minutes, hours, day_of_month, day_of_week, month, year,
#  day_of_year, week_of_year, timezone, year_since_2000, year_since_2020]
FEAT_SECONDS = 0
FEAT_MINUTES = 1
FEAT_HOURS = 2
FEAT_DAY_OF_MONTH = 3
FEAT_DAY_OF_WEEK = 4
FEAT_MONTH = 5
FEAT_YEAR = 6
FEAT_DAY_OF_YEAR = 7
FEAT_WEEK_OF_YEAR = 8
FEAT_TIMEZONE = 9
FEAT_YEAR_SINCE_2000 = 10
FEAT_YEAR_SINCE_2020 = 11

# Number of temporal aspects for cross-attention
N_TEMPORAL_ASPECTS = 5  # day_of_week, hour_bucket, month, weekend, quarter


class SetTimestampOps(nn.Module):
    """
    Type-aware operations for Set × Timestamp column pairs.

    Computes relationship embeddings that capture temporal patterns in set data:
    - When does each set category occur?
    - Which temporal aspects correlate with which categories?
    - How do set values distribute across time?
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
        # Feature 1: Temporal Distribution Gating
        # ============================================================================
        # Input: temporal features extracted from raw timestamp
        # day_of_week (7) + hour_bucket (4) + month (12) + is_weekend (1) + quarter (4)
        # + day_of_month_bucket (5) + day_of_year_bucket (4) = 37
        self.n_temporal_features = 37

        self.temporal_gate_mlp = nn.Sequential(
            nn.Linear(self.n_temporal_features, d_model // 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model // 2, d_model),
        )

        # ============================================================================
        # Feature 2: Cross-Attention (Set attends to Temporal Aspects)
        # ============================================================================
        # Learnable temporal aspect embeddings
        self.temporal_aspect_embeddings = nn.Parameter(
            torch.randn(N_TEMPORAL_ASPECTS, d_model) * 0.02
        )

        # Query projection (from set embedding)
        self.set_to_query = nn.Linear(d_model, n_attention_heads * self.d_head)
        # Key/Value projections (from temporal aspects)
        self.temporal_to_key = nn.Linear(d_model, n_attention_heads * self.d_head)
        self.temporal_to_value = nn.Linear(d_model, n_attention_heads * self.d_head)
        # Output projection
        self.cross_attn_out = nn.Linear(n_attention_heads * self.d_head, d_model)

        # ============================================================================
        # Feature 3: Temporal Embedding Modulation
        # ============================================================================
        # Cyclical temporal encoding (sin/cos for continuous time features)
        self.n_cyclical_features = 8  # 2 each for: hour, dow, month, week_of_year
        self.cyclical_mlp = nn.Sequential(
            nn.Linear(self.n_cyclical_features, d_model // 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model // 2, d_model),
        )

        # ============================================================================
        # Feature 4: Timestamp→Set Direction (time components predict set values)
        # ============================================================================
        # "Given this time, which set values are more likely?"
        # e.g., "status='CLOSED' happens more at noon", "category='urgent' on weekday mornings"
        # This is critical for SP where temporal features should predict target set values
        self.temporal_predictor = nn.Sequential(
            nn.Linear(self.n_temporal_features, d_model // 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model // 2, d_model),
        )

        # Interaction: how does set membership respond to temporal context?
        self.temporal_set_interaction = nn.Sequential(
            nn.Linear(d_model * 2, d_model),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model, d_model),
        )

        # ============================================================================
        # Fusion: Combine all features into final relationship embedding
        # ============================================================================
        # Input: gated_set + cross_attn + modulated_set + generic_mult + temporal_pred + temporal_interaction = 6 * d_model
        self.fusion_mlp = nn.Sequential(
            nn.Linear(6 * d_model, d_model * 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model * 2, d_model),
        )

        # Output normalization to stabilize training
        self.output_norm = nn.LayerNorm(d_model)

        logger.debug(f"   SetTimestampOps initialized: d_model={d_model}, heads={n_attention_heads}")

    def _extract_temporal_features(
        self,
        raw_timestamp: torch.Tensor,  # (batch, 12) raw timestamp features
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Extract temporal features for gating and cyclical modulation.

        Args:
            raw_timestamp: Raw 12-feature timestamp tensor from TimestampCodec

        Returns:
            temporal_features: (batch, 28) one-hot/binary temporal features
            cyclical_features: (batch, 8) sin/cos cyclical features
        """
        # CRITICAL: Sanitize NaN/Inf values BEFORE any operations
        # NaN in raw_timestamp causes gradient explosions and training failure
        raw_timestamp = torch.nan_to_num(raw_timestamp, nan=0.0, posinf=0.0, neginf=0.0)

        batch_size = raw_timestamp.shape[0]
        device = raw_timestamp.device

        # Extract raw values
        hour = raw_timestamp[:, FEAT_HOURS]  # 0-23
        dow = raw_timestamp[:, FEAT_DAY_OF_WEEK]  # 0-6
        month = raw_timestamp[:, FEAT_MONTH]  # 1-12
        week = raw_timestamp[:, FEAT_WEEK_OF_YEAR]  # 1-52
        day_of_month = raw_timestamp[:, FEAT_DAY_OF_MONTH]  # 1-31
        day_of_year = raw_timestamp[:, FEAT_DAY_OF_YEAR]  # 1-366

        # ============================================================================
        # One-hot/binary features for gating (37 total)
        # ============================================================================
        # Day of week: 7 one-hot
        dow_idx = dow.round().long().clamp(0, 6)
        dow_onehot = F.one_hot(dow_idx, num_classes=7).float()  # (batch, 7)

        # Hour bucket: 4 one-hot (night 0-5, morning 6-11, afternoon 12-17, evening 18-23)
        hour_bucket = (hour.long() // 6).clamp(0, 3)
        hour_onehot = F.one_hot(hour_bucket, num_classes=4).float()  # (batch, 4)

        # Month: 12 one-hot
        month_idx = (month.round().long() - 1).clamp(0, 11)
        month_onehot = F.one_hot(month_idx, num_classes=12).float()  # (batch, 12)

        # Weekend: 1 binary
        is_weekend = (dow_idx >= 5).float().unsqueeze(-1)  # (batch, 1)

        # Quarter: 4 one-hot
        quarter_idx = (month_idx // 3).clamp(0, 3)
        quarter_onehot = F.one_hot(quarter_idx, num_classes=4).float()  # (batch, 4)

        # Day of month bucket: 5 one-hot (1-7, 8-14, 15-21, 22-28, 29-31)
        # Captures patterns like "end of month billing", "first of month payments"
        dom_bucket = ((day_of_month.round().long() - 1) // 7).clamp(0, 4)
        dom_onehot = F.one_hot(dom_bucket, num_classes=5).float()  # (batch, 5)

        # Day of year bucket: 4 one-hot (quarterly)
        # Captures seasonal patterns beyond just month
        doy_bucket = ((day_of_year.round().long() - 1) // 92).clamp(0, 3)  # ~91.25 days per quarter
        doy_onehot = F.one_hot(doy_bucket, num_classes=4).float()  # (batch, 4)

        # Concatenate all: 7 + 4 + 12 + 1 + 4 + 5 + 4 = 37
        temporal_features = torch.cat([
            dow_onehot,
            hour_onehot,
            month_onehot,
            is_weekend,
            quarter_onehot,
            dom_onehot,
            doy_onehot,
        ], dim=-1)

        # ============================================================================
        # Cyclical features for modulation (8 total)
        # ============================================================================
        pi2 = 2 * math.pi

        # Hour cycle (24h period)
        hour_sin = torch.sin(pi2 * hour / 24)
        hour_cos = torch.cos(pi2 * hour / 24)

        # Day of week cycle (7 day period)
        dow_sin = torch.sin(pi2 * dow / 7)
        dow_cos = torch.cos(pi2 * dow / 7)

        # Month cycle (12 month period)
        month_sin = torch.sin(pi2 * (month - 1) / 12)
        month_cos = torch.cos(pi2 * (month - 1) / 12)

        # Week of year cycle (52 week period)
        week_sin = torch.sin(pi2 * (week - 1) / 52)
        week_cos = torch.cos(pi2 * (week - 1) / 52)

        cyclical_features = torch.stack([
            hour_sin, hour_cos,
            dow_sin, dow_cos,
            month_sin, month_cos,
            week_sin, week_cos,
        ], dim=-1)

        return temporal_features, cyclical_features

    def forward(
        self,
        set_embedding: torch.Tensor,       # (batch, d_model) - encoded set column
        timestamp_embedding: torch.Tensor,  # (batch, d_model) - encoded timestamp column
        raw_timestamp: torch.Tensor,        # (batch, 12) - raw timestamp features
    ) -> torch.Tensor:
        """
        Compute relationship embedding for Set × Timestamp pair.

        Captures BIDIRECTIONAL relationships:
        - Set→Timestamp: "when does this set value occur?" (status='CLOSED' happens at noon)
        - Timestamp→Set: "given this time, which set values are likely?" (predicting target from time)

        Args:
            set_embedding: Embedding from SetEncoder (batch, d_model)
            timestamp_embedding: Embedding from TimestampEncoder (batch, d_model)
            raw_timestamp: Raw 12-feature timestamp tensor from TimestampCodec

        Returns:
            Relationship embedding of shape (batch, d_model)
        """
        batch_size = set_embedding.shape[0]
        device = set_embedding.device

        # Extract temporal features
        temporal_features, cyclical_features = self._extract_temporal_features(raw_timestamp)

        # Check config for which features to compute
        use_gating = self.config is None or self.config.enable_temporal_gating
        use_cross_attn = self.config is None or self.config.enable_cross_attention

        # ============================================================================
        # Feature 1: Temporal Distribution Gating (Set→Timestamp direction)
        # ============================================================================
        # "When does this set value occur?"
        if use_gating:
            temporal_gate = self.temporal_gate_mlp(temporal_features)  # (batch, d_model)
            gated_set = set_embedding * torch.sigmoid(temporal_gate)
        else:
            gated_set = set_embedding

        # ============================================================================
        # Feature 2: Cross-Attention (Set attends to Temporal Aspects)
        # ============================================================================
        if use_cross_attn:
            # Query from set embedding: (batch, n_heads, d_head)
            Q = self.set_to_query(set_embedding).view(batch_size, self.n_attention_heads, self.d_head)

            # Keys/Values from temporal aspects: (n_aspects, n_heads, d_head)
            K = self.temporal_to_key(self.temporal_aspect_embeddings).view(
                N_TEMPORAL_ASPECTS, self.n_attention_heads, self.d_head
            )
            V = self.temporal_to_value(self.temporal_aspect_embeddings).view(
                N_TEMPORAL_ASPECTS, self.n_attention_heads, self.d_head
            )

            # Attention: Q @ K.T -> (batch, n_heads, n_aspects)
            # Q: (batch, n_heads, d_head)
            # K: (n_aspects, n_heads, d_head) -> transpose to (n_heads, d_head, n_aspects)
            K_t = K.permute(1, 2, 0)  # (n_heads, d_head, n_aspects)
            attn_scores = torch.einsum('bnd,nda->bna', Q, K_t) / math.sqrt(self.d_head)
            attn_weights = F.softmax(attn_scores, dim=-1)  # (batch, n_heads, n_aspects)

            # Weighted sum: attn_weights @ V -> (batch, n_heads, d_head)
            # V: (n_aspects, n_heads, d_head) -> (n_heads, n_aspects, d_head)
            V_t = V.permute(1, 0, 2)  # (n_heads, n_aspects, d_head)
            attended = torch.einsum('bna,nad->bnd', attn_weights, V_t)  # (batch, n_heads, d_head)

            # Flatten and project: (batch, n_heads * d_head) -> (batch, d_model)
            attended_flat = attended.reshape(batch_size, -1)
            cross_attn_out = self.cross_attn_out(attended_flat)
        else:
            cross_attn_out = torch.zeros_like(set_embedding)

        # ============================================================================
        # Feature 3: Temporal Embedding Modulation (Set→Timestamp direction)
        # ============================================================================
        modulation = self.cyclical_mlp(cyclical_features)  # (batch, d_model)
        modulated_set = set_embedding + set_embedding * modulation

        # ============================================================================
        # Generic embedding multiplication (always included)
        # ============================================================================
        generic_mult = set_embedding * timestamp_embedding

        # ============================================================================
        # Feature 4: Temporal Predictor (Timestamp→Set direction) - NEW
        # ============================================================================
        # "Given this time (weekend? 12pm? January?), which set values are likely?"
        # This is critical for SP where temporal features should predict target set values
        # e.g., "status='urgent' is more common on weekday mornings"
        temporal_pred = self.temporal_predictor(temporal_features)  # (batch, d_model)

        # Interaction: combine temporal prediction with set context
        # This learns "how does set membership respond to this temporal context"
        temporal_interaction = self.temporal_set_interaction(
            torch.cat([temporal_pred, set_embedding], dim=-1)
        )

        # ============================================================================
        # Fusion: Combine all features (6 total)
        # ============================================================================
        combined = torch.cat([
            gated_set,               # Set→Timestamp: when does this set value occur
            cross_attn_out,          # Set→Timestamp: set attends to temporal aspects
            modulated_set,           # Set→Timestamp: set modulated by cyclical time
            generic_mult,            # Generic: embedding product
            temporal_pred,           # Timestamp→Set: time predicts set values (NEW)
            temporal_interaction,    # Timestamp→Set: set response to time (NEW)
        ], dim=-1)  # (batch, 6 * d_model)

        # NaN ASSERTION: Check combined features before fusion
        assert not torch.isnan(combined).any(), "NaN in SetTimestampOps combined features before fusion!"

        result = self.output_norm(self.fusion_mlp(combined))

        # NaN ASSERTION: Check final output
        assert not torch.isnan(result).any(), "NaN in SetTimestampOps output!"

        return result
