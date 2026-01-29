"""
Training Rules Engine - Declarative condition-based training adjustments.

Replaces scattered if/else logic with a unified rule system.

Example rules:
    rules = [
        {
            "name": "auc_recall_divergence",
            "when": "validation_end",
            "condition": {
                "all": [
                    {"metric": "auc", "trend": "increasing", "window": 5},
                    {"metric": "recall_at_1", "trend": "flat", "window": 5}
                ]
            },
            "action": {"adjust": "temperature", "factor": 1.2},
            "cooldown": 3,
        },
        {
            "name": "embedding_collapse",
            "when": "epoch_end",
            "condition": {"metric": "std_dim", "below": 0.03},
            "action": {"adjust": "spread_weight", "factor": 1.5},
            "cooldown": 5,
        },
    ]

Usage:
    engine = RuleEngine(rules, action_targets={
        "lr": lr_timeline,
        "temperature": loss_framework,
        "spread_weight": weight_timeline,
        ...
    })

    # At each hook point:
    engine.on_validation_end(metrics)
    engine.on_epoch_end(metrics)
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable, Union
from enum import Enum
import numpy as np

logger = logging.getLogger(__name__)


# =============================================================================
# Enums and Types
# =============================================================================

class HookPoint(Enum):
    """When rules can be evaluated."""
    TRAINING_START = "training_start"
    BATCH_END = "batch_end"
    EPOCH_END = "epoch_end"
    VALIDATION_END = "validation_end"


class TrendDirection(Enum):
    """Trend detection results."""
    INCREASING = "increasing"
    DECREASING = "decreasing"
    FLAT = "flat"
    UNKNOWN = "unknown"


# =============================================================================
# Metric History Tracker
# =============================================================================

class MetricHistory:
    """
    Tracks metric values over time for trend detection.

    Stores last N values of each metric and provides trend analysis.
    """

    def __init__(self, max_history: int = 20):
        self.max_history = max_history
        self._history: Dict[str, List[float]] = {}
        self._epochs: Dict[str, List[int]] = {}  # Track which epoch each value came from

    def record(self, epoch: int, metrics: Dict[str, float]):
        """Record metrics for an epoch."""
        for name, value in metrics.items():
            if value is None:
                continue
            if name not in self._history:
                self._history[name] = []
                self._epochs[name] = []

            self._history[name].append(float(value))
            self._epochs[name].append(epoch)

            # Trim to max history
            if len(self._history[name]) > self.max_history:
                self._history[name] = self._history[name][-self.max_history:]
                self._epochs[name] = self._epochs[name][-self.max_history:]

    def get(self, metric: str, window: int = 1) -> Optional[List[float]]:
        """Get last N values of a metric."""
        if metric not in self._history:
            return None
        return self._history[metric][-window:]

    def get_latest(self, metric: str) -> Optional[float]:
        """Get most recent value of a metric."""
        if metric not in self._history or not self._history[metric]:
            return None
        return self._history[metric][-1]

    def compute_trend(self, metric: str, window: int = 5,
                      flat_threshold: float = 0.02) -> TrendDirection:
        """
        Compute trend direction for a metric over a window.

        Args:
            metric: Metric name
            window: Number of epochs to analyze
            flat_threshold: Relative change threshold for "flat" (default 2%)

        Returns:
            TrendDirection enum
        """
        values = self.get(metric, window)
        if values is None or len(values) < 2:
            return TrendDirection.UNKNOWN

        # Simple linear regression slope
        x = np.arange(len(values))
        y = np.array(values)

        # Compute slope using least squares
        n = len(values)
        slope = (n * np.sum(x * y) - np.sum(x) * np.sum(y)) / (n * np.sum(x**2) - np.sum(x)**2)

        # Normalize slope by mean value to get relative change per epoch
        mean_val = np.mean(y)
        if abs(mean_val) < 1e-10:
            return TrendDirection.FLAT

        relative_slope = slope / abs(mean_val)

        if abs(relative_slope) < flat_threshold / window:
            return TrendDirection.FLAT
        elif relative_slope > 0:
            return TrendDirection.INCREASING
        else:
            return TrendDirection.DECREASING

    def compute_slope(self, metric: str, window: int = 5) -> Optional[float]:
        """Compute raw slope (change per epoch) for a metric."""
        values = self.get(metric, window)
        if values is None or len(values) < 2:
            return None

        x = np.arange(len(values))
        y = np.array(values)
        n = len(values)
        slope = (n * np.sum(x * y) - np.sum(x) * np.sum(y)) / (n * np.sum(x**2) - np.sum(x)**2)
        return float(slope)


# =============================================================================
# Condition Evaluator
# =============================================================================

class ConditionEvaluator:
    """
    Evaluates rule conditions against current metrics and history.

    Supports:
        - String expressions: "num_rows > 1_000_000" or "auc > 0.8 and recall_at_1 < 0.5"
          Uses Python's eval() with restricted namespace (metrics + builtins disabled)
        - Trend checks: {"metric": "x", "trend": "increasing", "window": 5}
        - Compound: {"all": [...]} or {"any": [...]}
    """

    def __init__(self, history: MetricHistory):
        self.history = history

    def evaluate(self, condition: Union[str, Dict[str, Any]],
                 current_metrics: Dict[str, float],
                 epoch: int, total_epochs: int) -> bool:
        """
        Evaluate a condition.

        Args:
            condition: Condition specification - string expr or dict
            current_metrics: Current epoch's metrics
            epoch: Current epoch number
            total_epochs: Total training epochs

        Returns:
            True if condition is met
        """
        # Handle string expressions: "num_rows > 1_000_000"
        if isinstance(condition, str):
            return self._evaluate_expression(condition, current_metrics, epoch, total_epochs)

        # Compound conditions
        if "all" in condition:
            return all(self.evaluate(c, current_metrics, epoch, total_epochs)
                      for c in condition["all"])

        if "any" in condition:
            return any(self.evaluate(c, current_metrics, epoch, total_epochs)
                      for c in condition["any"])

        # Epoch percentage check
        if "epoch_pct" in condition:
            return self._check_epoch_pct(condition["epoch_pct"], epoch, total_epochs)

        # Metric-based checks
        if "metric" not in condition:
            logger.warning(f"Condition missing 'metric' key: {condition}")
            return False

        metric = condition["metric"]

        # Get current value (prefer current_metrics, fall back to history)
        value = current_metrics.get(metric)
        if value is None:
            value = self.history.get_latest(metric)

        # Threshold checks
        if "above" in condition:
            if value is None:
                return False
            return value > condition["above"]

        if "below" in condition:
            if value is None:
                return False
            return value < condition["below"]

        if "between" in condition:
            if value is None:
                return False
            low, high = condition["between"]
            return low <= value <= high

        # Trend checks
        if "trend" in condition:
            window = condition.get("window", 5)
            flat_threshold = condition.get("flat_threshold", 0.02)
            trend = self.history.compute_trend(metric, window, flat_threshold)
            expected = TrendDirection(condition["trend"])
            return trend == expected

        # Slope checks (more precise than trend)
        if "slope_above" in condition:
            window = condition.get("window", 5)
            slope = self.history.compute_slope(metric, window)
            if slope is None:
                return False
            return slope > condition["slope_above"]

        if "slope_below" in condition:
            window = condition.get("window", 5)
            slope = self.history.compute_slope(metric, window)
            if slope is None:
                return False
            return slope < condition["slope_below"]

        logger.warning(f"Unknown condition type: {condition}")
        return False

    def _evaluate_expression(self, expr: str, metrics: Dict[str, float],
                            epoch: int, total_epochs: int) -> bool:
        """
        Evaluate a string expression like "num_rows > 1_000_000".

        Uses Python eval() with a restricted namespace containing only metrics.
        Supports standard Python: >, <, >=, <=, ==, !=, and, or, not, parentheses.

        Args:
            expr: String expression to evaluate
            metrics: Current metrics dict
            epoch: Current epoch number
            total_epochs: Total training epochs

        Returns:
            True if expression evaluates to True
        """
        # Build namespace with all metrics + special variables
        namespace = dict(metrics)
        namespace["epoch"] = epoch
        namespace["total_epochs"] = total_epochs
        namespace["epoch_pct"] = epoch / total_epochs if total_epochs > 0 else 0.0

        # Add metrics from history that aren't in current metrics
        for metric_name in set(self.history._history.keys()) - set(metrics.keys()):
            value = self.history.get_latest(metric_name)
            if value is not None:
                namespace[metric_name] = value

        try:
            result = eval(expr, {"__builtins__": {}}, namespace)
            return bool(result)
        except NameError as e:
            logger.debug(f"Missing metric in expression '{expr}': {e}")
            return False
        except Exception as e:
            logger.warning(f"Failed to evaluate expression '{expr}': {e}")
            return False

    def _check_epoch_pct(self, spec: Dict[str, float], epoch: int, total_epochs: int) -> bool:
        """Check epoch percentage conditions."""
        pct = epoch / total_epochs if total_epochs > 0 else 0

        if "gte" in spec and pct < spec["gte"]:
            return False
        if "gt" in spec and pct <= spec["gt"]:
            return False
        if "lte" in spec and pct > spec["lte"]:
            return False
        if "lt" in spec and pct >= spec["lt"]:
            return False
        if "eq" in spec and abs(pct - spec["eq"]) > 0.01:
            return False

        return True


# =============================================================================
# Action Executor
# =============================================================================

@dataclass
class ActionTarget:
    """A target that can receive actions (e.g., LRTimeline, WeightTimeline)."""
    name: str
    # Methods to call for different action types
    increase: Optional[Callable[[float, str], None]] = None  # (factor, reason) -> None
    decrease: Optional[Callable[[float, str], None]] = None
    set_value: Optional[Callable[[float, str], None]] = None  # (value, reason) -> None
    get_value: Optional[Callable[[], float]] = None


class ActionExecutor:
    """
    Executes rule actions on registered targets.

    Targets are registered with their adjustment methods:
        executor.register_target("lr", ActionTarget(
            name="lr",
            increase=lambda f, r: lr_timeline.increase_lr(epoch, f, r),
            decrease=lambda f, r: lr_timeline.decrease_lr(epoch, f, r),
        ))
    """

    def __init__(self):
        self._targets: Dict[str, ActionTarget] = {}
        self._current_epoch: int = 0

    def register_target(self, name: str, target: ActionTarget):
        """Register an action target."""
        self._targets[name] = target

    def set_epoch(self, epoch: int):
        """Update current epoch (needed for some actions)."""
        self._current_epoch = epoch

    def execute(self, action: Dict[str, Any], reason: str) -> bool:
        """
        Execute an action.

        Supports two action types:
        1. "set": Set a config value directly (for training_start)
           {"set": "n_layers", "value": 4}

        2. "adjust": Multiply an existing value by a factor (for runtime adjustments)
           {"adjust": "lr", "factor": 1.2}

        Args:
            action: Action specification dict
            reason: Human-readable reason for the action

        Returns:
            True if action was executed successfully
        """
        # Handle "set" actions (direct value assignment, typically at training_start)
        if "set" in action:
            target_name = action["set"]
            value = action.get("value")
            if value is None:
                logger.warning(f"'set' action missing 'value': {action}")
                return False

            if target_name not in self._targets:
                logger.warning(f"Unknown action target: {target_name}")
                return False

            target = self._targets[target_name]
            if target.set_value:
                target.set_value(value, reason)
                logger.info(f"⚙️  ACTION: Set {target_name} = {value} ({reason})")
                return True
            else:
                logger.warning(f"Target {target_name} doesn't support set_value")
                return False

        # Handle "adjust" actions (factor-based adjustment)
        if "adjust" in action:
            target_name = action["adjust"]
            if target_name not in self._targets:
                logger.warning(f"Unknown action target: {target_name}")
                return False

            target = self._targets[target_name]
            factor = action.get("factor", 1.0)
            direction = action.get("direction", "increase" if factor > 1 else "decrease")

            # Handle explicit set_value via adjust (legacy support)
            if "value" in action:
                if target.set_value:
                    target.set_value(action["value"], reason)
                    logger.info(f"🎯 ACTION: Set {target_name} = {action['value']} ({reason})")
                    return True
                else:
                    logger.warning(f"Target {target_name} doesn't support set_value")
                    return False

            # Handle factor-based adjustment
            if direction == "increase" or factor > 1:
                if target.increase:
                    target.increase(factor, reason)
                    logger.info(f"📈 ACTION: Increase {target_name} by {factor}x ({reason})")
                    return True
                else:
                    logger.warning(f"Target {target_name} doesn't support increase")
                    return False
            else:
                if target.decrease:
                    target.decrease(factor, reason)
                    logger.info(f"📉 ACTION: Decrease {target_name} by {factor}x ({reason})")
                    return True
                else:
                    logger.warning(f"Target {target_name} doesn't support decrease")
                    return False

        logger.warning(f"Action must have 'set' or 'adjust' key: {action}")
        return False


# =============================================================================
# Training Rule
# =============================================================================

@dataclass
class TrainingRule:
    """A single training rule."""
    name: str
    when: HookPoint
    condition: Dict[str, Any]
    actions: List[Dict[str, Any]]  # List of actions to execute
    cooldown: int = 0  # Epochs to wait before rule can fire again
    max_fires: int = 0  # Max times rule can fire (0 = unlimited)
    enabled: bool = True

    # Runtime state (not part of config)
    _last_fired_epoch: int = field(default=-999, repr=False)
    _fire_count: int = field(default=0, repr=False)

    def can_fire(self, epoch: int) -> bool:
        """Check if rule is allowed to fire (cooldown, max_fires)."""
        if not self.enabled:
            return False
        if self.max_fires > 0 and self._fire_count >= self.max_fires:
            return False
        if epoch - self._last_fired_epoch < self.cooldown:
            return False
        return True

    def record_fire(self, epoch: int):
        """Record that the rule fired."""
        self._last_fired_epoch = epoch
        self._fire_count += 1


# =============================================================================
# Rule Engine
# =============================================================================

class RuleEngine:
    """
    Main rule engine that evaluates and executes rules at hook points.

    Usage:
        engine = RuleEngine()
        engine.add_rule(TrainingRule(...))
        engine.register_target("lr", ActionTarget(...))

        # At each hook:
        engine.on_validation_end(epoch, total_epochs, metrics)
    """

    def __init__(self, rules: Optional[List[TrainingRule]] = None):
        self.rules: List[TrainingRule] = rules or []
        self.history = MetricHistory()
        self.evaluator = ConditionEvaluator(self.history)
        self.executor = ActionExecutor()

        # Track fired rules for logging/debugging
        self._fired_rules: List[Dict[str, Any]] = []

    def add_rule(self, rule: TrainingRule):
        """Add a rule to the engine."""
        self.rules.append(rule)

    def add_rules_from_config(self, config: List[Dict[str, Any]]):
        """Add rules from a config list (dicts).

        Supports both single action and multiple actions:
            {"action": {...}}           # single action
            {"actions": [{...}, {...}]} # multiple actions
        """
        for rule_dict in config:
            # Support both "action" (single) and "actions" (list)
            if "actions" in rule_dict:
                actions = rule_dict["actions"]
            elif "action" in rule_dict:
                actions = [rule_dict["action"]]
            else:
                raise ValueError(f"Rule '{rule_dict.get('name', '?')}' missing 'action' or 'actions'")

            rule = TrainingRule(
                name=rule_dict["name"],
                when=HookPoint(rule_dict.get("when", "validation_end")),
                condition=rule_dict["condition"],
                actions=actions,
                cooldown=rule_dict.get("cooldown", 0),
                max_fires=rule_dict.get("max_fires", 0),
                enabled=rule_dict.get("enabled", True),
            )
            self.add_rule(rule)

    def register_target(self, name: str, target: ActionTarget):
        """Register an action target."""
        self.executor.register_target(name, target)

    def _run_hook(self, hook: HookPoint, epoch: int, total_epochs: int,
                  metrics: Dict[str, float]) -> List[str]:
        """
        Run all rules for a hook point.

        Returns:
            List of rule names that fired
        """
        self.executor.set_epoch(epoch)

        # Record metrics in history
        self.history.record(epoch, metrics)

        fired = []
        for rule in self.rules:
            if rule.when != hook:
                continue
            if not rule.can_fire(epoch):
                continue

            # Evaluate condition
            if self.evaluator.evaluate(rule.condition, metrics, epoch, total_epochs):
                # Execute all actions for this rule
                any_success = False
                for action in rule.actions:
                    action_name = action.get("action_name", action.get("set") or action.get("adjust"))
                    reason = f"Rule '{rule.name}' → {action_name}" if action_name else f"Rule '{rule.name}'"
                    success = self.executor.execute(action, reason)
                    if success:
                        any_success = True

                if any_success:
                    rule.record_fire(epoch)
                    fired.append(rule.name)

                    self._fired_rules.append({
                        "epoch": epoch,
                        "rule": rule.name,
                        "actions": rule.actions,
                        "metrics": {k: v for k, v in metrics.items() if v is not None},
                    })

        if fired:
            logger.info(f"🔔 Rules fired at {hook.value}: {', '.join(fired)}")

        return fired

    # Hook methods for each point
    def on_training_start(self, total_epochs: int, config: Dict[str, Any]) -> List[str]:
        """Called before training starts."""
        return self._run_hook(HookPoint.TRAINING_START, 0, total_epochs, config)

    def on_batch_end(self, epoch: int, batch: int, total_epochs: int,
                     metrics: Dict[str, float]) -> List[str]:
        """Called after each batch."""
        # Add batch info to metrics
        metrics = {**metrics, "_batch": batch}
        return self._run_hook(HookPoint.BATCH_END, epoch, total_epochs, metrics)

    def on_epoch_end(self, epoch: int, total_epochs: int,
                     metrics: Dict[str, float]) -> List[str]:
        """Called after training epoch, before validation."""
        return self._run_hook(HookPoint.EPOCH_END, epoch, total_epochs, metrics)

    def on_validation_end(self, epoch: int, total_epochs: int,
                          metrics: Dict[str, float]) -> List[str]:
        """Called after validation."""
        return self._run_hook(HookPoint.VALIDATION_END, epoch, total_epochs, metrics)

    def get_fired_rules_history(self) -> List[Dict[str, Any]]:
        """Get history of all fired rules."""
        return self._fired_rules.copy()

    def get_rule_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get stats for each rule."""
        return {
            rule.name: {
                "fire_count": rule._fire_count,
                "last_fired_epoch": rule._last_fired_epoch if rule._fire_count > 0 else None,
                "enabled": rule.enabled,
            }
            for rule in self.rules
        }


# =============================================================================
# Default Rules - imported from default_training_rules.py for easy editing
# =============================================================================

from featrix.neural.default_training_rules import (
    get_default_rules,
    get_architecture_rules,
    get_runtime_rules,
)


def create_rule_engine(
    rules: Optional[List[Dict[str, Any]]] = None,
    use_defaults: bool = True,
    include_architecture_rules: bool = True,
    include_runtime_rules: bool = True,
) -> RuleEngine:
    """
    Create a rule engine with optional default rules.

    Args:
        rules: Custom rules to add
        use_defaults: Whether to include default rules
        include_architecture_rules: Include training_start rules for architecture
        include_runtime_rules: Include runtime adjustment rules

    Returns:
        Configured RuleEngine
    """
    engine = RuleEngine()

    if use_defaults:
        if include_architecture_rules:
            engine.add_rules_from_config(get_architecture_rules())
        if include_runtime_rules:
            engine.add_rules_from_config(get_runtime_rules())

    if rules:
        engine.add_rules_from_config(rules)

    return engine
