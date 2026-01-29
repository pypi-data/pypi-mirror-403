#!/usr/bin/env python3
"""
Loss Framework - Modular, configurable loss system for tabular embeddings.

Goals:
1. Each loss is a self-contained module with standard interface
2. Config controls which losses are active and their weights
3. Easy to add new losses, run experiments, compare results
4. Clear logging of what's on/off and contribution of each loss

Usage:
    framework = LossFramework.from_config(config)
    total_loss, metrics = framework.compute_total(
        embeddings_1=masked_view_1,
        embeddings_2=masked_view_2,
        embeddings_unmasked=full_view,
        ...
    )
"""

import logging
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
# Contrastive Loss - The main attractive + repulsive force
# =============================================================================

class ContrastiveLoss(LossComponent):
    """
    Contrastive loss for masked embeddings with curriculum blending.

    Blends COSINE loss (learnable warmup) with INFONCE (discriminative):
    - Cosine: Loss = 1 - cosine_sim(masked, unmasked) - learnable from scratch
    - InfoNCE: Cross-entropy over similarity matrix - stronger discrimination

    Curriculum:
    - Epoch 0:     100% cosine, 0% InfoNCE (warmup)
    - Epoch N/2:   50% cosine, 50% InfoNCE (transition)
    - Epoch N:     0% cosine, 100% InfoNCE (discrimination)

    The blend is controlled by `infonce_weight` which goes from 0→1 over training.

    CRITICAL COMPONENTS (from legacy that were MISSING):
    1. Latent noise: Add small noise to targets before normalizing - prevents collapse
    2. Anti-collapse regularization: norm_penalty + diversity_penalty on predictions
    """

    def __init__(self, config: LossConfig):
        super().__init__("contrastive", config)
        self.base_temperature = config.params.get("temperature", 0.1)
        self.adaptive_temperature = config.params.get("adaptive_temperature", True)  # Use adaptive by default
        # Curriculum: warmup_epochs before starting InfoNCE blend
        # REDUCED from 5 to 2: need InfoNCE earlier for instance discrimination
        self.warmup_epochs = config.params.get("warmup_epochs", 2)
        # Curriculum: transition_epochs to blend from cosine to InfoNCE
        # REDUCED from 20 to 10: faster transition to InfoNCE
        self.transition_epochs = config.params.get("transition_epochs", 10)
        # MINIMUM InfoNCE weight: always have some NCE even during warmup
        # Pure cosine gives mushy gradients - need some InfoNCE for sharp discrimination
        self.min_infonce_weight = config.params.get("min_infonce_weight", 0.25)
        # Current infonce weight (0=pure cosine, 1=pure infonce)
        self._infonce_weight = self.min_infonce_weight  # Start with minimum, not 0
        # For adaptive temperature
        self._n_columns = config.params.get("n_columns", 20)  # Will be updated from kwargs
        self._temp_log_count = 0

        # Latent noise - from legacy infoNCE_loss (line 2325 in encoders.py)
        # Note: Legacy actually has latent_noise=0, so DISABLED by default
        # Keeping this as an option but not enabled
        self.latent_noise = config.params.get("latent_noise", 0.0)

        # CRITICAL: Anti-collapse regularization weights (from legacy compute_joint_infoNCE_loss)
        self.norm_penalty_weight = config.params.get("norm_penalty_weight", 0.1)
        self.diversity_penalty_weight = config.params.get("diversity_penalty_weight", 0.1)

    def _compute_adaptive_temp(self, batch_size: int) -> float:
        """
        Compute adaptive temperature based on batch size and columns.
        Matches the logic from encoders.py _compute_adaptive_temperature.
        """
        if not self.adaptive_temperature:
            return self.base_temperature

        import math

        # Base temperature: reasonable default
        base_temp = 0.1

        # Batch size factor: larger batches → more negatives → can use lower temp (sharper)
        batch_factor = max(0.7, min(1.5, batch_size / 256.0))

        # Column factor: more columns = more discriminative embeddings
        column_factor = 1.0 + (math.log10(max(10, self._n_columns)) - 1.0) * 0.15
        column_factor = max(0.8, min(1.5, column_factor))

        # Compute adaptive temp
        temp = base_temp / (batch_factor * column_factor)

        # Clamp to reasonable range
        temp = max(0.05, min(0.3, temp))

        # Log occasionally
        if self._temp_log_count < 5:
            logger.info(f"🌡️  ContrastiveLoss adaptive temp: {temp:.4f} (B={batch_size}, cols={self._n_columns})")
            self._temp_log_count += 1

        return temp

    def set_epoch(self, epoch: int, total_epochs: int):
        """Update the cosine↔InfoNCE blend based on training progress.

        IMPORTANT: Always maintain at least min_infonce_weight (default 25%) InfoNCE.
        Pure cosine contrastive gives mushy gradients compared to InfoNCE/NT-Xent.
        Even during warmup, we need some InfoNCE for instance discrimination.
        """
        if epoch < self.warmup_epochs:
            # Warmup: use minimum InfoNCE weight (not pure cosine!)
            self._infonce_weight = self.min_infonce_weight
        elif epoch >= self.warmup_epochs + self.transition_epochs:
            # After transition: pure InfoNCE
            self._infonce_weight = 1.0
        else:
            # Linear blend during transition: min_weight → 1.0
            progress = (epoch - self.warmup_epochs) / self.transition_epochs
            # Interpolate from min_infonce_weight to 1.0
            self._infonce_weight = self.min_infonce_weight + progress * (1.0 - self.min_infonce_weight)

    def compute(
        self,
        embeddings_1: torch.Tensor,
        embeddings_2: torch.Tensor,
        embeddings_unmasked: torch.Tensor,
        **kwargs
    ) -> Tuple[torch.Tensor, Dict[str, float]]:
        """
        Blended contrastive loss: cosine warmup → InfoNCE discrimination.

        CRITICAL FIX: Includes latent noise and anti-collapse regularization
        from legacy infoNCE_loss and compute_joint_infoNCE_loss.
        """
        device = embeddings_1.device
        B = embeddings_1.shape[0]

        if B < 2:
            return torch.tensor(0.0, device=device), {"n_samples": B}

        # Update n_columns from column_targets if provided (for adaptive temperature)
        column_targets = kwargs.get("column_targets")
        if column_targets is not None and len(column_targets.shape) >= 2:
            self._n_columns = column_targets.shape[1]

        # Compute adaptive temperature based on batch size
        temperature = self._compute_adaptive_temp(B)

        # =================================================================
        # CRITICAL FIX #1: Add latent noise to targets (from legacy line 2325)
        # This prevents collapse by making targets slightly noisy
        # Always add noise during training (we're a loss function, always in training)
        # =================================================================
        emb_unmasked_noisy = embeddings_unmasked
        if self.latent_noise > 0:
            emb_unmasked_noisy = embeddings_unmasked + torch.randn_like(embeddings_unmasked) * self.latent_noise

        # Normalize for cosine similarity (AFTER adding noise to targets)
        emb1 = F.normalize(embeddings_1, dim=1, eps=1e-8)
        emb2 = F.normalize(embeddings_2, dim=1, eps=1e-8)
        emb_unmasked = F.normalize(emb_unmasked_noisy, dim=1, eps=1e-8)

        # =====================================================================
        # COSINE LOSS: Same-row similarity (learnable from scratch)
        # =====================================================================
        cosine_sim_1 = (emb1 * emb_unmasked).sum(dim=1)  # (B,)
        cosine_sim_2 = (emb2 * emb_unmasked).sum(dim=1)  # (B,)
        cosine_loss_1 = (1.0 - cosine_sim_1).mean()
        cosine_loss_2 = (1.0 - cosine_sim_2).mean()
        cosine_loss = (cosine_loss_1 + cosine_loss_2) / 2

        # =====================================================================
        # INFONCE LOSS: Cross-entropy discrimination
        # =====================================================================
        targets = torch.arange(B, device=device)
        sim_matrix_1 = emb1 @ emb_unmasked.T / temperature
        infonce_loss_1 = F.cross_entropy(sim_matrix_1, targets)
        sim_matrix_2 = emb2 @ emb_unmasked.T / temperature
        infonce_loss_2 = F.cross_entropy(sim_matrix_2, targets)
        infonce_loss = (infonce_loss_1 + infonce_loss_2) / 2

        # =====================================================================
        # BLEND: Curriculum from cosine → InfoNCE
        # =====================================================================
        w = self._infonce_weight
        base_loss = (1 - w) * cosine_loss + w * infonce_loss

        # =================================================================
        # CRITICAL FIX #2: Anti-collapse regularization (from legacy lines 3513-3529)
        # 1. Norm penalty: keep embedding norms close to 1.0
        # 2. Diversity penalty: prevent all embeddings from collapsing to same direction
        # =================================================================

        # Norm penalty: embeddings should have norm close to 1.0 (before normalization)
        emb1_norms = embeddings_1.norm(dim=1)
        emb2_norms = embeddings_2.norm(dim=1)
        norm_penalty = ((emb1_norms - 1.0) ** 2).mean() + ((emb2_norms - 1.0) ** 2).mean()

        # Diversity penalty: penalize high self-similarity across batch (collapsed predictions)
        # Use the already-normalized embeddings
        self_sim_1 = emb1 @ emb1.T
        self_sim_2 = emb2 @ emb2.T
        off_diag_mask = ~torch.eye(B, dtype=torch.bool, device=device)
        pred_self_sim_1 = self_sim_1[off_diag_mask].mean()
        pred_self_sim_2 = self_sim_2[off_diag_mask].mean()
        diversity_penalty = (pred_self_sim_1 ** 2 + pred_self_sim_2 ** 2) / 2

        # Combine: base_loss + weighted penalties
        loss = base_loss + self.norm_penalty_weight * norm_penalty + self.diversity_penalty_weight * diversity_penalty

        # =====================================================================
        # METRICS
        # =====================================================================
        with torch.no_grad():
            # Cosine metrics
            mean_cosine_1 = cosine_sim_1.mean().item()
            mean_cosine_2 = cosine_sim_2.mean().item()

            # InfoNCE metrics (multiply back by temperature to get actual similarity)
            pos_sim = torch.diag(sim_matrix_1).mean().item() * temperature
            mask = ~torch.eye(B, dtype=torch.bool, device=device)
            neg_sim = sim_matrix_1[mask].mean().item() * temperature

            # InfoNCE accuracy
            preds_1 = sim_matrix_1.argmax(dim=1)
            preds_2 = sim_matrix_2.argmax(dim=1)
            accuracy_1 = (preds_1 == targets).float().mean().item()
            accuracy_2 = (preds_2 == targets).float().mean().item()
            accuracy = (accuracy_1 + accuracy_2) / 2

        metrics = {
            "loss": loss.item(),
            "base_loss": base_loss.item(),
            "cosine_loss": cosine_loss.item(),
            "infonce_loss": infonce_loss.item(),
            "infonce_weight": w,
            "pos_sim": pos_sim,
            "neg_sim": neg_sim,
            "separation": pos_sim - neg_sim,
            "accuracy": accuracy,
            "batch_size": B,  # For computing ×random multiplier
            "mean_cosine_1": mean_cosine_1,
            "mean_cosine_2": mean_cosine_2,
            "temperature": temperature,  # Log actual temperature used
            "mode": f"blend({1-w:.0%}cos+{w:.0%}nce)",
            # Anti-collapse metrics
            "norm_penalty": norm_penalty.item(),
            "diversity_penalty": diversity_penalty.item(),
            "mean_norm_1": emb1_norms.mean().item(),
            "mean_norm_2": emb2_norms.mean().item(),
            "self_sim_1": pred_self_sim_1.item(),
            "self_sim_2": pred_self_sim_2.item(),
            "latent_noise": self.latent_noise,
        }

        return loss, metrics


