#  -*- coding: utf-8 -*-
#
#  Copyright Featrix, Inc 2023-2025
#
#  Proprietary and Confidential. Unauthorized use, copying or dissemination
#  of these materials is strictly prohibited.
"""
Duration/Time Interval Relationship Operations

Type-aware relationship operations for DURATION columns.
Durations represent time intervals (not points in time), such as:
- session_duration, time_to_close, age_days, subscription_length
- response_time, processing_time, wait_time

Key distinction from TIMESTAMP:
- TIMESTAMP: A point in time (when something happened)
- DURATION: A span of time (how long something took)

Features for Duration × Duration:
- Ratio (A/B, B/A)
- Magnitude comparison (which is longer)
- Same magnitude bucket (seconds, minutes, hours, days)
- Relative difference

Features for Duration × Scalar:
- Rate computation (scalar per unit time)
- Time-weighted values

Features for Duration × Set:
- Duration patterns by category
- Category-specific duration distributions
"""
import logging
import math
import torch
import torch.nn as nn
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from featrix.neural.type_aware_ops_config import TypeAwareOpsConfig

logger = logging.getLogger(__name__)

# Duration magnitude buckets (in seconds)
DURATION_BUCKETS = [
    ("subsecond", 0, 1),
    ("seconds", 1, 60),
    ("minutes", 60, 3600),
    ("hours", 3600, 86400),
    ("days", 86400, 604800),
    ("weeks", 604800, 2592000),
    ("months", 2592000, 31536000),
    ("years", 31536000, float("inf")),
]


def get_duration_bucket(duration_seconds: torch.Tensor) -> torch.Tensor:
    """
    Get duration bucket index (0-7) for each duration.

    Args:
        duration_seconds: Duration in seconds (batch,)

    Returns:
        Bucket indices (batch,) in range [0, 7]
    """
    bucket = torch.zeros_like(duration_seconds, dtype=torch.long)
    for i, (_, low, high) in enumerate(DURATION_BUCKETS):
        mask = (duration_seconds >= low) & (duration_seconds < high)
        bucket = torch.where(mask, torch.tensor(i, device=bucket.device), bucket)
    return bucket


