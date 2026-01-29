#  -*- coding: utf-8 -*-
#
#  Copyright Featrix, Inc 2023-2025
#
#  Proprietary and Confidential.  Unauthorized use, copying or dissemination
#  of these materials is strictly prohibited.
#
"""
AUC Animation Module

Generates animated visualizations of embedding space quality metrics over training.
The primary metric is AUC from the contrastive learning task:
  - AUC = P(positive > negative) where:
    - positive = similarity(row_i_masked, row_i_unmasked) (same row)
    - negative = similarity(row_i_masked, row_j_unmasked) (different rows)
  - AUC = 0.5 means random (can't distinguish same-row from different-row)
  - AUC = 1.0 means perfect (same-row always beats different-row)

This measures how well the encoder creates distinguishable row representations.
"""

import logging
import os
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


def extract_auc_history(training_timeline: List[Dict[str, Any]]) -> Dict[str, List]:
    """
    Extract AUC and related metrics from training timeline.

    Args:
        training_timeline: List of epoch entries from EmbeddingSpace._training_timeline

    Returns:
        Dict with keys:
            - epochs: list of epoch numbers
            - auc: list of AUC values (0.5 = random, 1.0 = perfect)
            - recall_at_1: list of recall@1 values (fraction of correct top-1 predictions)
            - recall_at_5: list of recall@5 values
            - entropy_normalized: list of normalized entropy (1.0 = random, 0.0 = confident)
            - margin_mean: list of mean margins (positive - max_negative)
    """
    epochs = []
    auc = []
    recall_at_1 = []
    recall_at_5 = []
    entropy_normalized = []
    margin_mean = []

    for entry in training_timeline:
        if not isinstance(entry, dict):
            continue

        epoch = entry.get("epoch")
        if epoch is None:
            continue

        # Extract ranking metrics from collapse_diagnostics
        collapse_diag = entry.get("collapse_diagnostics")
        if not collapse_diag or not isinstance(collapse_diag, dict):
            continue

        ranking = collapse_diag.get("ranking_metrics")
        if not ranking or not isinstance(ranking, dict):
            continue

        # Only add if we have AUC
        if "auc" not in ranking:
            continue

        epochs.append(epoch)
        auc.append(ranking.get("auc", 0.5))
        recall_at_1.append(ranking.get("recall_at_1", 0.0))
        recall_at_5.append(ranking.get("recall_at_5", 0.0))
        entropy_normalized.append(ranking.get("entropy_normalized", 1.0))
        margin_mean.append(ranking.get("margin_mean", 0.0))

    return {
        "epochs": epochs,
        "auc": auc,
        "recall_at_1": recall_at_1,
        "recall_at_5": recall_at_5,
        "entropy_normalized": entropy_normalized,
        "margin_mean": margin_mean,
    }