# =============================================================================
# Separation Loss - Pure repulsive force
# =============================================================================

class SeparationLoss(LossComponent):
    """
    Penalizes high pairwise similarity between different rows.

    This is PURE REPULSION - no attractive component.
    Use sparingly, as contrastive loss already has repulsion built in.
    """

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
        """Penalize mean off-diagonal similarity."""
        device = embeddings_unmasked.device
        B = embeddings_unmasked.shape[0]

        if B < 2:
            return torch.tensor(0.0, device=device), {"n_samples": B}

        # Normalize
        emb = F.normalize(embeddings_unmasked, dim=1, eps=1e-8)

        # Pairwise cosine similarity
        sim_matrix = emb @ emb.T

        # Off-diagonal mean
        mask = ~torch.eye(B, dtype=torch.bool, device=device)
        off_diag = sim_matrix[mask]
        mean_sim = off_diag.mean()

        # Loss: penalize deviation from target (usually 0)
        loss = (mean_sim - self.target_sim) ** 2

        metrics = {
            "loss": loss.item(),
            "mean_sim": mean_sim.item(),
            "max_sim": off_diag.max().item(),
            "min_sim": off_diag.min().item(),
        }

        return loss, metrics


# =============================================================================
# Uniformity Loss - Spread embeddings on sphere
# =============================================================================

