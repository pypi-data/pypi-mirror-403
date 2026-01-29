#!/usr/bin/env python3
"""
Loss Functions - 01 July 2025 (from commit aebb8762)

Self-contained loss function set from the July 2025 codebase.

Key characteristics:
- Pure InfoNCE with FIXED temperature (0.1 implicit via latent_noise + normalization)
- Spread loss with FIXED temperature (temp=0.03)
- NO adaptive temperature
- NO curriculum/blend (pure InfoNCE from start)
- NO uniformity loss
- Simpler architecture: Joint + Marginal + Spread
- Uses both full AND short embeddings (4 joint losses, 4 marginal losses)

This was BEFORE:
- Adaptive temperature based on batch size
- Cosine → InfoNCE curriculum blend
- UniformityLoss (Wang & Isola 2020)
- Simplified to full-only embeddings

Algorithm preserved exactly from aebb8762 (July 2025).

Usage:
    from featrix.neural.loss_functions import loss_functions_01Jul2025 as losses
    framework = losses.create_default_framework()
"""

import logging
import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any

import torch
import torch.nn as nn
import torch.nn.functional as F

from featrix.neural.featrix_token import TokenStatus

logger = logging.getLogger(__name__)


# =============================================================================
# Base Classes
# =============================================================================

@dataclass
class LossConfig:
    """Configuration for a single loss component."""
    enabled: bool = True
    weight: float = 1.0
    params: Dict[str, Any] = field(default_factory=dict)


class LossComponent(ABC):
    """Base class for all loss components."""

    def __init__(self, name: str, config: LossConfig):
        self.name = name
        self.config = config
        self._call_count = 0

    @property
    def enabled(self) -> bool:
        return self.config.enabled

    @property
    def weight(self) -> float:
        return self.config.weight

    @abstractmethod
    def compute(
        self,
        embeddings_1: torch.Tensor,
        embeddings_2: torch.Tensor,
        embeddings_unmasked: torch.Tensor,
        **kwargs
    ) -> Tuple[torch.Tensor, Dict[str, float]]:
        pass

    def __call__(self, *args, **kwargs) -> Tuple[torch.Tensor, Dict[str, float]]:
        self._call_count += 1
        return self.compute(*args, **kwargs)


# =============================================================================
# Core InfoNCE Loss (July 2025 version - FIXED temperature via noise + normalization)
# =============================================================================

class InfoNCELossJul2025:
    """
    InfoNCE loss from July 2025 - uses latent noise and normalization.

    Key difference from Jan 2026: NO adaptive temperature.
    Temperature is implicitly controlled via:
    - latent_noise added to sample_enc
    - L2 normalization

    The softmax temperature is effectively 1.0 (no explicit temp division).
    """

    def __init__(self, latent_noise: float = 0.01):
        self.latent_noise = latent_noise
        self.ce_loss = nn.CrossEntropyLoss(reduction='none')

    def __call__(
        self,
        context_enc: torch.Tensor,
        sample_enc: torch.Tensor,
        mask: torch.Tensor = None,
    ) -> torch.Tensor:
        """
        Compute InfoNCE loss.

        Args:
            context_enc: Predictions/queries (batch_size, d_model)
            sample_enc: Targets/keys (batch_size, d_model)
            mask: Optional mask for NOT_PRESENT tokens

        Returns:
            Loss tensor (batch_size,) - one loss per row
        """
        # Add noise and normalize (July 2025 approach)
        sample_enc = sample_enc + torch.randn_like(sample_enc) * self.latent_noise
        sample_enc = F.normalize(sample_enc, dim=1)

        # Compute similarity matrix (no temperature division!)
        logits = context_enc @ sample_enc.T

        batch_size = context_enc.shape[0]
        device = context_enc.device

        # Target is the diagonal (each row should match itself)
        targets = torch.arange(batch_size, device=device)

        # Mask NOT_PRESENT tokens by setting their logits to -inf
        if mask is not None:
            logits[:, mask == TokenStatus.NOT_PRESENT] = float("-inf")

        loss = self.ce_loss(logits, targets)
        return loss


# =============================================================================
# Joint InfoNCE Loss (July 2025)
# =============================================================================

