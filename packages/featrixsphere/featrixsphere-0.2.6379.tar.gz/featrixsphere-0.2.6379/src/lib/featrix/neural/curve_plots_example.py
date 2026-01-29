"""
Example: Classification Curve Plots for Binary Classification

This shows all the curves we'd want to emit for D3 interactive widgets.
Each curve includes the raw data points and metadata needed for interactivity.

Curves included:
1. ROC Curve (TPR vs FPR) - with AUC, operating points
2. PR Curve (Precision vs Recall) - with AP, iso-F1 lines
3. Calibration Curve (reliability diagram) - with ECE, MCE
4. Cost Curve - cost vs threshold for different cost ratios
5. Threshold Curves - metrics (F1, precision, recall, accuracy) vs threshold
6. Lift Chart - lift vs percentage of population
7. Cumulative Gains - % of positives captured vs % of population
8. Decision Curve Analysis (DCA) - net benefit vs threshold

Run with: python -m src.lib.featrix.neural.curve_plots_example
"""

import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import (
    roc_curve, auc, precision_recall_curve, average_precision_score,
    confusion_matrix, f1_score, precision_score, recall_score,
    brier_score_loss
)
from sklearn.calibration import calibration_curve
from typing import Dict, List, Tuple, Any
import json


def compute_all_curve_data(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    cost_fp: float = 1.0,
    cost_fn: float = 1.0,
    n_bins: int = 10,
    n_thresholds: int = 101
) -> Dict[str, Any]:
    """
    Compute all curve data needed for interactive D3 widgets.

    Args:
        y_true: Binary ground truth labels (0 or 1)
        y_prob: Predicted probabilities for positive class
        cost_fp: Cost of false positive
        cost_fn: Cost of false negative
        n_bins: Number of bins for calibration curve
        n_thresholds: Number of thresholds for threshold-based curves

    Returns:
        Dictionary with all curve data and metadata
    """
    y_true = np.array(y_true)
    y_prob = np.array(y_prob)

    n_samples = len(y_true)
    n_pos = y_true.sum()
    n_neg = n_samples - n_pos
    prevalence = n_pos / n_samples

    result = {
        "metadata": {
            "n_samples": int(n_samples),
            "n_positive": int(n_pos),
            "n_negative": int(n_neg),
            "prevalence": float(prevalence),
            "cost_fp": cost_fp,
            "cost_fn": cost_fn,
        },
        "curves": {}
    }

    # =========================================================================
    # 1. ROC CURVE
    # =========================================================================
    fpr, tpr, roc_thresholds = roc_curve(y_true, y_prob)
    roc_auc = auc(fpr, tpr)

    # Youden's J statistic (optimal point on ROC)
    youdens_j = tpr - fpr
    youden_idx = np.argmax(youdens_j)
    youden_threshold = roc_thresholds[youden_idx]
    youden_point = (fpr[youden_idx], tpr[youden_idx])

    result["curves"]["roc"] = {
        "description": "Receiver Operating Characteristic - TPR vs FPR at various thresholds",
        "x_label": "False Positive Rate (1 - Specificity)",
        "y_label": "True Positive Rate (Sensitivity/Recall)",
        "auc": float(roc_auc),
        "points": [
            {"fpr": float(f), "tpr": float(t), "threshold": float(th) if th != np.inf else 1.0}
            for f, t, th in zip(fpr, tpr, roc_thresholds)
        ],
        "operating_points": {
            "youden": {
                "threshold": float(youden_threshold) if youden_threshold != np.inf else 1.0,
                "fpr": float(youden_point[0]),
                "tpr": float(youden_point[1]),
                "youdens_j": float(youdens_j[youden_idx]),
                "description": "Maximizes TPR - FPR (balanced accuracy)"
            },
            "diagonal": {
                "description": "Random classifier baseline",
                "points": [[0, 0], [1, 1]]
            }
        }
    }

    # =========================================================================
    # 2. PR CURVE (Precision-Recall)
    # =========================================================================
    precision, recall, pr_thresholds = precision_recall_curve(y_true, y_prob)
    pr_auc = average_precision_score(y_true, y_prob)

    # F1 at each point
    f1_scores = 2 * (precision * recall) / (precision + recall + 1e-10)
    best_f1_idx = np.argmax(f1_scores[:-1])  # Last point is (1, 0) sentinel
    best_f1_threshold = pr_thresholds[best_f1_idx] if best_f1_idx < len(pr_thresholds) else 0.5

    # Iso-F1 curves (for visualization)
    iso_f1_values = [0.2, 0.4, 0.6, 0.8]
    iso_f1_curves = []
    for f1_val in iso_f1_values:
        # F1 = 2PR/(P+R) => P = F1*R / (2R - F1)
        r_range = np.linspace(f1_val / 2 + 0.01, 1.0, 50)
        p_range = f1_val * r_range / (2 * r_range - f1_val)
        valid = (p_range > 0) & (p_range <= 1)
        iso_f1_curves.append({
            "f1": f1_val,
            "points": [{"recall": float(r), "precision": float(p)}
                       for r, p in zip(r_range[valid], p_range[valid])]
        })

    result["curves"]["pr"] = {
        "description": "Precision-Recall Curve - precision vs recall at various thresholds",
        "x_label": "Recall (Sensitivity/TPR)",
        "y_label": "Precision (Positive Predictive Value)",
        "auc": float(pr_auc),
        "points": [
            {"precision": float(p), "recall": float(r),
             "threshold": float(pr_thresholds[i]) if i < len(pr_thresholds) else 1.0,
             "f1": float(f1_scores[i])}
            for i, (p, r) in enumerate(zip(precision, recall))
        ],
        "operating_points": {
            "best_f1": {
                "threshold": float(best_f1_threshold),
                "precision": float(precision[best_f1_idx]),
                "recall": float(recall[best_f1_idx]),
                "f1": float(f1_scores[best_f1_idx]),
                "description": "Maximizes F1 score"
            },
            "baseline": {
                "precision": float(prevalence),
                "description": "Random classifier baseline (horizontal line at prevalence)"
            }
        },
        "iso_f1_curves": iso_f1_curves
    }

    # =========================================================================
    # 3. CALIBRATION CURVE (Reliability Diagram)
    # =========================================================================
    try:
        prob_true, prob_pred = calibration_curve(y_true, y_prob, n_bins=n_bins, strategy='uniform')

        # Compute bin counts for confidence intervals
        bin_edges = np.linspace(0, 1, n_bins + 1)
        bin_counts = []
        for i in range(n_bins):
            in_bin = (y_prob >= bin_edges[i]) & (y_prob < bin_edges[i + 1])
            bin_counts.append(int(in_bin.sum()))

        # ECE and MCE
        ece = np.mean(np.abs(prob_true - prob_pred) * np.array(bin_counts[:len(prob_true)]) / n_samples)
        mce = np.max(np.abs(prob_true - prob_pred))
        brier = brier_score_loss(y_true, y_prob)

        result["curves"]["calibration"] = {
            "description": "Calibration Curve - observed frequency vs predicted probability",
            "x_label": "Mean Predicted Probability",
            "y_label": "Fraction of Positives",
            "ece": float(ece),
            "mce": float(mce),
            "brier_score": float(brier),
            "n_bins": n_bins,
            "points": [
                {"predicted": float(pred), "observed": float(true), "count": count}
                for pred, true, count in zip(prob_pred, prob_true, bin_counts[:len(prob_true)])
            ],
            "perfect_calibration": {
                "description": "Perfect calibration line (y = x)",
                "points": [[0, 0], [1, 1]]
            },
            "histogram": {
                "description": "Distribution of predicted probabilities",
                "bins": [float(e) for e in bin_edges],
                "counts": bin_counts
            }
        }
    except Exception as e:
        result["curves"]["calibration"] = {"error": str(e)}

    # =========================================================================
    # 4. THRESHOLD CURVES (F1, Precision, Recall, Accuracy vs Threshold)
    # =========================================================================
    thresholds = np.linspace(0, 1, n_thresholds)
    threshold_metrics = []

    for t in thresholds:
        y_pred = (y_prob >= t).astype(int)

        # Compute all metrics at this threshold
        tp = ((y_true == 1) & (y_pred == 1)).sum()
        fp = ((y_true == 0) & (y_pred == 1)).sum()
        tn = ((y_true == 0) & (y_pred == 0)).sum()
        fn = ((y_true == 1) & (y_pred == 0)).sum()

        prec = tp / (tp + fp) if (tp + fp) > 0 else 0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0
        spec = tn / (tn + fp) if (tn + fp) > 0 else 0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0
        acc = (tp + tn) / n_samples
        balanced_acc = (rec + spec) / 2
        mcc_num = (tp * tn - fp * fn)
        mcc_den = np.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
        mcc = mcc_num / mcc_den if mcc_den > 0 else 0

        # Cost at this threshold
        cost = cost_fp * fp + cost_fn * fn

        # Youden's J
        youdens = rec + spec - 1  # TPR + TNR - 1 = TPR - FPR

        threshold_metrics.append({
            "threshold": float(t),
            "precision": float(prec),
            "recall": float(rec),
            "specificity": float(spec),
            "f1": float(f1),
            "accuracy": float(acc),
            "balanced_accuracy": float(balanced_acc),
            "mcc": float(mcc),
            "youdens_j": float(youdens),
            "cost": float(cost),
            "tp": int(tp),
            "fp": int(fp),
            "tn": int(tn),
            "fn": int(fn),
            "predicted_positive_rate": float((tp + fp) / n_samples)
        })

    # Find optimal thresholds for each metric
    f1_optimal_idx = max(range(len(threshold_metrics)), key=lambda i: threshold_metrics[i]["f1"])
    cost_optimal_idx = min(range(len(threshold_metrics)), key=lambda i: threshold_metrics[i]["cost"])
    youden_optimal_idx = max(range(len(threshold_metrics)), key=lambda i: threshold_metrics[i]["youdens_j"])
    balanced_acc_optimal_idx = max(range(len(threshold_metrics)), key=lambda i: threshold_metrics[i]["balanced_accuracy"])

    result["curves"]["threshold_metrics"] = {
        "description": "Various metrics as a function of classification threshold",
        "x_label": "Threshold",
        "y_label": "Metric Value",
        "points": threshold_metrics,
        "optimal_thresholds": {
            "f1": {
                "threshold": threshold_metrics[f1_optimal_idx]["threshold"],
                "value": threshold_metrics[f1_optimal_idx]["f1"],
                "description": "Maximizes F1 score"
            },
            "cost": {
                "threshold": threshold_metrics[cost_optimal_idx]["threshold"],
                "value": threshold_metrics[cost_optimal_idx]["cost"],
                "description": f"Minimizes cost (C_FP={cost_fp}, C_FN={cost_fn})"
            },
            "youden": {
                "threshold": threshold_metrics[youden_optimal_idx]["threshold"],
                "value": threshold_metrics[youden_optimal_idx]["youdens_j"],
                "description": "Maximizes TPR - FPR (Youden's J)"
            },
            "balanced_accuracy": {
                "threshold": threshold_metrics[balanced_acc_optimal_idx]["threshold"],
                "value": threshold_metrics[balanced_acc_optimal_idx]["balanced_accuracy"],
                "description": "Maximizes (TPR + TNR) / 2"
            }
        }
    }

    # =========================================================================
    # 4b. THRESHOLD PROFILES TABLE (the "money shot")
    # Quick-pick table for users to select a threshold strategy in 10 seconds
    # =========================================================================
    profiles = []

    # Helper to get metrics at a specific threshold index
    def get_profile_row(name: str, description: str, idx: int) -> dict:
        m = threshold_metrics[idx]
        return {
            "name": name,
            "description": description,
            "threshold": m["threshold"],
            "precision": m["precision"],
            "recall": m["recall"],
            "f1": m["f1"],
            "fpr": 1.0 - m["specificity"],  # FPR = 1 - TNR
            "specificity": m["specificity"],
            "accuracy": m["accuracy"],
            "tp": m["tp"],
            "fp": m["fp"],
            "fn": m["fn"],
            "tn": m["tn"],
            "predicted_positive_rate": m["predicted_positive_rate"]
        }

    # 1. Conservative (High Precision): highest threshold with Precision >= 0.80
    precision_target = 0.80
    conservative_idx = None
    for i, m in enumerate(threshold_metrics):
        if m["precision"] >= precision_target:
            conservative_idx = i
            break
    if conservative_idx is None:
        # Can't hit 0.80, find best precision achievable
        conservative_idx = max(range(len(threshold_metrics)),
                               key=lambda i: threshold_metrics[i]["precision"])
        actual_prec = threshold_metrics[conservative_idx]["precision"]
        profiles.append(get_profile_row(
            "Conservative (High Precision)",
            f"Best precision achievable: {actual_prec:.0%} (target 80% not reachable)",
            conservative_idx
        ))
    else:
        profiles.append(get_profile_row(
            "Conservative (High Precision)",
            f"Highest threshold with Precision >= {precision_target:.0%}",
            conservative_idx
        ))

    # 2. Balanced (F1): argmax F1
    profiles.append(get_profile_row(
        "Balanced (F1)",
        "Maximizes F1 score (harmonic mean of precision and recall)",
        f1_optimal_idx
    ))

    # 3. Recall-Heavy: max recall subject to Precision >= 0.60
    recall_prec_floor = 0.60
    recall_heavy_idx = None
    best_recall_at_prec = -1
    for i, m in enumerate(threshold_metrics):
        if m["precision"] >= recall_prec_floor and m["recall"] > best_recall_at_prec:
            best_recall_at_prec = m["recall"]
            recall_heavy_idx = i
    if recall_heavy_idx is None:
        # Can't hit 0.60 precision, use best F1 as fallback
        recall_heavy_idx = f1_optimal_idx
        profiles.append(get_profile_row(
            "Recall-Heavy",
            f"(Fallback to F1 - precision floor {recall_prec_floor:.0%} not achievable)",
            recall_heavy_idx
        ))
    else:
        profiles.append(get_profile_row(
            "Recall-Heavy",
            f"Max recall with Precision >= {recall_prec_floor:.0%}",
            recall_heavy_idx
        ))

    # 4. Low False Alarms (FPR cap): max recall subject to FPR <= 0.10
    fpr_cap = 0.10
    low_fpr_idx = None
    best_recall_at_fpr = -1
    for i, m in enumerate(threshold_metrics):
        fpr = 1.0 - m["specificity"]
        if fpr <= fpr_cap and m["recall"] > best_recall_at_fpr:
            best_recall_at_fpr = m["recall"]
            low_fpr_idx = i
    if low_fpr_idx is None:
        # Can't hit FPR <= 0.10, find lowest FPR achievable
        low_fpr_idx = min(range(len(threshold_metrics)),
                         key=lambda i: 1.0 - threshold_metrics[i]["specificity"])
        actual_fpr = 1.0 - threshold_metrics[low_fpr_idx]["specificity"]
        profiles.append(get_profile_row(
            "Low False Alarms (FPR cap)",
            f"Best FPR achievable: {actual_fpr:.1%} (target 10% not reachable)",
            low_fpr_idx
        ))
    else:
        profiles.append(get_profile_row(
            "Low False Alarms (FPR cap)",
            f"Max recall with FPR <= {fpr_cap:.0%}",
            low_fpr_idx
        ))

    # 5. Cost-Based: argmin cost_fp * FP + cost_fn * FN
    profiles.append(get_profile_row(
        "Cost-Based",
        f"Minimizes cost (C_FP={cost_fp}, C_FN={cost_fn})",
        cost_optimal_idx
    ))

    # 6. Youden's J (Balanced TPR/TNR)
    profiles.append(get_profile_row(
        "Youden's J (Balanced)",
        "Maximizes TPR - FPR (equal weight to sensitivity and specificity)",
        youden_optimal_idx
    ))

    result["threshold_profiles"] = {
        "description": "Quick-pick threshold strategies - select one in 10 seconds",
        "columns": ["Profile", "Threshold", "Precision", "Recall", "FPR", "TP", "FP", "FN", "TN"],
        "profiles": profiles
    }

    # =========================================================================
    # 5. COST CURVE (cost vs threshold for different cost ratios)
    # =========================================================================
    cost_ratios = [0.5, 1.0, 2.0, 5.0, 10.0]  # cost_fn / cost_fp ratios
    cost_curves = []

    for ratio in cost_ratios:
        costs = []
        for t in thresholds:
            y_pred = (y_prob >= t).astype(int)
            fp = ((y_true == 0) & (y_pred == 1)).sum()
            fn = ((y_true == 1) & (y_pred == 0)).sum()
            cost = 1.0 * fp + ratio * fn  # Normalize with C_FP = 1
            costs.append(float(cost))

        optimal_idx = np.argmin(costs)
        cost_curves.append({
            "cost_ratio": ratio,
            "label": f"C_FN/C_FP = {ratio}",
            "costs": costs,
            "optimal_threshold": float(thresholds[optimal_idx]),
            "optimal_cost": float(costs[optimal_idx])
        })

    result["curves"]["cost"] = {
        "description": "Total cost vs threshold for different cost ratios",
        "x_label": "Threshold",
        "y_label": "Total Cost (C_FP=1 normalized)",
        "thresholds": [float(t) for t in thresholds],
        "cost_curves": cost_curves,
        "theoretical_optimal": {
            "description": "Bayes-optimal threshold = C_FP / (C_FP + C_FN)",
            "formula": "threshold = 1 / (1 + cost_ratio)"
        }
    }

    # =========================================================================
    # 6. LIFT CHART
    # =========================================================================
    # Sort by predicted probability descending
    sorted_indices = np.argsort(-y_prob)
    sorted_labels = y_true[sorted_indices]

    # Cumulative positives
    cum_positives = np.cumsum(sorted_labels)
    n_points = len(sorted_labels)

    lift_points = []
    percentiles = np.linspace(0.01, 1.0, 100)
    for pct in percentiles:
        n_selected = int(pct * n_points)
        if n_selected == 0:
            continue

        positives_in_selection = cum_positives[n_selected - 1]
        expected_positives = n_selected * prevalence
        lift = positives_in_selection / expected_positives if expected_positives > 0 else 0

        lift_points.append({
            "percentile": float(pct),
            "lift": float(lift),
            "positives_captured": int(positives_in_selection),
            "n_selected": n_selected
        })

    result["curves"]["lift"] = {
        "description": "Lift Chart - how much better than random at each percentile",
        "x_label": "Percentage of Population (ranked by score)",
        "y_label": "Lift (ratio to random)",
        "points": lift_points,
        "baseline": {
            "lift": 1.0,
            "description": "Random model baseline"
        }
    }

    # =========================================================================
    # 7. CUMULATIVE GAINS CHART
    # =========================================================================
    gains_points = []
    for pct in percentiles:
        n_selected = int(pct * n_points)
        if n_selected == 0:
            continue

        positives_in_selection = cum_positives[n_selected - 1]
        pct_positives_captured = positives_in_selection / n_pos if n_pos > 0 else 0

        gains_points.append({
            "percentile": float(pct),
            "pct_positives_captured": float(pct_positives_captured),
            "positives_captured": int(positives_in_selection),
            "total_positives": int(n_pos)
        })

    # Wizard curve (perfect model)
    wizard_points = []
    for pct in percentiles:
        n_selected = int(pct * n_points)
        # Perfect model captures all positives first
        pct_captured = min(n_selected / n_pos, 1.0) if n_pos > 0 else 0
        wizard_points.append({
            "percentile": float(pct),
            "pct_positives_captured": float(pct_captured)
        })

    result["curves"]["cumulative_gains"] = {
        "description": "Cumulative Gains - % of positives captured vs % of population",
        "x_label": "Percentage of Population (ranked by score)",
        "y_label": "Percentage of Positives Captured",
        "points": gains_points,
        "wizard": {
            "points": wizard_points,
            "description": "Perfect model (captures all positives first)"
        },
        "baseline": {
            "description": "Random model (diagonal line)",
            "points": [[0, 0], [1, 1]]
        }
    }

    # =========================================================================
    # 8. DECISION CURVE ANALYSIS (DCA)
    # =========================================================================
    # Net benefit = (TP/N) - (FP/N) * (p_t / (1 - p_t))
    # where p_t is the threshold probability
    dca_points = []
    treat_all_points = []

    for t in thresholds[1:-1]:  # Avoid 0 and 1
        y_pred = (y_prob >= t).astype(int)
        tp = ((y_true == 1) & (y_pred == 1)).sum()
        fp = ((y_true == 0) & (y_pred == 1)).sum()

        # Net benefit for model
        odds = t / (1 - t) if t < 1 else float('inf')
        net_benefit = (tp / n_samples) - (fp / n_samples) * odds

        # Net benefit for "treat all"
        treat_all_tp = n_pos
        treat_all_fp = n_neg
        treat_all_net_benefit = (treat_all_tp / n_samples) - (treat_all_fp / n_samples) * odds

        dca_points.append({
            "threshold": float(t),
            "net_benefit": float(net_benefit),
            "tp": int(tp),
            "fp": int(fp)
        })

        treat_all_points.append({
            "threshold": float(t),
            "net_benefit": float(treat_all_net_benefit)
        })

    result["curves"]["decision_curve"] = {
        "description": "Decision Curve Analysis - net benefit vs threshold probability",
        "x_label": "Threshold Probability",
        "y_label": "Net Benefit",
        "model_points": dca_points,
        "treat_all_points": treat_all_points,
        "treat_none": {
            "net_benefit": 0.0,
            "description": "Treat none baseline (always 0)"
        },
        "interpretation": "Model is useful where its curve is above both baselines"
    }

    return result