def create_auc_animation(
    training_timeline: List[Dict[str, Any]],
    output_path: str,
    fps: int = 2,
    figsize: tuple = (12, 8),
    dpi: int = 100,
) -> Optional[str]:
    """
    Create an animated GIF showing AUC and related metrics over training.

    Args:
        training_timeline: List of epoch entries from EmbeddingSpace._training_timeline
        output_path: Path to save the animated GIF
        fps: Frames per second for animation
        figsize: Figure size (width, height) in inches
        dpi: Dots per inch for output

    Returns:
        Path to saved animation, or None if failed
    """
    try:
        import matplotlib.pyplot as plt
        import matplotlib.animation as animation
        import numpy as np
    except ImportError:
        logger.warning("matplotlib not available, cannot create AUC animation")
        return None

    # Extract data
    data = extract_auc_history(training_timeline)
    if not data["epochs"]:
        logger.warning("No AUC data found in training timeline")
        return None

    epochs = data["epochs"]
    auc_vals = data["auc"]
    recall_1 = data["recall_at_1"]
    recall_5 = data["recall_at_5"]
    entropy = data["entropy_normalized"]

    n_frames = len(epochs)
    if n_frames < 2:
        logger.warning("Not enough epochs for animation (need at least 2)")
        return None

    # Create figure with subplots
    fig, axes = plt.subplots(2, 2, figsize=figsize)
    fig.suptitle("Embedding Space Quality Over Training", fontsize=14, fontweight="bold")

    # Colors
    auc_color = "#2563eb"  # Blue
    recall_color = "#10b981"  # Green
    entropy_color = "#f59e0b"  # Orange
    random_color = "#ef4444"  # Red (for baselines)

    def init():
        """Initialize empty plots."""
        for ax in axes.flat:
            ax.clear()
        return []

    def animate(frame):
        """Update plots for each frame."""
        for ax in axes.flat:
            ax.clear()

        # Current data up to this frame
        current_epochs = epochs[: frame + 1]
        current_auc = auc_vals[: frame + 1]
        current_recall_1 = recall_1[: frame + 1]
        current_recall_5 = recall_5[: frame + 1]
        current_entropy = entropy[: frame + 1]

        # ============== AUC Plot (top-left) ==============
        ax1 = axes[0, 0]
        ax1.plot(current_epochs, current_auc, "-o", color=auc_color, linewidth=2, markersize=4)
        ax1.axhline(0.5, color=random_color, linestyle="--", alpha=0.7, label="Random (0.5)")
        ax1.axhline(0.9, color="#22c55e", linestyle="--", alpha=0.5, label="Good (0.9)")
        ax1.set_xlim(0, max(epochs) + 1)
        ax1.set_ylim(0.4, 1.05)
        ax1.set_xlabel("Epoch")
        ax1.set_ylabel("AUC")
        ax1.set_title(f"Contrastive AUC: {current_auc[-1]:.3f}", fontweight="bold")
        ax1.legend(loc="lower right", fontsize=8)
        ax1.grid(True, alpha=0.3)

        # Fill area above random baseline
        ax1.fill_between(
            current_epochs,
            0.5,
            current_auc,
            where=[a > 0.5 for a in current_auc],
            alpha=0.2,
            color=auc_color,
        )

        # ============== Recall@1 Plot (top-right) ==============
        ax2 = axes[0, 1]
        ax2.plot(current_epochs, current_recall_1, "-o", color=recall_color, linewidth=2, markersize=4, label="Recall@1")
        ax2.plot(current_epochs, current_recall_5, "-s", color="#06b6d4", linewidth=2, markersize=3, label="Recall@5")

        # Random baseline for recall@1 = 1/batch_size (assume ~200)
        random_recall = 1 / 200
        ax2.axhline(random_recall, color=random_color, linestyle="--", alpha=0.7, label=f"Random ({random_recall:.3f})")

        ax2.set_xlim(0, max(epochs) + 1)
        ax2.set_ylim(0, min(1.0, max(max(recall_1), max(recall_5)) * 1.2 + 0.05))
        ax2.set_xlabel("Epoch")
        ax2.set_ylabel("Recall")
        ax2.set_title(f"Recall@1: {current_recall_1[-1]:.1%}", fontweight="bold")
        ax2.legend(loc="lower right", fontsize=8)
        ax2.grid(True, alpha=0.3)

        # ============== Entropy Plot (bottom-left) ==============
        ax3 = axes[1, 0]
        ax3.plot(current_epochs, current_entropy, "-o", color=entropy_color, linewidth=2, markersize=4)
        ax3.axhline(1.0, color=random_color, linestyle="--", alpha=0.7, label="Random (1.0)")
        ax3.axhline(0.5, color="#22c55e", linestyle="--", alpha=0.5, label="Good (<0.5)")
        ax3.set_xlim(0, max(epochs) + 1)
        ax3.set_ylim(0, 1.1)
        ax3.set_xlabel("Epoch")
        ax3.set_ylabel("Normalized Entropy")
        ax3.set_title(f"Prediction Entropy: {current_entropy[-1]:.2f}", fontweight="bold")
        ax3.legend(loc="upper right", fontsize=8)
        ax3.grid(True, alpha=0.3)

        # Fill area below random (good)
        ax3.fill_between(
            current_epochs,
            current_entropy,
            1.0,
            where=[e < 1.0 for e in current_entropy],
            alpha=0.2,
            color=entropy_color,
        )

        # ============== Summary Text (bottom-right) ==============
        ax4 = axes[1, 1]
        ax4.axis("off")

        # Current epoch stats
        current_epoch = current_epochs[-1]
        stats_text = f"""
Epoch {current_epoch}

CONTRASTIVE QUALITY:
  AUC:        {current_auc[-1]:.3f}  {"✅" if current_auc[-1] > 0.8 else "⚠️" if current_auc[-1] > 0.6 else "❌"}
  Recall@1:   {current_recall_1[-1]:.1%}  {"✅" if current_recall_1[-1] > 0.1 else "⚠️" if current_recall_1[-1] > 0.02 else "❌"}
  Recall@5:   {current_recall_5[-1]:.1%}
  Entropy:    {current_entropy[-1]:.2f}  {"✅" if current_entropy[-1] < 0.5 else "⚠️" if current_entropy[-1] < 0.8 else "❌"}

INTERPRETATION:
  AUC > 0.8: Embeddings distinguish rows well
  AUC ≈ 0.5: Embeddings look random
  Low entropy: Confident predictions
  High entropy: Uncertain/random
"""
        ax4.text(
            0.05,
            0.95,
            stats_text,
            transform=ax4.transAxes,
            fontsize=10,
            fontfamily="monospace",
            verticalalignment="top",
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5),
        )

        plt.tight_layout()
        return []

    # Create animation
    anim = animation.FuncAnimation(
        fig, animate, init_func=init, frames=n_frames, interval=1000 // fps, blit=False
    )

    # Save as GIF
    try:
        anim.save(output_path, writer="pillow", fps=fps, dpi=dpi)
        logger.info(f"🎬 AUC animation saved to: {output_path}")
        plt.close(fig)
        return output_path
    except Exception as e:
        logger.error(f"Failed to save AUC animation: {e}")
        plt.close(fig)
        return None