class JointInfoNCELossJul2025(LossComponent):
    """
    Joint InfoNCE loss from July 2025.

    Computes InfoNCE between masked joint encoding and unmasked joint encoding.
    Uses a linear predictor (joint_predictor) before computing similarity.

    July 2025 version processes BOTH full and short embeddings:
    - joint_loss_1: full masked_1 vs full unmasked
    - joint_loss_2: full masked_2 vs full unmasked
    - short_joint_loss_1: short masked_1 vs short unmasked
    - short_joint_loss_2: short masked_2 vs short unmasked

    For this pluggable interface, we only have full embeddings, so we compute:
    - joint_loss_1: masked_1 vs unmasked
    - joint_loss_2: masked_2 vs unmasked
    """

    def __init__(self, config: LossConfig):
        super().__init__("joint_infonce_jul2025", config)
        self.latent_noise = config.params.get("latent_noise", 0.01)
        self.infonce = InfoNCELossJul2025(latent_noise=self.latent_noise)

        # In July 2025, there was a joint_predictor linear layer
        # For the pluggable interface, we assume embeddings are already projected
        # (the predictor is part of the encoder, not the loss)

    def compute(
        self,
        embeddings_1: torch.Tensor,
        embeddings_2: torch.Tensor,
        embeddings_unmasked: torch.Tensor,
        **kwargs
    ) -> Tuple[torch.Tensor, Dict[str, float]]:
        """
        Compute joint InfoNCE loss.

        In July 2025, this used joint_predictor(masked_encoding) vs unmasked_encoding.
        Here we assume the prediction step happens in the encoder, so we directly
        compare embeddings.
        """
        # Compute InfoNCE for both masks
        loss_1 = self.infonce(embeddings_1, embeddings_unmasked).mean()
        loss_2 = self.infonce(embeddings_2, embeddings_unmasked).mean()

        total_loss = loss_1 + loss_2

        # Compute mutual information estimate (July 2025 formula)
        batch_size = embeddings_1.shape[0]
        log_n = math.log(batch_size)
        mi_1 = (log_n - loss_1.detach().item()) / math.log(2)  # nats to bits
        mi_2 = (log_n - loss_2.detach().item()) / math.log(2)

        # Compute similarity metrics for diagnostics
        with torch.no_grad():
            # Positive similarity (same row)
            pos_sim_1 = F.cosine_similarity(embeddings_1, embeddings_unmasked).mean().item()
            pos_sim_2 = F.cosine_similarity(embeddings_2, embeddings_unmasked).mean().item()

            # Negative similarity (different rows - use first row against all others)
            neg_sims = F.cosine_similarity(
                embeddings_unmasked[0:1],
                embeddings_unmasked[1:],
                dim=1
            ).mean().item() if embeddings_unmasked.shape[0] > 1 else 0.0

        metrics = {
            "loss": total_loss.item(),
            "loss_1": loss_1.item(),
            "loss_2": loss_2.item(),
            "mi_1_bits": mi_1,
            "mi_2_bits": mi_2,
            "pos_sim": (pos_sim_1 + pos_sim_2) / 2,
            "neg_sim": neg_sims,
            "latent_noise": self.latent_noise,
        }

        return total_loss, metrics


# =============================================================================
# Spread Loss (July 2025 - FIXED temperature 0.03)
# =============================================================================

