#  -*- coding: utf-8 -*-
#
#  Copyright Featrix, Inc 2023-2025
#
#  Proprietary and Confidential. Unauthorized use, copying or dissemination
#  of these materials is strictly prohibited.
"""
Geographic Coordinate Relationship Operations

Type-aware relationship operations for GEO_COORD columns.
Supports:
1. Geo × Geo: Distance, bearing, same-region detection
2. Geo × Set: Regional clustering × category patterns
3. Geo × Scalar: Distance from centroid × value correlation
4. Geo × Timestamp: Location × time patterns (timezone, seasonality by latitude)

Features for Geo × Geo:
- Haversine distance (great circle distance in km)
- Initial bearing (compass direction A→B)
- Same-region detection at multiple precision levels
- North/South, East/West relative positioning
- Distance buckets (same location, walking, driving, flight)
"""
import logging
import math
import torch
import torch.nn as nn
from typing import Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from featrix.neural.type_aware_ops_config import TypeAwareOpsConfig

logger = logging.getLogger(__name__)

# Earth's radius in kilometers
EARTH_RADIUS_KM = 6371.0


def haversine_distance(
    lat1: torch.Tensor,
    lon1: torch.Tensor,
    lat2: torch.Tensor,
    lon2: torch.Tensor,
) -> torch.Tensor:
    """
    Compute haversine (great circle) distance between two points.

    Args:
        lat1, lon1: Coordinates of point A in degrees (batch,)
        lat2, lon2: Coordinates of point B in degrees (batch,)

    Returns:
        Distance in kilometers (batch,)
    """
    # Convert to radians
    lat1_rad = torch.deg2rad(lat1)
    lat2_rad = torch.deg2rad(lat2)
    lon1_rad = torch.deg2rad(lon1)
    lon2_rad = torch.deg2rad(lon2)

    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    # Haversine formula
    a = torch.sin(dlat / 2) ** 2 + torch.cos(lat1_rad) * torch.cos(lat2_rad) * torch.sin(dlon / 2) ** 2
    c = 2 * torch.asin(torch.sqrt(a.clamp(0, 1)))  # clamp for numerical stability

    return EARTH_RADIUS_KM * c


def compute_bearing(
    lat1: torch.Tensor,
    lon1: torch.Tensor,
    lat2: torch.Tensor,
    lon2: torch.Tensor,
) -> torch.Tensor:
    """
    Compute initial bearing (forward azimuth) from point A to point B.

    Args:
        lat1, lon1: Coordinates of point A in degrees (batch,)
        lat2, lon2: Coordinates of point B in degrees (batch,)

    Returns:
        Bearing in degrees [0, 360) (batch,)
    """
    lat1_rad = torch.deg2rad(lat1)
    lat2_rad = torch.deg2rad(lat2)
    dlon_rad = torch.deg2rad(lon2 - lon1)

    x = torch.sin(dlon_rad) * torch.cos(lat2_rad)
    y = torch.cos(lat1_rad) * torch.sin(lat2_rad) - torch.sin(lat1_rad) * torch.cos(lat2_rad) * torch.cos(dlon_rad)

    bearing = torch.atan2(x, y)
    bearing_deg = torch.rad2deg(bearing)

    # Normalize to [0, 360)
    return (bearing_deg + 360) % 360


def compute_geohash_match(
    lat1: torch.Tensor,
    lon1: torch.Tensor,
    lat2: torch.Tensor,
    lon2: torch.Tensor,
    precision: int,
) -> torch.Tensor:
    """
    Check if two coordinates fall in the same geohash cell at given precision.

    This is an approximation using grid cells rather than true geohash encoding.

    Args:
        lat1, lon1: Coordinates of point A in degrees
        lat2, lon2: Coordinates of point B in degrees
        precision: Grid precision (1=coarse ~1000km, 5=fine ~1km)

    Returns:
        Binary tensor (batch,) - 1.0 if same cell, 0.0 otherwise
    """
    # Grid cell sizes (approximate)
    # precision 1: ~10 degrees (~1000km)
    # precision 2: ~2.5 degrees (~250km)
    # precision 3: ~0.6 degrees (~60km)
    # precision 4: ~0.15 degrees (~15km)
    # precision 5: ~0.04 degrees (~4km)
    cell_size = 10.0 / (4 ** (precision - 1))

    # Compute grid cells
    cell1_lat = (lat1 / cell_size).floor()
    cell1_lon = (lon1 / cell_size).floor()
    cell2_lat = (lat2 / cell_size).floor()
    cell2_lon = (lon2 / cell_size).floor()

    same_cell = ((cell1_lat == cell2_lat) & (cell1_lon == cell2_lon)).float()
    return same_cell


