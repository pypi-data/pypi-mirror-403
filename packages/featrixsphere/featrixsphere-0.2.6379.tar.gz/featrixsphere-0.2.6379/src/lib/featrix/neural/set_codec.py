#
#
#  Proprietary and Confidential.  Unauthorized use, copying or dissemination
#  of these materials is strictly prohibited.
#
#  -*- coding: utf-8 -*-
#
#  Copyright Featrix, Inc 2023-2025
#
#  Proprietary and Confidential.  Unauthorized use, copying or dissemination
#  of these materials is strictly prohibited.
#
import base64
import hashlib
import io
import logging
import os
import pickle
import traceback
import sys
from typing import Optional

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from .gpu_utils import get_device
from featrix.neural.gpu_utils import is_gpu_available, empty_gpu_cache
from featrix.neural.embedding_utils import NormalizedEmbedding
from featrix.neural.featrix_token import Token
from featrix.neural.featrix_token import TokenStatus
from featrix.neural.model_config import ColumnType
from featrix.neural.model_config import SetEncoderConfig
from featrix.neural.string_codec import STRING_DIM
from featrix.neural.simple_mlp import SimpleMLP
from featrix.neural.simple_mlp import SimpleMLPConfig

logger = logging.getLogger(__name__)


class FocalLoss(nn.Module):
    """
    Focal Loss for addressing class imbalance in classification tasks.
    
    Focal Loss down-weights easy examples and focuses learning on hard examples.
    This is particularly effective for extreme class imbalance where standard
    cross-entropy (even with class weights) fails.
    
    Paper: "Focal Loss for Dense Object Detection" (Lin et al., 2017)
    https://arxiv.org/abs/1708.02002
    
    Args:
        alpha: Class weights tensor (optional). Should be same shape as number of classes.
        gamma: Focusing parameter. Higher values focus more on hard examples.
               gamma=0 reduces to standard cross-entropy.
               gamma=2 is recommended in the paper.
        min_weight: Minimum weight for easy examples (default=0.1).
                   Ensures correct predictions still get some credit.
    
    Example:
        For a 97% vs 3% class imbalance with gamma=2, min_weight=0.1:
        - Easy examples (97% confident) get weight max(0.1, (1-0.97)^2) = 0.1
        - Hard examples (60% confident) get weight (1-0.60)^2 = 0.16
        This gives 1.6x more weight to hard examples while still rewarding easy examples!
    """
    def __init__(self, alpha=None, gamma=2.0, min_weight=0.1):
        super().__init__()
        self.alpha = alpha  # class weights (tensor)
        self.gamma = gamma  # focusing parameter (higher = more focus on hard examples)
        self.min_weight = min_weight  # minimum weight for easy examples
    
    def forward(self, inputs, targets):
        """
        Args:
            inputs: Raw logits from model (batch_size, num_classes)
            targets: Ground truth class indices (batch_size,)
        
        Returns:
            Mean focal loss across the batch
        """
        # CRITICAL: Ensure inputs and targets are on the same device
        # This can happen if string codecs moved tokens to CPU but targets are still on GPU
        # OR if prediction is on CPU but targets are on GPU
        if inputs.device != targets.device:
            # Move targets to match inputs device (prediction's device)
            original_target_device = targets.device
            targets = targets.to(inputs.device)
            # Don't log device moves - too noisy
        
        # Compute cross entropy loss (per sample, not reduced)
        ce_loss = F.cross_entropy(inputs, targets, reduction='none', weight=self.alpha)
        
        # Get probability of the correct class
        # pt is the model's confidence in the correct class
        pt = torch.exp(-ce_loss)
        
        # Focal loss formula: FL = max(min_weight, (1 - pt)^gamma) * CE
        # When pt is high (easy example), clamp to min_weight → still get some credit
        # When pt is low (hard example), (1-pt)^gamma is large → up-weight
        focal_weight = torch.clamp((1 - pt) ** self.gamma, min=self.min_weight)
        focal_loss = focal_weight * ce_loss
        
        # Always use mean - that's the only thing that makes sense
        return focal_loss.mean()


class CostSensitiveFocalLoss(nn.Module):
    """
    Cost-Sensitive Focal Loss with automatic FP/FN costs from class imbalance.

    Combines Focal Loss's hard example mining with asymmetric misclassification costs
    derived automatically from class distribution. Minority class errors cost more.

    Args:
        class_counts: Tensor or list of class counts, e.g., [9000, 1000] for 90/10 split.
                      Costs are computed as inverse frequency: cost[i] = total / count[i].
                      If None, uses equal costs (reduces to standard Focal Loss).
        gamma: Focal loss focusing parameter. Higher = more focus on hard examples.
        min_weight: Minimum focal weight for easy examples.
        cost_exponent: Exponent for cost scaling. Default=1.0 (linear).
                       Use 0.5 for sqrt scaling (less aggressive), 2.0 for squared (more aggressive).
        max_cost_ratio: Cap the max/min cost ratio to prevent extreme values. Default=100.

    Example:
        # 97% negative, 3% positive → cost_fn ≈ 32x cost_fp
        >>> loss_fn = CostSensitiveFocalLoss(class_counts=[9700, 300], gamma=2.0)

        # Balanced → equal costs (same as regular FocalLoss)
        >>> loss_fn = CostSensitiveFocalLoss(class_counts=[500, 500], gamma=2.0)

        # Unknown distribution → compute at runtime from first batch
        >>> loss_fn = CostSensitiveFocalLoss(class_counts=None, gamma=2.0)
    """
    def __init__(self, class_counts=None, gamma=2.0, min_weight=0.1, cost_exponent=1.0, max_cost_ratio=100.0):
        super().__init__()
        self.gamma = gamma
        self.min_weight = min_weight
        self.cost_exponent = cost_exponent
        self.max_cost_ratio = max_cost_ratio

        # Compute costs from class counts
        if class_counts is not None:
            self.register_buffer('class_costs', self._compute_costs(class_counts))
        else:
            self.class_costs = None  # Will be computed from first batch

    def _compute_costs(self, class_counts):
        """Compute per-class costs from counts. Minority classes get higher costs."""
        if isinstance(class_counts, torch.Tensor):
            counts = class_counts.float()
        else:
            counts = torch.tensor(class_counts, dtype=torch.float32)

        total = counts.sum()
        # Inverse frequency: rare classes get high cost
        # cost[i] = (total / count[i]) ^ exponent
        costs = (total / counts.clamp(min=1)) ** self.cost_exponent

        # Normalize so mean cost = 1 (doesn't change loss scale)
        costs = costs / costs.mean()

        # Cap extreme ratios
        max_cost = costs.max()
        min_cost = costs.min()
        if max_cost / min_cost > self.max_cost_ratio:
            # Clamp to max ratio while preserving relative ordering
            costs = costs.clamp(min=max_cost / self.max_cost_ratio)
            costs = costs / costs.mean()  # Re-normalize

        return costs

    def forward(self, inputs, targets):
        """
        Args:
            inputs: Raw logits (batch_size, num_classes)
            targets: Ground truth class indices (batch_size,)

        Returns:
            Mean cost-sensitive focal loss
        """
        if inputs.device != targets.device:
            targets = targets.to(inputs.device)

        num_classes = inputs.size(1)

        # Compute costs from batch if not pre-computed
        if self.class_costs is None:
            # Estimate class counts from this batch
            batch_counts = torch.bincount(targets, minlength=num_classes).float()
            # CRITICAL: Register as buffer so it moves with .cpu()/.cuda()/.to()
            self.register_buffer('class_costs', self._compute_costs(batch_counts).to(inputs.device))

        # Ensure costs are on correct device
        if self.class_costs.device != inputs.device:
            self.class_costs = self.class_costs.to(inputs.device)

        # Compute softmax probabilities
        probs = F.softmax(inputs, dim=1)

        # Get probability of the correct class
        pt = probs.gather(1, targets.unsqueeze(1)).squeeze(1)

        # Focal weight: down-weight easy examples
        focal_weight = torch.clamp((1 - pt) ** self.gamma, min=self.min_weight)

        # Get cost weight per sample based on true class
        cost_weights = self.class_costs[targets]

        # Compute cross-entropy loss per sample
        ce_loss = F.cross_entropy(inputs, targets, reduction='none')

        # Combine: focal_weight * cost_weight * cross_entropy
        loss = focal_weight * cost_weights * ce_loss

        return loss.mean()


class PRAUCLoss(nn.Module):
    """
    PR-AUC Optimized Loss for imbalanced binary classification.
    
    This loss function directly optimizes for Precision-Recall AUC by using a
    differentiable surrogate that encourages ranking positive examples higher
    than negative examples, which is what PR-AUC measures.
    
    The loss uses an efficient approximation of average precision (AP) that:
    1. Computes a ranking loss that encourages positives to rank above negatives
    2. Uses class-weighted cross-entropy for stability and to handle imbalance
    
    This is particularly effective for imbalanced datasets where PR-AUC is more
    informative than ROC-AUC.
    
    Args:
        alpha: Class weights tensor (optional). Should be same shape as number of classes.
        temperature: Temperature parameter for soft ranking (default=1.0).
                    Lower values make ranking more strict.
        ranking_weight: Weight for ranking component (default=0.7).
        ce_weight: Weight for cross-entropy component (default=0.3).
    """
    def __init__(
        self,
        alpha=None,                 # class weights for CE, shape (2,)
        temperature=1.0,
        ranking_weight=0.6,
        ce_weight=0.4,
        margin=0.1,
        frac=0.25,                  # fraction of each class to consider as tails
        max_pairs=4096,
        max_k=64,
        max_m=64,
        use_logit_margin=True
    ):
        super().__init__()
        self.alpha = alpha
        self.temperature = float(temperature)
        self.margin = float(margin)
        self.frac = float(frac)
        self.max_pairs = int(max_pairs)
        self.max_k = int(max_k)
        self.max_m = int(max_m)
        self.use_logit_margin = bool(use_logit_margin)

        tw = ranking_weight + ce_weight
        self.ranking_weight = ranking_weight / tw if tw > 0 else 0.6
        self.ce_weight = ce_weight / tw if tw > 0 else 0.4

    def forward(self, inputs, targets):
        if inputs.device != targets.device:
            targets = targets.to(inputs.device)

        if inputs.size(1) != 2:
            return F.cross_entropy(inputs, targets, reduction="mean", weight=self.alpha)

        scores = (inputs[:, 1] - inputs[:, 0]) if self.use_logit_margin else inputs[:, 1]

        pos_mask = (targets == 1)
        neg_mask = (targets == 0)

        ranking_loss = inputs.new_tensor(0.0)
        n_pos = int(pos_mask.sum())
        n_neg = int(neg_mask.sum())

        if n_pos > 0 and n_neg > 0:
            pos_scores = scores[pos_mask]
            neg_scores = scores[neg_mask]

            # adaptive tail sizes (fraction of each class, with sane minimums)
            k = min(self.max_k, max(8, int(self.frac * n_neg)))
            m = min(self.max_m, max(8, int(self.frac * n_pos)))
            k = min(k, n_neg)
            m = min(m, n_pos)

            hard_negs = torch.topk(neg_scores, k=k, largest=True).values   # high negatives
            hard_pos  = torch.topk(pos_scores, k=m, largest=False).values  # low positives

            # cap total pairs
            pairs = k * m
            if pairs > self.max_pairs:
                scale = (self.max_pairs / pairs) ** 0.5
                k2 = max(1, int(k * scale))
                m2 = max(1, int(m * scale))
                hard_negs = hard_negs[:k2]
                hard_pos = hard_pos[:m2]

            temp = max(self.temperature, 1e-6)
            diff = (hard_negs[:, None] - hard_pos[None, :] + self.margin) / temp
            ranking_loss = F.softplus(diff).mean()

        ce_loss = F.cross_entropy(inputs, targets, reduction="mean", weight=self.alpha)
        return self.ranking_weight * ranking_loss + self.ce_weight * ce_loss


