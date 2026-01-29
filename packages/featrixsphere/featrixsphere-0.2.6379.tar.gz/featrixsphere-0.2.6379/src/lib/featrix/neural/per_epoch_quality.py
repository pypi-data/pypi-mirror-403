"""
Per-Epoch Quality Assessment

Lightweight quality checks that run every epoch during ES training.
Provides immediate feedback on embedding health without expensive computations.
"""

import logging
from typing import Dict, Tuple, Optional, List

logger = logging.getLogger(__name__)


def compute_epoch_quality_score(
    epoch_idx: int,
    current_emb_std: Optional[float],
    baseline_emb_std: Optional[float],
    gradient_norm: Optional[float],
    ranking_metrics: Optional[Dict[str, float]] = None,
    ww_instability: bool = False
) -> Tuple[float, str, List[str], Dict[str, float]]:
    """
    Compute a lightweight quality score for the current epoch.

    This runs every epoch and provides immediate feedback on training health
    without the overhead of full quality assessment.

    Args:
        epoch_idx: Current epoch number
        current_emb_std: Current embedding std/dim (from collapse diagnostics)
        baseline_emb_std: Baseline embedding std/dim (from early epochs, e.g. epoch 5)
        gradient_norm: Unclipped gradient norm
        ranking_metrics: Dict with recall_at_1, recall_at_5, margin_mean, auc, etc.
        ww_instability: Whether WeightWatcher detected instability this epoch

    Returns:
        Tuple of (score: float 0-100, grade: str A-F, warnings: List[str], breakdown: Dict[str, float])

    Score breakdown:
        - Embedding health (40 points): Based on std/dim (absolute threshold)
        - Gradient health (30 points): Based on gradient norm (absolute threshold)
        - Ranking quality (30 points): Based on Recall@1, AUC (absolute metrics)
    """
    score = 0.0
    warnings = []
    breakdown = {}  # Track component scores and explanations

    # =========================================================================
    # COMPONENT 1: EMBEDDING HEALTH (40 points)
    # =========================================================================
    embedding_score = 0.0
    embedding_reason = ""

    if current_emb_std is not None:
        # Absolute std/dim thresholds
        if current_emb_std >= 0.04:
            embedding_score = 40.0  # Excellent
            embedding_reason = f"std/dim={current_emb_std:.4f} ≥ 0.04 (healthy)"
        elif current_emb_std >= 0.03:
            embedding_score = 32.0  # Good (80%)
            embedding_reason = f"std/dim={current_emb_std:.4f} slightly low"
            warnings.append(f"⚠️  Embedding std/dim slightly low: {current_emb_std:.4f} (target: >0.04)")
        elif current_emb_std >= 0.02:
            embedding_score = 24.0  # Fair (60%)
            embedding_reason = f"std/dim={current_emb_std:.4f} compressed"
            warnings.append(f"⚠️  Embedding compression detected: {current_emb_std:.4f} (target: >0.04)")
        elif current_emb_std >= 0.01:
            embedding_score = 12.0  # Poor (30%)
            embedding_reason = f"std/dim={current_emb_std:.4f} collapsing"
            warnings.append(f"❌ Moderate embedding collapse: {current_emb_std:.4f} (target: >0.04)")
        else:
            embedding_score = 0.0  # Critical
            embedding_reason = f"std/dim={current_emb_std:.4f} COLLAPSED"
            warnings.append(f"❌ CRITICAL: Severe embedding collapse: {current_emb_std:.4f} (target: >0.04)")

        # Check for progressive collapse (if we have baseline)
        if baseline_emb_std is not None and baseline_emb_std > 0:
            decline_pct = ((baseline_emb_std - current_emb_std) / baseline_emb_std) * 100
            if decline_pct > 50:
                embedding_score *= 0.5  # Penalize 50% for progressive collapse
                embedding_reason += f", -{decline_pct:.0f}% from baseline"
                warnings.append(f"❌ Progressive collapse: {decline_pct:.1f}% decline from baseline")
            elif decline_pct > 20:
                embedding_score *= 0.8  # Penalize 20% for variance degradation
                embedding_reason += f", -{decline_pct:.0f}% from baseline"
                warnings.append(f"⚠️  Variance degrading: {decline_pct:.1f}% decline from baseline")
    else:
        # No embedding data available
        embedding_score = 20.0  # Neutral score (50% of max)
        embedding_reason = "no data (neutral)"

    score += embedding_score
    breakdown['embedding'] = {'score': embedding_score, 'max': 40, 'reason': embedding_reason}

    # =========================================================================
    # COMPONENT 2: GRADIENT HEALTH (30 points)
    # =========================================================================
    gradient_score = 0.0
    gradient_reason = ""

    if gradient_norm is not None:
        # Reasonable gradient norms for ES training (calibrated for real datasets with 100+ columns)
        # These thresholds are much higher than SP training because ES has many more parameters
        grad_str = f"{gradient_norm:.2f}" if gradient_norm < 1000 else f"{gradient_norm:.2e}"
        if gradient_norm < 0.01:
            gradient_score = 10.0  # Very small gradients (33%)
            gradient_reason = f"grad={grad_str} too small (dead network?)"
            warnings.append(f"⚠️  Very small gradients: {gradient_norm:.6f} (may indicate dead network)")
        elif gradient_norm < 5000:
            gradient_score = 30.0  # Healthy range for ES training
            gradient_reason = f"grad={grad_str} < 5K (healthy)"
        elif gradient_norm < 15000:
            gradient_score = 25.0  # Elevated but manageable (83%)
            gradient_reason = f"grad={grad_str} elevated but ok"
            # No warning - this is normal for large ES
        elif gradient_norm < 50000:
            gradient_score = 15.0  # High - watch it (50%)
            gradient_reason = f"grad={grad_str} high"
            warnings.append(f"⚠️  High gradient norm: {gradient_norm:.2f}")
        elif gradient_norm < 100000:
            gradient_score = 5.0  # Very high - instability risk (17%)
            gradient_reason = f"grad={grad_str} very high"
            warnings.append(f"❌ Very high gradient norm: {gradient_norm:.2f} (instability risk)")
        else:
            gradient_score = 0.0  # Exploding
            gradient_reason = f"grad={grad_str} EXPLODING"
            warnings.append(f"❌ CRITICAL: Gradient explosion: {gradient_norm:.2e}")
    else:
        # No gradient data available
        gradient_score = 15.0  # Neutral score (50% of max)
        gradient_reason = "no data (neutral)"

    # Penalize if WeightWatcher detected instability
    if ww_instability:
        gradient_score *= 0.5  # Cut gradient score in half
        gradient_reason += " + WW instability"
        warnings.append("⚠️  WeightWatcher detected instability")

    score += gradient_score
    breakdown['gradient'] = {'score': gradient_score, 'max': 30, 'reason': gradient_reason}

    # =========================================================================
    # COMPONENT 3: RANKING QUALITY (30 points)
    # Based on absolute metrics: Recall@1, AUC - these directly measure prediction quality
    # =========================================================================
    ranking_score = 0.0
    ranking_reason = ""

    if ranking_metrics is not None:
        recall_at_1 = ranking_metrics.get('recall_at_1', 0)
        auc = ranking_metrics.get('auc', 0)

        # Recall@1 is the primary metric (0-1 scale, higher is better)
        # Random baseline for 100 columns would be ~1%, so anything >10% is learning
        # Good models get 80-95%+
        if recall_at_1 >= 0.90:
            ranking_score = 30.0  # Excellent
            ranking_reason = f"Recall@1={recall_at_1:.0%} (excellent)"
        elif recall_at_1 >= 0.80:
            ranking_score = 25.0  # Good
            ranking_reason = f"Recall@1={recall_at_1:.0%} (good)"
        elif recall_at_1 >= 0.50:
            ranking_score = 20.0  # Fair
            ranking_reason = f"Recall@1={recall_at_1:.0%} (learning)"
        elif recall_at_1 >= 0.10:
            ranking_score = 15.0  # Weak but learning
            ranking_reason = f"Recall@1={recall_at_1:.0%} (weak)"
            warnings.append(f"⚠️  Low Recall@1: {recall_at_1:.1%} (target: >50%)")
        elif recall_at_1 >= 0.02:
            ranking_score = 10.0  # Barely above random
            ranking_reason = f"Recall@1={recall_at_1:.0%} (barely learning)"
            warnings.append(f"⚠️  Very low Recall@1: {recall_at_1:.1%} (near random)")
        else:
            ranking_score = 5.0  # At or below random
            ranking_reason = f"Recall@1={recall_at_1:.0%} (random)"
            warnings.append(f"❌ Recall@1 at random baseline: {recall_at_1:.1%}")

        # Bonus/penalty based on AUC (should be close to 1.0)
        if auc >= 0.99:
            ranking_reason += f", AUC={auc:.3f}"
        elif auc < 0.90:
            ranking_score *= 0.8  # Penalize low AUC
            ranking_reason += f", AUC={auc:.3f} (low)"
            warnings.append(f"⚠️  Low AUC: {auc:.3f} (target: >0.95)")
    else:
        # No ranking metrics available (early epochs before diagnostics run)
        ranking_score = 15.0  # Neutral score (50% of max)
        ranking_reason = "no ranking data yet"

    score += ranking_score
    breakdown['ranking'] = {'score': ranking_score, 'max': 30, 'reason': ranking_reason}

    # =========================================================================
    # CONVERT SCORE TO GRADE
    # =========================================================================
    if score >= 90:
        grade = "A"
    elif score >= 80:
        grade = "B"
    elif score >= 70:
        grade = "C"
    elif score >= 60:
        grade = "D"
    else:
        grade = "F"

    return score, grade, warnings, breakdown