class GeoGeoOps(nn.Module):
    """
    Type-aware operations for GEO_COORD × GEO_COORD column pairs.

    Computes relationship embeddings that capture spatial relationships:
    - How far apart are the two locations?
    - What direction is B from A?
    - Are they in the same region?
    - What distance bucket (walking, driving, flight)?
    """

    # Feature dimensions
    N_GEO_FEATURES = 16  # distance + bearing + same_region(5) + relative_pos(4) + buckets(5)

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
        # Raw Feature Processing
        # ============================================================================
        # Process raw geo features (distance, bearing, region match, etc.)
        self.geo_feature_mlp = nn.Sequential(
            nn.Linear(self.N_GEO_FEATURES, d_model // 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model // 2, d_model),
        )

        # ============================================================================
        # Embedding Interaction
        # ============================================================================
        # Combine geo embeddings with learned interactions
        self.interaction_mlp = nn.Sequential(
            nn.Linear(d_model * 3, d_model),  # geo_a + geo_b + product
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model, d_model),
        )

        # ============================================================================
        # Fusion
        # ============================================================================
        # Combine feature-based and embedding-based representations
        self.fusion_mlp = nn.Sequential(
            nn.Linear(d_model * 2, d_model),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model, d_model),
        )

        # Output normalization
        self.output_norm = nn.LayerNorm(d_model)

        logger.debug(f"   GeoGeoOps initialized: d_model={d_model}")

    def compute_geo_features(
        self,
        lat_a: torch.Tensor,
        lon_a: torch.Tensor,
        lat_b: torch.Tensor,
        lon_b: torch.Tensor,
    ) -> torch.Tensor:
        """
        Compute raw geographic features between two coordinate pairs.

        Args:
            lat_a, lon_a: Coordinates of point A in degrees (batch,)
            lat_b, lon_b: Coordinates of point B in degrees (batch,)

        Returns:
            Feature tensor of shape (batch, N_GEO_FEATURES)
        """
        device = lat_a.device

        # =========================================================================
        # Distance features (1 feature)
        # =========================================================================
        distance_km = haversine_distance(lat_a, lon_a, lat_b, lon_b)
        # Log-normalize distance (most distances are < 1000km, max ~20000km)
        distance_norm = torch.log1p(distance_km) / 10.0  # Normalize to ~[0, 1]

        # =========================================================================
        # Bearing features (1 feature)
        # =========================================================================
        bearing = compute_bearing(lat_a, lon_a, lat_b, lon_b)
        # Normalize to [0, 1]
        bearing_norm = bearing / 360.0

        # =========================================================================
        # Same-region features at multiple precisions (5 features)
        # =========================================================================
        same_region_1 = compute_geohash_match(lat_a, lon_a, lat_b, lon_b, precision=1)  # ~1000km
        same_region_2 = compute_geohash_match(lat_a, lon_a, lat_b, lon_b, precision=2)  # ~250km
        same_region_3 = compute_geohash_match(lat_a, lon_a, lat_b, lon_b, precision=3)  # ~60km
        same_region_4 = compute_geohash_match(lat_a, lon_a, lat_b, lon_b, precision=4)  # ~15km
        same_region_5 = compute_geohash_match(lat_a, lon_a, lat_b, lon_b, precision=5)  # ~4km

        # =========================================================================
        # Relative position features (4 features)
        # =========================================================================
        # Is B north of A?
        is_north = (lat_b > lat_a).float()
        # Is B east of A?
        is_east = (lon_b > lon_a).float()
        # Latitude difference (normalized)
        lat_diff = (lat_b - lat_a) / 180.0  # [-1, 1]
        # Longitude difference (normalized)
        lon_diff = (lon_b - lon_a) / 360.0  # [-1, 1] (approximately)

        # =========================================================================
        # Distance bucket features (5 features)
        # =========================================================================
        # Same location (<100m)
        is_same_location = (distance_km < 0.1).float()
        # Walking distance (<2km)
        is_walking = ((distance_km >= 0.1) & (distance_km < 2)).float()
        # Driving distance (2-50km)
        is_driving = ((distance_km >= 2) & (distance_km < 50)).float()
        # Regional (50-500km)
        is_regional = ((distance_km >= 50) & (distance_km < 500)).float()
        # Flight distance (>500km)
        is_flight = (distance_km >= 500).float()

        # =========================================================================
        # Stack all features
        # =========================================================================
        features = torch.stack([
            distance_norm,
            bearing_norm,
            same_region_1,
            same_region_2,
            same_region_3,
            same_region_4,
            same_region_5,
            is_north,
            is_east,
            lat_diff,
            lon_diff,
            is_same_location,
            is_walking,
            is_driving,
            is_regional,
            is_flight,
        ], dim=1)  # (batch, 16)

        return features

    def forward(
        self,
        geo_embedding_a: torch.Tensor,  # (batch, d_model) - encoded geo column A
        geo_embedding_b: torch.Tensor,  # (batch, d_model) - encoded geo column B
        lat_a: torch.Tensor,            # (batch,) - raw latitude A
        lon_a: torch.Tensor,            # (batch,) - raw longitude A
        lat_b: torch.Tensor,            # (batch,) - raw latitude B
        lon_b: torch.Tensor,            # (batch,) - raw longitude B
    ) -> torch.Tensor:
        """
        Compute relationship embedding for Geo × Geo pair.

        Args:
            geo_embedding_a: Embedding from GeoEncoder for column A
            geo_embedding_b: Embedding from GeoEncoder for column B
            lat_a, lon_a: Raw coordinates for column A
            lat_b, lon_b: Raw coordinates for column B

        Returns:
            Relationship embedding of shape (batch, d_model)
        """
        # ============================================================================
        # Raw Feature Processing
        # ============================================================================
        geo_features = self.compute_geo_features(lat_a, lon_a, lat_b, lon_b)
        feature_embedding = self.geo_feature_mlp(geo_features)

        # ============================================================================
        # Embedding Interaction
        # ============================================================================
        interaction_input = torch.cat([
            geo_embedding_a,
            geo_embedding_b,
            geo_embedding_a * geo_embedding_b,
        ], dim=-1)
        interaction_embedding = self.interaction_mlp(interaction_input)

        # ============================================================================
        # Fusion
        # ============================================================================
        combined = torch.cat([
            feature_embedding,
            interaction_embedding,
        ], dim=-1)

        return self.output_norm(self.fusion_mlp(combined))