class AdaptiveVotingLoss(nn.Module):
    """
    Win-rate based loss blending - weights losses by how often they "win" (are lowest).

    Combines FocalLoss (multiple gammas), PRAUCLoss, and CrossEntropyLoss with weights
    determined by tracking which loss is lowest each batch during training.

    WARNING: This approach can create self-reinforcing feedback loops where whichever
    loss happens to be lowest early gets higher weight, causing it to stay lowest
    while other losses are starved of gradient signal.

    Usage:
        loss_fn = AdaptiveVotingLoss(alpha=class_weights)
        loss = loss_fn(logits, targets)

    Args:
        alpha: Class weights tensor (optional)
        class_counts: Class counts for CostSensitiveFocalLoss (optional)
        temperature: Not used, kept for API compatibility
        focal_gamma: Not used, kept for API compatibility
        focal_min_weight: Minimum weight for focal loss (default: 0.1)
    """
    
    def __init__(
        self,
        alpha=None,
        class_counts=None,
        initial_weights=None,  # unused, kept for API compatibility
        learnable=True,        # unused, kept for API compatibility
        temperature=1.0,       # unused, kept for API compatibility
        focal_gamma=2.0,       # unused, kept for API compatibility
        focal_min_weight=0.1
    ):
        super().__init__()
        self.alpha = alpha
        self.class_counts = class_counts

        # Initialize individual loss functions
        # Use CostSensitiveFocalLoss if class_counts provided, otherwise fall back to FocalLoss
        if class_counts is not None:
            # Cost-sensitive focal losses with different gamma values
            self.focal_loss_g2 = CostSensitiveFocalLoss(class_counts=class_counts, gamma=2.0, min_weight=focal_min_weight)
            self.focal_loss_g3 = CostSensitiveFocalLoss(class_counts=class_counts, gamma=3.0, min_weight=focal_min_weight)
            self.focal_loss_g4 = CostSensitiveFocalLoss(class_counts=class_counts, gamma=4.0, min_weight=focal_min_weight)
        else:
            # Fall back to standard FocalLoss with alpha weights
            self.focal_loss_g2 = FocalLoss(alpha=alpha, gamma=2.0, min_weight=focal_min_weight)
            self.focal_loss_g3 = FocalLoss(alpha=alpha, gamma=3.0, min_weight=focal_min_weight)
            self.focal_loss_g4 = FocalLoss(alpha=alpha, gamma=4.0, min_weight=focal_min_weight)
        self.prauc_loss = PRAUCLoss(alpha=alpha)
        self.ce_loss = nn.CrossEntropyLoss(weight=alpha) if alpha is not None else nn.CrossEntropyLoss()

        # Loss names for logging
        self._loss_names = ['F_g2', 'F_g3', 'F_g4', 'PRAUC', 'CE']

        # No learnable parameters - weights are computed from win rates
        # Keep these for backward compatibility with old checkpoints
        self.weight_logits = None
        self.weight_net = None
        
        # Track epoch progress (set externally)
        self.epoch_progress = 0.0

        # Track running statistics for logging
        self._last_weights = None
        self._last_individual_losses = None
        self._weight_history = []

        # Track win counts (which loss is lowest each batch)
        # Now 5 losses: [focal_g2, focal_g3, focal_g4, prauc, ce]
        self._train_win_counts = [0, 0, 0, 0, 0]
        self._train_total_batches = 0
        self._val_win_counts = [0, 0, 0, 0, 0]
        self._val_total_batches = 0

        # Mode flag: 'train' or 'val' - only train wins affect weights
        self._mode = 'train'

        # Track mean losses for train vs val comparison (per loss type)
        self._train_loss_sums = [0.0, 0.0, 0.0, 0.0, 0.0]
        self._val_loss_sums = [0.0, 0.0, 0.0, 0.0, 0.0]
    
    def set_epoch_progress(self, progress: float):
        """Set current epoch progress (0.0 to 1.0) for context."""
        self.epoch_progress = min(1.0, max(0.0, progress))

    def set_mode(self, mode: str):
        """Set mode to 'train' or 'val'. Only train wins affect weights."""
        assert mode in ('train', 'val'), f"Mode must be 'train' or 'val', got {mode}"
        self._mode = mode
    
    def _compute_batch_features(self, inputs, targets):
        """Compute batch statistics for weight prediction."""
        with torch.no_grad():
            probs = F.softmax(inputs, dim=-1)
            
            # Class distribution in this batch
            n_samples = len(targets)
            class_0_ratio = (targets == 0).float().mean().item() if n_samples > 0 else 0.5
            class_1_ratio = (targets == 1).float().mean().item() if n_samples > 0 else 0.5
            
            # Prediction confidence statistics
            max_probs = probs.max(dim=-1).values
            mean_conf = max_probs.mean().item()
            std_conf = max_probs.std().item() if len(max_probs) > 1 else 0.0
            max_conf = max_probs.max().item()
            
            # Build feature vector
            features = torch.tensor([
                class_0_ratio,
                class_1_ratio, 
                mean_conf,
                std_conf,
                max_conf,
                self.epoch_progress
            ], device=inputs.device, dtype=inputs.dtype)
            
            return features.unsqueeze(0)  # [1, 6]
    
    def get_current_weights(self):
        """Get current loss weights (for logging)."""
        return self._last_weights
    
    def forward(self, inputs, targets):
        """
        Compute adaptively weighted loss.

        Args:
            inputs: Raw logits from model (batch_size, num_classes)
            targets: Ground truth class indices (batch_size,)

        Returns:
            Weighted combination of losses
        """
        # Ensure same device
        if inputs.device != targets.device:
            targets = targets.to(inputs.device)

        # Only works for binary classification with PRAUCLoss
        is_binary = inputs.size(1) == 2

        # Compute individual losses - multiple focal gammas
        focal_g2 = self.focal_loss_g2(inputs, targets)
        focal_g3 = self.focal_loss_g3(inputs, targets)
        focal_g4 = self.focal_loss_g4(inputs, targets)
        ce = self.ce_loss(inputs, targets)

        if is_binary:
            prauc = self.prauc_loss(inputs, targets)
        else:
            # PRAUCLoss only works for binary - use focal_g2 as substitute
            prauc = focal_g2

        # All losses as a list: [focal_g2, focal_g3, focal_g4, prauc, ce]
        all_losses = [focal_g2, focal_g3, focal_g4, prauc, ce]

        # Track loss values
        loss_vals = [l.detach().item() for l in all_losses]
        self._last_individual_losses = tuple(loss_vals)

        # Track which loss "wins" (is lowest) this batch - use raw values
        winner = loss_vals.index(min(loss_vals))

        # Track wins and loss sums separately for train and val
        if self._mode == 'train':
            self._train_win_counts[winner] += 1
            self._train_total_batches += 1
            for i, val in enumerate(loss_vals):
                self._train_loss_sums[i] += val
        else:
            self._val_win_counts[winner] += 1
            self._val_total_batches += 1
            for i, val in enumerate(loss_vals):
                self._val_loss_sums[i] += val

        # Compute weights based on TRAINING win rates only
        # During validation, use frozen weights from training
        if self._mode == 'train':
            if self._train_total_batches >= 10:
                win_rates = torch.tensor(
                    [max(0.01, c / self._train_total_batches) for c in self._train_win_counts],
                    device=inputs.device,
                    dtype=inputs.dtype
                )
                weights = win_rates / win_rates.sum()
            else:
                weights = torch.tensor([0.2, 0.2, 0.2, 0.2, 0.2], device=inputs.device, dtype=inputs.dtype)
            # Cache weights for validation (convert to float32 for numpy compatibility with BFloat16)
            self._frozen_weights = weights.detach().cpu().float().numpy()
        else:
            # Validation: use frozen weights from training
            if hasattr(self, '_frozen_weights') and self._frozen_weights is not None:
                weights = torch.tensor(self._frozen_weights, device=inputs.device, dtype=inputs.dtype)
            else:
                weights = torch.tensor([0.2, 0.2, 0.2, 0.2, 0.2], device=inputs.device, dtype=inputs.dtype)

        # Store for logging (convert to float32 for numpy compatibility with BFloat16)
        self._last_weights = weights.detach().cpu().float().numpy()

        # Weighted combination of all 5 losses
        total_loss = (weights[0] * focal_g2 + weights[1] * focal_g3 + weights[2] * focal_g4 +
                      weights[3] * prauc + weights[4] * ce)

        return total_loss

    def get_weight_summary(self) -> str:
        """Get summary of current weights for logging."""
        if self._last_weights is None:
            return "weights not computed yet"
        w = self._last_weights
        # 5 losses: F_g2, F_g3, F_g4, PRAUC, CE
        if len(w) == 5:
            summary = f"F2={w[0]:.2f}, F3={w[1]:.2f}, F4={w[2]:.2f}, P={w[3]:.2f}, CE={w[4]:.2f}"
        else:
            # Old 3-weight format
            summary = f"focal={w[0]:.2f}, prauc={w[1]:.2f}, ce={w[2]:.2f}"

        if hasattr(self, '_last_individual_losses') and self._last_individual_losses is not None:
            losses = self._last_individual_losses
            if len(losses) == 5:
                summary += f" | losses: {losses[0]:.3f}, {losses[1]:.3f}, {losses[2]:.3f}, {losses[3]:.3f}, {losses[4]:.3f}"
            else:
                summary += f" | losses: F={losses[0]:.4f}, P={losses[1]:.4f}, CE={losses[2]:.4f}"

        # Show train win rates
        if hasattr(self, '_train_total_batches') and self._train_total_batches > 0:
            n = len(self._train_win_counts)
            pcts = [100 * self._train_win_counts[i] / self._train_total_batches for i in range(n)]
            if n == 5:
                summary += f" | train_wins: F2={pcts[0]:.0f}%, F3={pcts[1]:.0f}%, F4={pcts[2]:.0f}%, P={pcts[3]:.0f}%, CE={pcts[4]:.0f}%"

        # Show train vs val loss comparison
        if (hasattr(self, '_train_total_batches') and self._train_total_batches > 0 and
            hasattr(self, '_val_total_batches') and self._val_total_batches > 0):
            train_means = [s / self._train_total_batches for s in self._train_loss_sums]
            val_means = [s / self._val_total_batches for s in self._val_loss_sums]
            # Show gap (val - train) for each loss type
            gaps = [val_means[i] - train_means[i] for i in range(5)]
            summary += f" | gap(v-t): F2={gaps[0]:+.3f}, F3={gaps[1]:+.3f}, F4={gaps[2]:+.3f}, P={gaps[3]:+.3f}, CE={gaps[4]:+.3f}"

        return summary

    def reset_win_counts(self):
        """Reset win counts and loss sums (call at start of each epoch)."""
        n = len(self._loss_names) if hasattr(self, '_loss_names') else 5
        self._train_win_counts = [0] * n
        self._train_total_batches = 0
        self._val_win_counts = [0] * n
        self._val_total_batches = 0
        self._train_loss_sums = [0.0] * n
        self._val_loss_sums = [0.0] * n

    def get_weights_dict(self) -> dict:
        """Get current weights as a dictionary for epoch metrics/charting."""
        result = {}

        # Current blending weights (5 losses: F_g2, F_g3, F_g4, PRAUC, CE)
        if self._last_weights is not None:
            w = self._last_weights
            if len(w) == 5:
                result["adaptive_weight_focal_g2"] = float(w[0])
                result["adaptive_weight_focal_g3"] = float(w[1])
                result["adaptive_weight_focal_g4"] = float(w[2])
                result["adaptive_weight_prauc"] = float(w[3])
                result["adaptive_weight_ce"] = float(w[4])
            else:
                # Old 3-weight format
                result["adaptive_weight_focal"] = float(w[0])
                result["adaptive_weight_prauc"] = float(w[1])
                result["adaptive_weight_ce"] = float(w[2])

        # Win rates (what percentage of batches each loss "won")
        if hasattr(self, '_train_total_batches') and self._train_total_batches > 0:
            n = len(self._train_win_counts)
            for i in range(n):
                pct = self._train_win_counts[i] / self._train_total_batches
                if n == 5:
                    names = ["focal_g2", "focal_g3", "focal_g4", "prauc", "ce"]
                    result[f"adaptive_winrate_{names[i]}"] = float(pct)
                else:
                    names = ["focal", "prauc", "ce"]
                    result[f"adaptive_winrate_{names[i]}"] = float(pct)

        # Individual loss values (last batch)
        if hasattr(self, '_last_individual_losses') and self._last_individual_losses is not None:
            losses = self._last_individual_losses
            if len(losses) == 5:
                result["adaptive_loss_focal_g2"] = float(losses[0])
                result["adaptive_loss_focal_g3"] = float(losses[1])
                result["adaptive_loss_focal_g4"] = float(losses[2])
                result["adaptive_loss_prauc"] = float(losses[3])
                result["adaptive_loss_ce"] = float(losses[4])
            else:
                result["adaptive_loss_focal"] = float(losses[0])
                result["adaptive_loss_prauc"] = float(losses[1])
                result["adaptive_loss_ce"] = float(losses[2])

        return result

    def get_gradient_diagnostics(self) -> str:
        """Get win-rate info (no gradients used anymore)."""
        if self._train_total_batches > 0:
            return f"win-rate weights (no grad), {self._train_total_batches} train batches, {self._val_total_batches} val batches"
        return "win-rate weights (no grad), no batches yet"