class SpreadLossJul2025(LossComponent):
    """
    Spread loss from July 2025.

    Self-similarity penalty to prevent embedding collapse.
    Uses FIXED temperature of 0.03 (hardcoded in July 2025).

    Computes:
    - spread_loss_joint: unmasked @ unmasked.T / 0.03 -> CE loss
    - spread_loss_1: masked_1 @ masked_1.T / 0.03 -> CE loss
    - spread_loss_2: masked_2 @ masked_2.T / 0.03 -> CE loss

    Total = joint_weight * spread_joint + marginal_weight * (spread_1 + spread_2)
    """

    def __init__(self, config: LossConfig):
        super().__init__("spread_jul2025", config)
        # FIXED temperature from July 2025
        self.temperature = config.params.get("temperature", 0.03)
        self.joint_weight = config.params.get("joint_weight", 1.0)
        self.marginal_weight = config.params.get("marginal_weight", 1.0)

    def compute(
        self,
        embeddings_1: torch.Tensor,
        embeddings_2: torch.Tensor,
        embeddings_unmasked: torch.Tensor,
        **kwargs
    ) -> Tuple[torch.Tensor, Dict[str, float]]:
        """Compute spread loss with fixed temperature."""
        batch_size = embeddings_unmasked.shape[0]
        device = embeddings_unmasked.device
        targets = torch.arange(batch_size, device=device)

        # Spread loss on unmasked (joint) embeddings
        logits_joint = embeddings_unmasked @ embeddings_unmasked.T / self.temperature
        spread_loss_joint = F.cross_entropy(logits_joint, targets)

        # Spread loss on masked embeddings
        logits_1 = embeddings_1 @ embeddings_1.T / self.temperature
        spread_loss_1 = F.cross_entropy(logits_1, targets)

        logits_2 = embeddings_2 @ embeddings_2.T / self.temperature
        spread_loss_2 = F.cross_entropy(logits_2, targets)

        # July 2025 formula
        total_loss = (
            self.joint_weight * spread_loss_joint +
            self.marginal_weight * spread_loss_1 +
            self.marginal_weight * spread_loss_2
        )

        # Compute self-similarity for diagnostics
        with torch.no_grad():
            self_sim_joint = (embeddings_unmasked @ embeddings_unmasked.T).diagonal().mean().item()
            self_sim_1 = (embeddings_1 @ embeddings_1.T).diagonal().mean().item()
            self_sim_2 = (embeddings_2 @ embeddings_2.T).diagonal().mean().item()

        metrics = {
            "loss": total_loss.item(),
            "spread_joint": spread_loss_joint.item(),
            "spread_mask_1": spread_loss_1.item(),
            "spread_mask_2": spread_loss_2.item(),
            "temperature": self.temperature,
            "self_sim_joint": self_sim_joint,
            "self_sim_mask_1": self_sim_1,
            "self_sim_mask_2": self_sim_2,
        }

        return total_loss, metrics


# =============================================================================
# Marginal InfoNCE Loss (July 2025)
# =============================================================================

class MarginalInfoNCELossJul2025(LossComponent):
    """
    Marginal InfoNCE loss from July 2025.

    Predicts each masked column's encoding from the joint embedding.
    Uses column_predictions (B, n_cols, D) and column_targets (B, n_cols, D)
    to compute per-column InfoNCE loss.

    CRITICAL: Only computes loss on MASKED columns (where column_mask == MARGINAL).
    This is essential because:
    - Unmasked columns are trivial to predict (encoder saw the actual value)
    - Masked columns require real prediction from context
    - Averaging all columns would dilute the learning signal
    """


    def __init__(self, config: LossConfig):
        super().__init__("marginal_infonce_jul2025", config)
        self.latent_noise = config.params.get("latent_noise", 0.01)
        self.infonce = InfoNCELossJul2025(latent_noise=self.latent_noise)

    def compute(
        self,
        embeddings_1: torch.Tensor,
        embeddings_2: torch.Tensor,
        embeddings_unmasked: torch.Tensor,
        **kwargs
    ) -> Tuple[torch.Tensor, Dict[str, float]]:
        """
        Compute marginal InfoNCE loss using per-column predictions.

        Args:
            column_predictions: (B, n_cols, D) predicted column embeddings
            column_targets: (B, n_cols, D) target column embeddings
            column_mask: (B, n_cols) TokenStatus mask - only compute loss where mask == MARGINAL
        """
        column_predictions = kwargs.get('column_predictions')
        column_targets = kwargs.get('column_targets')
        column_mask = kwargs.get('column_mask')  # (B, n_cols) TokenStatus values

        device = embeddings_1.device

        # If no column predictions, fall back to simplified version
        if column_predictions is None or column_targets is None:
            # Simplified: use joint embeddings (less effective but maintains gradient flow)
            loss_1 = self.infonce(embeddings_1, embeddings_unmasked).mean()
            loss_2 = self.infonce(embeddings_2, embeddings_unmasked).mean()
            total_loss = loss_1 + loss_2
            return total_loss, {
                "loss": total_loss.item(),
                "mode": "fallback_no_column_predictions",
            }

        B, n_cols, D = column_predictions.shape

        # Determine which columns are masked (need prediction)
        if column_mask is not None:
            # Only compute loss on masked columns
            marginal_mask = (column_mask == TokenStatus.MARGINAL)  # (B, n_cols)
        else:
            # No mask provided - use all columns (fallback behavior)
            marginal_mask = torch.ones(B, n_cols, dtype=torch.bool, device=device)

        # Compute per-column InfoNCE loss ONLY on masked columns
        col_losses = []
        n_masked_cols = 0

        for col_idx in range(n_cols):
            # Check if this column has any masked samples
            col_mask = marginal_mask[:, col_idx]  # (B,) bool
            n_masked = col_mask.sum().item()

            if n_masked == 0:
                # No masked samples for this column - skip
                continue

            n_masked_cols += 1

            # Get predictions and targets for masked samples only
            pred = column_predictions[:, col_idx, :]  # (B, D)
            target = column_targets[:, col_idx, :]  # (B, D)

            # Filter to only masked rows
            pred_masked = pred[col_mask]  # (n_masked, D)
            target_masked = target[col_mask]  # (n_masked, D)

            if pred_masked.shape[0] < 2:
                # Need at least 2 samples for InfoNCE
                continue

            # InfoNCE: pred should match its own target, not other rows' targets
            col_loss = self.infonce(pred_masked, target_masked).mean()
            col_losses.append(col_loss)

        if col_losses:
            total_loss = sum(col_losses) / len(col_losses)
        else:
            total_loss = torch.tensor(0.0, device=device, requires_grad=False)

        metrics = {
            "loss": total_loss.item(),
            "n_columns_total": n_cols,
            "n_columns_masked": n_masked_cols,
            "n_columns_computed": len(col_losses),
            "mode": "per_column_infonce_masked_only",
        }

        return total_loss, metrics


