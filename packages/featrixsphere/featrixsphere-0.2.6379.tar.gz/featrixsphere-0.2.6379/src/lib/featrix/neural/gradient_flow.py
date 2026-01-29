#  -*- coding: utf-8 -*-
#
#  Copyright Featrix, Inc 2023-2025
#
#  Proprietary and Confidential. Unauthorized use, copying or dissemination
#  of these materials is strictly prohibited.
#
"""
Gradient Flow Tracking - Monitor Encoder vs Predictor Gradient Health

This module provides epoch-level gradient flow tracking that feeds into the
adaptive control system. It detects:
1. Gradient suppression (encoder gradients collapsing after weight adjustments)
2. Gradient imbalance (encoder vs predictor magnitude mismatch)
3. Recovery failure (gradients don't recover after interventions)

Key insight from the adaptive control guidelines:
> "After adaptive adjustments, do encoder gradients recover, or do they stay suppressed?"
> If suppressed → controller is stabilizing the loss by killing learning.

Usage:
    from featrix.neural.gradient_flow import (
        GradientFlowTracker, GradientFlowStats, compute_epoch_gradient_flow
    )

    # Create tracker at training start
    tracker = GradientFlowTracker()

    # After each epoch's backward pass (while gradients are populated)
    stats = compute_epoch_gradient_flow(encoder)
    result = tracker.update(epoch_idx, stats)

    if result['suppression_detected']:
        logger.warning(f"Gradient suppression detected: {result['suppression_type']}")

    # Feed to WeightTimeline for adaptive response
    weight_timeline.update_with_gradient_flow(epoch_idx, std_per_dim, result)
"""
import logging
import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from featrix.neural.adaptive_event_log import (
    AdaptiveEvent,
    ExpectedEffect,
    ReasonCode,
    get_adaptive_event_log,
)
from featrix.neural.timeline_events import post_timeline_event

logger = logging.getLogger(__name__)


# ============================================================================
# GRADIENT FLOW STATS - Per-epoch snapshot
# ============================================================================

@dataclass
class GradientFlowStats:
    """
    Epoch-level gradient flow statistics for adaptive control.

    Tracks encoder vs predictor gradient magnitude to detect:
    - Gradient suppression (encoder gradients collapsing)
    - Gradient imbalance (one component dominating)
    - Learning stagnation (all gradients vanishing)
    """
    encoder_norm: float = 0.0          # Global encoder gradient norm
    predictor_norm: float = 0.0        # Global predictor gradient norm
    log_ratio: float = 0.0             # log(encoder) - log(predictor)
    col_encoder_norm: float = 0.0      # Column encoder gradient norm
    joint_encoder_norm: float = 0.0    # Joint encoder gradient norm
    is_balanced: bool = True           # Within 10× (|log_ratio| < 2.3)
    encoder_suppressed: bool = False   # Encoder gradients collapsed
    predictor_suppressed: bool = False # Predictor gradients collapsed

    def to_dict(self) -> Dict[str, Any]:
        return {
            'encoder_norm': self.encoder_norm,
            'predictor_norm': self.predictor_norm,
            'log_ratio': self.log_ratio,
            'col_encoder_norm': self.col_encoder_norm,
            'joint_encoder_norm': self.joint_encoder_norm,
            'is_balanced': self.is_balanced,
            'encoder_suppressed': self.encoder_suppressed,
            'predictor_suppressed': self.predictor_suppressed,
        }


def compute_epoch_gradient_flow(encoder) -> GradientFlowStats:
    """
    Compute gradient flow statistics for the current state of the model.

    Call this after the backward pass when gradients are populated.
    This provides the data needed for WeightTimeline's gradient-aware adaptation.

    Args:
        encoder: The EmbeddedSpace encoder with column_encoder, joint_encoder, and predictors

    Returns:
        GradientFlowStats with computed metrics
    """
    stats = GradientFlowStats()

    # Collect gradient norms by component
    col_enc_squared = 0.0
    joint_enc_squared = 0.0
    predictor_squared = 0.0

    col_enc_count = 0
    joint_enc_count = 0
    predictor_count = 0

    for name, param in encoder.named_parameters():
        if param.grad is None:
            continue

        grad_norm_sq = param.grad.norm().item() ** 2

        if 'column_encoder' in name:
            col_enc_squared += grad_norm_sq
            col_enc_count += 1
        elif 'joint_encoder' in name:
            joint_enc_squared += grad_norm_sq
            joint_enc_count += 1
        elif 'predictor' in name:
            predictor_squared += grad_norm_sq
            predictor_count += 1

    # Compute norms
    stats.col_encoder_norm = math.sqrt(col_enc_squared) if col_enc_squared > 0 else 0.0
    stats.joint_encoder_norm = math.sqrt(joint_enc_squared) if joint_enc_squared > 0 else 0.0
    stats.predictor_norm = math.sqrt(predictor_squared) if predictor_squared > 0 else 0.0

    # Total encoder norm (column + joint)
    stats.encoder_norm = math.sqrt(col_enc_squared + joint_enc_squared)

    # Compute log ratio (encoder vs predictor)
    if stats.encoder_norm > 1e-10 and stats.predictor_norm > 1e-10:
        stats.log_ratio = math.log(stats.encoder_norm) - math.log(stats.predictor_norm)
        stats.is_balanced = abs(stats.log_ratio) < 2.3  # Within 10×
    else:
        stats.log_ratio = float('nan')
        stats.is_balanced = False

    # Detect suppression (very small gradients)
    SUPPRESSION_THRESHOLD = 1e-7
    stats.encoder_suppressed = stats.encoder_norm < SUPPRESSION_THRESHOLD and col_enc_count > 0
    stats.predictor_suppressed = stats.predictor_norm < SUPPRESSION_THRESHOLD and predictor_count > 0

    return stats


