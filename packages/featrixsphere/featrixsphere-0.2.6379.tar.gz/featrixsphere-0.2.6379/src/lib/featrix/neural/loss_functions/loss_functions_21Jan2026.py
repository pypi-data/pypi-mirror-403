#!/usr/bin/env python3
"""
Loss Functions - 21 January 2026

Self-contained loss function set. Implements:
- ContrastiveLoss: Cosine → InfoNCE curriculum blend
- UniformityLoss: Wang & Isola 2020 log-sum-exp repulsion (applies to masked embeddings)
- ColumnPredictionLoss: Same-row cosine similarity for column prediction
- ReconstructionLoss: MSE for scalar reconstruction
- SeparationLoss: Pure repulsion (disabled by default)
- DiversityLoss: Encourage use of all dimensions (disabled by default)

Key changes from previous versions:
- UniformityLoss now applies to masked embeddings (embeddings_1, embeddings_2) not unmasked
  This ensures gradients flow back and the repulsive force actually trains the model.
- ContrastiveLoss blends cosine (learnable from scratch) with InfoNCE (discriminative)
- ColumnPredictionLoss uses same-row cosine by default (more learnable than InfoNCE)

Usage:
    from featrix.neural.loss_functions import loss_functions_21Jan2026 as losses
    framework = losses.create_default_framework()
    total_loss, metrics = framework.compute_total(embeddings_1, embeddings_2, embeddings_unmasked)
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any

import torch
import torch.nn as nn
import torch.nn.functional as F

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
        """
        Compute the loss value and metrics.

        Args:
            embeddings_1: (B, D) embeddings from mask view 1
            embeddings_2: (B, D) embeddings from mask view 2
            embeddings_unmasked: (B, D) embeddings from unmasked view
            **kwargs: Additional inputs (column encodings, labels, etc.)

        Returns:
            loss: Scalar tensor
            metrics: Dict of diagnostic values (for logging)
        """
        pass

    def __call__(self, *args, **kwargs) -> Tuple[torch.Tensor, Dict[str, float]]:
        self._call_count += 1
        return self.compute(*args, **kwargs)


# =============================================================================
# Contrastive Loss - Cosine → InfoNCE curriculum blend
# =============================================================================

class ContrastiveLoss(LossComponent):
    """
    Contrastive loss with curriculum blending from cosine to InfoNCE.

    - Cosine: Loss = 1 - cosine_sim(masked, unmasked) - learnable from scratch
    - InfoNCE: Cross-entropy over similarity matrix - stronger discrimination

    Curriculum (updated):
    - Always maintain at least 25% InfoNCE (pure cosine gives mushy gradients)
    - Epoch 0-2:          75% cosine + 25% InfoNCE (warmup with some discrimination)
    - Epoch 2-12:         Linear blend → 100% InfoNCE
    - Epoch 12+:          100% InfoNCE (full discrimination)
    """

    def __init__(self, config: LossConfig):
        super().__init__("contrastive", config)
        self.temperature = config.params.get("temperature", 0.1)
        # REDUCED warmup and transition for faster InfoNCE engagement
        self.warmup_epochs = config.params.get("warmup_epochs", 2)
        self.transition_epochs = config.params.get("transition_epochs", 10)
        # MINIMUM InfoNCE weight: always have some NCE for instance discrimination
        self.min_infonce_weight = config.params.get("min_infonce_weight", 0.25)
        self._infonce_weight = self.min_infonce_weight  # Start with minimum, not 0

    def set_epoch(self, epoch: int, total_epochs: int):
        """Update the cosine↔InfoNCE blend based on training progress.

        IMPORTANT: Always maintain at least min_infonce_weight (25%) InfoNCE.
        Pure cosine gives mushy gradients - need InfoNCE for sharp discrimination.
        """
        if epoch < self.warmup_epochs:
            self._infonce_weight = self.min_infonce_weight
        elif epoch >= self.warmup_epochs + self.transition_epochs:
            self._infonce_weight = 1.0
        else:
            progress = (epoch - self.warmup_epochs) / self.transition_epochs
            self._infonce_weight = self.min_infonce_weight + progress * (1.0 - self.min_infonce_weight)

    def compute(
        self,
        embeddings_1: torch.Tensor,
        embeddings_2: torch.Tensor,
        embeddings_unmasked: torch.Tensor,
        **kwargs
    ) -> Tuple[torch.Tensor, Dict[str, float]]:
        device = embeddings_1.device
        B = embeddings_1.shape[0]

        if B < 2:
            return torch.tensor(0.0, device=device), {"n_samples": B}

        # Normalize for cosine similarity
        emb1 = F.normalize(embeddings_1, dim=1, eps=1e-8)
        emb2 = F.normalize(embeddings_2, dim=1, eps=1e-8)
        emb_unmasked = F.normalize(embeddings_unmasked, dim=1, eps=1e-8)

        # COSINE LOSS: Same-row similarity
        cosine_sim_1 = (emb1 * emb_unmasked).sum(dim=1)
        cosine_sim_2 = (emb2 * emb_unmasked).sum(dim=1)
        cosine_loss = ((1.0 - cosine_sim_1).mean() + (1.0 - cosine_sim_2).mean()) / 2

        # INFONCE LOSS: Cross-entropy discrimination
        targets = torch.arange(B, device=device)
        sim_matrix_1 = emb1 @ emb_unmasked.T / self.temperature
        sim_matrix_2 = emb2 @ emb_unmasked.T / self.temperature
        infonce_loss = (F.cross_entropy(sim_matrix_1, targets) + F.cross_entropy(sim_matrix_2, targets)) / 2

        # BLEND
        w = self._infonce_weight
        loss = (1 - w) * cosine_loss + w * infonce_loss

        # METRICS
        with torch.no_grad():
            pos_sim = torch.diag(sim_matrix_1).mean().item() * self.temperature
            mask = ~torch.eye(B, dtype=torch.bool, device=device)
            neg_sim = sim_matrix_1[mask].mean().item() * self.temperature
            preds_1 = sim_matrix_1.argmax(dim=1)
            preds_2 = sim_matrix_2.argmax(dim=1)
            accuracy = ((preds_1 == targets).float().mean().item() + (preds_2 == targets).float().mean().item()) / 2

        metrics = {
            "loss": loss.item(),
            "cosine_loss": cosine_loss.item(),
            "infonce_loss": infonce_loss.item(),
            "infonce_weight": w,
            "pos_sim": pos_sim,
            "neg_sim": neg_sim,
            "separation": pos_sim - neg_sim,
            "accuracy": accuracy,
            "mode": f"blend({1-w:.0%}cos+{w:.0%}nce)",
        }

        return loss, metrics


# =============================================================================
# Uniformity Loss - Wang & Isola 2020 (applies to MASKED embeddings)
# =============================================================================

class UniformityLoss(LossComponent):
    """
    Log-sum-exp uniformity loss (Wang & Isola 2020).

    Encourages embeddings to be uniformly distributed on the unit sphere.

    CRITICAL: Applies to MASKED embeddings (embeddings_1, embeddings_2) which have gradients,
    NOT to embeddings_unmasked which is typically detached.
    """

    def __init__(self, config: LossConfig):
        super().__init__("uniformity", config)
        self.temperature = config.params.get("temperature", 2.0)

    def _compute_uniformity_for_embeddings(self, emb: torch.Tensor) -> Tuple[torch.Tensor, float, float]:
        device = emb.device
        B = emb.shape[0]

        emb_norm = F.normalize(emb, dim=1, eps=1e-8)
        sim_matrix = emb_norm @ emb_norm.T
        dist_sq = 2.0 - 2.0 * sim_matrix

        mask = ~torch.eye(B, dtype=torch.bool, device=device)
        dist_sq_offdiag = dist_sq[mask].view(B, B - 1)

        loss = torch.logsumexp(-self.temperature * dist_sq_offdiag, dim=1).mean()

        return loss, dist_sq_offdiag.mean().item(), dist_sq_offdiag.min().item()

    def compute(
        self,
        embeddings_1: torch.Tensor,
        embeddings_2: torch.Tensor,
        embeddings_unmasked: torch.Tensor,
        **kwargs
    ) -> Tuple[torch.Tensor, Dict[str, float]]:
        device = embeddings_1.device
        B = embeddings_1.shape[0]

        if B < 2:
            return torch.tensor(0.0, device=device), {"n_samples": B}

        # Apply to MASKED embeddings (which have gradients)
        loss_1, mean_dist_1, min_dist_1 = self._compute_uniformity_for_embeddings(embeddings_1)
        loss_2, mean_dist_2, min_dist_2 = self._compute_uniformity_for_embeddings(embeddings_2)

        loss = (loss_1 + loss_2) / 2

        metrics = {
            "loss": loss.item(),
            "mean_dist_sq": (mean_dist_1 + mean_dist_2) / 2,
            "min_dist_sq": min(min_dist_1, min_dist_2),
        }

        return loss, metrics


# =============================================================================
# Column Prediction Loss - Same-row cosine similarity
# =============================================================================

class ColumnPredictionLoss(LossComponent):
    """
    Predict masked columns from visible columns using same-row cosine similarity.

    Uses SAME-ROW cosine similarity (not InfoNCE across batch):
    - Loss = 1 - cosine_similarity (minimizes to 0 when perfectly aligned)
    """

    def __init__(self, config: LossConfig):
        super().__init__("column_prediction", config)
        self.temperature = config.params.get("temperature", 0.1)
        self.use_infonce = config.params.get("use_infonce", False)

    def compute(
        self,
        embeddings_1: torch.Tensor,
        embeddings_2: torch.Tensor,
        embeddings_unmasked: torch.Tensor,
        column_predictions: Optional[torch.Tensor] = None,
        column_targets: Optional[torch.Tensor] = None,
        **kwargs
    ) -> Tuple[torch.Tensor, Dict[str, float]]:
        device = embeddings_unmasked.device

        if column_predictions is None or column_targets is None:
            return torch.tensor(0.0, device=device), {"skipped": True}

        B, n_cols, D = column_predictions.shape

        if self.use_infonce:
            total_loss = 0.0
            n_computed = 0
            for col_idx in range(n_cols):
                pred = F.normalize(column_predictions[:, col_idx], dim=1, eps=1e-8)
                target = F.normalize(column_targets[:, col_idx], dim=1, eps=1e-8)
                sim_matrix = pred @ target.T / self.temperature
                targets = torch.arange(B, device=device)
                col_loss = F.cross_entropy(sim_matrix, targets)
                total_loss += col_loss
                n_computed += 1
            if n_computed > 0:
                total_loss = total_loss / n_computed
            metrics = {"loss": total_loss.item() if isinstance(total_loss, torch.Tensor) else total_loss, "mode": "infonce"}
        else:
            pred_norm = F.normalize(column_predictions, dim=-1, eps=1e-8)
            target_norm = F.normalize(column_targets, dim=-1, eps=1e-8)
            cosine_sim = (pred_norm * target_norm).sum(dim=-1)
            total_loss = (1.0 - cosine_sim).mean()
            metrics = {
                "loss": total_loss.item(),
                "mode": "cosine",
                "mean_cosine_sim": cosine_sim.mean().item(),
            }

        return total_loss, metrics


# =============================================================================
# Reconstruction Loss (for scalars)
# =============================================================================

class ReconstructionLoss(LossComponent):
    """MSE reconstruction loss for scalar columns."""

    def __init__(self, config: LossConfig):
        super().__init__("reconstruction", config)

    def compute(
        self,
        embeddings_1: torch.Tensor,
        embeddings_2: torch.Tensor,
        embeddings_unmasked: torch.Tensor,
        decoded_values: Optional[torch.Tensor] = None,
        target_values: Optional[torch.Tensor] = None,
        **kwargs
    ) -> Tuple[torch.Tensor, Dict[str, float]]:
        device = embeddings_unmasked.device

        if decoded_values is None or target_values is None:
            return torch.tensor(0.0, device=device), {"skipped": True}

        loss = F.mse_loss(decoded_values, target_values)
        metrics = {"loss": loss.item(), "mae": (decoded_values - target_values).abs().mean().item()}

        return loss, metrics


# =============================================================================
# Separation Loss - Pure repulsion (disabled by default)
# =============================================================================

class SeparationLoss(LossComponent):
    """Penalizes high pairwise similarity between different rows."""

    def __init__(self, config: LossConfig):
        super().__init__("separation", config)
        self.target_sim = config.params.get("target_sim", 0.0)

    def compute(
        self,
        embeddings_1: torch.Tensor,
        embeddings_2: torch.Tensor,
        embeddings_unmasked: torch.Tensor,
        **kwargs
    ) -> Tuple[torch.Tensor, Dict[str, float]]:
        device = embeddings_unmasked.device
        B = embeddings_unmasked.shape[0]

        if B < 2:
            return torch.tensor(0.0, device=device), {"n_samples": B}

        emb = F.normalize(embeddings_unmasked, dim=1, eps=1e-8)
        sim_matrix = emb @ emb.T
        mask = ~torch.eye(B, dtype=torch.bool, device=device)
        off_diag = sim_matrix[mask]
        mean_sim = off_diag.mean()
        loss = (mean_sim - self.target_sim) ** 2

        metrics = {"loss": loss.item(), "mean_sim": mean_sim.item()}

        return loss, metrics


# =============================================================================
# Diversity Loss - Use all dimensions (disabled by default)
# =============================================================================

class DiversityLoss(LossComponent):
    """Encourages embeddings to use all dimensions."""

    def __init__(self, config: LossConfig):
        super().__init__("diversity", config)
        self.target_std_multiplier = config.params.get("target_std_multiplier", 1.0)

    def compute(
        self,
        embeddings_1: torch.Tensor,
        embeddings_2: torch.Tensor,
        embeddings_unmasked: torch.Tensor,
        **kwargs
    ) -> Tuple[torch.Tensor, Dict[str, float]]:
        device = embeddings_unmasked.device
        B, D = embeddings_unmasked.shape

        if B < 2:
            return torch.tensor(0.0, device=device), {"n_samples": B}

        emb = F.normalize(embeddings_unmasked, dim=1, eps=1e-8)
        std_per_dim = emb.std(dim=0)
        target_std = self.target_std_multiplier / (D ** 0.5)
        deficit = torch.clamp(target_std - std_per_dim, min=0.0)
        loss = (deficit ** 2).mean()

        metrics = {"loss": loss.item(), "mean_std": std_per_dim.mean().item()}

        return loss, metrics


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
        """Default config: contrastive + uniformity + column_prediction."""
        return cls(
            losses={
                "contrastive": LossConfig(enabled=True, weight=1.0, params={"temperature": 0.1}),
                "column_prediction": LossConfig(enabled=True, weight=0.1, params={"temperature": 0.1}),
                "reconstruction": LossConfig(enabled=True, weight=0.05),
                "separation": LossConfig(enabled=False, weight=1.0),
                "uniformity": LossConfig(enabled=True, weight=0.3, params={"temperature": 2.0}),
                "diversity": LossConfig(enabled=False, weight=1.0),
            }
        )


class LossFramework:
    """Orchestrates all loss components."""

    LOSS_TYPES = {
        "contrastive": ContrastiveLoss,
        "separation": SeparationLoss,
        "uniformity": UniformityLoss,
        "diversity": DiversityLoss,
        "column_prediction": ColumnPredictionLoss,
        "reconstruction": ReconstructionLoss,
    }

    def __init__(self, config: FrameworkConfig):
        self.config = config
        self.components: Dict[str, LossComponent] = {}
        self._batch_count = 0

        for name, loss_config in config.losses.items():
            if name in self.LOSS_TYPES:
                self.components[name] = self.LOSS_TYPES[name](loss_config)

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

        # Log contrastive diagnostics if present
        # CONTRASTIVE (masked→unmasked): Row-level contrastive loss
        # - Embeddings: masked view (emb1/emb2) vs unmasked view (emb_unmasked)
        # - Positives: same row (masked and unmasked are different views of the same row)
        # - Negatives: all other rows in the batch (cross-row comparisons)
        contrastive = metrics["components"].get("contrastive", {})
        if contrastive and "pos_sim" in contrastive:
            mode = contrastive.get("mode", "unknown")
            logger.info(
                f"  📊 Contrastive (masked→unmasked) [{mode}]: pos_sim={contrastive['pos_sim']:.3f} "
                f"neg_sim={contrastive['neg_sim']:.3f} "
                f"separation={contrastive['separation']:.3f} "
                f"loss={contrastive['loss']:.3f}"
            )

        # Log column prediction diagnostics if present
        col_pred = metrics["components"].get("column_prediction", {})
        if col_pred and "mean_cosine_sim" in col_pred:
            logger.info(
                f"  📊 ColPred [{col_pred.get('mode', 'unknown')}]: "
                f"mean_cosine={col_pred['mean_cosine_sim']:.3f} "
                f"loss={col_pred['loss']:.3f}"
            )

    def set_epoch(self, epoch: int, total_epochs: int):
        for name, comp in self.components.items():
            if hasattr(comp, 'set_epoch'):
                comp.set_epoch(epoch, total_epochs)

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
    """Create a framework with sensible defaults."""
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
