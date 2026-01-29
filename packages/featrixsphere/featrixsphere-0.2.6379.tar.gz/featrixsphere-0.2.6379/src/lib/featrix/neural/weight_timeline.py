"""
Weight Timeline - Adaptive Loss Weight Scheduling Based on Embedding Health

Manages loss weights (spread, marginal, joint) and diversity loss parameters
dynamically based on embedding space health metrics.

Key insight: Time-based curriculum learning fails when embeddings collapse early.
This system uses condition-based control - adjusting weights based on actual
embedding health (std/dim) rather than fixed epoch schedules.

Thresholds:
- Target std/dim: 0.04 (healthy embeddings)
- Warning: < 0.035 (nudge spread weight up gradually)
- Emergency: < 0.02 (aggressive intervention)

Like LRTimeline, changes are applied smoothly over windows to avoid shocks.
"""
import math
import logging
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Tuple, Any
from enum import Enum

from featrix.neural.timeline_events import post_timeline_event
from featrix.neural.adaptive_event_log import (
    AdaptiveEvent,
    ExpectedEffect,
    ReasonCode,
    get_adaptive_event_log,
)

logger = logging.getLogger(__name__)


class EmbeddingHealthZone(Enum):
    """Embedding health classification based on std/dim."""
    RANDOM = "random"        # >= 0.055: embeddings still look random, not learning structure
    HEALTHY = "healthy"      # 0.04-0.055: embeddings well-spread AND learning structure
    RECOVERING = "recovering"  # 0.035-0.04: improving but not there yet
    WARNING = "warning"      # 0.02-0.035: concerning, need intervention
    EMERGENCY = "emergency"  # < 0.02: critical, aggressive action needed


@dataclass
class WeightState:
    """Current state of all managed weights."""
    spread_weight: float = 1.0
    marginal_weight: float = 0.25
    joint_weight: float = 1.0

    # Diversity loss parameters
    diversity_temperature: float = 0.1
    diversity_weight: float = 1.0

    # Separation loss weight (anti-collapse: penalizes high off-diagonal similarity)
    # Warmup schedule: high during first 10% of epochs, then cosine decay with floor
    separation_weight: float = 1.0

    def to_dict(self) -> Dict[str, float]:
        return {
            'spread_weight': self.spread_weight,
            'marginal_weight': self.marginal_weight,
            'joint_weight': self.joint_weight,
            'diversity_temperature': self.diversity_temperature,
            'diversity_weight': self.diversity_weight,
            'separation_weight': self.separation_weight,
        }


@dataclass
class WeightAdjustment:
    """Record of a weight adjustment event."""
    epoch: int
    trigger: str  # 'health_warning', 'health_emergency', 'health_recovery', 'manual'
    zone: EmbeddingHealthZone
    std_dim: float
    old_weights: WeightState
    new_weights: WeightState
    reason: str


@dataclass
class ActiveNudge:
    """An active gradual weight adjustment in progress."""
    start_epoch: int
    duration: int  # epochs
    weight_name: str  # 'spread_weight', 'marginal_weight', etc.
    start_value: float
    target_value: float
    reason: str
    nudge_type: str  # 'increase' or 'decrease'