class GeoSetOps(nn.Module):
    """
    Type-aware operations for GEO_COORD × SET column pairs.

    Captures patterns like:
    - "Urban areas → higher delivery density category"
    - "Coastal regions → seafood restaurant category"
    - "High-altitude locations → outdoor equipment category"
    """

    def __init__(
        self,
        d_model: int,
        config: Optional["TypeAwareOpsConfig"] = None,
    ):
        super().__init__()
        self.d_model = d_model
        self.config = config

        # Geo-conditioned set gating
        self.geo_gate_mlp = nn.Sequential(
            nn.Linear(d_model, d_model // 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model // 2, d_model),
        )

        # Set-conditioned geo interpretation
        self.set_context_mlp = nn.Sequential(
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
        geo_embedding: torch.Tensor,  # (batch, d_model)
        set_embedding: torch.Tensor,  # (batch, d_model)
    ) -> torch.Tensor:
        """Compute relationship for Geo × Set pair."""
        # Geo gates set
        geo_gate = torch.sigmoid(self.geo_gate_mlp(geo_embedding))
        gated_set = set_embedding * geo_gate

        # Set contextualizes geo
        set_context = self.set_context_mlp(set_embedding)
        contextualized_geo = geo_embedding * set_context

        # Interaction
        interaction = self.interaction_mlp(
            torch.cat([geo_embedding, set_embedding], dim=-1)
        )

        # Product
        product = geo_embedding * set_embedding

        # Fusion
        combined = torch.cat([
            gated_set,
            contextualized_geo,
            interaction,
            product,
        ], dim=-1)

        return self.output_norm(self.fusion_mlp(combined))


class GeoScalarOps(nn.Module):
    """
    Type-aware operations for GEO_COORD × SCALAR column pairs.

    Captures patterns like:
    - "Distance from city center → property price"
    - "Latitude → average temperature"
    - "Elevation → oxygen level"
    """

    def __init__(
        self,
        d_model: int,
        config: Optional["TypeAwareOpsConfig"] = None,
    ):
        super().__init__()
        self.d_model = d_model
        self.config = config

        # Geo-conditioned scalar scaling
        self.geo_scale_mlp = nn.Sequential(
            nn.Linear(d_model, d_model // 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model // 2, d_model),
        )

        # Scalar-conditioned geo gating
        self.scalar_gate_mlp = nn.Sequential(
            nn.Linear(d_model, d_model // 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model // 2, d_model),
        )

        # Spatial-scalar correlation
        self.correlation_mlp = nn.Sequential(
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
        geo_embedding: torch.Tensor,    # (batch, d_model)
        scalar_embedding: torch.Tensor, # (batch, d_model)
    ) -> torch.Tensor:
        """Compute relationship for Geo × Scalar pair."""
        # Geo scales scalar
        geo_scale = self.geo_scale_mlp(geo_embedding)
        scaled_scalar = scalar_embedding * geo_scale

        # Scalar gates geo
        scalar_gate = torch.sigmoid(self.scalar_gate_mlp(scalar_embedding))
        gated_geo = geo_embedding * scalar_gate

        # Correlation
        correlation = self.correlation_mlp(
            torch.cat([geo_embedding, scalar_embedding], dim=-1)
        )

        # Product
        product = geo_embedding * scalar_embedding

        # Fusion
        combined = torch.cat([
            scaled_scalar,
            gated_geo,
            correlation,
            product,
        ], dim=-1)

        return self.output_norm(self.fusion_mlp(combined))


class GeoTimestampOps(nn.Module):
    """
    Type-aware operations for GEO_COORD × TIMESTAMP column pairs.

    Captures patterns like:
    - "Location timezone alignment with event time"
    - "Latitude × season → daylight hours"
    - "Coastal location × hurricane season"
    """

    def __init__(
        self,
        d_model: int,
        config: Optional["TypeAwareOpsConfig"] = None,
    ):
        super().__init__()
        self.d_model = d_model
        self.config = config

        # Geo-conditioned temporal interpretation
        self.geo_temporal_mlp = nn.Sequential(
            nn.Linear(d_model, d_model // 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model // 2, d_model),
        )

        # Temporal-conditioned geo interpretation
        self.temporal_geo_mlp = nn.Sequential(
            nn.Linear(d_model, d_model // 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model // 2, d_model),
        )

        # Spatiotemporal interaction
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
        geo_embedding: torch.Tensor,       # (batch, d_model)
        timestamp_embedding: torch.Tensor, # (batch, d_model)
    ) -> torch.Tensor:
        """Compute relationship for Geo × Timestamp pair."""
        # Geo modulates temporal
        geo_temporal = self.geo_temporal_mlp(geo_embedding)
        modulated_temporal = timestamp_embedding * geo_temporal

        # Temporal modulates geo
        temporal_geo = self.temporal_geo_mlp(timestamp_embedding)
        modulated_geo = geo_embedding * temporal_geo

        # Interaction
        interaction = self.interaction_mlp(
            torch.cat([geo_embedding, timestamp_embedding], dim=-1)
        )

        # Product
        product = geo_embedding * timestamp_embedding

        # Fusion
        combined = torch.cat([
            modulated_temporal,
            modulated_geo,
            interaction,
            product,
        ], dim=-1)

        return self.output_norm(self.fusion_mlp(combined))