class AdaptiveAUCGuidedLoss(nn.Module):
    """
    AUC-guided loss blending - adjusts weights based on validation AUC feedback.

    Unlike voting (unstable) or learning (optimizes loss not AUC), this approach:
    1. Uses stable weights during each epoch (no per-batch changes)
    2. After each epoch, receives the validation AUC via update_from_auc()
    3. Tracks which weights produced the best AUC so far
    4. When AUC improves: keep current weights, save as new best
    5. When AUC degrades: blend toward the best-known weights

    This provides the 6% lift from adaptive loss while eliminating variance
    from per-batch weight updates.

    Usage:
        loss_fn = AdaptiveAUCGuidedLoss(alpha=class_weights)
        for epoch in range(n_epochs):
            # Training loop uses stable weights
            for batch in train_loader:
                loss = loss_fn(logits, targets)
                loss.backward()
            # After epoch, update weights based on validation AUC
            val_auc = compute_validation_auc()
            loss_fn.update_from_auc(val_auc)

    Args:
        alpha: Class weights tensor (optional)
        class_counts: Class counts for CostSensitiveFocalLoss (optional)
        initial_weights: Starting weights [f_g2, f_g3, f_g4, prauc, ce] (default: equal)
        blend_rate: How fast to blend toward best weights when AUC drops (default: 0.3)
        exploration_rate: Chance to try small random weight perturbation (default: 0.1)
    """

    def __init__(
        self,
        alpha=None,
        class_counts=None,
        initial_weights=None,
        learnable=True,        # unused, kept for API compatibility
        temperature=1.0,       # unused, kept for API compatibility
        focal_gamma=2.0,       # unused, kept for API compatibility
        focal_min_weight=0.1,
        blend_rate=0.3,
        exploration_rate=0.1
    ):
        super().__init__()
        self.alpha = alpha
        self.class_counts = class_counts
        self.blend_rate = blend_rate
        self.exploration_rate = exploration_rate

        # Initialize individual loss functions
        if class_counts is not None:
            self.focal_loss_g2 = CostSensitiveFocalLoss(class_counts=class_counts, gamma=2.0, min_weight=focal_min_weight)
            self.focal_loss_g3 = CostSensitiveFocalLoss(class_counts=class_counts, gamma=3.0, min_weight=focal_min_weight)
            self.focal_loss_g4 = CostSensitiveFocalLoss(class_counts=class_counts, gamma=4.0, min_weight=focal_min_weight)
        else:
            self.focal_loss_g2 = FocalLoss(alpha=alpha, gamma=2.0, min_weight=focal_min_weight)
            self.focal_loss_g3 = FocalLoss(alpha=alpha, gamma=3.0, min_weight=focal_min_weight)
            self.focal_loss_g4 = FocalLoss(alpha=alpha, gamma=4.0, min_weight=focal_min_weight)
        self.prauc_loss = PRAUCLoss(alpha=alpha)
        self.ce_loss = nn.CrossEntropyLoss(weight=alpha) if alpha is not None else nn.CrossEntropyLoss()

        # Loss names for logging
        self._loss_names = ['F_g2', 'F_g3', 'F_g4', 'PRAUC', 'CE']

        # Current weights (stable during each epoch)
        if initial_weights is not None:
            self._current_weights = np.array(initial_weights, dtype=np.float32)
            self._current_weights = self._current_weights / self._current_weights.sum()
        else:
            self._current_weights = np.array([0.2, 0.2, 0.2, 0.2, 0.2], dtype=np.float32)

        # Best weights (produced highest AUC so far)
        self._best_weights = self._current_weights.copy()
        self._best_auc = 0.0

        # History for analysis
        self._auc_history = []
        self._weight_history = []

        # Track epoch progress and mode
        self.epoch_progress = 0.0
        self._mode = 'train'
        self._current_epoch = 0

        # For logging
        self._last_weights = None
        self._last_individual_losses = None
        self._train_total_batches = 0
        self._val_total_batches = 0

        # Per-loss AUC tracking (for smarter weight adjustment)
        self._loss_auc_correlations = [0.0, 0.0, 0.0, 0.0, 0.0]

        logger.info(f"🎯 AdaptiveAUCGuidedLoss initialized: blend_rate={blend_rate}, exploration={exploration_rate}")

    def set_epoch_progress(self, progress: float):
        """Set current epoch progress (0.0 to 1.0)."""
        self.epoch_progress = min(1.0, max(0.0, progress))

    def set_mode(self, mode: str):
        """Set mode to 'train' or 'val'."""
        assert mode in ('train', 'val'), f"Mode must be 'train' or 'val', got {mode}"
        self._mode = mode

    def update_from_auc(self, val_auc: float, epoch: int = None):
        """
        Update weights based on validation AUC feedback.

        Call this after each epoch with the validation AUC.

        Args:
            val_auc: Validation AUC-ROC for this epoch
            epoch: Current epoch number (optional, for logging)
        """
        if epoch is not None:
            self._current_epoch = epoch

        self._auc_history.append(val_auc)
        self._weight_history.append(self._current_weights.copy())

        old_weights = self._current_weights.copy()

        if val_auc > self._best_auc:
            # AUC improved - save current weights as best
            self._best_auc = val_auc
            self._best_weights = self._current_weights.copy()
            logger.info(f"🎯 AUC improved to {val_auc:.4f} - saving weights as new best: {self._format_weights(self._current_weights)}")

            # Slight exploration: try small random perturbation
            if np.random.random() < self.exploration_rate:
                perturbation = np.random.randn(5) * 0.05
                self._current_weights = self._current_weights + perturbation
                self._current_weights = np.clip(self._current_weights, 0.02, 0.8)
                self._current_weights = self._current_weights / self._current_weights.sum()
                logger.info(f"   🎲 Exploring: {self._format_weights(old_weights)} → {self._format_weights(self._current_weights)}")
        else:
            # AUC degraded or stayed same - blend toward best weights
            auc_drop = self._best_auc - val_auc
            # Blend more aggressively for larger drops
            adaptive_blend = min(0.8, self.blend_rate * (1 + auc_drop * 10))

            self._current_weights = (1 - adaptive_blend) * self._current_weights + adaptive_blend * self._best_weights
            self._current_weights = self._current_weights / self._current_weights.sum()

            logger.info(f"🎯 AUC {val_auc:.4f} < best {self._best_auc:.4f} (Δ={-auc_drop:.4f}) - blending toward best weights")
            logger.info(f"   {self._format_weights(old_weights)} → {self._format_weights(self._current_weights)}")

    def _format_weights(self, weights):
        """Format weights for logging."""
        return f"F2={weights[0]:.2f}, F3={weights[1]:.2f}, F4={weights[2]:.2f}, P={weights[3]:.2f}, CE={weights[4]:.2f}"

    def forward(self, inputs, targets):
        """
        Compute weighted loss using current stable weights.

        Args:
            inputs: Raw logits from model (batch_size, num_classes)
            targets: Ground truth class indices (batch_size,)

        Returns:
            Weighted combination of losses
        """
        if inputs.device != targets.device:
            targets = targets.to(inputs.device)

        is_binary = inputs.size(1) == 2

        # Compute individual losses
        focal_g2 = self.focal_loss_g2(inputs, targets)
        focal_g3 = self.focal_loss_g3(inputs, targets)
        focal_g4 = self.focal_loss_g4(inputs, targets)
        ce = self.ce_loss(inputs, targets)

        if is_binary:
            prauc = self.prauc_loss(inputs, targets)
        else:
            prauc = focal_g2

        all_losses = [focal_g2, focal_g3, focal_g4, prauc, ce]

        # Track for logging
        self._last_individual_losses = tuple(l.detach().item() for l in all_losses)

        if self._mode == 'train':
            self._train_total_batches += 1
        else:
            self._val_total_batches += 1

        # Use current stable weights
        weights = torch.tensor(self._current_weights, device=inputs.device, dtype=inputs.dtype)
        self._last_weights = self._current_weights.copy()

        # Weighted combination
        total_loss = (weights[0] * focal_g2 + weights[1] * focal_g3 + weights[2] * focal_g4 +
                      weights[3] * prauc + weights[4] * ce)

        return total_loss

    def get_weight_summary(self) -> str:
        """Get summary of current weights for logging."""
        w = self._current_weights
        summary = f"F2={w[0]:.2f}, F3={w[1]:.2f}, F4={w[2]:.2f}, P={w[3]:.2f}, CE={w[4]:.2f}"

        if self._last_individual_losses is not None:
            losses = self._last_individual_losses
            summary += f" | losses: {losses[0]:.3f}, {losses[1]:.3f}, {losses[2]:.3f}, {losses[3]:.3f}, {losses[4]:.3f}"

        summary += f" | best_auc: {self._best_auc:.4f}"

        return summary

    def reset_win_counts(self):
        """Reset batch counts (call at start of each epoch)."""
        self._train_total_batches = 0
        self._val_total_batches = 0

    def get_weights_dict(self) -> dict:
        """Get current weights as a dictionary for epoch metrics/charting."""
        w = self._current_weights
        result = {
            "adaptive_weight_focal_g2": float(w[0]),
            "adaptive_weight_focal_g3": float(w[1]),
            "adaptive_weight_focal_g4": float(w[2]),
            "adaptive_weight_prauc": float(w[3]),
            "adaptive_weight_ce": float(w[4]),
            "adaptive_best_auc": float(self._best_auc),
        }

        if self._last_individual_losses is not None:
            losses = self._last_individual_losses
            result["adaptive_loss_focal_g2"] = float(losses[0])
            result["adaptive_loss_focal_g3"] = float(losses[1])
            result["adaptive_loss_focal_g4"] = float(losses[2])
            result["adaptive_loss_prauc"] = float(losses[3])
            result["adaptive_loss_ce"] = float(losses[4])

        return result

    def get_gradient_diagnostics(self) -> str:
        """Get AUC-guided info."""
        return f"AUC-guided weights, best_auc={self._best_auc:.4f}, epochs_tracked={len(self._auc_history)}"


class AdaptiveLearningLoss(nn.Module):
    """
    Gradient-based learned loss blending - learns optimal loss weights via backprop.

    Combines FocalLoss (multiple gammas), PRAUCLoss, and CrossEntropyLoss with learnable
    weight_logits that are optimized via gradient descent on the combined loss.

    This approach learns weights that minimize the total loss, naturally favoring
    whichever loss component helps most at each stage of training.

    Usage:
        loss_fn = AdaptiveLearningLoss(alpha=class_weights)
        loss = loss_fn(logits, targets)
        # Weights adapt via gradient descent during training

    Args:
        alpha: Class weights tensor (optional)
        class_counts: Class counts for CostSensitiveFocalLoss (optional)
        initial_weights: Starting weights [f_g2, f_g3, f_g4, prauc, ce] (default: equal)
        temperature: Softmax temperature for weight normalization (default: 1.0)
        focal_min_weight: Minimum weight for focal loss (default: 0.1)
    """

    def __init__(
        self,
        alpha=None,
        class_counts=None,
        initial_weights=None,
        learnable=True,        # unused, kept for API compatibility
        temperature=1.0,
        focal_gamma=2.0,       # unused, kept for API compatibility
        focal_min_weight=0.1
    ):
        super().__init__()
        self.alpha = alpha
        self.class_counts = class_counts
        self.temperature = temperature

        # Initialize individual loss functions
        if class_counts is not None:
            self.focal_loss_g2 = CostSensitiveFocalLoss(class_counts=class_counts, gamma=2.0, min_weight=focal_min_weight)
            self.focal_loss_g3 = CostSensitiveFocalLoss(class_counts=class_counts, gamma=3.0, min_weight=focal_min_weight)
            self.focal_loss_g4 = CostSensitiveFocalLoss(class_counts=class_counts, gamma=4.0, min_weight=focal_min_weight)
        else:
            self.focal_loss_g2 = FocalLoss(alpha=alpha, gamma=2.0, min_weight=focal_min_weight)
            self.focal_loss_g3 = FocalLoss(alpha=alpha, gamma=3.0, min_weight=focal_min_weight)
            self.focal_loss_g4 = FocalLoss(alpha=alpha, gamma=4.0, min_weight=focal_min_weight)
        self.prauc_loss = PRAUCLoss(alpha=alpha)
        self.ce_loss = nn.CrossEntropyLoss(weight=alpha) if alpha is not None else nn.CrossEntropyLoss()

        # Loss names for logging
        self._loss_names = ['F_g2', 'F_g3', 'F_g4', 'PRAUC', 'CE']

        # LEARNABLE WEIGHTS: optimized via gradient descent
        # Initialize with provided weights or equal weights
        if initial_weights is not None:
            init_logits = torch.tensor(initial_weights, dtype=torch.float32)
        else:
            init_logits = torch.zeros(5)  # Equal weights after softmax
        self.weight_logits = nn.Parameter(init_logits)

        # Track epoch progress (set externally)
        self.epoch_progress = 0.0

        # Track running statistics for logging
        self._last_weights = None
        self._last_individual_losses = None
        self._weight_history = []

        # Mode flag: 'train' or 'val'
        self._mode = 'train'

        # Track batch counts for logging
        self._train_total_batches = 0
        self._val_total_batches = 0

    def set_epoch_progress(self, progress: float):
        """Set current epoch progress (0.0 to 1.0) for context."""
        self.epoch_progress = min(1.0, max(0.0, progress))

    def set_mode(self, mode: str):
        """Set mode to 'train' or 'val'."""
        assert mode in ('train', 'val'), f"Mode must be 'train' or 'val', got {mode}"
        self._mode = mode

    def get_current_weights(self):
        """Get current loss weights (for logging)."""
        return self._last_weights

    def forward(self, inputs, targets):
        """
        Compute adaptively weighted loss with learnable weights.

        Args:
            inputs: Raw logits from model (batch_size, num_classes)
            targets: Ground truth class indices (batch_size,)

        Returns:
            Weighted combination of losses
        """
        # Ensure same device
        if inputs.device != targets.device:
            targets = targets.to(inputs.device)

        # Only works for binary classification with PRAUCLoss
        is_binary = inputs.size(1) == 2

        # Compute individual losses
        focal_g2 = self.focal_loss_g2(inputs, targets)
        focal_g3 = self.focal_loss_g3(inputs, targets)
        focal_g4 = self.focal_loss_g4(inputs, targets)
        ce = self.ce_loss(inputs, targets)

        if is_binary:
            prauc = self.prauc_loss(inputs, targets)
        else:
            prauc = focal_g2  # PRAUCLoss only works for binary

        all_losses = [focal_g2, focal_g3, focal_g4, prauc, ce]

        # Track loss values
        loss_vals = [l.detach().item() for l in all_losses]
        self._last_individual_losses = tuple(loss_vals)

        # Track batch counts
        if self._mode == 'train':
            self._train_total_batches += 1
        else:
            self._val_total_batches += 1

        # Compute weights from learnable logits via softmax
        # Ensure weight_logits is on the right device
        logits = self.weight_logits.to(inputs.device)
        weights = F.softmax(logits / self.temperature, dim=0)

        # Store for logging
        self._last_weights = weights.detach().cpu().float().numpy()

        # Weighted combination of all 5 losses
        total_loss = (weights[0] * focal_g2 + weights[1] * focal_g3 + weights[2] * focal_g4 +
                      weights[3] * prauc + weights[4] * ce)

        return total_loss

    def get_weight_summary(self) -> str:
        """Get summary of current weights for logging."""
        if self._last_weights is None:
            return "weights not computed yet"
        w = self._last_weights
        summary = f"F2={w[0]:.2f}, F3={w[1]:.2f}, F4={w[2]:.2f}, P={w[3]:.2f}, CE={w[4]:.2f}"

        if self._last_individual_losses is not None:
            losses = self._last_individual_losses
            summary += f" | losses: {losses[0]:.3f}, {losses[1]:.3f}, {losses[2]:.3f}, {losses[3]:.3f}, {losses[4]:.3f}"

        # Show logits (learnable parameters)
        logits = self.weight_logits.detach().cpu().numpy()
        summary += f" | logits: {logits[0]:.2f}, {logits[1]:.2f}, {logits[2]:.2f}, {logits[3]:.2f}, {logits[4]:.2f}"

        return summary

    def reset_win_counts(self):
        """Reset batch counts (call at start of each epoch). No win counts in this version."""
        self._train_total_batches = 0
        self._val_total_batches = 0

    def get_weights_dict(self) -> dict:
        """Get current weights as a dictionary for epoch metrics/charting."""
        result = {}

        # Current blending weights
        if self._last_weights is not None:
            w = self._last_weights
            result["adaptive_weight_focal_g2"] = float(w[0])
            result["adaptive_weight_focal_g3"] = float(w[1])
            result["adaptive_weight_focal_g4"] = float(w[2])
            result["adaptive_weight_prauc"] = float(w[3])
            result["adaptive_weight_ce"] = float(w[4])

        # Individual loss values (last batch)
        if self._last_individual_losses is not None:
            losses = self._last_individual_losses
            result["adaptive_loss_focal_g2"] = float(losses[0])
            result["adaptive_loss_focal_g3"] = float(losses[1])
            result["adaptive_loss_focal_g4"] = float(losses[2])
            result["adaptive_loss_prauc"] = float(losses[3])
            result["adaptive_loss_ce"] = float(losses[4])

        # Logits (learnable parameters)
        logits = self.weight_logits.detach().cpu().numpy()
        result["adaptive_logit_focal_g2"] = float(logits[0])
        result["adaptive_logit_focal_g3"] = float(logits[1])
        result["adaptive_logit_focal_g4"] = float(logits[2])
        result["adaptive_logit_prauc"] = float(logits[3])
        result["adaptive_logit_ce"] = float(logits[4])

        return result

    def get_gradient_diagnostics(self) -> str:
        """Get gradient info for learnable weights."""
        if self.weight_logits.grad is not None:
            grad = self.weight_logits.grad.cpu().numpy()
            grad_str = f"grad: [{grad[0]:.4f}, {grad[1]:.4f}, {grad[2]:.4f}, {grad[3]:.4f}, {grad[4]:.4f}]"
        else:
            grad_str = "grad: None"
        return f"learnable weights, {self._train_total_batches} train batches, {grad_str}"


