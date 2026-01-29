#!/usr/bin/env python3
"""
auto_calibrate.py

Drop-in calibration utilities for PyTorch models (binary + multiclass).

Goals:
- Accept Torch tensors (logits + labels) as the primary interface.
- Provide multiple calibration methods:
    1) Temperature Scaling (TS)  [works for binary + multiclass]
    2) Platt Scaling / Logistic calibration (binary only) via sklearn
    3) Isotonic Regression (binary only) via sklearn
    4) Vector/Per-class Temperature Scaling (multiclass; optional)
- Compute standard calibration metrics:
    - NLL (cross-entropy)
    - Brier score
    - ECE / MCE (expected / max calibration error)
    - Accuracy, AUROC (binary), PR-AUC (binary) [optional sklearn]
- Save a "calibration packet" JSON with:
    - raw probs, calibrated probs, bin stats, thresholds
- Save a reliability diagram (matplotlib) and optional histograms.
- Provide an "auto" mode that evaluates candidate calibrators on a held-out split
  and picks the best by a chosen objective (default: NLL, then ECE tie-break).

Dependencies:
- torch
- numpy  (only used for small bridges and JSON)
- matplotlib (for plots)
- scikit-learn (for isotonic/logistic + optional AUROC/PR-AUC)
"""

from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union, Literal

import torch
import torch.nn as nn
import torch.nn.functional as F

# Optional deps
try:
    import numpy as np
except Exception:  # pragma: no cover
    np = None

try:
    from sklearn.isotonic import IsotonicRegression
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score, average_precision_score
except Exception:  # pragma: no cover
    IsotonicRegression = None
    LogisticRegression = None
    roc_auc_score = None
    average_precision_score = None

try:
    import matplotlib.pyplot as plt
except Exception:  # pragma: no cover
    plt = None


Tensor = torch.Tensor
CalibObjective = Literal["nll", "ece", "brier"]


# -----------------------------
# Metrics
# -----------------------------

@torch.no_grad()
def softmax_probs(logits: Tensor) -> Tensor:
    if logits.ndim != 2:
        raise ValueError(f"logits must be (N, C), got {tuple(logits.shape)}")
    return F.softmax(logits, dim=-1)


@torch.no_grad()
def binary_probs_from_logits(logits: Tensor, pos_index: int = 1) -> Tensor:
    """
    For binary classifier logits shape (N,2), returns P(class=pos_index).
    """
    probs = softmax_probs(logits)
    if probs.shape[1] != 2:
        raise ValueError("binary_probs_from_logits expects logits with C=2")
    return probs[:, pos_index]


@torch.no_grad()
def nll_from_logits(logits: Tensor, labels: Tensor) -> float:
    """
    Multiclass NLL = cross entropy.
    labels: (N,) int64 in [0..C-1]
    """
    labels = labels.long()
    loss = F.cross_entropy(logits, labels, reduction="mean")
    return float(loss.item())


@torch.no_grad()
def brier_score_multiclass(probs: Tensor, labels: Tensor) -> float:
    """
    Multiclass Brier score:
      mean over samples of sum_k (p_k - y_k)^2
    """
    labels = labels.long()
    n, c = probs.shape
    y = torch.zeros((n, c), device=probs.device, dtype=probs.dtype)
    y.scatter_(1, labels.view(-1, 1), 1.0)
    return float(((probs - y) ** 2).sum(dim=1).mean().item())


@torch.no_grad()
def brier_score_binary(p_pos: Tensor, y_pos: Tensor) -> float:
    """
    Binary Brier score: mean((p - y)^2)
    y_pos: {0,1}
    """
    y_pos = y_pos.float()
    return float(((p_pos - y_pos) ** 2).mean().item())


