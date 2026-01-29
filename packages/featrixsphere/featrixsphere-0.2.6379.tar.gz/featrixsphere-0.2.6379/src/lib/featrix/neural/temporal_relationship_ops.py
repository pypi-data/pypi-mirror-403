#  -*- coding: utf-8 -*-
#
#  Copyright Featrix, Inc 2023-2025
#
#  Proprietary and Confidential. Unauthorized use, copying or dissemination
#  of these materials is strictly prohibited.
"""
Temporal Relationship Operations

Type-aware relationship operations for timestamp columns:
1. Timestamp × Timestamp: Compute temporal deltas (days apart, same dow, etc.)
2. String × Timestamp: Inject textual temporal representations (month names, day names)

These operations augment the generic embedding operations in DynamicRelationshipExtractor
with domain-specific temporal knowledge.

Features for Timestamp × Timestamp (31 total):
- Basic deltas: delta_days, delta_hours, abs_delta_days, order
- Alignment: same_dow, same_month, same_year, same_week, same_quarter
- Cyclical deltas: delta_dow, delta_month, delta_quarter, delta_hour_of_day
- Time-of-day: same_time_of_day, both_business_hours, both_night
- Weekend: same_weekend_status, weekday_to_weekend, weekend_to_weekday
- Day-of-month: same_dom_bucket, both_month_start, both_month_end
- Relative windows: is_same_day, is_adjacent_day, is_within_week, is_within_month
- Holiday: is_holiday_a, is_holiday_b, both_holiday, days_to_holiday_a, days_to_holiday_b
"""
import logging
import math
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Optional, Tuple

from featrix.neural.model_config import ColumnType
from featrix.neural.us_holidays import get_holiday_features

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

# Textual representations for temporal features
DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
MONTH_NAMES = ["January", "February", "March", "April", "May", "June",
               "July", "August", "September", "October", "November", "December"]
QUARTER_NAMES = ["Q1", "Q2", "Q3", "Q4"]
TIME_OF_DAY_NAMES = ["Night", "Morning", "Afternoon", "Evening"]  # 0-5, 6-11, 12-17, 18-23
SEASON_NAMES = ["Winter", "Spring", "Summer", "Fall"]  # Based on month
WEEKEND_NAMES = ["Weekday", "Weekend"]


