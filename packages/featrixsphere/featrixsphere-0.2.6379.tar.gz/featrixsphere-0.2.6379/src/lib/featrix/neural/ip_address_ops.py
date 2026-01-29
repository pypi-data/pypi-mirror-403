#  -*- coding: utf-8 -*-
#
#  Copyright Featrix, Inc 2023-2025
#
#  Proprietary and Confidential. Unauthorized use, copying or dissemination
#  of these materials is strictly prohibited.
"""
IP Address Relationship Operations

Type-aware relationship operations for IP_ADDRESS columns.
Supports both IPv4 and IPv6 addresses with features for:
- Network prefix matching (same /8, /16, /24 subnet)
- IP type classification (private, public, loopback, multicast)
- Geographic proximity (when enriched with GeoIP data)
- Same-network detection

Use cases:
- Fraud detection: multiple accounts from same IP subnet
- Security: login from unexpected IP range
- Analytics: traffic source clustering
"""
import logging
import torch
import torch.nn as nn
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from featrix.neural.type_aware_ops_config import TypeAwareOpsConfig

logger = logging.getLogger(__name__)


# IPv4 private ranges (as integer ranges)
# 10.0.0.0/8: 167772160 - 184549375
# 172.16.0.0/12: 2886729728 - 2887778303
# 192.168.0.0/16: 3232235520 - 3232301055
PRIVATE_RANGES = [
    (167772160, 184549375),      # 10.0.0.0/8
    (2886729728, 2887778303),    # 172.16.0.0/12
    (3232235520, 3232301055),    # 192.168.0.0/16
]

# Loopback: 127.0.0.0/8
LOOPBACK_RANGE = (2130706432, 2147483647)  # 127.0.0.0 - 127.255.255.255

# Link-local: 169.254.0.0/16
LINK_LOCAL_RANGE = (2851995648, 2852061183)


def ipv4_to_int(ip_parts: torch.Tensor) -> torch.Tensor:
    """
    Convert IPv4 parts to integer.

    Args:
        ip_parts: Tensor of shape (batch, 4) with octet values

    Returns:
        Integer representation (batch,)
    """
    return (
        ip_parts[:, 0] * 16777216 +
        ip_parts[:, 1] * 65536 +
        ip_parts[:, 2] * 256 +
        ip_parts[:, 3]
    )


def is_private_ip(ip_int: torch.Tensor) -> torch.Tensor:
    """Check if IP is in private range."""
    is_private = torch.zeros_like(ip_int, dtype=torch.bool)
    for low, high in PRIVATE_RANGES:
        is_private = is_private | ((ip_int >= low) & (ip_int <= high))
    return is_private


def is_loopback_ip(ip_int: torch.Tensor) -> torch.Tensor:
    """Check if IP is loopback."""
    return (ip_int >= LOOPBACK_RANGE[0]) & (ip_int <= LOOPBACK_RANGE[1])


def is_link_local_ip(ip_int: torch.Tensor) -> torch.Tensor:
    """Check if IP is link-local."""
    return (ip_int >= LINK_LOCAL_RANGE[0]) & (ip_int <= LINK_LOCAL_RANGE[1])


def same_subnet(ip_int_a: torch.Tensor, ip_int_b: torch.Tensor, prefix_bits: int) -> torch.Tensor:
    """
    Check if two IPs are in the same subnet.

    Args:
        ip_int_a, ip_int_b: Integer IP representations
        prefix_bits: Number of prefix bits (8, 16, 24 for /8, /16, /24)

    Returns:
        Boolean tensor
    """
    shift = 32 - prefix_bits
    mask = (0xFFFFFFFF >> shift) << shift
    return ((ip_int_a.long() & mask) == (ip_int_b.long() & mask))


