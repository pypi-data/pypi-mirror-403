#  -*- coding: utf-8 -*-
#
#  Copyright Featrix, Inc 2023-2025
#
#  Proprietary and Confidential. Unauthorized use, copying or dissemination
#  of these materials is strictly prohibited.
#
"""
Adaptive Event Log - Unified Tracking of All Adaptive Variable Changes

This module provides a centralized, append-only event log for tracking every
adaptive variable change across all controllers (WeightTimeline, LRTimeline,
GradientFlowTracker, etc.).

Key design principles:
1. Attribution: Every change records WHY it happened (trigger metric, reason code)
2. Batching: Multiple changes from the same trigger share a group_id
3. Rate limiting: Prevents twitchy controllers from flooding the log
4. Post-hoc analysis: Structured format enables "what changed and when?" queries

Usage:
    from featrix.neural.adaptive_event_log import get_adaptive_event_log, AdaptiveEvent

    log = get_adaptive_event_log()

    # Start a batch when making multiple related changes
    group_id = log.start_event_group(
        epoch=10,
        step=1500,
        controller_name="WeightTimeline",
        reason_code=ReasonCode.EMBEDDING_COLLAPSE,
        trigger_metric="std_per_dim",
        trigger_value=0.018
    )

    # Emit individual variable changes
    log.emit(AdaptiveEvent(
        variable="spread_weight",
        old_value=5.0,
        new_value=7.5,
        expected_effect=ExpectedEffect.INCREASE_SPREAD,
        group_id=group_id
    ))

    # End the batch
    log.end_event_group(group_id)
"""
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ============================================================================
# REASON CODES - Why did this change happen?
# ============================================================================

class ReasonCode(Enum):
    """Standardized reason codes for adaptive changes."""

    # Embedding health reasons
    EMBEDDING_COLLAPSE = "embedding_collapse"           # std/dim < emergency threshold
    EMBEDDING_WARNING = "embedding_warning"             # std/dim < warning threshold
    EMBEDDING_RECOVERY = "embedding_recovery"           # std/dim returned to healthy

    # Gradient flow reasons
    ENCODER_GRADIENT_SUPPRESSED = "encoder_grad_suppressed"   # Encoder gradients collapsed
    PREDICTOR_GRADIENT_SUPPRESSED = "pred_grad_suppressed"    # Predictor gradients collapsed
    GRADIENT_IMBALANCE = "gradient_imbalance"                 # Encoder/predictor ratio > 10×
    GRADIENT_RECOVERED = "gradient_recovered"                 # Gradients recovered after intervention

    # Loss-based reasons
    LOSS_PLATEAU = "loss_plateau"                       # Loss stopped improving
    LOSS_SPIKE = "loss_spike"                           # Sudden loss increase
    LOSS_OSCILLATION = "loss_oscillation"               # Loss oscillating (sign changes)

    # Class balance reasons
    IMBALANCE_RECALL_DROP = "imbalance_recall_drop"     # Minority class recall dropped
    IMBALANCE_PRECISION_DROP = "imbalance_precision_drop"
    CLASS_WEIGHT_REBALANCE = "class_weight_rebalance"

    # Metric-based reasons
    FP_SPIKE = "fp_spike"                               # False positive rate spiked
    FN_SPIKE = "fn_spike"                               # False negative rate spiked
    AUC_DROP = "auc_drop"                               # AUC decreased significantly

    # Scheduled/manual reasons
    SCHEDULED_WARMUP = "scheduled_warmup"               # Part of warmup schedule
    SCHEDULED_DECAY = "scheduled_decay"                 # Part of decay schedule
    MANUAL_OVERRIDE = "manual_override"                 # User/config specified

    # Recovery/safety reasons
    COOLDOWN_EXPIRED = "cooldown_expired"               # Cooldown period ended
    STACKING_LIMIT_HIT = "stacking_limit_hit"           # Hit max consecutive adjustments
    EMERGENCY_INTERVENTION = "emergency_intervention"    # Critical situation override


# ============================================================================
# EXPECTED EFFECTS - What do we expect this change to do?
# ============================================================================