# Alias for backward compatibility - points to the voting version by default
AdaptiveLoss = AdaptiveVotingLoss


class SetEncoder(nn.Module):
    def __init__(self, config: SetEncoderConfig, string_cache=None, member_names=None, column_name=None):
        super().__init__()
        self.config = config
        self.string_cache = string_cache
        # Store cache filename for reconnection after unpickling
        if string_cache is not None and hasattr(string_cache, 'filename'):
            self._string_cache_filename = string_cache.filename
        else:
            self._string_cache_filename = None
        self.member_names = member_names or []
        self.column_name = column_name  # NEW: column name for semantic initialization
        
        # Build name-to-index mapping for OOV handling
        self.name_to_idx = {str(name): idx for idx, name in enumerate(self.member_names)} if self.member_names else {}

        # Check init style from config
        from featrix.neural.sphere_config import get_config
        use_hypersphere = get_config().use_hypersphere_init()

        if use_hypersphere:
            # HYPERSPHERE INITIALIZATION (new - may hurt AUC)
            # Initialize embeddings as random unit vectors to cover the sphere uniformly.
            self._replacement_embedding = nn.Parameter(torch.randn(config.d_model))
            self._replacement_embedding.data = self._replacement_embedding.data / self._replacement_embedding.data.norm()

            self.embedding = nn.Embedding(config.n_members, config.d_model)
            with torch.no_grad():
                self.embedding.weight.normal_()
                self.embedding.weight.div_(self.embedding.weight.norm(dim=1, keepdim=True))
        else:
            # XAVIER INITIALIZATION (old/good - 0.7 AUC commits used this)
            self._replacement_embedding = nn.Parameter(torch.zeros(config.d_model))
            nn.init.xavier_uniform_(self._replacement_embedding.unsqueeze(0))
            self._replacement_embedding.data = self._replacement_embedding.data.squeeze(0)

            self.embedding = nn.Embedding(config.n_members, config.d_model)
            nn.init.xavier_uniform_(self.embedding.weight)
        
        # ADAPTIVE MIXTURE: Enable semantic embeddings if available
        # We'll create a learnable mixture between learned embeddings and BERT semantics
        # ALWAYS enable if we have string_cache and member_names (make all SetEncoders adaptive)
        from featrix.neural.sphere_config import get_config
        # Enable semantic mixture if we have the prerequisites (string_cache and member_names)
        # The config flag can disable it, but by default we try to enable it
        config_enabled = get_config().use_semantic_set_initialization()
        self.use_semantic_mixture = (config_enabled and 
                                      string_cache is not None and 
                                      member_names and
                                      len(member_names) > 0)
        
        if self.use_semantic_mixture:
            col_prefix = f"[{column_name}] " if column_name else ""
            
            # Create projection layer for BERT embeddings
            # Init style depends on use_hypersphere_init flag
            self.bert_projection = nn.Linear(STRING_DIM, config.d_model, bias=False)
            if get_config().use_hypersphere_init():
                # HYPERSPHERE: orthogonal + unit norm rows for sphere coverage (new)
                nn.init.orthogonal_(self.bert_projection.weight)
                with torch.no_grad():
                    self.bert_projection.weight.div_(self.bert_projection.weight.norm(dim=1, keepdim=True))
            else:
                # XAVIER: standard init (old/good - 0.7 AUC commits)
                nn.init.xavier_uniform_(self.bert_projection.weight)
            
            # Pre-compute BERT embeddings for all known members
            self.bert_embeddings = self._precompute_bert_embeddings()
            
            # ============================================================================
            # MIXTURE WEIGHTS: Gating network, per-member, or global
            # ============================================================================
            # GATING NETWORK (preferred): Small MLP that looks at learned and semantic
            # embeddings and decides the mixture weight dynamically per-sample.
            # This is more principled than per-member logits because:
            # 1. No per-member parameters (avoids overfitting)
            # 2. Gate is conditioned on actual embedding values, not just member index
            # 3. Gradients flow naturally (no zero-gradient from learned==semantic init)
            use_gating_network = getattr(config, 'use_gating_network', True)
            use_per_member = getattr(config, 'use_per_member_mixture', False)  # Deprecated, use gating
            
            self.use_gating_network = use_gating_network
            self.use_per_member_mixture = use_per_member and not use_gating_network and len(member_names) > 0
            
            # Initialize mixture logit for fallback / logging
            if config.initial_mixture_logit is not None:
                initial_logit = config.initial_mixture_logit
            else:
                initial_logit = 0.5  # Slight learned bias (~62% LRN / 38% SEM)

            if self.use_gating_network:
                # GATING NETWORK: MLP that takes [learned, semantic] and outputs gate
                # Input: 2 * d_model (concatenated learned + semantic)
                # Hidden: small to avoid overfitting (min of d_model//4 or 32)
                # Output: 1 (gate value, pre-sigmoid)
                gate_hidden = min(config.d_model // 4, 32)
                self.mixture_gate = nn.Sequential(
                    nn.Linear(2 * config.d_model, gate_hidden),
                    nn.ReLU(),
                    nn.Linear(gate_hidden, 1)
                )
                # Initialize with slight learned bias - learned embeddings become crisper/more
                # discriminative than frozen BERT embeddings as they train end-to-end
                with torch.no_grad():
                    # Set final layer bias to produce ~62% learned / 38% semantic at init
                    self.mixture_gate[-1].bias.fill_(initial_logit)
                    # Small weights for stable initial behavior
                    for layer in self.mixture_gate:
                        if isinstance(layer, nn.Linear):
                            nn.init.xavier_uniform_(layer.weight, gain=0.5)
                
                self.mixture_logit = None  # Not used with gating network
                self.mixture_logits = None
                logger.info(f"{col_prefix}GATING NETWORK: 2*{config.d_model} → {gate_hidden} → 1")
                
            elif self.use_per_member_mixture:
                # DEPRECATED: Per-member logits (kept for backward compatibility)
                base_logits = torch.full((config.n_members,), initial_logit, dtype=torch.float32)
                logit_noise = torch.randn(config.n_members) * 0.1
                self.mixture_logits = nn.Parameter(base_logits + logit_noise)
                self.mixture_logit = nn.Parameter(torch.tensor([initial_logit], dtype=torch.float32))
                self.mixture_gate = None
            else:
                # Global mixture weight (simplest option)
                self.mixture_logit = nn.Parameter(torch.tensor([initial_logit], dtype=torch.float32))
                self.mixture_logits = None
                self.mixture_gate = None
            
            # ============================================================================
            # ORDINAL ENCODING: Add positional embeddings for ordered categories
            # ============================================================================
            ordinal_info = getattr(config, 'ordinal_info', None)
            self.is_ordinal = ordinal_info is not None and ordinal_info.get('is_ordinal', False)
            self.ordinal_weight = getattr(config, 'ordinal_weight', 0.3)
            
            if self.is_ordinal:
                ordered_values = ordinal_info.get('ordered_values') or []
                if not ordered_values:
                    # Ordinal detection said is_ordinal=True but didn't provide ordered_values
                    # This is a bug in ordinal detection - log warning and disable ordinal encoding
                    logger.warning(f"{col_prefix}ORDINAL: is_ordinal=True but ordered_values is empty/None - disabling ordinal encoding")
                    self.is_ordinal = False
                    self.ordinal_embedding = None
                # Build ordinal position mapping: category_idx → ordinal_position (0 to n-1)
                ordinal_positions = {}
                for pos, val in enumerate(ordered_values):
                    # Map value to its index in member_names
                    if val in self.name_to_idx:
                        member_idx = self.name_to_idx[val]
                        ordinal_positions[member_idx] = pos
                
                # Create ordinal position embedding
                n_ordinal = len(ordered_values)
                if n_ordinal > 0:
                    # Small positional embedding that captures order
                    self.ordinal_embedding = nn.Embedding(n_ordinal, config.d_model)
                    # Initialize with smooth gradient (earlier positions → one direction, later → other)
                    with torch.no_grad():
                        for i in range(n_ordinal):
                            # Normalized position from -1 to 1
                            norm_pos = 2.0 * i / max(1, n_ordinal - 1) - 1.0
                            # Create smooth positional pattern
                            pos_pattern = torch.zeros(config.d_model)
                            for dim in range(config.d_model):
                                # Mix of sin/cos at different frequencies
                                freq = (dim + 1) / config.d_model * 3.14159
                                pos_pattern[dim] = norm_pos * (0.5 + 0.5 * torch.sin(torch.tensor(freq * i)).item())
                            self.ordinal_embedding.weight[i] = pos_pattern * 0.1  # Small magnitude
                    
                    # Store position mapping as buffer (non-trainable)
                    ordinal_pos_tensor = torch.zeros(config.n_members, dtype=torch.long)
                    for member_idx, ord_pos in ordinal_positions.items():
                        ordinal_pos_tensor[member_idx] = ord_pos
                    self.register_buffer('_ordinal_positions', ordinal_pos_tensor)
                    self.register_buffer('_has_ordinal_position', 
                                        torch.tensor([1 if i in ordinal_positions else 0 
                                                     for i in range(config.n_members)], dtype=torch.bool))
                    
                    logger.info(f"{col_prefix}ORDINAL: {n_ordinal} ordered values, weight={self.ordinal_weight:.2f}")
                else:
                    self.ordinal_embedding = None
                    self.is_ordinal = False
            else:
                self.ordinal_embedding = None
            
            # ============================================================================
            # CURRICULUM LEARNING & TEMPERATURE ANNEALING
            # ============================================================================
            # CURRICULUM LEARNING: Disabled by default - was over-constraining mixture learning
            # The semantic floor was preventing the model from learning when to use learned embeddings
            # because it clamped mixture weights, which crushed gradients through the chain rule
            self.use_curriculum_learning = getattr(config, 'use_curriculum_learning', False)
            self.semantic_floor_start = getattr(config, 'semantic_floor_start', 0.5)  # Reduced from 0.7
            self.semantic_floor_end = getattr(config, 'semantic_floor_end', 0.0)  # Allow full learned if model wants
            
            # TEMPERATURE ANNEALING: End at 0.5 instead of 0.2 to prevent gradient crushing
            # At temp=0.2, sigmoid is in saturation zone with near-zero gradients
            # At temp=0.5, we still get sharpening but maintain healthy gradient flow
            self.use_temperature_annealing = getattr(config, 'use_temperature_annealing', True)
            self.temperature_start = getattr(config, 'temperature_start', 1.0)
            self.temperature_end = getattr(config, 'temperature_end', 0.5)  # Was 0.2 - too aggressive
            
            # Entropy regularization weight (configurable)
            self.entropy_reg_weight = getattr(config, 'entropy_regularization_weight', 0.3)
            
            # Epoch tracking for curriculum/annealing (updated by EmbeddingSpace during training)
            self.register_buffer('_epoch_counter', torch.tensor(0, dtype=torch.long))
            self.register_buffer('_total_epochs', torch.tensor(100, dtype=torch.long))  # Will be updated
            self.register_buffer('_last_logged_epoch', torch.tensor(-1, dtype=torch.long))  # Track last logged epoch to avoid batch spam
            
            # ============================================================================
            # LEARNED EMBEDDING INITIALIZATION
            # ============================================================================
            # Strategy: Initialize learned embeddings DIFFERENTLY from BERT so the gating
            # network has two genuinely different options to choose from.
            #
            # - ORDINAL columns: Place embeddings along a line in embedding space,
            #   encoding the semantic order that BERT doesn't capture.
            # - NON-ORDINAL columns: Keep hypersphere initialization (already done above).
            #
            # BERT embeddings are still precomputed for OOV handling at inference.

            if self.is_ordinal and ordinal_info:
                init_method = self._init_ordinal_line(ordinal_info)
            else:
                init_method = "hypersphere"  # Keep hypersphere init from embedding creation

            # Summary log
            features = []
            if self.use_per_member_mixture:
                features.append("per-member-mix")
            if self.is_ordinal:
                features.append("ordinal")
            if self.use_curriculum_learning:
                features.append("curriculum")
            if self.use_temperature_annealing:
                features.append("temp-anneal")
            features_str = ", ".join(features) if features else "basic"

            logger.info(f"{col_prefix}ADAPTIVE: {len(self.bert_embeddings)} BERT embeddings, init={init_method}, logit={initial_logit:.2f} [{features_str}]")
        else:
            self.bert_projection = None
            self.bert_embeddings = None
            self.mixture_logit = None
            self.mixture_logits = None
            self.use_per_member_mixture = False
            self.is_ordinal = False
            self.ordinal_embedding = None
            self.ordinal_weight = 0.0
            self.use_curriculum_learning = False
            self.use_temperature_annealing = False
            self.entropy_reg_weight = 0.1
            self.semantic_floor_start = 0.0
            self.semantic_floor_end = 0.0
            self.temperature_start = 1.0
            self.temperature_end = 1.0
            
            # Legacy path: one-time semantic initialization without mixture
            if get_config().use_semantic_set_initialization() and string_cache is not None and member_names:
                logger.info(f"🎨 Legacy: One-time semantic initialization (no adaptive mixture)")
                initialized = self._init_from_string_cache()
                logger.info(f"   ✅ Initialized {initialized}/{len(member_names)} set embeddings semantically")
                
                # Create projection for OOV handling at inference only
                self.bert_projection = nn.Linear(STRING_DIM, config.d_model, bias=False)
                nn.init.xavier_uniform_(self.bert_projection.weight, gain=0.5)
        
        # SPARSITY-AWARE GRADIENT SCALING
        if config.sparsity_ratio > 0.01:
            min_scale = 0.1
            gradient_scale = max(1.0 - config.sparsity_ratio, min_scale)
            
            def _scale_replacement_grad(grad):
                """Scale gradient to compensate for frequency imbalance"""
                return grad * gradient_scale
            
            self._replacement_embedding.register_hook(_scale_replacement_grad)
            
            logger.info(
                f"⚖️  Sparsity-aware gradient scaling ENABLED: "
                f"sparsity={config.sparsity_ratio:.1%}, "
                f"gradient_scale={gradient_scale:.2f}"
            )
    
    def get_actual_mixture_weight(self) -> tuple:
        """
        Get the ACTUAL mixture weight being used in forward pass (with temperature and curriculum).
        
        Returns:
            Tuple of (learned_weight, semantic_weight, raw_logit, temperature, epoch_progress)
            where learned_weight + semantic_weight = 1.0
            
        This is for accurate logging - the raw sigmoid(mixture_logit) does NOT reflect
        the actual weights used because:
        1. Temperature annealing scales the logit before sigmoid
        2. Curriculum learning clamps the mixture weight by max_learned
        
        For gating network mode, raw_logit is the last observed mean gate value.
        """
        # For gating network, we track the last mean weight in forward pass
        if self.use_gating_network:
            # Use last observed mean weight (updated in forward pass)
            if hasattr(self, '_last_gate_mean'):
                learned_weight = self._last_gate_mean
            else:
                learned_weight = 0.38  # Default before first forward
            semantic_weight = 1.0 - learned_weight
            
            # Get epoch info
            current_epoch = self._epoch_counter.item()
            total_epochs = max(1, self._total_epochs.item())
            epoch_progress = current_epoch / total_epochs
            
            if self.use_temperature_annealing:
                temperature = self.temperature_start + (self.temperature_end - self.temperature_start) * epoch_progress
            else:
                temperature = 1.0
            
            return (learned_weight, semantic_weight, 0.0, temperature, epoch_progress)
        
        if not self.use_semantic_mixture or self.mixture_logit is None:
            return (1.0, 0.0, 0.0, 1.0, 0.0)  # 100% learned, no semantic
        
        # Get epoch progress
        current_epoch = self._epoch_counter.item()
        total_epochs = max(1, self._total_epochs.item())
        epoch_progress = current_epoch / total_epochs
        
        # Compute temperature (same as forward pass)
        if self.use_temperature_annealing:
            temperature = self.temperature_start + (self.temperature_end - self.temperature_start) * epoch_progress
            temperature = max(0.1, temperature)
        else:
            temperature = 1.0
        
        # Get raw logit (use mean of per-member if available)
        if self.use_per_member_mixture and self.mixture_logits is not None:
            raw_logit = self.mixture_logits.mean().item()
        else:
            raw_logit = self.mixture_logit.item()
        
        # Compute raw weight with temperature scaling (same as forward pass)
        import math
        raw_weight = 1.0 / (1.0 + math.exp(-raw_logit / temperature))  # sigmoid with temp
        
        # Apply curriculum learning if enabled (same as forward pass)
        if self.use_curriculum_learning:
            semantic_floor = self.semantic_floor_start + \
                            (self.semantic_floor_end - self.semantic_floor_start) * epoch_progress
            max_learned = 1.0 - semantic_floor
            learned_weight = raw_weight * max_learned
        else:
            learned_weight = raw_weight
        
        semantic_weight = 1.0 - learned_weight
        
        return (learned_weight, semantic_weight, raw_logit, temperature, epoch_progress)

    def _precompute_bert_embeddings(self):
        """Pre-compute and cache BERT embeddings for all known members (BATCHED for speed)"""
        if not self.string_cache or not self.member_names:
            return {}
        
        bert_cache = {}
        
        # BATCH ENCODE: Use batch method if available (much faster)
        if hasattr(self.string_cache, 'get_embeddings_batch'):
            member_strings = [str(m) for m in self.member_names]
            embeddings = self.string_cache.get_embeddings_batch(member_strings)
            
            nan_count = 0
            inf_count = 0
            for idx, bert_emb in enumerate(embeddings):
                if bert_emb is not None:
                    with torch.no_grad():
                        if isinstance(bert_emb, torch.Tensor):
                            bert_tensor = bert_emb.detach().clone().to(dtype=torch.float32, device=self._replacement_embedding.device)
                        else:
                            bert_tensor = torch.tensor(bert_emb, dtype=torch.float32, device=self._replacement_embedding.device)

                        # Check for NaN/Inf in raw BERT embedding from server
                        if torch.isnan(bert_tensor).any():
                            nan_count += 1
                            continue  # Skip this embedding
                        if torch.isinf(bert_tensor).any():
                            inf_count += 1
                            continue  # Skip this embedding

                        projected = self.bert_projection(bert_tensor.unsqueeze(0))

                        # Check for NaN/Inf after projection
                        if torch.isnan(projected).any() or torch.isinf(projected).any():
                            logger.warning(f"[{self.column_name}] BERT projection produced NaN/Inf for member idx={idx}")
                            continue  # Skip this embedding

                        bert_cache[idx] = projected.squeeze(0)

            if nan_count > 0 or inf_count > 0:
                logger.error(f"💥 [{self.column_name}] _precompute_bert_embeddings: {nan_count} NaN, {inf_count} Inf in raw BERT embeddings from server")
        else:
            # Fallback: batch encode all member names at once
            member_strings = [str(m) for m in self.member_names]
            if hasattr(self.string_cache, 'get_embeddings_batch'):
                # Use batch encoding - much faster!
                bert_embeddings = self.string_cache.get_embeddings_batch(member_strings)
                for idx, bert_emb in enumerate(bert_embeddings):
                    if bert_emb is not None:
                        with torch.no_grad():
                            if isinstance(bert_emb, torch.Tensor):
                                bert_tensor = bert_emb.detach().clone().to(dtype=torch.float32, device=self._replacement_embedding.device)
                            else:
                                bert_tensor = torch.tensor(bert_emb, dtype=torch.float32, device=self._replacement_embedding.device)
                            projected = self.bert_projection(bert_tensor.unsqueeze(0))
                            bert_cache[idx] = projected.squeeze(0)
            else:
                # Old StringCache - one-at-a-time (slower but works)
                for idx, member_name in enumerate(self.member_names):
                    bert_emb = self.string_cache.get_embedding_from_cache(str(member_name))
                    if bert_emb is not None:
                        with torch.no_grad():
                            if isinstance(bert_emb, torch.Tensor):
                                bert_tensor = bert_emb.detach().clone().to(dtype=torch.float32, device=self._replacement_embedding.device)
                            else:
                                bert_tensor = torch.tensor(bert_emb, dtype=torch.float32, device=self._replacement_embedding.device)
                            projected = self.bert_projection(bert_tensor.unsqueeze(0))
                            bert_cache[idx] = projected.squeeze(0)
        
        return bert_cache
    
    def _init_from_bert(self):
        """Warm-start learned embeddings with BERT vectors (for adaptive mixture)"""
        if not self.bert_embeddings:
            return 0

        initialized_count = 0
        for idx, bert_embedding in self.bert_embeddings.items():
            with torch.no_grad():
                self.embedding.weight[idx] = bert_embedding.clone()
            initialized_count += 1

        return initialized_count

    def _init_ordinal_line(self, ordinal_info: dict) -> str:
        """
        Initialize learned embeddings along a line for ordinal columns.

        Places embeddings from "low" to "high" along a random direction in embedding space.
        This gives learned embeddings an advantage over semantic BERT embeddings -
        they encode the ordering explicitly from the start, which BERT doesn't capture.

        Args:
            ordinal_info: Dict with 'ordered_values' list in semantic order (low to high)

        Returns:
            Initialization method string for logging ("ordinal-line" or "xavier")
        """
        if not ordinal_info:
            return "xavier"

        ordered_values = ordinal_info.get('ordered_values') or []
        if len(ordered_values) < 2:
            return "xavier"

        d_model = self.embedding.weight.shape[1]

        with torch.no_grad():
            # Generate random direction for the ordinal line
            # Use two endpoints to create a line from "low" to "high"
            direction = torch.randn(d_model)
            direction = direction / direction.norm()  # Unit vector

            # Scale: embeddings will range from -0.5 to +0.5 along this direction
            # Plus small perpendicular noise for each embedding
            n_ordered = len(ordered_values)
            initialized = 0

            for i, val in enumerate(ordered_values):
                if val in self.name_to_idx:
                    member_idx = self.name_to_idx[val]
                    # Position along line: -0.5 (lowest) to +0.5 (highest)
                    t = i / max(1, n_ordered - 1)  # 0.0 to 1.0
                    position = (t - 0.5) * 1.0  # -0.5 to +0.5

                    # Main component: position along ordinal direction
                    embedding = position * direction

                    # Add small orthogonal noise to break symmetry
                    noise = torch.randn(d_model) * 0.05
                    # Remove component parallel to direction
                    noise = noise - (noise @ direction) * direction
                    embedding = embedding + noise

                    self.embedding.weight[member_idx] = embedding
                    initialized += 1

            if initialized > 0:
                logger.info(f"[{self.column_name}] ORDINAL INIT: {initialized}/{n_ordered} values placed along line")
                return "ordinal-line"

        return "xavier"

    def _init_from_column_and_values(self, column_name, member_names):
        """
        Initialize embeddings using BERT(column_name) + BERT(value).
        
        This gives each embedding TWO pieces of context:
        1. What column it belongs to (e.g., "business_type")
        2. What value it represents (e.g., "Auto Transport")
        
        Result: "yes" in "is_active" is different from "yes" in "approved" 
        because the column context differs.
        """
        if not self.string_cache or not member_names:
            return 0
        
        # Get column name embedding once (reused for all members)
        column_emb = None
        if column_name:
            column_emb = self.string_cache.get_embedding_from_cache(str(column_name))
        
        # Create MLP to project concatenated embeddings → d_model
        string_dim = STRING_DIM
        # Input is column_emb + value_emb (concatenated)
        input_dim = string_dim * 2 if column_emb is not None else string_dim
        hidden_dim = max(64, self.config.d_model // 2)
        
        temp_mlp = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, self.config.d_model)
        )
        
        # Initialize MLP weights
        for layer in temp_mlp:
            if isinstance(layer, nn.Linear):
                nn.init.xavier_uniform_(layer.weight, gain=0.5)
                if hasattr(layer, 'bias') and layer.bias is not None:
                    nn.init.zeros_(layer.bias)
        
        # Move temp_mlp to same device as embedding
        device = self.embedding.weight.device
        temp_mlp.to(device)
        
        column_tensor = None
        if column_emb is not None:
            # Keep on CPU for DataLoader workers
            # Use clone().detach() if tensor, from_numpy() if numpy array
            if isinstance(column_emb, torch.Tensor):
                column_tensor = column_emb.clone().detach().to(torch.float32)
            else:
                column_tensor = torch.from_numpy(column_emb).to(torch.float32)
        
        # BATCH ENCODE: Get all value embeddings at once
        if hasattr(self.string_cache, 'get_embeddings_batch'):
            member_strings = [str(m) for m in member_names]
            value_embeddings = self.string_cache.get_embeddings_batch(member_strings)
        else:
            # Fallback: one-at-a-time
            value_embeddings = [self.string_cache.get_embedding_from_cache(str(m)) for m in member_names]
        
        initialized_count = 0
        for idx, value_emb in enumerate(value_embeddings):
            if value_emb is not None:
                # Keep on CPU for DataLoader workers
                # Use clone().detach() if tensor, from_numpy() if numpy array
                if isinstance(value_emb, torch.Tensor):
                    value_tensor = value_emb.clone().detach().to(torch.float32)
                else:
                    value_tensor = torch.from_numpy(value_emb).to(torch.float32)
                
                # Concatenate column + value embeddings
                if column_tensor is not None:
                    combined = torch.cat([column_tensor, value_tensor]).unsqueeze(0)
                else:
                    combined = value_tensor.unsqueeze(0)
                
                # Move to device and project through MLP to d_model
                with torch.no_grad():
                    combined = combined.to(device)
                    projected = temp_mlp(combined)
                    self.embedding.weight[idx] = projected.squeeze(0)
                
                initialized_count += 1
        
        return initialized_count

    @property
    def unknown_embedding(self):
        # FIXME: what was the rationale for unknown embeddings again?
        return nn.functional.normalize(self._replacement_embedding, dim=-1)

    @property
    def marginal_embedding(self):
        # We return the same vector as NOT_PRESENT token because they are treated the
        # same from a probabilistic point of view by the network, and should be treated
        # the same when the model is queried.
        # However, they must remain distinct tokens because the masking strategy for the loss
        # function is affected by whether a field is NOT_PRESENT, or MARGINAL.
        return nn.functional.normalize(self._replacement_embedding, dim=-1)

    @property
    def not_present_embedding(self):
        return nn.functional.normalize(self._replacement_embedding, dim=-1)

    def forward(self, token, return_strategy_encodings: bool = False):
        """
        Encode set token batch into embeddings.

        Args:
            token: TokenBatch with value as member indices [batch_size]
            return_strategy_encodings: If True, also return component encodings
                                       for strategy-aware relationship ops

        Returns:
            If return_strategy_encodings is False:
                (short_vec, full_vec) tuple of embeddings
            If return_strategy_encodings is True:
                (short_vec, full_vec, all_strategy_encodings) where
                all_strategy_encodings is (batch, n_components, d_model)
                Components are: [learned, semantic, ordinal] (ordinal only if enabled)
        """
        # EMERGENCY FIX: Convert float to long for embedding layer
        value = token.value
        if value.dtype == torch.float32:
            value = value.long()
        
        # CRITICAL: Ensure value is on the same device as module parameters
        # Respect FEATRIX_FORCE_CPU_SINGLE_PREDICTOR env var - force CPU if set
        force_cpu = os.environ.get('FEATRIX_FORCE_CPU_SINGLE_PREDICTOR') == '1'
        
        # Get device from embedding layer
        module_device = None
        if not force_cpu:
            try:
                module_device = next(self.embedding.parameters()).device
            except (StopIteration, AttributeError):
                pass
        
        # Force CPU mode if env var is set
        if force_cpu:
            module_device = torch.device('cpu')
            if list(self.parameters()):
                first_param_device = next(self.parameters()).device
                if first_param_device.type != 'cpu':
                    self.cpu()
        
        # Move value to module device if there's a mismatch
        if module_device is not None and value.device != module_device:
            value = value.to(device=module_device)
        
        # Create new token with modified value (Token.value is read-only)
        token = Token(
            value=value,
            status=token.status,
            attention_mask=token.attention_mask if hasattr(token, 'attention_mask') else None
        )
        
        # CRITICAL FIX: Clamp token values to valid range BEFORE embedding lookup
        # This prevents out-of-bounds errors when NOT_PRESENT tokens have value=0
        # but the embedding table doesn't include index 0
        max_valid_idx = self.embedding.num_embeddings - 1
        safe_value = torch.clamp(token.value, 0, max_valid_idx)
        
        # Get learned embeddings (use safe_value to avoid out-of-bounds)
        learned_embed = self.embedding(safe_value)  # [batch_size, d_model]

        # NaN DIAGNOSTIC: Check learned embedding immediately (first batch of each epoch)
        if self.training:
            diag_key = '_nan_check_learned_epoch'
            current_epoch = self._epoch_counter.item() if hasattr(self, '_epoch_counter') else 0
            if not hasattr(self, diag_key) or getattr(self, diag_key) != current_epoch:
                setattr(self, diag_key, current_epoch)
                has_nan = torch.isnan(learned_embed).any().item()
                has_inf = torch.isinf(learned_embed).any().item()
                if has_nan or has_inf:
                    col_name = self.column_name or 'unknown'
                    logger.error(f"💥 NaN/Inf in learned_embed [{col_name}] epoch={current_epoch}: NaN={has_nan}, Inf={has_inf}")
                    # Check embedding weights
                    has_nan_weights = torch.isnan(self.embedding.weight).any().item()
                    has_inf_weights = torch.isinf(self.embedding.weight).any().item()
                    logger.error(f"   embedding.weight: NaN={has_nan_weights}, Inf={has_inf_weights}")
                    # Check safe_value
                    logger.error(f"   safe_value: min={safe_value.min().item()}, max={safe_value.max().item()}, dtype={safe_value.dtype}")

        # ADAPTIVE MIXTURE: Mix learned and semantic embeddings if enabled
        if self.use_semantic_mixture and self.bert_embeddings:
            # Get BERT embeddings for this batch
            batch_size = token.value.shape[0]
            bert_embed = torch.zeros_like(learned_embed)  # [batch_size, d_model]
            
            # Track BERT coverage for logging
            bert_available_count = 0
            bert_nan_count = 0
            for batch_idx in range(batch_size):
                member_idx = token.value[batch_idx].item()
                if member_idx in self.bert_embeddings:
                    bert_emb_val = self.bert_embeddings[member_idx]
                    # Check for NaN in cached BERT embedding
                    if torch.isnan(bert_emb_val).any() or torch.isinf(bert_emb_val).any():
                        bert_nan_count += 1
                        # Use learned embedding as fallback for NaN BERT
                        bert_embed[batch_idx] = learned_embed[batch_idx].detach()
                    else:
                        bert_embed[batch_idx] = bert_emb_val
                        bert_available_count += 1
                else:
                    # If BERT embedding not available, use learned embedding
                    bert_embed[batch_idx] = learned_embed[batch_idx].detach()

            # Log NaN BERT embeddings (first batch only)
            if bert_nan_count > 0 and not hasattr(self, '_bert_nan_logged'):
                self._bert_nan_logged = True
                col_name = self.column_name or 'unknown'
                logger.error(f"💥 Found {bert_nan_count}/{batch_size} NaN/Inf in cached BERT embeddings [{col_name}]")
            
            # ============================================================================
            # COMPUTE MIXTURE WEIGHTS (gating network, per-member, or global)
            # ============================================================================
            current_epoch = self._epoch_counter.item()
            total_epochs = max(1, self._total_epochs.item())
            epoch_progress = current_epoch / total_epochs  # 0.0 to 1.0
            
            # TEMPERATURE ANNEALING: Start soft, end sharp
            if self.use_temperature_annealing:
                temperature = self.temperature_start + (self.temperature_end - self.temperature_start) * epoch_progress
                temperature = max(0.1, temperature)  # Avoid division issues
            else:
                temperature = 1.0
            
            # Compute mixture weights using chosen strategy
            if self.use_gating_network and self.mixture_gate is not None:
                # GATING NETWORK: MLP looks at both embeddings and decides the gate
                # This is more principled than per-member logits because:
                # 1. Gate is conditioned on actual embedding VALUES
                # 2. Gradients flow naturally (learned != semantic by construction)
                # 3. No per-member parameters (less overfitting)
                gate_input = torch.cat([learned_embed, bert_embed], dim=-1)  # [batch, 2*d_model]
                gate_logit = self.mixture_gate(gate_input).squeeze(-1)  # [batch]
                
                # Apply temperature scaling
                raw_weights = torch.sigmoid(gate_logit / temperature)  # [batch]
                
                # CURRICULUM LEARNING: Enforce minimum semantic weight early in training
                if self.use_curriculum_learning:
                    semantic_floor = self.semantic_floor_start + \
                                    (self.semantic_floor_end - self.semantic_floor_start) * epoch_progress
                    max_learned = 1.0 - semantic_floor
                    mixture_weights = raw_weights * max_learned  # [batch]
                else:
                    mixture_weights = raw_weights
                
                # Expand for broadcasting
                mixture_weights_expanded = mixture_weights.unsqueeze(1)  # [batch, 1]
                
                # Mix embeddings
                embed = mixture_weights_expanded * learned_embed + (1 - mixture_weights_expanded) * bert_embed
                
                # Summary stats for logging
                mean_weight = mixture_weights.mean().item()
                learned_pct = mean_weight * 100
                semantic_pct = (1 - mean_weight) * 100
                
                # Track for get_actual_mixture_weight() logging
                self._last_gate_mean = mean_weight
                
            elif self.use_per_member_mixture and self.mixture_logits is not None:
                # DEPRECATED: Per-member logits
                member_indices = safe_value  # [batch_size]
                batch_logits = self.mixture_logits[member_indices]  # [batch_size]
                
                # Apply temperature scaling
                raw_weights = torch.sigmoid(batch_logits / temperature)  # [batch_size]
                
                # CURRICULUM LEARNING
                if self.use_curriculum_learning:
                    semantic_floor = self.semantic_floor_start + \
                                    (self.semantic_floor_end - self.semantic_floor_start) * epoch_progress
                    max_learned = 1.0 - semantic_floor
                    mixture_weights = raw_weights * max_learned  # [batch_size]
                else:
                    mixture_weights = raw_weights
                
                mixture_weights_expanded = mixture_weights.unsqueeze(1)  # [batch_size, 1]
                embed = mixture_weights_expanded * learned_embed + (1 - mixture_weights_expanded) * bert_embed
                
                mean_weight = mixture_weights.mean().item()
                learned_pct = mean_weight * 100
                semantic_pct = (1 - mean_weight) * 100
                
                # Update global mixture_logit for logging
                with torch.no_grad():
                    self.mixture_logit.fill_(self.mixture_logits.mean().item())
            else:
                # GLOBAL MIXTURE: Single weight for all categories (simplest)
                raw_weight = torch.sigmoid(self.mixture_logit / temperature)
                
                # CURRICULUM LEARNING
                if self.use_curriculum_learning:
                    semantic_floor = self.semantic_floor_start + \
                                    (self.semantic_floor_end - self.semantic_floor_start) * epoch_progress
                    max_learned = 1.0 - semantic_floor
                    mixture_weight = raw_weight * max_learned
                else:
                    mixture_weight = raw_weight
                
                learned_pct = mixture_weight.item() * 100
                semantic_pct = (1 - mixture_weight.item()) * 100
                
                embed = mixture_weight * learned_embed + (1 - mixture_weight) * bert_embed
                mixture_weights = mixture_weight  # For entropy calc
            
            # ============================================================================
            # ORDINAL ENCODING: Add positional information for ordered categories
            # ============================================================================
            if self.is_ordinal and self.ordinal_embedding is not None:
                # Get ordinal positions for this batch
                ordinal_positions = self._ordinal_positions[safe_value]  # [batch_size]
                has_ordinal = self._has_ordinal_position[safe_value]  # [batch_size]
                
                # Get ordinal embeddings
                ordinal_embed = self.ordinal_embedding(ordinal_positions)  # [batch_size, d_model]
                
                # Only add ordinal info where we have valid ordinal positions
                # Use ordinal_weight to blend: embed = embed + ordinal_weight * ordinal_embed
                ordinal_mask = has_ordinal.unsqueeze(1).float()  # [batch_size, 1]
                embed = embed + self.ordinal_weight * ordinal_mask * ordinal_embed
            
            # ============================================================================
            # LOGGING (first batch only)
            # ============================================================================
            if self.training and not hasattr(self, '_mixture_attempts_logged'):
                col_prefix = f"[{self.column_name}] " if self.column_name else ""
                logger.debug(f"{col_prefix}MIXTURE: BERT={bert_available_count}/{batch_size}, "
                           f"temp={temperature:.2f}, learned={learned_pct:.1f}%, semantic={semantic_pct:.1f}%")
                if self.use_per_member_mixture:
                    logger.debug(f"   Per-member mixture: min={mixture_weights.min().item():.3f}, "
                               f"max={mixture_weights.max().item():.3f}, mean={mixture_weights.mean().item():.3f}")
                if self.is_ordinal:
                    logger.debug(f"   Ordinal encoding active, weight={self.ordinal_weight:.2f}")
                self._mixture_attempts_logged = True
            
            # ============================================================================
            # ENTROPY REGULARIZATION
            # ============================================================================
            if self.training:
                # Binary entropy: H = -p*log(p) - (1-p)*log(1-p)
                # Maximum at p=0.5, minimum at p=0 or p=1
                if self.use_per_member_mixture and self.mixture_logits is not None:
                    # Mean entropy across batch
                    p = mixture_weights
                    entropy = -(p * torch.log(p + 1e-10) + (1-p) * torch.log(1-p + 1e-10))
                    entropy = entropy.mean()
                else:
                    p = mixture_weights
                    entropy = -(p * torch.log(p + 1e-10) + (1-p) * torch.log(1-p + 1e-10))
                    entropy = entropy.mean()
                
                # Penalize high entropy with configurable weight
                entropy_loss = self.entropy_reg_weight * entropy
                
                # Store for logging (detach to avoid keeping gradient graph in logging vars)
                if not hasattr(self, '_last_entropy'):
                    self._last_entropy = entropy.detach().item()
                    self._last_mixture_weight = learned_pct / 100.0
                else:
                    self._last_entropy = 0.9 * self._last_entropy + 0.1 * entropy.detach().item()
                    self._last_mixture_weight = 0.9 * self._last_mixture_weight + 0.1 * (learned_pct / 100.0)
                
                # Log mixture evolution once per epoch
                if current_epoch != self._last_logged_epoch.item():
                    col_name_display = self.column_name or "unknown"
                    
                    # Track logit changes across epochs (only if mixture_logit exists)
                    logit_str = ""
                    if self.mixture_logit is not None:
                        if not hasattr(self, '_previous_logit'):
                            self._previous_logit = self.mixture_logit.item()
                            logit_change = 0.0
                        else:
                            logit_change = self.mixture_logit.item() - self._previous_logit
                            self._previous_logit = self.mixture_logit.item()
                        logit_str = f"Logit={self.mixture_logit.item():.4f} (Δ={logit_change:+.4f}), "
                    
                    # Extra info for enhanced features
                    extra_info = []
                    if self.use_curriculum_learning:
                        extra_info.append(f"floor={semantic_floor:.2f}")
                    if self.use_temperature_annealing:
                        extra_info.append(f"temp={temperature:.2f}")
                    if self.is_ordinal:
                        extra_info.append("ordinal")
                    extra_str = f" [{', '.join(extra_info)}]" if extra_info else ""
                    
                    # Per-member stats if available
                    pm_stats = ""
                    if self.use_per_member_mixture and self.mixture_logits is not None:
                        pm_weights = torch.sigmoid(self.mixture_logits).detach()
                        pm_range = (pm_weights.max() - pm_weights.min()).item()
                        pm_std = pm_weights.std().item()
                        pm_stats = f", PM_range={pm_range:.3f}, PM_std={pm_std:.4f}"
                    
                    # Log with gradient info (DEBUG to reduce per-epoch spam)
                    log_msg = (f"   🔄 Epoch {current_epoch} - SetEncoder '{col_name_display}': "
                              f"Mixture={learned_pct:.1f}%LRN/{semantic_pct:.1f}%SEM, "
                              f"{logit_str}"
                              f"Entropy={entropy.detach().item():.4f}{extra_str}{pm_stats}")
                    logger.debug(log_msg)
                    
                    # Mark this epoch as logged
                    self._last_logged_epoch.fill_(current_epoch)
                
                # Store entropy loss so it can be collected and added to total loss
                self._current_entropy_loss = entropy_loss
            else:
                # Not training - clear entropy loss
                self._current_entropy_loss = None
        else:
            # No adaptive mixture - use learned embeddings only
            self._current_entropy_loss = None
            if self.training and not hasattr(self, '_no_mixture_logged'):
                logger.info(f"🔍 SetEncoder ({self.column_name or 'unknown'}): Using learned embeddings only (no semantic mixture)")
                logger.info(f"   Reason: use_semantic_mixture={self.use_semantic_mixture}, "
                          f"bert_embeddings={'available' if self.bert_embeddings else 'None'}")
                self._no_mixture_logged = True
            embed = learned_embed
        
        # OOV HANDLING: Use BERT projection for unknown values (legacy path)
        if not self.use_semantic_mixture and self.bert_projection is not None:
            unknown_mask = (token.status == TokenStatus.UNKNOWN)
            
            if unknown_mask.any() and self.string_cache is not None and hasattr(token, 'original_string'):
                unknown_indices = unknown_mask.nonzero(as_tuple=True)[0].tolist()
                if unknown_indices:
                    # BATCH ENCODE: Get all unknown values at once instead of one-at-a-time
                    original_values = []
                    valid_indices = []
                    for idx in unknown_indices:
                        original_value = token.original_string[idx] if hasattr(token, 'original_string') else None
                        if original_value:
                            original_values.append(str(original_value))
                            valid_indices.append(idx)
                    
                    if original_values and hasattr(self.string_cache, 'get_embeddings_batch'):
                        # Use batch encoding - much faster!
                        bert_embeddings = self.string_cache.get_embeddings_batch(original_values)
                        for idx, bert_emb in zip(valid_indices, bert_embeddings):
                            if bert_emb is not None:
                                with torch.no_grad():
                                    # Use detach().clone() to avoid warning when copying from tensor
                                    if isinstance(bert_emb, torch.Tensor):
                                        bert_tensor = bert_emb.detach().clone().to(dtype=torch.float32)
                                    else:
                                        bert_tensor = torch.tensor(bert_emb, dtype=torch.float32)
                                    projected = self.bert_projection(bert_tensor.unsqueeze(0))
                                    embed[idx] = projected.squeeze(0)
                                token.status[idx] = TokenStatus.OK
                    else:
                        # Fallback: one-at-a-time (old StringCache or no batch support)
                        for idx in unknown_indices:
                            original_value = token.original_string[idx] if hasattr(token, 'original_string') else None
                            if original_value:
                                bert_emb = self.string_cache.get_embedding_from_cache(str(original_value))
                                if bert_emb is not None:
                                    with torch.no_grad():
                                        # Use detach().clone() to avoid warning when copying from tensor
                                        if isinstance(bert_emb, torch.Tensor):
                                            bert_tensor = bert_emb.detach().clone().to(dtype=torch.float32)
                                        else:
                                            bert_tensor = torch.tensor(bert_emb, dtype=torch.float32)
                                        projected = self.bert_projection(bert_tensor.unsqueeze(0))
                                        embed[idx] = projected.squeeze(0)
                                    token.status[idx] = TokenStatus.OK
        
        # Override embeddings for unknown and not present tokens
        # CRITICAL: Create comparison tensors on same device as token.status to avoid CPU tensor creation
        not_present_value = torch.tensor(TokenStatus.NOT_PRESENT, device=token.status.device, dtype=token.status.dtype)
        unknown_value = torch.tensor(TokenStatus.UNKNOWN, device=token.status.device, dtype=token.status.dtype)
        marginal_value = torch.tensor(TokenStatus.MARGINAL, device=token.status.device, dtype=token.status.dtype)

        # Cast replacement embedding to match output dtype (handles bfloat16 mixed precision)
        replacement = self._replacement_embedding.to(embed.dtype)
        embed[token.status == not_present_value] = replacement
        embed[token.status == unknown_value] = replacement
        embed[token.status == marginal_value] = replacement
        
        # CONDITIONAL NORMALIZATION based on config
        if self.config.normalize_output:
            # CRITICAL FIX: Add eps=1e-8 to prevent NaN gradients when norm is near zero
            short_vec = nn.functional.normalize(embed[:, 0:3], dim=1, eps=1e-8)
            full_vec = nn.functional.normalize(embed, dim=1, eps=1e-8)
        else:
            short_vec = embed[:, 0:3]
            full_vec = embed

        # NaN DIAGNOSTIC: Check for NaN/Inf in forward pass output (first batch only per epoch)
        if self.training:
            diag_key = '_nan_check_epoch'
            current_epoch = self._epoch_counter.item() if hasattr(self, '_epoch_counter') else 0
            if not hasattr(self, diag_key) or getattr(self, diag_key) != current_epoch:
                setattr(self, diag_key, current_epoch)
                has_nan_short = torch.isnan(short_vec).any().item()
                has_nan_full = torch.isnan(full_vec).any().item()
                has_inf_short = torch.isinf(short_vec).any().item()
                has_inf_full = torch.isinf(full_vec).any().item()
                if has_nan_short or has_nan_full or has_inf_short or has_inf_full:
                    col_name = self.column_name or 'unknown'
                    logger.error(f"💥 NaN/Inf in SetEncoder forward [{col_name}] epoch={current_epoch}:")
                    logger.error(f"   short_vec: NaN={has_nan_short}, Inf={has_inf_short}")
                    logger.error(f"   full_vec: NaN={has_nan_full}, Inf={has_inf_full}")
                    # Trace source: check intermediate values
                    has_nan_learned = torch.isnan(learned_embed).any().item() if 'learned_embed' in dir() else 'N/A'
                    has_nan_bert = torch.isnan(bert_embed).any().item() if 'bert_embed' in dir() and bert_embed is not None else 'N/A'
                    has_nan_replacement = torch.isnan(self._replacement_embedding).any().item()
                    logger.error(f"   Source tracing: learned_embed NaN={has_nan_learned}, bert_embed NaN={has_nan_bert}, replacement NaN={has_nan_replacement}")
                    # Check bert_projection weights
                    if hasattr(self, 'bert_projection') and self.bert_projection is not None:
                        has_nan_proj = any(torch.isnan(p).any().item() for p in self.bert_projection.parameters())
                        logger.error(f"   bert_projection weights NaN={has_nan_proj}")
                    # Check gating network
                    if hasattr(self, 'mixture_gate') and self.mixture_gate is not None:
                        has_nan_gate = any(torch.isnan(p).any().item() for p in self.mixture_gate.parameters())
                        logger.error(f"   mixture_gate weights NaN={has_nan_gate}")

        # DIAGNOSTIC: Check if set encoder is producing diverse outputs
        if self.training and hasattr(self, 'column_name') and self.column_name:
            current_epoch = getattr(self, '_current_epoch', torch.tensor(0)).item() if hasattr(self, '_current_epoch') else 0
            diag_key = f'_set_diag_{self.column_name}'
            if not hasattr(self, diag_key) or getattr(self, diag_key) != current_epoch:
                setattr(self, diag_key, current_epoch)
                with torch.no_grad():
                    if embed.shape[0] > 1:
                        embed_norm = nn.functional.normalize(embed, dim=1)
                        cos_matrix = embed_norm @ embed_norm.T
                        mask = ~torch.eye(embed.shape[0], dtype=torch.bool, device=cos_matrix.device)
                        avg_cos = cos_matrix[mask].mean().item()
                        # Count unique values in batch
                        n_unique = token.value.unique().numel()
                        logger.info(f"🔬 SET ENCODER [{self.column_name}] epoch={current_epoch}:")
                        logger.info(f"   Unique values in batch: {n_unique}/{embed.shape[0]}")
                        logger.info(f"   Output avg pairwise cos: {avg_cos:.4f} (low=diverse, high=collapsed)")
                        if avg_cos > 0.5:
                            logger.warning(f"   ⚠️  HIGH SIMILARITY: outputs all look similar! (column: {self.column_name}, avg_cos={avg_cos:.3f})")

        if return_strategy_encodings:
            # Build strategy encodings for strategy-aware relationship ops
            # Components: learned, semantic, ordinal (if enabled)
            strategy_list = [learned_embed]  # Always have learned

            if self.use_semantic_mixture and 'bert_embed' in dir():
                strategy_list.append(bert_embed)
            else:
                # No semantic mixture - duplicate learned as placeholder
                strategy_list.append(learned_embed)

            if self.is_ordinal and self.ordinal_embedding is not None and 'ordinal_embed' in dir():
                strategy_list.append(ordinal_embed)
            else:
                # No ordinal - use zeros as placeholder
                strategy_list.append(torch.zeros_like(learned_embed))

            # Stack: [batch, n_components, d_model]
            all_strategy_encodings = torch.stack(strategy_list, dim=1)
            return short_vec, full_vec, all_strategy_encodings
        return short_vec, full_vec

    def get_strategy_names(self):
        """Return list of component names in order (for strategy-aware relationship ops)."""
        names = ['LEARNED', 'SEMANTIC']
        if self.is_ordinal and self.ordinal_embedding is not None:
            names.append('ORDINAL')
        else:
            names.append('ORDINAL_PLACEHOLDER')
        return names

    def get_n_strategies(self):
        """Return number of encoding components."""
        return 3  # learned, semantic, ordinal (or placeholders)

    def __getstate__(self):
        """Exclude string_cache from pickling (contains non-picklable sqlite3.Connection)"""
        state = self.__dict__.copy()
        state.pop("string_cache", None)
        return state
    
    def __setstate__(self, state):
        """Restore state and reconnect to global string cache"""
        self.__dict__.update(state)

        # Backward compatibility: add missing attributes from newer versions
        if not hasattr(self, 'use_gating_network'):
            self.use_gating_network = False  # Old checkpoints don't have gating networks
            logger.debug("SetEncoder.__setstate__: Added missing use_gating_network=False for backward compatibility")
        if not hasattr(self, 'mixture_gate'):
            self.mixture_gate = None  # Old checkpoints don't have gating networks
            logger.debug("SetEncoder.__setstate__: Added missing mixture_gate=None for backward compatibility")
        if not hasattr(self, 'use_temperature_annealing'):
            self.use_temperature_annealing = True
            logger.debug("SetEncoder.__setstate__: Added missing use_temperature_annealing=True for backward compatibility")
        if not hasattr(self, 'temperature_start'):
            self.temperature_start = 1.0
            logger.debug("SetEncoder.__setstate__: Added missing temperature_start=1.0 for backward compatibility")
        if not hasattr(self, 'temperature_end'):
            self.temperature_end = 0.5
            logger.debug("SetEncoder.__setstate__: Added missing temperature_end=0.5 for backward compatibility")
        if not hasattr(self, 'use_curriculum_learning'):
            self.use_curriculum_learning = True
            logger.debug("SetEncoder.__setstate__: Added missing use_curriculum_learning=True for backward compatibility")
        if not hasattr(self, 'use_per_member_mixture'):
            self.use_per_member_mixture = True
            logger.debug("SetEncoder.__setstate__: Added missing use_per_member_mixture=True for backward compatibility")
        if not hasattr(self, 'entropy_reg_weight'):
            self.entropy_reg_weight = 0.3
            logger.debug("SetEncoder.__setstate__: Added missing entropy_reg_weight=0.3 for backward compatibility")
        # Ordinal/semantic attributes that may be missing in old checkpoints
        if not hasattr(self, 'is_ordinal'):
            self.is_ordinal = False
        if not hasattr(self, 'ordinal_embedding'):
            self.ordinal_embedding = None
        if not hasattr(self, 'ordinal_weight'):
            self.ordinal_weight = 0.0
        if not hasattr(self, 'semantic_floor_start'):
            self.semantic_floor_start = 0.5
        if not hasattr(self, 'semantic_floor_end'):
            self.semantic_floor_end = 0.0
        if not hasattr(self, 'use_semantic_mixture'):
            self.use_semantic_mixture = False
        if not hasattr(self, 'bert_embeddings'):
            self.bert_embeddings = None
        if not hasattr(self, 'bert_projection'):
            self.bert_projection = None
        if not hasattr(self, 'mixture_logit'):
            self.mixture_logit = None
        if not hasattr(self, 'mixture_logits'):
            self.mixture_logits = None

        # CRITICAL: Move to CPU if in CPU mode (embedding table might be on GPU)
        import os
        force_cpu = os.environ.get('FEATRIX_FORCE_CPU_SINGLE_PREDICTOR') == '1'
        if force_cpu:
            if hasattr(self, 'embedding') and self.embedding is not None:
                if list(self.embedding.parameters()):
                    embedding_device = next(self.embedding.parameters()).device
                    if embedding_device.type == 'cuda':
                        logger.info(f"📊 SetEncoder '{self.column_name}': embedding table on GPU - moving to CPU")
                        self.cpu()
            if is_gpu_available():
                empty_gpu_cache()

        # Reconnect to the global string cache if we have a filename
        if hasattr(self, '_string_cache_filename') and self._string_cache_filename:
            try:
                from featrix.neural.string_codec import get_global_string_cache
                self.string_cache = get_global_string_cache(
                    cache_filename=self._string_cache_filename,
                    initial_values=[],  # Global cache already has the data
                    debug_name=self.column_name or 'restored_set_encoder'
                )
            except Exception as e:
                logger.warning(f"⚠️ Failed to reconnect SetEncoder to global cache: {e}")
                self.string_cache = None
        else:
            self.string_cache = None

    @staticmethod
    def get_default_config(
        d_model: int, 
        n_members: int, 
        sparsity_ratio: float = 0.0, 
        initial_mixture_logit: Optional[float] = None,
        ordinal_info: Optional[dict] = None,
        use_per_member_mixture: bool = True,
        use_curriculum_learning: bool = True,
        use_temperature_annealing: bool = True,
        entropy_regularization_weight: float = 0.3,
    ):
        """Initialize the encoder with default parameters for the neural network.
        
        Args:
            d_model: Embedding dimension
            n_members: Number of set members
            sparsity_ratio: Ratio of null/missing values (0.0 = dense, 1.0 = all null)
            initial_mixture_logit: Initial value for mixture logit (None = -0.5 for semantic bias)
                                  Positive → prefer learned embeddings
                                  Negative → prefer semantic (BERT) embeddings
                                  0.0 = 50/50 mixture, +1.0 ≈ 73% learned, -1.0 ≈ 27% learned
            ordinal_info: Dict with ordinal detection results (is_ordinal, ordered_values, etc.)
            use_per_member_mixture: If True, each category gets its own mixture weight
            use_curriculum_learning: If True, start with semantic-heavy and shift to learned
            use_temperature_annealing: If True, make mixture decisions sharper over training
            entropy_regularization_weight: Weight for entropy penalty (higher = more decisive)
        """
        # Import here to avoid circular import
        from .sphere_config import get_config
        
        # Get normalization setting from global config
        normalize_column_encoders = get_config().get_normalize_column_encoders()
        
        return SetEncoderConfig(
            d_model=d_model,
            n_members=n_members,
            normalize_output=normalize_column_encoders,  # Config-controlled normalization
            sparsity_ratio=sparsity_ratio,  # Pass sparsity for gradient scaling
            initial_mixture_logit=initial_mixture_logit,  # Pass initial mixture logit if provided
            # New v0.2+ options
            ordinal_info=ordinal_info,
            use_per_member_mixture=use_per_member_mixture,
            use_curriculum_learning=use_curriculum_learning,
            use_temperature_annealing=use_temperature_annealing,
            entropy_regularization_weight=entropy_regularization_weight,
        )