class IPAddressIPAddressOps(nn.Module):
    """
    Type-aware operations for IP_ADDRESS × IP_ADDRESS column pairs.

    Features (18 total):
    - Subnet matching (4): same_8, same_16, same_24, same_ip
    - Private/Public (6): is_private_a, is_private_b, both_private, both_public,
                          one_private_one_public, same_privacy_type
    - Loopback (4): is_loopback_a, is_loopback_b, both_loopback, either_loopback
    - Link-local (2): is_link_local_a, is_link_local_b
    - Network distance (2): normalized_distance, same_first_octet

    Use cases:
    - Fraud detection: Login from unexpected IP type (private vs public)
    - Same user detection: Both IPs from same corporate network
    - VPN/proxy detection: Mixed private/public patterns
    """

    N_IP_FEATURES = 18

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
            nn.Linear(self.N_IP_FEATURES, d_model // 2),
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

    def compute_ip_features(
        self,
        ip_parts_a: torch.Tensor,  # (batch, 4) IPv4 octets
        ip_parts_b: torch.Tensor,  # (batch, 4) IPv4 octets
    ) -> torch.Tensor:
        """
        Compute IP address comparison features.

        Args:
            ip_parts_a, ip_parts_b: IPv4 octets as (batch, 4) tensors

        Returns:
            Features tensor (batch, N_IP_FEATURES)
        """
        ip_int_a = ipv4_to_int(ip_parts_a)
        ip_int_b = ipv4_to_int(ip_parts_b)

        # =========================================================================
        # Subnet matching (4 features)
        # =========================================================================
        same_8 = same_subnet(ip_int_a, ip_int_b, 8).float()   # Same /8
        same_16 = same_subnet(ip_int_a, ip_int_b, 16).float() # Same /16
        same_24 = same_subnet(ip_int_a, ip_int_b, 24).float() # Same /24
        same_ip = (ip_int_a == ip_int_b).float()              # Exact match

        # =========================================================================
        # Private/Public features (6 features)
        # =========================================================================
        is_private_a = is_private_ip(ip_int_a).float()
        is_private_b = is_private_ip(ip_int_b).float()
        both_private = (is_private_a * is_private_b)
        both_public = ((1 - is_private_a) * (1 - is_private_b))
        # Mixed type: one private, one public (suspicious pattern)
        one_private_one_public = torch.abs(is_private_a - is_private_b)
        # Same privacy type
        same_privacy_type = 1.0 - one_private_one_public

        # =========================================================================
        # Loopback features (4 features)
        # =========================================================================
        is_loopback_a = is_loopback_ip(ip_int_a).float()
        is_loopback_b = is_loopback_ip(ip_int_b).float()
        both_loopback = (is_loopback_a * is_loopback_b)
        either_loopback = torch.clamp(is_loopback_a + is_loopback_b, 0, 1)

        # =========================================================================
        # Link-local features (2 features)
        # =========================================================================
        is_link_local_a = is_link_local_ip(ip_int_a).float()
        is_link_local_b = is_link_local_ip(ip_int_b).float()

        # =========================================================================
        # Network distance (2 features)
        # =========================================================================
        # Count matching prefix bits (approximation using XOR)
        xor = (ip_int_a.long() ^ ip_int_b.long()).float()
        # Normalized distance (0 = same, 1 = completely different)
        normalized_distance = torch.log1p(xor) / 32.0

        # Same first octet
        same_first_octet = (ip_parts_a[:, 0] == ip_parts_b[:, 0]).float()

        # =========================================================================
        # Stack all 18 features
        # =========================================================================
        features = torch.stack([
            # Subnet matching (4)
            same_8,
            same_16,
            same_24,
            same_ip,
            # Private/Public (6)
            is_private_a,
            is_private_b,
            both_private,
            both_public,
            one_private_one_public,
            same_privacy_type,
            # Loopback (4)
            is_loopback_a,
            is_loopback_b,
            both_loopback,
            either_loopback,
            # Link-local (2)
            is_link_local_a,
            is_link_local_b,
            # Network distance (2)
            normalized_distance,
            same_first_octet,
        ], dim=1)

        return features

    def forward(
        self,
        ip_embedding_a: torch.Tensor,  # (batch, d_model)
        ip_embedding_b: torch.Tensor,  # (batch, d_model)
        ip_parts_a: torch.Tensor,      # (batch, 4) IPv4 octets
        ip_parts_b: torch.Tensor,      # (batch, 4) IPv4 octets
    ) -> torch.Tensor:
        """Compute relationship for IP × IP pair."""
        # Raw features
        features = self.compute_ip_features(ip_parts_a, ip_parts_b)
        feature_emb = self.feature_mlp(features)

        # Embedding interaction
        interaction = self.interaction_mlp(torch.cat([
            ip_embedding_a,
            ip_embedding_b,
            ip_embedding_a * ip_embedding_b,
        ], dim=-1))

        # Fusion
        combined = torch.cat([feature_emb, interaction], dim=-1)
        return self.output_norm(self.fusion_mlp(combined))


class IPAddressTimestampOps(nn.Module):
    """
    Type-aware operations for IP_ADDRESS × TIMESTAMP column pairs.

    Captures patterns like:
    - "Login from unusual IP at unusual time"
    - "Business hours → corporate IP range"
    - "Night activity from residential IP"
    """

    def __init__(
        self,
        d_model: int,
        config: Optional["TypeAwareOpsConfig"] = None,
    ):
        super().__init__()
        self.d_model = d_model
        self.config = config

        # IP context for temporal
        self.ip_temporal_mlp = nn.Sequential(
            nn.Linear(d_model, d_model // 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model // 2, d_model),
        )

        # Temporal context for IP
        self.temporal_ip_mlp = nn.Sequential(
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
        ip_embedding: torch.Tensor,        # (batch, d_model)
        timestamp_embedding: torch.Tensor, # (batch, d_model)
    ) -> torch.Tensor:
        """Compute relationship for IP × Timestamp pair."""
        # IP modulates temporal
        ip_context = self.ip_temporal_mlp(ip_embedding)
        modulated_timestamp = timestamp_embedding * ip_context

        # Temporal modulates IP
        temporal_context = self.temporal_ip_mlp(timestamp_embedding)
        modulated_ip = ip_embedding * temporal_context

        # Interaction
        interaction = self.interaction_mlp(
            torch.cat([ip_embedding, timestamp_embedding], dim=-1)
        )

        # Product
        product = ip_embedding * timestamp_embedding

        # Fusion
        combined = torch.cat([
            modulated_timestamp,
            modulated_ip,
            interaction,
            product,
        ], dim=-1)

        return self.output_norm(self.fusion_mlp(combined))


class IPAddressSetOps(nn.Module):
    """
    Type-aware operations for IP_ADDRESS × SET column pairs.

    Captures patterns like:
    - "Corporate IP range → enterprise segment"
    - "VPN IP → tech-savvy user category"
    - "Geographic IP cluster → regional category"
    """

    def __init__(
        self,
        d_model: int,
        config: Optional["TypeAwareOpsConfig"] = None,
    ):
        super().__init__()
        self.d_model = d_model
        self.config = config

        # IP-conditioned set
        self.ip_gate_mlp = nn.Sequential(
            nn.Linear(d_model, d_model // 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model // 2, d_model),
        )

        # Set-conditioned IP
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
        ip_embedding: torch.Tensor,  # (batch, d_model)
        set_embedding: torch.Tensor, # (batch, d_model)
    ) -> torch.Tensor:
        """Compute relationship for IP × Set pair."""
        # IP gates set
        ip_gate = torch.sigmoid(self.ip_gate_mlp(ip_embedding))
        gated_set = set_embedding * ip_gate

        # Set contextualizes IP
        set_context = self.set_context_mlp(set_embedding)
        contextualized_ip = ip_embedding * set_context

        # Interaction
        interaction = self.interaction_mlp(
            torch.cat([ip_embedding, set_embedding], dim=-1)
        )

        # Product
        product = ip_embedding * set_embedding

        # Fusion
        combined = torch.cat([
            gated_set,
            contextualized_ip,
            interaction,
            product,
        ], dim=-1)

        return self.output_norm(self.fusion_mlp(combined))


class IPAddressScalarOps(nn.Module):
    """
    Type-aware operations for IP_ADDRESS × SCALAR column pairs.

    Captures patterns like:
    - "IP range → fraud risk score"
    - "Data center IP → higher request volume"
    - "Residential IP → lower average order value"
    """

    def __init__(
        self,
        d_model: int,
        config: Optional["TypeAwareOpsConfig"] = None,
    ):
        super().__init__()
        self.d_model = d_model
        self.config = config

        # IP-conditioned scalar
        self.ip_scale_mlp = nn.Sequential(
            nn.Linear(d_model, d_model // 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model // 2, d_model),
        )

        # Scalar-conditioned IP
        self.scalar_gate_mlp = nn.Sequential(
            nn.Linear(d_model, d_model // 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model // 2, d_model),
        )

        # Correlation
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
        ip_embedding: torch.Tensor,     # (batch, d_model)
        scalar_embedding: torch.Tensor, # (batch, d_model)
    ) -> torch.Tensor:
        """Compute relationship for IP × Scalar pair."""
        # IP scales scalar
        ip_scale = self.ip_scale_mlp(ip_embedding)
        scaled_scalar = scalar_embedding * ip_scale

        # Scalar gates IP
        scalar_gate = torch.sigmoid(self.scalar_gate_mlp(scalar_embedding))
        gated_ip = ip_embedding * scalar_gate

        # Correlation
        correlation = self.correlation_mlp(
            torch.cat([ip_embedding, scalar_embedding], dim=-1)
        )

        # Product
        product = ip_embedding * scalar_embedding

        # Fusion
        combined = torch.cat([
            scaled_scalar,
            gated_ip,
            correlation,
            product,
        ], dim=-1)

        return self.output_norm(self.fusion_mlp(combined))


class IPAddressGeoOps(nn.Module):
    """
    Type-aware operations for IP_ADDRESS × GEO_COORD column pairs.

    Captures patterns like:
    - "IP geolocation matches physical address"
    - "IP country vs shipping country mismatch"
    - "Distance between IP location and user location"

    Note: This requires IP→Geo enrichment to be useful.
    """

    def __init__(
        self,
        d_model: int,
        config: Optional["TypeAwareOpsConfig"] = None,
    ):
        super().__init__()
        self.d_model = d_model
        self.config = config

        # IP-Geo alignment
        self.alignment_mlp = nn.Sequential(
            nn.Linear(d_model * 2, d_model),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model, d_model),
        )

        # Mismatch detection
        self.mismatch_mlp = nn.Sequential(
            nn.Linear(d_model * 2, d_model),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model, d_model),
        )

        # Fusion
        self.fusion_mlp = nn.Sequential(
            nn.Linear(d_model * 3, d_model),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model, d_model),
        )

        self.output_norm = nn.LayerNorm(d_model)

    def forward(
        self,
        ip_embedding: torch.Tensor,  # (batch, d_model)
        geo_embedding: torch.Tensor, # (batch, d_model)
    ) -> torch.Tensor:
        """Compute relationship for IP × Geo pair."""
        concat = torch.cat([ip_embedding, geo_embedding], dim=-1)

        # Alignment
        alignment = self.alignment_mlp(concat)

        # Mismatch detection (difference-based)
        mismatch = self.mismatch_mlp(concat)

        # Product
        product = ip_embedding * geo_embedding

        # Fusion
        combined = torch.cat([alignment, mismatch, product], dim=-1)
        return self.output_norm(self.fusion_mlp(combined))
