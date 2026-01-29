#!/usr/bin/env python3
"""
Sphere Configuration Management

Loads configuration from /sphere/app/config.json if it exists, otherwise uses defaults.
Makes it easy to experiment with different model configurations without code changes.
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Capture the original working directory when module loads
# This is important because tests may chdir during execution
_ORIGINAL_CWD = os.getcwd()

# Default configuration paths - searched in order
# 1. Original CWD config.json (captured at module import time)
# 2. Current CWD config.json (for cases where chdir happened before import)
# 3. /sphere/app/config.json (for production deployments)
DEFAULT_CONFIG_PATHS = [
    os.path.join(_ORIGINAL_CWD, "config.json"),  # Original CWD (absolute)
    "config.json",  # Current CWD (relative, in case of late import)
    "/sphere/app/config.json",  # Production
]
DEFAULT_CONFIG_PATH = "/sphere/app/config.json"  # Kept for backward compatibility

# Default values if config file is missing
DEFAULT_CONFIG = {
    # === EMBEDDING SPACE ARCHITECTURE (auto-tuned based on data) ===
    "d_model": None,  # Auto-computed based on column count: <10→64, <30→128, <60→192, ≥60→256
    "n_transformer_layers": None,  # Auto-computed based on column count: <10→3, <30→5, <60→7, ≥60→8
    "n_attention_heads": None,  # Auto-computed based on detected column relationships
    # === NORMALIZATION ===
    "normalize_column_encoders": False,  # Phase 1 fix: only normalize in joint encoder
    "normalize_joint_encoder": True,  # Should almost always be True
    "use_semantic_set_initialization": False,  # DISABLED for regression testing - Initialize set embeddings from BERT (also enables OOV handling)
    "enable_spectral_norm_clipping": True,  # Enable spectral norm clipping during training
    "spectral_norm_clip_threshold": 12.0,  # Maximum spectral norm before clipping (if enabled)
    "adaptive_scalar_hidden_dim": 16,  # Hidden dimension for AdaptiveScalarEncoder MLPs (default: 16 for speed)
    "use_delimiter_preprocessing": False,  # Preprocess delimited strings ("a,b,c" → "a\nb\nc") before BERT encoding
    "enable_predictor_architecture_selection": False,  # DISABLED: Architecture selection wastes 30+ epochs for <1% improvement
    "string_server_host": "taco.local",  # String server host: "taco", "taco.local", or "localhost" (None = use local model)
    "es_weight_initialization": "random",  # "random" = standard pytorch init, "pca_string" = init from PCA of string embeddings
    "use_bf16": False,  # BF16 mixed precision training (RTX 4090/Ampere+ only, saves ~50% memory)
    "enable_predictor_attention": True,  # Enable attention mechanism in predictor MLPs (improves AUC ~5%)
    "predictor_attention_heads": None,  # Auto-size based on d_hidden (d_hidden//32, clamped to [4,16]). Set explicitly to override.
    "disable_curriculum_learning": False,  # Disable loss weight curriculum (use constant 1.0 weights for spread/marginal/joint)
    "enable_spread_loss": True,  # Re-enabled 2026-01-22: Good 0.7 AUC commits had this enabled
    "freeze_es_warmup_enabled": True,  # Freeze embedding space for first 5% of SP training epochs (only if > 5 epochs)
    "max_sp_epochs": None,  # Override max epochs for single predictor training (None = use default from training args)
    "max_es_epochs": None,  # Override max epochs for embedding space training (None = use default from training args)
    "enable_embedding_diversity_loss": True,  # ENABLED BY DEFAULT: Prevents global embedding collapse (std/dim → 0)
    "embedding_diversity_weight": 1.0,  # Weight for diversity loss (if enabled) - matches spread_loss_weight for equal importance
    "use_muon_optimizer": False,  # Use Muon optimizer instead of AdamW (experimental, may improve convergence)
    "use_strategy_aware_relationships": True,  # Learn best encoding strategy per scalar-scalar relationship (+6% AUC on Spaceship Titanic)
    "strategy_aware_top_k": 4,  # Number of strategy combinations to evaluate per relationship (if strategy-aware enabled)
    "enable_reconstruction_loss": True,  # Add direct value reconstruction loss to marginal loss (helps scalar encoding)
    "reconstruction_loss_weight": 1.0,  # Weight for reconstruction loss (if enabled)
    "sp_es_lr_ratio": 0.05,  # Ratio of encoder LR to predictor LR during SP fine-tuning (encoder_lr = predictor_lr * ratio)
    "sp_freeze_epochs": None,  # Number of epochs to freeze ES during SP training (None = 5% of total epochs)
    "sp_n_hidden_layers": None,  # Number of hidden layers in SP predictor MLP (None = use default from training args)
    "sp_d_hidden": None,  # Hidden dimension for SP predictor MLP (None = use es.d_model, typically 256)
    "sp_dropout": None,  # Dropout for SP predictor (None = auto-compute based on dataset size and imbalance)
    # Hyperparameter search experiment settings
    "hyperparam_search_file": None,  # Path to ThingsToTry JSON file (None = disabled)
    "hyperparam_results_file": None,  # Path to ThingsTried JSON file for results (None = auto-generate)
    "hyperparam_evaluate_at_epoch": 20,  # Evaluate experiment at this epoch
    # Individual hyperparameter overrides (can be set via experiment or directly)
    "sp_adaptive_dropout": False,  # Enable adaptive dropout (increases when AUC plateaus)
    "sp_label_smoothing": 0.0,  # Label smoothing factor (0.0 = disabled)
    "sp_weight_decay": 0.0,  # Weight decay for optimizer (0.0 = disabled)
    "sp_oscillation_amplitude": 0.15,  # LR oscillation amplitude (0.0 = disabled, 0.15 = ±15%)
    "sp_batch_size": None,  # Override batch size (None = use default)
    "sp_lr_schedule": "LRTimeline",  # LR schedule: "LRTimeline" or "OneCycleLR"
    # Ablation controls for loss mechanisms
    "sp_adaptive_focal_loss": True,  # Enable adaptive FocalLoss adjustments mid-training
    "sp_pairwise_ranking_loss": True,  # Enable pairwise ranking loss component
    "sp_pairwise_ranking_weight": 0.1,  # Weight for pairwise ranking loss (if enabled)
    "sp_logit_clamp": True,  # Enable logit clamping to [-20, 20]
    "sp_use_focal_loss": True,  # Use FocalLoss (False = use CrossEntropyLoss)
    "sp_focal_gamma_adaptable": False,  # Use classic FocalLoss with adaptive gamma adjustments (legacy behavior)
    "sp_adaptive_loss_type": "auc_guided",  # "auc_guided" = stable weights updated by val AUC, "voting" = win-rate based, "learning" = gradient-learned
    # Type-aware relationship operations
    "enable_type_aware_ops": True,  # Enable all new type-aware relationship ops (set×ts, scalar×ts, set×set, etc.)
    # Adam optimizer configuration
    "adam_eps": 1e-8,  # Adam epsilon for numerical stability (default: 1e-8, try 1e-10 for smoother curves)
    # === SHORT EMBEDDING (3D) ANTI-COLLAPSE LOSSES ===
    # These are critical for preventing the 3D visualization embeddings from collapsing
    # while the 256D embeddings remain healthy. See loss_short_embedding.py for details.
    # IMPORTANT: Keep these weights LOW (0.1-0.5 range) to prevent oscillation!
    # High weights cause gradient wars between conflicting losses (spread vs repulsion vs uniformity).
    # The main ES training loss (joint/marginal) should dominate; these are just regularizers.
    "enable_short_uniformity_loss": True,  # Log-sum-exp uniformity loss (Wang & Isola 2020)
    "short_uniformity_weight": 0.2,  # Weight for uniformity loss (was 2.0 - caused oscillation)
    "enable_short_diversity_loss": True,  # Per-dimension std enforcement (target: 1/sqrt(3) ≈ 0.577)
    "short_diversity_weight": 0.5,  # Weight for diversity loss (was 5.0 - caused oscillation)
    "enable_short_repulsion_loss": True,  # Pairwise repulsion for points too close together
    "short_repulsion_weight": 0.3,  # Weight for repulsion loss (was 3.0 - caused oscillation)
    "short_repulsion_threshold": 0.7,  # Similarity threshold (0.7 ≈ 45° angle) - penalize pairs above this
    "enable_short_spread_loss": True,  # Bounding box coverage loss (penalize small bounding box)
    "short_spread_weight": 2.0,  # Weight for spread loss (increased to push for better coverage)
    "short_spread_target_diagonal": 0.95,  # Target diagonal ratio (95% ≈ 3.29 of √12 ≈ 3.46)
    # === SPHERICAL CAP OVERLAP LOSS (Label Separation) ===
    # Penalizes overlap between spherical caps of different labels on the 3D sphere.
    # Each label's territory is approximated as a spherical cap (centroid + angular radius).
    # Minimizing cap overlap encourages different classes to occupy separate regions.
    "enable_short_cap_overlap_loss": True,  # Enable spherical cap overlap loss for label separation during SP training
    "short_cap_overlap_weight": 0.5,  # Weight for cap overlap loss (was 5.0 - keep low to prevent oscillation)
    "short_cap_overlap_margin": 0.1,  # Angular margin (radians) between caps (~6 degrees)
    # === EMBEDDING INITIALIZATION ===
    # Controls whether embeddings use hypersphere init (unit vectors) or Xavier init.
    # DISABLED 2026-01-22: Testing if hypersphere init hurts AUC. Good 0.7 commits used Xavier.
    "use_hypersphere_init": False,  # False=Xavier (old/good), True=unit vectors on hypersphere (new)
    # === JOINT ENCODER POOLING ===
    # Controls how column encodings are combined into joint embedding.
    # CLS token approach works better with variable-length rows (NULL columns excluded).
    # Mean pooling was switched to fix variance collapse but doesn't handle NULLs properly.
    "use_cls_token_pooling": True,  # True=CLS token (handles NULLs), False=mean of columns (broken for NULLs)
}


class SphereConfig:
    """
    Singleton configuration manager for Sphere.
    
    Usage:
        config = SphereConfig.get_instance()
        d_model = config.get_d_model()
    """
    
    _instance: Optional['SphereConfig'] = None
    _config: Dict[str, Any] = None
    _config_path: str = DEFAULT_CONFIG_PATH
    
    def __init__(self):
        """Private constructor. Use get_instance() instead."""
        if SphereConfig._instance is not None:
            raise RuntimeError("Use SphereConfig.get_instance() instead of direct instantiation")
        self._load_config()
    
    @classmethod
    def get_instance(cls, config_path: str = None) -> 'SphereConfig':
        """
        Get the singleton instance of SphereConfig.
        
        Args:
            config_path: Optional custom path to config file (for testing)
        
        Returns:
            SphereConfig instance
        """
        if cls._instance is None:
            if config_path:
                cls._config_path = config_path
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def reset(cls):
        """Reset the singleton (useful for testing)."""
        cls._instance = None
        cls._config = None
        cls._config_path = DEFAULT_CONFIG_PATH
    
    def _load_config(self):
        """Load configuration from file or use defaults.

        Searches multiple paths in order:
        1. Custom path (if set via get_instance(config_path=...))
        2. Local config.json (current working directory)
        3. /sphere/app/config.json (production)
        """
        # Build list of paths to search
        paths_to_search = []
        if self._config_path != DEFAULT_CONFIG_PATH:
            # Custom path was specified - search it first
            paths_to_search.append(Path(self._config_path))
        # Add default search paths
        for p in DEFAULT_CONFIG_PATHS:
            paths_to_search.append(Path(p))

        # Try each path in order
        for config_file in paths_to_search:
            if config_file.exists():
                try:
                    with open(config_file, 'r') as f:
                        self._config = json.load(f)
                    logger.info(f"📋 Loaded Sphere configuration from {config_file.absolute()}")
                    logger.info(f"   Configuration: {json.dumps(self._config, indent=2)}")

                    # Merge with defaults (in case config file doesn't have all keys)
                    for key, default_value in DEFAULT_CONFIG.items():
                        if key not in self._config:
                            logger.info(f"   Using default for missing key '{key}': {default_value}")
                            self._config[key] = default_value
                    return  # Successfully loaded

                except json.JSONDecodeError as e:
                    logger.error(f"❌ Failed to parse config file {config_file}: {e}")
                    continue  # Try next path
                except Exception as e:
                    logger.error(f"❌ Error reading config file {config_file}: {e}")
                    continue  # Try next path

        # No config file found - use defaults
        logger.info(f"ℹ️  No config file found in search paths: {[str(p) for p in paths_to_search]}")
        logger.info(f"   Using default configuration: {json.dumps(DEFAULT_CONFIG, indent=2)}")
        self._config = DEFAULT_CONFIG.copy()
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by key.
        
        Args:
            key: Configuration key
            default: Default value if key not found
        
        Returns:
            Configuration value or default
        """
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any) -> Any:
        """
        Set a configuration value (for testing/runtime override).
        
        Args:
            key: Configuration key
            value: Value to set
        
        Returns:
            Previous value (or None if key didn't exist)
        
        Example:
            config = get_config()
            old_value = config.set("es_weight_initialization", "pca_string")
            # ... do something ...
            config.set("es_weight_initialization", old_value)  # restore
        """
        old_value = self._config.get(key)
        self._config[key] = value
        logger.info(f"📋 Config override: {key} = {value} (was: {old_value})")
        return old_value
    
    def get_d_model(self) -> Optional[int]:
        """
        Get the d_model (embedding dimension) parameter.

        Returns None if not explicitly set - caller should use auto_compute_d_model() instead.
        """
        return self._config.get("d_model")
    
    def get_normalize_column_encoders(self) -> bool:
        """
        Get whether to normalize individual column encoder outputs.
        
        When False: Column encoders return unnormalized vectors (Phase 1 fix)
        When True: Column encoders normalize their outputs (legacy behavior)
        
        Default: True (for backward compatibility)
        
        This controls the redundant normalization that limits sphere coverage.
        Setting to False removes column-level normalization, keeping only the
        final joint encoder normalization.
        """
        return self._config.get("normalize_column_encoders", DEFAULT_CONFIG["normalize_column_encoders"])
    
    def get_normalize_joint_encoder(self) -> bool:
        """
        Get whether to normalize joint encoder output.
        
        This should almost always be True to ensure embeddings lie on unit sphere.
        
        Default: True
        
        Only set to False for experimental purposes or specific use cases
        where unnormalized embeddings are desired.
        """
        return self._config.get("normalize_joint_encoder", DEFAULT_CONFIG["normalize_joint_encoder"])
    
    def use_semantic_set_initialization(self) -> bool:
        """
        Get whether to initialize set embeddings using BERT vectors from string cache.
        
        When True:
        - Set embeddings are initialized with semantic vectors (e.g., colors, sizes in order)
        - Out-of-vocabulary values at inference can use BERT projection instead of UNKNOWN
        - Faster convergence and better rare value handling
        
        Default: False (backward compatible)
        
        Requires string cache to be enabled during training.
        """
        return self._config.get("use_semantic_set_initialization", DEFAULT_CONFIG.get("use_semantic_set_initialization", False))
    
    def use_delimiter_preprocessing(self) -> bool:
        """
        Get whether to preprocess delimited strings before BERT encoding.
        
        When True:
        - Detect common delimiters (comma, semicolon, pipe, slash, tab) in string columns
        - Preprocess: "a,b,c" → "a\\nb\\nc" before BERT encoding
        - Results in better embeddings for multi-valued fields
        - Requires 30%+ of values to have delimiter to activate
        
        When False:
        - No delimiter detection or preprocessing
        - Strings are encoded by BERT as-is
        - DELIMITER strategy in adaptive encoder still learns when to trust BERT's raw encoding
        
        Default: False (conservative - no preprocessing)
        
        Note: Enabling this CHANGES string cache keys for columns with detected delimiters.
        Existing trained models with cached strings may need retraining.
        Only detects "safe" delimiters: , ; | / :: // \\t (not - or _ due to false positive risk)
        """
        return self._config.get("use_delimiter_preprocessing", DEFAULT_CONFIG.get("use_delimiter_preprocessing", False))

    def use_hypersphere_init(self) -> bool:
        """
        Get whether to use hypersphere initialization for embeddings.

        When True:
        - Embeddings initialized as random unit vectors (uniform on hypersphere)
        - Projection layers use orthogonal init + normalize to unit norm
        - Transformer encoder uses special init for spread outputs

        When False:
        - Embeddings use Xavier uniform initialization (the old/good way)
        - Projection layers use default PyTorch init
        - This was the behavior in commits with ~0.7 AUC (Jan 19, 2026)

        Default: False (Xavier - the old/good initialization)
        """
        return self._config.get("use_hypersphere_init", DEFAULT_CONFIG.get("use_hypersphere_init", False))

    def use_cls_token_pooling(self) -> bool:
        """
        Get whether to use CLS token pooling for joint embeddings.

        When True:
        - Joint embedding is the CLS token output (position 0) from transformer
        - NOT_PRESENT columns are properly excluded (CLS attends to present columns)
        - Better for variable-length rows (different NULL patterns)

        When False:
        - Joint embedding is mean of column outputs (positions 1:)
        - NOT_PRESENT columns still contribute to mean (broken for sparse data)
        - Was switched to fix CLS variance collapse but breaks NULL handling

        Default: True (CLS token - proper NULL handling)
        """
        return self._config.get("use_cls_token_pooling", DEFAULT_CONFIG.get("use_cls_token_pooling", True))

    def get_enable_spectral_norm_clipping(self) -> bool:
        """
        Get whether to enable spectral norm clipping during training.
        
        When True:
        - Spectral norms of layers exceeding the threshold are clipped
        - Helps stabilize training by preventing extreme weight values
        
        When False:
        - No spectral norm clipping is applied
        - Layers can have arbitrarily large spectral norms
        
        Default: True (for stability)
        
        Note: This can be disabled to allow more exploration during training,
        but may lead to instability in some cases.
        """
        return self._config.get("enable_spectral_norm_clipping", DEFAULT_CONFIG.get("enable_spectral_norm_clipping", True))
    
    def get_spectral_norm_clip_threshold(self) -> float:
        """
        Get the spectral norm clipping threshold.
        
        If spectral norm clipping is enabled, layers with spectral norms
        exceeding this threshold will be clipped down to this value.
        
        Default: 12.0
        
        Higher values allow larger weight magnitudes.
        Lower values enforce more conservative weight constraints.
        """
        return self._config.get("spectral_norm_clip_threshold", DEFAULT_CONFIG.get("spectral_norm_clip_threshold", 12.0))
    
    def get_adaptive_scalar_hidden_dim(self) -> int:
        """
        Get the hidden dimension size for AdaptiveScalarEncoder MLPs.
        
        Each strategy (linear, log, robust, rank, periodic) uses an MLP with this hidden size.
        Smaller values = faster training but potentially less expressive.
        
        Default: 16 (good balance of speed and quality)
        
        Common values:
        - 16: Fast, 4× faster than 64 (recommended for most use cases)
        - 32: Medium, 2× faster than 64 (good accuracy/speed tradeoff)
        - 64: Slow, most expressive (use if accuracy is critical)
        """
        return self._config.get("adaptive_scalar_hidden_dim", DEFAULT_CONFIG.get("adaptive_scalar_hidden_dim", 16))
    
    def get_string_server_host(self) -> Optional[str]:
        """
        Get the string server host configuration.
        
        Returns:
            "taco" - Use remote string server (tries taco.local first, then taco, then proxy)
            "taco.local" - Use remote string server directly at taco.local:9000
            "localhost" - Use local string server at localhost:9000
            None - Use local sentence transformer model (legacy behavior)
        
        Default: "taco.local" (uses remote string server)
        """
        return self._config.get("string_server_host", DEFAULT_CONFIG.get("string_server_host", "taco.local"))
    
    def get_enable_predictor_architecture_selection(self) -> bool:
        """
        Get whether to enable automatic predictor architecture selection during EmbeddingSpace training.
        
        When True:
        - The system will train multiple candidate predictor architectures for a few epochs
        - Selects the best architecture based on validation loss
        - Affects both column predictors and joint predictor
        - Only runs on fresh training (not when resuming from checkpoint)
        
        When False:
        - Uses default predictor architecture (no selection)
        - Faster training start (skips architecture selection phase)
        
        Default: False (DISABLED - architecture selection provides <1% improvement for 30+ epochs overhead)
        
        Note: Architecture selection adds ~15 epochs × 2-4 candidates = ~30-60 epochs of overhead
        before main training begins, but typically only shows <1% validation loss improvement.
        """
        return self._config.get("enable_predictor_architecture_selection", DEFAULT_CONFIG.get("enable_predictor_architecture_selection", False))
    
    def get_es_weight_initialization(self) -> str:
        """
        Get the embedding space weight initialization strategy.
        
        Options:
        - "random": Standard PyTorch initialization (default)
        - "pca_string": Initialize weights using PCA of string embeddings from sentence transformer
        
        Default: "random"
        
        The PCA initialization uses statistics from sentence transformer embeddings to set
        initial weight distributions. This can help with convergence but requires access
        to the string server for BERT embeddings.
        
        Can be overridden by FEATRIX_ES_WEIGHT_INIT environment variable for testing.
        """
        # Check environment variable first (for ablation testing)
        env_value = os.getenv("FEATRIX_ES_WEIGHT_INIT")
        if env_value in ("random", "pca_string"):
            return env_value
        return self._config.get("es_weight_initialization", DEFAULT_CONFIG.get("es_weight_initialization", "random"))
    
    def get_use_bf16(self) -> bool:
        """
        Get whether to use BF16 mixed precision training.
        
        When True:
        - Training uses BF16 (bfloat16) mixed precision on supported GPUs
        - Saves ~50% memory (activations stored in 16-bit instead of 32-bit)
        - Requires Ampere or newer GPU (RTX 30xx+, RTX 40xx, A100, H100)
        - Better numerical stability than FP16 (no GradScaler needed)
        - Similar or slightly faster than FP32
        
        When False:
        - Training uses FP32 (standard 32-bit floating point)
        - More memory usage but works on all GPUs
        
        Default: False (off, for compatibility)
        
        Note: If enabled on incompatible GPU, automatically falls back to FP32.
        Recommended for RTX 4090 and other Ampere+ GPUs when hitting memory limits.
        """
        return self._config.get("use_bf16", DEFAULT_CONFIG.get("use_bf16", False))
    
    def get_enable_predictor_attention(self) -> bool:
        """
        Get whether to enable attention mechanism in predictor MLPs.
        
        Can be set via:
        1. Environment variable: FEATRIX_ENABLE_PREDICTOR_ATTENTION=1 or 0 (highest priority)
        2. config.json: "enable_predictor_attention": true
        
        When True:
        - Predictor MLPs include multi-head self-attention layers between feedforward blocks
        - Allows the model to learn relationships between different embedding dimensions
        - Can improve performance on complex tasks by learning which dimensions to attend to
        - Adds computational overhead (~10-20% slower training)
        
        When False:
        - Predictor uses standard feedforward MLP (no attention)
        - Faster training, standard behavior
        
        Default: False (disabled, experimental feature)
        
        Note: This is an experimental feature. Enable to test if attention improves
        predictor performance on your specific tasks. Requires n_hidden_layers > 0 to have effect.
        """
        # Check environment variable first (highest priority)
        env_val = os.environ.get("FEATRIX_ENABLE_PREDICTOR_ATTENTION", "").strip()
        if env_val == "1":
            return True
        elif env_val == "0":
            return False
        # Fall back to config
        return self._config.get("enable_predictor_attention", DEFAULT_CONFIG.get("enable_predictor_attention", False))
    
    def get_predictor_attention_heads(self) -> Optional[int]:
        """
        Get the number of attention heads for predictor attention mechanism.

        Only used when enable_predictor_attention=True.

        Default: None (auto-size based on d_hidden: d_hidden//32, clamped to [4,16])

        Common explicit values:
        - 4: Good for d_hidden=128
        - 8: Good for d_hidden=256
        - 16: Good for d_hidden=512

        Returns None to signal auto-sizing based on d_hidden.
        """
        return self._config.get("predictor_attention_heads", DEFAULT_CONFIG.get("predictor_attention_heads", None))
    
    def get_disable_curriculum_learning(self) -> bool:
        """
        Get whether to disable curriculum learning (loss weight scheduling).
        
        Can be set via:
        1. Environment variable: FEATRIX_DISABLE_CURRICULUM=1 (highest priority)
        2. config.json: "disable_curriculum_learning": true
        
        When True:
        - All loss weights (spread, marginal, joint) are fixed at 1.0 throughout training
        - No phase-based loss weighting or transitions
        - Useful for debugging or comparing with/without curriculum
        
        When False:
        - Uses the default 3-phase curriculum learning schedule:
          Phase 1 (0-30%): Spread focus (10:0.02:0.5)
          Phase 2 (30-85%): Reconstruction focus (1:0.25:2) - marginal+joint aligned
          Phase 3 (85-100%): Refinement (2:0.15:2)
        - Smooth cosine transitions between phases
        
        Default: False (curriculum learning enabled)
        """
        # Environment variable takes priority over config.json
        env_val = os.environ.get("FEATRIX_DISABLE_CURRICULUM", "").lower()
        if env_val in ("1", "true", "yes"):
            return True
        if env_val in ("0", "false", "no"):
            return False
        # Fall back to config.json
        return self._config.get("disable_curriculum_learning", DEFAULT_CONFIG.get("disable_curriculum_learning", False))
    
    def get_max_sp_epochs(self) -> int:
        """
        Get the maximum number of epochs for single predictor training.
        
        Can be set via:
        1. Environment variable: FEATRIX_MAX_SP_EPOCHS=<int> (highest priority)
        2. config.json: "max_sp_epochs": <int>
        
        When set to a positive integer:
        - Overrides the epochs parameter passed to training
        - Useful for quick I/O testing (e.g., set to 3 to test save/load quickly)
        
        When None or 0:
        - Use the epochs parameter from training args (default behavior)
        
        Default: None (use training args)
        """
        # Environment variable takes priority
        env_val = os.environ.get("FEATRIX_MAX_SP_EPOCHS", "").strip()
        if env_val:
            try:
                val = int(env_val)
                if val > 0:
                    return val
            except ValueError:
                pass
        # Fall back to config.json
        val = self._config.get("max_sp_epochs", DEFAULT_CONFIG.get("max_sp_epochs", None))
        if val and val > 0:
            return val
        return None
    
    def get_max_es_epochs(self) -> int:
        """
        Get the maximum number of epochs for embedding space training.
        
        Can be set via:
        1. Environment variable: FEATRIX_MAX_ES_EPOCHS=<int> (highest priority)
        2. config.json: "max_es_epochs": <int>
        
        When set to a positive integer:
        - Overrides the epochs parameter passed to training
        - Useful for quick I/O testing (e.g., set to 3 to test save/load quickly)
        
        When None or 0:
        - Use the epochs parameter from training args (default behavior)
        
        Default: None (use training args)
        """
        # Environment variable takes priority
        env_val = os.environ.get("FEATRIX_MAX_ES_EPOCHS", "").strip()
        if env_val:
            try:
                val = int(env_val)
                if val > 0:
                    return val
            except ValueError:
                pass
        # Fall back to config.json
        val = self._config.get("max_es_epochs", DEFAULT_CONFIG.get("max_es_epochs", None))
        if val and val > 0:
            return val
        return None
    
    def auto_compute_d_model(self, num_columns: int) -> int:
        """
        Auto-compute d_model based on number of columns (if not manually set).
        
        Tiers (multiples of 64):
        - < 10 columns:  64
        - < 30 columns:  128
        - < 60 columns:  192
        - >= 60 columns: 256
        
        Args:
            num_columns: Number of columns in dataset
        
        Returns:
            Recommended d_model
        """
        # Check if manually overridden in config (None means auto-compute)
        if self._config.get("d_model") is not None:
            return self._config["d_model"]

        # Auto-compute based on tiers
        if num_columns < 10:
            return 64
        elif num_columns < 30:
            return 128
        elif num_columns < 60:
            return 192
        else:
            return 256
    
    def get_all(self) -> Dict[str, Any]:
        """Get all configuration as a dictionary."""
        return self._config.copy()
    
    def get_enable_embedding_diversity_loss(self) -> bool:
        """
        Get whether to enable embedding diversity loss during ES training.
        
        Can be set via:
        1. Environment variable: FEATRIX_ENABLE_EMBEDDING_DIVERSITY_LOSS=1 or 0 (highest priority)
        2. config.json: "enable_embedding_diversity_loss": true
        
        When True:
        - Adds a variance-based diversity loss to encourage embeddings to spread out
        - Helps prevent embedding collapse where all embeddings become similar
        - Loss penalizes low per-dimension variance across the batch
        
        When False:
        - Only uses standard losses (spread, joint, marginal)
        - No explicit diversity enforcement
        
        Default: True (ENABLED - critical for preventing global collapse)
        
        Background: Introduced to address embedding collapse issues where validation
        loss looked good but embeddings were compressed to a small region of space
        (e.g., alphafreight-mini with std/dim=0.0028). Spread loss prevents LOCAL
        collapse (within batch) but not GLOBAL collapse (across all batches).
        
        Note: This is essential for training stability. Only disable for ablation studies.
        """
        # Check environment variable first (highest priority)
        env_val = os.environ.get("FEATRIX_ENABLE_EMBEDDING_DIVERSITY_LOSS", "").strip()
        if env_val == "1":
            return True
        elif env_val == "0":
            return False
        # Fall back to config.json
        return self._config.get("enable_embedding_diversity_loss", DEFAULT_CONFIG.get("enable_embedding_diversity_loss", True))
    
    def get_embedding_diversity_weight(self) -> float:
        """
        Get the weight for embedding diversity loss (if enabled).
        
        Can be set via:
        1. Environment variable: FEATRIX_EMBEDDING_DIVERSITY_WEIGHT=<float> (highest priority)
        2. config.json: "embedding_diversity_weight": <float>
        
        This controls how strongly the diversity loss affects training.
        Typical values: 0.5-2.0
        - Too low (<0.5): diversity loss has minimal effect, collapse may still occur
        - Good range (0.5-2.0): balanced with other losses (spread, joint, marginal)
        - Too high (>2.0): may interfere with primary objectives
        
        Default: 1.0 (equal weight with spread_loss_weight)
        
        Rationale: Diversity loss prevents GLOBAL collapse (all batches in same region)
        while spread loss prevents LOCAL collapse (rows in same batch being identical).
        These are equally important failure modes, hence equal default weights.
        
        Only used if get_enable_embedding_diversity_loss() returns True.
        """
        # Check environment variable first (highest priority)
        env_val = os.environ.get("FEATRIX_EMBEDDING_DIVERSITY_WEIGHT", "").strip()
        if env_val:
            try:
                val = float(env_val)
                if val > 0:
                    return val
            except ValueError:
                pass
        # Fall back to config.json
        return self._config.get("embedding_diversity_weight", DEFAULT_CONFIG.get("embedding_diversity_weight", 1.0))

    def get_enable_spread_loss(self) -> bool:
        """
        Get whether to enable spread loss during ES training.

        Can be set via:
        1. Environment variable: FEATRIX_ENABLE_SPREAD_LOSS=1 or 0 (highest priority)
        2. config.json: "enable_spread_loss": true/false

        When True:
        - Spread loss (triplet-style contrastive loss) is included in total loss
        - Encourages different rows to have different joint embeddings

        When False:
        - Spread loss is disabled (set to 0)
        - Only joint, marginal, diversity, and reconstruction losses are used

        Default: True (spread loss enabled)

        Rationale: Spread loss was originally designed to prevent embedding collapse,
        but with diversity loss also preventing collapse, spread loss may be redundant.
        Disable for ablation testing to see if it improves training.
        """
        # Check environment variable first (highest priority)
        env_val = os.environ.get("FEATRIX_ENABLE_SPREAD_LOSS", "").strip()
        if env_val in ("1", "true", "yes"):
            return True
        elif env_val in ("0", "false", "no"):
            return False
        # Fall back to config.json
        return self._config.get("enable_spread_loss", DEFAULT_CONFIG.get("enable_spread_loss", True))

    def get_use_muon_optimizer(self) -> bool:
        """
        Get whether to use Muon optimizer instead of AdamW.

        Can be set via:
        1. Environment variable: FEATRIX_USE_MUON=1 or 0 (highest priority)
        2. config.json: "use_muon_optimizer": true

        When True:
        - Uses Muon optimizer (requires muon package to be installed)
        - Muon is a momentum-based optimizer designed for neural network training
        - May provide faster convergence on some tasks
        - Falls back to AdamW if muon package is not available

        When False:
        - Uses AdamW optimizer (default behavior)
        - Priority: 8-bit AdamW > Fused AdamW > Regular AdamW

        Default: False (use AdamW)

        Note: This is an experimental feature. Muon may not work well with all
        architectures or learning rate schedules. Test thoroughly before using in production.
        """
        # Check environment variable first (highest priority)
        env_val = os.environ.get("FEATRIX_USE_MUON", "").strip()
        if env_val in ("1", "true", "yes"):
            return True
        elif env_val in ("0", "false", "no"):
            return False
        # Fall back to config.json
        return self._config.get("use_muon_optimizer", DEFAULT_CONFIG.get("use_muon_optimizer", False))

    def get_enable_reconstruction_loss(self) -> bool:
        """
        Get whether to enable direct value reconstruction loss in marginal loss.

        Can be set via:
        1. Environment variable: FEATRIX_ENABLE_RECONSTRUCTION_LOSS=1 or 0 (highest priority)
        2. config.json: "enable_reconstruction_loss": true

        When True:
        - Adds a direct value prediction head to each column predictor
        - Scalars: MSE loss between predicted and actual normalized value
        - Sets/Categoricals: CrossEntropy loss between predicted class logits and actual class
        - This provides direct supervision to ensure embeddings preserve value information

        When False:
        - Only uses InfoNCE contrastive loss (default behavior)
        - Marginal loss only requires predictions to be "closer" to correct targets in batch

        Default: False (for ablation testing - enable explicitly to test)

        Rationale: Contrastive loss alone can lead to mode collapse where predictions
        always output the "average" embedding. Direct reconstruction forces the model
        to preserve actual value information in the embeddings.
        """
        env_val = os.environ.get("FEATRIX_ENABLE_RECONSTRUCTION_LOSS", "").strip()
        if env_val in ("1", "true", "yes"):
            return True
        elif env_val in ("0", "false", "no"):
            return False
        return self._config.get("enable_reconstruction_loss", DEFAULT_CONFIG.get("enable_reconstruction_loss", False))

    def get_reconstruction_loss_weight(self) -> float:
        """
        Get the weight for reconstruction loss (if enabled).

        Can be set via:
        1. Environment variable: FEATRIX_RECONSTRUCTION_LOSS_WEIGHT=<float> (highest priority)
        2. config.json: "reconstruction_loss_weight": <float>

        This controls how strongly the reconstruction loss affects training relative to InfoNCE.
        Typical values: 0.1-2.0
        - Too low (<0.1): reconstruction has minimal effect
        - Good range (0.5-2.0): balanced with contrastive loss
        - Too high (>2.0): may dominate and ignore contrastive structure

        Default: 1.0 (equal weight with InfoNCE loss)

        Only used if get_enable_reconstruction_loss() returns True.
        """
        env_val = os.environ.get("FEATRIX_RECONSTRUCTION_LOSS_WEIGHT", "").strip()
        if env_val:
            try:
                val = float(env_val)
                if val > 0:
                    return val
            except ValueError:
                pass
        return self._config.get("reconstruction_loss_weight", DEFAULT_CONFIG.get("reconstruction_loss_weight", 1.0))

    def get_sp_es_lr_ratio(self) -> float:
        """
        Get the ratio of encoder LR to predictor LR during SP fine-tuning.

        Can be set via:
        1. Environment variable: FEATRIX_SP_ES_LR_RATIO=<float> (highest priority)
        2. config.json: "sp_es_lr_ratio": <float>

        This controls how fast the encoder learns relative to the predictor during
        single predictor training with fine_tune=True.

        Formula: encoder_lr = predictor_lr * sp_es_lr_ratio

        Typical values:
        - 0.0: Frozen encoder (head-only training, safest for small labeled datasets)
        - 0.02: Very conservative fine-tuning (encoder LR = 2e-6)
        - 0.05: Safe fine-tuning (encoder LR = 5e-6) - lets head do the work, encoder only nudges
        - 0.10: Hard cap (maximum allowed value)

        Default: 0.05 (safe fine-tuning - encoder learns at 5% of predictor rate)
        Hard cap: 0.10 (prevents encoder from overwhelming predictor)

        Rationale: With a good embedding space (Recall@1 > 70%), full joint fine-tuning
        can be counterproductive with limited labels (<1000). Lower ratios let the
        predictor head do the work while the encoder only makes small corrections.
        """
        ES_LR_RATIO_CAP = 0.10  # Hard cap to prevent encoder overwhelming predictor

        env_val = os.environ.get("FEATRIX_SP_ES_LR_RATIO", "").strip()
        if env_val:
            try:
                val = float(env_val)
                if val >= 0:  # Allow 0 for frozen encoder
                    # Apply hard cap
                    return min(val, ES_LR_RATIO_CAP)
            except ValueError:
                pass

        ratio = self._config.get("sp_es_lr_ratio", DEFAULT_CONFIG.get("sp_es_lr_ratio", 0.05))
        # Apply hard cap to config value too
        return min(ratio, ES_LR_RATIO_CAP)

    def get_sp_freeze_epochs(self) -> int:
        """
        Get the number of epochs to freeze ES during SP training.

        Can be set via:
        1. Environment variable: FEATRIX_SP_FREEZE_EPOCHS=<int> (highest priority)
        2. config.json: "sp_freeze_epochs": <int>

        When set to a positive integer:
        - ES is frozen for exactly this many epochs at the start of SP training
        - Predictor learns from stable embeddings before encoder fine-tuning begins
        - After freeze period, ES is unfrozen and both train jointly

        When None or 0:
        - Uses default: 5% of total epochs (min 1 epoch if total > 5)
        - If total epochs <= 5, no freezing (not enough time for warmup)

        Default: None (use 5% heuristic)

        Rationale: Freezing the ES initially allows the predictor to learn useful
        features from stable embeddings. Once the predictor has a reasonable signal,
        the ES can be unfrozen to fine-tune for the specific prediction task.

        Use cases:
        - sp_freeze_epochs=50: Freeze ES for 50 epochs (e.g., for 100-epoch run, 50% frozen)
        - sp_freeze_epochs=0: No freezing, train both from epoch 0
        - sp_freeze_epochs=None: Use 5% heuristic
        """
        env_val = os.environ.get("FEATRIX_SP_FREEZE_EPOCHS", "").strip()
        if env_val:
            try:
                val = int(env_val)
                return val  # Allow 0 to mean "no freezing"
            except ValueError:
                pass
        return self._config.get("sp_freeze_epochs", DEFAULT_CONFIG.get("sp_freeze_epochs", None))

    def get_sp_n_hidden_layers(self) -> int:
        """
        Get the number of hidden layers for SP predictor MLP.

        Can be set via:
        1. Environment variable: FEATRIX_SP_N_HIDDEN_LAYERS=<int> (highest priority)
        2. config.json: "sp_n_hidden_layers": <int>

        Common values:
        - 0: Linear model (no hidden layers)
        - 1: Single hidden layer (simple, fast)
        - 2: Two hidden layers (default in most cases)
        - 3: Three hidden layers (more expressive)

        Default: None (use value from training args, typically 2)
        """
        env_val = os.environ.get("FEATRIX_SP_N_HIDDEN_LAYERS", "").strip()
        if env_val:
            try:
                val = int(env_val)
                if val >= 0:
                    return val
            except ValueError:
                pass
        return self._config.get("sp_n_hidden_layers", DEFAULT_CONFIG.get("sp_n_hidden_layers", None))

    def get_sp_d_hidden(self) -> Optional[int]:
        """
        Get the hidden dimension for SP predictor MLP.

        Can be set via:
        1. Environment variable: FEATRIX_SP_D_HIDDEN=<int> (highest priority)
        2. config.json: "sp_d_hidden": <int>

        Common values:
        - 64: Very small predictor (for tiny datasets or fast inference)
        - 128: Small predictor (good for <500 rows, reduces overfitting)
        - 256: Default (matches d_model of embedding space)
        - 512: Large predictor (for complex decision boundaries)

        Default: None (use es.d_model, typically 256)
        """
        env_val = os.environ.get("FEATRIX_SP_D_HIDDEN", "").strip()
        if env_val:
            try:
                val = int(env_val)
                if val > 0:
                    return val
            except ValueError:
                pass
        return self._config.get("sp_d_hidden", DEFAULT_CONFIG.get("sp_d_hidden", None))

    def get_sp_dropout(self) -> Optional[float]:
        """
        Get the dropout rate for SP predictor.

        Can be set via:
        1. Environment variable: FEATRIX_SP_DROPOUT=<float> (highest priority)
        2. config.json: "sp_dropout": <float>

        When set to a value (0.0-1.0):
        - Uses this exact dropout rate for the SP predictor MLP
        - Overrides auto-computation

        When None:
        - Auto-computes dropout based on dataset size and class imbalance
        - See _compute_adaptive_dropout() in single_predictor.py

        Recommended values by dataset characteristics:
        - Very small (<200 rows) or highly imbalanced: 0.05-0.1
        - Small (200-500 rows): 0.1-0.2
        - Medium (500-2000 rows): 0.2-0.3
        - Large (2000+ rows): 0.3-0.4

        Default: None (auto-compute)
        """
        env_val = os.environ.get("FEATRIX_SP_DROPOUT", "").strip()
        if env_val:
            try:
                val = float(env_val)
                if 0.0 <= val <= 1.0:
                    return val
            except ValueError:
                pass
        return self._config.get("sp_dropout", DEFAULT_CONFIG.get("sp_dropout", None))

    # ========================================================================
    # Hyperparameter Search Configuration
    # ========================================================================

    def get_hyperparam_search_file(self) -> Optional[str]:
        """Get path to ThingsToTry JSON file for hyperparameter search."""
        return self._config.get("hyperparam_search_file", DEFAULT_CONFIG.get("hyperparam_search_file", None))

    def get_hyperparam_results_file(self) -> Optional[str]:
        """Get path to ThingsTried JSON file for results."""
        return self._config.get("hyperparam_results_file", DEFAULT_CONFIG.get("hyperparam_results_file", None))

    def get_hyperparam_evaluate_at_epoch(self) -> int:
        """Get epoch at which to evaluate experiments."""
        return self._config.get("hyperparam_evaluate_at_epoch", DEFAULT_CONFIG.get("hyperparam_evaluate_at_epoch", 20))

    def get_sp_adaptive_dropout(self) -> bool:
        """Get whether adaptive dropout is enabled (increases when AUC plateaus)."""
        return self._config.get("sp_adaptive_dropout", DEFAULT_CONFIG.get("sp_adaptive_dropout", False))

    def get_sp_label_smoothing(self) -> float:
        """Get label smoothing factor (0.0 = disabled)."""
        return self._config.get("sp_label_smoothing", DEFAULT_CONFIG.get("sp_label_smoothing", 0.0))

    def get_sp_weight_decay(self) -> float:
        """Get weight decay for optimizer (0.0 = disabled)."""
        return self._config.get("sp_weight_decay", DEFAULT_CONFIG.get("sp_weight_decay", 0.0))

    def get_sp_oscillation_amplitude(self) -> float:
        """Get LR oscillation amplitude (0.0 = disabled, 0.15 = ±15%)."""
        return self._config.get("sp_oscillation_amplitude", DEFAULT_CONFIG.get("sp_oscillation_amplitude", 0.15))

    def get_sp_batch_size(self) -> Optional[int]:
        """Get batch size override (None = use default)."""
        return self._config.get("sp_batch_size", DEFAULT_CONFIG.get("sp_batch_size", None))

    def get_sp_lr_schedule(self) -> str:
        """Get LR schedule type: 'LRTimeline' or 'OneCycleLR'."""
        return self._config.get("sp_lr_schedule", DEFAULT_CONFIG.get("sp_lr_schedule", "LRTimeline"))

    # ========================================================================
    # SP Loss Ablation Controls
    # ========================================================================

    def get_sp_adaptive_focal_loss(self) -> bool:
        """Get whether adaptive FocalLoss adjustments are enabled mid-training."""
        return self._config.get("sp_adaptive_focal_loss", DEFAULT_CONFIG.get("sp_adaptive_focal_loss", True))

    def get_sp_pairwise_ranking_loss(self) -> bool:
        """Get whether pairwise ranking loss component is enabled."""
        return self._config.get("sp_pairwise_ranking_loss", DEFAULT_CONFIG.get("sp_pairwise_ranking_loss", True))

    def get_sp_pairwise_ranking_weight(self) -> float:
        """Get weight for pairwise ranking loss (if enabled)."""
        return self._config.get("sp_pairwise_ranking_weight", DEFAULT_CONFIG.get("sp_pairwise_ranking_weight", 0.1))

    def get_sp_logit_clamp(self) -> bool:
        """Get whether logit clamping to [-20, 20] is enabled."""
        return self._config.get("sp_logit_clamp", DEFAULT_CONFIG.get("sp_logit_clamp", True))

    def get_sp_use_focal_loss(self) -> bool:
        """Get whether to use FocalLoss (False = use CrossEntropyLoss)."""
        return self._config.get("sp_use_focal_loss", DEFAULT_CONFIG.get("sp_use_focal_loss", True))

    def get_sp_focal_gamma_adaptable(self) -> bool:
        """Get whether to use classic FocalLoss with adaptive gamma adjustments (legacy behavior).

        When True: Uses FocalLoss(gamma=2.0, min_weight=0.1) with runtime gamma/min_weight
                   adjustments based on class prediction bias detection.
        When False: Uses CostSensitiveFocalLoss with fixed costs derived from class imbalance.
        """
        return self._config.get("sp_focal_gamma_adaptable", DEFAULT_CONFIG.get("sp_focal_gamma_adaptable", False))

    def get_sp_adaptive_loss_type(self) -> str:
        """
        Get the adaptive loss type for single predictor training.

        Options:
        - "voting": Win-rate based weights (AdaptiveVotingLoss) - weights based on which loss is lowest each batch
        - "learning": Gradient-learned weights (AdaptiveLearningLoss) - weights learned via backprop

        Can be set via:
        1. Environment variable: FEATRIX_SP_ADAPTIVE_LOSS_TYPE=voting or learning (highest priority)
        2. config.json: "sp_adaptive_loss_type": "learning"

        Default: "learning" (original approach, uses gradient descent to learn weights)

        Note: "voting" has been observed to create self-reinforcing feedback loops where
        whichever loss happens to be lowest early gets higher weight, starving other losses.
        """
        env_val = os.environ.get("FEATRIX_SP_ADAPTIVE_LOSS_TYPE", "").strip().lower()
        if env_val in ("voting", "learning"):
            return env_val
        return self._config.get("sp_adaptive_loss_type", DEFAULT_CONFIG.get("sp_adaptive_loss_type", "learning"))

    # ========================================================================
    # Type-Aware Relationship Operations Configuration
    # ========================================================================

    def get_enable_type_aware_ops(self) -> bool:
        """
        Get whether to enable type-aware relationship operations.

        Can be set via:
        1. Environment variable: FEATRIX_ENABLE_TYPE_AWARE_OPS=1 or 0 (highest priority)
        2. config.json: "enable_type_aware_ops": true

        When True:
        - Uses specialized ops for type-specific column pairs:
          - Set × Timestamp: temporal gating, cross-attention
          - Scalar × Timestamp: cyclical correlation, trend encoding
          - Set × Set: co-occurrence attention, bilinear interaction
          - Set × Scalar: conditioned gating
          - Scalar × Scalar: ratio encoding

        When False:
        - Uses generic element-wise multiplication for all pairs
        - Faster, simpler

        Default: False (experimental, disabled by default)
        """
        env_val = os.environ.get("FEATRIX_ENABLE_TYPE_AWARE_OPS", "").strip()
        if env_val == "1":
            return True
        elif env_val == "0":
            return False
        return self._config.get("enable_type_aware_ops", DEFAULT_CONFIG.get("enable_type_aware_ops", False))

    # ========================================================================
    # Adam Optimizer Configuration
    # ========================================================================

    def get_adam_eps(self) -> float:
        """
        Get the epsilon value for Adam/AdamW optimizer.

        Can be set via:
        1. Environment variable: FEATRIX_ADAM_EPS=<float> (highest priority)
        2. config.json: "adam_eps": <float>

        This controls numerical stability in Adam's denominator: θ = θ - lr * m / (√v + eps)

        Common values:
        - 1e-8: PyTorch default, good for most cases
        - 1e-10: Smoother optimization curves, may help with noisy gradients
        - 1e-6: More aggressive, can help escape sharp minima

        Default: 1e-8 (PyTorch default)

        Ablation testing: Try 1e-10 for potentially smoother loss curves.
        """
        env_val = os.environ.get("FEATRIX_ADAM_EPS", "").strip()
        if env_val:
            try:
                val = float(env_val)
                if val > 0:
                    return val
            except ValueError:
                pass
        return self._config.get("adam_eps", DEFAULT_CONFIG.get("adam_eps", 1e-8))

    def apply_experiment_overrides(self, changes: Dict[str, Any]) -> None:
        """
        Apply experiment hyperparameter overrides to config.

        Args:
            changes: Dict of parameter changes from experiment, e.g.:
                     {"dropout": 0.2, "n_hidden_layers": 3}
        """
        # Map experiment keys to config keys
        key_mapping = {
            "dropout": "sp_dropout",
            "n_hidden_layers": "sp_n_hidden_layers",
            "d_hidden": "sp_d_hidden",
            "attention_heads": "predictor_attention_heads",
            "adaptive_dropout": "sp_adaptive_dropout",
            "label_smoothing": "sp_label_smoothing",
            "weight_decay": "sp_weight_decay",
            "oscillation_amplitude": "sp_oscillation_amplitude",
            "batch_size": "sp_batch_size",
            "lr_schedule": "sp_lr_schedule",
            # Ablation controls
            "adaptive_focal_loss": "sp_adaptive_focal_loss",
            "pairwise_ranking_loss": "sp_pairwise_ranking_loss",
            "pairwise_ranking_weight": "sp_pairwise_ranking_weight",
            "logit_clamp": "sp_logit_clamp",
            "use_focal_loss": "sp_use_focal_loss",
        }

        for exp_key, value in changes.items():
            config_key = key_mapping.get(exp_key, exp_key)
            self._config[config_key] = value
            logger.info(f"   📝 Experiment override: {config_key} = {value}")

            # Special case: attention_heads=0 means disable attention entirely
            if exp_key == "attention_heads" and value == 0:
                self._config["enable_predictor_attention"] = False
                logger.info(f"   📝 Experiment override: enable_predictor_attention = False (attention_heads=0)")

    def log_config(self, prefix: str = ""):
        """
        Log all configuration parameters.

        Args:
            prefix: Optional prefix for log messages
        """
        logger.info(f"{prefix}🔧 Sphere Configuration:")
        for key, value in self._config.items():
            logger.info(f"{prefix}   {key}: {value}")


def get_d_model() -> Optional[int]:
    """
    Convenience function to get d_model from configuration.

    Returns:
        d_model value if explicitly set, None if auto-compute should be used.
        Callers should use auto_compute_d_model(num_columns) when None is returned.

    Example:
        from featrix.neural.sphere_config import get_d_model, get_config

        d_model = get_d_model()
        if d_model is None:
            d_model = get_config().auto_compute_d_model(num_columns)
    """
    return SphereConfig.get_instance().get_d_model()


def get_config() -> SphereConfig:
    """
    Convenience function to get the configuration instance.
    
    Returns:
        SphereConfig instance
    
    Example:
        from featrix.neural.sphere_config import get_config
        
        config = get_config()
        d_model = config.get_d_model()
        learning_rate = config.get("learning_rate", 0.001)
    """
    return SphereConfig.get_instance()


if __name__ == "__main__":
    # Demo usage
    print("Sphere Configuration Demo")
    print("=" * 60)
    
    config = get_config()
    config.log_config()
    
    print(f"\nGetting specific values:")
    print(f"  d_model: {config.get_d_model()}")
    print(f"  custom_key (default=42): {config.get('custom_key', 42)}")

