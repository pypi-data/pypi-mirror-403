#!/usr/bin/env python3
"""
Loss Functions - 01 January 2026 (from commit ab876d8e)

Self-contained loss function set from the Jan 1st codebase.

Key characteristics:
- Pure InfoNCE for all losses (no cosine warmup, no curriculum blend)
- Adaptive temperature based on batch size and column count
- Joint InfoNCE loss: masked encoding vs unmasked encoding
- Marginal InfoNCE loss: predict masked columns from visible columns
- Spread loss: self-similarity penalty to prevent collapse
- Entropy regularization for adaptive encoders

This was BEFORE:
- Cosine → InfoNCE curriculum blend
- UniformityLoss (Wang & Isola 2020)
- Same-row cosine for column prediction

Usage:
    from featrix.neural.loss_functions import loss_functions_01Jan2026 as losses
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
# Adaptive Temperature Computation (from ab876d8e)
# =============================================================================

def compute_adaptive_temperature(batch_size: int, n_columns: int, temp_override: Optional[float] = None) -> float:
    """
    Compute adaptive temperature for InfoNCE loss.

    Temperature controls sharpness of contrastive learning:
    - Lower temp (e.g., 0.01) = sharper, more aggressive separation
    - Higher temp (e.g., 0.2) = softer, more forgiving

    Args:
        batch_size: Current batch size
        n_columns: Number of columns in the dataset
        temp_override: If provided, use this temperature instead

    Returns:
        Temperature value (float)
    """
    if temp_override is not None:
        return temp_override

    # Base temperature: reasonable default for most datasets
    base_temp = 0.1

    # Batch size factor: larger batches can handle sharper temp
    # Normalize to batch_size=256 (more common for real training)
    batch_factor = max(0.7, min(1.5, batch_size / 256.0))

    # Column factor: more columns = more discriminative embeddings
    # log(10) ≈ 1.0, log(100) ≈ 2.0, log(200) ≈ 2.3
    column_factor = 1.0 + (math.log10(max(10, n_columns)) - 1.0) * 0.15
    column_factor = max(0.8, min(1.5, column_factor))

    # Compute adaptive temp
    temp = base_temp / (batch_factor * column_factor)

    # Clamp to reasonable range
    temp = max(0.05, min(0.3, temp))

    return temp


# =============================================================================
# Joint InfoNCE Loss - Masked vs Unmasked embeddings
# =============================================================================

class JointInfoNCELoss(LossComponent):
    """
    InfoNCE loss between masked and unmasked joint embeddings.

    This is the original joint contrastive loss from Jan 2026:
    - Uses cross-entropy over similarity matrix
    - Adaptive temperature based on batch size and columns
    - No cosine warmup - pure InfoNCE from the start
    """

    def __init__(self, config: LossConfig):
        super().__init__("joint_infonce", config)
        self.n_columns = config.params.get("n_columns", 20)
        self.latent_noise = config.params.get("latent_noise", 0.0)

    def compute(
        self,
        embeddings_1: torch.Tensor,
        embeddings_2: torch.Tensor,
        embeddings_unmasked: torch.Tensor,
        **kwargs
    ) -> Tuple[torch.Tensor, Dict[str, float]]:
        """
        Compute InfoNCE loss: masked embeddings should match their unmasked version.
        """
        device = embeddings_1.device
        B = embeddings_1.shape[0]

        if B < 2:
            return torch.tensor(0.0, device=device), {"n_samples": B}

        # Compute adaptive temperature
        temp = compute_adaptive_temperature(B, self.n_columns)

        # Add latent noise and normalize (as in original)
        if self.latent_noise > 0:
            embeddings_unmasked = embeddings_unmasked + torch.randn_like(embeddings_unmasked) * self.latent_noise
        emb_unmasked = F.normalize(embeddings_unmasked, dim=1, eps=1e-8)

        # Compute InfoNCE for both masked views
        targets = torch.arange(B, device=device)

        # View 1
        emb1 = F.normalize(embeddings_1, dim=1, eps=1e-8)
        logits_1 = emb1 @ emb_unmasked.T / temp
        loss_1 = F.cross_entropy(logits_1, targets)

        # View 2
        emb2 = F.normalize(embeddings_2, dim=1, eps=1e-8)
        logits_2 = emb2 @ emb_unmasked.T / temp
        loss_2 = F.cross_entropy(logits_2, targets)

        loss = (loss_1 + loss_2) / 2

        # Metrics
        with torch.no_grad():
            pos_sim = torch.diag(logits_1).mean().item() * temp
            mask = ~torch.eye(B, dtype=torch.bool, device=device)
            neg_sim = logits_1[mask].mean().item() * temp
            preds = logits_1.argmax(dim=1)
            accuracy = (preds == targets).float().mean().item()

        metrics = {
            "loss": loss.item(),
            "loss_1": loss_1.item(),
            "loss_2": loss_2.item(),
            "temperature": temp,
            "pos_sim": pos_sim,
            "neg_sim": neg_sim,
            "separation": pos_sim - neg_sim,
            "accuracy": accuracy,
        }

        return loss, metrics


# =============================================================================
# Marginal InfoNCE Loss - Column prediction
# =============================================================================

class MarginalInfoNCELoss(LossComponent):
    """
    InfoNCE loss for predicting masked columns from visible columns.

    This is the core column prediction task:
    - For each masked column, predict its embedding from context
    - Uses InfoNCE across the batch (not same-row cosine)
    - Adaptive temperature

    CRITICAL: Only computes loss on MASKED columns (where column_mask == MARGINAL).
    This is essential because:
    - Unmasked columns are trivial to predict (encoder saw the actual value)
    - Masked columns require real prediction from context
    - Averaging all columns would dilute the learning signal

    Note: This requires column_predictions and column_targets tensors.
    """

    def __init__(self, config: LossConfig):
        super().__init__("marginal_infonce", config)
        self.n_columns = config.params.get("n_columns", 20)

    def compute(
        self,
        embeddings_1: torch.Tensor,
        embeddings_2: torch.Tensor,
        embeddings_unmasked: torch.Tensor,
        column_predictions: Optional[torch.Tensor] = None,
        column_targets: Optional[torch.Tensor] = None,
        **kwargs
    ) -> Tuple[torch.Tensor, Dict[str, float]]:
        """
        Compute marginal InfoNCE loss for column prediction.

        Args:
            column_predictions: (B, n_cols, D) predicted column embeddings
            column_targets: (B, n_cols, D) target column embeddings
            column_mask: (B, n_cols) TokenStatus mask - only compute loss where mask == MARGINAL
        """
        device = embeddings_unmasked.device
        column_mask = kwargs.get('column_mask')  # (B, n_cols) TokenStatus values

        if column_predictions is None or column_targets is None:
            return torch.tensor(0.0, device=device), {"skipped": True}

        B, n_cols, D = column_predictions.shape

        # Determine which columns are masked (need prediction)
        if column_mask is not None:
            # Only compute loss on masked columns
            marginal_mask = (column_mask == TokenStatus.MARGINAL)  # (B, n_cols)
        else:
            # No mask provided - use all columns (fallback behavior)
            marginal_mask = torch.ones(B, n_cols, dtype=torch.bool, device=device)

        # Compute adaptive temperature
        temp = compute_adaptive_temperature(B, n_cols)

        # Compute InfoNCE for each column
        # IMPORTANT: Use list + sum() to preserve gradient flow
        # DO NOT use torch.tensor(0.0) + add which breaks the computation graph
        col_losses_tensor = []
        col_losses_values = []
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

            # Normalize for InfoNCE
            pred_norm = F.normalize(pred_masked, dim=1, eps=1e-8)
            target_norm = F.normalize(target_masked, dim=1, eps=1e-8)

            # InfoNCE: which row does this prediction belong to?
            targets_idx = torch.arange(pred_masked.shape[0], device=device)
            logits = pred_norm @ target_norm.T / temp
            col_loss = F.cross_entropy(logits, targets_idx)

            col_losses_tensor.append(col_loss)
            col_losses_values.append(col_loss.item())

        if col_losses_tensor:
            total_loss = sum(col_losses_tensor) / len(col_losses_tensor)
        else:
            total_loss = torch.tensor(0.0, device=device, requires_grad=False)

        metrics = {
            "loss": total_loss.item(),
            "n_columns_total": n_cols,
            "n_columns_masked": n_masked_cols,
            "n_columns_computed": len(col_losses_tensor),
            "temperature": temp,
            "mean_col_loss": sum(col_losses_values) / len(col_losses_values) if col_losses_values else 0.0,
            "mode": "infonce_masked_only",
        }

        return total_loss, metrics


# =============================================================================
# Spread Loss - Self-similarity penalty
# =============================================================================

class SpreadLoss(LossComponent):
    """
    Spread loss to prevent embedding collapse.

    Penalizes self-similarity within each batch:
    - Each embedding should be most similar to itself
    - Cross-entropy over self-similarity matrix

    This is different from UniformityLoss:
    - SpreadLoss uses CE over self-similarity
    - UniformityLoss uses log-sum-exp of distances
    """

    def __init__(self, config: LossConfig):
        super().__init__("spread", config)
        self.n_columns = config.params.get("n_columns", 20)
        self.joint_weight = config.params.get("joint_weight", 1.0)
        self.marginal_weight = config.params.get("marginal_weight", 1.0)

    def compute(
        self,
        embeddings_1: torch.Tensor,
        embeddings_2: torch.Tensor,
        embeddings_unmasked: torch.Tensor,
        **kwargs
    ) -> Tuple[torch.Tensor, Dict[str, float]]:
        """
        Compute spread loss to prevent collapse.
        """
        device = embeddings_unmasked.device
        B = embeddings_unmasked.shape[0]

        if B < 2:
            return torch.tensor(0.0, device=device), {"n_samples": B}

        # Compute adaptive temperature
        # Use different base temp for spread (0.2 vs 0.1 for joint)
        base_temp = 0.2
        batch_factor = max(0.5, min(2.0, B / 128.0))
        column_factor = max(0.5, min(1.5, self.n_columns / 20.0))
        temp = base_temp / (batch_factor * column_factor)
        temp = max(0.01, min(0.4, temp))

        targets = torch.arange(B, device=device)

        # Unmasked self-similarity
        emb_unmasked = F.normalize(embeddings_unmasked, dim=1, eps=1e-8)
        logits_joint = emb_unmasked @ emb_unmasked.T / temp
        spread_loss_joint = F.cross_entropy(logits_joint, targets)

        # View 1 self-similarity
        emb1 = F.normalize(embeddings_1, dim=1, eps=1e-8)
        logits_1 = emb1 @ emb1.T / temp
        spread_loss_1 = F.cross_entropy(logits_1, targets)

        # View 2 self-similarity
        emb2 = F.normalize(embeddings_2, dim=1, eps=1e-8)
        logits_2 = emb2 @ emb2.T / temp
        spread_loss_2 = F.cross_entropy(logits_2, targets)

        total = (
            self.joint_weight * spread_loss_joint
            + self.marginal_weight * spread_loss_1
            + self.marginal_weight * spread_loss_2
        )

        metrics = {
            "loss": total.item(),
            "joint": spread_loss_joint.item(),
            "mask_1": spread_loss_1.item(),
            "mask_2": spread_loss_2.item(),
            "temperature": temp,
        }

        return total, metrics


# =============================================================================
# Framework Config and LossFramework
# =============================================================================

@dataclass
class FrameworkConfig:
    """Configuration for the entire loss framework."""
    losses: Dict[str, LossConfig] = field(default_factory=dict)
    log_every_n_batches: int = 1

    @classmethod
    def default(cls) -> "FrameworkConfig":
        """
        Default config from Jan 2026: joint + marginal InfoNCE + spread.

        No uniformity loss, no cosine warmup.
        """
        return cls(
            losses={
                "joint_infonce": LossConfig(enabled=True, weight=1.0, params={"n_columns": 20}),
                "marginal_infonce": LossConfig(enabled=True, weight=1.0, params={"n_columns": 20}),
                "spread": LossConfig(enabled=True, weight=1.0, params={
                    "n_columns": 20,
                    "joint_weight": 1.0,
                    "marginal_weight": 1.0,
                }),
            }
        )


class LossFramework:
    """Orchestrates all loss components."""

    LOSS_TYPES = {
        "joint_infonce": JointInfoNCELoss,
        "marginal_infonce": MarginalInfoNCELoss,
        "spread": SpreadLoss,
    }

    def __init__(self, config: FrameworkConfig):
        self.config = config
        self.components: Dict[str, LossComponent] = {}
        self._batch_count = 0

        for name, loss_config in config.losses.items():
            if name in self.LOSS_TYPES:
                self.components[name] = self.LOSS_TYPES[name](loss_config)

        self._log_config()

    def _log_config(self):
        logger.info("=" * 60)
        logger.info("LOSS FRAMEWORK CONFIGURATION (01 Jan 2026)")
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
                    "loss": loss.item() if isinstance(loss, torch.Tensor) else loss,
                    "weighted_loss": weighted_loss.item() if isinstance(weighted_loss, torch.Tensor) else weighted_loss,
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
        # Each component can include arbitrary metrics - consumers walk dynamically

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

        # Log InfoNCE diagnostics if present
        joint = metrics["components"].get("joint_infonce", {})
        if joint and "accuracy" in joint:
            logger.info(
                f"  📊 Joint InfoNCE: acc={joint['accuracy']:.1%} "
                f"pos_sim={joint['pos_sim']:.3f} "
                f"neg_sim={joint['neg_sim']:.3f} "
                f"temp={joint['temperature']:.4f}"
            )

    def set_epoch(self, epoch: int, total_epochs: int):
        """No curriculum in this version - placeholder for interface compatibility."""
        pass

    def enable(self, name: str):
        if name in self.components:
            self.components[name].config.enabled = True

    def disable(self, name: str):
        if name in self.components:
            self.components[name].config.enabled = False

    def set_weight(self, name: str, weight: float):
        if name in self.components:
            self.components[name].config.weight = weight


# =============================================================================
# Convenience functions
# =============================================================================

def create_default_framework() -> LossFramework:
    """Create a framework with Jan 2026 defaults."""
    return LossFramework(FrameworkConfig.default())


def create_framework_from_dict(config_dict: Dict[str, Any]) -> LossFramework:
    """Create a framework from a dictionary config."""
    losses = {}
    for name, params in config_dict.items():
        if isinstance(params, dict):
            params = params.copy()
            enabled = params.pop("enabled", True)
            weight = params.pop("weight", 1.0)
            losses[name] = LossConfig(enabled=enabled, weight=weight, params=params)

    return LossFramework(FrameworkConfig(losses=losses))