def create_auc_static_plot(
    training_timeline: List[Dict[str, Any]],
    output_path: str,
    figsize: tuple = (14, 10),
) -> Optional[str]:
    """
    Create a static multi-panel plot showing AUC and related metrics over training.

    This is faster than animation and useful for quick analysis.

    Args:
        training_timeline: List of epoch entries from EmbeddingSpace._training_timeline
        output_path: Path to save the PNG

    Returns:
        Path to saved plot, or None if failed
    """
    try:
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        logger.warning("matplotlib not available, cannot create AUC plot")
        return None

    # Extract data
    data = extract_auc_history(training_timeline)
    if not data["epochs"]:
        logger.warning("No AUC data found in training timeline")
        return None

    epochs = data["epochs"]
    auc_vals = data["auc"]
    recall_1 = data["recall_at_1"]
    recall_5 = data["recall_at_5"]
    entropy = data["entropy_normalized"]
    margin = data["margin_mean"]

    # Create figure
    fig, axes = plt.subplots(2, 2, figsize=figsize)
    fig.suptitle("Embedding Space Quality Over Training", fontsize=14, fontweight="bold")

    # Colors
    auc_color = "#2563eb"
    recall_color = "#10b981"
    entropy_color = "#f59e0b"
    margin_color = "#8b5cf6"
    random_color = "#ef4444"

    # ============== AUC Plot ==============
    ax1 = axes[0, 0]
    ax1.plot(epochs, auc_vals, "-o", color=auc_color, linewidth=2, markersize=3)
    ax1.axhline(0.5, color=random_color, linestyle="--", alpha=0.7, label="Random (0.5)")
    ax1.axhline(0.9, color="#22c55e", linestyle="--", alpha=0.5, label="Good (0.9)")
    ax1.fill_between(epochs, 0.5, auc_vals, where=[a > 0.5 for a in auc_vals], alpha=0.2, color=auc_color)
    ax1.set_xlabel("Epoch")
    ax1.set_ylabel("AUC")
    ax1.set_title("Contrastive AUC", fontweight="bold")
    ax1.legend(loc="lower right", fontsize=8)
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim(0.4, 1.05)

    # ============== Recall Plot ==============
    ax2 = axes[0, 1]
    ax2.plot(epochs, recall_1, "-o", color=recall_color, linewidth=2, markersize=3, label="Recall@1")
    ax2.plot(epochs, recall_5, "-s", color="#06b6d4", linewidth=2, markersize=2, label="Recall@5")
    random_recall = 1 / 200
    ax2.axhline(random_recall, color=random_color, linestyle="--", alpha=0.7, label=f"Random ({random_recall:.3f})")
    ax2.set_xlabel("Epoch")
    ax2.set_ylabel("Recall")
    ax2.set_title("Recall@K", fontweight="bold")
    ax2.legend(loc="lower right", fontsize=8)
    ax2.grid(True, alpha=0.3)

    # ============== Entropy Plot ==============
    ax3 = axes[1, 0]
    ax3.plot(epochs, entropy, "-o", color=entropy_color, linewidth=2, markersize=3)
    ax3.axhline(1.0, color=random_color, linestyle="--", alpha=0.7, label="Random (1.0)")
    ax3.fill_between(epochs, entropy, 1.0, where=[e < 1.0 for e in entropy], alpha=0.2, color=entropy_color)
    ax3.set_xlabel("Epoch")
    ax3.set_ylabel("Normalized Entropy")
    ax3.set_title("Prediction Entropy (lower = more confident)", fontweight="bold")
    ax3.legend(loc="upper right", fontsize=8)
    ax3.grid(True, alpha=0.3)
    ax3.set_ylim(0, 1.1)

    # ============== Margin Plot ==============
    ax4 = axes[1, 1]
    ax4.plot(epochs, margin, "-o", color=margin_color, linewidth=2, markersize=3)
    ax4.axhline(0, color=random_color, linestyle="--", alpha=0.7, label="Zero margin")
    ax4.fill_between(epochs, 0, margin, where=[m > 0 for m in margin], alpha=0.2, color=margin_color)
    ax4.set_xlabel("Epoch")
    ax4.set_ylabel("Mean Margin")
    ax4.set_title("Margin (positive - max_negative)", fontweight="bold")
    ax4.legend(loc="lower right", fontsize=8)
    ax4.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    logger.info(f"📊 AUC plot saved to: {output_path}")
    return output_path