@torch.no_grad()
def ece_mce(
    probs: Tensor,
    labels: Tensor,
    n_bins: int = 15,
) -> Tuple[float, float, List[Dict[str, Any]]]:
    """
    ECE/MCE for multiclass using:
      conf = max prob
      pred = argmax
      acc(bin) vs conf(bin)
    Returns: (ece, mce, bins)
      bins: list of dicts with counts, avg_conf, avg_acc, gap
    """
    labels = labels.long()
    conf, pred = probs.max(dim=1)
    correct = (pred == labels).float()

    # bins are [0,1] partitioned into n_bins
    bin_edges = torch.linspace(0, 1, n_bins + 1, device=probs.device)
    ece = torch.tensor(0.0, device=probs.device)
    mce = torch.tensor(0.0, device=probs.device)

    out_bins: List[Dict[str, Any]] = []
    n = probs.shape[0]

    for i in range(n_bins):
        lo = bin_edges[i]
        hi = bin_edges[i + 1]
        # include right edge on last bin
        if i == n_bins - 1:
            mask = (conf >= lo) & (conf <= hi)
        else:
            mask = (conf >= lo) & (conf < hi)

        count = int(mask.sum().item())
        if count == 0:
            out_bins.append(
                {
                    "bin": i,
                    "lo": float(lo.item()),
                    "hi": float(hi.item()),
                    "n": 0,
                    "avg_conf": None,
                    "avg_acc": None,
                    "gap": None,
                }
            )
            continue

        avg_conf = conf[mask].mean()
        avg_acc = correct[mask].mean()
        gap = (avg_acc - avg_conf).abs()

        ece = ece + (count / n) * gap
        mce = torch.maximum(mce, gap)

        out_bins.append(
            {
                "bin": i,
                "lo": float(lo.item()),
                "hi": float(hi.item()),
                "n": count,
                "avg_conf": float(avg_conf.item()),
                "avg_acc": float(avg_acc.item()),
                "gap": float((avg_acc - avg_conf).item()),
            }
        )

    return float(ece.item()), float(mce.item()), out_bins


@torch.no_grad()
def binary_reliability_bins(
    p_pos: Tensor,
    y_pos: Tensor,
    n_bins: int = 15,
) -> List[Dict[str, Any]]:
    """
    Reliability bins for binary: bin by predicted p_pos.
    For each bin: empirical positive rate vs mean predicted probability.
    """
    y_pos = y_pos.float()
    bin_edges = torch.linspace(0, 1, n_bins + 1, device=p_pos.device)
    out_bins: List[Dict[str, Any]] = []
    n = p_pos.shape[0]

    for i in range(n_bins):
        lo = bin_edges[i]
        hi = bin_edges[i + 1]
        if i == n_bins - 1:
            mask = (p_pos >= lo) & (p_pos <= hi)
        else:
            mask = (p_pos >= lo) & (p_pos < hi)

        count = int(mask.sum().item())
        if count == 0:
            out_bins.append(
                {
                    "bin": i,
                    "lo": float(lo.item()),
                    "hi": float(hi.item()),
                    "n": 0,
                    "avg_p": None,
                    "emp_rate": None,
                    "gap": None,
                }
            )
            continue

        avg_p = p_pos[mask].mean()
        emp = y_pos[mask].mean()
        out_bins.append(
            {
                "bin": i,
                "lo": float(lo.item()),
                "hi": float(hi.item()),
                "n": count,
                "avg_p": float(avg_p.item()),
                "emp_rate": float(emp.item()),
                "gap": float((emp - avg_p).item()),
            }
        )
    return out_bins


# -----------------------------
# Calibrators
# -----------------------------

class CalibratorBase:
    """
    Base class for calibrators. Works on logits.
    """

    def fit(self, logits: Tensor, labels: Tensor) -> "CalibratorBase":
        raise NotImplementedError

    def transform_logits(self, logits: Tensor) -> Tensor:
        raise NotImplementedError

    def transform_probs(self, logits: Tensor) -> Tensor:
        return softmax_probs(self.transform_logits(logits))

    def state_dict(self) -> Dict[str, Any]:
        return {}

    def load_state_dict(self, state: Dict[str, Any]) -> None:
        _ = state


class IdentityCalibrator(CalibratorBase):
    def fit(self, logits: Tensor, labels: Tensor) -> "IdentityCalibrator":
        return self

    def transform_logits(self, logits: Tensor) -> Tensor:
        return logits