def plot_all_curves(curve_data: Dict[str, Any], save_path: str = None):
    """
    Create a multi-panel matplotlib figure showing all curves.
    """
    fig, axes = plt.subplots(3, 3, figsize=(15, 15))
    fig.suptitle("Classification Performance Curves", fontsize=14, fontweight='bold')

    metadata = curve_data["metadata"]
    curves = curve_data["curves"]

    # 1. ROC Curve
    ax = axes[0, 0]
    roc = curves["roc"]
    fpr = [p["fpr"] for p in roc["points"]]
    tpr = [p["tpr"] for p in roc["points"]]
    ax.plot(fpr, tpr, 'b-', linewidth=2, label=f'ROC (AUC={roc["auc"]:.3f})')
    ax.plot([0, 1], [0, 1], 'k--', linewidth=1, label='Random')

    # Mark Youden's point
    youden = roc["operating_points"]["youden"]
    ax.scatter([youden["fpr"]], [youden["tpr"]], c='red', s=100, zorder=5,
               label=f'Youden (t={youden["threshold"]:.2f})')

    ax.set_xlabel(roc["x_label"])
    ax.set_ylabel(roc["y_label"])
    ax.set_title("ROC Curve")
    ax.legend(loc='lower right')
    ax.set_xlim([0, 1])
    ax.set_ylim([0, 1])
    ax.grid(True, alpha=0.3)

    # 2. PR Curve
    ax = axes[0, 1]
    pr = curves["pr"]
    recall = [p["recall"] for p in pr["points"]]
    precision = [p["precision"] for p in pr["points"]]
    ax.plot(recall, precision, 'b-', linewidth=2, label=f'PR (AP={pr["auc"]:.3f})')

    # Baseline
    ax.axhline(y=pr["operating_points"]["baseline"]["precision"], color='k',
               linestyle='--', linewidth=1, label='Random')

    # Mark best F1 point
    best_f1 = pr["operating_points"]["best_f1"]
    ax.scatter([best_f1["recall"]], [best_f1["precision"]], c='red', s=100, zorder=5,
               label=f'Best F1={best_f1["f1"]:.2f} (t={best_f1["threshold"]:.2f})')

    # Iso-F1 curves
    for iso in pr["iso_f1_curves"]:
        r = [p["recall"] for p in iso["points"]]
        p = [p["precision"] for p in iso["points"]]
        ax.plot(r, p, 'g--', alpha=0.3)
        if len(r) > 0:
            ax.text(r[-1], p[-1], f'F1={iso["f1"]}', fontsize=8, alpha=0.5)

    ax.set_xlabel(pr["x_label"])
    ax.set_ylabel(pr["y_label"])
    ax.set_title("Precision-Recall Curve")
    ax.legend(loc='lower left')
    ax.set_xlim([0, 1])
    ax.set_ylim([0, 1])
    ax.grid(True, alpha=0.3)

    # 3. Calibration Curve
    ax = axes[0, 2]
    if "error" not in curves["calibration"]:
        cal = curves["calibration"]
        pred = [p["predicted"] for p in cal["points"]]
        obs = [p["observed"] for p in cal["points"]]
        counts = [p["count"] for p in cal["points"]]

        ax.plot([0, 1], [0, 1], 'k--', linewidth=1, label='Perfect')
        ax.scatter(pred, obs, s=[c/max(counts)*500 for c in counts], c='blue', alpha=0.6,
                   label=f'ECE={cal["ece"]:.3f}')
        ax.plot(pred, obs, 'b-', alpha=0.5)

        ax.set_xlabel(cal["x_label"])
        ax.set_ylabel(cal["y_label"])
        ax.set_title(f'Calibration (Brier={cal["brier_score"]:.3f})')
        ax.legend()
        ax.set_xlim([0, 1])
        ax.set_ylim([0, 1])
        ax.grid(True, alpha=0.3)

    # 4. Threshold Metrics
    ax = axes[1, 0]
    tm = curves["threshold_metrics"]
    thresholds = [p["threshold"] for p in tm["points"]]
    f1s = [p["f1"] for p in tm["points"]]
    precs = [p["precision"] for p in tm["points"]]
    recs = [p["recall"] for p in tm["points"]]
    specs = [p["specificity"] for p in tm["points"]]

    ax.plot(thresholds, f1s, 'b-', linewidth=2, label='F1')
    ax.plot(thresholds, precs, 'g-', linewidth=1.5, label='Precision')
    ax.plot(thresholds, recs, 'r-', linewidth=1.5, label='Recall')
    ax.plot(thresholds, specs, 'm-', linewidth=1.5, label='Specificity')

    # Mark optimal thresholds
    f1_opt = tm["optimal_thresholds"]["f1"]
    ax.axvline(x=f1_opt["threshold"], color='b', linestyle=':', alpha=0.5)

    ax.set_xlabel("Threshold")
    ax.set_ylabel("Metric Value")
    ax.set_title("Metrics vs Threshold")
    ax.legend(loc='center left')
    ax.set_xlim([0, 1])
    ax.set_ylim([0, 1])
    ax.grid(True, alpha=0.3)

    # 5. Cost Curve
    ax = axes[1, 1]
    cost = curves["cost"]
    thresholds = cost["thresholds"]
    for cc in cost["cost_curves"]:
        ax.plot(thresholds, cc["costs"], label=cc["label"])
        ax.scatter([cc["optimal_threshold"]], [cc["optimal_cost"]], s=50, zorder=5)

    ax.set_xlabel(cost["x_label"])
    ax.set_ylabel(cost["y_label"])
    ax.set_title("Cost vs Threshold")
    ax.legend(loc='upper right', fontsize=8)
    ax.set_xlim([0, 1])
    ax.grid(True, alpha=0.3)

    # 6. Youden's J and Balanced Accuracy
    ax = axes[1, 2]
    youdens = [p["youdens_j"] for p in tm["points"]]
    bal_acc = [p["balanced_accuracy"] for p in tm["points"]]
    mcc = [p["mcc"] for p in tm["points"]]

    ax.plot(thresholds, youdens, 'b-', linewidth=2, label="Youden's J (TPR-FPR)")
    ax.plot(thresholds, bal_acc, 'g-', linewidth=2, label="Balanced Accuracy")
    ax.plot(thresholds, mcc, 'r-', linewidth=2, label="MCC")

    youden_opt = tm["optimal_thresholds"]["youden"]
    ax.axvline(x=youden_opt["threshold"], color='b', linestyle=':', alpha=0.5,
               label=f'Youden opt={youden_opt["threshold"]:.2f}')

    ax.set_xlabel("Threshold")
    ax.set_ylabel("Metric Value")
    ax.set_title("Balanced Metrics vs Threshold")
    ax.legend(loc='best', fontsize=8)
    ax.set_xlim([0, 1])
    ax.grid(True, alpha=0.3)

    # 7. Lift Chart
    ax = axes[2, 0]
    lift = curves["lift"]
    pcts = [p["percentile"] for p in lift["points"]]
    lifts = [p["lift"] for p in lift["points"]]

    ax.plot(pcts, lifts, 'b-', linewidth=2, label='Model')
    ax.axhline(y=1.0, color='k', linestyle='--', label='Random')

    ax.set_xlabel(lift["x_label"])
    ax.set_ylabel(lift["y_label"])
    ax.set_title("Lift Chart")
    ax.legend()
    ax.set_xlim([0, 1])
    ax.grid(True, alpha=0.3)

    # 8. Cumulative Gains
    ax = axes[2, 1]
    gains = curves["cumulative_gains"]
    pcts = [p["percentile"] for p in gains["points"]]
    captured = [p["pct_positives_captured"] for p in gains["points"]]
    wizard_pcts = [p["percentile"] for p in gains["wizard"]["points"]]
    wizard_captured = [p["pct_positives_captured"] for p in gains["wizard"]["points"]]

    ax.plot(pcts, captured, 'b-', linewidth=2, label='Model')
    ax.plot(wizard_pcts, wizard_captured, 'g-', linewidth=1.5, label='Perfect')
    ax.plot([0, 1], [0, 1], 'k--', linewidth=1, label='Random')

    ax.set_xlabel(gains["x_label"])
    ax.set_ylabel(gains["y_label"])
    ax.set_title("Cumulative Gains")
    ax.legend()
    ax.set_xlim([0, 1])
    ax.set_ylim([0, 1])
    ax.grid(True, alpha=0.3)

    # 9. Decision Curve Analysis
    ax = axes[2, 2]
    dca = curves["decision_curve"]
    dca_thresholds = [p["threshold"] for p in dca["model_points"]]
    dca_nb = [p["net_benefit"] for p in dca["model_points"]]
    treat_all_nb = [p["net_benefit"] for p in dca["treat_all_points"]]

    ax.plot(dca_thresholds, dca_nb, 'b-', linewidth=2, label='Model')
    ax.plot(dca_thresholds, treat_all_nb, 'r-', linewidth=1.5, label='Treat All')
    ax.axhline(y=0, color='k', linestyle='--', label='Treat None')

    ax.set_xlabel(dca["x_label"])
    ax.set_ylabel(dca["y_label"])
    ax.set_title("Decision Curve Analysis")
    ax.legend(loc='upper right')
    ax.set_xlim([0, 1])
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved to {save_path}")

    # plt.show()  # Comment out for non-interactive use
    plt.close(fig)
    return fig