class UniformityLoss(LossComponent):
    """
    Log-sum-exp uniformity loss (Wang & Isola 2020).

    Encourages embeddings to be uniformly distributed on the unit sphere.
    This is a softer repulsion than SeparationLoss.

    CRITICAL: Applies to MASKED embeddings (embeddings_1, embeddings_2) which have gradients,
    NOT to embeddings_unmasked which is typically detached. This ensures the repulsive force
    actually pushes the training embeddings apart.
    """

    def __init__(self, config: LossConfig):
        super().__init__("uniformity", config)
        self.temperature = config.params.get("temperature", 2.0)

    def _compute_uniformity_for_embeddings(self, emb: torch.Tensor) -> Tuple[torch.Tensor, float, float]:
        """Compute uniformity loss for a single set of embeddings."""
        device = emb.device
        B = emb.shape[0]

        # Normalize
        emb_norm = F.normalize(emb, dim=1, eps=1e-8)

        # Pairwise squared distances (for unit vectors: 2 - 2*cos_sim)
        sim_matrix = emb_norm @ emb_norm.T
        dist_sq = 2.0 - 2.0 * sim_matrix

        # Mask diagonal
        mask = ~torch.eye(B, dtype=torch.bool, device=device)
        dist_sq_offdiag = dist_sq[mask].view(B, B - 1)

        # Log-sum-exp of negative distances (penalizes close pairs)
        loss = torch.logsumexp(-self.temperature * dist_sq_offdiag, dim=1).mean()

        return loss, dist_sq_offdiag.mean().item(), dist_sq_offdiag.min().item()

    def compute(
        self,
        embeddings_1: torch.Tensor,
        embeddings_2: torch.Tensor,
        embeddings_unmasked: torch.Tensor,
        **kwargs
    ) -> Tuple[torch.Tensor, Dict[str, float]]:
        """
        Log-sum-exp uniformity loss applied to MASKED embeddings.

        CRITICAL FIX: Apply to embeddings_1 and embeddings_2 (which have gradients),
        not embeddings_unmasked (which is typically detached and won't backprop).
        This ensures the repulsive force actually trains the model to spread embeddings.
        """
        device = embeddings_1.device
        B = embeddings_1.shape[0]

        if B < 2:
            return torch.tensor(0.0, device=device), {"n_samples": B}

        # Compute uniformity for both masked views
        loss_1, mean_dist_1, min_dist_1 = self._compute_uniformity_for_embeddings(embeddings_1)
        loss_2, mean_dist_2, min_dist_2 = self._compute_uniformity_for_embeddings(embeddings_2)

        # Average the losses
        loss = (loss_1 + loss_2) / 2

        metrics = {
            "loss": loss.item(),
            "mean_dist_sq": (mean_dist_1 + mean_dist_2) / 2,
            "min_dist_sq": min(min_dist_1, min_dist_2),
            "loss_1": loss_1.item(),
            "loss_2": loss_2.item(),
        }

        return loss, metrics


# =============================================================================
# Spread Loss - Cross-entropy self-similarity (original working version)
# =============================================================================