class TemperatureScaling(CalibratorBase):
    """
    Classic temperature scaling:
      logits' = logits / T
    T optimized to minimize NLL on calibration set.
    """

    def __init__(self, init_T: float = 1.0, max_iter: int = 200, lr: float = 0.05):
        self.init_T = float(init_T)
        self.max_iter = int(max_iter)
        self.lr = float(lr)
        self._T: Optional[float] = None

    def fit(self, logits: Tensor, labels: Tensor) -> "TemperatureScaling":
        device = logits.device
        labels = labels.long()

        # constrain T > 0 by optimizing log_T
        log_T = torch.tensor(math.log(self.init_T), device=device, requires_grad=True)

        optimizer = torch.optim.LBFGS([log_T], lr=self.lr, max_iter=self.max_iter)

        def closure():
            optimizer.zero_grad(set_to_none=True)
            T = torch.exp(log_T)
            loss = F.cross_entropy(logits / T, labels, reduction="mean")
            loss.backward()
            return loss

        optimizer.step(closure)
        self._T = float(torch.exp(log_T).detach().item())
        return self

    def transform_logits(self, logits: Tensor) -> Tensor:
        if self._T is None:
            raise RuntimeError("TemperatureScaling not fitted")
        return logits / self._T

    def state_dict(self) -> Dict[str, Any]:
        return {"T": self._T, "type": "temperature_scaling"}

    def load_state_dict(self, state: Dict[str, Any]) -> None:
        self._T = float(state["T"])


class VectorTemperatureScaling(CalibratorBase):
    """
    Multiclass vector temperature scaling:
      logits'_c = logits_c / T_c
    This is more flexible than scalar T, but can overfit on small calibration sets.
    """

    def __init__(self, max_iter: int = 200, lr: float = 0.05):
        self.max_iter = int(max_iter)
        self.lr = float(lr)
        self._T: Optional[Tensor] = None  # shape (C,)

    def fit(self, logits: Tensor, labels: Tensor) -> "VectorTemperatureScaling":
        device = logits.device
        labels = labels.long()
        _, c = logits.shape

        log_T = torch.zeros((c,), device=device, requires_grad=True)
        optimizer = torch.optim.LBFGS([log_T], lr=self.lr, max_iter=self.max_iter)

        def closure():
            optimizer.zero_grad(set_to_none=True)
            T = torch.exp(log_T).clamp_min(1e-6)
            loss = F.cross_entropy(logits / T, labels, reduction="mean")
            loss.backward()
            return loss

        optimizer.step(closure)
        self._T = torch.exp(log_T).detach()
        return self

    def transform_logits(self, logits: Tensor) -> Tensor:
        if self._T is None:
            raise RuntimeError("VectorTemperatureScaling not fitted")
        return logits / self._T

    def state_dict(self) -> Dict[str, Any]:
        return {"T": self._T.detach().cpu().tolist(), "type": "vector_temperature_scaling"}

    def load_state_dict(self, state: Dict[str, Any]) -> None:
        self._T = torch.tensor(state["T"], dtype=torch.float32)


class SklearnBinaryPlatt(CalibratorBase):
    """
    Platt scaling (logistic regression on logit scores).
    Uses sklearn LogisticRegression on a single score:
      score = logit_pos - logit_neg
    """

    def __init__(self):
        if LogisticRegression is None or np is None:
            raise ImportError("scikit-learn and numpy required for SklearnBinaryPlatt")
        self.model = LogisticRegression(solver="lbfgs")
        self._fitted = False

    def fit(self, logits: Tensor, labels: Tensor) -> "SklearnBinaryPlatt":
        if logits.shape[1] != 2:
            raise ValueError("SklearnBinaryPlatt expects C=2 logits")
        # score as log-odds proxy
        score = (logits[:, 1] - logits[:, 0]).detach().cpu().float().numpy().reshape(-1, 1)
        y = labels.detach().cpu().long().numpy()
        self.model.fit(score, y)
        self._fitted = True
        return self

    def transform_logits(self, logits: Tensor) -> Tensor:
        if not self._fitted:
            raise RuntimeError("SklearnBinaryPlatt not fitted")
        score = (logits[:, 1] - logits[:, 0]).detach().cpu().float().numpy().reshape(-1, 1)
        p1 = self.model.predict_proba(score)[:, 1]
        # return logits reconstructed from calibrated prob
        p1_t = torch.tensor(p1, device=logits.device, dtype=logits.dtype).clamp(1e-6, 1 - 1e-6)
        # logit(p) for positive; convert to 2-class logits with symmetric form
        logit_p = torch.log(p1_t) - torch.log1p(-p1_t)
        out = torch.stack([-0.5 * logit_p, 0.5 * logit_p], dim=1)
        return out

    def state_dict(self) -> Dict[str, Any]:
        return {"type": "sklearn_platt", "coef": self.model.coef_.tolist(), "intercept": self.model.intercept_.tolist()}

    def load_state_dict(self, state: Dict[str, Any]) -> None:
        # reconstruct LogisticRegression parameters
        coef = np.array(state["coef"])
        intercept = np.array(state["intercept"])
        self.model = LogisticRegression(solver="lbfgs")
        self.model.classes_ = np.array([0, 1])
        self.model.coef_ = coef
        self.model.intercept_ = intercept
        self._fitted = True