class DurationDurationOps(nn.Module):
    """
    Type-aware operations for DURATION × DURATION column pairs.

    Captures patterns like:
    - "Response time vs resolution time ratio"
    - "Session duration vs time to purchase"
    - "Wait time vs service time comparison"
    """

    N_DURATION_FEATURES = 12  # ratio + comparison + buckets + relative

    def __init__(
        self,
        d_model: int,
        config: Optional["TypeAwareOpsConfig"] = None,
    ):
        super().__init__()
        self.d_model = d_model
        self.config = config

        # Raw feature processing
        self.feature_mlp = nn.Sequential(
            nn.Linear(self.N_DURATION_FEATURES, d_model // 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model // 2, d_model),
        )

        # Embedding interaction
        self.interaction_mlp = nn.Sequential(
            nn.Linear(d_model * 3, d_model),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model, d_model),
        )

        # Fusion
        self.fusion_mlp = nn.Sequential(
            nn.Linear(d_model * 2, d_model),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model, d_model),
        )

        self.output_norm = nn.LayerNorm(d_model)

    def compute_duration_features(
        self,
        duration_a: torch.Tensor,  # Duration in seconds (batch,)
        duration_b: torch.Tensor,  # Duration in seconds (batch,)
    ) -> torch.Tensor:
        """
        Compute raw duration comparison features.

        Returns tensor of shape (batch, N_DURATION_FEATURES)
        """
        # Avoid division by zero
        eps = 1e-8

        # =========================================================================
        # Ratio features (2)
        # =========================================================================
        ratio_ab = torch.log1p(duration_a / (duration_b + eps))  # log(A/B)
        ratio_ba = torch.log1p(duration_b / (duration_a + eps))  # log(B/A)

        # =========================================================================
        # Magnitude comparison (3)
        # =========================================================================
        a_longer = (duration_a > duration_b).float()
        a_shorter = (duration_a < duration_b).float()
        similar_magnitude = (torch.abs(duration_a - duration_b) < (duration_a + duration_b + eps) * 0.1).float()

        # =========================================================================
        # Bucket features (3)
        # =========================================================================
        bucket_a = get_duration_bucket(duration_a)
        bucket_b = get_duration_bucket(duration_b)

        same_bucket = (bucket_a == bucket_b).float()
        bucket_diff = (bucket_a - bucket_b).float() / 7.0  # Normalize to ~[-1, 1]
        bucket_a_norm = bucket_a.float() / 7.0
        bucket_b_norm = bucket_b.float() / 7.0

        # =========================================================================
        # Relative difference (2)
        # =========================================================================
        abs_diff = torch.abs(duration_a - duration_b)
        abs_diff_norm = torch.log1p(abs_diff) / 20.0  # Normalize large differences

        relative_diff = abs_diff / (duration_a + duration_b + eps)  # 0 = same, 1 = very different

        # =========================================================================
        # Stack all features
        # =========================================================================
        features = torch.stack([
            ratio_ab,
            ratio_ba,
            a_longer,
            a_shorter,
            similar_magnitude,
            same_bucket,
            bucket_diff,
            bucket_a_norm,
            bucket_b_norm,
            abs_diff_norm,
            relative_diff,
            torch.zeros_like(duration_a),  # Padding to 12 features
        ], dim=1)

        return features

    def forward(
        self,
        duration_embedding_a: torch.Tensor,  # (batch, d_model)
        duration_embedding_b: torch.Tensor,  # (batch, d_model)
        duration_a_seconds: torch.Tensor,    # (batch,) raw duration in seconds
        duration_b_seconds: torch.Tensor,    # (batch,) raw duration in seconds
    ) -> torch.Tensor:
        """Compute relationship for Duration × Duration pair."""
        # Raw features
        features = self.compute_duration_features(duration_a_seconds, duration_b_seconds)
        feature_emb = self.feature_mlp(features)

        # Embedding interaction
        interaction = self.interaction_mlp(torch.cat([
            duration_embedding_a,
            duration_embedding_b,
            duration_embedding_a * duration_embedding_b,
        ], dim=-1))

        # Fusion
        combined = torch.cat([feature_emb, interaction], dim=-1)
        return self.output_norm(self.fusion_mlp(combined))