class SpreadLoss(LossComponent):
    """
    Spread loss using cross-entropy on self-similarity matrix.

    This is the ORIGINAL spread loss that was used when AUC was 0.78+.
    It differs from UniformityLoss (log-sum-exp) - this uses cross-entropy
    where each row should be most similar to itself.

    Formula: CE(softmax(embeddings @ embeddings.T / temp), identity)

    This provides a strong repulsive force between different rows while
    maintaining that each row should match itself.
    """

    def __init__(self, config: LossConfig):
        super().__init__("spread", config)
        # Match legacy temperature (0.2 base, not 0.03)
        # Legacy compute_spread_loss uses base_temp=0.2 with adaptive scaling
        self.temperature = config.params.get("temperature", 0.2)

    def compute(
        self,
        embeddings_1: torch.Tensor,
        embeddings_2: torch.Tensor,
        embeddings_unmasked: torch.Tensor,
        **kwargs
    ) -> Tuple[torch.Tensor, Dict[str, float]]:
        """
        Compute spread loss using cross-entropy on self-similarity.

        CRITICAL: Do NOT normalize embeddings before computing spread loss!
        Legacy code (compute_spread_loss in encoders.py) uses unnormalized embeddings.
        For 128D normalized embeddings, random vectors are nearly orthogonal (dot~0),
        so the loss is ~0 and provides no gradient. Unnormalized embeddings have
        varying norms that give meaningful gradients.

        Applies to all three views: unmasked, masked_1, masked_2
        """
        device = embeddings_unmasked.device
        B = embeddings_unmasked.shape[0]
        D = embeddings_unmasked.shape[1]

        if B < 2:
            logger.warning(f"SpreadLoss: B={B} < 2, returning 0 (dim={D})")
            return torch.tensor(0.0, device=device), {"n_samples": B, "dim": D, "skipped": True}

        # Target: each row matches itself (diagonal)
        targets = torch.arange(B, device=device)

        # CRITICAL: Do NOT normalize! Use raw embeddings like legacy code.
        # Legacy: logits_joint = unmasked_encoding @ unmasked_encoding.T / temp
        # This gives non-zero gradients in high dimensions where normalized vectors are orthogonal.

        # Self-similarity matrices (unnormalized)
        logits_unmasked = embeddings_unmasked @ embeddings_unmasked.T / self.temperature
        logits_1 = embeddings_1 @ embeddings_1.T / self.temperature
        logits_2 = embeddings_2 @ embeddings_2.T / self.temperature

        # Cross-entropy losses
        loss_unmasked = F.cross_entropy(logits_unmasked, targets)
        loss_1 = F.cross_entropy(logits_1, targets)
        loss_2 = F.cross_entropy(logits_2, targets)

        # Total spread loss
        loss = loss_unmasked + loss_1 + loss_2

        # Debug: check for collapse (all embeddings identical)
        if not hasattr(self, '_collapse_check_count'):
            self._collapse_check_count = 0
        if self._collapse_check_count < 3:
            with torch.no_grad():
                diag_mean = torch.diag(logits_unmasked).mean().item()
                off_diag_mask = ~torch.eye(B, dtype=torch.bool, device=device)
                off_diag_mean = logits_unmasked[off_diag_mask].mean().item()
                sim_range = (logits_unmasked.max() - logits_unmasked.min()).item()
                logger.info(f"🔍 SpreadLoss DEBUG (D={D}): diag={diag_mean:.4f}, off_diag={off_diag_mean:.4f}, "
                           f"range={sim_range:.4f}, temp={self.temperature}")
            self._collapse_check_count += 1

        # Metrics (using unnormalized embeddings to match loss computation)
        with torch.no_grad():
            sim_matrix = embeddings_unmasked @ embeddings_unmasked.T
            # Diagonal similarity (should be high)
            diag_sim = torch.diag(sim_matrix).mean().item()
            # Off-diagonal similarity (should be low)
            mask = ~torch.eye(B, dtype=torch.bool, device=device)
            off_diag_sim = sim_matrix[mask].mean().item()

        metrics = {
            "loss": loss.item(),
            "loss_unmasked": loss_unmasked.item(),
            "loss_1": loss_1.item(),
            "loss_2": loss_2.item(),
            "diag_sim": diag_sim,
            "off_diag_sim": off_diag_sim,
            "separation": diag_sim - off_diag_sim,
            "temperature": self.temperature,
            "batch_size": B,
            "dim": D,
        }

        # Debug logging for first few batches
        if not hasattr(self, '_log_count'):
            self._log_count = 0
        if self._log_count < 5:
            logger.info(f"📊 SpreadLoss: B={B}, D={D}, loss={loss.item():.4f}, temp={self.temperature}")
            self._log_count += 1

        return loss, metrics


# =============================================================================
# Diversity Loss - Use all dimensions
# =============================================================================

class DiversityLoss(LossComponent):
    """
    Encourages embeddings to use all dimensions (not collapse to subspace).

    Penalizes dimensions with low variance across the batch.
    """

    def __init__(self, config: LossConfig):
        super().__init__("diversity", config)
        # Target std for uniform on sphere: 1/sqrt(d)
        # But we allow config override
        self.target_std_multiplier = config.params.get("target_std_multiplier", 1.0)

    def compute(
        self,
        embeddings_1: torch.Tensor,
        embeddings_2: torch.Tensor,
        embeddings_unmasked: torch.Tensor,
        **kwargs
    ) -> Tuple[torch.Tensor, Dict[str, float]]:
        """Penalize low per-dimension variance."""
        device = embeddings_unmasked.device
        B, D = embeddings_unmasked.shape

        if B < 2:
            return torch.tensor(0.0, device=device), {"n_samples": B, "d_model": D}

        # Normalize
        emb = F.normalize(embeddings_unmasked, dim=1, eps=1e-8)

        # Per-dimension std
        std_per_dim = emb.std(dim=0)

        # Target std for uniform distribution on unit sphere
        target_std = self.target_std_multiplier / (D ** 0.5)

        # Penalize dimensions below target
        deficit = torch.clamp(target_std - std_per_dim, min=0.0)
        loss = (deficit ** 2).mean()

        metrics = {
            "loss": loss.item(),
            "mean_std": std_per_dim.mean().item(),
            "min_std": std_per_dim.min().item(),
            "max_std": std_per_dim.max().item(),
            "target_std": target_std,
        }

        return loss, metrics