class TemporalRelationshipOps(nn.Module):
    """
    Type-aware temporal relationship operations.

    For timestamp × timestamp pairs:
    - Computes raw temporal deltas (days, hours, etc.)
    - Computes cycle alignment (same dow, same month, etc.)
    - Projects through learned MLP to d_model

    For string × timestamp pairs:
    - Generates textual representations of temporal features
    - Uses shared text encoding to bridge string and timestamp semantics
    """

    def __init__(
        self,
        d_model: int,
        col_types: Dict[str, ColumnType],
        col_names_in_order: List[str],
        string_encoder_fn: Optional[callable] = None,
    ):
        """
        Args:
            d_model: Model dimension
            col_types: Dict mapping column name to ColumnType
            col_names_in_order: Ordered list of column names
            string_encoder_fn: Function to encode text strings (from StringEncoder)
        """
        super().__init__()
        self.d_model = d_model
        self.col_types = col_types
        self.col_names = col_names_in_order
        self.string_encoder_fn = string_encoder_fn

        # Build column index -> type mapping
        self.col_idx_to_type: Dict[int, ColumnType] = {}
        for idx, name in enumerate(col_names_in_order):
            self.col_idx_to_type[idx] = col_types.get(name, ColumnType.FREE_STRING)

        # Identify timestamp and string column indices
        self.timestamp_cols = [
            idx for idx, ctype in self.col_idx_to_type.items()
            if ctype == ColumnType.TIMESTAMP
        ]
        self.string_cols = [
            idx for idx, ctype in self.col_idx_to_type.items()
            if ctype == ColumnType.FREE_STRING
        ]

        # Count timestamp pairs
        n_ts_pairs = len(self.timestamp_cols) * (len(self.timestamp_cols) - 1) // 2
        n_str_ts_pairs = len(self.string_cols) * len(self.timestamp_cols)

        if n_ts_pairs > 0 or n_str_ts_pairs > 0:
            logger.info(f"🕐 TemporalRelationshipOps: {len(self.timestamp_cols)} timestamp cols, "
                       f"{len(self.string_cols)} string cols")
            logger.info(f"   Timestamp×Timestamp pairs: {n_ts_pairs}")
            logger.info(f"   String×Timestamp pairs: {n_str_ts_pairs}")

        # ============================================================================
        # Timestamp × Timestamp: Temporal delta features (31 total)
        # ============================================================================
        # Basic deltas (4):
        #   delta_days, delta_hours, abs_delta_days, order
        # Alignment (5):
        #   same_dow, same_month, same_year, same_week, same_quarter
        # Cyclical deltas (4):
        #   delta_dow, delta_month, delta_quarter, delta_hour_of_day
        # Time-of-day alignment (3):
        #   same_time_of_day, both_business_hours, both_night
        # Weekend patterns (3):
        #   same_weekend_status, weekday_to_weekend, weekend_to_weekday
        # Day-of-month patterns (3):
        #   same_dom_bucket, both_month_start, both_month_end
        # Relative time windows (4):
        #   is_same_day, is_adjacent_day, is_within_week, is_within_month
        # Holiday features (5):
        #   is_holiday_a, is_holiday_b, both_holiday, days_to_holiday_a, days_to_holiday_b
        self.n_temporal_delta_features = 31

        self.temporal_delta_mlp = nn.Sequential(
            nn.Linear(self.n_temporal_delta_features, d_model),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model, d_model),
        )

        # ============================================================================
        # String × Timestamp: Textual temporal embeddings
        # ============================================================================
        # We'll create embeddings for temporal text tokens that can be compared
        # with string embeddings. These are learned embeddings, not from StringEncoder.
        # This is simpler and avoids dependency on StringEncoder at init time.

        # Embed day names (7 days)
        self.day_name_embeddings = nn.Embedding(7, d_model)
        # Embed month names (12 months)
        self.month_name_embeddings = nn.Embedding(12, d_model)
        # Embed quarter names (4 quarters)
        self.quarter_embeddings = nn.Embedding(4, d_model)
        # Embed time of day (4 periods)
        self.time_of_day_embeddings = nn.Embedding(4, d_model)
        # Embed weekend/weekday (2)
        self.weekend_embeddings = nn.Embedding(2, d_model)

        # MLP to combine string embedding with temporal text embeddings
        # Input: string_emb (d_model) + temporal_text_emb (d_model)
        self.string_timestamp_mlp = nn.Sequential(
            nn.Linear(d_model * 2, d_model),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model, d_model),
        )

    def compute_timestamp_timestamp_features(
        self,
        raw_features_a: torch.Tensor,  # (batch, 12) raw timestamp features
        raw_features_b: torch.Tensor,  # (batch, 12) raw timestamp features
    ) -> torch.Tensor:
        """
        Compute temporal delta features between two timestamps.

        Returns 31 features covering:
        - Basic deltas and order
        - Alignment (same dow, month, year, week, quarter)
        - Cyclical deltas (dow, month, quarter, hour)
        - Time-of-day patterns
        - Weekend patterns
        - Day-of-month patterns
        - Relative time windows
        - Holiday features

        Args:
            raw_features_a: Raw 12-feature timestamp tensor for column A
            raw_features_b: Raw 12-feature timestamp tensor for column B

        Returns:
            Tensor of shape (batch, 31)
        """
        # CRITICAL: Sanitize NaN/Inf values BEFORE any operations
        # NaN in raw_features causes gradient explosions and training failure
        raw_features_a = torch.nan_to_num(raw_features_a, nan=0.0, posinf=0.0, neginf=0.0)
        raw_features_b = torch.nan_to_num(raw_features_b, nan=0.0, posinf=0.0, neginf=0.0)

        batch_size = raw_features_a.shape[0]
        device = raw_features_a.device

        # Extract relevant features
        year_a = raw_features_a[:, FEAT_YEAR]
        year_b = raw_features_b[:, FEAT_YEAR]
        doy_a = raw_features_a[:, FEAT_DAY_OF_YEAR]  # Day of year (1-366)
        doy_b = raw_features_b[:, FEAT_DAY_OF_YEAR]
        hour_a = raw_features_a[:, FEAT_HOURS]
        hour_b = raw_features_b[:, FEAT_HOURS]
        dow_a = raw_features_a[:, FEAT_DAY_OF_WEEK]
        dow_b = raw_features_b[:, FEAT_DAY_OF_WEEK]
        month_a = raw_features_a[:, FEAT_MONTH]
        month_b = raw_features_b[:, FEAT_MONTH]
        week_a = raw_features_a[:, FEAT_WEEK_OF_YEAR]
        week_b = raw_features_b[:, FEAT_WEEK_OF_YEAR]
        dom_a = raw_features_a[:, FEAT_DAY_OF_MONTH]  # Day of month (1-31)
        dom_b = raw_features_b[:, FEAT_DAY_OF_MONTH]

        # =========================================================================
        # Basic deltas (4 features)
        # =========================================================================
        # Approximate delta_days: (year_diff * 365) + (doy_diff)
        delta_days = (year_a - year_b) * 365 + (doy_a - doy_b)
        delta_hours = delta_days * 24 + (hour_a - hour_b)
        abs_delta_days = torch.abs(delta_days)

        # Temporal order: A before B = 1, same = 0, B before A = -1
        order = torch.sign(delta_days)

        # Normalize continuous features
        delta_days_norm = torch.sign(delta_days) * torch.log1p(torch.abs(delta_days))
        delta_hours_norm = torch.sign(delta_hours) * torch.log1p(torch.abs(delta_hours))
        abs_delta_days_norm = torch.log1p(abs_delta_days)

        # =========================================================================
        # Alignment features (5 features)
        # =========================================================================
        dow_a_int = dow_a.round().long()
        dow_b_int = dow_b.round().long()
        month_a_int = month_a.round().long()
        month_b_int = month_b.round().long()

        same_dow = (dow_a_int == dow_b_int).float()
        same_month = (month_a_int == month_b_int).float()
        same_year = (year_a.round() == year_b.round()).float()
        same_week = (week_a.round() == week_b.round()).float()

        # Quarter: months 1-3 = Q1, 4-6 = Q2, etc.
        quarter_a = ((month_a_int - 1) // 3).clamp(0, 3)
        quarter_b = ((month_b_int - 1) // 3).clamp(0, 3)
        same_quarter = (quarter_a == quarter_b).float()

        # =========================================================================
        # Cyclical delta features (4 features)
        # =========================================================================
        # Delta DOW: circular distance on 7-day cycle, normalized to [-0.5, 0.5]
        delta_dow_raw = (dow_a - dow_b) % 7
        delta_dow = torch.where(delta_dow_raw > 3.5, delta_dow_raw - 7, delta_dow_raw) / 7.0

        # Delta month: circular distance on 12-month cycle, normalized
        delta_month_raw = ((month_a - month_b) % 12)
        delta_month = torch.where(delta_month_raw > 6, delta_month_raw - 12, delta_month_raw) / 12.0

        # Delta quarter: circular distance on 4-quarter cycle
        delta_quarter_raw = ((quarter_a - quarter_b) % 4).float()
        delta_quarter = torch.where(delta_quarter_raw > 2, delta_quarter_raw - 4, delta_quarter_raw) / 4.0

        # Delta hour of day: circular distance on 24-hour cycle
        delta_hour_raw = (hour_a - hour_b) % 24
        delta_hour_of_day = torch.where(delta_hour_raw > 12, delta_hour_raw - 24, delta_hour_raw) / 24.0

        # =========================================================================
        # Time-of-day alignment features (3 features)
        # =========================================================================
        # Time of day buckets: Night (0-5), Morning (6-11), Afternoon (12-17), Evening (18-23)
        tod_a = (hour_a // 6).long().clamp(0, 3)
        tod_b = (hour_b // 6).long().clamp(0, 3)
        same_time_of_day = (tod_a == tod_b).float()

        # Business hours: 9am-5pm (hours 9-16 inclusive)
        is_business_a = ((hour_a >= 9) & (hour_a <= 16)).float()
        is_business_b = ((hour_b >= 9) & (hour_b <= 16)).float()
        both_business_hours = (is_business_a * is_business_b)

        # Night hours: 10pm-6am (hours 22-23 or 0-5)
        is_night_a = ((hour_a >= 22) | (hour_a <= 5)).float()
        is_night_b = ((hour_b >= 22) | (hour_b <= 5)).float()
        both_night = (is_night_a * is_night_b)

        # =========================================================================
        # Weekend patterns (3 features)
        # =========================================================================
        is_weekend_a = (dow_a_int >= 5).float()  # Saturday=5, Sunday=6
        is_weekend_b = (dow_b_int >= 5).float()

        same_weekend_status = ((is_weekend_a == is_weekend_b)).float()
        weekday_to_weekend = ((1 - is_weekend_a) * is_weekend_b)  # A weekday, B weekend
        weekend_to_weekday = (is_weekend_a * (1 - is_weekend_b))  # A weekend, B weekday

        # =========================================================================
        # Day-of-month patterns (3 features)
        # =========================================================================
        # DOM buckets: 1-7, 8-14, 15-21, 22-28, 29-31
        dom_bucket_a = ((dom_a.round().long() - 1) // 7).clamp(0, 4)
        dom_bucket_b = ((dom_b.round().long() - 1) // 7).clamp(0, 4)

        same_dom_bucket = (dom_bucket_a == dom_bucket_b).float()
        both_month_start = ((dom_bucket_a == 0) & (dom_bucket_b == 0)).float()  # Both in days 1-7
        both_month_end = ((dom_bucket_a >= 3) & (dom_bucket_b >= 3)).float()    # Both in days 22+

        # =========================================================================
        # Relative time windows (4 features)
        # =========================================================================
        is_same_day = (abs_delta_days < 1).float()
        is_adjacent_day = ((abs_delta_days >= 1) & (abs_delta_days < 2)).float()
        is_within_week = (abs_delta_days <= 7).float()
        is_within_month = (abs_delta_days <= 30).float()

        # =========================================================================
        # Holiday features (5 features)
        # =========================================================================
        # Get holiday info for timestamp A
        is_holiday_a, days_to_holiday_a, _ = get_holiday_features(
            year_a, month_a, dom_a, doy_a, max_holiday_distance=30
        )
        # Get holiday info for timestamp B
        is_holiday_b, days_to_holiday_b, _ = get_holiday_features(
            year_b, month_b, dom_b, doy_b, max_holiday_distance=30
        )

        both_holiday = (is_holiday_a * is_holiday_b)

        # =========================================================================
        # Stack all 31 features
        # =========================================================================
        features = torch.stack([
            # Basic deltas (4)
            delta_days_norm,
            delta_hours_norm,
            abs_delta_days_norm,
            order,
            # Alignment (5)
            same_dow,
            same_month,
            same_year,
            same_week,
            same_quarter,
            # Cyclical deltas (4)
            delta_dow,
            delta_month,
            delta_quarter,
            delta_hour_of_day,
            # Time-of-day (3)
            same_time_of_day,
            both_business_hours,
            both_night,
            # Weekend (3)
            same_weekend_status,
            weekday_to_weekend,
            weekend_to_weekday,
            # Day-of-month (3)
            same_dom_bucket,
            both_month_start,
            both_month_end,
            # Relative windows (4)
            is_same_day,
            is_adjacent_day,
            is_within_week,
            is_within_month,
            # Holidays (5)
            is_holiday_a,
            is_holiday_b,
            both_holiday,
            days_to_holiday_a,
            days_to_holiday_b,
        ], dim=1)  # (batch, 31)

        # NaN ASSERTION: Check temporal features before returning
        assert not torch.isnan(features).any(), "NaN in TemporalRelationshipOps.compute_timestamp_timestamp_features output!"

        return features

    def compute_timestamp_timestamp_relationship(
        self,
        raw_features_a: torch.Tensor,
        raw_features_b: torch.Tensor,
    ) -> torch.Tensor:
        """
        Compute relationship token for timestamp × timestamp pair.

        Args:
            raw_features_a: Raw 12-feature timestamp tensor for column A
            raw_features_b: Raw 12-feature timestamp tensor for column B

        Returns:
            Relationship embedding of shape (batch, d_model)
        """
        features = self.compute_timestamp_timestamp_features(raw_features_a, raw_features_b)
        return self.temporal_delta_mlp(features)

    def get_temporal_text_embeddings(
        self,
        raw_features: torch.Tensor,  # (batch, 12) raw timestamp features
    ) -> Dict[str, torch.Tensor]:
        """
        Get textual temporal embeddings for timestamp features.

        Args:
            raw_features: Raw 12-feature timestamp tensor

        Returns:
            Dict with keys: 'day_name', 'month_name', 'quarter', 'time_of_day', 'weekend'
            Each value is (batch, d_model) embedding
        """
        # CRITICAL: Sanitize NaN/Inf values BEFORE any operations
        # NaN in raw_features causes gradient explosions and training failure
        raw_features = torch.nan_to_num(raw_features, nan=0.0, posinf=0.0, neginf=0.0)

        batch_size = raw_features.shape[0]
        device = raw_features.device

        # Extract and convert to indices
        dow = raw_features[:, FEAT_DAY_OF_WEEK].round().long().clamp(0, 6)
        month = (raw_features[:, FEAT_MONTH].round().long() - 1).clamp(0, 11)  # 1-12 -> 0-11
        hour = raw_features[:, FEAT_HOURS].round().long().clamp(0, 23)

        # Quarter from month (0-2 -> Q1, 3-5 -> Q2, etc.)
        quarter = (month // 3).clamp(0, 3)

        # Time of day from hour (0-5 -> Night, 6-11 -> Morning, etc.)
        time_of_day = (hour // 6).clamp(0, 3)

        # Weekend from day of week (5, 6 = weekend)
        is_weekend = (dow >= 5).long()

        return {
            'day_name': self.day_name_embeddings(dow),
            'month_name': self.month_name_embeddings(month),
            'quarter': self.quarter_embeddings(quarter),
            'time_of_day': self.time_of_day_embeddings(time_of_day),
            'weekend': self.weekend_embeddings(is_weekend),
        }

    def compute_string_timestamp_relationship(
        self,
        string_embedding: torch.Tensor,  # (batch, d_model) from StringEncoder
        raw_timestamp_features: torch.Tensor,  # (batch, 12) raw timestamp features
        temporal_aspect: str = 'all',  # 'day_name', 'month_name', 'quarter', 'time_of_day', 'weekend', or 'all'
    ) -> torch.Tensor:
        """
        Compute relationship token for string × timestamp pair.

        This bridges the semantic gap by comparing the string embedding
        with textual representations of the timestamp's temporal features.

        Args:
            string_embedding: Embedding from StringEncoder
            raw_timestamp_features: Raw 12-feature timestamp tensor
            temporal_aspect: Which temporal text to use

        Returns:
            Relationship embedding of shape (batch, d_model)
        """
        temporal_embs = self.get_temporal_text_embeddings(raw_timestamp_features)

        if temporal_aspect == 'all':
            # Combine all temporal text embeddings (mean pool)
            all_embs = torch.stack(list(temporal_embs.values()), dim=0)  # (5, batch, d_model)
            temporal_text_emb = all_embs.mean(dim=0)  # (batch, d_model)
        else:
            temporal_text_emb = temporal_embs.get(temporal_aspect, temporal_embs['day_name'])

        # Concatenate string embedding with temporal text embedding
        combined = torch.cat([string_embedding, temporal_text_emb], dim=-1)  # (batch, d_model * 2)
        return self.string_timestamp_mlp(combined)

    def is_timestamp_pair(self, col_i: int, col_j: int) -> bool:
        """Check if both columns are timestamps."""
        return (
            self.col_idx_to_type.get(col_i) == ColumnType.TIMESTAMP and
            self.col_idx_to_type.get(col_j) == ColumnType.TIMESTAMP
        )

    def is_string_timestamp_pair(self, col_i: int, col_j: int) -> Tuple[bool, Optional[int], Optional[int]]:
        """
        Check if one column is string and other is timestamp.

        Returns:
            (is_str_ts_pair, string_col_idx, timestamp_col_idx)
        """
        type_i = self.col_idx_to_type.get(col_i)
        type_j = self.col_idx_to_type.get(col_j)

        if type_i == ColumnType.FREE_STRING and type_j == ColumnType.TIMESTAMP:
            return True, col_i, col_j
        elif type_i == ColumnType.TIMESTAMP and type_j == ColumnType.FREE_STRING:
            return True, col_j, col_i
        else:
            return False, None, None