class SklearnBinaryIsotonic(CalibratorBase):
    """
    Isotonic regression on p_pos from softmax(logits).
    Works only for binary.
    """

    def __init__(self, y_min: float = 0.0, y_max: float = 1.0, out_of_bounds: str = "clip"):
        if IsotonicRegression is None or np is None:
            raise ImportError("scikit-learn and numpy required for SklearnBinaryIsotonic")
        self.iso = IsotonicRegression(y_min=y_min, y_max=y_max, out_of_bounds=out_of_bounds)
        self._fitted = False

    def fit(self, logits: Tensor, labels: Tensor) -> "SklearnBinaryIsotonic":
        if logits.shape[1] != 2:
            raise ValueError("SklearnBinaryIsotonic expects C=2 logits")
        p = binary_probs_from_logits(logits).detach().cpu().float().numpy()
        y = labels.detach().cpu().long().numpy()
        self.iso.fit(p, y)
        self._fitted = True
        return self

    def transform_logits(self, logits: Tensor) -> Tensor:
        if not self._fitted:
            raise RuntimeError("SklearnBinaryIsotonic not fitted")
        p = binary_probs_from_logits(logits).detach().cpu().float().numpy()
        p_cal = self.iso.predict(p)
        p_cal_t = torch.tensor(p_cal, device=logits.device, dtype=logits.dtype).clamp(1e-6, 1 - 1e-6)
        logit_p = torch.log(p_cal_t) - torch.log1p(-p_cal_t)
        out = torch.stack([-0.5 * logit_p, 0.5 * logit_p], dim=1)
        return out

    def state_dict(self) -> Dict[str, Any]:
        # isotonic stores breakpoints internally; easiest is to pickle in your system.
        # Here we export the learned knots plus min/max for predict().
        return {
            "type": "sklearn_isotonic",
            "X_thresholds": self.iso.X_thresholds_.tolist(),
            "y_thresholds": self.iso.y_thresholds_.tolist(),
            "X_min": float(self.iso.X_min_),
            "X_max": float(self.iso.X_max_),
            "increasing": bool(self.iso.increasing_),
        }

    def load_state_dict(self, state: Dict[str, Any]) -> None:
        from scipy.interpolate import interp1d

        self.iso = IsotonicRegression(out_of_bounds="clip")
        self.iso.X_thresholds_ = np.array(state["X_thresholds"], dtype=float)
        self.iso.y_thresholds_ = np.array(state["y_thresholds"], dtype=float)
        self.iso.X_min_ = state["X_min"]
        self.iso.X_max_ = state["X_max"]
        self.iso.increasing_ = state["increasing"]
        # Rebuild the interpolation function that sklearn uses internally
        self.iso.f_ = interp1d(
            self.iso.X_thresholds_,
            self.iso.y_thresholds_,
            kind="linear",
            bounds_error=False,
            fill_value=(self.iso.y_thresholds_[0], self.iso.y_thresholds_[-1]),
        )
        self._fitted = True


# -----------------------------
# Evaluation + Auto selection
# -----------------------------

@dataclass
class CalibReport:
    name: str
    objective: CalibObjective
    metrics: Dict[str, float]
    bins: List[Dict[str, Any]]
    extra: Dict[str, Any]


def _compute_optional_binary_auc_metrics(p_pos: Tensor, y_pos: Tensor) -> Dict[str, float]:
    out: Dict[str, float] = {}
    if roc_auc_score is None or average_precision_score is None:
        return out
    p = p_pos.detach().cpu().float().numpy()
    y = y_pos.detach().cpu().long().numpy()
    # Guard: if only one class present, sklearn will throw
    if len(set(y.tolist())) < 2:
        return out
    out["auc_roc"] = float(roc_auc_score(y, p))
    out["auc_pr"] = float(average_precision_score(y, p))
    return out