# =============================================================================
# Column Prediction Loss (Marginal)
# =============================================================================

class ColumnPredictionLoss(LossComponent):
    """
    Predict masked columns from visible columns.

    This is the core TASK - can we predict column A from columns B, C, D?

    Uses SAME-ROW cosine similarity (not InfoNCE across batch):
    - For each column, compute cosine similarity between prediction and target of SAME row
    - Loss = 1 - cosine_similarity (minimizes to 0 when perfectly aligned)

    This is learnable from the start because:
    - We're asking "how well does this prediction match THIS row's target?"
    - NOT "which of 128 rows does this prediction belong to?" (impossible at init)
    """

    def __init__(self, config: LossConfig):
        super().__init__("column_prediction", config)
        self.temperature = config.params.get("temperature", 0.1)
        # Use same-row cosine by default (more learnable)
        self.use_infonce = config.params.get("use_infonce", False)

    def compute(
        self,
        embeddings_1: torch.Tensor,
        embeddings_2: torch.Tensor,
        embeddings_unmasked: torch.Tensor,
        column_predictions: Optional[torch.Tensor] = None,
        column_targets: Optional[torch.Tensor] = None,
        column_mask: Optional[torch.Tensor] = None,
        **kwargs
    ) -> Tuple[torch.Tensor, Dict[str, float]]:
        """
        Same-row cosine similarity loss for column prediction.

        CRITICAL: Only computes loss on MASKED columns (TokenStatus.MARGINAL).
        Unmasked columns have trivial predictions (input=target) and would dominate
        the loss if included.

        Args:
            column_predictions: (B, n_cols, D) predicted column embeddings
            column_targets: (B, n_cols, D) target column embeddings
            column_mask: (B, n_cols) mask tensor where MARGINAL (3) = masked, OK (2) = not masked
        """
        device = embeddings_unmasked.device

        if column_predictions is None or column_targets is None:
            return torch.tensor(0.0, device=device), {"skipped": True}

        B, n_cols, D = column_predictions.shape

        # CRITICAL: Only compute loss on MASKED columns
        # If mask not provided, compute on all (backward compat, but suboptimal)
        if column_mask is not None:
            mask_bool = (column_mask == TokenStatus.MARGINAL)  # (B, n_cols) - True where masked
            n_masked = mask_bool.sum().item()
            if n_masked == 0:
                # No masked columns in this batch - skip loss computation
                return torch.tensor(0.0, device=device, requires_grad=True), {
                    "skipped": True,
                    "reason": "no_masked_columns",
                    "n_masked": 0,
                }
        else:
            mask_bool = None
            n_masked = B * n_cols  # All positions

        if self.use_infonce:
            # Original InfoNCE approach (hard to learn from scratch)
            total_loss = 0.0
            n_computed = 0
            for col_idx in range(n_cols):
                # Check if this column has any masked positions
                if mask_bool is not None:
                    col_mask = mask_bool[:, col_idx]  # (B,)
                    if not col_mask.any():
                        continue  # Skip unmasked columns
                    # Only include masked rows for this column
                    pred = F.normalize(column_predictions[col_mask, col_idx], dim=1, eps=1e-8)
                    target = F.normalize(column_targets[col_mask, col_idx], dim=1, eps=1e-8)
                    batch_size = pred.shape[0]
                    if batch_size < 2:
                        continue  # Need at least 2 samples for InfoNCE
                else:
                    pred = F.normalize(column_predictions[:, col_idx], dim=1, eps=1e-8)
                    target = F.normalize(column_targets[:, col_idx], dim=1, eps=1e-8)
                    batch_size = B

                sim_matrix = pred @ target.T / self.temperature
                targets = torch.arange(batch_size, device=device)
                col_loss = F.cross_entropy(sim_matrix, targets)
                total_loss += col_loss
                n_computed += 1
            if n_computed > 0:
                total_loss = total_loss / n_computed
            else:
                total_loss = torch.tensor(0.0, device=device, requires_grad=True)

            metrics = {
                "loss": total_loss.item() if isinstance(total_loss, torch.Tensor) else total_loss,
                "n_columns": n_computed,
                "n_masked_positions": n_masked,
                "mode": "infonce",
            }
        else:
            # Same-row cosine similarity (more learnable)
            # Normalize both predictions and targets
            pred_norm = F.normalize(column_predictions, dim=-1, eps=1e-8)  # (B, n_cols, D)
            target_norm = F.normalize(column_targets, dim=-1, eps=1e-8)  # (B, n_cols, D)

            # Compute same-row cosine similarity for each (row, col) pair
            # This is element-wise dot product along D dimension, then sum
            cosine_sim = (pred_norm * target_norm).sum(dim=-1)  # (B, n_cols)

            # Loss = 1 - cosine_similarity (0 when perfectly aligned)
            loss_per_position = 1.0 - cosine_sim  # (B, n_cols)

            # CRITICAL: Only average over MASKED positions
            if mask_bool is not None:
                # Mask out unmasked positions (set to 0) then compute mean over masked only
                masked_loss = loss_per_position * mask_bool.float()  # Zero out unmasked
                total_loss = masked_loss.sum() / n_masked  # Mean over masked positions only

                # Compute metrics only on masked positions
                masked_cosine = cosine_sim[mask_bool]  # (n_masked,)
                mean_cosine = masked_cosine.mean().item() if len(masked_cosine) > 0 else 0.0
                min_cosine = masked_cosine.min().item() if len(masked_cosine) > 0 else 0.0
                max_cosine = masked_cosine.max().item() if len(masked_cosine) > 0 else 0.0
            else:
                # No mask - average over all positions (backward compat)
                total_loss = loss_per_position.mean()
                mean_cosine = cosine_sim.mean().item()
                min_cosine = cosine_sim.min().item()
                max_cosine = cosine_sim.max().item()

            metrics = {
                "loss": total_loss.item(),
                "n_columns": n_cols,
                "n_masked_positions": n_masked,
                "mode": "cosine",
                "mean_cosine_sim": mean_cosine,
                "min_cosine_sim": min_cosine,
                "max_cosine_sim": max_cosine,
            }

        return total_loss, metrics


