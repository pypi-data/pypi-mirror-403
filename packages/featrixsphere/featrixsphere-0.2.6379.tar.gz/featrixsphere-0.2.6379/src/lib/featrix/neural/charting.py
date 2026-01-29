#  -*- coding: utf-8 -*-
#
#  Copyright Featrix, Inc 2023-2025
#
#  Proprietary and Confidential.  Unauthorized use, copying or dissemination
#  of these materials is strictly prohibited.
#

"""
Charting utilities for training visualization.
"""

import logging
import os
import traceback
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


def plot_training_timeline(
    training_timeline: List[Dict],
    output_dir: str,
    n_epochs: int,
    optimizer_params: Optional[Dict] = None,
    training_info: Optional[Dict] = None,
    hostname: Optional[str] = None,
    software_version: Optional[str] = None,
    session_id: Optional[str] = None,
    job_id: Optional[str] = None,
    baseline_lr_schedule: Optional[List[float]] = None,
    baseline_weight_schedule: Optional[Dict[str, List[float]]] = None,
) -> None:
    """Plot comprehensive training timeline: loss, LR, events, and model health metrics as PNG.
    
    Creates a multi-panel plot showing:
    - Training and validation loss over epochs
    - Learning rate schedule
    - Model health metrics (WW alpha, embedding std, column loss std, gradient norms)
    - Timeline events (corrective actions, failures, interventions)
    
    Args:
        training_timeline: List of epoch entry dictionaries from training
        output_dir: Directory to save the plot
        n_epochs: Total number of epochs
        optimizer_params: Optional optimizer parameters for metadata
        training_info: Optional training info dict (for best checkpoint epoch)
        hostname: Optional hostname for metadata display
        software_version: Optional software version for metadata display
        session_id: Optional session ID for metadata display
        job_id: Optional job ID for metadata display
        baseline_lr_schedule: Optional list of baseline/planned LR values per epoch
        baseline_weight_schedule: Optional dict with 'spread', 'marginal', 'joint' keys,
            each containing a list of planned weight values per epoch
    """
    try:
        import matplotlib.pyplot as plt
        import numpy as np
        import matplotlib.cm as cm
    except ImportError:
        logger.warning("⚠️  matplotlib not available, skipping timeline plot")
        return
    
    if not training_timeline:
        logger.warning("⚠️  No timeline data available for plotting")
        return
    
    try:
        # Extract data from timeline
        epochs = []
        train_losses = []
        val_losses = []
        learning_rates = []
        dropout_rates = []
        failures = []  # List of (epoch, failure_type) tuples
        corrective_actions = []  # List of (epoch, action_type, trigger) tuples
        early_stop_blocked = []  # List of epochs where early stop was blocked
        
        # Health metrics arrays (aligned with epochs list)
        ww_alpha = []
        ww_entries_found = 0  # Count how many entries have weightwatcher data
        ww_alpha_values_found = 0  # Count how many have actual alpha values
        embedding_std = []
        d_model = None  # Will be extracted from collapse_diagnostics
        column_loss_std = []
        gradient_norms = []

        # Joint predictor debug metrics (SEPARATION, weight changes)
        joint_separation = []
        joint_weight_change = []
        joint_grad_norm = []

        # Rank statistics (per-epoch aggregated from batches)
        pred_rank1_mean = []
        pred_rank1_std = []
        identity_rank1_mean = []
        identity_diff_mean = []

        # Adaptive masking info
        mask_min_ratio = []
        mask_max_ratio = []
        mask_ramp_progress = []
        
        # Dynamic loss components (framework v2) - discovered from val_loss_components
        # Keys will be like 'full_contrastive', 'full_column_prediction', 'full_spread', 'short_spread', etc.
        dynamic_loss_components = {}  # Dict[component_name, List[float or None]]

        # Legacy loss components (for backward compatibility with old training runs)
        marginal_losses = []
        joint_losses = []
        spread_losses = []
        diversity_losses = []
        reconstruction_losses = []
        metric_losses = []
        separation_losses = []
        off_diag_sims = []
        short_uniformity_losses = []

        # Loss weights per epoch
        spread_weights = []
        marginal_weights = []
        joint_weights = []

        # Track all timeline events (warnings, errors, etc.)
        timeline_events = []  # List of (epoch, event_type, event_subtype, description) tuples
        
        for entry in training_timeline:
            if not isinstance(entry, dict):
                continue
            
            epoch = entry.get('epoch')
            if epoch is None:
                # Some timeline entries might not have epoch (shouldn't happen, but be safe)
                continue
            
            # Check if this is an event entry (warning, error, etc.) vs epoch entry
            # Event entries have 'event_type' field, epoch entries have 'train_loss' or 'learning_rate'
            event_type = entry.get('event_type')
            has_epoch_metrics = entry.get('train_loss') is not None or entry.get('learning_rate') is not None
            
            if event_type and not has_epoch_metrics:
                # This is a timeline event (warning_start, warning_resolved, error, etc.)
                event_subtype = entry.get('warning_type') or entry.get('error_type') or entry.get('action_type', 'UNKNOWN')
                description = entry.get('description', entry.get('warning_type', entry.get('error_type', 'Event')))
                timeline_events.append((epoch, event_type, event_subtype, description))
                # Continue to next entry - don't process as epoch entry
                continue
            
            # This is an epoch entry - extract metrics
            epochs.append(epoch)
            train_losses.append(entry.get('train_loss'))
            val_losses.append(entry.get('validation_loss'))
            learning_rates.append(entry.get('learning_rate'))
            dropout_rates.append(entry.get('dropout_rate'))
            
            # Extract UNWEIGHTED loss components from val_loss_components
            val_comp = entry.get('val_loss_components', {})
            if val_comp and isinstance(val_comp, dict):
                # Framework v2: dynamically discover all loss components (full_*, short_*)
                # Look for keys like 'full_contrastive', 'full_column_prediction', 'full_spread', 'short_spread', etc.
                for key, value in val_comp.items():
                    # Only collect numeric loss values (skip _batch_losses, _batch_sizes, modes, etc.)
                    if isinstance(value, (int, float)) and not key.startswith('_'):
                        # Skip totals and non-component keys
                        if key in ('total', 'full_total', 'short_total'):
                            continue
                        # Skip auxiliary metrics (pos_sim, neg_sim, accuracy, mean_cosine_sim, separation - these are diagnostic, not losses)
                        if any(key.endswith(suffix) for suffix in ('_pos_sim', '_neg_sim', '_accuracy', '_mean_cosine_sim', '_mode', '_separation')):
                            continue
                        if key not in dynamic_loss_components:
                            # Initialize with None for all previous epochs
                            dynamic_loss_components[key] = [None] * (len(epochs) - 1)
                        dynamic_loss_components[key].append(value)

                # Ensure all discovered components have an entry for this epoch
                for key in dynamic_loss_components:
                    if len(dynamic_loss_components[key]) < len(epochs):
                        dynamic_loss_components[key].append(None)

                # Legacy keys (for old training runs)
                marginal_losses.append(val_comp.get('marginal'))
                joint_losses.append(val_comp.get('joint'))
                spread_losses.append(val_comp.get('spread'))
                diversity_losses.append(val_comp.get('diversity'))
                reconstruction_losses.append(val_comp.get('reconstruction'))
                metric_losses.append(val_comp.get('metric'))
                separation_losses.append(val_comp.get('separation'))
                off_diag_sims.append(val_comp.get('off_diag_sim'))
                short_uniformity_losses.append(val_comp.get('short_uniformity'))
            else:
                # No val_loss_components - append None to all dynamic components
                for key in dynamic_loss_components:
                    dynamic_loss_components[key].append(None)
                marginal_losses.append(None)
                joint_losses.append(None)
                spread_losses.append(None)
                diversity_losses.append(None)
                reconstruction_losses.append(None)
                metric_losses.append(None)
                separation_losses.append(None)
                off_diag_sims.append(None)
                short_uniformity_losses.append(None)

            # Extract loss weights for this epoch
            loss_weights = entry.get('loss_weights', {})
            if loss_weights and isinstance(loss_weights, dict):
                spread_weights.append(loss_weights.get('spread_weight'))
                marginal_weights.append(loss_weights.get('marginal_weight'))
                joint_weights.append(loss_weights.get('joint_weight'))
            else:
                spread_weights.append(None)
                marginal_weights.append(None)
                joint_weights.append(None)

            # Extract health metrics for this epoch entry (aligned with epochs list)
            # WeightWatcher alpha
            ww_data = entry.get('weightwatcher')
            if ww_data and isinstance(ww_data, dict):
                ww_entries_found += 1
                alpha_val = ww_data.get('avg_alpha')
                if alpha_val is not None:
                    ww_alpha_values_found += 1
                ww_alpha.append(alpha_val)
            else:
                ww_alpha.append(None)
            
            # Embedding std (from collapse diagnostics if available)
            collapse_diag = entry.get('collapse_diagnostics', {})
            if collapse_diag and isinstance(collapse_diag, dict):
                je = collapse_diag.get('joint_embedding', {})
                if je and isinstance(je, dict):
                    embedding_std.append(je.get('std_per_dim_mean'))
                    # Extract d_model from std_per_dim_full if not already set
                    if d_model is None:
                        std_full = je.get('std_per_dim_full')
                        if std_full and isinstance(std_full, list):
                            d_model = len(std_full)
                else:
                    embedding_std.append(None)
            else:
                embedding_std.append(None)
            
            # Column loss std (computed from relationship extractor data if available)
            col_loss_std_val = entry.get('column_loss_std')
            column_loss_std.append(col_loss_std_val)
            
            # Gradient norm
            grad_data = entry.get('gradients', {})
            if grad_data and isinstance(grad_data, dict):
                gradient_norms.append(grad_data.get('unclipped_norm'))
            else:
                # Fallback to direct gradient_norm field
                gradient_norms.append(entry.get('gradient_norm'))

            # Joint predictor debug metrics (SEPARATION, weight changes, grad norm)
            # For framework v2, get separation from val_loss_components (full_contrastive_separation)
            jp_debug = entry.get('joint_predictor_debug', {})
            sep_value = None
            if jp_debug and isinstance(jp_debug, dict):
                sep_value = jp_debug.get('separation')
                joint_weight_change.append(jp_debug.get('weight_change_from_init'))
                joint_grad_norm.append(jp_debug.get('grad_norm'))

                # Rank statistics
                rank_stats = jp_debug.get('rank_stats', {})
                if rank_stats:
                    pred_rank1_mean.append(rank_stats.get('pred_rank1_mean'))
                    pred_rank1_std.append(rank_stats.get('pred_rank1_std'))
                    identity_rank1_mean.append(rank_stats.get('identity_rank1_mean'))
                    identity_diff_mean.append(rank_stats.get('identity_diff_mean'))
                else:
                    pred_rank1_mean.append(None)
                    pred_rank1_std.append(None)
                    identity_rank1_mean.append(None)
                    identity_diff_mean.append(None)
            else:
                joint_weight_change.append(None)
                joint_grad_norm.append(None)
                pred_rank1_mean.append(None)
                pred_rank1_std.append(None)
                identity_rank1_mean.append(None)
                identity_diff_mean.append(None)

            # Framework v2: get separation from val_loss_components if not from joint_predictor_debug
            if sep_value is None and val_comp:
                # Try full_contrastive_separation first (explicit), then compute from pos_sim/neg_sim
                sep_value = val_comp.get('full_contrastive_separation')
                if sep_value is None:
                    pos_sim = val_comp.get('full_contrastive_pos_sim')
                    neg_sim = val_comp.get('full_contrastive_neg_sim')
                    if pos_sim is not None and neg_sim is not None:
                        sep_value = pos_sim - neg_sim
            joint_separation.append(sep_value)

            # Adaptive masking info
            masking_info = entry.get('adaptive_masking', {})
            if masking_info:
                mask_min_ratio.append(masking_info.get('min_mask_ratio'))
                mask_max_ratio.append(masking_info.get('max_mask_ratio'))
                mask_ramp_progress.append(masking_info.get('ramp_progress'))
            else:
                mask_min_ratio.append(None)
                mask_max_ratio.append(None)
                mask_ramp_progress.append(None)

            # Track failures
            failures_detected = entry.get('failures_detected', [])
            if failures_detected:
                for failure in failures_detected:
                    failures.append((epoch, failure))
            
            # Track corrective actions
            actions = entry.get('corrective_actions', [])
            for action in actions:
                if isinstance(action, dict):
                    action_type = action.get('action_type', 'UNKNOWN')
                    trigger = action.get('trigger', 'UNKNOWN')
                    corrective_actions.append((epoch, action_type, trigger))
            
            # Track early stop blocking
            if entry.get('early_stop_blocked', False):
                early_stop_blocked.append(epoch)
        
        if not epochs:
            logger.warning("⚠️  No valid epoch data in timeline for plotting")
            return
        
        # Extract data rotation epochs for vertical lines
        rotation_epochs = []
        for entry in training_timeline:
            if entry.get('event_type') == 'train_val_gradual_rotation':
                rotation_epochs.append(entry.get('epoch'))
        
        # Create figure with subplots (now 12 panels: total loss, marginal loss, other component losses, loss weights, LR, 4 health metrics, joint predictor, rank/masking, events)
        # All share the same x-axis (epochs) and are stacked tightly
        fig = plt.figure(figsize=(16, 28))
        gs = fig.add_gridspec(12, 1, hspace=0.05, height_ratios=[1, 0.8, 1, 0.8, 1, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8])

        ax1 = fig.add_subplot(gs[0])  # Total loss curves (train + val)
        ax_marginal = fig.add_subplot(gs[1], sharex=ax1)  # Marginal loss (own panel)
        ax2 = fig.add_subplot(gs[2], sharex=ax1)  # Unweighted loss components (joint, spread, etc. - no marginal)
        ax_weights = fig.add_subplot(gs[3], sharex=ax1)  # Loss weights per epoch
        ax3 = fig.add_subplot(gs[4], sharex=ax1)  # Learning rate
        ax4 = fig.add_subplot(gs[5], sharex=ax1)  # WW Alpha
        ax5 = fig.add_subplot(gs[6], sharex=ax1)  # Embedding std
        ax6 = fig.add_subplot(gs[7], sharex=ax1)  # Column loss std
        ax7 = fig.add_subplot(gs[8], sharex=ax1)  # Gradient norm
        ax_joint = fig.add_subplot(gs[9], sharex=ax1)  # Joint predictor SEPARATION
        ax_rank = fig.add_subplot(gs[10], sharex=ax1)  # Rank1 and masking
        ax8 = fig.add_subplot(gs[11], sharex=ax1)  # Events timeline

        # Hide x-axis labels on all but the bottom panel
        for ax in [ax1, ax_marginal, ax2, ax_weights, ax3, ax4, ax5, ax6, ax7, ax_joint, ax_rank]:
            plt.setp(ax.get_xticklabels(), visible=False)

        # Align all y-axis labels at a fixed position
        all_axes = [ax1, ax_marginal, ax2, ax_weights, ax3, ax4, ax5, ax6, ax7, ax_joint, ax_rank, ax8]
        for ax in all_axes:
            ax.yaxis.set_label_coords(-0.06, 0.5)

        # ========== SUBPLOT 1: Loss Curves ==========
        epochs_array = np.array(epochs)
        
        # Plot training loss
        train_mask = np.array([x is not None for x in train_losses])
        if train_mask.any():
            ax1.plot(epochs_array[train_mask], np.array(train_losses)[train_mask], 
                    '-', linewidth=2, color='#dc2626', label='Train Loss', 
                    marker='o', markersize=3, alpha=0.8)
        
        # Plot validation loss
        val_mask = np.array([x is not None for x in val_losses])
        if val_mask.any():
            ax1.plot(epochs_array[val_mask], np.array(val_losses)[val_mask], 
                    '--', linewidth=2, color='#f97316', label='Val Loss', 
                    marker='s', markersize=3, alpha=0.8)
            
            # Mark best epoch (lowest val loss)
            valid_val_losses = [(e, v) for e, v in zip(epochs_array[val_mask], np.array(val_losses)[val_mask]) if v is not None and not np.isnan(v)]
            if valid_val_losses:
                best_epoch, best_loss = min(valid_val_losses, key=lambda x: x[1])
                ax1.scatter([best_epoch], [best_loss], s=200, c='gold', marker='*',
                          zorder=10, edgecolors='black', linewidths=2, label='Best Epoch')
        
        ax1.set_ylabel('Loss', fontsize=12, fontweight='bold')

        # Build title: Training Timeline (ES <session_id>, date, host, version)
        from datetime import datetime
        date_str = datetime.now().strftime('%Y-%m-%d %H:%M')

        metadata_parts = []
        if session_id:
            metadata_parts.append(f"ES {session_id}")
        metadata_parts.append(date_str)
        if hostname:
            metadata_parts.append(hostname)
        if software_version:
            metadata_parts.append(f"v{software_version}")

        title = f"Training Timeline ({', '.join(metadata_parts)})"
        ax1.set_title(title, fontsize=14, fontweight='bold', pad=15)
        ax1.legend(loc='center left', bbox_to_anchor=(1.01, 0.5), fontsize=8)
        ax1.grid(True, alpha=0.3)
        # Set x-axis to full planned epoch range (all subplots share this axis)
        ax1.set_xlim(-1, n_epochs)
        
        # ========== SUBPLOT: MARGINAL LOSS (own panel) ==========
        # For log scale, filter out None, NaN, and values <= 0
        # Check for framework v2 key first (full_column_prediction), fall back to legacy (marginal)
        marginal_data = dynamic_loss_components.get('full_column_prediction', marginal_losses)
        marginal_mask = np.array([x is not None and not np.isnan(x) and x > 0 for x in marginal_data])

        if marginal_mask.any():
            label = 'Column Prediction' if 'full_column_prediction' in dynamic_loss_components else 'Marginal'
            ax_marginal.plot(epochs_array[marginal_mask], np.array(marginal_data)[marginal_mask],
                    '-', linewidth=2, color='#ef4444', label=f'{label} (unweighted)',
                    marker='o', markersize=3, alpha=0.8)
            ax_marginal.set_ylabel('Marginal Loss', fontsize=11, fontweight='bold')
            ax_marginal.set_yscale('log')
            ax_marginal.legend(loc='center left', bbox_to_anchor=(1.01, 0.5), fontsize=8)
            ax_marginal.grid(True, alpha=0.3)
        else:
            ax_marginal.text(0.5, 0.5, 'No marginal loss data', ha='center', va='center',
                    transform=ax_marginal.transAxes, fontsize=10, color='gray')
            ax_marginal.set_ylabel('Marginal Loss', fontsize=11, fontweight='bold')
        ax_marginal.set_xlim(left=-1)

        # ========== SUBPLOT: LOSS COMPONENTS (dynamically discovered) ==========
        # Color palette for dynamic components
        component_colors = [
            '#3b82f6',  # blue
            '#10b981',  # green
            '#8b5cf6',  # purple
            '#f97316',  # orange
            '#06b6d4',  # cyan
            '#ef4444',  # red
            '#ec4899',  # pink
            '#eab308',  # yellow
            '#14b8a6',  # teal
            '#a855f7',  # violet
        ]
        component_markers = ['s', '^', 'D', 'x', 'o', 'v', '*', 'p', 'h', '+']

        # Human-readable labels for framework v2 component names
        component_labels = {
            'full_contrastive': 'Contrastive (128D)',
            'full_column_prediction': 'Column Pred (128D)',
            'full_spread': 'Spread (128D)',
            'full_separation': 'Separation (128D)',
            'full_uniformity': 'Uniformity (128D)',
            'full_diversity': 'Diversity (128D)',
            'full_reconstruction': 'Reconstruction (128D)',
            'short_contrastive': 'Contrastive (3D)',
            'short_spread': 'Spread (3D)',
            'short_separation': 'Separation (3D)',
            'short_uniformity': 'Uniformity (3D)',
            # Legacy names
            'joint': 'Joint',
            'spread': 'Spread',
            'marginal': 'Marginal',
            'diversity': 'Diversity',
            'reconstruction': 'Reconstruction',
            'metric': 'Metric',
            'separation': 'Separation',
        }

        any_plotted = False
        color_idx = 0

        # Plot dynamic components (framework v2)
        # Skip full_column_prediction since it's in its own panel
        for comp_name, comp_values in sorted(dynamic_loss_components.items()):
            if comp_name == 'full_column_prediction':
                continue  # Already plotted in marginal panel

            mask = np.array([x is not None and not np.isnan(x) and x > 0 for x in comp_values])
            if mask.any():
                color = component_colors[color_idx % len(component_colors)]
                marker = component_markers[color_idx % len(component_markers)]
                label = component_labels.get(comp_name, comp_name.replace('_', ' ').title())
                ax2.plot(epochs_array[mask], np.array(comp_values)[mask],
                        '-', linewidth=2, color=color, label=label,
                        marker=marker, markersize=3, alpha=0.8)
                any_plotted = True
                color_idx += 1

        # Fall back to legacy components if no dynamic components found
        if not any_plotted:
            legacy_components = [
                (joint_losses, 'Joint', '#3b82f6', 's'),
                (spread_losses, 'Spread', '#10b981', '^'),
                (diversity_losses, 'Diversity', '#8b5cf6', 'D'),
                (reconstruction_losses, 'Reconstruction', '#f97316', 'x'),
                (metric_losses, 'Metric', '#06b6d4', 'o'),
                (separation_losses, 'Separation', '#ef4444', 'v'),
                (short_uniformity_losses, 'Short Uniformity', '#ec4899', '*'),
            ]
            for values, label, color, marker in legacy_components:
                mask = np.array([x is not None and not np.isnan(x) and x > 0 for x in values])
                if mask.any():
                    ax2.plot(epochs_array[mask], np.array(values)[mask],
                            '-', linewidth=2, color=color, label=label,
                            marker=marker, markersize=3, alpha=0.8)
                    any_plotted = True

        if any_plotted:
            ax2.set_ylabel('Loss', fontsize=11, fontweight='bold')
            ax2.set_yscale('log')
            ax2.legend(loc='center left', bbox_to_anchor=(1.01, 0.5), fontsize=8)
            ax2.grid(True, alpha=0.3)
        else:
            ax2.text(0.5, 0.5, 'No unweighted loss component data', ha='center', va='center',
                    transform=ax2.transAxes, fontsize=10, color='gray')
            ax2.set_ylabel('Loss', fontsize=11, fontweight='bold')
        ax2.set_xlim(left=-1)

        # ========== SUBPLOT: LOSS WEIGHTS ==========
        # Always show full epoch range for weight schedule (like LR panel)
        ax_weights.set_xlim(-1, n_epochs)

        # Plot baseline/planned weight schedule as dashed lines FIRST (if provided)
        # This shows the full planned schedule even before training completes
        if baseline_weight_schedule is not None:
            baseline_epochs = np.arange(len(baseline_weight_schedule.get('spread', [])))
            if len(baseline_epochs) > 0:
                if 'spread' in baseline_weight_schedule:
                    ax_weights.plot(baseline_epochs, baseline_weight_schedule['spread'],
                            '--', linewidth=1.5, color='#10b981', label='Spread (planned)',
                            alpha=0.5, zorder=5)
                if 'marginal' in baseline_weight_schedule:
                    ax_weights.plot(baseline_epochs, baseline_weight_schedule['marginal'],
                            '--', linewidth=1.5, color='#ef4444', label='Marginal (planned)',
                            alpha=0.5, zorder=5)
                if 'joint' in baseline_weight_schedule:
                    ax_weights.plot(baseline_epochs, baseline_weight_schedule['joint'],
                            '--', linewidth=1.5, color='#3b82f6', label='Joint (planned)',
                            alpha=0.5, zorder=5)

        # Plot actual weights on top
        spread_w_mask = np.array([x is not None for x in spread_weights])
        marginal_w_mask = np.array([x is not None for x in marginal_weights])
        joint_w_mask = np.array([x is not None for x in joint_weights])

        if spread_w_mask.any():
            ax_weights.plot(epochs_array[spread_w_mask], np.array(spread_weights)[spread_w_mask],
                    '-', linewidth=2, color='#10b981', label='Spread Weight',
                    marker='^', markersize=3, alpha=0.8, zorder=10)
        if marginal_w_mask.any():
            ax_weights.plot(epochs_array[marginal_w_mask], np.array(marginal_weights)[marginal_w_mask],
                    '-', linewidth=2, color='#ef4444', label='Marginal Weight',
                    marker='o', markersize=3, alpha=0.8, zorder=10)
        if joint_w_mask.any():
            ax_weights.plot(epochs_array[joint_w_mask], np.array(joint_weights)[joint_w_mask],
                    '-', linewidth=2, color='#3b82f6', label='Joint Weight',
                    marker='s', markersize=3, alpha=0.8, zorder=10)

        # Add vertical "current epoch" line
        if epochs:
            current_epoch = max(epochs)
            ax_weights.axvline(x=current_epoch, color='cyan', linestyle='--', linewidth=1.5, alpha=0.7, zorder=15)

        if spread_w_mask.any() or marginal_w_mask.any() or joint_w_mask.any() or baseline_weight_schedule is not None:
            ax_weights.set_ylabel('Weight', fontsize=11, fontweight='bold')
            ax_weights.legend(loc='center left', bbox_to_anchor=(1.01, 0.5), fontsize=7, ncol=1)
            ax_weights.grid(True, alpha=0.3)
        else:
            ax_weights.text(0.5, 0.5, 'No loss weight data', ha='center', va='center',
                    transform=ax_weights.transAxes, fontsize=10, color='gray')
            ax_weights.set_ylabel('Weight', fontsize=11, fontweight='bold')

        # ========== SUBPLOT 3: Learning Rate ==========
        # Calculate phase boundaries based on LRTimeline schedule
        # Phase 1 (0-15%): Warmup (cubic ramp)
        # Phase 2 (15-20%): Stabilization (flat at max)
        # Phase 3a (20-45%): Productive (decay + oscillation)
        # Phase 3b (45-70%): Cosine descent
        # Phase 4 (70-100%): Cooldown (linear)
        phase1_end = int(0.15 * n_epochs)
        phase2_end = int(0.20 * n_epochs)
        phase3a_end = int(0.45 * n_epochs)
        phase3b_end = int(0.70 * n_epochs)

        # Always show full epoch range for LR schedule
        ax3.set_xlim(-1, n_epochs)

        # Shade regions with different colors (show full plan)
        ax3.axvspan(-1, phase1_end, alpha=0.1, color='blue')
        ax3.axvspan(phase1_end, phase2_end, alpha=0.1, color='green')
        ax3.axvspan(phase2_end, phase3a_end, alpha=0.1, color='yellow')
        ax3.axvspan(phase3a_end, phase3b_end, alpha=0.1, color='orange')
        ax3.axvspan(phase3b_end, n_epochs, alpha=0.1, color='red')

        # Plot baseline/planned LR schedule as dashed gray line FIRST (if provided)
        # This shows the full planned schedule even before training completes
        if baseline_lr_schedule is not None and len(baseline_lr_schedule) > 0:
            baseline_epochs = np.arange(len(baseline_lr_schedule))
            ax3.plot(baseline_epochs, baseline_lr_schedule,
                    '--', linewidth=1.5, color='#94a3b8', label='Planned LR',
                    alpha=0.7, zorder=5)

        # Plot actual LR on top
        lr_mask = np.array([x is not None and x > 0 for x in learning_rates])
        if lr_mask.any():
            ax3.plot(epochs_array[lr_mask], np.array(learning_rates)[lr_mask],
                    '-', linewidth=2.5, color='#2563eb', label='Actual LR',
                    marker='o', markersize=3, alpha=0.8, zorder=10)

        # Mark LR adjustments from corrective actions
        lr_actions = [(e, t) for e, a, t in corrective_actions if 'LR' in a.upper()]
        for epoch, trigger in lr_actions:
            if epoch < len(epochs_array) and lr_mask[epochs_array == epoch].any():
                idx = np.where(epochs_array == epoch)[0][0]
                if idx < len(learning_rates) and learning_rates[idx] is not None:
                    ax3.scatter([epoch], [learning_rates[idx]], s=120, c='#dc2626',
                               marker='^', zorder=10, edgecolors='black', linewidths=1.5)

        # Add vertical "current epoch" line
        if epochs:
            current_epoch = max(epochs)
            ax3.axvline(x=current_epoch, color='cyan', linestyle='--', linewidth=1.5, alpha=0.7, zorder=15)

        # Add phase labels at top of plot
        # Get y-axis max for label positioning (use baseline schedule if available)
        if baseline_lr_schedule and len(baseline_lr_schedule) > 0:
            y_max = max(baseline_lr_schedule) * 1.5
        elif lr_mask.any():
            y_max = max(np.array(learning_rates)[lr_mask]) * 1.5
        else:
            y_max = 1e-3

        # Phase labels
        ax3.text((0 + phase1_end) / 2, y_max * 0.8, 'Warmup\n(cubic)', ha='center', fontsize=8, color='blue', fontweight='bold')
        ax3.text((phase1_end + phase2_end) / 2, y_max * 0.9, 'Stab', ha='center', fontsize=8, color='green', fontweight='bold')
        ax3.text((phase2_end + phase3a_end) / 2, y_max * 0.75, 'Productive\n(decay+wiggle)', ha='center', fontsize=8, color='#9a6700', fontweight='bold')
        ax3.text((phase3a_end + phase3b_end) / 2, y_max * 0.5, 'Cosine\nDescent', ha='center', fontsize=8, color='darkorange', fontweight='bold')
        ax3.text((phase3b_end + n_epochs) / 2, y_max * 0.15, 'Cooldown', ha='center', fontsize=8, color='darkred', fontweight='bold')

        ax3.set_ylabel('Learning Rate', fontsize=11, fontweight='bold')
        ax3.legend(loc='center left', bbox_to_anchor=(1.01, 0.5), fontsize=8)
        ax3.grid(True, alpha=0.3)
        ax3.set_yscale('log')

        # ========== SUBPLOT 4: WeightWatcher Alpha ==========
        # Thresholds: alpha 2-5 = healthy (green), alpha >= 8 = noise (red)
        ww_healthy_min, ww_healthy_max = 2.0, 5.0
        ww_noise_threshold = 8.0

        ww_mask = np.array([x is not None and not np.isnan(x) for x in ww_alpha])
        if ww_mask.any():
            ww_vals = np.array(ww_alpha)[ww_mask]
            y_max = max(ww_vals.max() * 1.1, ww_noise_threshold + 1)

            # Shaded regions for healthy (green) and noise (red)
            ax4.axhspan(ww_healthy_min, ww_healthy_max, alpha=0.15, color='#22c55e', zorder=1)
            if y_max >= ww_noise_threshold:
                ax4.axhspan(ww_noise_threshold, y_max, alpha=0.15, color='#ef4444', zorder=1)
            else:
                # Just draw a line if noise threshold is above y_max
                ax4.axhline(y=ww_noise_threshold, color='#ef4444', linestyle='--',
                           linewidth=1.5, alpha=0.7)

            # Labels on right side
            ax4.text(1.01, (ww_healthy_min + ww_healthy_max) / 2, 'Healthy',
                    transform=ax4.get_yaxis_transform(), fontsize=8, color='#22c55e',
                    va='center', fontweight='bold')
            ax4.text(1.01, ww_noise_threshold, 'Noise',
                    transform=ax4.get_yaxis_transform(), fontsize=8, color='#ef4444',
                    va='center', fontweight='bold')

            # Plot alpha values
            ax4.plot(epochs_array[ww_mask], ww_vals,
                    '-', linewidth=2, color='#10b981',
                    marker='o', markersize=3, alpha=0.8, zorder=10)
            ax4.set_ylabel('WW Alpha', fontsize=11, fontweight='bold')
            ax4.set_ylim(0, y_max)
            ax4.grid(True, alpha=0.3)
        else:
            # Explain why there's no data
            if ww_entries_found == 0:
                no_data_msg = 'No WW Alpha data (WeightWatcher disabled or not run)'
            elif ww_alpha_values_found == 0:
                no_data_msg = f'No WW Alpha data ({ww_entries_found} WW runs, but no alpha values returned)'
            else:
                no_data_msg = 'No WW Alpha data (all values NaN)'
            ax4.text(0.5, 0.5, no_data_msg, ha='center', va='center',
                    transform=ax4.transAxes, fontsize=10, color='gray')
            ax4.set_ylabel('WW Alpha', fontsize=11, fontweight='bold')
        ax4.set_xlim(left=-1)

        # ========== SUBPLOT 5: Embedding Std/Dim ==========
        emb_std_mask = np.array([x is not None and not np.isnan(x) for x in embedding_std])
        # Thresholds for embedding std/dim quality:
        #   0.02 = collapsed (representations have collapsed)
        #   0.04 = target (healthy learned representations)
        #   0.06 = random (random baseline for L2-normalized d=256)
        collapsed_threshold = 0.02
        target_threshold = 0.04
        random_threshold = 0.06

        if emb_std_mask.any():
            ax5.plot(epochs_array[emb_std_mask], np.array(embedding_std)[emb_std_mask],
                     '-', linewidth=2, color='#8b5cf6', label='Embedding Std/Dim',
                     marker='s', markersize=3, alpha=0.8)

        # Always show the threshold lines (even without data)
        ax5.axhline(y=collapsed_threshold, color='#ef4444', linestyle='--',
                   linewidth=1.5, alpha=0.7)
        ax5.axhline(y=target_threshold, color='#22c55e', linestyle='--',
                   linewidth=1.5, alpha=0.7)
        ax5.axhline(y=random_threshold, color='#6b7280', linestyle='--',
                   linewidth=1.5, alpha=0.7)

        # Add labels on right side of plot
        ax5.text(1.01, collapsed_threshold, 'Collapsed', transform=ax5.get_yaxis_transform(),
                fontsize=8, color='#ef4444', va='center', fontweight='bold')
        ax5.text(1.01, target_threshold, 'Target', transform=ax5.get_yaxis_transform(),
                fontsize=8, color='#22c55e', va='center', fontweight='bold')
        ax5.text(1.01, random_threshold, 'Random', transform=ax5.get_yaxis_transform(),
                fontsize=8, color='#6b7280', va='center', fontweight='bold')

        ax5.set_ylabel('Embedding Std/Dim', fontsize=11, fontweight='bold')
        if emb_std_mask.any():
            ax5.legend(loc='center left', bbox_to_anchor=(1.01, 0.5), fontsize=8)
        ax5.grid(True, alpha=0.3)

        if not emb_std_mask.any():
            ax5.text(0.5, 0.5, 'No embedding std data', ha='center', va='center',
                    transform=ax5.transAxes, fontsize=10, color='gray')

        ax5.set_xlim(left=-1)
        # Fixed Y-axis range: 0.02 to 0.06 (with small padding)
        ax5.set_ylim(0.015, 0.065)

        # ========== SUBPLOT 6: Column Loss Std ==========
        col_std_mask = np.array([x is not None and not np.isnan(x) for x in column_loss_std])
        if col_std_mask.any():
            ax6.plot(epochs_array[col_std_mask], np.array(column_loss_std)[col_std_mask],
                     '-', linewidth=2, color='#f59e0b', label='Column Loss Std',
                     marker='^', markersize=3, alpha=0.8)
            ax6.set_ylabel('Column Loss Std', fontsize=11, fontweight='bold')
            ax6.legend(loc='center left', bbox_to_anchor=(1.01, 0.5), fontsize=8)
            ax6.grid(True, alpha=0.3)
        else:
            ax6.text(0.5, 0.5, 'No column loss std data', ha='center', va='center',
                    transform=ax6.transAxes, fontsize=10, color='gray')
            ax6.set_ylabel('Column Loss Std', fontsize=11, fontweight='bold')
        ax6.set_xlim(left=-1)

        # ========== SUBPLOT 7: Gradient Norm ==========
        grad_mask = np.array([x is not None and x > 0 for x in gradient_norms])
        if grad_mask.any():
            ax7.plot(epochs_array[grad_mask], np.array(gradient_norms)[grad_mask],
                     '-', linewidth=2, color='#6366f1', label='Gradient Norm',
                     marker='x', markersize=3, alpha=0.8)
            ax7.set_ylabel('Gradient Norm', fontsize=11, fontweight='bold')
            ax7.set_yscale('log')
            ax7.legend(loc='center left', bbox_to_anchor=(1.01, 0.5), fontsize=8)
            ax7.grid(True, alpha=0.3)
        else:
            ax7.text(0.5, 0.5, 'No gradient norm data', ha='center', va='center',
                    transform=ax7.transAxes, fontsize=10, color='gray')
            ax7.set_ylabel('Gradient Norm', fontsize=11, fontweight='bold')
        ax7.set_xlim(left=-1)

        # ========== SUBPLOT: Joint Predictor SEPARATION ==========
        # SEPARATION = diag(sim) - off_diag(sim), should increase if learning
        # Values near 0 mean the model can't distinguish correct from incorrect pairs
        sep_mask = np.array([x is not None for x in joint_separation])
        if sep_mask.any():
            ax_joint.axhline(y=0, color='gray', linestyle='--', linewidth=1, alpha=0.5)  # Zero baseline
            ax_joint.plot(epochs_array[sep_mask], np.array(joint_separation)[sep_mask],
                         '-', linewidth=2, color='#8b5cf6', label='SEPARATION',
                         marker='o', markersize=4, alpha=0.8)
            # Add warning threshold lines
            ax_joint.axhline(y=0.01, color='orange', linestyle=':', linewidth=1, alpha=0.5, label='Min expected')
            ax_joint.axhline(y=-0.01, color='red', linestyle=':', linewidth=1, alpha=0.5)
            ax_joint.set_ylabel('SEPARATION', fontsize=11, fontweight='bold')
            ax_joint.legend(loc='center left', bbox_to_anchor=(1.01, 0.5), fontsize=9)
            ax_joint.grid(True, alpha=0.3)
            # Color the background based on health
            ax_joint.axhspan(-1, 0, alpha=0.1, color='red', label=None)  # Bad: negative separation
            ax_joint.axhspan(0, 0.01, alpha=0.1, color='yellow', label=None)  # Warning: too low
        else:
            ax_joint.text(0.5, 0.5, 'No contrastive SEPARATION data', ha='center', va='center',
                         transform=ax_joint.transAxes, fontsize=10, color='gray')
            ax_joint.set_ylabel('SEPARATION', fontsize=11, fontweight='bold')
        ax_joint.set_xlim(left=-1)
        ax_joint.set_ylim(-0.1, 1.0)  # Fixed y-axis: separation ranges 0-1

        # ========== SUBPLOT: Rank1 & Masking ==========
        # Plot pred_rank1 (with std as error bars) and masking ratio
        # Single Y-axis: both rank1 and mask ratio are percentages (0-100%)
        rank1_mask = np.array([x is not None for x in pred_rank1_mean])
        has_rank_data = rank1_mask.any()

        if has_rank_data:
            rank1_vals = np.array([x if x is not None else np.nan for x in pred_rank1_mean])
            rank1_std_vals = np.array([x if x is not None else 0 for x in pred_rank1_std])

            # Plot pred_rank1 as percentage with error band
            ax_rank.fill_between(
                epochs_array[rank1_mask],
                (rank1_vals[rank1_mask] - rank1_std_vals[rank1_mask]) * 100,
                (rank1_vals[rank1_mask] + rank1_std_vals[rank1_mask]) * 100,
                alpha=0.2, color='#22c55e'
            )
            ax_rank.plot(epochs_array[rank1_mask], rank1_vals[rank1_mask] * 100,
                        '-', linewidth=2, color='#22c55e', label='Pred Rank1 %',
                        marker='o', markersize=3, alpha=0.9)

            # Plot identity_rank1 for comparison
            id_rank1_mask = np.array([x is not None for x in identity_rank1_mean])
            if id_rank1_mask.any():
                id_rank1_vals = np.array([x if x is not None else np.nan for x in identity_rank1_mean])
                ax_rank.plot(epochs_array[id_rank1_mask], id_rank1_vals[id_rank1_mask] * 100,
                            '--', linewidth=1.5, color='#3b82f6', label='Identity Rank1 %',
                            marker='s', markersize=2, alpha=0.7)

            # Plot masking ratio on same axis (also a percentage)
            mask_min_mask = np.array([x is not None for x in mask_min_ratio])
            mask_max_mask = np.array([x is not None for x in mask_max_ratio])

            if mask_min_mask.any() and mask_max_mask.any():
                min_vals = np.array([x if x is not None else np.nan for x in mask_min_ratio])
                max_vals = np.array([x if x is not None else np.nan for x in mask_max_ratio])

                # Plot masking range as shaded area
                ax_rank.fill_between(
                    epochs_array[mask_min_mask],
                    min_vals[mask_min_mask] * 100,
                    max_vals[mask_min_mask] * 100,
                    alpha=0.2, color='#f97316', label='Mask Range'
                )
                # Plot midpoint line
                mid_vals = (min_vals + max_vals) / 2
                ax_rank.plot(epochs_array[mask_min_mask], mid_vals[mask_min_mask] * 100,
                             '-', linewidth=1.5, color='#f97316', label='Mask %',
                             marker='^', markersize=2, alpha=0.8)

            ax_rank.axhline(y=100, color='gray', linestyle=':', linewidth=1, alpha=0.5)
            ax_rank.axhline(y=1, color='red', linestyle=':', linewidth=1, alpha=0.5, label='Random (1%)')
            ax_rank.set_ylabel('Percentage', fontsize=11, fontweight='bold')
            ax_rank.set_ylim(-5, 110)
            ax_rank.legend(loc='center left', bbox_to_anchor=(1.01, 0.5), fontsize=8)
            ax_rank.grid(True, alpha=0.3)
        else:
            ax_rank.text(0.5, 0.5, 'No rank1 or masking data', ha='center', va='center',
                        transform=ax_rank.transAxes, fontsize=10, color='gray')
            ax_rank.set_ylabel('Percentage', fontsize=11, fontweight='bold')
        ax_rank.set_xlim(left=-1)

        # ========== SUBPLOT 8: Events Timeline ==========
        # Each unique event type gets its own Y row
        # Consecutive failures become shaded duration boxes
        all_events = []

        # Add failures
        for epoch, failure_type in failures:
            all_events.append((epoch, 'failure', failure_type, f'Failure: {failure_type}'))

        # Add corrective actions
        for epoch, action_type, trigger in corrective_actions:
            all_events.append((epoch, 'corrective_action', action_type, f'Action: {action_type}'))

        # Add early stop blocking
        for epoch in early_stop_blocked:
            all_events.append((epoch, 'early_stop_blocked', 'EARLY_STOP_BLOCKED', 'Early Stop Blocked'))

        # Add timeline events (warnings, errors, etc.)
        for epoch, event_type, event_subtype, description in timeline_events:
            all_events.append((epoch, event_type, event_subtype, description))

        if all_events:
            # Color mapping for event subtypes
            EVENT_COLORS = {
                # Failures (red spectrum)
                'NO_LEARNING': '#ef4444',
                'UNSTABLE_TRAINING': '#dc2626',
                'DIVERGENCE': '#b91c1c',
                'OVERFITTING': '#f87171',
                # Warnings (yellow/orange)
                'SLOW_LEARNING': '#f59e0b',
                'HIGH_ALPHA': '#fb923c',
                'LOW_ALPHA': '#fbbf24',
                # System events (blue/cyan)
                'DATA_ROTATION': '#06b6d4',
                'EARLY_STOP_BLOCKED': '#0ea5e9',
                # Architecture (teal/green)
                'STRATEGY_PRUNE': '#14b8a6',
                'GRADIENT_FLOW_UPDATE': '#10b981',
                'GRADIENT_FLOW_INITIALIZED': '#22c55e',
                # Positive (green)
                'BEST_CHECKPOINT_SAVED': '#22c55e',
                'CV_DECISION': '#a3e635',
                'RESOLVED': '#4ade80',
            }

            DEFAULT_COLORS = {
                'failure': '#ef4444',
                'warning_start': '#f59e0b',
                'warning_resolved': '#22c55e',
                'corrective_action': '#3b82f6',
                'other': '#6b7280',
            }

            EVENT_SYMBOLS = {
                'failure': 'X',
                'warning_start': '^',
                'warning_resolved': 'v',
                'corrective_action': 'o',
                'best_checkpoint_saved': '*',
                'cv_decision': '*',
                'gradient_flow_initialized': '*',
                'gradient_flow_update': '*',
                'strategy_prune': 'P',
                'other': 's',
            }

            def get_color(event_type, event_subtype):
                if event_subtype:
                    normalized = event_subtype.upper().replace(' ', '_')
                    if normalized in EVENT_COLORS:
                        return EVENT_COLORS[normalized]
                return DEFAULT_COLORS.get(event_type, '#6b7280')

            def get_symbol(event_type):
                return EVENT_SYMBOLS.get(event_type, 's')

            # Group events by unique (event_type, event_subtype) for separate Y rows
            event_types_seen = {}  # key -> list of epochs
            for epoch, event_type, event_subtype, description in all_events:
                key = (event_type, event_subtype or 'UNKNOWN')
                if key not in event_types_seen:
                    event_types_seen[key] = []
                event_types_seen[key].append(epoch)

            # Sort event types for consistent ordering (failures first, then others)
            def sort_key(key):
                event_type, subtype = key
                type_order = {'failure': 0, 'warning_start': 1, 'warning_resolved': 2,
                              'corrective_action': 3, 'other': 4}
                return (type_order.get(event_type, 5), subtype)

            sorted_event_types = sorted(event_types_seen.keys(), key=sort_key)

            # Assign Y position to each event type
            y_positions = {}
            for i, key in enumerate(sorted_event_types):
                y_positions[key] = i

            n_rows = len(sorted_event_types)
            plotted_labels = set()

            # First pass: draw shaded regions for consecutive failures
            for key, epoch_list in event_types_seen.items():
                event_type, subtype = key
                if event_type != 'failure':
                    continue

                y_pos = y_positions[key]
                color = get_color(event_type, subtype)
                epoch_list_sorted = sorted(epoch_list)

                # Find consecutive runs
                if len(epoch_list_sorted) > 0:
                    runs = []
                    run_start = epoch_list_sorted[0]
                    run_end = epoch_list_sorted[0]

                    for ep in epoch_list_sorted[1:]:
                        if ep == run_end + 1:
                            # Consecutive
                            run_end = ep
                        else:
                            # Gap - save current run, start new one
                            runs.append((run_start, run_end))
                            run_start = ep
                            run_end = ep
                    runs.append((run_start, run_end))

                    # Draw shaded boxes for runs longer than 1 epoch
                    for start, end in runs:
                        if end > start:
                            # Shaded box spanning the duration
                            ax8.axhspan(y_pos - 0.4, y_pos + 0.4,
                                       xmin=(start - 0.5) / n_epochs if n_epochs > 0 else 0,
                                       xmax=(end + 0.5) / n_epochs if n_epochs > 0 else 1,
                                       alpha=0.3, color=color, zorder=1)
                            # Also draw using axvspan for better alignment
                            ax8.fill_between([start - 0.5, end + 0.5],
                                            y_pos - 0.4, y_pos + 0.4,
                                            alpha=0.3, color=color, zorder=1)

            # Second pass: plot individual event markers
            for key, epoch_list in event_types_seen.items():
                event_type, subtype = key
                y_pos = y_positions[key]
                color = get_color(event_type, subtype)
                symbol = get_symbol(event_type)

                # Label for legend
                label_key = f'{subtype} ({event_type})'
                label = label_key if label_key not in plotted_labels else ''
                if label:
                    plotted_labels.add(label_key)

                ax8.scatter(epoch_list, [y_pos] * len(epoch_list),
                           s=120, c=color, marker=symbol,
                           zorder=10, edgecolors='black', linewidths=1,
                           label=label, alpha=0.9)

            # Add Y-axis labels for each event type
            y_labels = []
            y_ticks = []
            for key in sorted_event_types:
                event_type, subtype = key
                y_ticks.append(y_positions[key])
                # Shorten label: just show subtype
                y_labels.append(subtype.replace('_', ' ').title()[:20])

            ax8.set_yticks(y_ticks)
            ax8.set_yticklabels(y_labels, fontsize=8)
            ax8.set_ylim(-0.5, n_rows - 0.5)

            ax8.set_ylabel('Events', fontsize=12, fontweight='bold')
            ax8.set_xlabel('Epoch', fontsize=12, fontweight='bold')
            ax8.legend(loc='center left', bbox_to_anchor=(1.01, 0.5), fontsize=7, ncol=1)
            ax8.grid(True, alpha=0.3, axis='x')
        else:
            ax8.text(0.5, 0.5, 'No events recorded', ha='center', va='center',
                    transform=ax8.transAxes, fontsize=12, color='gray')
            ax8.set_ylabel('Events', fontsize=12, fontweight='bold')
            ax8.set_xlabel('Epoch', fontsize=12, fontweight='bold')

        ax8.set_xlim(left=-1, right=max(epochs) + 1 if epochs else n_epochs)
        
        # Add vertical lines for data rotation across ALL panels
        if rotation_epochs:
            for ax in [ax1, ax_marginal, ax2, ax_weights, ax3, ax4, ax5, ax6, ax7, ax_joint, ax_rank, ax8]:
                for rot_epoch in rotation_epochs:
                    ax.axvline(x=rot_epoch, color='cyan', linestyle='--', linewidth=1.5, alpha=0.5, zorder=1)
        
        # Add metadata text (left side)
        metadata_text = []
        if optimizer_params:
            metadata_text.append(f"Initial LR: {optimizer_params.get('lr', 'N/A')}")
        if training_info and 'best_checkpoint_epoch' in training_info:
            metadata_text.append(f"Best Epoch: {training_info.get('best_checkpoint_epoch', 'N/A')}")
        if metadata_text:
            fig.text(0.02, 0.02, ' | '.join(metadata_text), fontsize=9,
                    verticalalignment='bottom', style='italic', color='gray')

        # Add session_id and job_id footer (right side)
        footer_parts = []
        if session_id:
            footer_parts.append(f"session: {session_id}")
        if job_id:
            footer_parts.append(f"job: {job_id}")
        if footer_parts:
            fig.text(0.98, 0.02, ' | '.join(footer_parts), fontsize=8,
                    verticalalignment='bottom', horizontalalignment='right',
                    style='italic', color='gray', family='monospace')
        
        # Save plot
        plot_path = os.path.join(output_dir, "training_timeline.png")
        plt.savefig(plot_path, dpi=150)  # No bbox_inches='tight' - prevents labels from exploding figure size
        plt.close()

        logger.info(f"📊 Training timeline plot saved to: {plot_path}")
        
    except Exception as e:
        logger.error(f"❌ Failed to plot training timeline: {e}")
        logger.error(traceback.format_exc())