def save_auc_animation_from_es(embedding_space, output_dir: str = None) -> Optional[str]:
    """
    Convenience function to create AUC animation from an EmbeddingSpace object.

    Args:
        embedding_space: EmbeddingSpace instance with _training_timeline
        output_dir: Directory to save animation (defaults to ES output_dir)

    Returns:
        Path to saved animation, or None if failed
    """
    if not hasattr(embedding_space, "_training_timeline") or not embedding_space._training_timeline:
        logger.warning("No training timeline available for AUC animation")
        return None

    if output_dir is None:
        output_dir = getattr(embedding_space, "output_dir", ".")

    output_path = os.path.join(output_dir, "auc_animation.gif")
    return create_auc_animation(embedding_space._training_timeline, output_path)


def save_auc_plot_from_es(embedding_space, output_dir: str = None) -> Optional[str]:
    """
    Convenience function to create static AUC plot from an EmbeddingSpace object.

    Args:
        embedding_space: EmbeddingSpace instance with _training_timeline
        output_dir: Directory to save plot (defaults to ES output_dir)

    Returns:
        Path to saved plot, or None if failed
    """
    if not hasattr(embedding_space, "_training_timeline") or not embedding_space._training_timeline:
        logger.warning("No training timeline available for AUC plot")
        return None

    if output_dir is None:
        output_dir = getattr(embedding_space, "output_dir", ".")

    output_path = os.path.join(output_dir, "auc_quality.png")
    return create_auc_static_plot(embedding_space._training_timeline, output_path)
