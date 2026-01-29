#  -*- coding: utf-8 -*-
#
#  Copyright Featrix, Inc 2023-2025
#
#  Proprietary and Confidential. Unauthorized use, copying or dissemination
#  of these materials is strictly prohibited.
"""
Scalar × Timestamp Relationship Operations

Type-aware relationship operations for Scalar × Timestamp column pairs.
Learns associations like:
- "sales are 2x higher on weekends"
- "temperature peaks at 2pm"
- "price drops in January"

Features:
1. Temporal Trend Encoding - encode scalar with temporal context
2. Cyclical Correlation - correlate scalar with cyclical time components
3. Temporal Context Modulation - modulate scalar by time-of-day/day-of-week
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
FEAT_HOURS = 2
FEAT_DAY_OF_WEEK = 4
FEAT_MONTH = 5
FEAT_DAY_OF_MONTH = 6
FEAT_WEEK_OF_YEAR = 8
FEAT_DAY_OF_YEAR = 9


class ScalarTimestampOps(nn.Module):
    """
    Type-aware operations for Scalar × Timestamp column pairs.

    Computes relationship embeddings that capture how scalar values
    correlate with temporal patterns:
    - How does the scalar value vary by time of day?
    - Are there weekly/monthly patterns in the scalar?
    - Does the scalar peak at certain times?
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
        # Feature 1: Temporal Trend Encoding
        # ============================================================================
        # Encode scalar with different temporal contexts
        # Hour encoding
        self.hour_encoder = nn.Sequential(
            nn.Linear(4, d_model // 4),  # 4 hour buckets
            nn.ReLU(),
            nn.Linear(d_model // 4, d_model),
        )
        # Day of week encoding
        self.dow_encoder = nn.Sequential(
            nn.Linear(7, d_model // 4),  # 7 days
            nn.ReLU(),
            nn.Linear(d_model // 4, d_model),
        )
        # Month encoding
        self.month_encoder = nn.Sequential(
            nn.Linear(12, d_model // 4),  # 12 months
            nn.ReLU(),
            nn.Linear(d_model // 4, d_model),
        )

        # ============================================================================
        # Feature 2: Cyclical Correlation
        # ============================================================================
        # Correlate scalar with cyclical time components (sin/cos)
        # 8 cyclical features: sin/cos for hour, dow, month, week
        self.n_cyclical_features = 8
        self.cyclical_mlp = nn.Sequential(
            nn.Linear(d_model + self.n_cyclical_features, d_model),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model, d_model),
        )

        # ============================================================================
        # Feature 3: Rate/Trend Context
        # ============================================================================
        # Learn a "typical rate of change" context embedding
        # This captures whether scalar-timestamp pairs exhibit trends
        self.rate_mlp = nn.Sequential(
            nn.Linear(d_model * 2, d_model),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model, d_model),
        )

        # ============================================================================
        # Feature 4: Timestamp→Scalar Direction (time components predict scalar patterns)
        # ============================================================================
        # "Given this time, what scalar value would we expect?"
        # This is critical for SP training where we want temporal features to predict target
        # 37 temporal features: dow(7) + hour_bucket(4) + month(12) + weekend(1) + quarter(4)
        #                     + day_of_month_bucket(5) + day_of_year_bucket(4)
        self.n_temporal_features = 37
        self.temporal_predictor = nn.Sequential(
            nn.Linear(self.n_temporal_features, d_model // 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model // 2, d_model),
        )

        # Interaction: how does scalar respond to temporal context?
        self.temporal_scalar_interaction = nn.Sequential(
            nn.Linear(d_model * 2, d_model),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model, d_model),
        )

        # ============================================================================
        # Fusion: Combine all features
        # ============================================================================
        # Input: trend_hour + trend_dow + trend_month + cyclical + rate + generic + temporal_pred + temporal_interaction = 8 * d_model
        self.fusion_mlp = nn.Sequential(
            nn.Linear(8 * d_model, d_model * 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model * 2, d_model),
        )

        # Output normalization to stabilize training
        self.output_norm = nn.LayerNorm(d_model)

        logger.debug(f"   ScalarTimestampOps initialized: d_model={d_model}")

    def _extract_temporal_features(
        self,
        raw_timestamp: torch.Tensor,  # (batch, 12) raw timestamp features
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Extract temporal features for trend encoding, cyclical correlation, and predictive features.

        Args:
            raw_timestamp: Raw 12-feature timestamp tensor from TimestampCodec

        Returns:
            hour_onehot: (batch, 4) hour bucket one-hot
            dow_onehot: (batch, 7) day of week one-hot
            month_onehot: (batch, 12) month one-hot
            cyclical_features: (batch, 8) sin/cos cyclical features
            temporal_features: (batch, 37) all temporal features for prediction
        """
        # CRITICAL: Sanitize NaN/Inf values BEFORE any operations
        # NaN in raw_timestamp causes gradient explosions and training failure
        raw_timestamp = torch.nan_to_num(raw_timestamp, nan=0.0, posinf=0.0, neginf=0.0)

        # Extract raw values
        hour = raw_timestamp[:, FEAT_HOURS]  # 0-23
        dow = raw_timestamp[:, FEAT_DAY_OF_WEEK]  # 0-6
        month = raw_timestamp[:, FEAT_MONTH]  # 1-12
        week = raw_timestamp[:, FEAT_WEEK_OF_YEAR]  # 1-52
        day_of_month = raw_timestamp[:, FEAT_DAY_OF_MONTH]  # 1-31
        day_of_year = raw_timestamp[:, FEAT_DAY_OF_YEAR]  # 1-366

        # ============================================================================
        # One-hot features for trend encoding
        # ============================================================================
        # Hour bucket: 4 one-hot (night 0-5, morning 6-11, afternoon 12-17, evening 18-23)
        hour_bucket = (hour.long() // 6).clamp(0, 3)
        hour_onehot = F.one_hot(hour_bucket, num_classes=4).float()  # (batch, 4)

        # Day of week: 7 one-hot
        dow_idx = dow.round().long().clamp(0, 6)
        dow_onehot = F.one_hot(dow_idx, num_classes=7).float()  # (batch, 7)

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

        # ============================================================================
        # Combined temporal features for prediction (37 total)
        # ============================================================================
        # dow(7) + hour_bucket(4) + month(12) + weekend(1) + quarter(4) + dom(5) + doy(4) = 37
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
        # Cyclical features for correlation
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

        return hour_onehot, dow_onehot, month_onehot, cyclical_features, temporal_features

    def forward(
        self,
        scalar_embedding: torch.Tensor,     # (batch, d_model) - encoded scalar column
        timestamp_embedding: torch.Tensor,  # (batch, d_model) - encoded timestamp column
        raw_timestamp: torch.Tensor,        # (batch, 12) - raw timestamp features
    ) -> torch.Tensor:
        """
        Compute relationship embedding for Scalar × Timestamp pair.

        Captures BIDIRECTIONAL relationships:
        - Scalar→Timestamp: "how does this scalar vary with time?" (sales higher on weekends)
        - Timestamp→Scalar: "given this time, what scalar do we expect?" (predicting target from time)

        Args:
            scalar_embedding: Embedding from ScalarEncoder (batch, d_model)
            timestamp_embedding: Embedding from TimestampEncoder (batch, d_model)
            raw_timestamp: Raw 12-feature timestamp tensor from TimestampCodec

        Returns:
            Relationship embedding of shape (batch, d_model)
        """
        # Extract temporal features
        hour_onehot, dow_onehot, month_onehot, cyclical_features, temporal_features = self._extract_temporal_features(
            raw_timestamp
        )

        # Check config for which features to compute
        use_cyclical = self.config is None or self.config.enable_cyclical_features

        # ============================================================================
        # Feature 1: Temporal Trend Encoding (Scalar→Timestamp direction)
        # ============================================================================
        # "How does this scalar vary with time?"
        # Encode temporal aspects
        hour_encoding = self.hour_encoder(hour_onehot)    # (batch, d_model)
        dow_encoding = self.dow_encoder(dow_onehot)       # (batch, d_model)
        month_encoding = self.month_encoder(month_onehot) # (batch, d_model)

        # Multiplicative interaction: scalar * temporal_encoding
        # This captures "how does scalar vary with time"
        scalar_x_hour = scalar_embedding * hour_encoding
        scalar_x_dow = scalar_embedding * dow_encoding
        scalar_x_month = scalar_embedding * month_encoding

        # ============================================================================
        # Feature 2: Cyclical Correlation (Scalar→Timestamp direction)
        # ============================================================================
        if use_cyclical:
            # Concatenate scalar embedding with cyclical features
            scalar_with_cyclical = torch.cat([scalar_embedding, cyclical_features], dim=-1)
            scalar_cyclical = self.cyclical_mlp(scalar_with_cyclical)
        else:
            scalar_cyclical = scalar_embedding

        # ============================================================================
        # Feature 3: Rate/Trend Context
        # ============================================================================
        # Learn rate of change context from scalar + timestamp pair
        rate_context = self.rate_mlp(torch.cat([scalar_embedding, timestamp_embedding], dim=-1))

        # ============================================================================
        # Generic embedding multiplication (always included)
        # ============================================================================
        generic_mult = scalar_embedding * timestamp_embedding

        # ============================================================================
        # Feature 4: Temporal Predictor (Timestamp→Scalar direction) - NEW
        # ============================================================================
        # "Given this time (weekend? 12pm? January?), what scalar do we expect?"
        # This is critical for SP where temporal features should predict target
        temporal_pred = self.temporal_predictor(temporal_features)  # (batch, d_model)

        # Interaction: combine temporal prediction with scalar context
        # This learns "how does the scalar respond to this temporal context"
        temporal_interaction = self.temporal_scalar_interaction(
            torch.cat([temporal_pred, scalar_embedding], dim=-1)
        )

        # ============================================================================
        # Fusion: Combine all features (8 total)
        # ============================================================================
        combined = torch.cat([
            scalar_x_hour,           # Scalar→Timestamp: scalar by hour
            scalar_x_dow,            # Scalar→Timestamp: scalar by day of week
            scalar_x_month,          # Scalar→Timestamp: scalar by month
            scalar_cyclical,         # Scalar→Timestamp: cyclical patterns
            rate_context,            # Bidirectional: rate/trend
            generic_mult,            # Generic: embedding product
            temporal_pred,           # Timestamp→Scalar: time predicts scalar (NEW)
            temporal_interaction,    # Timestamp→Scalar: scalar response to time (NEW)
        ], dim=-1)  # (batch, 8 * d_model)

        # NaN ASSERTION: Check combined features before fusion
        assert not torch.isnan(combined).any(), "NaN in ScalarTimestampOps combined features before fusion!"

        result = self.output_norm(self.fusion_mlp(combined))

        # NaN ASSERTION: Check final output
        assert not torch.isnan(result).any(), "NaN in ScalarTimestampOps output!"

        return result
