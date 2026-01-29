#  -*- coding: utf-8 -*-
#
#  Copyright Featrix, Inc 2023-2025
#
#  Proprietary and Confidential. Unauthorized use, copying or dissemination
#  of these materials is strictly prohibited.
#
"""
Default Training Rules - Declarative condition-based training adjustments.

This file contains the default rules for the training rules engine.
Edit this file to add/modify/remove rules.

Rules are evaluated at specific hook points:
- training_start: Before training begins (for architecture selection)
- epoch_end: After each training epoch
- validation_end: After validation

Condition syntax:
- String expressions: "num_rows > 1_000_000" or "auc > 0.8 and recall_at_1 < 0.5"
- Dict-based for trends: {"metric": "loss", "trend": "increasing", "window": 5}
- Compound: {"all": [...]} or {"any": [...]}

Action types:
- "set": Set a value directly (for training_start)
  {"set": "n_layers", "value": 4}
- "adjust": Multiply by a factor (for runtime adjustments)
  {"adjust": "temperature", "factor": 1.2}

Rule options:
- "cooldown": Epochs to wait before rule can fire again (default: 0)
- "max_fires": Max times rule can fire total, 0 = unlimited (default: 0)
- "enabled": Set to false to disable rule (default: true)

Conflict resolution:
- Multiple rules CAN fire in the same epoch
- If multiple rules adjust the same target, effects STACK (multiply)
- Use cooldowns to prevent runaway stacking
- Design rules with non-overlapping conditions when possible

Available metrics by hook point:

training_start:
- num_rows: Number of rows in dataset
- num_cols: Number of columns in dataset
- (architecture selection - metrics from dataset, not training)

epoch_end (after training epoch, before validation):
- train_loss: Training loss this epoch
- grad_norm: Gradient norm (unclipped)
- lr: Current learning rate
- dropout: Current dropout rate
- std_dim: Embedding std per dimension (collapse indicator)
- emb_norm: Embedding norm mean
- spread_weight, marginal_weight, joint_weight: Current loss weights
- epoch, total_epochs, epoch_pct: Progress info

validation_end (after validation):
- All epoch_end metrics PLUS:
- val_loss: Validation loss
- auc: AUC-ROC for ranking
- recall_at_1, recall_at_5: Recall@K metrics
- pos_sim, neg_sim: Positive/negative similarity means
- separation: pos_sim - neg_sim (higher = better)

Trend conditions (for epoch_end/validation_end):
- {"metric": "X", "trend": "increasing/decreasing/flat", "window": 5}

Available action targets:
- temperature: Loss temperature (higher = softer softmax)
- spread_weight: Spread loss weight (via WeightTimeline)
- lr: Learning rate (via LRTimeline) - NOT YET WIRED
- dropout: Dropout rate (via DropoutScheduler) - NOT YET WIRED
"""

from typing import Any, Dict, List


def get_default_rules() -> List[Dict[str, Any]]:
    """
    Get the default training rules.

    Returns:
        List of rule configurations
    """
    return [
        # =====================================================================
        # RUNTIME RULES - Adjust based on training dynamics
        # =====================================================================

        # AUC good but Recall@1 bad -> increase temperature (softer softmax)
        # Higher temp spreads probability mass, helping recall at cost of precision
        {
            "name": "Good AUC Bad Recall",
            "when": "validation_end",
            "condition": "auc > 0.7 and recall_at_1 < 0.3",
            "actions": [
                {"adjust": "temperature", "factor": 1.2, "action_name": "Increase Temperature"},
            ],
            "cooldown": 5,
        },

        # TODO: Add more rules as we wire up more action targets
        # - Embedding collapse -> increase spread weight (need to verify spread_weight target works)
        # - No learning -> boost LR (need to wire LRTimeline)
        # - Overfitting -> increase dropout (need to wire DropoutScheduler)
    ]


def get_architecture_rules() -> List[Dict[str, Any]]:
    """
    Get rules for architecture selection at training_start.

    These rules set n_layers, n_heads, d_model, dropout based on
    dataset characteristics (num_rows, num_cols).
    """
    return [r for r in get_default_rules() if r.get("when") == "training_start"]


def get_runtime_rules() -> List[Dict[str, Any]]:
    """
    Get rules for runtime adjustments during training.

    These rules adjust lr, temperature, weights based on
    training dynamics (loss trends, AUC, gradients).
    """
    return [r for r in get_default_rules() if r.get("when") != "training_start"]