class WeightTimeline:
    """
    Adaptive loss weight scheduler based on embedding health.

    Unlike time-based curriculum learning, this responds to actual embedding
    conditions. If embeddings start collapsing, it increases spread weight
    to counteract. If embeddings are healthy, it allows focus on reconstruction.

    All changes are applied gradually (like LRTimeline boosts) to avoid
    destabilizing training.

    Stacking limits:
    - Maximum consecutive increases before requiring recovery: MAX_CONSECUTIVE_INCREASES
    - Each adjustment waits for previous nudge to complete before stacking
    - This prevents runaway weight escalation
    """

    # Health thresholds
    TARGET_STD_DIM = 0.04
    WARNING_THRESHOLD = 0.035
    EMERGENCY_THRESHOLD = 0.02
    # Random initialization threshold - embeddings near this value aren't learning
    RANDOM_THRESHOLD = 0.057

    # Weight bounds
    MIN_SPREAD_WEIGHT = 1.0
    MAX_SPREAD_WEIGHT = 20.0
    MIN_MARGINAL_WEIGHT = 0.1
    MAX_MARGINAL_WEIGHT = 1.0
    MIN_JOINT_WEIGHT = 0.5
    MAX_JOINT_WEIGHT = 15.0  # High enough to force structure learning

    # Diversity loss bounds
    MIN_DIVERSITY_TEMP = 0.05
    MAX_DIVERSITY_TEMP = 0.5
    MIN_DIVERSITY_WEIGHT = 0.5
    MAX_DIVERSITY_WEIGHT = 5.0

    # Stacking limits - prevent runaway escalation
    MAX_CONSECUTIVE_INCREASES = 4  # Max times we can increase before requiring recovery
    MAX_CONSECUTIVE_DECREASES = 3  # Max times we can decrease before stabilizing

    def __init__(
        self,
        n_epochs: int,
        initial_spread_weight: float = 5.0,
        initial_marginal_weight: float = 0.25,
        initial_joint_weight: float = 10.0,  # Start high to force structure learning
        initial_diversity_temperature: float = 0.1,
        initial_diversity_weight: float = 1.0,
        # Separation loss warmup parameters
        initial_separation_weight: float = 5.0,  # Start high for warmup (anti-collapse)
        separation_warmup_pct: float = 0.10,  # 10% of epochs at full strength
        separation_floor: float = 0.5,  # Minimum weight after decay (keeps some anti-collapse)
        # Adjustment parameters
        nudge_window_pct: float = 0.05,  # 5% of epochs for gradual changes
        min_nudge_window: int = 3,  # minimum 3 epochs for any adjustment
        # Health check frequency
        check_frequency: int = 1,  # check every epoch by default
        # Response aggressiveness
        warning_response_factor: float = 1.2,  # 20% adjustment per warning
        emergency_response_factor: float = 1.5,  # 50% adjustment in emergency
        recovery_response_factor: float = 0.95,  # 5% reduction when healthy
    ):
        """
        Initialize weight timeline.

        Args:
            n_epochs: Total training epochs
            initial_*: Starting values for each weight/parameter
            nudge_window_pct: Fraction of epochs for gradual adjustments
            min_nudge_window: Minimum epochs for any adjustment window
            check_frequency: How often to check embedding health (epochs)
            warning_response_factor: Multiplier for warning-level adjustments
            emergency_response_factor: Multiplier for emergency adjustments
            recovery_response_factor: Multiplier when recovering (< 1 to reduce)
        """
        self.n_epochs = n_epochs
        self.check_frequency = check_frequency

        # Response factors
        self.warning_response_factor = warning_response_factor
        self.emergency_response_factor = emergency_response_factor
        self.recovery_response_factor = recovery_response_factor

        # Calculate nudge window size
        self.nudge_window = max(min_nudge_window, int(n_epochs * nudge_window_pct))

        # Separation loss warmup schedule parameters
        self.initial_separation_weight = initial_separation_weight
        self.separation_warmup_pct = separation_warmup_pct
        self.separation_floor = separation_floor
        self.separation_warmup_epochs = max(1, int(n_epochs * separation_warmup_pct))

        # Initialize baseline weights
        self.baseline_weights = WeightState(
            spread_weight=initial_spread_weight,
            marginal_weight=initial_marginal_weight,
            joint_weight=initial_joint_weight,
            diversity_temperature=initial_diversity_temperature,
            diversity_weight=initial_diversity_weight,
            separation_weight=initial_separation_weight,  # Start at warmup level
        )

        # Current effective weights (baseline + active nudges)
        self.current_weights = WeightState(
            spread_weight=initial_spread_weight,
            marginal_weight=initial_marginal_weight,
            joint_weight=initial_joint_weight,
            diversity_temperature=initial_diversity_temperature,
            diversity_weight=initial_diversity_weight,
            separation_weight=initial_separation_weight,
        )

        # Active nudges (gradual adjustments in progress)
        self.active_nudges: List[ActiveNudge] = []

        # History tracking
        self.adjustments: List[WeightAdjustment] = []
        self.health_history: Dict[int, Tuple[float, EmbeddingHealthZone]] = {}
        self.weight_history: Dict[int, WeightState] = {}

        # Current epoch
        self.current_epoch = 0

        # Track consecutive epochs in each zone for hysteresis
        self.consecutive_random_epochs = 0
        self.consecutive_warning_epochs = 0
        self.consecutive_emergency_epochs = 0
        self.consecutive_healthy_epochs = 0

        # Cooldown to prevent oscillation
        self.last_adjustment_epoch = -10  # Allow immediate first adjustment
        self.adjustment_cooldown = max(3, self.nudge_window // 2)

        # Track consecutive adjustments to prevent runaway stacking
        self.consecutive_increases = 0  # How many increases without recovery
        self.consecutive_decreases = 0  # How many decreases without stabilizing

        # Gradient flow tracking for suppression detection
        self._gradient_flow_history: List[Dict[str, Any]] = []
        self._last_gradient_adjustment_epoch = -10
        self._gradient_suppression_responses = 0

        # Current step (for event logging)
        self._current_step = 0

        # Enable/disable event emission
        self._emit_events = True

        logger.info("⚖️ WeightTimeline Initialized:")
        logger.info(f"   Total epochs: {n_epochs}")
        logger.info(f"   Nudge window: {self.nudge_window} epochs")
        logger.info(f"   Health thresholds: random>={self.RANDOM_THRESHOLD - 0.002}, healthy>={self.TARGET_STD_DIM}, "
                   f"warning<{self.WARNING_THRESHOLD}, emergency<{self.EMERGENCY_THRESHOLD}")
        logger.info(f"   Initial weights: spread={initial_spread_weight}, "
                   f"marginal={initial_marginal_weight}, joint={initial_joint_weight} (high to force structure)")
        logger.info(f"   Diversity: temp={initial_diversity_temperature}, weight={initial_diversity_weight}")

    def classify_health(self, std_dim: float) -> EmbeddingHealthZone:
        """Classify embedding health based on std/dim value.

        Key insight: High std/dim near RANDOM_THRESHOLD means embeddings
        aren't learning structure - they still look like random initialization.
        We want std/dim to DROP below random as structure is learned.
        """
        if std_dim >= self.RANDOM_THRESHOLD - 0.002:  # ~0.055+: still random
            return EmbeddingHealthZone.RANDOM
        elif std_dim >= self.TARGET_STD_DIM:  # 0.04-0.055: healthy AND structured
            return EmbeddingHealthZone.HEALTHY
        elif std_dim >= self.WARNING_THRESHOLD:
            return EmbeddingHealthZone.RECOVERING
        elif std_dim >= self.EMERGENCY_THRESHOLD:
            return EmbeddingHealthZone.WARNING
        else:
            return EmbeddingHealthZone.EMERGENCY

    def get_separation_weight_for_epoch(self, epoch: int) -> float:
        """
        Compute separation weight for the given epoch using warmup + cosine decay schedule.

        Schedule:
        - Epochs 0 to warmup_epochs: Full weight (initial_separation_weight)
        - Epochs warmup_epochs to n_epochs: Cosine decay from initial to floor
        - Always at least separation_floor to maintain some anti-collapse pressure

        Args:
            epoch: Current epoch number

        Returns:
            Separation weight for this epoch
        """
        if epoch < self.separation_warmup_epochs:
            # Warmup phase: full weight
            return self.initial_separation_weight

        # Decay phase: cosine annealing from initial to floor
        decay_epochs = self.n_epochs - self.separation_warmup_epochs
        if decay_epochs <= 0:
            return self.separation_floor

        # Progress through decay phase (0 to 1)
        decay_progress = (epoch - self.separation_warmup_epochs) / decay_epochs
        decay_progress = min(1.0, decay_progress)  # Clamp to 1.0

        # Cosine decay: starts at 1, ends at 0, with smooth transition
        # Add small "wiggle" by not going all the way to floor
        cosine_factor = 0.5 * (1 + math.cos(math.pi * decay_progress))

        # Interpolate between initial and floor
        weight = self.separation_floor + (self.initial_separation_weight - self.separation_floor) * cosine_factor

        return weight

    def update(self, epoch: int, std_dim: float) -> WeightState:
        """
        Update weights based on current embedding health.

        This is the main entry point - call once per epoch with the current
        embedding std/dim measurement.

        Args:
            epoch: Current epoch number
            std_dim: Current embedding std per dimension

        Returns:
            Current effective weights to use for this epoch
        """
        self.current_epoch = epoch

        # Classify health
        zone = self.classify_health(std_dim)
        self.health_history[epoch] = (std_dim, zone)

        # Update consecutive counters
        self._update_consecutive_counters(zone)

        # Check if we should make an adjustment
        if epoch % self.check_frequency == 0:
            self._maybe_adjust_weights(epoch, std_dim, zone)

        # Apply active nudges to get current effective weights
        self._apply_active_nudges(epoch)

        # Apply separation weight schedule (warmup + cosine decay)
        self.current_weights.separation_weight = self.get_separation_weight_for_epoch(epoch)

        # Record weight history
        self.weight_history[epoch] = WeightState(
            spread_weight=self.current_weights.spread_weight,
            marginal_weight=self.current_weights.marginal_weight,
            joint_weight=self.current_weights.joint_weight,
            diversity_temperature=self.current_weights.diversity_temperature,
            diversity_weight=self.current_weights.diversity_weight,
            separation_weight=self.current_weights.separation_weight,
        )

        return self.current_weights

    def update_with_gradient_flow(
        self,
        epoch: int,
        std_dim: float,
        gradient_flow_result: Dict[str, Any],
        step: int = None
    ) -> WeightState:
        """
        Update weights based on embedding health AND gradient flow.

        This extends the standard update() to also respond to gradient suppression.
        Call this instead of update() when gradient flow data is available.

        Args:
            epoch: Current epoch number
            std_dim: Current embedding std per dimension
            gradient_flow_result: Result from GradientFlowTracker.update()
            step: Current global optimizer step (for event logging)

        Returns:
            Current effective weights to use for this epoch
        """
        if step is not None:
            self._current_step = step

        # First, do the standard embedding health update
        weights = self.update(epoch, std_dim)

        # Store gradient flow data
        self._gradient_flow_history.append({
            'epoch': epoch,
            'step': step,
            **gradient_flow_result
        })
        if len(self._gradient_flow_history) > 200:
            self._gradient_flow_history = self._gradient_flow_history[-200:]

        # Check for gradient suppression response
        if gradient_flow_result.get('suppression_detected', False):
            # Check cooldown (don't respond too frequently)
            gradient_cooldown = max(5, self.adjustment_cooldown)
            if epoch - self._last_gradient_adjustment_epoch >= gradient_cooldown:
                self._respond_to_gradient_suppression(
                    epoch, std_dim, gradient_flow_result
                )

        # Check recovery status from gradient flow
        recovery_status = gradient_flow_result.get('recovery_status', 'n/a')
        if recovery_status == 'suppressed':
            # Gradients failed to recover after our adjustment
            # This is the "controller killing learning" scenario
            logger.warning(
                f"⚠️  [epoch={epoch}] Gradient recovery FAILED after weight adjustment. "
                f"Controller may be over-stabilizing."
            )
            # Emit event for this critical situation
            if self._emit_events:
                log = get_adaptive_event_log()
                log.emit_simple(
                    variable="gradient_flow.recovery_failed",
                    old_value=1.0,
                    new_value=0.0,
                    epoch=epoch,
                    step=self._current_step,
                    controller_name="WeightTimeline",
                    reason_code=ReasonCode.ENCODER_GRADIENT_SUPPRESSED,
                    trigger_metric="recovery_status",
                    trigger_value=0.0,
                    expected_effect=ExpectedEffect.STABILIZE_LEARNING,
                    notes="Weight adjustment failed to restore encoder gradients",
                    force=True,
                )

        return weights

    def _respond_to_gradient_suppression(
        self,
        epoch: int,
        std_dim: float,
        gradient_flow_result: Dict[str, Any]
    ) -> None:
        """
        Respond to detected gradient suppression.

        When encoder gradients are suppressed, we need to:
        1. Reduce spread weight (less aggressive spread enforcement)
        2. Increase marginal weight (more reconstruction signal)

        This is the opposite of embedding collapse response!
        """
        suppression_type = gradient_flow_result.get('suppression_type', 'encoder')
        encoder_ratio = gradient_flow_result.get('encoder_suppression_ratio', 1.0)

        # Only respond to encoder suppression (predictor suppression is less critical)
        if suppression_type not in ('encoder', 'both'):
            return

        # Check stacking limit
        if self._gradient_suppression_responses >= 2:
            if epoch % 10 == 0:
                logger.warning(
                    f"⚠️ [epoch={epoch}] Gradient suppression detected but at response limit "
                    f"({self._gradient_suppression_responses})"
                )
            return

        old_spread = self.baseline_weights.spread_weight
        old_marginal = self.baseline_weights.marginal_weight

        # Reduce spread weight (less aggressive = more gradient to encoder)
        new_spread = max(
            old_spread * 0.85,  # 15% reduction
            self.MIN_SPREAD_WEIGHT
        )

        # Increase marginal weight (more reconstruction signal)
        new_marginal = min(
            old_marginal * 1.15,  # 15% increase
            self.MAX_MARGINAL_WEIGHT
        )

        # Only adjust if meaningful change
        if abs(new_spread - old_spread) < 0.1 and abs(new_marginal - old_marginal) < 0.01:
            return

        # Create nudges
        gradient_window = max(3, self.nudge_window // 2)  # Faster response
        self._create_nudge(epoch, 'spread_weight', new_spread, gradient_window,
                          'gradient_suppression_spread_decrease')
        self._create_nudge(epoch, 'marginal_weight', new_marginal, gradient_window,
                          'gradient_suppression_marginal_increase')

        # Update baseline
        self.baseline_weights.spread_weight = new_spread
        self.baseline_weights.marginal_weight = new_marginal

        self._last_gradient_adjustment_epoch = epoch
        self._gradient_suppression_responses += 1

        logger.warning(
            f"🔧 [epoch={epoch}] Gradient suppression response ({self._gradient_suppression_responses}/2): "
            f"encoder_ratio={encoder_ratio:.3f}"
        )
        logger.warning(f"   spread: {old_spread:.2f} → {new_spread:.2f} (↓ reduce encoder pressure)")
        logger.warning(f"   marginal: {old_marginal:.3f} → {new_marginal:.3f} (↑ more reconstruction signal)")

        # Emit events
        if self._emit_events:
            self._emit_adjustment_events(
                epoch=epoch,
                reason_code=ReasonCode.ENCODER_GRADIENT_SUPPRESSED,
                trigger_metric="encoder_suppression_ratio",
                trigger_value=encoder_ratio,
                changes=[
                    ("spread_weight", old_spread, new_spread, ExpectedEffect.INCREASE_ENCODER_GRADIENT),
                    ("marginal_weight", old_marginal, new_marginal, ExpectedEffect.INCREASE_ENCODER_GRADIENT),
                ],
                notes=f"Gradient suppression type: {suppression_type}"
            )

        # Post to timeline
        post_timeline_event({
            'epoch': epoch,
            'event_type': 'gradient_suppression_response',
            'suppression_type': suppression_type,
            'encoder_ratio': encoder_ratio,
            'spread_old': old_spread,
            'spread_new': new_spread,
            'marginal_old': old_marginal,
            'marginal_new': new_marginal,
        })

    def _emit_adjustment_events(
        self,
        epoch: int,
        reason_code: ReasonCode,
        trigger_metric: str,
        trigger_value: float,
        changes: List[Tuple[str, float, float, ExpectedEffect]],
        notes: str = None
    ) -> None:
        """
        Emit events to AdaptiveEventLog for weight adjustments.

        Args:
            epoch: Current epoch
            reason_code: Why this adjustment is happening
            trigger_metric: What metric triggered this
            trigger_value: Value of the trigger metric
            changes: List of (variable, old_value, new_value, expected_effect) tuples
            notes: Optional notes
        """
        if not self._emit_events:
            return

        log = get_adaptive_event_log()

        # Start an event group for this batch of changes
        group_id = log.start_event_group(
            epoch=epoch,
            step=self._current_step,
            controller_name="WeightTimeline",
            reason_code=reason_code,
            trigger_metric=trigger_metric,
            trigger_value=trigger_value,
            metric_window="last_1_epoch",
        )

        # Emit individual variable changes
        for variable, old_val, new_val, expected_effect in changes:
            log.emit(AdaptiveEvent(
                variable=variable,
                old_value=old_val,
                new_value=new_val,
                epoch=epoch,
                step=self._current_step,
                expected_effect=expected_effect,
                cooldown_applied=epoch - self.last_adjustment_epoch < self.adjustment_cooldown,
                cooldown_remaining=max(0, self.adjustment_cooldown - (epoch - self.last_adjustment_epoch)),
                notes=notes,
            ))

        # End the group
        log.end_event_group(group_id)

    def set_step(self, step: int) -> None:
        """Set current optimizer step for event logging."""
        self._current_step = step

    def _update_consecutive_counters(self, zone: EmbeddingHealthZone) -> None:
        """Update consecutive epoch counters for hysteresis."""
        if zone == EmbeddingHealthZone.RANDOM:
            self.consecutive_random_epochs += 1
            self.consecutive_healthy_epochs = 0
            self.consecutive_warning_epochs = 0
            self.consecutive_emergency_epochs = 0
        elif zone == EmbeddingHealthZone.HEALTHY:
            self.consecutive_healthy_epochs += 1
            self.consecutive_random_epochs = 0
            self.consecutive_warning_epochs = 0
            self.consecutive_emergency_epochs = 0
        elif zone == EmbeddingHealthZone.RECOVERING:
            # Recovering counts as partial healthy
            self.consecutive_healthy_epochs += 0.5
            self.consecutive_random_epochs = 0
            self.consecutive_warning_epochs = 0
            self.consecutive_emergency_epochs = 0
        elif zone == EmbeddingHealthZone.WARNING:
            self.consecutive_warning_epochs += 1
            self.consecutive_random_epochs = 0
            self.consecutive_healthy_epochs = 0
            self.consecutive_emergency_epochs = 0
        else:  # EMERGENCY
            self.consecutive_emergency_epochs += 1
            self.consecutive_random_epochs = 0
            self.consecutive_warning_epochs = 0
            self.consecutive_healthy_epochs = 0

    def _maybe_adjust_weights(
        self,
        epoch: int,
        std_dim: float,
        zone: EmbeddingHealthZone
    ) -> None:
        """Decide whether to make a weight adjustment based on health zone."""

        # Check cooldown
        if epoch - self.last_adjustment_epoch < self.adjustment_cooldown:
            return

        # Check if there are active nudges still in progress for spread_weight
        # Don't stack new adjustments until the current one completes
        spread_nudge_active = any(
            n.weight_name == 'spread_weight' and epoch < n.start_epoch + n.duration
            for n in self.active_nudges
        )
        if spread_nudge_active:
            return

        # RANDOM zone: embeddings aren't learning structure - keep joint weight HIGH
        if zone == EmbeddingHealthZone.RANDOM:
            self._respond_to_random(epoch, std_dim)
            return

        # Emergency: respond immediately (unless we've hit stacking limit)
        if zone == EmbeddingHealthZone.EMERGENCY:
            if self.consecutive_increases < self.MAX_CONSECUTIVE_INCREASES:
                self._respond_to_emergency(epoch, std_dim)
            else:
                # Hit max increases - log but don't escalate further
                if epoch % 10 == 0:  # Log periodically
                    logger.warning(f"⚠️ [epoch={epoch}] Emergency but at max increases ({self.consecutive_increases}), "
                                  f"waiting for recovery. spread_weight={self.baseline_weights.spread_weight:.2f}")
            return

        # Warning: respond after consecutive epochs (hysteresis)
        if zone == EmbeddingHealthZone.WARNING and self.consecutive_warning_epochs >= 2:
            if self.consecutive_increases < self.MAX_CONSECUTIVE_INCREASES:
                self._respond_to_warning(epoch, std_dim)
            return

        # Healthy: embeddings have learned structure - can relax joint weight
        if zone == EmbeddingHealthZone.HEALTHY and self.consecutive_healthy_epochs >= 3:
            # Reduce joint weight if it's elevated (structure is learned)
            if self.baseline_weights.joint_weight > 5.0:
                self._respond_to_structure_learned(epoch, std_dim)
            # Also reduce spread weight if elevated
            elif self.baseline_weights.spread_weight > 5.0:
                if self.consecutive_decreases < self.MAX_CONSECUTIVE_DECREASES:
                    self._respond_to_recovery(epoch, std_dim)
            return

        # Reset decrease counter if we're healthy but not decreasing
        if zone == EmbeddingHealthZone.HEALTHY:
            # We're healthy and not above default - reset increase counter
            if self.baseline_weights.spread_weight <= 5.0:
                self.consecutive_increases = 0

    def _respond_to_random(self, epoch: int, std_dim: float) -> None:
        """
        Response when embeddings are still near random initialization.

        When std/dim is near RANDOM_THRESHOLD (~0.057), the embeddings haven't
        learned meaningful structure yet. Keep joint weight HIGH to force the
        joint encoder to create structure.

        This is NOT an emergency - it's expected early in training. We just
        need to ensure joint weight stays high until structure emerges.
        """
        old_joint = self.baseline_weights.joint_weight

        # If joint weight has dropped below 8, push it back up
        # (it started at 10, we want to keep it high while still random)
        if old_joint < 8.0:
            new_joint = min(old_joint * 1.25, 12.0)  # Increase by 25%, cap at 12

            random_window = max(3, self.nudge_window)
            self._create_nudge(epoch, 'joint_weight', new_joint, random_window,
                              'random_joint_increase')
            self.baseline_weights.joint_weight = new_joint

            logger.info(f"🎲 [epoch={epoch}] Embeddings still random (std/dim={std_dim:.4f}): "
                       f"joint_weight {old_joint:.1f} → {new_joint:.1f}")

            # Post to timeline
            post_timeline_event({
                'epoch': epoch,
                'event_type': 'random_response',
                'std_dim': std_dim,
                'joint_old': old_joint,
                'joint_new': new_joint,
            })

            self.last_adjustment_epoch = epoch
        else:
            # Joint weight is already high enough, just log occasionally
            if epoch % 20 == 0:
                logger.debug(f"🎲 [epoch={epoch}] Embeddings still random (std/dim={std_dim:.4f}), "
                           f"joint_weight={old_joint:.1f} (keeping high)")

    def _respond_to_structure_learned(self, epoch: int, std_dim: float) -> None:
        """
        Response when embeddings have learned structure (dropped below random).

        When std/dim drops well below RANDOM_THRESHOLD into the HEALTHY zone,
        it means the joint encoder has successfully created structure. We can
        now gradually reduce joint weight to let fine-tuning proceed.
        """
        old_joint = self.baseline_weights.joint_weight

        # Gradually reduce joint weight toward a moderate level (5.0)
        # Don't drop too fast - we still need some structure enforcement
        new_joint = max(
            old_joint * 0.9,  # 10% reduction
            5.0  # Don't go below 5.0
        )

        # Only adjust if meaningful change
        if abs(new_joint - old_joint) < 0.3:
            return

        structure_window = int(self.nudge_window * 1.5)  # Slower adjustment
        self._create_nudge(epoch, 'joint_weight', new_joint, structure_window,
                          'structure_learned_joint_decrease')
        self.baseline_weights.joint_weight = new_joint

        logger.info(f"✨ [epoch={epoch}] Structure learned (std/dim={std_dim:.4f}): "
                   f"joint_weight {old_joint:.1f} → {new_joint:.1f}")

        # Post to timeline
        post_timeline_event({
            'epoch': epoch,
            'event_type': 'structure_learned',
            'std_dim': std_dim,
            'joint_old': old_joint,
            'joint_new': new_joint,
        })

        self.last_adjustment_epoch = epoch
        self.consecutive_decreases += 1

    def _respond_to_emergency(self, epoch: int, std_dim: float) -> None:
        """Aggressive response to emergency (std < 0.02)."""
        old_weights = WeightState(
            spread_weight=self.baseline_weights.spread_weight,
            marginal_weight=self.baseline_weights.marginal_weight,
            joint_weight=self.baseline_weights.joint_weight,
            diversity_temperature=self.baseline_weights.diversity_temperature,
            diversity_weight=self.baseline_weights.diversity_weight,
        )

        # Increase spread weight aggressively
        new_spread = min(
            self.baseline_weights.spread_weight * self.emergency_response_factor,
            self.MAX_SPREAD_WEIGHT
        )

        # Increase diversity weight
        new_diversity_weight = min(
            self.baseline_weights.diversity_weight * 1.3,
            self.MAX_DIVERSITY_WEIGHT
        )

        # Decrease diversity temperature (sharper gradients)
        new_diversity_temp = max(
            self.baseline_weights.diversity_temperature * 0.8,
            self.MIN_DIVERSITY_TEMP
        )

        # Decrease marginal weight (focus on spread)
        new_marginal = max(
            self.baseline_weights.marginal_weight * 0.8,
            self.MIN_MARGINAL_WEIGHT
        )

        # Create nudges for gradual transitions
        # Use shorter window for emergency (faster response)
        emergency_window = max(2, self.nudge_window // 2)

        self._create_nudge(epoch, 'spread_weight', new_spread, emergency_window,
                          'emergency_spread_increase')
        self._create_nudge(epoch, 'diversity_weight', new_diversity_weight, emergency_window,
                          'emergency_diversity_increase')
        self._create_nudge(epoch, 'diversity_temperature', new_diversity_temp, emergency_window,
                          'emergency_temp_decrease')
        self._create_nudge(epoch, 'marginal_weight', new_marginal, emergency_window,
                          'emergency_marginal_decrease')

        # Update baseline (this is where we want to be after nudge completes)
        self.baseline_weights.spread_weight = new_spread
        self.baseline_weights.diversity_weight = new_diversity_weight
        self.baseline_weights.diversity_temperature = new_diversity_temp
        self.baseline_weights.marginal_weight = new_marginal

        new_weights = WeightState(
            spread_weight=new_spread,
            marginal_weight=new_marginal,
            joint_weight=self.baseline_weights.joint_weight,
            diversity_temperature=new_diversity_temp,
            diversity_weight=new_diversity_weight,
        )

        # Record adjustment
        self.adjustments.append(WeightAdjustment(
            epoch=epoch,
            trigger='health_emergency',
            zone=EmbeddingHealthZone.EMERGENCY,
            std_dim=std_dim,
            old_weights=old_weights,
            new_weights=new_weights,
            reason=f"Emergency: std/dim={std_dim:.4f} < {self.EMERGENCY_THRESHOLD}"
        ))

        self.last_adjustment_epoch = epoch
        self.consecutive_emergency_epochs = 0

        # Track consecutive increases for stacking limit
        self.consecutive_increases += 1
        self.consecutive_decreases = 0  # Reset decrease counter

        logger.warning(f"🚨 [epoch={epoch}] EMERGENCY weight adjustment ({self.consecutive_increases}/{self.MAX_CONSECUTIVE_INCREASES}): std/dim={std_dim:.4f}")
        logger.warning(f"   spread: {old_weights.spread_weight:.2f} → {new_spread:.2f}")
        logger.warning(f"   diversity_weight: {old_weights.diversity_weight:.2f} → {new_diversity_weight:.2f}")
        logger.warning(f"   diversity_temp: {old_weights.diversity_temperature:.3f} → {new_diversity_temp:.3f}")
        logger.warning(f"   marginal: {old_weights.marginal_weight:.3f} → {new_marginal:.3f}")

        # Post to timeline
        post_timeline_event({
            'epoch': epoch,
            'event_type': 'weight_adjustment',
            'zone': 'emergency',
            'std_dim': std_dim,
            'spread_old': old_weights.spread_weight,
            'spread_new': new_spread,
            'marginal_old': old_weights.marginal_weight,
            'marginal_new': new_marginal,
        })

        # Emit to AdaptiveEventLog
        if self._emit_events:
            self._emit_adjustment_events(
                epoch=epoch,
                reason_code=ReasonCode.EMBEDDING_COLLAPSE,
                trigger_metric="std_per_dim",
                trigger_value=std_dim,
                changes=[
                    ("spread_weight", old_weights.spread_weight, new_spread, ExpectedEffect.INCREASE_SPREAD),
                    ("marginal_weight", old_weights.marginal_weight, new_marginal, ExpectedEffect.DECREASE_SPREAD),
                    ("diversity_weight", old_weights.diversity_weight, new_diversity_weight, ExpectedEffect.INCREASE_SPREAD),
                    ("diversity_temperature", old_weights.diversity_temperature, new_diversity_temp, ExpectedEffect.INCREASE_SPREAD),
                ],
                notes=f"Emergency: std/dim={std_dim:.4f} < {self.EMERGENCY_THRESHOLD}"
            )

    def _respond_to_warning(self, epoch: int, std_dim: float) -> None:
        """Moderate response to warning (std 0.02-0.035)."""
        old_weights = WeightState(
            spread_weight=self.baseline_weights.spread_weight,
            marginal_weight=self.baseline_weights.marginal_weight,
            joint_weight=self.baseline_weights.joint_weight,
            diversity_temperature=self.baseline_weights.diversity_temperature,
            diversity_weight=self.baseline_weights.diversity_weight,
        )

        # Increase spread weight moderately
        new_spread = min(
            self.baseline_weights.spread_weight * self.warning_response_factor,
            self.MAX_SPREAD_WEIGHT
        )

        # Slight increase to diversity weight
        new_diversity_weight = min(
            self.baseline_weights.diversity_weight * 1.1,
            self.MAX_DIVERSITY_WEIGHT
        )

        # Create nudges
        self._create_nudge(epoch, 'spread_weight', new_spread, self.nudge_window,
                          'warning_spread_increase')
        self._create_nudge(epoch, 'diversity_weight', new_diversity_weight, self.nudge_window,
                          'warning_diversity_increase')

        # Update baseline
        self.baseline_weights.spread_weight = new_spread
        self.baseline_weights.diversity_weight = new_diversity_weight

        new_weights = WeightState(
            spread_weight=new_spread,
            marginal_weight=self.baseline_weights.marginal_weight,
            joint_weight=self.baseline_weights.joint_weight,
            diversity_temperature=self.baseline_weights.diversity_temperature,
            diversity_weight=new_diversity_weight,
        )

        # Record adjustment
        self.adjustments.append(WeightAdjustment(
            epoch=epoch,
            trigger='health_warning',
            zone=EmbeddingHealthZone.WARNING,
            std_dim=std_dim,
            old_weights=old_weights,
            new_weights=new_weights,
            reason=f"Warning: std/dim={std_dim:.4f} < {self.WARNING_THRESHOLD}"
        ))

        self.last_adjustment_epoch = epoch
        self.consecutive_warning_epochs = 0

        # Track consecutive increases for stacking limit
        self.consecutive_increases += 1
        self.consecutive_decreases = 0  # Reset decrease counter

        logger.info(f"⚠️ [epoch={epoch}] Warning weight adjustment ({self.consecutive_increases}/{self.MAX_CONSECUTIVE_INCREASES}): std/dim={std_dim:.4f}")
        logger.info(f"   spread: {old_weights.spread_weight:.2f} → {new_spread:.2f}")
        logger.info(f"   diversity_weight: {old_weights.diversity_weight:.2f} → {new_diversity_weight:.2f}")

        # Post to timeline
        post_timeline_event({
            'epoch': epoch,
            'event_type': 'weight_adjustment',
            'zone': 'warning',
            'std_dim': std_dim,
            'spread_old': old_weights.spread_weight,
            'spread_new': new_spread,
        })

        # Emit to AdaptiveEventLog
        if self._emit_events:
            self._emit_adjustment_events(
                epoch=epoch,
                reason_code=ReasonCode.EMBEDDING_WARNING,
                trigger_metric="std_per_dim",
                trigger_value=std_dim,
                changes=[
                    ("spread_weight", old_weights.spread_weight, new_spread, ExpectedEffect.INCREASE_SPREAD),
                    ("diversity_weight", old_weights.diversity_weight, new_diversity_weight, ExpectedEffect.INCREASE_SPREAD),
                ],
                notes=f"Warning: std/dim={std_dim:.4f} < {self.WARNING_THRESHOLD}"
            )

    def _respond_to_recovery(self, epoch: int, std_dim: float) -> None:
        """Gradual reduction when embeddings are healthy."""
        old_weights = WeightState(
            spread_weight=self.baseline_weights.spread_weight,
            marginal_weight=self.baseline_weights.marginal_weight,
            joint_weight=self.baseline_weights.joint_weight,
            diversity_temperature=self.baseline_weights.diversity_temperature,
            diversity_weight=self.baseline_weights.diversity_weight,
        )

        # Gradually reduce spread weight toward default
        default_spread = 5.0
        new_spread = max(
            self.baseline_weights.spread_weight * self.recovery_response_factor,
            default_spread  # Don't go below default
        )

        # Only adjust if there's meaningful change
        if abs(new_spread - self.baseline_weights.spread_weight) < 0.1:
            return

        # Create nudge (use longer window for recovery - be gentle)
        recovery_window = int(self.nudge_window * 1.5)
        self._create_nudge(epoch, 'spread_weight', new_spread, recovery_window,
                          'recovery_spread_decrease')

        # Update baseline
        self.baseline_weights.spread_weight = new_spread

        new_weights = WeightState(
            spread_weight=new_spread,
            marginal_weight=self.baseline_weights.marginal_weight,
            joint_weight=self.baseline_weights.joint_weight,
            diversity_temperature=self.baseline_weights.diversity_temperature,
            diversity_weight=self.baseline_weights.diversity_weight,
        )

        # Record adjustment
        self.adjustments.append(WeightAdjustment(
            epoch=epoch,
            trigger='health_recovery',
            zone=EmbeddingHealthZone.HEALTHY,
            std_dim=std_dim,
            old_weights=old_weights,
            new_weights=new_weights,
            reason=f"Recovery: std/dim={std_dim:.4f} >= {self.TARGET_STD_DIM} (reducing elevated spread)"
        ))

        self.last_adjustment_epoch = epoch
        self.consecutive_healthy_epochs = 0

        # Track consecutive decreases for stacking limit
        self.consecutive_decreases += 1
        self.consecutive_increases = 0  # Reset increase counter - we're healthy now

        logger.info(f"✅ [epoch={epoch}] Recovery weight adjustment ({self.consecutive_decreases}/{self.MAX_CONSECUTIVE_DECREASES}): std/dim={std_dim:.4f}")
        logger.info(f"   spread: {old_weights.spread_weight:.2f} → {new_spread:.2f} (toward default)")

        # Emit to AdaptiveEventLog
        if self._emit_events:
            self._emit_adjustment_events(
                epoch=epoch,
                reason_code=ReasonCode.EMBEDDING_RECOVERY,
                trigger_metric="std_per_dim",
                trigger_value=std_dim,
                changes=[
                    ("spread_weight", old_weights.spread_weight, new_spread, ExpectedEffect.DECREASE_SPREAD),
                ],
                notes=f"Recovery: std/dim={std_dim:.4f} >= {self.TARGET_STD_DIM}"
            )

        # Also reset gradient suppression response counter when healthy
        self._gradient_suppression_responses = 0

    def _create_nudge(
        self,
        epoch: int,
        weight_name: str,
        target_value: float,
        duration: int,
        reason: str
    ) -> None:
        """Create a gradual nudge toward a target value."""
        current_value = getattr(self.baseline_weights, weight_name)

        # Determine nudge type
        nudge_type = 'increase' if target_value > current_value else 'decrease'

        # Remove any existing nudge for this weight (supersede it)
        self.active_nudges = [n for n in self.active_nudges if n.weight_name != weight_name]

        # Add new nudge
        nudge = ActiveNudge(
            start_epoch=epoch,
            duration=duration,
            weight_name=weight_name,
            start_value=current_value,
            target_value=target_value,
            reason=reason,
            nudge_type=nudge_type,
        )
        self.active_nudges.append(nudge)

        logger.debug(f"   Created nudge: {weight_name} {current_value:.3f} → {target_value:.3f} "
                    f"over {duration} epochs ({reason})")

    def _apply_active_nudges(self, epoch: int) -> None:
        """Apply all active nudges to compute current effective weights."""
        # Start from baseline
        self.current_weights.spread_weight = self.baseline_weights.spread_weight
        self.current_weights.marginal_weight = self.baseline_weights.marginal_weight
        self.current_weights.joint_weight = self.baseline_weights.joint_weight
        self.current_weights.diversity_temperature = self.baseline_weights.diversity_temperature
        self.current_weights.diversity_weight = self.baseline_weights.diversity_weight

        # Apply each active nudge
        completed_nudges = []
        for nudge in self.active_nudges:
            if epoch < nudge.start_epoch:
                continue

            if epoch >= nudge.start_epoch + nudge.duration:
                # Nudge completed - mark for removal
                completed_nudges.append(nudge)
                # Set to target value
                setattr(self.current_weights, nudge.weight_name, nudge.target_value)
                continue

            # Nudge in progress - interpolate
            progress = (epoch - nudge.start_epoch) / nudge.duration
            interpolated = self._smooth_interpolate(
                progress,
                nudge.start_value,
                nudge.target_value
            )
            setattr(self.current_weights, nudge.weight_name, interpolated)

        # Remove completed nudges
        for nudge in completed_nudges:
            self.active_nudges.remove(nudge)
            logger.debug(f"   Nudge completed: {nudge.weight_name} → {nudge.target_value:.3f}")

    def _smooth_interpolate(
        self,
        progress: float,
        start_value: float,
        end_value: float
    ) -> float:
        """
        Smooth cosine interpolation between two values.

        Uses cosine curve for smooth acceleration/deceleration.
        """
        # Cosine interpolation: smooth start and end
        t = (1 - math.cos(progress * math.pi)) / 2
        return start_value + (end_value - start_value) * t

    def get_weights(self, epoch: Optional[int] = None) -> WeightState:
        """Get current or historical weights for an epoch."""
        if epoch is None:
            return self.current_weights

        if epoch in self.weight_history:
            return self.weight_history[epoch]

        # If asking for future epoch, return current
        return self.current_weights

    def get_spread_weight(self, epoch: Optional[int] = None) -> float:
        """Get spread weight for epoch."""
        return self.get_weights(epoch).spread_weight

    def get_marginal_weight(self, epoch: Optional[int] = None) -> float:
        """Get marginal weight for epoch."""
        return self.get_weights(epoch).marginal_weight

    def get_joint_weight(self, epoch: Optional[int] = None) -> float:
        """Get joint weight for epoch."""
        return self.get_weights(epoch).joint_weight

    def get_diversity_temperature(self, epoch: Optional[int] = None) -> float:
        """Get diversity loss temperature for epoch."""
        return self.get_weights(epoch).diversity_temperature

    def get_diversity_weight(self, epoch: Optional[int] = None) -> float:
        """Get diversity loss weight for epoch."""
        return self.get_weights(epoch).diversity_weight

    def get_separation_weight(self, epoch: Optional[int] = None) -> float:
        """Get separation loss weight for epoch (warmup schedule with cosine decay)."""
        return self.get_weights(epoch).separation_weight

    def manual_adjust(
        self,
        epoch: int,
        spread_weight: Optional[float] = None,
        marginal_weight: Optional[float] = None,
        joint_weight: Optional[float] = None,
        diversity_temperature: Optional[float] = None,
        diversity_weight: Optional[float] = None,
        reason: str = "manual adjustment"
    ) -> None:
        """
        Manually adjust weights (for testing or override).

        Changes are applied gradually over the nudge window.
        """
        old_weights = WeightState(
            spread_weight=self.baseline_weights.spread_weight,
            marginal_weight=self.baseline_weights.marginal_weight,
            joint_weight=self.baseline_weights.joint_weight,
            diversity_temperature=self.baseline_weights.diversity_temperature,
            diversity_weight=self.baseline_weights.diversity_weight,
        )

        if spread_weight is not None:
            spread_weight = max(self.MIN_SPREAD_WEIGHT, min(spread_weight, self.MAX_SPREAD_WEIGHT))
            self._create_nudge(epoch, 'spread_weight', spread_weight, self.nudge_window, reason)
            self.baseline_weights.spread_weight = spread_weight

        if marginal_weight is not None:
            marginal_weight = max(self.MIN_MARGINAL_WEIGHT, min(marginal_weight, self.MAX_MARGINAL_WEIGHT))
            self._create_nudge(epoch, 'marginal_weight', marginal_weight, self.nudge_window, reason)
            self.baseline_weights.marginal_weight = marginal_weight

        if joint_weight is not None:
            joint_weight = max(self.MIN_JOINT_WEIGHT, min(joint_weight, self.MAX_JOINT_WEIGHT))
            self._create_nudge(epoch, 'joint_weight', joint_weight, self.nudge_window, reason)
            self.baseline_weights.joint_weight = joint_weight

        if diversity_temperature is not None:
            diversity_temperature = max(self.MIN_DIVERSITY_TEMP, min(diversity_temperature, self.MAX_DIVERSITY_TEMP))
            self._create_nudge(epoch, 'diversity_temperature', diversity_temperature, self.nudge_window, reason)
            self.baseline_weights.diversity_temperature = diversity_temperature

        if diversity_weight is not None:
            diversity_weight = max(self.MIN_DIVERSITY_WEIGHT, min(diversity_weight, self.MAX_DIVERSITY_WEIGHT))
            self._create_nudge(epoch, 'diversity_weight', diversity_weight, self.nudge_window, reason)
            self.baseline_weights.diversity_weight = diversity_weight

        new_weights = WeightState(
            spread_weight=self.baseline_weights.spread_weight,
            marginal_weight=self.baseline_weights.marginal_weight,
            joint_weight=self.baseline_weights.joint_weight,
            diversity_temperature=self.baseline_weights.diversity_temperature,
            diversity_weight=self.baseline_weights.diversity_weight,
        )

        # Record adjustment
        std_dim = self.health_history.get(epoch, (0.0, EmbeddingHealthZone.HEALTHY))[0]
        zone = self.health_history.get(epoch, (0.0, EmbeddingHealthZone.HEALTHY))[1]

        self.adjustments.append(WeightAdjustment(
            epoch=epoch,
            trigger='manual',
            zone=zone,
            std_dim=std_dim,
            old_weights=old_weights,
            new_weights=new_weights,
            reason=reason
        ))

        logger.info(f"🔧 [epoch={epoch}] Manual weight adjustment: {reason}")

    def adjust_spread_weight(self, factor: float, reason: str) -> None:
        """
        Adjust spread weight by a multiplicative factor.

        Used by training rules engine for condition-based adjustments.

        Args:
            factor: Multiplicative factor (e.g., 1.3 to increase by 30%)
            reason: Human-readable reason for the adjustment
        """
        current = self.get_spread_weight()
        new_value = current * factor
        # Clamp to valid range
        new_value = max(self.MIN_SPREAD_WEIGHT, min(new_value, self.MAX_SPREAD_WEIGHT))
        self.manual_adjust(
            epoch=self.current_epoch,
            spread_weight=new_value,
            reason=f"{reason} (×{factor:.2f})"
        )

    def get_state_dict(self) -> Dict[str, Any]:
        """Get state for checkpointing."""
        return {
            'n_epochs': self.n_epochs,
            'current_epoch': self.current_epoch,
            'baseline_weights': self.baseline_weights.to_dict(),
            'current_weights': self.current_weights.to_dict(),
            'health_history': {k: (v[0], v[1].value) for k, v in self.health_history.items()},
            'weight_history': {k: v.to_dict() for k, v in self.weight_history.items()},
            'consecutive_random_epochs': self.consecutive_random_epochs,
            'consecutive_warning_epochs': self.consecutive_warning_epochs,
            'consecutive_emergency_epochs': self.consecutive_emergency_epochs,
            'consecutive_healthy_epochs': self.consecutive_healthy_epochs,
            'last_adjustment_epoch': self.last_adjustment_epoch,
            # Stacking limit counters
            'consecutive_increases': self.consecutive_increases,
            'consecutive_decreases': self.consecutive_decreases,
            'adjustments': [
                {
                    'epoch': a.epoch,
                    'trigger': a.trigger,
                    'zone': a.zone.value,
                    'std_dim': a.std_dim,
                    'old_weights': a.old_weights.to_dict(),
                    'new_weights': a.new_weights.to_dict(),
                    'reason': a.reason,
                }
                for a in self.adjustments
            ],
            'active_nudges': [
                {
                    'start_epoch': n.start_epoch,
                    'duration': n.duration,
                    'weight_name': n.weight_name,
                    'start_value': n.start_value,
                    'target_value': n.target_value,
                    'reason': n.reason,
                    'nudge_type': n.nudge_type,
                }
                for n in self.active_nudges
            ],
            # Gradient flow tracking state
            'gradient_flow_history': self._gradient_flow_history[-50:],  # Keep last 50
            'last_gradient_adjustment_epoch': self._last_gradient_adjustment_epoch,
            'gradient_suppression_responses': self._gradient_suppression_responses,
        }

    def load_state_dict(self, state_dict: Dict[str, Any]) -> None:
        """Load state from checkpoint."""
        self.n_epochs = state_dict.get('n_epochs', self.n_epochs)
        self.current_epoch = state_dict.get('current_epoch', 0)

        # Restore baseline weights
        if 'baseline_weights' in state_dict:
            bw = state_dict['baseline_weights']
            self.baseline_weights = WeightState(
                spread_weight=bw.get('spread_weight', 5.0),
                marginal_weight=bw.get('marginal_weight', 0.25),
                joint_weight=bw.get('joint_weight', 1.0),
                diversity_temperature=bw.get('diversity_temperature', 0.1),
                diversity_weight=bw.get('diversity_weight', 1.0),
            )

        # Restore current weights
        if 'current_weights' in state_dict:
            cw = state_dict['current_weights']
            self.current_weights = WeightState(
                spread_weight=cw.get('spread_weight', 5.0),
                marginal_weight=cw.get('marginal_weight', 0.25),
                joint_weight=cw.get('joint_weight', 1.0),
                diversity_temperature=cw.get('diversity_temperature', 0.1),
                diversity_weight=cw.get('diversity_weight', 1.0),
            )

        # Restore health history
        self.health_history = {}
        for k, v in state_dict.get('health_history', {}).items():
            epoch = int(k) if isinstance(k, str) else k
            self.health_history[epoch] = (v[0], EmbeddingHealthZone(v[1]))

        # Restore weight history
        self.weight_history = {}
        for k, v in state_dict.get('weight_history', {}).items():
            epoch = int(k) if isinstance(k, str) else k
            self.weight_history[epoch] = WeightState(
                spread_weight=v.get('spread_weight', 5.0),
                marginal_weight=v.get('marginal_weight', 0.25),
                joint_weight=v.get('joint_weight', 1.0),
                diversity_temperature=v.get('diversity_temperature', 0.1),
                diversity_weight=v.get('diversity_weight', 1.0),
            )

        # Restore counters
        self.consecutive_random_epochs = state_dict.get('consecutive_random_epochs', 0)
        self.consecutive_warning_epochs = state_dict.get('consecutive_warning_epochs', 0)
        self.consecutive_emergency_epochs = state_dict.get('consecutive_emergency_epochs', 0)
        self.consecutive_healthy_epochs = state_dict.get('consecutive_healthy_epochs', 0)
        self.last_adjustment_epoch = state_dict.get('last_adjustment_epoch', -10)

        # Restore stacking limit counters
        self.consecutive_increases = state_dict.get('consecutive_increases', 0)
        self.consecutive_decreases = state_dict.get('consecutive_decreases', 0)

        # Restore active nudges
        self.active_nudges = []
        for n in state_dict.get('active_nudges', []):
            self.active_nudges.append(ActiveNudge(
                start_epoch=n['start_epoch'],
                duration=n['duration'],
                weight_name=n['weight_name'],
                start_value=n['start_value'],
                target_value=n['target_value'],
                reason=n['reason'],
                nudge_type=n['nudge_type'],
            ))

        # Restore adjustments
        self.adjustments = []
        for a in state_dict.get('adjustments', []):
            old_w = a['old_weights']
            new_w = a['new_weights']
            self.adjustments.append(WeightAdjustment(
                epoch=a['epoch'],
                trigger=a['trigger'],
                zone=EmbeddingHealthZone(a['zone']),
                std_dim=a['std_dim'],
                old_weights=WeightState(**old_w),
                new_weights=WeightState(**new_w),
                reason=a['reason'],
            ))

        # Restore gradient flow tracking state
        self._gradient_flow_history = state_dict.get('gradient_flow_history', [])
        self._last_gradient_adjustment_epoch = state_dict.get('last_gradient_adjustment_epoch', -10)
        self._gradient_suppression_responses = state_dict.get('gradient_suppression_responses', 0)

        logger.info(f"🔄 WeightTimeline state restored: epoch={self.current_epoch}, "
                   f"{len(self.adjustments)} adjustments, {len(self.active_nudges)} active nudges")

    def summary(self) -> str:
        """Get text summary of weight timeline state."""
        lines = []
        lines.append("=" * 70)
        lines.append("WEIGHT TIMELINE SUMMARY")
        lines.append("=" * 70)
        lines.append(f"Current epoch: {self.current_epoch} / {self.n_epochs}")
        lines.append("")
        lines.append("Current Weights:")
        lines.append(f"  spread_weight:         {self.current_weights.spread_weight:.3f}")
        lines.append(f"  marginal_weight:       {self.current_weights.marginal_weight:.3f}")
        lines.append(f"  joint_weight:          {self.current_weights.joint_weight:.3f}")
        lines.append(f"  diversity_temperature: {self.current_weights.diversity_temperature:.4f}")
        lines.append(f"  diversity_weight:      {self.current_weights.diversity_weight:.3f}")
        lines.append("")
        lines.append("Health Thresholds:")
        lines.append(f"  Random:    >= {self.RANDOM_THRESHOLD - 0.002} (embeddings not learning)")
        lines.append(f"  Healthy:   {self.TARGET_STD_DIM}-{self.RANDOM_THRESHOLD - 0.002} (structured)")
        lines.append(f"  Warning:   < {self.WARNING_THRESHOLD}")
        lines.append(f"  Emergency: < {self.EMERGENCY_THRESHOLD}")
        lines.append("")
        lines.append("Stacking Limits:")
        lines.append(f"  Consecutive increases: {self.consecutive_increases}/{self.MAX_CONSECUTIVE_INCREASES}")
        lines.append(f"  Consecutive decreases: {self.consecutive_decreases}/{self.MAX_CONSECUTIVE_DECREASES}")
        lines.append("")

        if self.adjustments:
            lines.append(f"Adjustments Made: {len(self.adjustments)}")
            for adj in self.adjustments[-5:]:  # Last 5
                lines.append(f"  Epoch {adj.epoch}: {adj.trigger} ({adj.zone.value}) - {adj.reason}")
        else:
            lines.append("No adjustments made yet.")

        if self.active_nudges:
            lines.append("")
            lines.append(f"Active Nudges: {len(self.active_nudges)}")
            for nudge in self.active_nudges:
                lines.append(f"  {nudge.weight_name}: {nudge.start_value:.3f} → {nudge.target_value:.3f} "
                           f"(epochs {nudge.start_epoch}-{nudge.start_epoch + nudge.duration})")

        lines.append("=" * 70)
        return "\n".join(lines)

    def plot_history(self, save_path: str, figsize=(14, 10)) -> None:
        """
        Plot weight timeline history with health zones.

        Creates a multi-panel plot showing:
        - Embedding health (std/dim) with zone coloring
        - Loss weights over time
        - Diversity parameters over time
        """
        try:
            import matplotlib.pyplot as plt
            import numpy as np
        except ImportError:
            logger.warning("matplotlib not available, cannot plot weight history")
            return

        if not self.weight_history:
            logger.warning("No weight history to plot")
            return

        epochs = sorted(self.weight_history.keys())

        fig, axes = plt.subplots(3, 1, figsize=figsize, sharex=True)

        # ========== Panel 1: Embedding Health ==========
        ax1 = axes[0]

        if self.health_history:
            health_epochs = sorted(self.health_history.keys())
            std_dims = [self.health_history[e][0] for e in health_epochs]

            ax1.plot(health_epochs, std_dims, '-', linewidth=2, color='#2563eb', label='std/dim')

            # Add threshold lines
            ax1.axhline(self.TARGET_STD_DIM, color='green', linestyle='--', alpha=0.7, label=f'Target ({self.TARGET_STD_DIM})')
            ax1.axhline(self.WARNING_THRESHOLD, color='orange', linestyle='--', alpha=0.7, label=f'Warning ({self.WARNING_THRESHOLD})')
            ax1.axhline(self.EMERGENCY_THRESHOLD, color='red', linestyle='--', alpha=0.7, label=f'Emergency ({self.EMERGENCY_THRESHOLD})')

            # Color zones
            ax1.fill_between(health_epochs, self.TARGET_STD_DIM, max(std_dims) * 1.1,
                            alpha=0.1, color='green', label='Healthy zone')
            ax1.fill_between(health_epochs, self.WARNING_THRESHOLD, self.TARGET_STD_DIM,
                            alpha=0.1, color='yellow')
            ax1.fill_between(health_epochs, self.EMERGENCY_THRESHOLD, self.WARNING_THRESHOLD,
                            alpha=0.1, color='orange')
            ax1.fill_between(health_epochs, 0, self.EMERGENCY_THRESHOLD,
                            alpha=0.1, color='red')

        ax1.set_ylabel('Embedding std/dim', fontsize=11, fontweight='bold')
        ax1.set_title('Weight Timeline: Adaptive Loss Weights Based on Embedding Health',
                     fontsize=14, fontweight='bold')
        ax1.legend(loc='upper right', fontsize=8)
        ax1.grid(True, alpha=0.3)
        ax1.set_ylim(0.0, 1.0)

        # ========== Panel 2: Loss Weights ==========
        ax2 = axes[1]

        spread_weights = [self.weight_history[e].spread_weight for e in epochs]
        marginal_weights = [self.weight_history[e].marginal_weight for e in epochs]
        joint_weights = [self.weight_history[e].joint_weight for e in epochs]

        ax2.plot(epochs, spread_weights, '-', linewidth=2, color='#10b981', label='spread_weight')
        ax2.plot(epochs, marginal_weights, '-', linewidth=2, color='#ef4444', label='marginal_weight')
        ax2.plot(epochs, joint_weights, '-', linewidth=2, color='#3b82f6', label='joint_weight')

        # Mark adjustments
        for adj in self.adjustments:
            if adj.trigger == 'health_emergency':
                ax2.axvline(adj.epoch, color='red', linestyle=':', alpha=0.5)
            elif adj.trigger == 'health_warning':
                ax2.axvline(adj.epoch, color='orange', linestyle=':', alpha=0.5)
            elif adj.trigger == 'health_recovery':
                ax2.axvline(adj.epoch, color='green', linestyle=':', alpha=0.5)

        ax2.set_ylabel('Loss Weights', fontsize=11, fontweight='bold')
        ax2.legend(loc='upper right', fontsize=9)
        ax2.grid(True, alpha=0.3)

        # ========== Panel 3: Diversity Parameters ==========
        ax3 = axes[2]

        div_temps = [self.weight_history[e].diversity_temperature for e in epochs]
        div_weights = [self.weight_history[e].diversity_weight for e in epochs]

        ax3_twin = ax3.twinx()

        line1, = ax3.plot(epochs, div_weights, '-', linewidth=2, color='#8b5cf6', label='diversity_weight')
        line2, = ax3_twin.plot(epochs, div_temps, '-', linewidth=2, color='#f59e0b', label='diversity_temp')

        ax3.set_ylabel('Diversity Weight', fontsize=11, fontweight='bold', color='#8b5cf6')
        ax3_twin.set_ylabel('Diversity Temperature', fontsize=11, fontweight='bold', color='#f59e0b')
        ax3.set_xlabel('Epoch', fontsize=11, fontweight='bold')

        # Combined legend
        lines = [line1, line2]
        labels = [l.get_label() for l in lines]
        ax3.legend(lines, labels, loc='upper right', fontsize=9)
        ax3.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()

        logger.info(f"📊 Weight timeline plot saved to: {save_path}")


# =============================================================================
# TEST
# =============================================================================

def test_weight_timeline():
    """Test weight timeline with simulated embedding health."""
    import random

    print("=" * 70)
    print("WEIGHT TIMELINE TEST")
    print("=" * 70)

    # Create timeline
    wt = WeightTimeline(
        n_epochs=100,
        initial_spread_weight=5.0,
        initial_marginal_weight=0.25,
        initial_joint_weight=1.0,
    )

    print(wt.summary())
    print()

    # Simulate training with varying embedding health
    print("Simulating training...")

    # Simulate: starts healthy, collapses around epoch 30, recovers around epoch 60
    for epoch in range(100):
        if epoch < 20:
            # Healthy start
            std_dim = 0.055 + random.gauss(0, 0.005)
        elif epoch < 40:
            # Gradual collapse
            std_dim = 0.055 - (epoch - 20) * 0.002 + random.gauss(0, 0.003)
        elif epoch < 60:
            # Warning/emergency zone
            std_dim = 0.015 + random.gauss(0, 0.003)
        else:
            # Recovery
            recovery_progress = (epoch - 60) / 40
            std_dim = 0.015 + recovery_progress * 0.035 + random.gauss(0, 0.003)

        std_dim = max(0.005, std_dim)  # Floor at 0.005

        weights = wt.update(epoch, std_dim)

        if epoch % 20 == 0:
            zone = wt.classify_health(std_dim)
            print(f"Epoch {epoch:3d}: std={std_dim:.4f} ({zone.value:10s}) "
                  f"spread={weights.spread_weight:.2f}, "
                  f"marginal={weights.marginal_weight:.3f}, "
                  f"diversity_w={weights.diversity_weight:.2f}")

    print()
    print(wt.summary())

    # Plot if matplotlib available
    try:
        wt.plot_history("weight_timeline_test.png")
        print("\n✅ Plot saved to weight_timeline_test.png")
    except Exception as e:
        print(f"\n⚠️ Could not create plot: {e}")

    print()
    print("=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    test_weight_timeline()