def log_epoch_quality(
    epoch_idx: int,
    n_epochs: int,
    score: float,
    grade: str,
    warnings: List[str],
    current_emb_std: Optional[float] = None,
    gradient_norm: Optional[float] = None,
    recall_at_1: Optional[float] = None,
    breakdown: Optional[Dict[str, float]] = None
) -> None:
    """
    Log the per-epoch quality assessment in a compact, readable format.

    Args:
        epoch_idx: Current epoch number
        n_epochs: Total epochs
        score: Quality score (0-100)
        grade: Letter grade (A-F)
        warnings: List of warning messages
        current_emb_std: Current embedding std/dim (for display)
        gradient_norm: Current gradient norm (for display)
        recall_at_1: Recall@1 metric (for display)
        breakdown: Dict with component scores (embedding, gradient, ranking)
    """
    # Compact one-line summary
    grade_emoji = {
        "A": "✅",
        "B": "👍",
        "C": "⚠️ ",
        "D": "❌",
        "F": "💥"
    }

    emoji = grade_emoji.get(grade, "❓")

    # Build metrics string
    metrics = []
    if current_emb_std is not None:
        metrics.append(f"std/dim={current_emb_std:.4f}")
    if gradient_norm is not None:
        if gradient_norm < 1000:
            metrics.append(f"grad={gradient_norm:.2f}")
        else:
            metrics.append(f"grad={gradient_norm:.2e}")
    if recall_at_1 is not None:
        metrics.append(f"Recall@1={recall_at_1:.1%}")

    metrics_str = ", ".join(metrics) if metrics else "no metrics"

    logger.info(f"{emoji} Epoch {epoch_idx}/{n_epochs} Quality: {grade} ({score:.0f}/100) | {metrics_str}")

    # Log score breakdown as a table with explanations
    if breakdown:
        emb = breakdown.get('embedding', {})
        grad = breakdown.get('gradient', {})
        rank = breakdown.get('ranking', {})

        # Extract scores and reasons
        emb_score = emb.get('score', 0) if isinstance(emb, dict) else emb
        emb_max = emb.get('max', 40) if isinstance(emb, dict) else 40
        emb_reason = emb.get('reason', '') if isinstance(emb, dict) else ''

        grad_score = grad.get('score', 0) if isinstance(grad, dict) else grad
        grad_max = grad.get('max', 30) if isinstance(grad, dict) else 30
        grad_reason = grad.get('reason', '') if isinstance(grad, dict) else ''

        rank_score = rank.get('score', 0) if isinstance(rank, dict) else rank
        rank_max = rank.get('max', 30) if isinstance(rank, dict) else 30
        rank_reason = rank.get('reason', '') if isinstance(rank, dict) else ''

        # Truncate reasons to fit in table (40 chars max)
        max_reason_len = 40
        emb_reason = emb_reason[:max_reason_len] if len(emb_reason) > max_reason_len else emb_reason
        grad_reason = grad_reason[:max_reason_len] if len(grad_reason) > max_reason_len else grad_reason
        rank_reason = rank_reason[:max_reason_len] if len(rank_reason) > max_reason_len else rank_reason

        # Log as a compact table
        logger.info(f"   ┌─────────────┬────────┬──────────────────────────────────────────┐")
        logger.info(f"   │ Component   │ Score  │ Reason                                   │")
        logger.info(f"   ├─────────────┼────────┼──────────────────────────────────────────┤")
        logger.info(f"   │ Embedding   │ {emb_score:2.0f}/{emb_max:2.0f}  │ {emb_reason:<40} │")
        logger.info(f"   │ Gradient    │ {grad_score:2.0f}/{grad_max:2.0f}  │ {grad_reason:<40} │")
        logger.info(f"   │ Ranking     │ {rank_score:2.0f}/{rank_max:2.0f}  │ {rank_reason:<40} │")
        logger.info(f"   ├─────────────┼────────┼──────────────────────────────────────────┤")
        logger.info(f"   │ TOTAL       │ {score:2.0f}/100 │ Grade: {grade}                                  │")
        logger.info(f"   └─────────────┴────────┴──────────────────────────────────────────┘")

    # Log warnings if any (indented for readability)
    if warnings:
        for warning in warnings:
            logger.info(f"   {warning}")


def should_stop_training(
    consecutive_failing_epochs: int,
    max_failing_epochs: int = 10
) -> bool:
    """
    Determine if training should stop based on consecutive failing quality checks.
    
    Args:
        consecutive_failing_epochs: Number of consecutive epochs with F grade
        max_failing_epochs: Maximum consecutive failures before stopping
    
    Returns:
        bool: True if training should stop
    """
    return consecutive_failing_epochs >= max_failing_epochs