# =============================================================================
# Reconstruction Loss (for scalars)
# =============================================================================

class ReconstructionLoss(LossComponent):
    """
    MSE reconstruction loss for scalar columns.

    Ensures embeddings can decode back to original values.
    """

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
        """MSE between decoded and target values."""
        device = embeddings_unmasked.device

        if decoded_values is None or target_values is None:
            return torch.tensor(0.0, device=device), {"skipped": True}

        loss = F.mse_loss(decoded_values, target_values)

        metrics = {
            "loss": loss.item(),
            "mae": (decoded_values - target_values).abs().mean().item(),
        }

        return loss, metrics


# =============================================================================
# Loss Framework - Orchestrates all losses
# =============================================================================

@dataclass
class FrameworkConfig:
    """Configuration for the entire loss framework."""
    losses: Dict[str, LossConfig] = field(default_factory=dict)
    log_every_n_batches: int = 1  # Log every batch for diagnostics

    @classmethod
    def default(cls) -> "FrameworkConfig":
        """Simplified default config - just the essentials."""
        return cls(
            losses={
                # Re-enabled contrastive but we pass RAW embeddings (not predictor output)
                # in compute_total_loss_v2. The contrastive task should be: masked embedding
                # should be more similar to its own unmasked embedding than to other rows.
                "contrastive": LossConfig(enabled=True, weight=1.0, params={"temperature": 0.1}),
                # Column prediction (marginal loss) - predict original column embeddings
                # This is like BERT's MLM: predict masked tokens from context
                "column_prediction": LossConfig(enabled=True, weight=0.1, params={"temperature": 0.1}),
                "reconstruction": LossConfig(enabled=True, weight=0.05),
                # SPREAD: ENABLED - Original working spread loss (cross-entropy self-similarity)
                # This was used when AUC was 0.78+. Provides strong repulsion.
                # Temperature 0.2 matches legacy compute_spread_loss (base_temp=0.2)
                "spread": LossConfig(enabled=True, weight=1.0, params={"temperature": 0.2}),
                # Disabled - spread is better for our use case
                "separation": LossConfig(enabled=False, weight=1.0),
                "uniformity": LossConfig(enabled=False, weight=0.3, params={"temperature": 2.0}),
                "diversity": LossConfig(enabled=False, weight=1.0),
            }
        )

    @classmethod
    def minimal(cls) -> "FrameworkConfig":
        """Minimal config - just contrastive + column prediction."""
        return cls(
            losses={
                "contrastive": LossConfig(enabled=True, weight=1.0, params={"temperature": 0.1}),
                "column_prediction": LossConfig(enabled=True, weight=0.01, params={"temperature": 0.1}),
            }
        )