def demo():
    """Generate demo curves with synthetic data."""
    np.random.seed(42)

    # Create imbalanced binary classification data
    n_samples = 1000
    n_pos = 100  # 10% positive rate

    # Simulate predictions: positive class gets higher scores on average
    # But with significant overlap to create realistic AUC ~0.75-0.85
    y_true = np.array([1] * n_pos + [0] * (n_samples - n_pos))

    # Positive class: mean ~0.55, some overlap with negatives
    pos_probs = np.random.beta(3, 3, n_pos) * 0.6 + 0.25  # Range ~0.25-0.85, mean ~0.55

    # Negative class: mean ~0.35, some overlap with positives
    neg_probs = np.random.beta(3, 4, n_samples - n_pos) * 0.6 + 0.1  # Range ~0.1-0.7, mean ~0.35

    y_prob = np.concatenate([pos_probs, neg_probs])
    y_prob = np.clip(y_prob, 0.01, 0.99)

    # Shuffle
    indices = np.random.permutation(n_samples)
    y_true = y_true[indices]
    y_prob = y_prob[indices]

    print("=" * 60)
    print("Computing all classification curves...")
    print(f"  n_samples: {n_samples}")
    print(f"  n_positive: {n_pos} ({n_pos/n_samples:.1%})")
    print("=" * 60)

    # Compute all curve data
    curve_data = compute_all_curve_data(
        y_true, y_prob,
        cost_fp=1.0,
        cost_fn=5.0,  # False negatives cost 5x more
        n_bins=10,
        n_thresholds=101
    )

    # Print summary
    print("\nMetadata:")
    print(json.dumps(curve_data["metadata"], indent=2))

    print(f"\nROC AUC: {curve_data['curves']['roc']['auc']:.3f}")
    print(f"PR AUC:  {curve_data['curves']['pr']['auc']:.3f}")

    # Print the MONEY SHOT - threshold profiles table
    print("\n" + "=" * 100)
    print("THRESHOLD PROFILES (pick one in 10 seconds)")
    print("=" * 100)
    print(f"{'Profile':<30} {'Thr':>6} {'Prec':>7} {'Recall':>7} {'F1':>6} {'FPR':>6} {'TP':>5} {'FP':>5} {'FN':>5} {'TN':>5}")
    print("-" * 100)
    for p in curve_data["threshold_profiles"]["profiles"]:
        print(f"{p['name']:<30} {p['threshold']:>6.2f} {p['precision']:>6.1%} {p['recall']:>6.1%} {p['f1']:>6.2f} {p['fpr']:>5.1%} {p['tp']:>5} {p['fp']:>5} {p['fn']:>5} {p['tn']:>5}")
    print("-" * 100)

    # Save JSON for D3
    json_path = "/Users/admin/Desktop/tetra-ws/featrix/taco-fixes/curve_data_example.json"
    with open(json_path, 'w') as f:
        json.dump(curve_data, f, indent=2)
    print(f"\nSaved JSON data to: {json_path}")

    # Plot
    plot_all_curves(
        curve_data,
        save_path="/Users/admin/Desktop/tetra-ws/featrix/taco-fixes/classification_curves.png"
    )


if __name__ == "__main__":
    demo()