# ============================================================================
# GRADIENT FLOW TRACKER - Multi-epoch tracking
# ============================================================================

class GradientFlowTracker:
    """
    Tracks gradient flow over epochs for suppression detection.

    Key insight: A single low gradient norm isn't alarming. What matters is:
    1. Sudden drops (suppression ratio < 0.3 vs EMA)
    2. Sustained suppression (multiple consecutive epochs)
    3. Recovery failure (gradients don't recover after weight adjustments)

    This tracker feeds data to WeightTimeline and emits events to the
    AdaptiveEventLog for post-hoc analysis.
    """

    # Thresholds
    SUPPRESSION_RATIO_THRESHOLD = 0.3   # Current < 30% of EMA = suppressed
    CONSECUTIVE_SUPPRESSED_ALERT = 3    # Alert after 3 consecutive suppressed epochs
    EMA_ALPHA = 0.2                      # EMA smoothing factor (20% new, 80% history)

    def __init__(self, emit_events: bool = True):
        """
        Initialize the gradient flow tracker.

        Args:
            emit_events: If True, emit events to AdaptiveEventLog
        """
        self.emit_events = emit_events

        # EMA tracking
        self.encoder_norm_ema: Optional[float] = None
        self.predictor_norm_ema: Optional[float] = None

        # History for analysis
        self.history: List[Dict[str, Any]] = []

        # Suppression tracking
        self.consecutive_encoder_suppressed = 0
        self.consecutive_predictor_suppressed = 0
        self.total_encoder_suppressed_epochs = 0
        self.total_predictor_suppressed_epochs = 0

        # Recovery tracking (did gradients recover after weight adjustments?)
        self.last_adjustment_epoch: int = -1
        self.pre_adjustment_encoder_norm: Optional[float] = None
        self.recovery_status: str = "n/a"  # "recovered", "suppressed", "n/a"

        # Current step (for event logging)
        self._current_step = 0

    def update(self, epoch: int, stats: GradientFlowStats, step: int = None) -> Dict[str, Any]:
        """
        Update tracker with new epoch's gradient flow stats.

        Args:
            epoch: Current epoch index
            stats: GradientFlowStats from compute_epoch_gradient_flow()
            step: Current global step (for event logging)

        Returns:
            dict with:
            - suppression_detected: bool
            - suppression_type: "encoder" | "predictor" | "both" | None
            - suppression_ratio: float (current / EMA)
            - recovery_status: "recovered" | "suppressed" | "pending" | "n/a"
        """
        if step is not None:
            self._current_step = step

        result = {
            'epoch': epoch,
            'suppression_detected': False,
            'suppression_type': None,
            'encoder_suppression_ratio': 1.0,
            'predictor_suppression_ratio': 1.0,
            'recovery_status': self.recovery_status,
            'consecutive_encoder_suppressed': self.consecutive_encoder_suppressed,
            'consecutive_predictor_suppressed': self.consecutive_predictor_suppressed,
            'encoder_norm': stats.encoder_norm,
            'predictor_norm': stats.predictor_norm,
            'log_ratio': stats.log_ratio,
            'is_balanced': stats.is_balanced,
        }

        # Initialize EMA on first epoch
        if self.encoder_norm_ema is None:
            self.encoder_norm_ema = stats.encoder_norm if stats.encoder_norm > 0 else 1.0
            self.predictor_norm_ema = stats.predictor_norm if stats.predictor_norm > 0 else 1.0
            self.history.append({
                'epoch': epoch,
                'encoder_norm': stats.encoder_norm,
                'predictor_norm': stats.predictor_norm,
                'log_ratio': stats.log_ratio,
            })
            # Post to timeline
            post_timeline_event({
                'epoch': epoch,
                'event_type': 'gradient_flow_initialized',
                'encoder_norm': stats.encoder_norm,
                'predictor_norm': stats.predictor_norm,
                'log_ratio': stats.log_ratio if not math.isnan(stats.log_ratio) else None,
            })
            return result

        # Compute suppression ratios
        encoder_ratio = stats.encoder_norm / self.encoder_norm_ema if self.encoder_norm_ema > 1e-10 else 1.0
        predictor_ratio = stats.predictor_norm / self.predictor_norm_ema if self.predictor_norm_ema > 1e-10 else 1.0

        result['encoder_suppression_ratio'] = encoder_ratio
        result['predictor_suppression_ratio'] = predictor_ratio

        # Check for encoder suppression
        encoder_suppressed = encoder_ratio < self.SUPPRESSION_RATIO_THRESHOLD
        if encoder_suppressed:
            self.consecutive_encoder_suppressed += 1
            self.total_encoder_suppressed_epochs += 1
        else:
            self.consecutive_encoder_suppressed = 0

        # Check for predictor suppression
        predictor_suppressed = predictor_ratio < self.SUPPRESSION_RATIO_THRESHOLD
        if predictor_suppressed:
            self.consecutive_predictor_suppressed += 1
            self.total_predictor_suppressed_epochs += 1
        else:
            self.consecutive_predictor_suppressed = 0

        result['consecutive_encoder_suppressed'] = self.consecutive_encoder_suppressed
        result['consecutive_predictor_suppressed'] = self.consecutive_predictor_suppressed

        # Alert if consecutive suppression exceeds threshold
        suppression_type = None
        if self.consecutive_encoder_suppressed >= self.CONSECUTIVE_SUPPRESSED_ALERT:
            result['suppression_detected'] = True
            suppression_type = 'encoder'

        if self.consecutive_predictor_suppressed >= self.CONSECUTIVE_SUPPRESSED_ALERT:
            result['suppression_detected'] = True
            if suppression_type == 'encoder':
                suppression_type = 'both'
            else:
                suppression_type = 'predictor'

        result['suppression_type'] = suppression_type

        # Emit suppression event if detected
        if result['suppression_detected'] and self.emit_events:
            self._emit_suppression_event(epoch, result, stats)

        # Check recovery after weight adjustment
        if self.last_adjustment_epoch >= 0 and self.pre_adjustment_encoder_norm is not None:
            epochs_since_adjustment = epoch - self.last_adjustment_epoch
            if epochs_since_adjustment <= 5:
                # Still in recovery window
                if stats.encoder_norm >= self.pre_adjustment_encoder_norm * 0.8:
                    self.recovery_status = "recovered"
                else:
                    self.recovery_status = "pending"
            else:
                # Recovery window expired
                if stats.encoder_norm >= self.pre_adjustment_encoder_norm * 0.8:
                    self.recovery_status = "recovered"
                else:
                    self.recovery_status = "suppressed"
                    # Emit recovery failure event
                    if self.emit_events and self.recovery_status == "suppressed":
                        self._emit_recovery_failure_event(epoch, stats)

        result['recovery_status'] = self.recovery_status

        # Update EMA (only if not suppressed, to maintain baseline)
        if not encoder_suppressed:
            self.encoder_norm_ema = self.EMA_ALPHA * stats.encoder_norm + (1 - self.EMA_ALPHA) * self.encoder_norm_ema
        if not predictor_suppressed:
            self.predictor_norm_ema = self.EMA_ALPHA * stats.predictor_norm + (1 - self.EMA_ALPHA) * self.predictor_norm_ema

        # Record history
        self.history.append({
            'epoch': epoch,
            'encoder_norm': stats.encoder_norm,
            'predictor_norm': stats.predictor_norm,
            'log_ratio': stats.log_ratio,
            'encoder_ratio': encoder_ratio,
            'predictor_ratio': predictor_ratio,
            'encoder_suppressed': encoder_suppressed,
            'predictor_suppressed': predictor_suppressed,
        })

        # Keep history bounded
        if len(self.history) > 200:
            self.history = self.history[-200:]

        # Post to timeline (every epoch)
        post_timeline_event({
            'epoch': epoch,
            'event_type': 'gradient_flow_update',
            'encoder_norm': stats.encoder_norm,
            'predictor_norm': stats.predictor_norm,
            'log_ratio': stats.log_ratio if not math.isnan(stats.log_ratio) else None,
            'encoder_ratio': encoder_ratio,
            'predictor_ratio': predictor_ratio,
            'encoder_suppressed': encoder_suppressed,
            'predictor_suppressed': predictor_suppressed,
            'is_balanced': stats.is_balanced,
        })

        # Log if significant
        if result['suppression_detected']:
            logger.warning(
                f"⚠️  [epoch={epoch}] Gradient suppression detected: {suppression_type} "
                f"(enc_ratio={encoder_ratio:.3f}, pred_ratio={predictor_ratio:.3f})"
            )
        elif not stats.is_balanced and epoch % 10 == 0:
            logger.info(
                f"📊 [epoch={epoch}] Gradient flow imbalanced: logR={stats.log_ratio:+.2f} "
                f"(encoder_norm={stats.encoder_norm:.2e}, predictor_norm={stats.predictor_norm:.2e})"
            )

        return result

    def record_weight_adjustment(self, epoch: int, current_encoder_norm: float):
        """
        Record that a weight adjustment was made, so we can track recovery.

        Call this when WeightTimeline makes an adjustment.
        """
        self.last_adjustment_epoch = epoch
        self.pre_adjustment_encoder_norm = current_encoder_norm
        self.recovery_status = "pending"

        post_timeline_event({
            'epoch': epoch,
            'event_type': 'gradient_flow_adjustment_recorded',
            'pre_adjustment_encoder_norm': current_encoder_norm,
        })

    def _emit_suppression_event(self, epoch: int, result: Dict[str, Any], stats: GradientFlowStats):
        """Emit a gradient suppression event to the AdaptiveEventLog."""
        log = get_adaptive_event_log()

        # Determine reason code based on suppression type
        if result['suppression_type'] == 'encoder':
            reason = ReasonCode.ENCODER_GRADIENT_SUPPRESSED
        elif result['suppression_type'] == 'predictor':
            reason = ReasonCode.PREDICTOR_GRADIENT_SUPPRESSED
        else:
            reason = ReasonCode.ENCODER_GRADIENT_SUPPRESSED  # default to encoder

        log.emit_simple(
            variable="gradient_flow.encoder_norm",
            old_value=self.encoder_norm_ema or 0.0,
            new_value=stats.encoder_norm,
            epoch=epoch,
            step=self._current_step,
            controller_name="GradientFlowTracker",
            reason_code=reason,
            trigger_metric="encoder_suppression_ratio",
            trigger_value=result['encoder_suppression_ratio'],
            expected_effect=ExpectedEffect.BALANCE_GRADIENTS,
            notes=f"Consecutive suppressed epochs: {self.consecutive_encoder_suppressed}",
            force=True,  # Always log suppression events
        )

    def _emit_recovery_failure_event(self, epoch: int, stats: GradientFlowStats):
        """Emit a recovery failure event to the AdaptiveEventLog."""
        log = get_adaptive_event_log()

        log.emit_simple(
            variable="gradient_flow.recovery_status",
            old_value=1.0,  # Expected recovery
            new_value=0.0,  # Failed to recover
            epoch=epoch,
            step=self._current_step,
            controller_name="GradientFlowTracker",
            reason_code=ReasonCode.ENCODER_GRADIENT_SUPPRESSED,
            trigger_metric="encoder_norm",
            trigger_value=stats.encoder_norm,
            expected_effect=ExpectedEffect.INCREASE_ENCODER_GRADIENT,
            notes=f"Recovery failed after {epoch - self.last_adjustment_epoch} epochs",
            force=True,
        )

    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics for logging/debugging."""
        return {
            'encoder_norm_ema': self.encoder_norm_ema,
            'predictor_norm_ema': self.predictor_norm_ema,
            'total_encoder_suppressed_epochs': self.total_encoder_suppressed_epochs,
            'total_predictor_suppressed_epochs': self.total_predictor_suppressed_epochs,
            'consecutive_encoder_suppressed': self.consecutive_encoder_suppressed,
            'consecutive_predictor_suppressed': self.consecutive_predictor_suppressed,
            'recovery_status': self.recovery_status,
            'history_length': len(self.history),
        }

    def get_recent_log_ratios(self, n: int = 10) -> List[float]:
        """Get the last n log ratios for trend analysis."""
        return [h['log_ratio'] for h in self.history[-n:] if not math.isnan(h.get('log_ratio', float('nan')))]

    def detect_oscillation(self, window: int = 10) -> Dict[str, Any]:
        """
        Detect if gradients are oscillating (sign changes in log_ratio).

        This can indicate the controller is over-correcting.
        """
        log_ratios = self.get_recent_log_ratios(window)
        if len(log_ratios) < 3:
            return {'oscillating': False, 'sign_changes': 0}

        sign_changes = sum(1 for i in range(1, len(log_ratios))
                         if log_ratios[i] * log_ratios[i-1] < 0)

        return {
            'oscillating': sign_changes >= len(log_ratios) * 0.5,
            'sign_changes': sign_changes,
            'window_size': len(log_ratios),
        }