class LossFramework:
    """
    Orchestrates all loss components.

    Usage:
        framework = LossFramework(FrameworkConfig.default())
        total_loss, metrics = framework.compute_total(
            embeddings_1=view1,
            embeddings_2=view2,
            embeddings_unmasked=full_view,
        )
    """

    # Registry of available loss types
    LOSS_TYPES = {
        "contrastive": ContrastiveLoss,
        "separation": SeparationLoss,
        "uniformity": UniformityLoss,
        "spread": SpreadLoss,  # Original working spread loss (cross-entropy self-similarity)
        "diversity": DiversityLoss,
        "column_prediction": ColumnPredictionLoss,
        "reconstruction": ReconstructionLoss,
    }

    def __init__(self, config: FrameworkConfig):
        self.config = config
        self.components: Dict[str, LossComponent] = {}
        self._batch_count = 0

        # Instantiate configured losses
        for name, loss_config in config.losses.items():
            if name in self.LOSS_TYPES:
                self.components[name] = self.LOSS_TYPES[name](loss_config)
            else:
                logger.warning(f"Unknown loss type: {name}")

        # Log configuration
        self._log_config()

    def _log_config(self):
        """Log the active configuration."""
        logger.info("=" * 60)
        logger.info("LOSS FRAMEWORK CONFIGURATION")
        logger.info("=" * 60)

        enabled = []
        disabled = []

        for name, comp in self.components.items():
            if comp.enabled:
                enabled.append(f"  ✓ {name}: weight={comp.weight}")
            else:
                disabled.append(f"  ✗ {name}: DISABLED")

        logger.info("ENABLED losses:")
        for line in enabled:
            logger.info(line)

        if disabled:
            logger.info("DISABLED losses:")
            for line in disabled:
                logger.info(line)

        logger.info("=" * 60)

    def compute_total(
        self,
        embeddings_1: torch.Tensor,
        embeddings_2: torch.Tensor,
        embeddings_unmasked: torch.Tensor,
        **kwargs
    ) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """
        Compute total loss from all enabled components.

        Returns:
            total_loss: Weighted sum of all enabled losses
            metrics: Dict with per-component metrics and totals
        """
        device = embeddings_1.device
        all_metrics = {
            "total": 0.0,
            "components": {},
        }

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

        all_metrics["total"] = total_loss.item() if isinstance(total_loss, torch.Tensor) else total_loss

        # Periodic logging
        self._batch_count += 1
        if self._batch_count % self.config.log_every_n_batches == 0:
            self._log_batch_metrics(all_metrics)

        return total_loss, all_metrics

    def _log_batch_metrics(self, metrics: Dict[str, Any]):
        """Log metrics for this batch."""
        parts = [f"LOSS total={metrics['total']:.4f}"]
        for name, comp_metrics in metrics["components"].items():
            if "error" not in comp_metrics:
                parts.append(f"{name}={comp_metrics['weighted_loss']:.4f}")
        logger.info(" | ".join(parts))

        # Log contrastive diagnostics if available
        # CONTRASTIVE (masked→unmasked): Row-level contrastive loss
        # - Embeddings: masked view (emb1/emb2) vs unmasked view (emb_unmasked)
        # - Positives: same row (masked and unmasked are different views of the same row)
        # - Negatives: all other rows in the batch (cross-row comparisons)
        # - R@1 measures: can we match a masked embedding back to its unmasked source?
        contrastive = metrics["components"].get("contrastive", {})
        if contrastive and "pos_sim" in contrastive:
            mode = contrastive.get("mode", "unknown")
            acc = contrastive.get('accuracy', 0.0)
            pos_sim = contrastive['pos_sim']
            neg_sim = contrastive['neg_sim']
            separation = pos_sim - neg_sim
            # Compute ×random multiplier to contextualize the percentage
            bs = contrastive.get('batch_size', 256)
            random_acc = 1.0 / bs if bs > 0 else 0.004
            acc_vs_random = acc / random_acc if random_acc > 0 else 0
            logger.info(
                f"  📊 Contrastive (masked→unmasked) [{mode}]: R@1={acc:.1%} (×{acc_vs_random:.1f} random) "
                f"pos={pos_sim:.3f} neg={neg_sim:.3f} sep={separation:.3f} "
                f"loss={contrastive['loss']:.3f}"
            )

        # Log column prediction diagnostics
        col_pred = metrics["components"].get("column_prediction", {})
        if col_pred and "mean_cosine_sim" in col_pred:
            n_masked = col_pred.get('n_masked_positions', 'N/A')
            logger.info(
                f"  📊 ColPred [{col_pred.get('mode', 'unknown')}]: "
                f"mean_cosine={col_pred['mean_cosine_sim']:.3f} "
                f"n_masked={n_masked} "
                f"loss={col_pred['loss']:.3f}"
            )

    def enable(self, name: str):
        """Enable a loss component."""
        if name in self.components:
            self.components[name].config.enabled = True
            logger.info(f"Enabled loss: {name}")

    def disable(self, name: str):
        """Disable a loss component."""
        if name in self.components:
            self.components[name].config.enabled = False
            logger.info(f"Disabled loss: {name}")

    def set_weight(self, name: str, weight: float):
        """Set weight for a loss component."""
        if name in self.components:
            self.components[name].config.weight = weight
            logger.info(f"Set {name} weight to {weight}")

    def set_epoch(self, epoch: int, total_epochs: int):
        """
        Update curriculum-aware loss components for the current epoch.

        Components like ContrastiveLoss use this to blend cosine→InfoNCE.
        """
        for name, comp in self.components.items():
            if hasattr(comp, 'set_epoch'):
                comp.set_epoch(epoch, total_epochs)

    def get_summary(self) -> str:
        """Get a string summary of the framework configuration."""
        lines = ["Loss Framework Summary:"]
        for name, comp in self.components.items():
            status = "ON" if comp.enabled else "OFF"
            lines.append(f"  {name}: {status} (weight={comp.weight})")
        return "\n".join(lines)


# =============================================================================
# Dual Embedding Framework (128D + 3D)
# =============================================================================

@dataclass
class DualFrameworkConfig:
    """Configuration for dual (128D + 3D) loss framework."""
    full_config: FrameworkConfig = field(default_factory=FrameworkConfig.default)
    short_config: FrameworkConfig = field(default_factory=FrameworkConfig.default)
    short_weight: float = 1.0  # Weight for 3D loss relative to 128D
    log_every_n_batches: int = 50

    @classmethod
    def default(cls) -> "DualFrameworkConfig":
        """Default config: same losses for both, equal weight."""
        return cls(
            full_config=FrameworkConfig.default(),
            short_config=FrameworkConfig(
                losses={
                    # For 3D: contrastive + spread (same as full, but 3D is more constrained)
                    "contrastive": LossConfig(enabled=True, weight=1.0, params={"temperature": 0.07}),  # Sharper temperature for 3D
                    "spread": LossConfig(enabled=True, weight=1.0, params={"temperature": 0.03}),  # Original spread loss
                    "separation": LossConfig(enabled=True, weight=0.5),  # Extra repulsion for 3D
                }
            ),
            short_weight=0.1,  # Reduced from 1.0 - 3D spread was dominating total loss
        )

    @classmethod
    def minimal(cls) -> "DualFrameworkConfig":
        """Minimal: just contrastive for both."""
        contrastive_only = FrameworkConfig(
            losses={
                "contrastive": LossConfig(enabled=True, weight=1.0, params={"temperature": 0.1}),
            }
        )
        return cls(
            full_config=contrastive_only,
            short_config=contrastive_only,
            short_weight=1.0,
        )