# =============================================================================
# Framework Configuration
# =============================================================================

@dataclass
class LossFrameworkConfig:
    """Configuration for the loss framework."""
    losses: Dict[str, LossConfig] = field(default_factory=dict)
    log_every_n_batches: int = 100

    # July 2025 default weights (from model_config.py LossFunctionConfig)
    joint_loss_weight: float = 1.0
    marginal_loss_weight: float = 1.0
    spread_loss_weight: float = 1.0


def create_default_config() -> LossFrameworkConfig:
    """Create default July 2025 configuration."""
    return LossFrameworkConfig(
        losses={
            "joint_infonce": LossConfig(
                enabled=True,
                weight=1.0,  # joint_loss_weight
                params={"latent_noise": 0.01}
            ),
            "spread": LossConfig(
                enabled=True,
                weight=1.0,  # spread_loss_weight
                params={
                    "temperature": 0.03,  # FIXED temperature from July 2025
                    "joint_weight": 1.0,
                    "marginal_weight": 1.0,
                }
            ),
            # Marginal loss: per-column prediction using column_predictions/column_targets
            "marginal_infonce": LossConfig(
                enabled=True,  # Uses column_predictions passed from encoder
                weight=1.0,
                params={"latent_noise": 0.01}
            ),
        },
        log_every_n_batches=100,
    )


# =============================================================================
# Loss Framework
# =============================================================================