class SetCodec(nn.Module):
    def __init__(self, members: set, enc_dim: int, remove_nan=True, class_weights=None, loss_type="cross_entropy", sparsity_ratio=0.0, string_cache=None, ordinal_info=None):
        super().__init__()
        self._is_decodable = True

        self.members = members
        self.sparsity_ratio = sparsity_ratio  # Store sparsity ratio for later use
        self.string_cache = string_cache  # Store string cache path for semantic initialization
        self.ordinal_info = ordinal_info  # Store ordinal detection results for encoder recreation
        if remove_nan:
            self.members.discard("nan")
            self.members.discard("NaN")
            self.members.discard("Nan")
            self.members.discard("NAN")
            self.members.discard("None")        # null, NULL, nil
            # empty strings - not sure if it's a great idea to include them here
            self.members.discard("")
            self.members.discard(" ")

            for x in self.members:
                try:
                    if str(x).strip() == "":
                        self.members.discard(x)
                except Exception:
                    traceback.print_exc(file=sys.stdout)
                    print("... continuing")

        # Sorting ensures that two encoders created using the same set will
        # have the same mapping from members to tokens.
        uniques = sorted(list(self.members))
        uniques = ["<UNKNOWN>"] + uniques
        # Need to re-compute the set members, after adding <UNKNOWN>
        # TODO: this seems very hacky.
        self.members = set(uniques)
        self.n_members = len(self.members)

        self.enc_dim = enc_dim
        self.members_to_tokens = {member: token for token, member in enumerate(uniques)}
        self.tokens_to_members = {
            token: member for member, token in self.members_to_tokens.items()
        }
        # Store member names (excluding <UNKNOWN>) for semantic initialization
        self.member_names = [m for m in uniques if m != "<UNKNOWN>"]
        
        # DIAGNOSTIC: Log the token mapping for debugging backwards learning
        # Condense to one line to avoid log spam
        sorted_mappings = sorted(self.members_to_tokens.items(), key=lambda x: x[1])
        mapping_str = ", ".join([f"{token}:'{member}'" for member, token in sorted_mappings[:10]])
        if len(sorted_mappings) > 10:
            mapping_str += f", ... ({len(sorted_mappings)} total tokens)"
        
        # Create loss function with optional class weighting
        # loss_type can be "focal", "cross_entropy", "prauc", or "adaptive"
        # FocalLoss: Better for single predictor training with imbalanced classes
        # CrossEntropyLoss: More stable for embedding space training
        # PRAUCLoss: Hard negative mining - directly optimizes precision-recall tradeoff
        # AdaptiveLoss: Learned blend of all three - MLP learns optimal weights during training
        loss_name = ""
        if loss_type == "focal":
            # For single predictor, use min_weight=0.1 so correct negatives still get credit
            focal_min_weight = 0.1
            if class_weights is not None:
                self.loss_fn = FocalLoss(alpha=class_weights, gamma=2.0, min_weight=focal_min_weight)
            else:
                self.loss_fn = FocalLoss(alpha=None, gamma=2.0, min_weight=focal_min_weight)
            loss_name = f"FocalLoss(γ=2.0)"
        elif loss_type == "cross_entropy":
            self.loss_fn = nn.CrossEntropyLoss()
            loss_name = "CrossEntropy"
        elif loss_type == "prauc":
            # PRAUCLoss: Hard negative mining for reducing FP while maintaining recall
            # Finds hardest negatives (high-scoring negs → FP) and hardest positives (low-scoring pos → FN)
            # Penalizes when hard negatives outrank hard positives
            # Best for: reducing FP without sacrificing recall
            if class_weights is not None:
                self.loss_fn = PRAUCLoss(alpha=class_weights)
            else:
                self.loss_fn = PRAUCLoss(alpha=None)
            loss_name = "PRAUCLoss(hard-neg-mining)"
        elif loss_type == "adaptive":
            # AdaptiveLoss: learns optimal blend of focal (multiple gammas), prauc, and cross-entropy
            # Two implementations: "voting" (win-rate based) or "learning" (gradient-learned)
            from featrix.neural.sphere_config import get_config
            adaptive_loss_type = get_config().get_sp_adaptive_loss_type()
            if adaptive_loss_type == "voting":
                self.loss_fn = AdaptiveVotingLoss(alpha=class_weights)
                loss_name = "AdaptiveVotingLoss(win-rate)"
            else:
                self.loss_fn = AdaptiveLearningLoss(alpha=class_weights)
                loss_name = "AdaptiveLearningLoss(gradient)"
        else:
            raise ValueError(f"Unknown loss_type '{loss_type}'. Expected 'focal', 'cross_entropy', 'prauc', or 'adaptive'.")
        
        # ONE LINE: token count, mapping, loss
        logger.info(f"SetCodec: {len(sorted_mappings)} tokens [{mapping_str}], loss={loss_name}")

    def get_codec_name(self):
        return ColumnType.SET

    def get_codec_info(self):
        d = {"num_uniques": len(self.members), 
             "enc_dim": self.enc_dim}
        if len(self.members) <= 50:
            d['uniques'] = self.members
        return d

    def get_not_present_token(self):
        return Token(
            value=0,
            status=TokenStatus.NOT_PRESENT,  # torch.tensor([TokenStatus.NOT_PRESENT] * 1),
        )
    
    def get_marginal_token(self):
        """Return a token representing a masked/marginal value for reconstruction testing."""
        return Token(
            value=0,  # Value doesn't matter for MARGINAL tokens
            status=TokenStatus.MARGINAL,
        )

    def get_visualization_domain(self, _min=None, _max=None, _steps=40):
        # ignore inputs for now.
        # We could maybe use _steps to reduce a big set somehow?
        #
        the_members = [
            self.detokenize(Token(value=i, status=TokenStatus.OK))
            for i in range(len(self.members))
        ]

        return the_members

    @property
    def token_dtype(self):
        return int

    def tokenize(self, member):
        # TODO: must be able to tokenize an entire batch in a single go, and return
        # a batch token.

        # TODO:
        try:
            member = str(member)
        except Exception:
            return Token(
                value=torch.tensor(0, dtype=torch.float32),
                status=TokenStatus.UNKNOWN,
            )

        if member in self.members_to_tokens:
            return Token(
                value=torch.tensor(self.members_to_tokens[member], dtype=torch.float32),
                status=TokenStatus.OK,
            )
        else:
            # check for a blasted float. -- we need to solve this upstream when we're creating the tokenizer. But we also should probably handle basic mix/matches like uppercase/lowercase...
            # ... and whitespace trimming...
            if member + ".0" in self.members_to_tokens:
                return Token(
                    value=torch.tensor(self.members_to_tokens[member + ".0"], dtype=torch.float32),
                    status=TokenStatus.OK,
                )

            return Token(
                # the member does not matter for UNKNOWN status, but it's got to
                # be something that does not throw an error when passed to the embedding
                # module, because we embed first, and then overwrite with UNKNOWN vector.
                value=torch.tensor(0, dtype=torch.float32),
                status=TokenStatus.UNKNOWN,
            )

    def detokenize(self, token):
        # ToDO: it should really be a batch of tokens that we take in.
        if (
            token.status == TokenStatus.NOT_PRESENT
            or token.status == TokenStatus.UNKNOWN
        ):
            raise ValueError(f"Cannot detokenize a token with status {token.status}.")
        else:
            if token.value in self.tokens_to_members:
                return self.tokens_to_members[token.value]
            else:
                raise ValueError(f"Cannot decode token with value {token.value}.")

    def loss(self, logits, targets):
        return self.loss_fn(logits, targets)

    def loss_single(self, logits, target):
        # Loss function specific to batches of size one, and single targets.

        # We assume that target can be the wrong type, because it's type depends on the
        # types of other target variables it's batched with, and that it's provided as a
        # single value. Therefore, it must be cast to the correct type, and a dimension
        # must be added via `unsqueeze`.
        target = target.long().unsqueeze(dim=0)

        return self.loss(logits, target)

    def save(self):
        # we create a json dict.
        buffer = io.BytesIO()
        torch.save(self.state_dict(), buffer)

        buffer_b64 = "base64:" + str(
            base64.standard_b64encode(buffer.getvalue()).decode("utf8")
        )
        checksum = hashlib.md5(buffer.getvalue()).hexdigest()
        enc_bytes = pickle.dumps(self.members)
        members_b64 = "base64:" + str(
            base64.standard_b64encode(enc_bytes).decode("utf8")
        )

        d = {
            "type": "SetCodec",
            "embedding": buffer_b64,
            "embedding_checksum": checksum,
            "enc_dim": self.enc_dim,
            "members": members_b64,
        }

        return d

    def load(self, j):
        d_type = j.get("type")
        assert d_type == "SetCodec", "wrong load method called for __%s__" % d_type
        self.enc_dim = j.get("enc_dim")

        ########################
        # Set up members/uniques
        ########################
        members = j.get("members")
        assert members.startswith("base64:")
        members = members[6:]

        try:
            # theEncoder is a string 'b'<>'' ... sigh
            # print("members = __%s__" % members)
            e64 = base64.standard_b64decode(members)  # uniques[2:-1])
            unpickledEncoder = pickle.loads(e64)  # pickleBytes.read())
            # print("unpickledEncoder = ", unpickledEncoder)
            self.members = unpickledEncoder  # encoders[key] = unpickledEncoder
        except Exception:
            print(f"PICKLE ERROR for = __{j}__")
            traceback.print_exc()

        # copied from constructor
        uniques = sorted(list(self.members))
        self.members_to_tokens = {member: token for token, member in enumerate(uniques)}
        self.tokens_to_members = {
            token: member for member, token in self.members_to_tokens.items()
        }

        ########################
        # Set up embedding stuff
        ########################
        embed = j.get("embedding")
        embed_checksum = j.get("embedding_checksum")

        if embed.startswith("base64:"):
            embed = embed[6:]

        r64 = base64.standard_b64decode(embed)
        r_checksum64 = hashlib.md5(r64).hexdigest()

        if r_checksum64 != embed_checksum:
            print(f"CHECKSUMS {r_checksum64} and {embed_checksum} DO NOT MATCH - !")
            return

        buffer = io.BytesIO(r64)
        theDict = torch.load(buffer, weights_only=False)
        # print("theDict = ", theDict)

        # Without the below 'initializations', the load_state_dict() fails due to Size mismatches.
        self._unknown_embedding = nn.Parameter(torch.randn(self.enc_dim))
        self.register_buffer("not_present", torch.zeros(self.enc_dim))
        self.embedding = NormalizedEmbedding(len(uniques), self.enc_dim)
        self.load_state_dict(theDict)
        return


def runTest():
    colors = ["blue", "red", "green"]

    # Save what we make.
    codec = SetCodec(set(colors), enc_dim=50)
    jj = codec.save()
    print(jj)

    # Load what we saved.
    newCodec = SetCodec(set([]), enc_dim=50)
    newCodec.load(jj)

    assert newCodec.members == codec.members
    assert newCodec.enc_dim == codec.enc_dim
    assert torch.equal(newCodec.unknown, codec.unknown)
    assert torch.equal(newCodec.embedding.embed.weight, codec.embedding.embed.weight)
    print("PASS!")
    #    print(newCodec.members)
    return


if __name__ == "__main__":
    runTest()