@torch.no_grad()
def evaluate_calibration(
    calibrator: CalibratorBase,
    logits: Tensor,
    labels: Tensor,
    n_bins: int = 15,
) -> Tuple[Dict[str, float], List[Dict[str, Any]], Dict[str, Any]]:
    """
    Returns metrics + bins + extra.
    """
    labels = labels.long()
    logits_c = calibrator.transform_logits(logits)
    probs_c = softmax_probs(logits_c)

    metrics: Dict[str, float] = {}
    metrics["nll"] = nll_from_logits(logits_c, labels)
    metrics["brier"] = brier_score_multiclass(probs_c, labels)
    ece, mce, bins = ece_mce(probs_c, labels, n_bins=n_bins)
    metrics["ece"] = ece
    metrics["mce"] = mce

    # Accuracy
    pred = probs_c.argmax(dim=1)
    metrics["acc"] = float((pred == labels).float().mean().item())

    extra: Dict[str, Any] = {}

    # If binary, add binary-specific metrics and reliability bins on p_pos
    if probs_c.shape[1] == 2:
        p_pos = probs_c[:, 1]
        y_pos = labels
        metrics["brier_binary"] = brier_score_binary(p_pos, y_pos)
        extra["reliability_bins_binary"] = binary_reliability_bins(p_pos, y_pos, n_bins=n_bins)
        extra.update(_compute_optional_binary_auc_metrics(p_pos, y_pos))

        # A simple "over/under confidence" mean gap (emp - pred) for binary bins
        gaps = [b["gap"] for b in extra["reliability_bins_binary"] if b["gap"] is not None]
        if gaps:
            extra["mean_reliability_gap"] = float(sum(gaps) / len(gaps))

    return metrics, bins, extra


def _pick_best(
    reports: List[CalibReport],
    objective: CalibObjective,
) -> CalibReport:
    """
    Primary: minimize objective.
    Tie-break: minimize ECE, then minimize Brier.
    """
    def key(r: CalibReport):
        return (r.metrics[objective], r.metrics.get("ece", 1e9), r.metrics.get("brier", 1e9))
    return sorted(reports, key=key)[0]


def _train_val_split(
    logits: Tensor,
    labels: Tensor,
    val_fraction: float = 0.25,
    seed: int = 1337,
) -> Tuple[Tensor, Tensor, Tensor, Tensor]:
    """
    Simple random split.
    """
    n = logits.shape[0]
    if n < 10:
        raise ValueError("Need at least 10 samples to split for calibration.")
    g = torch.Generator(device="cpu")
    g.manual_seed(seed)
    perm = torch.randperm(n, generator=g)
    n_val = max(1, int(round(n * val_fraction)))
    val_idx = perm[:n_val]
    tr_idx = perm[n_val:]
    return logits[tr_idx], labels[tr_idx], logits[val_idx], labels[val_idx]