class ExpectedEffect(Enum):
    """What effect do we expect from this change?"""

    # Embedding effects
    INCREASE_SPREAD = "increase_spread"                 # Spread embeddings apart
    DECREASE_SPREAD = "decrease_spread"                 # Allow embeddings to cluster
    STABILIZE_EMBEDDINGS = "stabilize_embeddings"

    # Gradient effects
    INCREASE_ENCODER_GRADIENT = "increase_enc_grad"
    DECREASE_ENCODER_GRADIENT = "decrease_enc_grad"
    BALANCE_GRADIENTS = "balance_gradients"

    # Learning effects
    INCREASE_LEARNING_RATE = "increase_lr"
    DECREASE_LEARNING_RATE = "decrease_lr"
    STABILIZE_LEARNING = "stabilize_learning"

    # Classification effects
    INCREASE_RECALL = "increase_recall"
    INCREASE_PRECISION = "increase_precision"
    REDUCE_FP = "reduce_fp"
    REDUCE_FN = "reduce_fn"

    # General effects
    PREVENT_OSCILLATION = "prevent_oscillation"
    ALLOW_EXPLORATION = "allow_exploration"
    NO_EXPECTED_EFFECT = "none"


# ============================================================================
# ADAPTIVE EVENT - A single variable change
# ============================================================================

@dataclass
class AdaptiveEvent:
    """
    A single adaptive variable change event.

    This captures everything needed to understand what changed, when, why,
    and what we expected to happen.
    """
    # Required fields
    variable: str                           # e.g., "spread_weight", "class_weight.pos"
    old_value: float
    new_value: float

    # Auto-computed
    delta: float = field(init=False)
    timestamp: datetime = field(default_factory=datetime.now)
    event_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    # Context (set by event group or explicitly)
    epoch: int = 0
    step: int = 0
    group_id: Optional[str] = None          # Links related changes

    # Attribution
    reason_code: ReasonCode = ReasonCode.MANUAL_OVERRIDE
    trigger_metric: Optional[str] = None
    trigger_value: Optional[float] = None
    metric_window: Optional[str] = None     # e.g., "last_200_steps", "last_1_epoch"

    # Controller info
    controller_name: str = "unknown"
    rule_id: Optional[str] = None           # Which specific rule fired

    # State tracking
    cooldown_applied: bool = False
    cooldown_remaining: int = 0

    # Expected outcome
    expected_effect: ExpectedEffect = ExpectedEffect.NO_EXPECTED_EFFECT

    # Optional metadata
    confidence: float = 1.0                 # 0-1 confidence score
    severity: float = 0.5                   # 0-1 severity (0=minor, 1=critical)
    notes: Optional[str] = None             # Keep bounded (max 200 chars)

    def __post_init__(self):
        self.delta = self.new_value - self.old_value
        if self.notes and len(self.notes) > 200:
            self.notes = self.notes[:197] + "..."

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'event_id': self.event_id,
            'timestamp': self.timestamp.isoformat(),
            'epoch': self.epoch,
            'step': self.step,
            'group_id': self.group_id,
            'variable': self.variable,
            'old_value': self.old_value,
            'new_value': self.new_value,
            'delta': self.delta,
            'reason_code': self.reason_code.value,
            'trigger_metric': self.trigger_metric,
            'trigger_value': self.trigger_value,
            'metric_window': self.metric_window,
            'controller_name': self.controller_name,
            'rule_id': self.rule_id,
            'cooldown_applied': self.cooldown_applied,
            'cooldown_remaining': self.cooldown_remaining,
            'expected_effect': self.expected_effect.value,
            'confidence': self.confidence,
            'severity': self.severity,
            'notes': self.notes,
        }


# ============================================================================
# EVENT GROUP - Batch of related changes
# ============================================================================

@dataclass
class EventGroup:
    """
    A batch of related adaptive events triggered by the same condition.

    When a single trigger (e.g., embedding collapse) causes multiple variable
    changes (spread_weight, diversity_weight, etc.), they share a group_id.
    """
    group_id: str
    epoch: int
    step: int
    controller_name: str
    reason_code: ReasonCode
    trigger_metric: str
    trigger_value: float
    metric_window: Optional[str] = None
    started_at: datetime = field(default_factory=datetime.now)
    ended_at: Optional[datetime] = None
    events: List[AdaptiveEvent] = field(default_factory=list)

    def add_event(self, event: AdaptiveEvent):
        """Add an event to this group."""
        event.group_id = self.group_id
        event.epoch = self.epoch
        event.step = self.step
        event.controller_name = self.controller_name
        event.reason_code = self.reason_code
        event.trigger_metric = self.trigger_metric
        event.trigger_value = self.trigger_value
        event.metric_window = self.metric_window
        self.events.append(event)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'group_id': self.group_id,
            'epoch': self.epoch,
            'step': self.step,
            'controller_name': self.controller_name,
            'reason_code': self.reason_code.value,
            'trigger_metric': self.trigger_metric,
            'trigger_value': self.trigger_value,
            'metric_window': self.metric_window,
            'started_at': self.started_at.isoformat(),
            'ended_at': self.ended_at.isoformat() if self.ended_at else None,
            'event_count': len(self.events),
            'events': [e.to_dict() for e in self.events],
        }