class DurationScalarOps(nn.Module):
    """
    Type-aware operations for DURATION × SCALAR column pairs.

    Captures patterns like:
    - "Revenue per hour of service"
    - "Cost per day of delay"
    - "Clicks per minute of session"
    """

    def __init__(
        self,
        d_model: int,
        config: Optional["TypeAwareOpsConfig"] = None,
    ):
        super().__init__()
        self.d_model = d_model
        self.config = config

        # Duration-conditioned scalar (rate computation)
        self.rate_mlp = nn.Sequential(
            nn.Linear(d_model * 2, d_model),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model, d_model),
        )

        # Scalar-conditioned duration
        self.weighted_duration_mlp = nn.Sequential(
            nn.Linear(d_model * 2, d_model),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model, d_model),
        )

        # Gating
        self.duration_gate_mlp = nn.Sequential(
            nn.Linear(d_model, d_model // 2),
            nn.ReLU(),
            nn.Linear(d_model // 2, d_model),
        )

        # Fusion
        self.fusion_mlp = nn.Sequential(
            nn.Linear(d_model * 4, d_model),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model, d_model),
        )

        self.output_norm = nn.LayerNorm(d_model)

    def forward(
        self,
        duration_embedding: torch.Tensor,  # (batch, d_model)
        scalar_embedding: torch.Tensor,    # (batch, d_model)
    ) -> torch.Tensor:
        """Compute relationship for Duration × Scalar pair."""
        # Rate computation: scalar / duration
        rate = self.rate_mlp(torch.cat([scalar_embedding, duration_embedding], dim=-1))

        # Time-weighted scalar
        weighted = self.weighted_duration_mlp(torch.cat([duration_embedding, scalar_embedding], dim=-1))

        # Gating
        gate = torch.sigmoid(self.duration_gate_mlp(duration_embedding))
        gated_scalar = scalar_embedding * gate

        # Product
        product = duration_embedding * scalar_embedding

        # Fusion
        combined = torch.cat([rate, weighted, gated_scalar, product], dim=-1)
        return self.output_norm(self.fusion_mlp(combined))


class DurationSetOps(nn.Module):
    """
    Type-aware operations for DURATION × SET column pairs.

    Captures patterns like:
    - "Premium customers have shorter wait times"
    - "Category X has longer processing duration"
    - "Status='urgent' correlates with faster resolution"
    """

    def __init__(
        self,
        d_model: int,
        config: Optional["TypeAwareOpsConfig"] = None,
    ):
        super().__init__()
        self.d_model = d_model
        self.config = config

        # Set-conditioned duration
        self.set_context_mlp = nn.Sequential(
            nn.Linear(d_model, d_model // 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model // 2, d_model),
        )

        # Duration-conditioned set
        self.duration_gate_mlp = nn.Sequential(
            nn.Linear(d_model, d_model // 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model // 2, d_model),
        )

        # Interaction
        self.interaction_mlp = nn.Sequential(
            nn.Linear(d_model * 2, d_model),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model, d_model),
        )

        # Fusion
        self.fusion_mlp = nn.Sequential(
            nn.Linear(d_model * 4, d_model),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model, d_model),
        )

        self.output_norm = nn.LayerNorm(d_model)

    def forward(
        self,
        duration_embedding: torch.Tensor,  # (batch, d_model)
        set_embedding: torch.Tensor,       # (batch, d_model)
    ) -> torch.Tensor:
        """Compute relationship for Duration × Set pair."""
        # Set context modulates duration
        set_context = self.set_context_mlp(set_embedding)
        contextualized_duration = duration_embedding * set_context

        # Duration gates set
        duration_gate = torch.sigmoid(self.duration_gate_mlp(duration_embedding))
        gated_set = set_embedding * duration_gate

        # Interaction
        interaction = self.interaction_mlp(
            torch.cat([duration_embedding, set_embedding], dim=-1)
        )

        # Product
        product = duration_embedding * set_embedding

        # Fusion
        combined = torch.cat([
            contextualized_duration,
            gated_set,
            interaction,
            product,
        ], dim=-1)

        return self.output_norm(self.fusion_mlp(combined))


class DurationTimestampOps(nn.Module):
    """
    Type-aware operations for DURATION × TIMESTAMP column pairs.

    Captures patterns like:
    - "Orders placed at night have longer shipping duration"
    - "Weekend sessions are longer than weekday"
    - "Holiday period → extended processing time"
    """

    def __init__(
        self,
        d_model: int,
        config: Optional["TypeAwareOpsConfig"] = None,
    ):
        super().__init__()
        self.d_model = d_model
        self.config = config

        # Temporal context for duration
        self.temporal_context_mlp = nn.Sequential(
            nn.Linear(d_model, d_model // 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model // 2, d_model),
        )

        # Duration context for temporal
        self.duration_context_mlp = nn.Sequential(
            nn.Linear(d_model, d_model // 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model // 2, d_model),
        )

        # Interaction
        self.interaction_mlp = nn.Sequential(
            nn.Linear(d_model * 2, d_model),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model, d_model),
        )

        # Fusion
        self.fusion_mlp = nn.Sequential(
            nn.Linear(d_model * 4, d_model),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model, d_model),
        )

        self.output_norm = nn.LayerNorm(d_model)

    def forward(
        self,
        duration_embedding: torch.Tensor,   # (batch, d_model)
        timestamp_embedding: torch.Tensor,  # (batch, d_model)
    ) -> torch.Tensor:
        """Compute relationship for Duration × Timestamp pair."""
        # Temporal context modulates duration
        temporal_context = self.temporal_context_mlp(timestamp_embedding)
        contextualized_duration = duration_embedding * temporal_context

        # Duration context modulates temporal
        duration_context = self.duration_context_mlp(duration_embedding)
        contextualized_timestamp = timestamp_embedding * duration_context

        # Interaction
        interaction = self.interaction_mlp(
            torch.cat([duration_embedding, timestamp_embedding], dim=-1)
        )

        # Product
        product = duration_embedding * timestamp_embedding

        # Fusion
        combined = torch.cat([
            contextualized_duration,
            contextualized_timestamp,
            interaction,
            product,
        ], dim=-1)

        return self.output_norm(self.fusion_mlp(combined))