def plot_sp_training_timeline(
    training_timeline: List[Dict],
    output_dir: str,
    n_epochs: int,
    optimizer_params: Optional[Dict] = None,
    training_info: Optional[Dict] = None,
    hostname: Optional[str] = None,
    software_version: Optional[str] = None,
    session_id: Optional[str] = None,
    job_id: Optional[str] = None,
) -> None:
    """Plot comprehensive Single Predictor training timeline: loss, LR, metrics, and events as PNG.
    
    Creates a multi-panel plot showing:
    - Training and validation loss over epochs
    - Learning rate schedule
    - Metrics (AUC, accuracy, etc.)
    - Timeline events (warnings, errors, corrective actions)
    
    Args:
        training_timeline: List of epoch entry dictionaries from SP training
        output_dir: Directory to save the plot
        n_epochs: Total number of epochs
        optimizer_params: Optional optimizer parameters for metadata
        training_info: Optional training info dict (for best checkpoint epoch)
        hostname: Optional hostname for metadata display
        software_version: Optional software version for metadata display
        session_id: Optional session ID for metadata display
        job_id: Optional job ID for metadata display
    """
    try:
        import matplotlib.pyplot as plt
        import numpy as np
        import matplotlib.cm as cm
    except ImportError:
        logger.warning("⚠️  matplotlib not available, skipping timeline plot")
        return
    
    if not training_timeline:
        logger.warning("⚠️  No timeline data available for plotting")
        return
    
    try:
        # Extract data from timeline
        epochs = []
        train_losses = []
        val_losses = []
        learning_rates = []
        es_learning_rates = []  # ES (Embedding Space) learning rates
        aucs = []
        accuracies = []
        pr_aucs = []
        roc_aucs = []
        gradient_norms = []
        embedding_stds = []  # Embedding std for collapse detection

        # Class separation metrics (for collapse detection)
        class_separations = []
        cohens_ds = []
        mean_prob_pos_classes = []
        mean_prob_neg_classes = []
        prob_ranges = []
        model_collapsed_flags = []

        # Track all timeline events
        timeline_events = []
        warnings = []
        corrective_actions = []
        
        for entry in training_timeline:
            if not isinstance(entry, dict):
                continue
            
            epoch = entry.get('epoch')
            if epoch is None:
                continue
            
            # Check if this is an event entry vs epoch entry
            event_type = entry.get('event_type')
            has_epoch_metrics = entry.get('train_loss') is not None or entry.get('learning_rate') is not None
            
            if event_type and not has_epoch_metrics:
                # Timeline event
                event_subtype = entry.get('warning_type') or entry.get('error_type') or entry.get('action_type', 'UNKNOWN')
                description = entry.get('description', entry.get('warning_type', entry.get('error_type', 'Event')))
                timeline_events.append((epoch, event_type, event_subtype, description))
                continue
            
            # Epoch entry - extract metrics
            epochs.append(epoch)
            train_losses.append(entry.get('train_loss'))
            val_losses.append(entry.get('validation_loss'))
            learning_rates.append(entry.get('learning_rate'))
            es_learning_rates.append(entry.get('es_learning_rate'))  # Extract ES LR
            
            # Extract metrics
            metrics = entry.get('metrics', {})
            if isinstance(metrics, dict):
                aucs.append(metrics.get('auc'))
                accuracies.append(metrics.get('accuracy'))
                pr_aucs.append(metrics.get('pr_auc'))
                roc_aucs.append(metrics.get('roc_auc'))
            else:
                aucs.append(None)
                accuracies.append(None)
                pr_aucs.append(None)
                roc_aucs.append(None)
            
            # Gradient norm
            grad_data = entry.get('gradients', {})
            if grad_data and isinstance(grad_data, dict):
                gradient_norms.append(grad_data.get('unclipped_norm'))
            else:
                gradient_norms.append(entry.get('gradient_norm'))

            # Embedding std (for collapse detection)
            embedding_stds.append(entry.get('embedding_std'))

            # Class separation metrics (for collapse detection)
            class_separations.append(metrics.get('class_separation') if isinstance(metrics, dict) else None)
            cohens_ds.append(metrics.get('cohens_d') if isinstance(metrics, dict) else None)
            mean_prob_pos_classes.append(metrics.get('mean_prob_pos_class') if isinstance(metrics, dict) else None)
            mean_prob_neg_classes.append(metrics.get('mean_prob_neg_class') if isinstance(metrics, dict) else None)
            prob_ranges.append(metrics.get('prob_range') if isinstance(metrics, dict) else None)
            model_collapsed_flags.append(metrics.get('model_collapsed', False) if isinstance(metrics, dict) else False)

            # Track warnings and corrective actions
            if entry.get('warnings'):
                for warning in entry.get('warnings', []):
                    warnings.append((epoch, warning.get('type', 'UNKNOWN')))
            
            if entry.get('corrective_actions'):
                for action in entry.get('corrective_actions', []):
                    if isinstance(action, dict):
                        corrective_actions.append((epoch, action.get('action_type', 'UNKNOWN'), action.get('trigger', 'UNKNOWN')))
        
        if not epochs:
            logger.warning("⚠️  No valid epoch data in timeline for plotting")
            return
        
        # Create figure with subplots - tighter spacing, no individual titles
        fig = plt.figure(figsize=(16, 18))
        gs = fig.add_gridspec(7, 1, hspace=0.08, height_ratios=[1, 1, 1, 1, 1, 1, 0.8])

        ax1 = fig.add_subplot(gs[0])  # Loss curves
        ax2 = fig.add_subplot(gs[1])  # Learning rate
        ax3 = fig.add_subplot(gs[2])  # AUC / ROC-AUC
        ax3b = fig.add_subplot(gs[3])  # PR-AUC
        ax_class_sep = fig.add_subplot(gs[4])  # Class separation metrics
        ax5 = fig.add_subplot(gs[5])  # Embedding Std
        ax4 = fig.add_subplot(gs[6])  # Events timeline
        
        epochs_array = np.array(epochs)
        
        # ========== SUBPLOT 1: Loss Curves ==========
        train_mask = np.array([x is not None for x in train_losses])
        if train_mask.any():
            ax1.plot(epochs_array[train_mask], np.array(train_losses)[train_mask], 
                    '-', linewidth=2, color='#dc2626', label='Train Loss', 
                    marker='o', markersize=3, alpha=0.8)
        
        val_mask = np.array([x is not None for x in val_losses])
        if val_mask.any():
            ax1.plot(epochs_array[val_mask], np.array(val_losses)[val_mask], 
                    '--', linewidth=2, color='#f97316', label='Val Loss', 
                    marker='s', markersize=3, alpha=0.8)
            
            # Mark best epoch
            valid_val_losses = [(e, v) for e, v in zip(epochs_array[val_mask], np.array(val_losses)[val_mask]) if v is not None and not np.isnan(v)]
            if valid_val_losses:
                best_epoch, best_loss = min(valid_val_losses, key=lambda x: x[1])
                ax1.scatter([best_epoch], [best_loss], s=200, c='gold', marker='*',
                          zorder=10, edgecolors='black', linewidths=2, label='Best Epoch')
        
        ax1.set_ylabel('Loss', fontsize=12, fontweight='bold')
        fig.suptitle('SP Training Timeline: Loss + LR + Metrics + Events', fontsize=16, fontweight='bold', y=0.98)
        ax1.legend(loc='best', fontsize=10)
        ax1.grid(True, alpha=0.3)
        ax1.set_xlim(left=-1)
        ax1.tick_params(labelbottom=False)  # Hide x-axis labels
        
        # ========== SUBPLOT 2: Learning Rate ==========
        lr_mask = np.array([x is not None and x > 0 for x in learning_rates])
        if lr_mask.any():
            ax2.plot(epochs_array[lr_mask], np.array(learning_rates)[lr_mask], 
                    '-', linewidth=2.5, color='#2563eb', label='SP Learning Rate', 
                    marker='o', markersize=3, alpha=0.8)
        
        # Plot ES LR if available
        es_lr_mask = np.array([x is not None and x > 0 for x in es_learning_rates])
        if es_lr_mask.any():
            ax2.plot(epochs_array[es_lr_mask], np.array(es_learning_rates)[es_lr_mask], 
                    '--', linewidth=2.5, color='#10b981', label='ES Learning Rate', 
                    marker='s', markersize=3, alpha=0.8)
        
        # Mark ES freeze/unfreeze events on LR plot
        for epoch, event_type, event_subtype, description in timeline_events:
            if event_type == 'es_frozen':
                # Mark ES frozen with vertical line
                ax2.axvline(epoch, color='orange', linestyle=':', linewidth=2, alpha=0.7, 
                           label='ES Frozen' if epoch == min([e for e, et, _, _ in timeline_events if et == 'es_frozen'], default=epoch) else '')
            elif event_type == 'es_unfrozen':
                # Mark ES unfrozen with vertical line
                ax2.axvline(epoch, color='purple', linestyle=':', linewidth=2, alpha=0.7,
                           label='ES Unfrozen' if epoch == min([e for e, et, _, _ in timeline_events if et == 'es_unfrozen'], default=epoch) else '')
                # Also mark the ES LR start point
                if es_lr_mask.any() and epoch < len(es_learning_rates):
                    es_lr_at_unfreeze = es_learning_rates[epoch] if epoch < len(es_learning_rates) else None
                    if es_lr_at_unfreeze is not None and es_lr_at_unfreeze > 0:
                        ax2.scatter([epoch], [es_lr_at_unfreeze], s=200, c='purple', marker='D',
                                   zorder=10, edgecolors='black', linewidths=2, alpha=0.9)
            elif event_type == 'lr_adjustment':
                # Mark LR adjustments with markers
                if epoch >= 0 and epoch < len(learning_rates) and learning_rates[epoch] is not None:
                    lr_at_epoch = learning_rates[epoch]
                    adjustment_type = event_subtype if isinstance(event_subtype, str) else 'unknown'
                    # Use different markers/colors based on adjustment type
                    if 'encoder_increase' in adjustment_type or 'encoder' in adjustment_type.lower():
                        ax2.scatter([epoch], [lr_at_epoch], s=150, c='green', marker='^',
                                   zorder=10, edgecolors='black', linewidths=1.5, alpha=0.8,
                                   label='ES LR ↑' if epoch == min([e for e, et, _, _ in timeline_events if et == 'lr_adjustment'], default=epoch) else '')
                    elif 'predictor_decrease' in adjustment_type or 'predictor' in adjustment_type.lower():
                        ax2.scatter([epoch], [lr_at_epoch], s=150, c='red', marker='v',
                                   zorder=10, edgecolors='black', linewidths=1.5, alpha=0.8,
                                   label='SP LR ↓' if epoch == min([e for e, et, _, _ in timeline_events if et == 'lr_adjustment'], default=epoch) else '')
                    elif 'adaptive_initial' in adjustment_type:
                        # Initial adaptive adjustment (epoch -1, show at epoch 0)
                        if epoch == -1 and len(learning_rates) > 0 and learning_rates[0] is not None:
                            ax2.scatter([0], [learning_rates[0]], s=150, c='blue', marker='*',
                                       zorder=10, edgecolors='black', linewidths=1.5, alpha=0.8,
                                       label='Initial LR Adjust')
            elif event_type == 'training_restart':
                # Mark training restart with vertical line
                ax2.axvline(epoch, color='red', linestyle='--', linewidth=2, alpha=0.7,
                           label='Training Restart' if epoch == min([e for e, et, _, _ in timeline_events if et == 'training_restart'], default=epoch) else '')
            elif event_type == 'best_epoch':
                # Mark best epoch with star
                if epoch >= 0 and epoch < len(learning_rates) and learning_rates[epoch] is not None:
                    lr_at_epoch = learning_rates[epoch]
                    ax2.scatter([epoch], [lr_at_epoch], s=250, c='gold', marker='*',
                               zorder=11, edgecolors='black', linewidths=2, alpha=0.9,
                               label='Best Epoch' if epoch == min([e for e, et, _, _ in timeline_events if et == 'best_epoch'], default=epoch) else '')
        
        ax2.set_ylabel('Learning Rate', fontsize=12, fontweight='bold')
        ax2.legend(loc='best', fontsize=10)
        ax2.grid(True, alpha=0.3)
        ax2.set_yscale('log')
        ax2.set_xlim(left=-1)
        ax2.tick_params(labelbottom=False)  # Hide x-axis labels
        
        # ========== SUBPLOT 3: AUC / ROC-AUC ==========
        has_auc_metrics = False

        auc_mask = np.array([x is not None and not np.isnan(x) for x in aucs])
        roc_mask = np.array([x is not None and not np.isnan(x) for x in roc_aucs])

        if auc_mask.any():
            has_auc_metrics = True
            ax3.plot(epochs_array[auc_mask], np.array(aucs)[auc_mask],
                    '-', linewidth=2, color='#10b981', label='AUC',
                    marker='o', markersize=3, alpha=0.8)

        if roc_mask.any():
            has_auc_metrics = True
            ax3.plot(epochs_array[roc_mask], np.array(roc_aucs)[roc_mask],
                    '--', linewidth=2, color='#8b5cf6', label='ROC-AUC',
                    marker='s', markersize=3, alpha=0.8)

        if has_auc_metrics:
            ax3.set_ylabel('AUC-ROC', fontsize=12, fontweight='bold')
            ax3.legend(loc='best', fontsize=10)
            ax3.grid(True, alpha=0.3)
            ax3.set_xlim(left=-1)
        else:
            ax3.text(0.5, 0.5, 'No AUC metrics available', ha='center', va='center',
                    transform=ax3.transAxes, fontsize=12, color='gray')
            ax3.set_ylabel('AUC-ROC', fontsize=12, fontweight='bold')
        ax3.tick_params(labelbottom=False)  # Hide x-axis labels

        # ========== SUBPLOT 4: PR-AUC ==========
        has_pr_metrics = False

        pr_mask = np.array([x is not None and not np.isnan(x) for x in pr_aucs])

        if pr_mask.any():
            has_pr_metrics = True
            ax3b.plot(epochs_array[pr_mask], np.array(pr_aucs)[pr_mask],
                     '-', linewidth=2, color='#f59e0b', label='PR-AUC',
                     marker='^', markersize=3, alpha=0.8)

        if has_pr_metrics:
            ax3b.set_ylabel('PR-AUC', fontsize=12, fontweight='bold')
            ax3b.legend(loc='best', fontsize=10)
            ax3b.grid(True, alpha=0.3)
            ax3b.set_xlim(left=-1)
        else:
            ax3b.text(0.5, 0.5, 'No PR-AUC metrics available', ha='center', va='center',
                    transform=ax3b.transAxes, fontsize=12, color='gray')
            ax3b.set_ylabel('PR-AUC', fontsize=12, fontweight='bold')
        ax3b.tick_params(labelbottom=False)  # Hide x-axis labels

        # ========== SUBPLOT 5: Class Separation (Collapse Detection) ==========
        has_class_sep = False

        # Plot mean probability for positive vs negative class
        pos_prob_mask = np.array([x is not None and not np.isnan(x) for x in mean_prob_pos_classes])
        neg_prob_mask = np.array([x is not None and not np.isnan(x) for x in mean_prob_neg_classes])

        if pos_prob_mask.any():
            has_class_sep = True
            ax_class_sep.plot(epochs_array[pos_prob_mask], np.array(mean_prob_pos_classes)[pos_prob_mask],
                     '-', linewidth=2, color='#10b981', label='Mean P(pos) for actual positives',
                     marker='o', markersize=3, alpha=0.8)

        if neg_prob_mask.any():
            has_class_sep = True
            ax_class_sep.plot(epochs_array[neg_prob_mask], np.array(mean_prob_neg_classes)[neg_prob_mask],
                     '--', linewidth=2, color='#ef4444', label='Mean P(pos) for actual negatives',
                     marker='s', markersize=3, alpha=0.8)

        # Add reference line at 0.5 (random guessing)
        if has_class_sep:
            ax_class_sep.axhline(y=0.5, color='gray', linestyle=':', alpha=0.5, label='Random (0.5)')

        # Mark epochs where model collapsed
        collapse_epochs = [e for e, c in zip(epochs, model_collapsed_flags) if c]
        if collapse_epochs and has_class_sep:
            # Get y values at collapse epochs for scatter plot
            for ce in collapse_epochs:
                if ce in epochs:
                    idx = epochs.index(ce)
                    if idx < len(mean_prob_pos_classes) and mean_prob_pos_classes[idx] is not None:
                        ax_class_sep.scatter([ce], [mean_prob_pos_classes[idx]], s=200, c='red', marker='X',
                                           zorder=10, edgecolors='black', linewidths=2, alpha=0.9,
                                           label='Model Collapsed' if ce == collapse_epochs[0] else '')

        # Mark ES unfreeze event with vertical line
        for epoch, event_type, event_subtype, description in timeline_events:
            if event_type == 'es_unfrozen':
                ax_class_sep.axvline(epoch, color='purple', linestyle=':', linewidth=2, alpha=0.7,
                                    label='ES Unfrozen')
            elif event_type == 'post_unfreeze_collapse':
                ax_class_sep.axvline(epoch, color='red', linestyle='--', linewidth=2, alpha=0.7,
                                    label='Post-Unfreeze Collapse')

        if has_class_sep:
            ax_class_sep.set_ylabel('Class Probs', fontsize=12, fontweight='bold')
            ax_class_sep.legend(loc='best', fontsize=9, ncol=2)
            ax_class_sep.grid(True, alpha=0.3)
            ax_class_sep.set_xlim(left=-1)
            ax_class_sep.set_ylim(0, 1)
        else:
            ax_class_sep.text(0.5, 0.5, 'No class separation metrics available', ha='center', va='center',
                    transform=ax_class_sep.transAxes, fontsize=12, color='gray')
            ax_class_sep.set_ylabel('Class Probs', fontsize=12, fontweight='bold')
        ax_class_sep.tick_params(labelbottom=False)  # Hide x-axis labels

        # ========== SUBPLOT 6: Embedding Std (Collapse Detection) ==========
        has_embedding_std = False

        emb_std_mask = np.array([x is not None and not np.isnan(x) for x in embedding_stds])

        if emb_std_mask.any():
            has_embedding_std = True
            ax5.plot(epochs_array[emb_std_mask], np.array(embedding_stds)[emb_std_mask],
                     '-', linewidth=2, color='#8b5cf6', label='Embedding Std',
                     marker='o', markersize=3, alpha=0.8)

            # Add horizontal line at collapse threshold (0.01)
            ax5.axhline(y=0.01, color='red', linestyle='--', alpha=0.5, label='Collapse threshold')

        if has_embedding_std:
            ax5.set_ylabel('Embedding Std', fontsize=12, fontweight='bold')
            ax5.legend(loc='best', fontsize=10)
            ax5.grid(True, alpha=0.3)
            ax5.set_xlim(left=-1)
        else:
            ax5.text(0.5, 0.5, 'No embedding std data available', ha='center', va='center',
                    transform=ax5.transAxes, fontsize=12, color='gray')
            ax5.set_ylabel('Embedding Std', fontsize=12, fontweight='bold')
        ax5.tick_params(labelbottom=False)  # Hide x-axis labels

        # ========== SUBPLOT 6: Events Timeline ==========
        # Use same event plotting logic as ES
        all_events = []
        
        for epoch, warning_type in warnings:
            all_events.append((epoch, 'warning', warning_type, f'Warning: {warning_type}'))
        
        for epoch, action_type, trigger in corrective_actions:
            all_events.append((epoch, 'corrective_action', action_type, f'Action: {action_type}'))
        
        for epoch, event_type, event_subtype, description in timeline_events:
            all_events.append((epoch, event_type, event_subtype, description))
        
        if all_events:
            # ========== ORGANIZED EVENT VISUALIZATION (same system as ES) ==========
            # Symbol = what happened, Color = severity/domain

            EVENT_COLORS = {
                # Overfitting (red spectrum)
                'MILD_OVERFITTING': '#ffb3b3', 'MODERATE_OVERFITTING': '#ff4444',
                'SEVERE_OVERFITTING': '#8b0000', 'OVERFITTING': '#ff4444',
                # Learning issues (blue spectrum)
                'NO_LEARNING': '#4169e1', 'SLOW_LEARNING': '#6495ed',
                'DIVERGENCE': '#00008b', 'UNSTABLE_LOSS': '#1e90ff',
                'RANDOM_PREDICTIONS': '#4169e1',  # random guessing = learning issue
                # Gradient/weight issues (orange spectrum)
                'GRADIENT_EXPLOSION': '#ff8c00', 'GRADIENT_VANISHING': '#ffa500',
                'WEIGHT_EXPLOSION': '#ff6347', 'HIGH_ALPHA': '#ff7f50', 'LOW_ALPHA': '#ffd700',
                # Collapse issues (purple spectrum)
                'EMBEDDING_COLLAPSE': '#9932cc', 'REPRESENTATION_COLLAPSE': '#8b008b',
                'POST_UNFREEZE_COLLAPSE': '#dc143c',  # crimson - critical
                'MODEL_COLLAPSED': '#dc143c',  # crimson - critical
                # ES control events (purple/green spectrum)
                'ES_UNFROZEN': '#9400d3', 'ES_FROZEN': '#8b008b',
                'LR_ADJUSTMENT': '#32cd32',  # green - corrective action
                # System events
                'DATA_ROTATION': '#00ced1', 'EARLY_STOP_BLOCKED': '#ffa07a',
                # Positive/resolved
                'RESOLVED': '#32cd32',
            }
            DEFAULT_COLORS = {
                'failure': '#dc143c', 'error': '#dc143c', 'warning_start': '#ffd700',
                'warning_resolved': '#32cd32', 'corrective_action': '#4169e1',
                'warning': '#ffd700', 'weightwatcher_warning': '#ff8c00',
                'es_unfrozen': '#9400d3', 'es_frozen': '#8b008b',
                'post_unfreeze_collapse': '#dc143c', 'lr_adjustment': '#32cd32',
                'other': '#808080',
            }
            EVENT_SYMBOLS = {
                'failure': 'x', 'error': 'x', 'warning_start': '^', 'warning_resolved': 'v',
                'corrective_action': 'o', 'warning': '^', 'weightwatcher_warning': 'D',
                'es_unfrozen': 'D', 'es_frozen': 's', 'post_unfreeze_collapse': 'X',
                'lr_adjustment': '^', 'other': '*',
            }

            def get_event_color(event_type, event_subtype):
                if event_subtype and event_subtype.upper() in EVENT_COLORS:
                    return EVENT_COLORS[event_subtype.upper()]
                normalized = event_subtype.upper().replace(' ', '_') if event_subtype else ''
                if normalized in EVENT_COLORS:
                    return EVENT_COLORS[normalized]
                return DEFAULT_COLORS.get(event_type, '#808080')

            def get_event_symbol(event_type):
                return EVENT_SYMBOLS.get(event_type, '*')

            CATEGORY_ORDER = [
                ('Overfitting', ['MILD_OVERFITTING', 'MODERATE_OVERFITTING', 'SEVERE_OVERFITTING', 'OVERFITTING']),
                ('Learning', ['NO_LEARNING', 'SLOW_LEARNING', 'DIVERGENCE', 'UNSTABLE_LOSS', 'RANDOM_PREDICTIONS']),
                ('Gradients', ['GRADIENT_EXPLOSION', 'GRADIENT_VANISHING', 'WEIGHT_EXPLOSION']),
                ('Collapse', ['EMBEDDING_COLLAPSE', 'REPRESENTATION_COLLAPSE', 'POST_UNFREEZE_COLLAPSE', 'MODEL_COLLAPSED']),
                ('WeightWatcher', ['HIGH_ALPHA', 'LOW_ALPHA']),
                ('ES Control', ['ES_UNFROZEN', 'ES_FROZEN', 'LR_ADJUSTMENT']),
                ('System', ['DATA_ROTATION', 'EARLY_STOP_BLOCKED']),
            ]
            subtype_to_category = {}
            for cat_name, subtypes in CATEGORY_ORDER:
                for st in subtypes:
                    subtype_to_category[st] = cat_name

            events_by_category = {cat: [] for cat, _ in CATEGORY_ORDER}
            events_by_category['Other'] = []

            for epoch, event_type, event_subtype, description in all_events:
                normalized_subtype = event_subtype.upper().replace(' ', '_') if event_subtype else 'UNKNOWN'
                category = subtype_to_category.get(normalized_subtype, 'Other')
                events_by_category[category].append((epoch, event_type, event_subtype, description))

            y_offset = 0
            y_spacing = 1.0
            plotted_labels = set()

            for category, subtypes in CATEGORY_ORDER + [('Other', [])]:
                category_events = events_by_category.get(category, [])
                if not category_events:
                    continue
                y_pos = y_offset
                for epoch, event_type, event_subtype, description in category_events:
                    color = get_event_color(event_type, event_subtype)
                    symbol = get_event_symbol(event_type)
                    label_key = f'{event_subtype} ({event_type})'
                    label = label_key if label_key not in plotted_labels else ''
                    if label:
                        plotted_labels.add(label_key)
                    ax4.scatter([epoch], [y_pos], s=150, c=color, marker=symbol,
                               zorder=10, edgecolors='black', linewidths=1.5,
                               label=label, alpha=0.85)
                ax4.text(-2, y_pos, category, fontsize=9, fontweight='bold',
                        ha='right', va='center', color='#555555')
                y_offset += y_spacing

            ax4.set_ylabel('Events', fontsize=12, fontweight='bold')
            ax4.set_xlabel('Epoch', fontsize=12, fontweight='bold')
            ax4.legend(loc='upper right', fontsize=8, ncol=2)
            ax4.grid(True, alpha=0.3, axis='x')
            ax4.set_yticks([])
        else:
            ax4.text(0.5, 0.5, 'No events recorded', ha='center', va='center',
                    transform=ax4.transAxes, fontsize=12, color='gray')
            ax4.set_ylabel('Events', fontsize=12, fontweight='bold')
            ax4.set_xlabel('Epoch', fontsize=12, fontweight='bold')
        
        ax4.set_xlim(left=-1, right=max(epochs) + 1 if epochs else n_epochs)
        
        # Add metadata at bottom of figure
        plot_path = os.path.join(output_dir, "sp_training_timeline.png")
        
        # Build metadata lines
        metadata_lines = []
        
        # Line 1: hostname and version
        line1_parts = []
        if hostname:
            line1_parts.append(f"Host: {hostname}")
        if software_version:
            line1_parts.append(f"Version: {software_version}")
        if line1_parts:
            metadata_lines.append(' | '.join(line1_parts))
        
        # Line 2: session_id and job_id
        line2_parts = []
        if session_id:
            line2_parts.append(f"Session: {session_id}")
        if job_id:
            line2_parts.append(f"Job: {job_id}")
        if line2_parts:
            metadata_lines.append(' | '.join(line2_parts))
        
        # Line 3: file path
        if plot_path:
            metadata_lines.append(f"File: {plot_path}")
        
        # Line 4: training info (Initial LR, Best Epoch)
        line4_parts = []
        if optimizer_params:
            line4_parts.append(f"Initial LR: {optimizer_params.get('lr', 'N/A')}")
        if training_info and 'best_checkpoint_epoch' in training_info:
            line4_parts.append(f"Best Epoch: {training_info.get('best_checkpoint_epoch', 'N/A')}")
        if line4_parts:
            metadata_lines.append(' | '.join(line4_parts))
        
        # Add metadata text to figure
        if metadata_lines:
            metadata_text = '\n'.join(metadata_lines)
            fig.text(0.02, 0.01, metadata_text, fontsize=8, 
                    verticalalignment='bottom', style='italic', color='gray',
                    family='monospace')
        
        # Save plot
        plt.savefig(plot_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        logger.info(f"📊 SP training timeline plot saved to: {plot_path}")

    except Exception as e:
        logger.error(f"❌ Failed to plot SP training timeline: {e}")
        logger.error(traceback.format_exc())


def plot_embedding_std_heatmap(
    training_timeline: List[Dict],
    output_dir: str,
    hostname: Optional[str] = None,
    software_version: Optional[str] = None,
) -> None:
    """Plot heatmap of embedding std per dimension over epochs.

    Creates a 2D heatmap where:
    - X-axis: epoch
    - Y-axis: embedding dimension (0 to d_model-1)
    - Color: std of that dimension at that epoch

    This visualizes how the entropy/differentiation of each embedding
    dimension evolves over training.

    Args:
        training_timeline: List of epoch entries with collapse_diagnostics
        output_dir: Directory to save the heatmap
        hostname: Optional hostname for title
        software_version: Optional version for title
    """
    try:
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        logger.warning("⚠️  matplotlib not available, skipping embedding std heatmap")
        return

    try:
        if not training_timeline:
            logger.warning("⚠️  No training timeline data for embedding std heatmap")
            return

        # Extract per-dimension std data from each epoch
        epochs = []
        std_per_dim_data = []

        for entry in training_timeline:
            epoch = entry.get('epoch', len(epochs))
            collapse_diag = entry.get('collapse_diagnostics')

            if collapse_diag and isinstance(collapse_diag, dict):
                joint_emb = collapse_diag.get('joint_embedding', {})
                std_full = joint_emb.get('std_per_dim_full')

                if std_full and isinstance(std_full, list) and len(std_full) > 0:
                    epochs.append(epoch)
                    std_per_dim_data.append(std_full)

        if not std_per_dim_data:
            logger.warning("⚠️  No per-dimension std data found in training timeline")
            return

        # Convert to numpy array: shape (n_epochs, d_model)
        std_matrix = np.array(std_per_dim_data)
        n_epochs_actual, d_model = std_matrix.shape

        logger.info(f"📊 Generating embedding std heatmap: {n_epochs_actual} epochs x {d_model} dimensions")

        # Create the heatmap
        fig, ax = plt.subplots(figsize=(14, 10))

        # Transpose so dimensions are on Y axis, epochs on X axis
        # Shape becomes (d_model, n_epochs)
        std_matrix_T = std_matrix.T

        # Create heatmap with imshow
        im = ax.imshow(
            std_matrix_T,
            aspect='auto',
            origin='lower',
            cmap='viridis',
            interpolation='nearest',
            vmin=0,
            vmax=max(0.08, np.percentile(std_matrix_T, 99))  # Cap at 99th percentile or 0.08
        )

        # Add colorbar
        cbar = fig.colorbar(im, ax=ax, label='Std per Dimension', shrink=0.8)

        # Labels
        ax.set_xlabel('Epoch', fontsize=12, fontweight='bold')
        ax.set_ylabel('Embedding Dimension', fontsize=12, fontweight='bold')

        # Title
        title_parts = ['Embedding Std/Dim Heatmap']
        if hostname:
            title_parts.append(f'({hostname}')
            if software_version:
                title_parts[-1] += f', {software_version})'
            else:
                title_parts[-1] += ')'
        ax.set_title(' '.join(title_parts), fontsize=14, fontweight='bold')

        # Set x-axis ticks to actual epochs
        if len(epochs) > 20:
            # Show every 10th epoch
            tick_indices = np.arange(0, len(epochs), max(1, len(epochs) // 20))
            ax.set_xticks(tick_indices)
            ax.set_xticklabels([epochs[i] for i in tick_indices])
        else:
            ax.set_xticks(range(len(epochs)))
            ax.set_xticklabels(epochs)

        # Set y-axis ticks (show every 16th or 32nd dimension)
        dim_step = 16 if d_model <= 256 else 32
        dim_ticks = np.arange(0, d_model, dim_step)
        ax.set_yticks(dim_ticks)
        ax.set_yticklabels(dim_ticks)

        # Add horizontal lines at key dimensions for reference
        for d in range(0, d_model, 64):
            ax.axhline(y=d, color='white', linestyle='--', linewidth=0.5, alpha=0.3)

        # Add vertical line at current epoch
        ax.axvline(x=len(epochs)-1, color='cyan', linestyle='--', linewidth=1.5, alpha=0.7)

        # Add reference lines for target std values
        # 0.06 = random init, 0.04 = target, 0.02 = collapse
        # These would show as colors in the legend area

        # Add summary statistics as text
        mean_std_start = std_matrix[0].mean() if len(std_matrix) > 0 else 0
        mean_std_end = std_matrix[-1].mean() if len(std_matrix) > 0 else 0
        min_std_end = std_matrix[-1].min() if len(std_matrix) > 0 else 0
        max_std_end = std_matrix[-1].max() if len(std_matrix) > 0 else 0

        stats_text = (
            f"Initial mean: {mean_std_start:.4f}\n"
            f"Final mean: {mean_std_end:.4f}\n"
            f"Final range: [{min_std_end:.4f}, {max_std_end:.4f}]"
        )
        ax.text(
            1.02, 0.5, stats_text,
            transform=ax.transAxes,
            fontsize=9,
            verticalalignment='center',
            family='monospace',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5)
        )

        plt.tight_layout()

        # Save
        plot_path = os.path.join(output_dir, 'embedding_std_heatmap.png')
        plt.savefig(plot_path, dpi=150, bbox_inches='tight')
        plt.close()

        logger.info(f"📊 Embedding std heatmap saved to: {plot_path}")

        # Also save the raw data as numpy for further analysis
        data_path = os.path.join(output_dir, 'embedding_std_per_dim.npz')
        np.savez(
            data_path,
            epochs=np.array(epochs),
            std_matrix=std_matrix,  # (n_epochs, d_model)
            d_model=d_model
        )
        logger.info(f"📊 Embedding std data saved to: {data_path}")

    except Exception as e:
        logger.error(f"❌ Failed to plot embedding std heatmap: {e}")
        logger.error(traceback.format_exc())