def auto_fit_calibrator(
    logits: Tensor,
    labels: Tensor,
    candidates: Optional[List[str]] = None,
    objective: CalibObjective = "nll",
    n_bins: int = 15,
    val_fraction: float = 0.25,
    seed: int = 1337,
    verbose: bool = True,
) -> Tuple[CalibratorBase, Dict[str, Any]]:
    """
    Fit multiple calibrators and pick the best one by `objective` on a held-out split.

    candidates:
      - "identity"
      - "temp"            (temperature scaling)
      - "vtemp"           (vector temperature scaling; multiclass only)
      - "platt"           (binary only, sklearn)
      - "isotonic"        (binary only, sklearn)
    """
    if candidates is None:
        candidates = ["identity", "temp", "platt", "isotonic", "vtemp"]

    logits = logits.detach()
    labels = labels.detach().long()
    if logits.ndim != 2:
        raise ValueError("logits must be (N, C)")

    C = logits.shape[1]
    is_binary = (C == 2)

    # Split
    tr_logits, tr_labels, va_logits, va_labels = _train_val_split(
        logits, labels, val_fraction=val_fraction, seed=seed
    )

    reports: List[CalibReport] = []
    fitted: Dict[str, CalibratorBase] = {}

    def add(name: str, calib: CalibratorBase):
        fitted[name] = calib
        m, bins, extra = evaluate_calibration(calib, va_logits, va_labels, n_bins=n_bins)
        reports.append(CalibReport(name=name, objective=objective, metrics=m, bins=bins, extra=extra))

    # Identity
    if "identity" in candidates:
        add("identity", IdentityCalibrator().fit(tr_logits, tr_labels))

    # Temperature Scaling (always valid)
    if "temp" in candidates:
        add("temp", TemperatureScaling().fit(tr_logits, tr_labels))

    # Vector temperature scaling (multiclass only; binary allowed but usually not needed)
    if "vtemp" in candidates and C >= 3:
        add("vtemp", VectorTemperatureScaling().fit(tr_logits, tr_labels))

    # Binary-only sklearn methods
    if is_binary:
        if "platt" in candidates:
            if LogisticRegression is not None and np is not None:
                add("platt", SklearnBinaryPlatt().fit(tr_logits, tr_labels))
            elif verbose:
                print("[auto_calibrate] Skipping platt: sklearn/numpy not available")
        if "isotonic" in candidates:
            if IsotonicRegression is not None and np is not None:
                add("isotonic", SklearnBinaryIsotonic().fit(tr_logits, tr_labels))
            elif verbose:
                print("[auto_calibrate] Skipping isotonic: sklearn/numpy not available")

    best = _pick_best(reports, objective=objective)
    best_cal = fitted[best.name]

    summary = {
        "objective": objective,
        "picked": best.name,
        "val_fraction": val_fraction,
        "seed": seed,
        "reports": [
            {
                "name": r.name,
                "metrics": r.metrics,
                "extra": r.extra,
            }
            for r in reports
        ],
    }

    if verbose:
        print("[auto_calibrate] Candidate results (on held-out calib split):")
        for r in reports:
            line = f"  - {r.name:9s} {objective}={r.metrics[objective]:.6f}  ece={r.metrics.get('ece', float('nan')):.6f}  brier={r.metrics.get('brier', float('nan')):.6f}"
            if "auc_roc" in r.metrics:
                line += f"  auc_roc={r.metrics['auc_roc']:.4f}"
            print(line)
        print(f"[auto_calibrate] Picked: {best.name}")

    # Refit best on ALL data (standard practice)
    best_cal.fit(logits, labels)
    summary["refit_on_full"] = True
    summary["best_state_dict"] = best_cal.state_dict()

    return best_cal, summary


# -----------------------------
# Plotting + Packet
# -----------------------------

def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def save_reliability_diagram(
    probs: Tensor,
    labels: Tensor,
    out_png: str,
    n_bins: int = 15,
    title: str = "Reliability Diagram",
) -> None:
    if plt is None:
        raise ImportError("matplotlib required to save reliability diagram")

    labels = labels.long()
    ece, mce, bins = ece_mce(probs, labels, n_bins=n_bins)

    # Build points: average confidence per bin vs accuracy per bin
    xs = []
    ys = []
    ns = []
    for b in bins:
        if b["n"] and b["avg_conf"] is not None:
            xs.append(b["avg_conf"])
            ys.append(b["avg_acc"])
            ns.append(b["n"])

    plt.figure(figsize=(6, 6))
    plt.plot([0, 1], [0, 1], linestyle="--")
    if xs:
        sizes = [max(20, min(300, n * 3)) for n in ns]
        plt.scatter(xs, ys, s=sizes)
    plt.xlim(0, 1)
    plt.ylim(0, 1)
    plt.xlabel("Confidence")
    plt.ylabel("Accuracy")
    plt.title(f"{title}\nECE={ece:.4f}  MCE={mce:.4f}")
    plt.tight_layout()
    plt.savefig(out_png, dpi=160)
    plt.close()