class DualEmbeddingLossFramework:
    """
    Handles both 128D (full) and 3D (short) embeddings.

    Runs the loss framework twice - once for each embedding type.
    This allows different configurations for each if needed.

    Usage:
        framework = DualEmbeddingLossFramework(DualFrameworkConfig.default())
        total_loss, metrics = framework.compute_total(
            full_embeddings_1=full_view1,
            full_embeddings_2=full_view2,
            full_embeddings_unmasked=full_unmasked,
            short_embeddings_1=short_view1,
            short_embeddings_2=short_view2,
            short_embeddings_unmasked=short_unmasked,
        )
    """

    def __init__(self, config: DualFrameworkConfig):
        self.config = config
        self.full_framework = LossFramework(config.full_config)
        self.short_framework = LossFramework(config.short_config)
        self._batch_count = 0

        logger.info("=" * 60)
        logger.info("DUAL EMBEDDING LOSS FRAMEWORK")
        logger.info(f"  Short (3D) weight: {config.short_weight}")
        logger.info("=" * 60)

    def compute_total(
        self,
        full_embeddings_1: torch.Tensor,
        full_embeddings_2: torch.Tensor,
        full_embeddings_unmasked: torch.Tensor,
        short_embeddings_1: torch.Tensor,
        short_embeddings_2: torch.Tensor,
        short_embeddings_unmasked: torch.Tensor,
        **kwargs
    ) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """
        Compute total loss for both 128D and 3D embeddings.

        Returns:
            total_loss: full_loss + short_weight * short_loss
            metrics: Dict with metrics for both embedding types
        """
        # Compute 128D loss
        full_loss, full_metrics = self.full_framework.compute_total(
            embeddings_1=full_embeddings_1,
            embeddings_2=full_embeddings_2,
            embeddings_unmasked=full_embeddings_unmasked,
            **kwargs
        )

        # Compute 3D loss
        short_loss, short_metrics = self.short_framework.compute_total(
            embeddings_1=short_embeddings_1,
            embeddings_2=short_embeddings_2,
            embeddings_unmasked=short_embeddings_unmasked,
            # Don't pass column_predictions etc to short - not applicable
        )

        # Combine
        total_loss = full_loss + self.config.short_weight * short_loss

        metrics = {
            "total": total_loss.item(),
            "full": full_metrics,
            "short": short_metrics,
            "full_loss": full_loss.item(),
            "short_loss": short_loss.item(),
        }

        # Periodic logging
        self._batch_count += 1
        if self._batch_count % self.config.log_every_n_batches == 0:
            self._log_batch_metrics(metrics)

        return total_loss, metrics

    def set_epoch(self, epoch: int, total_epochs: int):
        """
        Update curriculum-aware loss components for the current epoch.

        Propagates to both full (128D) and short (3D) frameworks.
        """
        self.full_framework.set_epoch(epoch, total_epochs)
        self.short_framework.set_epoch(epoch, total_epochs)

    def _log_batch_metrics(self, metrics: Dict[str, Any]):
        """Log combined metrics."""
        full_total = metrics["full"]["total"]
        short_total = metrics["short"]["total"]

        # Build component summary for full
        full_parts = []
        for name, comp_metrics in metrics["full"]["components"].items():
            if "error" not in comp_metrics and "weighted_loss" in comp_metrics:
                full_parts.append(f"{name}={comp_metrics['weighted_loss']:.3f}")

        # Build component summary for short
        short_parts = []
        for name, comp_metrics in metrics["short"]["components"].items():
            if "error" not in comp_metrics and "weighted_loss" in comp_metrics:
                short_parts.append(f"{name}={comp_metrics['weighted_loss']:.3f}")

        logger.info(
            f"📊 LOSS total={metrics['total']:.3f} | "
            f"128D={full_total:.3f} [{', '.join(full_parts)}] | "
            f"3D={short_total:.3f} [{', '.join(short_parts)}]"
        )

    def get_summary(self) -> str:
        """Get summary of both frameworks."""
        lines = [
            "Dual Embedding Loss Framework:",
            f"  Short weight: {self.config.short_weight}",
            "",
            "128D (Full) Framework:",
        ]
        for name, comp in self.full_framework.components.items():
            status = "ON" if comp.enabled else "OFF"
            lines.append(f"    {name}: {status} (weight={comp.weight})")

        lines.append("")
        lines.append("3D (Short) Framework:")
        for name, comp in self.short_framework.components.items():
            status = "ON" if comp.enabled else "OFF"
            lines.append(f"    {name}: {status} (weight={comp.weight})")

        return "\n".join(lines)


# =============================================================================
# Convenience functions
# =============================================================================

def create_default_framework() -> LossFramework:
    """Create a framework with sensible defaults."""
    return LossFramework(FrameworkConfig.default())


def create_minimal_framework() -> LossFramework:
    """Create a minimal framework for testing."""
    return LossFramework(FrameworkConfig.minimal())


def create_dual_framework() -> DualEmbeddingLossFramework:
    """Create dual framework with sensible defaults."""
    return DualEmbeddingLossFramework(DualFrameworkConfig.default())


def create_framework_from_dict(config_dict: Dict[str, Any]) -> LossFramework:
    """
    Create a framework from a dictionary config.

    Example:
        config = {
            "contrastive": {"enabled": True, "weight": 1.0, "temperature": 0.1},
            "separation": {"enabled": False},
        }
        framework = create_framework_from_dict(config)
    """
    losses = {}
    for name, params in config_dict.items():
        if isinstance(params, dict):
            params = params.copy()  # Don't mutate original
            enabled = params.pop("enabled", True)
            weight = params.pop("weight", 1.0)
            losses[name] = LossConfig(enabled=enabled, weight=weight, params=params)

    return LossFramework(FrameworkConfig(losses=losses))
