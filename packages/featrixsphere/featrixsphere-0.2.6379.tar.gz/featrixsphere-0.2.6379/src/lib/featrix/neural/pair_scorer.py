#  -*- coding: utf-8 -*-
#
#  Copyright Featrix, Inc 2023-2025
#
#  Proprietary and Confidential. Unauthorized use, copying or dissemination
#  of these materials is strictly prohibited.
"""
PairScorer: Generic lift-based scoring and pruning for column pairs.

This class encapsulates the logic for:
1. Tracking pair statistics (lift EMA, observation count)
2. Computing importance scores (lift + confidence weighting)
3. Pruning low-performing pairs based on lift
4. Selecting top-K pairs for exploration/exploitation

Used for both:
- Generic relationship pairs (element-wise ops)
- Type-aware pairs (SetSet, ScalarScalar, etc.)
"""
import logging
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


@dataclass
class PairStats:
    """Statistics for a single pair."""
    n: int = 0                    # Observation count
    lift_ema: float = 0.0         # Exponential moving average of lift
    lift_sum: float = 0.0         # Sum of lifts (for computing mean)
    lift_sum_sq: float = 0.0      # Sum of squared lifts (for computing variance)
    last_epoch_active: int = -1   # Last epoch this pair was active


class PairScorer:
    """Generic lift-based scoring and pruning for column pairs.

    This class tracks pair statistics, computes importance scores,
    and provides methods for selecting/pruning pairs based on their
    contribution to learning.

    Args:
        name: Identifier for logging (e.g., "generic", "set_set", "scalar_scalar")
        max_pairs: Maximum number of pairs to keep active (None = unlimited)
        exploration_epochs: Number of epochs before pruning starts
        top_k_fraction: Fraction of pairs to keep after exploration (0.0-1.0)
        lift_ema_alpha: EMA decay factor for lift (0.05-0.2)
        min_support_prune: Minimum observations before a pair can be pruned
        ucb_alpha: UCB exploration bonus coefficient
    """

    def __init__(
        self,
        name: str,
        max_pairs: Optional[int] = None,
        exploration_epochs: int = 10,
        top_k_fraction: float = 0.40,
        lift_ema_alpha: float = 0.1,
        min_support_prune: int = 20,
        ucb_alpha: float = 1.5,
    ):
        self.name = name
        self.max_pairs = max_pairs
        self.exploration_epochs = exploration_epochs
        self.top_k_fraction = top_k_fraction
        self.lift_ema_alpha = lift_ema_alpha
        self.min_support_prune = min_support_prune
        self.ucb_alpha = ucb_alpha

        # Pair statistics: (i, j) -> PairStats
        self._stats: Dict[Tuple[int, int], PairStats] = {}

        # Disabled pairs (pruned based on low lift)
        self.disabled_pairs: Set[Tuple[int, int]] = set()

        # All possible pairs for this scorer
        self.all_pairs: List[Tuple[int, int]] = []

        # Current epoch (for exploration vs exploitation)
        self.current_epoch: int = 0

        # Track total observations for global statistics
        self._total_observations: int = 0

    def initialize_pairs(self, pairs: List[Tuple[int, int]]) -> None:
        """Initialize the set of pairs this scorer will track.

        Args:
            pairs: List of (i, j) pairs to track
        """
        self.all_pairs = list(pairs)
        for pair in pairs:
            if pair not in self._stats:
                self._stats[pair] = PairStats()

        logger.info(f"🎯 PairScorer[{self.name}]: Initialized with {len(pairs)} pairs"
                   f" (max={self.max_pairs or 'unlimited'})")

    def get_active_pairs(self) -> List[Tuple[int, int]]:
        """Get list of currently active (non-disabled) pairs.

        If max_pairs is set and we have more than that,
        returns top-K by importance score.
        """
        active = [p for p in self.all_pairs if p not in self.disabled_pairs]

        # If no limit or within limit, return all active
        if self.max_pairs is None or len(active) <= self.max_pairs:
            return active

        # Otherwise, select top-K by importance
        scored = [(p, self._compute_importance(p)) for p in active]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [p for p, _ in scored[:self.max_pairs]]

    def update_lift(
        self,
        pair: Tuple[int, int],
        lift: float,
        epoch: int,
    ) -> None:
        """Update lift statistics for a pair.

        Args:
            pair: (i, j) pair
            lift: Computed lift value (positive = helpful, negative = harmful)
            epoch: Current training epoch
        """
        if pair not in self._stats:
            self._stats[pair] = PairStats()

        stats = self._stats[pair]
        stats.n += 1
        stats.last_epoch_active = epoch

        # EMA update for lift
        if stats.n == 1:
            stats.lift_ema = lift
        else:
            stats.lift_ema = (1 - self.lift_ema_alpha) * stats.lift_ema + self.lift_ema_alpha * lift

        # Track for variance computation
        stats.lift_sum += lift
        stats.lift_sum_sq += lift * lift

        self._total_observations += 1

    def _compute_importance(self, pair: Tuple[int, int]) -> float:
        """Compute importance score for a pair using lift + UCB.

        Returns:
            Importance score (higher = more important)
        """
        stats = self._stats.get(pair)
        if stats is None or stats.n == 0:
            # Unknown pairs get high score for exploration
            return float('inf')

        # Base score is lift EMA
        score = stats.lift_ema

        # Add UCB exploration bonus
        if self._total_observations > 0:
            ucb_bonus = self.ucb_alpha * math.sqrt(
                math.log(self._total_observations + 1) / (stats.n + 1)
            )
            score += ucb_bonus

        return score

    def should_prune(self) -> bool:
        """Check if we should prune pairs this epoch."""
        return (
            self.current_epoch >= self.exploration_epochs and
            len(self.disabled_pairs) < len(self.all_pairs)
        )

    def prune_bottom_pairs(self, n_to_prune: int = 1) -> List[Tuple[int, int]]:
        """Prune the N lowest-performing pairs.

        Args:
            n_to_prune: Number of pairs to disable

        Returns:
            List of pairs that were disabled
        """
        active = [p for p in self.all_pairs if p not in self.disabled_pairs]

        # Only prune pairs with sufficient observations
        prunable = [
            p for p in active
            if self._stats.get(p, PairStats()).n >= self.min_support_prune
        ]

        if not prunable:
            return []

        # Sort by importance (ascending - worst first)
        scored = [(p, self._compute_importance(p)) for p in prunable]
        scored.sort(key=lambda x: x[1])

        # Disable the worst N
        newly_disabled = []
        for pair, score in scored[:n_to_prune]:
            # Only prune if lift is negative (actually harmful)
            if score < 0:
                self.disabled_pairs.add(pair)
                newly_disabled.append(pair)

        if newly_disabled:
            logger.info(f"🔪 PairScorer[{self.name}]: Pruned {len(newly_disabled)} pairs "
                       f"(active: {len(active) - len(newly_disabled)}/{len(self.all_pairs)})")

        return newly_disabled

    def get_stats_summary(self) -> Dict:
        """Get summary statistics for logging."""
        active = [p for p in self.all_pairs if p not in self.disabled_pairs]

        lift_values = [
            self._stats[p].lift_ema
            for p in active
            if p in self._stats and self._stats[p].n > 0
        ]

        return {
            'name': self.name,
            'total_pairs': len(self.all_pairs),
            'active_pairs': len(active),
            'disabled_pairs': len(self.disabled_pairs),
            'total_observations': self._total_observations,
            'mean_lift': sum(lift_values) / len(lift_values) if lift_values else 0.0,
            'min_lift': min(lift_values) if lift_values else 0.0,
            'max_lift': max(lift_values) if lift_values else 0.0,
        }

    def log_stats(self) -> None:
        """Log current statistics."""
        stats = self.get_stats_summary()
        logger.info(
            f"📊 PairScorer[{self.name}]: "
            f"{stats['active_pairs']}/{stats['total_pairs']} active, "
            f"lift: mean={stats['mean_lift']:.4f}, "
            f"range=[{stats['min_lift']:.4f}, {stats['max_lift']:.4f}]"
        )

    def advance_epoch(self) -> None:
        """Advance to the next epoch."""
        self.current_epoch += 1

    def get_state_dict(self) -> Dict:
        """Get state for checkpointing."""
        return {
            'name': self.name,
            'max_pairs': self.max_pairs,
            'exploration_epochs': self.exploration_epochs,
            'top_k_fraction': self.top_k_fraction,
            'lift_ema_alpha': self.lift_ema_alpha,
            'min_support_prune': self.min_support_prune,
            'ucb_alpha': self.ucb_alpha,
            'stats': {
                str(k): {
                    'n': v.n,
                    'lift_ema': v.lift_ema,
                    'lift_sum': v.lift_sum,
                    'lift_sum_sq': v.lift_sum_sq,
                    'last_epoch_active': v.last_epoch_active,
                }
                for k, v in self._stats.items()
            },
            'disabled_pairs': [list(p) for p in self.disabled_pairs],
            'all_pairs': [list(p) for p in self.all_pairs],
            'current_epoch': self.current_epoch,
            'total_observations': self._total_observations,
        }

    def load_state_dict(self, state: Dict) -> None:
        """Load state from checkpoint."""
        self.name = state.get('name', self.name)
        self.max_pairs = state.get('max_pairs', self.max_pairs)
        self.exploration_epochs = state.get('exploration_epochs', self.exploration_epochs)
        self.top_k_fraction = state.get('top_k_fraction', self.top_k_fraction)
        self.lift_ema_alpha = state.get('lift_ema_alpha', self.lift_ema_alpha)
        self.min_support_prune = state.get('min_support_prune', self.min_support_prune)
        self.ucb_alpha = state.get('ucb_alpha', self.ucb_alpha)
        self.current_epoch = state.get('current_epoch', 0)
        self._total_observations = state.get('total_observations', 0)

        # Restore stats
        self._stats = {}
        for k_str, v in state.get('stats', {}).items():
            # Parse tuple key from string
            k = eval(k_str)  # Safe: we serialized it ourselves
            self._stats[k] = PairStats(
                n=v['n'],
                lift_ema=v['lift_ema'],
                lift_sum=v.get('lift_sum', 0.0),
                lift_sum_sq=v.get('lift_sum_sq', 0.0),
                last_epoch_active=v.get('last_epoch_active', -1),
            )

        # Restore sets
        self.disabled_pairs = {tuple(p) for p in state.get('disabled_pairs', [])}
        self.all_pairs = [tuple(p) for p in state.get('all_pairs', [])]