# ============================================================================
# ADAPTIVE EVENT LOG - The main log
# ============================================================================

class AdaptiveEventLog:
    """
    Centralized, append-only log of all adaptive variable changes.

    Features:
    - Event batching: Related changes share a group_id
    - Rate limiting: Prevents controller twitchiness
    - History analysis: Query what changed and when
    - Oscillation detection: Detects variables bouncing back and forth
    """

    # Rate limiting: minimum steps between events for the same variable
    MIN_STEPS_BETWEEN_EVENTS = 50

    # Maximum events to keep in memory
    MAX_EVENTS = 10000

    def __init__(self, run_id: str = None, seed: int = None,
                 git_sha: str = None, config_hash: str = None):
        """
        Initialize the event log.

        Args:
            run_id: Unique identifier for this training run
            seed: Random seed used
            git_sha: Git commit hash (for reproducibility)
            config_hash: Hash of the config (for reproducibility)
        """
        self.run_id = run_id or str(uuid.uuid4())[:12]
        self.seed = seed
        self.git_sha = git_sha
        self.config_hash = config_hash

        # Event storage
        self.events: List[AdaptiveEvent] = []
        self.groups: Dict[str, EventGroup] = {}

        # Rate limiting: track last event step per variable
        self._last_event_step: Dict[str, int] = {}

        # Active group (for batching)
        self._active_group: Optional[EventGroup] = None

        # Statistics
        self.total_events_emitted = 0
        self.total_events_rate_limited = 0
        self.events_by_controller: Dict[str, int] = {}
        self.events_by_reason: Dict[str, int] = {}

        logger.debug(f"AdaptiveEventLog initialized: run_id={self.run_id}")

    def start_event_group(
        self,
        epoch: int,
        step: int,
        controller_name: str,
        reason_code: ReasonCode,
        trigger_metric: str,
        trigger_value: float,
        metric_window: str = None
    ) -> str:
        """
        Start a new event group for batching related changes.

        Call this before emitting multiple events from the same trigger.
        Returns the group_id to pass to emitted events.
        """
        group_id = f"{controller_name[:8]}_{epoch}_{step}_{str(uuid.uuid4())[:4]}"

        self._active_group = EventGroup(
            group_id=group_id,
            epoch=epoch,
            step=step,
            controller_name=controller_name,
            reason_code=reason_code,
            trigger_metric=trigger_metric,
            trigger_value=trigger_value,
            metric_window=metric_window,
        )

        return group_id

    def end_event_group(self, group_id: str = None):
        """
        End the current event group.

        Finalizes the group and clears the active group state.
        """
        if self._active_group is None:
            return

        if group_id and self._active_group.group_id != group_id:
            logger.warning(f"Group ID mismatch: expected {group_id}, got {self._active_group.group_id}")

        self._active_group.ended_at = datetime.now()
        self.groups[self._active_group.group_id] = self._active_group

        # Log the group summary
        if self._active_group.events:
            variables = [e.variable for e in self._active_group.events]
            logger.debug(f"EventGroup {self._active_group.group_id}: "
                        f"{len(self._active_group.events)} events "
                        f"({', '.join(variables[:3])}{'...' if len(variables) > 3 else ''})")

        self._active_group = None

    def emit(self, event: AdaptiveEvent, force: bool = False) -> bool:
        """
        Emit an adaptive event to the log.

        Args:
            event: The event to emit
            force: If True, bypass rate limiting

        Returns:
            True if event was logged, False if rate-limited
        """
        # Rate limiting check
        if not force:
            last_step = self._last_event_step.get(event.variable, -999999)
            if event.step - last_step < self.MIN_STEPS_BETWEEN_EVENTS:
                self.total_events_rate_limited += 1
                return False

        # If we have an active group, add to it
        if self._active_group is not None:
            self._active_group.add_event(event)

        # Add run metadata
        # (event already has epoch, step, etc. from group or explicit setting)

        # Store event
        self.events.append(event)
        self._last_event_step[event.variable] = event.step

        # Update statistics
        self.total_events_emitted += 1
        self.events_by_controller[event.controller_name] = \
            self.events_by_controller.get(event.controller_name, 0) + 1
        self.events_by_reason[event.reason_code.value] = \
            self.events_by_reason.get(event.reason_code.value, 0) + 1

        # Trim if too many events
        if len(self.events) > self.MAX_EVENTS:
            self.events = self.events[-self.MAX_EVENTS:]

        return True

    def emit_simple(
        self,
        variable: str,
        old_value: float,
        new_value: float,
        epoch: int,
        step: int,
        controller_name: str,
        reason_code: ReasonCode,
        trigger_metric: str = None,
        trigger_value: float = None,
        expected_effect: ExpectedEffect = ExpectedEffect.NO_EXPECTED_EFFECT,
        notes: str = None,
        force: bool = False
    ) -> bool:
        """
        Convenience method to emit a simple event without creating an AdaptiveEvent object.
        """
        event = AdaptiveEvent(
            variable=variable,
            old_value=old_value,
            new_value=new_value,
            epoch=epoch,
            step=step,
            controller_name=controller_name,
            reason_code=reason_code,
            trigger_metric=trigger_metric,
            trigger_value=trigger_value,
            expected_effect=expected_effect,
            notes=notes,
        )
        return self.emit(event, force=force)

    # ========================================================================
    # QUERY METHODS
    # ========================================================================

    def get_events_for_variable(self, variable: str, last_n: Optional[int] = None) -> List[AdaptiveEvent]:
        """Get all events for a specific variable."""
        events = [e for e in self.events if e.variable == variable]
        if last_n is not None and last_n > 0:
            events = events[len(events) - last_n:]
        return events

    def get_events_in_epoch(self, epoch: int) -> List[AdaptiveEvent]:
        """Get all events in a specific epoch."""
        return [e for e in self.events if e.epoch == epoch]

    def get_events_by_controller(self, controller_name: str) -> List[AdaptiveEvent]:
        """Get all events from a specific controller."""
        return [e for e in self.events if e.controller_name == controller_name]

    def get_events_by_reason(self, reason_code: ReasonCode) -> List[AdaptiveEvent]:
        """Get all events with a specific reason code."""
        return [e for e in self.events if e.reason_code == reason_code]

    def detect_oscillation(self, variable: str, window: int = 10) -> Dict[str, Any]:
        """
        Detect if a variable is oscillating (bouncing back and forth).

        Returns dict with:
        - oscillating: bool
        - sign_changes: int (direction reversals in window)
        - avg_magnitude: float (average |delta|)
        """
        events = self.get_events_for_variable(variable, last_n=window)
        if len(events) < 3:
            return {'oscillating': False, 'sign_changes': 0, 'avg_magnitude': 0.0}

        deltas = [e.delta for e in events]
        sign_changes = sum(1 for i in range(1, len(deltas))
                         if deltas[i] * deltas[i-1] < 0)
        avg_magnitude = sum(abs(d) for d in deltas) / len(deltas)

        # Oscillating if >50% of changes are reversals
        oscillating = sign_changes >= len(deltas) * 0.5

        return {
            'oscillating': oscillating,
            'sign_changes': sign_changes,
            'avg_magnitude': avg_magnitude,
            'window_size': len(events),
        }

    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics for the log."""
        return {
            'run_id': self.run_id,
            'total_events': len(self.events),
            'total_emitted': self.total_events_emitted,
            'total_rate_limited': self.total_events_rate_limited,
            'events_by_controller': dict(self.events_by_controller),
            'events_by_reason': dict(self.events_by_reason),
            'unique_variables': len(set(e.variable for e in self.events)),
            'total_groups': len(self.groups),
        }

    def to_list(self) -> List[Dict[str, Any]]:
        """Export all events as a list of dicts."""
        return [e.to_dict() for e in self.events]


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

_ADAPTIVE_EVENT_LOG: Optional[AdaptiveEventLog] = None


def get_adaptive_event_log() -> AdaptiveEventLog:
    """Get or create the global adaptive event log."""
    global _ADAPTIVE_EVENT_LOG
    if _ADAPTIVE_EVENT_LOG is None:
        _ADAPTIVE_EVENT_LOG = AdaptiveEventLog()
    return _ADAPTIVE_EVENT_LOG


def set_adaptive_event_log(log: AdaptiveEventLog):
    """Set the global adaptive event log (e.g., with run metadata)."""
    global _ADAPTIVE_EVENT_LOG
    _ADAPTIVE_EVENT_LOG = log


def reset_adaptive_event_log():
    """Reset the global log (for testing or new runs)."""
    global _ADAPTIVE_EVENT_LOG
    _ADAPTIVE_EVENT_LOG = None
