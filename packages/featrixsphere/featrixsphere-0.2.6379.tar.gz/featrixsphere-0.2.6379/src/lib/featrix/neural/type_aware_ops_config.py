#  -*- coding: utf-8 -*-
#
#  Copyright Featrix, Inc 2023-2025
#
#  Proprietary and Confidential. Unauthorized use, copying or dissemination
#  of these materials is strictly prohibited.
"""
TypeAwareOpsConfig: Configuration for type-aware relationship operations.

Controls which type-specific relationship operations are enabled, supporting
easy ablation testing and gradual rollout of new operations.

Environment variable override:
    FEATRIX_TYPE_AWARE_OPS=none|existing|p0|no_set_timestamp,no_set_set,...
"""
import os
import logging
from dataclasses import dataclass, field, asdict
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class TypeAwareOpsConfig:
    """Configuration for type-aware relationship operations.

    All flags default to True for production. Set to False for ablation testing.

    Attributes:
        enable_timestamp_timestamp: Existing - delta_days, same_dow, etc.
        enable_string_timestamp: Existing - day_name embeddings
        enable_set_timestamp: NEW (P0) - temporal gating for set×timestamp
        enable_scalar_timestamp: NEW (P0) - cyclical correlation for scalar×timestamp
        enable_set_set: NEW (P1) - co-occurrence attention for set×set
        enable_set_scalar: NEW (P1) - scalar-conditioned gating for set×scalar
        enable_scalar_scalar_enhanced: NEW (P2) - ratio encoding for scalar×scalar
        enable_all_type_aware: Master switch - False = all generic ops only
        enable_generic_ops: False = type-aware only (for comparison)

    Granular controls (within specific ops):
        enable_temporal_gating: Within set×timestamp
        enable_cross_attention: Within set×timestamp, set×set
        enable_cyclical_features: Within scalar×timestamp
        enable_ratio_encoding: Within scalar×scalar
    """
    # P0: Timestamp combinations (existing ops - keep enabled by default)
    enable_timestamp_timestamp: bool = True      # Existing - delta_days, same_dow, etc.
    enable_string_timestamp: bool = True         # Existing - day_name embeddings

    # P0: NEW timestamp combinations (disabled by default - experimental)
    enable_set_timestamp: bool = False           # NEW - temporal gating
    enable_scalar_timestamp: bool = False        # NEW - cyclical correlation

    # P1: Set combinations (disabled by default - experimental)
    enable_set_set: bool = False                 # NEW - co-occurrence attention
    enable_set_scalar: bool = False              # NEW - scalar-conditioned gating

    # P2: Scalar combinations (disabled by default - experimental)
    enable_scalar_scalar_enhanced: bool = False  # NEW - ratio encoding

    # Strategy-aware relationship ops (experimental - learns best encoding strategy per relationship)
    # All controlled by same SphereConfig flag: use_strategy_aware_relationships
    enable_strategy_aware_scalar_scalar: bool = False   # Use strategy selection for scalar×scalar
    enable_strategy_aware_string_scalar: bool = False   # Use strategy selection for string×scalar
    enable_strategy_aware_set_scalar: bool = False      # Use strategy selection for set×scalar
    strategy_aware_top_k: int = 4                       # Number of strategy combos to evaluate per pair

    # P3: Email/Domain combinations (disabled by default - experimental)
    enable_email_domain_set: bool = False        # NEW - free/corporate × set
    enable_email_domain_scalar: bool = False     # NEW - free/corporate × scalar
    enable_email_domain_timestamp: bool = False  # NEW - domain × time patterns
    enable_email_domain_string: bool = False     # NEW - domain main part × string semantics

    # P4: URL combinations (disabled by default - experimental)
    enable_url_set: bool = False                 # NEW - URL presence/protocol/TLD × set
    enable_url_scalar: bool = False              # NEW - URL features × scalar correlation
    enable_url_timestamp: bool = False           # NEW - URL × time patterns
    enable_url_string: bool = False              # NEW - URL path/query × string semantics

    # Master switches for ablation
    enable_all_type_aware: bool = True           # False = all generic ops only
    enable_generic_ops: bool = True              # False = type-aware only (for comparison)

    # Granular control within ops
    enable_temporal_gating: bool = True          # Within set×timestamp
    enable_cross_attention: bool = True          # Within set×timestamp, set×set
    enable_cyclical_features: bool = True        # Within scalar×timestamp
    enable_ratio_encoding: bool = True           # Within scalar×scalar

    # Limits for type-aware pairs (to prevent explosion with many columns)
    max_set_set_pairs: int = 20                  # Max Set×Set pairs (None = unlimited)
    max_set_scalar_pairs: int = 30               # Max Set×Scalar pairs (None = unlimited)
    max_scalar_scalar_pairs: int = 15            # Max Scalar×Scalar pairs (None = unlimited)
    max_set_timestamp_pairs: int = 20            # Max Set×Timestamp pairs (None = unlimited)
    max_scalar_timestamp_pairs: int = 20         # Max Scalar×Timestamp pairs (None = unlimited)
    max_email_domain_set_pairs: int = 15         # Max Email/Domain×Set pairs (None = unlimited)
    max_email_domain_scalar_pairs: int = 15      # Max Email/Domain×Scalar pairs (None = unlimited)
    max_email_domain_timestamp_pairs: int = 10   # Max Email/Domain×Timestamp pairs (None = unlimited)
    max_email_domain_string_pairs: int = 10      # Max Email/Domain×String pairs (None = unlimited)
    max_url_set_pairs: int = 15                  # Max URL×Set pairs (None = unlimited)
    max_url_scalar_pairs: int = 15               # Max URL×Scalar pairs (None = unlimited)
    max_url_timestamp_pairs: int = 10            # Max URL×Timestamp pairs (None = unlimited)
    max_url_string_pairs: int = 10               # Max URL×String pairs (None = unlimited)

    @classmethod
    def all_disabled(cls) -> "TypeAwareOpsConfig":
        """All type-aware ops disabled - generic only baseline."""
        return cls(
            enable_timestamp_timestamp=False,
            enable_string_timestamp=False,
            enable_set_timestamp=False,
            enable_scalar_timestamp=False,
            enable_set_set=False,
            enable_set_scalar=False,
            enable_scalar_scalar_enhanced=False,
            enable_email_domain_set=False,
            enable_email_domain_scalar=False,
            enable_email_domain_timestamp=False,
            enable_email_domain_string=False,
            enable_url_set=False,
            enable_url_scalar=False,
            enable_url_timestamp=False,
            enable_url_string=False,
            enable_all_type_aware=False,
            enable_temporal_gating=False,
            enable_cross_attention=False,
            enable_cyclical_features=False,
            enable_ratio_encoding=False,
        )

    @classmethod
    def only_existing(cls) -> "TypeAwareOpsConfig":
        """Only existing ops (timestamp×timestamp, string×timestamp)."""
        return cls(
            enable_set_timestamp=False,
            enable_scalar_timestamp=False,
            enable_set_set=False,
            enable_set_scalar=False,
            enable_scalar_scalar_enhanced=False,
        )

    @classmethod
    def only_p0(cls) -> "TypeAwareOpsConfig":
        """Only P0 ops (all timestamp combinations)."""
        return cls(
            enable_set_set=False,
            enable_set_scalar=False,
            enable_scalar_scalar_enhanced=False,
        )

    @classmethod
    def only_p0_p1(cls) -> "TypeAwareOpsConfig":
        """P0 + P1 ops (timestamps + set combinations)."""
        return cls(
            enable_set_timestamp=True,
            enable_scalar_timestamp=True,
            enable_set_set=True,
            enable_set_scalar=True,
            enable_scalar_scalar_enhanced=False,
        )

    @classmethod
    def all_new_enabled(cls) -> "TypeAwareOpsConfig":
        """Enable ALL new type-aware ops (for testing)."""
        return cls(
            enable_set_timestamp=True,
            enable_scalar_timestamp=True,
            enable_set_set=True,
            enable_set_scalar=True,
            enable_scalar_scalar_enhanced=True,
            enable_email_domain_set=True,
            enable_email_domain_scalar=True,
            enable_email_domain_timestamp=True,
            enable_email_domain_string=True,
            enable_url_set=True,
            enable_url_scalar=True,
            enable_url_timestamp=True,
            enable_url_string=True,
        )

    @classmethod
    def from_sphere_config(cls) -> "TypeAwareOpsConfig":
        """Create config from SphereConfig (/sphere/app/config.json).

        config.json example:
            {"enable_type_aware_ops": true}
        """
        from featrix.neural.sphere_config import get_config
        enabled = get_config().get_enable_type_aware_ops()

        if enabled:
            return cls.all_new_enabled()
        else:
            return cls.only_existing()

    @classmethod
    def from_env(cls) -> "TypeAwareOpsConfig":
        """Create config from FEATRIX_TYPE_AWARE_OPS environment variable.

        NOTE: Prefer from_sphere_config() which reads from /sphere/app/config.json.
        This method is kept for backwards compatibility and quick testing.

        Supported values:
            - "auto" (default): Read from SphereConfig (config.json)
            - "none": All type-aware ops disabled (generic only)
            - "existing": Only timestamp×timestamp and string×timestamp
            - "p0": All timestamp combinations (existing + set×ts + scalar×ts)
            - "p0_p1": P0 + set×set, set×scalar
            - "all": All type-aware ops enabled
            - Comma-separated flags: "no_set_timestamp,no_set_set" to disable specific ops

        Examples:
            FEATRIX_TYPE_AWARE_OPS=none python train.py
            FEATRIX_TYPE_AWARE_OPS=no_set_timestamp,no_cross_attention python train.py
        """
        preset = os.environ.get("FEATRIX_TYPE_AWARE_OPS", "auto")

        if preset == "auto":
            # Read from SphereConfig (config.json) by default
            return cls.from_sphere_config()
        elif preset == "none":
            return cls.all_disabled()
        elif preset == "existing":
            return cls.only_existing()
        elif preset == "p0":
            return cls.only_p0()
        elif preset == "p0_p1":
            return cls.only_p0_p1()
        elif preset == "all":
            return cls.all_new_enabled()
        else:
            # Parse individual flags: "no_set_timestamp,no_set_set"
            config = cls()
            for flag in preset.split(","):
                flag = flag.strip()
                if flag.startswith("no_"):
                    field_name = f"enable_{flag[3:]}"
                    if hasattr(config, field_name):
                        setattr(config, field_name, False)
                        logger.info(f"   TypeAwareOpsConfig: disabled {field_name} via env")
                    else:
                        logger.warning(f"   TypeAwareOpsConfig: unknown flag '{flag}' (field '{field_name}' not found)")
            return config

    def get_enabled_ops(self) -> list:
        """Return list of enabled type-aware op names."""
        enabled = []
        for key, value in asdict(self).items():
            if key.startswith("enable_") and value and key != "enable_all_type_aware" and key != "enable_generic_ops":
                enabled.append(key.replace("enable_", ""))
        return enabled

    def log_config(self, prefix: str = "   ") -> None:
        """Log the current configuration."""
        if not self.enable_all_type_aware:
            logger.info(f"{prefix}TypeAwareOpsConfig: ALL type-aware ops DISABLED (generic only)")
            return

        enabled = self.get_enabled_ops()
        disabled = []
        for key, value in asdict(self).items():
            if key.startswith("enable_") and not value and key != "enable_all_type_aware" and key != "enable_generic_ops":
                disabled.append(key.replace("enable_", ""))

        logger.info(f"{prefix}TypeAwareOpsConfig: {len(enabled)} ops enabled")
        if disabled:
            logger.info(f"{prefix}  Disabled: {', '.join(disabled)}")