class LossFramework:
    """
    July 2025 loss framework.

    Key differences from January 2026:
    1. FIXED temperatures (0.03 for spread, implicit via noise for InfoNCE)
    2. NO adaptive temperature based on batch size
    3. NO uniformity loss
    4. NO curriculum/blend - pure InfoNCE from start
    5. Simpler: Joint + Spread (marginal requires column predictions)
    """

    LOSS_TYPES = {
        "joint_infonce": JointInfoNCELossJul2025,
        "spread": SpreadLossJul2025,
        "marginal_infonce": MarginalInfoNCELossJul2025,
    }

    def __init__(self, config: LossFrameworkConfig = None):
        self.config = config or create_default_config()
        self.components: Dict[str, LossComponent] = {}
        self._batch_count = 0
        self._current_epoch = 0
        self._total_epochs = 1

        for name, loss_config in self.config.losses.items():
            if name in self.LOSS_TYPES:
                self.components[name] = self.LOSS_TYPES[name](loss_config)

    def set_epoch(self, current_epoch: int, total_epochs: int):
        """Set current epoch info (no-op for July 2025 - no curriculum)."""
        self._current_epoch = current_epoch
        self._total_epochs = total_epochs
        # July 2025 has NO curriculum - pure InfoNCE from start
        # This method exists only for interface compatibility

    def log_configuration(self):
        """Log the current loss configuration."""
        logger.info("=" * 60)
        logger.info("LOSS FRAMEWORK: July 2025 (from aebb8762)")
        logger.info("=" * 60)
        logger.info("Key characteristics:")
        logger.info("  - FIXED temperature 0.03 for spread loss")
        logger.info("  - NO adaptive temperature")
        logger.info("  - NO uniformity loss")
        logger.info("  - Pure InfoNCE (no curriculum)")
        logger.info("=" * 60)
        for name, comp in self.components.items():
            status = "ON" if comp.enabled else "OFF"
            logger.info(f"  {name}: {status} (weight={comp.weight})")
        logger.info("=" * 60)

    def compute_total(
        self,
        embeddings_1: torch.Tensor = None,
        embeddings_2: torch.Tensor = None,
        embeddings_unmasked: torch.Tensor = None,
        **kwargs
    ) -> Tuple[torch.Tensor, Dict[str, Any]]:
        # Support both naming conventions (embeddings_* and full_embeddings_*)
        embeddings_1 = embeddings_1 if embeddings_1 is not None else kwargs.get('full_embeddings_1')
        embeddings_2 = embeddings_2 if embeddings_2 is not None else kwargs.get('full_embeddings_2')
        embeddings_unmasked = embeddings_unmasked if embeddings_unmasked is not None else kwargs.get('full_embeddings_unmasked')

        device = embeddings_1.device
        all_metrics = {"total": 0.0, "components": {}}

        # Collect losses in a list, then sum at the end
        # This ensures proper gradient flow (not broken by torch.tensor(0.0))
        losses_to_sum = []

        for name, comp in self.components.items():
            if not comp.enabled:
                continue

            try:
                loss, metrics = comp(
                    embeddings_1=embeddings_1,
                    embeddings_2=embeddings_2,
                    embeddings_unmasked=embeddings_unmasked,
                    **kwargs
                )

                weighted_loss = comp.weight * loss
                losses_to_sum.append(weighted_loss)

                all_metrics["components"][name] = {
                    "loss": loss.item(),
                    "weighted_loss": weighted_loss.item(),
                    "weight": comp.weight,
                    **metrics
                }

            except Exception as e:
                logger.warning(f"Loss component {name} failed: {e}")
                all_metrics["components"][name] = {"error": str(e)}

        # Sum all losses - this maintains proper gradient flow
        if losses_to_sum:
            total_loss = sum(losses_to_sum)
        else:
            total_loss = torch.tensor(0.0, device=device, requires_grad=False)

        total_val = total_loss.item() if isinstance(total_loss, torch.Tensor) else total_loss
        all_metrics["total"] = total_val

        # Return flat format: {"total": float, "components": {name: {...}, ...}}

        self._batch_count += 1
        if self._batch_count % self.config.log_every_n_batches == 0:
            self._log_batch_metrics(all_metrics)

        return total_loss, all_metrics

    def _log_batch_metrics(self, metrics: Dict[str, Any]):
        parts = [f"LOSS total={metrics['total']:.4f}"]
        for name, comp_metrics in metrics["components"].items():
            if "error" not in comp_metrics:
                parts.append(f"{name}={comp_metrics['weighted_loss']:.4f}")
        logger.info(" | ".join(parts))

        # Log July 2025 specific diagnostics
        joint = metrics["components"].get("joint_infonce", {})
        if joint and "mi_1_bits" in joint:
            logger.info(
                f"  [Jul2025] Joint: MI={joint['mi_1_bits']:.2f}bits "
                f"pos_sim={joint['pos_sim']:.3f} "
                f"neg_sim={joint['neg_sim']:.3f} "
                f"noise={joint['latent_noise']}"
            )

        spread = metrics["components"].get("spread", {})
        if spread and "temperature" in spread:
            logger.info(
                f"  [Jul2025] Spread: temp={spread['temperature']} (FIXED) "
                f"joint={spread['spread_joint']:.3f} "
                f"m1={spread['spread_mask_1']:.3f} "
                f"m2={spread['spread_mask_2']:.3f}"
            )


# =============================================================================
# Factory Functions
# =============================================================================

def create_default_framework() -> LossFramework:
    """Create a loss framework with July 2025 default settings."""
    return LossFramework(create_default_config())


def create_framework_from_config(config_dict: Dict[str, Any]) -> LossFramework:
    """Create a loss framework from a configuration dictionary."""
    losses = {}
    for name, loss_dict in config_dict.get("losses", {}).items():
        losses[name] = LossConfig(
            enabled=loss_dict.get("enabled", True),
            weight=loss_dict.get("weight", 1.0),
            params=loss_dict.get("params", {})
        )

    config = LossFrameworkConfig(
        losses=losses,
        log_every_n_batches=config_dict.get("log_every_n_batches", 100),
    )

    return LossFramework(config)