def make_calibration_packet(
    logits: Tensor,
    labels: Tensor,
    calibrator: CalibratorBase,
    n_bins: int = 15,
    extra_fields: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    JSON-friendly packet with raw + calibrated stats.

    Note: We avoid dumping all probs by default for huge datasets.
          If you want them, set extra_fields={"dump_probs": True}.
    """
    labels = labels.long()
    logits_raw = logits.detach()
    logits_cal = calibrator.transform_logits(logits_raw).detach()

    probs_raw = softmax_probs(logits_raw)
    probs_cal = softmax_probs(logits_cal)

    metrics_raw, bins_raw, extra_raw = evaluate_calibration(IdentityCalibrator(), logits_raw, labels, n_bins=n_bins)
    metrics_cal, bins_cal, extra_cal = evaluate_calibration(IdentityCalibrator(), logits_cal, labels, n_bins=n_bins)

    packet: Dict[str, Any] = {
        "n": int(labels.shape[0]),
        "c": int(logits.shape[1]),
        "calibrator": calibrator.state_dict(),
        "raw": {
            "metrics": metrics_raw,
            "bins": bins_raw,
            "extra": extra_raw,
        },
        "calibrated": {
            "metrics": metrics_cal,
            "bins": bins_cal,
            "extra": extra_cal,
        },
    }

    if extra_fields:
        packet.update(extra_fields)

    dump_probs = bool(packet.get("dump_probs", False))
    if dump_probs:
        # Store probs (potentially big)
        packet["probs_raw"] = probs_raw.detach().cpu().tolist()
        packet["probs_cal"] = probs_cal.detach().cpu().tolist()
        packet["labels"] = labels.detach().cpu().tolist()

    return packet


def save_json(obj: Dict[str, Any], path: str) -> None:
    _ensure_dir(os.path.dirname(path) or ".")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)


# -----------------------------
# High-level API
# -----------------------------

@dataclass
class AutoCalibrateResult:
    calibrator: CalibratorBase
    summary: Dict[str, Any]
    packet_path: Optional[str] = None
    diagram_path: Optional[str] = None


def auto_calibrate(
    logits: Tensor,
    labels: Tensor,
    out_dir: str,
    run_name: str = "calibration",
    candidates: Optional[List[str]] = None,
    objective: CalibObjective = "nll",
    n_bins: int = 15,
    val_fraction: float = 0.25,
    seed: int = 1337,
    save_probs: bool = False,
    make_plot: bool = True,
    verbose: bool = True,
) -> AutoCalibrateResult:
    """
    One-call calibration:
      - fits best calibrator (auto selection)
      - writes summary + calibration packet + plot
      - returns fitted calibrator (use it in inference)

    Inputs are Torch tensors:
      logits: (N, C) float
      labels: (N,) int
    """
    _ensure_dir(out_dir)

    cal, summary = auto_fit_calibrator(
        logits=logits,
        labels=labels,
        candidates=candidates,
        objective=objective,
        n_bins=n_bins,
        val_fraction=val_fraction,
        seed=seed,
        verbose=verbose,
    )

    packet = make_calibration_packet(
        logits=logits,
        labels=labels,
        calibrator=cal,
        n_bins=n_bins,
        extra_fields={"run_name": run_name, "dump_probs": save_probs},
    )

    packet_path = os.path.join(out_dir, f"{run_name}_packet.json")
    save_json(packet, packet_path)

    diagram_path = None
    if make_plot:
        # Plot using calibrated probs
        probs_cal = cal.transform_probs(logits)
        diagram_path = os.path.join(out_dir, f"{run_name}_reliability.png")
        save_reliability_diagram(
            probs=probs_cal,
            labels=labels,
            out_png=diagram_path,
            n_bins=n_bins,
            title=f"{run_name} ({summary['picked']})",
        )

    if verbose:
        raw_m = packet["raw"]["metrics"]
        cal_m = packet["calibrated"]["metrics"]
        print("[auto_calibrate] Raw metrics:", raw_m)
        print("[auto_calibrate] Calibrated metrics:", cal_m)
        print("[auto_calibrate] Wrote packet:", packet_path)
        if diagram_path:
            print("[auto_calibrate] Wrote diagram:", diagram_path)

    return AutoCalibrateResult(
        calibrator=cal,
        summary=summary,
        packet_path=packet_path,
        diagram_path=diagram_path,
    )


# -----------------------------
# Example usage
# -----------------------------

def _example():
    """
    Example with random logits. Replace with your actual tensors.
    """
    device = "cuda" if torch.cuda.is_available() else "cpu"

    N = 1000
    C = 2
    logits = torch.randn(N, C, device=device)
    labels = torch.randint(0, C, (N,), device=device)

    res = auto_calibrate(
        logits=logits,
        labels=labels,
        out_dir="./calib_out",
        run_name="sp_target",
        candidates=["identity", "temp", "platt", "isotonic"],
        objective="nll",
        n_bins=10,
        val_fraction=0.25,
        seed=1337,
        save_probs=False,
        make_plot=True,
        verbose=True,
    )

    # Apply during inference:
    new_logits = torch.randn(10, C, device=device)
    cal_probs = res.calibrator.transform_probs(new_logits)
    print("Calibrated probs:", cal_probs)


if __name__ == "__main__":
    _example()
