#  -*- coding: utf-8 -*-
#
#  Copyright Featrix, Inc 2023-2025
#
#  Proprietary and Confidential.  Unauthorized use, copying or dissemination
#  of these materials is strictly prohibited.
#
from dataclasses import dataclass
import logging
import math

import torch
import torch.nn as nn
import torch.nn.functional as F

from featrix.neural.model_config import SimpleMLPConfig
from featrix.neural.sphere_config import SphereConfig

logger = logging.getLogger(__name__)


class AdaptiveDropoutScheduler:
    """
    Adaptive dropout that increases when AUC plateaus/declines.

    Monitors AUC-ROC and increases dropout when improvement stalls,
    helping prevent overfitting in later stages of training.

    Usage:
        scheduler = AdaptiveDropoutScheduler(base_dropout=0.1, max_dropout=0.4)
        for epoch in range(n_epochs):
            # ... training ...
            new_dropout = scheduler.step(current_auc)
            model.set_dropout(new_dropout)
    """

    def __init__(
        self,
        base_dropout: float = 0.1,
        max_dropout: float = 0.4,
        patience: int = 5,
        increase_factor: float = 1.2,
    ):
        """
        Initialize adaptive dropout scheduler.

        Args:
            base_dropout: Starting dropout rate
            max_dropout: Maximum dropout rate
            patience: Epochs without improvement before increasing dropout
            increase_factor: Factor to multiply dropout by when increasing
        """
        self.base_dropout = base_dropout
        self.max_dropout = max_dropout
        self.patience = patience
        self.increase_factor = increase_factor

        self.current_dropout = base_dropout
        self.best_auc = 0.0
        self.epochs_since_improvement = 0

    def step(self, current_auc: float) -> float:
        """
        Update dropout based on current AUC.

        Args:
            current_auc: Current epoch's AUC-ROC

        Returns:
            New dropout rate to use
        """
        if current_auc > self.best_auc:
            # Improvement - reset counter, keep current dropout
            self.best_auc = current_auc
            self.epochs_since_improvement = 0
            logger.debug(f"AdaptiveDropout: AUC improved to {current_auc:.4f}, dropout={self.current_dropout:.2f}")
        else:
            # No improvement
            self.epochs_since_improvement += 1

            if self.epochs_since_improvement >= self.patience:
                # Increase dropout
                old_dropout = self.current_dropout
                self.current_dropout = min(
                    self.current_dropout * self.increase_factor,
                    self.max_dropout
                )
                if self.current_dropout > old_dropout:
                    logger.info(
                        f"📈 AdaptiveDropout: No improvement for {self.epochs_since_improvement} epochs, "
                        f"increasing dropout {old_dropout:.2f} → {self.current_dropout:.2f}"
                    )
                # Reset counter after increase
                self.epochs_since_improvement = 0

        return self.current_dropout

    def get_dropout(self) -> float:
        """Get current dropout rate."""
        return self.current_dropout

    def reset(self) -> None:
        """Reset scheduler to initial state."""
        self.current_dropout = self.base_dropout
        self.best_auc = 0.0
        self.epochs_since_improvement = 0

# class SimpleMLP(nn.Module):
#     def __init__(
#         self, d_in, d_out, d_hidden, hidden_layers=0, dropout=0.1, normalize=True
#     ):
#         super().__init__()

#         if hidden_layers == 0:
#             self.model = nn.Linear(d_in, d_out)
#         else:
#             layers_prefix = [
#                 nn.Linear(d_in, d_hidden),
#             ]

#             layers_middle = []
#             for _ in range(hidden_layers - 1):
#                 layers_middle.append(nn.LeakyReLU())
#                 layers_middle.append(nn.Linear(d_hidden, d_hidden))

#             layers_suffix = [
#                 nn.BatchNorm1d(d_hidden, affine=False),
#                 nn.LeakyReLU(),
#                 nn.Dropout(p=dropout),
#                 nn.Linear(d_hidden, d_out),
#             ]

#             layers = layers_prefix + layers_middle + layers_suffix

#             self.model = nn.Sequential(*layers)

#         self.normalize = normalize

#     def forward(self, input):
#         out = self.model(input)
#         if self.normalize:
#             out = nn.functional.normalize(out, dim=1)
#         return out


class SelfAttentionBlock(nn.Module):
    """
    Self-attention block for single embedding vectors.

    Learns to attend to different dimensions of the embedding vector by:
    1. Creating multiple query/key/value projections (multi-head)
    2. Computing attention weights over the embedding dimensions
    3. Re-weighting the embedding based on learned importance

    This allows the model to learn which embedding dimensions are most
    relevant for the prediction task.

    Init strategies:
    - 'xavier': Standard xavier uniform init (good for long training, >=100 epochs)
    - 'per_head_orthogonal': Each head has orthogonal rows (original approach)
    - 'between_head_orthogonal': Different heads project to orthogonal subspaces
      (best for short training, <=50 epochs - forces diversity from start)
    """
    def __init__(self, d_model: int, n_heads: int = 4, dropout: float = 0.1,
                 init_strategy: str = 'between_head_orthogonal'):
        super().__init__()
        assert d_model % n_heads == 0, f"d_model ({d_model}) must be divisible by n_heads ({n_heads})"
        assert init_strategy in ('xavier', 'per_head_orthogonal', 'between_head_orthogonal'), \
            f"init_strategy must be one of: xavier, per_head_orthogonal, between_head_orthogonal"

        self.d_model = d_model
        self.n_heads = n_heads
        self.d_k = d_model // n_heads
        self.init_strategy = init_strategy

        # Projections for Q, K, V - each projects to d_model
        self.w_q = nn.Linear(d_model, d_model, bias=False)
        self.w_k = nn.Linear(d_model, d_model, bias=False)
        self.w_v = nn.Linear(d_model, d_model, bias=False)
        self.w_o = nn.Linear(d_model, d_model)

        self.dropout = nn.Dropout(dropout)
        self.layer_norm = nn.LayerNorm(d_model)

        # For diagnostic: track attention statistics
        self._last_attn_weights = None

        # Head mask for dynamic pruning: None = all heads active, tensor of 0/1 = mask
        self.register_buffer('head_mask', None)

        # Initialize weights based on strategy
        self._init_weights()

    def _init_weights(self):
        """
        Initialize attention weights based on the selected strategy.

        Strategies:
        - 'xavier': Standard xavier uniform - simple, works well for long training
        - 'per_head_orthogonal': Each head has orthogonal rows within itself
        - 'between_head_orthogonal': Different heads project to orthogonal subspaces,
          ensuring maximum diversity at initialization (best for short training)
        """
        if self.init_strategy == 'xavier':
            # Simple xavier init - good baseline for long training
            nn.init.xavier_uniform_(self.w_q.weight, gain=1.0)
            nn.init.xavier_uniform_(self.w_k.weight, gain=1.0)
            logger.debug(f"SelfAttentionBlock: Initialized {self.n_heads} heads with xavier (standard)")

        elif self.init_strategy == 'per_head_orthogonal':
            # Original approach: each head has orthogonal rows within itself
            for linear in [self.w_q, self.w_k]:
                weight = linear.weight.data
                for h in range(self.n_heads):
                    start_idx = h * self.d_k
                    end_idx = (h + 1) * self.d_k
                    head_weight = torch.empty(self.d_k, self.d_model, device=weight.device, dtype=weight.dtype)
                    nn.init.orthogonal_(head_weight, gain=1.0)
                    weight[start_idx:end_idx, :] = head_weight
            logger.debug(f"SelfAttentionBlock: Initialized {self.n_heads} heads with per-head orthogonal")

        elif self.init_strategy == 'between_head_orthogonal':
            # New approach: heads project to orthogonal subspaces
            # This ensures different heads attend to different parts of the input
            # from the very first step - critical for short training
            for linear in [self.w_q, self.w_k]:
                weight = linear.weight.data
                # Create one big orthogonal matrix [d_model, d_model]
                # Each head gets a d_k slice, guaranteed orthogonal to other heads
                full_orthogonal = torch.empty(self.d_model, self.d_model, device=weight.device, dtype=weight.dtype)
                nn.init.orthogonal_(full_orthogonal, gain=1.0)
                # Copy it to the weight matrix
                # w_q/w_k shape is [d_model, d_model] where rows are output dims
                weight.copy_(full_orthogonal)
            logger.debug(f"SelfAttentionBlock: Initialized {self.n_heads} heads with between-head orthogonal (diverse)")

        # V weights use standard xavier init - these project to output space
        nn.init.xavier_uniform_(self.w_v.weight, gain=1.0)

        # Output projection: moderate init to not disrupt residual connection
        nn.init.xavier_uniform_(self.w_o.weight, gain=0.5)
        nn.init.zeros_(self.w_o.bias)

    def set_head_mask(self, mask: torch.Tensor = None):
        """
        Set mask to disable specific attention heads.

        Args:
            mask: [n_heads] tensor of 0/1 values, or None to enable all heads.
                  0 = head disabled, 1 = head enabled
        """
        if mask is not None:
            assert mask.shape == (self.n_heads,), f"Mask shape must be [{self.n_heads}], got {mask.shape}"
            self.head_mask = mask.float()
        else:
            self.head_mask = None

    def prune_inactive_heads(self, threshold: float = 0.1):
        """
        Automatically disable heads that contribute little based on attention patterns.

        Args:
            threshold: Heads with utilization below this are disabled
        """
        if self._last_attn_weights is None:
            return

        attn = self._last_attn_weights  # [batch, n_heads, n_heads] - attention between heads

        # Compute per-head importance: how much each head attends to vs is attended from
        # Row = what this head attends to, Col = what attends to this head
        head_outgoing = attn.mean(dim=0).sum(dim=-1)  # [n_heads] - avg attention this head gives
        head_incoming = attn.mean(dim=0).sum(dim=0)   # [n_heads] - avg attention this head receives

        # Combine: heads that both give and receive attention are important
        head_importance = (head_outgoing + head_incoming) / 2

        # Normalize to [0, 1]
        if head_importance.max() > head_importance.min():
            head_importance = (head_importance - head_importance.min()) / (head_importance.max() - head_importance.min())
        else:
            head_importance = torch.ones(self.n_heads, device=attn.device)

        # Create mask: keep heads with importance > threshold
        mask = (head_importance > threshold).float()
        n_active = mask.sum().item()

        # Always keep at least 1 head
        if n_active == 0:
            mask[head_importance.argmax()] = 1.0

        self.head_mask = mask
        return {
            'head_importance': head_importance.tolist(),
            'mask': mask.tolist(),
            'n_active': int(mask.sum().item()),
            'n_total': self.n_heads,
        }

    def forward(self, x):
        """
        Args:
            x: [batch, d_model] - single embedding vector
            
        Returns:
            [batch, d_model] - attended representation
        """
        residual = x
        batch_size = x.size(0)
        
        # Project to Q, K, V: [batch, d_model]
        Q = self.w_q(x)  # [batch, d_model]
        K = self.w_k(x)  # [batch, d_model]
        V = self.w_v(x)  # [batch, d_model]
        
        # Reshape for multi-head: [batch, n_heads, d_k]
        Q = Q.view(batch_size, self.n_heads, self.d_k)  # [batch, n_heads, d_k]
        K = K.view(batch_size, self.n_heads, self.d_k)  # [batch, n_heads, d_k]
        V = V.view(batch_size, self.n_heads, self.d_k)  # [batch, n_heads, d_k]
        
        # Compute attention scores: Q @ K^T gives [batch, n_heads, d_k, d_k]
        # This learns relationships between different parts of the embedding
        scores = torch.matmul(Q, K.transpose(-2, -1)) / math.sqrt(self.d_k)  # [batch, n_heads, d_k, d_k]
        
        # Apply softmax to get attention weights
        attn_weights = F.softmax(scores, dim=-1)  # [batch, n_heads, d_k, d_k]

        # Store for diagnostics (detached to avoid memory leak)
        self._last_attn_weights = attn_weights.detach()

        attn_weights = self.dropout(attn_weights)

        # Apply attention to values
        attn_output = torch.matmul(attn_weights, V)  # [batch, n_heads, d_k]

        # Apply head mask if set (dynamic head pruning)
        # Use getattr for backwards compatibility with models saved before head_mask was added
        head_mask = getattr(self, 'head_mask', None)
        if head_mask is not None:
            # Expand mask to [1, n_heads, 1] for broadcasting
            mask = head_mask.view(1, self.n_heads, 1)
            attn_output = attn_output * mask

        # Concatenate heads: [batch, d_model]
        attn_output = attn_output.view(batch_size, self.d_model)
        
        # Output projection
        output = self.w_o(attn_output)  # [batch, d_model]
        output = self.dropout(output)
        
        # Add residual and layer norm
        output = self.layer_norm(output + residual)

        return output

    def get_head_diagnostics(self) -> dict:
        """
        Compute diagnostics to assess if we have too many or too few heads.

        Returns dict with:
        - head_entropy: avg entropy per head (higher = more diverse attention)
        - head_similarity: avg cosine similarity between heads (lower = more diverse heads)
        - effective_heads: estimated number of non-redundant heads
        - head_mass: per-head contribution (sums to 1.0)
        - head_gini: Gini coefficient of head mass (0=equal, 1=one head dominates)
        - dominant_head: which head has the most mass
        - dominant_head_mass: fraction of total attention from dominant head

        Interpretation:
        - head_similarity > 0.8: heads are too similar, probably too many heads
        - head_entropy < 0.1: attention is too focused, heads may be underutilized
        - effective_heads < n_heads * 0.5: many redundant heads, consider fewer
        - head_gini > 0.5: attention is concentrated in few heads
        - dominant_head_mass > 0.7: you effectively have a 1-head model
        """
        if self._last_attn_weights is None:
            return {'error': 'No attention weights captured yet'}

        attn = self._last_attn_weights  # [batch, n_heads, n_heads] - attention between heads
        batch_size = attn.size(0)

        # 1. Head entropy: measure how spread out attention is per head (row-wise)
        # Each row shows what that head attends to
        entropy = -(attn * torch.log(attn + 1e-10)).sum(dim=-1)  # [batch, n_heads]
        max_entropy = math.log(self.n_heads)  # Maximum possible entropy
        normalized_entropy = entropy / max_entropy  # [batch, n_heads], range [0, 1]
        avg_entropy = normalized_entropy.mean().item()

        # 2. Head similarity: cosine similarity between heads' attention patterns (rows)
        attn_norm = attn / (attn.norm(dim=-1, keepdim=True) + 1e-10)  # [batch, n_heads, n_heads]
        # Compute pairwise similarity: [batch, n_heads, n_heads]
        similarity_matrix = torch.bmm(attn_norm, attn_norm.transpose(1, 2))
        # Average off-diagonal elements (exclude self-similarity)
        mask = 1 - torch.eye(self.n_heads, device=attn.device).unsqueeze(0)
        avg_similarity = (similarity_matrix * mask).sum() / (mask.sum() * batch_size)
        avg_similarity = avg_similarity.item()

        # 3. Effective heads: use singular values to estimate rank
        attn_mean = attn.mean(dim=0)  # [n_heads, n_heads]
        try:
            _, S, _ = torch.svd(attn_mean)
            # Effective rank: sum(s_i) ^ 2 / sum(s_i^2)
            S_sum = S.sum()
            S_sq_sum = (S ** 2).sum()
            effective_heads = (S_sum ** 2 / S_sq_sum).item() if S_sq_sum > 0 else self.n_heads
        except Exception:
            effective_heads = self.n_heads  # Fallback if SVD fails

        # 4. Per-head mass: how much total attention does each head contribute?
        # Sum attention weights per head across batch, normalize to get distribution
        head_mass = attn.sum(dim=-1).mean(dim=0)  # [n_heads] - avg attention mass per head
        head_mass = head_mass / (head_mass.sum() + 1e-10)  # Normalize to sum to 1.0
        head_mass_list = head_mass.tolist()

        # 5. Gini coefficient: measure inequality of head contributions
        # Gini = 0 means all heads contribute equally, Gini = 1 means one head dominates
        sorted_mass, _ = torch.sort(head_mass)
        n = self.n_heads
        cumsum = torch.cumsum(sorted_mass, dim=0)
        gini = (2 * torch.sum((torch.arange(1, n + 1, device=attn.device) * sorted_mass)) - (n + 1) * sorted_mass.sum()) / (n * sorted_mass.sum() + 1e-10)
        gini = gini.item()

        # 6. Dominant head analysis
        dominant_head = int(head_mass.argmax().item())
        dominant_head_mass = head_mass[dominant_head].item()

        # 7. Build ASCII similarity matrix for logging
        sim_matrix_avg = similarity_matrix.mean(dim=0)  # [n_heads, n_heads]
        ascii_matrix = self._format_similarity_matrix_ascii(sim_matrix_avg)

        # 8. Actionable interpretation
        interpretation = []
        if dominant_head_mass > 0.7:
            interpretation.append(f"HEAD_{dominant_head} dominates with {dominant_head_mass:.0%} - effectively a 1-head model")
        elif dominant_head_mass > 0.5:
            interpretation.append(f"HEAD_{dominant_head} has {dominant_head_mass:.0%} - consider fewer heads")
        if gini > 0.5:
            interpretation.append(f"High Gini ({gini:.2f}) - attention concentrated in few heads")
        if effective_heads < self.n_heads * 0.5:
            interpretation.append(f"Only {effective_heads:.1f}/{self.n_heads} effective heads - redundancy detected")
        if not interpretation:
            interpretation.append("Head utilization looks healthy")

        return {
            'n_heads': self.n_heads,
            'd_k': self.d_k,
            'head_entropy': avg_entropy,
            'head_similarity': avg_similarity,
            'effective_heads': effective_heads,
            'utilization': effective_heads / self.n_heads,
            'head_mass': head_mass_list,
            'head_gini': gini,
            'dominant_head': dominant_head,
            'dominant_head_mass': dominant_head_mass,
            'interpretation': interpretation,
            'similarity_matrix_ascii': ascii_matrix,
        }

    def _format_similarity_matrix_ascii(self, sim_matrix: torch.Tensor) -> str:
        """
        Format similarity matrix as numeric table for logging.

        Shows actual similarity values (0.0-1.0) between heads.
        """
        n = sim_matrix.size(0)

        lines = []
        # Header row
        header = "      " + "".join(f"  H{i:d}  " for i in range(n))
        lines.append(header)
        lines.append("      " + "-" * (6 * n))

        for i in range(n):
            row = f"H{i}:   "
            for j in range(n):
                val = sim_matrix[i, j].item()
                if i == j:
                    row += "  1.00 "  # Diagonal (self-similarity = 1.0)
                else:
                    row += f" {val:5.2f} "
            lines.append(row)

        return "\n".join(lines)


class SimpleMLP(nn.Module):

    @staticmethod
    def _compute_attention_heads(d_hidden: int, configured_heads: int = None) -> int:
        """
        Compute optimal number of attention heads based on d_hidden.

        Auto-sizes to d_hidden // 64 (giving head_dim=64) with bounds [2, 16].
        This is a conservative "small model" prior - for small d_hidden, fewer heads
        avoids redundancy. For larger models, more heads are allowed.

        Examples:
            d_hidden=128 → 2 heads (head_dim=64)
            d_hidden=256 → 4 heads (head_dim=64)
            d_hidden=512 → 8 heads (head_dim=64)
            d_hidden=1024 → 16 heads (head_dim=64)

        If configured_heads is provided and divides d_hidden evenly, uses that instead.

        Args:
            d_hidden: Hidden dimension of the MLP
            configured_heads: Explicitly configured number of heads (optional)

        Returns:
            Number of attention heads that evenly divides d_hidden
        """
        # If explicitly configured and valid, use it
        if configured_heads is not None and d_hidden % configured_heads == 0:
            return configured_heads

        # Auto-size: target head_dim of 64, bounded [2, 16] heads
        # This is more conservative than head_dim=32 - fewer heads for small models
        auto_heads = max(2, min(16, d_hidden // 64))

        # Ensure it divides evenly - bias DOWNWARD to prefer fewer heads under uncertainty
        if d_hidden % auto_heads != 0:
            # Try lower values first (bias downward for safety)
            for delta in range(1, auto_heads):
                if auto_heads - delta >= 2 and d_hidden % (auto_heads - delta) == 0:
                    auto_heads = auto_heads - delta
                    break
            else:
                # Only try upward if downward failed
                for delta in range(1, 17 - auto_heads):
                    if auto_heads + delta <= 16 and d_hidden % (auto_heads + delta) == 0:
                        auto_heads = auto_heads + delta
                        break
                else:
                    # Fallback: find any divisor, prefer smaller
                    for n in [2, 4, 8, 16, 1]:
                        if d_hidden % n == 0:
                            auto_heads = n
                            break

        return auto_heads

    def __init__(
        # self, d_in, d_out, d_hidden, hidden_layers=0, dropout=0.1, normalize=True, residual=True, use_batch_norm=True,
        self,
        config: SimpleMLPConfig,
    ):
        super().__init__()

        self.config = config

        # Determine if attention should be enabled
        # If use_attention is None, check global config
        # Use getattr() for backward compatibility with old configs that don't have these fields
        use_attention = getattr(config, 'use_attention', None)
        if use_attention is None:
            sphere_config = SphereConfig.get_instance()
            self.use_attention = sphere_config.get_enable_predictor_attention()
            # Auto-size attention heads based on d_hidden if not explicitly configured
            configured_heads = sphere_config.get_predictor_attention_heads()
            self.attention_heads = self._compute_attention_heads(config.d_hidden, configured_heads)
        else:
            self.use_attention = use_attention
            configured_heads = getattr(config, 'attention_heads', None)
            self.attention_heads = self._compute_attention_heads(config.d_hidden, configured_heads)
        
        # Attention dropout defaults to main dropout if not specified
        attention_dropout = getattr(config, 'attention_dropout', None)
        self.attention_dropout = attention_dropout if attention_dropout is not None else config.dropout
        
        # Log attention configuration (debug level to avoid spam during grid search)
        if self.use_attention and config.n_hidden_layers > 0:
            logger.debug(f"Predictor attention ENABLED: {self.attention_heads} heads, dropout={self.attention_dropout:.3f}")
        elif self.use_attention and config.n_hidden_layers == 0:
            logger.debug(f"Predictor attention requested but n_hidden_layers=0 - attention disabled (requires hidden layers)")

        # If there's 0 requested hidden layers, we just use a single linear layer.
        if config.n_hidden_layers == 0:
            self.single_layer = nn.Linear(config.d_in, config.d_out)
            self.use_attention = False  # Can't use attention with 0 hidden layers

        self.linear_in = nn.Linear(config.d_in, config.d_hidden, bias=True)
        self.linear_out = nn.Linear(config.d_hidden, config.d_out, bias=True)

        # For global_residual, init linear_out to near-zero so output ≈ input at init
        # This makes identity trivial from the start (no learning needed for identity)
        global_residual = getattr(config, 'global_residual', False)
        if global_residual and config.d_in == config.d_out:
            nn.init.zeros_(self.linear_out.weight)
            nn.init.zeros_(self.linear_out.bias)
            logger.info(f"🎯 SimpleMLP: global_residual=True, zero-init linear_out for identity-at-init")

        module_list = []
        attention_list = []
        
        # Check for LayerNorm preference (better for small batches)
        use_layer_norm = getattr(config, 'use_layer_norm', False)

        for _ in range(config.n_hidden_layers):
            # Feedforward block
            # Priority: LayerNorm (if enabled) > BatchNorm (if enabled) > no normalization
            if use_layer_norm:
                # LayerNorm: stable regardless of batch size, better for small batches
                modules = [
                    nn.Linear(config.d_hidden, config.d_hidden),
                    nn.LayerNorm(config.d_hidden),
                    nn.GELU(),
                    nn.Dropout(config.dropout),
                ]
            elif config.use_batch_norm:
                # BatchNorm: needs batch_size >= 32 for stable statistics
                modules = [
                    nn.Linear(config.d_hidden, config.d_hidden),
                    nn.BatchNorm1d(config.d_hidden),
                    nn.GELU(),
                    nn.Dropout(config.dropout),
                ]
            else:
                modules = [
                    nn.Linear(config.d_hidden, config.d_hidden),
                    nn.GELU(),
                    nn.Dropout(config.dropout),
                ]

            module_list.append(nn.Sequential(*modules))
            
            # Attention block (if enabled)
            if self.use_attention:
                attention_list.append(
                    SelfAttentionBlock(
                        d_model=config.d_hidden,
                        n_heads=self.attention_heads,
                        dropout=self.attention_dropout
                    )
                )
            else:
                attention_list.append(None)

        self.layers = nn.ModuleList(module_list)
        self.attention_layers = nn.ModuleList(attention_list) if self.use_attention else None

        # Debug flag for logging batch norm statistics
        # Only enable for debugging - logs every forward pass (very verbose!)
        self.debug_batchnorm = True

        # Initialize weights properly to prevent gradient explosions in deeper networks
        self._init_weights()

    def _init_weights(self):
        """
        Initialize weights using appropriate initialization for stable gradient flow.

        For deeper networks (3+ layers), improper initialization can cause gradient
        explosions. We use different strategies based on the fan ratio:

        - Normal layers (fan_out/fan_in < 10): Kaiming initialization
        - Extreme expansion layers (fan_out/fan_in >= 10): Xavier initialization
          to prevent gradient explosion during backprop (e.g., 3→256 in short predictor)

        Uses gain=0.5 for output layer to prevent over-amplification when residual
        connections are used.
        """
        # Input projection: check for extreme fan ratio (like 3→256 in short predictor)
        fan_in = self.config.d_in
        fan_out = self.config.d_hidden
        fan_ratio = fan_out / fan_in if fan_in > 0 else 1.0

        if fan_ratio >= 10:
            # Extreme expansion (e.g., 3→256): use Xavier for balanced forward/backward
            # Kaiming fan_in would cause ~fan_ratio× gradient scaling during backprop
            nn.init.xavier_uniform_(self.linear_in.weight, gain=1.0)
            logger.debug(f"SimpleMLP: Using Xavier init for linear_in (fan_ratio={fan_ratio:.1f}×)")
        else:
            # Normal case: Kaiming for GELU (approximate as ReLU for gain calculation)
            nn.init.kaiming_normal_(self.linear_in.weight, mode='fan_in', nonlinearity='relu')
        if self.linear_in.bias is not None:
            nn.init.zeros_(self.linear_in.bias)

        # Hidden layers: Kaiming for each linear layer (these are d_hidden→d_hidden, fan_ratio=1)
        for layer_seq in self.layers:
            for module in layer_seq:
                if isinstance(module, nn.Linear):
                    nn.init.kaiming_normal_(module.weight, mode='fan_in', nonlinearity='relu')
                    if module.bias is not None:
                        nn.init.zeros_(module.bias)

        # Output projection: check for extreme contraction (like 256→3)
        out_fan_in = self.config.d_hidden
        out_fan_out = self.config.d_out
        out_fan_ratio = out_fan_in / out_fan_out if out_fan_out > 0 else 1.0

        global_residual = getattr(self.config, 'global_residual', False)
        if global_residual and self.config.d_in == self.config.d_out:
            # Already zero-initialized above for global_residual - don't overwrite
            pass
        elif out_fan_ratio >= 10:
            # Extreme contraction (e.g., 256→3): use Xavier for balanced forward/backward
            nn.init.xavier_uniform_(self.linear_out.weight, gain=0.5)
            logger.debug(f"SimpleMLP: Using Xavier init for linear_out (fan_ratio={out_fan_ratio:.1f}×)")
        else:
            nn.init.kaiming_normal_(self.linear_out.weight, mode='fan_out', nonlinearity='linear')
            # Scale down for deeper networks to prevent gradient explosion
            if self.config.n_hidden_layers >= 3:
                self.linear_out.weight.data *= 0.5
        if self.linear_out.bias is not None:
            nn.init.zeros_(self.linear_out.bias)

        # Single layer case (n_hidden_layers == 0)
        if hasattr(self, 'single_layer'):
            nn.init.xavier_uniform_(self.single_layer.weight, gain=1.0)
            if self.single_layer.bias is not None:
                nn.init.zeros_(self.single_layer.bias)

    def __setstate__(self, state):
        """Handle backward compatibility when loading old checkpoints.

        Old checkpoints may not have use_attention or attention_layers attributes.
        """
        self.__dict__.update(state)

        # Backward compatibility: add use_attention if missing
        if not hasattr(self, 'use_attention'):
            self.use_attention = False
            logger.debug("SimpleMLP.__setstate__: Added missing use_attention=False for backward compatibility")

        # Backward compatibility: add attention_layers if missing
        if not hasattr(self, 'attention_layers'):
            self.attention_layers = None
            logger.debug("SimpleMLP.__setstate__: Added missing attention_layers=None for backward compatibility")

        # Backward compatibility: add attention_heads if missing
        if not hasattr(self, 'attention_heads'):
            self.attention_heads = 4
            logger.debug("SimpleMLP.__setstate__: Added missing attention_heads=4 for backward compatibility")

        # Backward compatibility: add attention_dropout if missing
        if not hasattr(self, 'attention_dropout'):
            self.attention_dropout = getattr(self.config, 'dropout', 0.1) if hasattr(self, 'config') else 0.1
            logger.debug("SimpleMLP.__setstate__: Added missing attention_dropout for backward compatibility")

        # Backward compatibility: add debug_batchnorm if missing
        if not hasattr(self, 'debug_batchnorm'):
            self.debug_batchnorm = False

    def set_dropout(self, dropout: float) -> None:
        """
        Set dropout rate for all dropout layers in the model.

        Used by AdaptiveDropoutScheduler to adjust dropout during training.

        Args:
            dropout: New dropout rate (0.0 to 1.0)
        """
        for name, module in self.named_modules():
            if isinstance(module, nn.Dropout):
                module.p = dropout

        # Update attention dropout if using attention
        if self.use_attention and self.attention_layers is not None:
            for attn_layer in self.attention_layers:
                if attn_layer is not None and hasattr(attn_layer, 'dropout'):
                    attn_layer.dropout.p = dropout

        logger.debug(f"SimpleMLP: Set dropout to {dropout:.2f}")

    def get_attention_diagnostics(self) -> dict:
        """
        Get diagnostics for all attention layers to assess head count appropriateness.

        Returns dict with per-layer diagnostics and summary recommendation.

        Usage:
            mlp = SimpleMLP(config)
            # ... run some forward passes ...
            diag = mlp.get_attention_diagnostics()
            print(diag['recommendation'])
        """
        if not self.use_attention or self.attention_layers is None:
            return {'enabled': False, 'message': 'Attention not enabled'}

        layer_diagnostics = []
        for i, attn_layer in enumerate(self.attention_layers):
            if attn_layer is not None:
                diag = attn_layer.get_head_diagnostics()
                diag['layer'] = i
                layer_diagnostics.append(diag)

        if not layer_diagnostics:
            return {'enabled': True, 'message': 'No attention weights captured yet'}

        # Aggregate across layers
        avg_entropy = sum(d['head_entropy'] for d in layer_diagnostics) / len(layer_diagnostics)
        avg_similarity = sum(d['head_similarity'] for d in layer_diagnostics) / len(layer_diagnostics)
        avg_utilization = sum(d['utilization'] for d in layer_diagnostics) / len(layer_diagnostics)
        avg_gini = sum(d.get('head_gini', 0) for d in layer_diagnostics) / len(layer_diagnostics)

        # Get dominant head info from first layer
        dominant_head = layer_diagnostics[0].get('dominant_head', 0)
        dominant_head_mass = layer_diagnostics[0].get('dominant_head_mass', 0)
        head_mass = layer_diagnostics[0].get('head_mass', [])

        n_heads = layer_diagnostics[0]['n_heads']
        d_k = layer_diagnostics[0]['d_k']

        # Generate recommendation - actionable insights
        recommendation = []

        # Check for dominant head (most actionable signal)
        if dominant_head_mass > 0.7:
            recommendation.append(f"HEAD_{dominant_head} dominates ({dominant_head_mass:.0%}) - effectively 1-head model, reduce to n_heads=2")
        elif dominant_head_mass > 0.5:
            recommendation.append(f"HEAD_{dominant_head} has {dominant_head_mass:.0%} - consider fewer heads")

        # Check Gini (inequality of head contributions)
        if avg_gini > 0.5:
            recommendation.append(f"High Gini ({avg_gini:.2f}) - attention concentrated in few heads")

        # Legacy checks
        if avg_similarity > 0.8:
            recommendation.append(f"High head similarity ({avg_similarity:.2f}) - heads learning redundant patterns")
        if avg_utilization < 0.5:
            effective = avg_utilization * n_heads
            recommendation.append(f"Low utilization ({avg_utilization:.1%}) - only ~{effective:.1f}/{n_heads} effective heads")
        if avg_entropy < 0.1:
            recommendation.append(f"Low entropy ({avg_entropy:.2f}) - attention too focused")
        if avg_entropy > 0.9:
            recommendation.append(f"High entropy ({avg_entropy:.2f}) - attention too diffuse")

        if not recommendation:
            recommendation.append(f"Head utilization healthy ({n_heads} heads, d_k={d_k})")

        # Get ASCII similarity matrix from first layer
        similarity_matrix_ascii = None
        if layer_diagnostics and 'similarity_matrix_ascii' in layer_diagnostics[0]:
            similarity_matrix_ascii = layer_diagnostics[0]['similarity_matrix_ascii']

        return {
            'enabled': True,
            'n_heads': n_heads,
            'd_k': d_k,
            'avg_entropy': avg_entropy,
            'avg_similarity': avg_similarity,
            'avg_utilization': avg_utilization,
            'avg_gini': avg_gini,
            'dominant_head': dominant_head,
            'dominant_head_mass': dominant_head_mass,
            'head_mass': head_mass,
            'layers': layer_diagnostics,
            'recommendation': '; '.join(recommendation),
            'similarity_matrix_ascii': similarity_matrix_ascii,
        }

    def log_batchnorm_stats(self):
        """Log statistics about all BatchNorm layers in the model."""
        if not self.config.use_batch_norm:
            logger.info("🔍 BatchNorm: Not using batch normalization")
            return
            
        logger.info(f"🔍 BatchNorm Debug - Model training mode: {self.training}")
        
        for layer_idx, layer in enumerate(self.layers):
            for module_idx, module in enumerate(layer):
                if isinstance(module, nn.BatchNorm1d):
                    bn = module
                    logger.info(f"🔍 BatchNorm Layer {layer_idx}.{module_idx}:")
                    logger.info(f"   Training mode: {bn.training}")
                    logger.info(f"   Num batches tracked: {bn.num_batches_tracked.item() if bn.num_batches_tracked is not None else 'N/A'}")
                    if bn.running_mean is not None:
                        logger.info(f"   Running mean: min={bn.running_mean.min().item():.4f}, max={bn.running_mean.max().item():.4f}, std={bn.running_mean.std().item():.4f}")
                    if bn.running_var is not None:
                        logger.info(f"   Running var: min={bn.running_var.min().item():.4f}, max={bn.running_var.max().item():.4f}, mean={bn.running_var.mean().item():.4f}")
                    if bn.weight is not None:
                        logger.info(f"   Gamma (weight): min={bn.weight.min().item():.4f}, max={bn.weight.max().item():.4f}")
                    if bn.bias is not None:
                        logger.info(f"   Beta (bias): min={bn.bias.min().item():.4f}, max={bn.bias.max().item():.4f}")

    def forward(self, x):
        if self.config.n_hidden_layers == 0:
            return self.single_layer(x)

        # CRITICAL: Ensure input is on the same device as module parameters
        # This fixes device mismatch errors where input is on CPU but module is on CUDA
        module_device = None
        try:
            module_device = next(self.parameters()).device
        except (StopIteration, AttributeError):
            pass
        
        # Move input to module device if there's a mismatch
        if module_device is not None and x.device != module_device:
            x = x.to(device=module_device)
        
        # x = self.batch_norm_in(x)
        x_input = x
        x = self.linear_in(x)

        for layer_idx, layer in enumerate(self.layers):
            x_before = x
            
            # Feedforward block
            if self.config.residual:
                x = x + layer(x)
            else:
                x = layer(x)
            
            # Attention block (if enabled)
            if self.use_attention and self.attention_layers[layer_idx] is not None:
                x = self.attention_layers[layer_idx](x)
            
            # Debug: Check if output changed (backwards compatible - check if attribute exists)
            # Only log during training mode to reduce eval noise
            # COMMENTED OUT: Too verbose, clutters logs
            # if getattr(self, 'debug_batchnorm', False) and self.config.use_batch_norm and self.training:
            #     x_diff = (x - x_before).abs().mean().item() if not self.config.residual else (x - x_before - layer(x_before)).abs().mean().item()
            #     logger.debug(f"🔍 Layer {layer_idx} output change: {x_diff:.6f}")


        x = self.linear_out(x)

        # Global residual: skip connection from input to output
        # Makes identity trivial to learn (mlp(x) just needs to output 0)
        # Only valid when d_in == d_out
        global_residual = getattr(self.config, 'global_residual', False)
        if global_residual and self.config.d_in == self.config.d_out:
            x = x + x_input

        if self.config.normalize:
            x_before_norm = x
            x = F.normalize(x, p=2, dim=-1)
            # Backwards compatible - check if attribute exists
            # Only log during training mode to reduce eval noise
            if getattr(self, 'debug_batchnorm', False) and self.training:
                norm_change = (x - x_before_norm).abs().mean().item()
                logger.debug(f"🔍 Output normalization change: {norm_change:.6f}")

        return x

    # def __init__(
    #     self, d_in, d_out, d_hidden, hidden_layers=0, dropout=0.1, normalize=True
    # ):
    #     super().__init__()

    #     if hidden_layers == 0:
    #         self.model = nn.Linear(d_in, d_out)
    #     else:
    #         layers_prefix = [
    #             nn.Linear(d_in, d_hidden),
    #         ]

    #         layers_middle = []
    #         # for _ in range(hidden_layers - 1):
    #         #     layers_middle.append(nn.LeakyReLU())
    #         #     layers_middle.append(nn.Linear(d_hidden, d_hidden))

    #         layers_suffix = [
    #             # nn.BatchNorm1d(d_hidden, affine=False),
    #             # nn.LeakyReLU(),
    #             # nn.Dropout(p=dropout),
    #             nn.Linear(d_hidden, d_out),
    #         ]

    #         layers = layers_prefix + layers_middle + layers_suffix

    #         self.model = nn.Sequential(*layers)

    #     self.linear = nn.Linear(d_in, d_out)
    #     # self.linear_in = nn.Linear(d_in, d_hidden, bias=True)
    #     # self.linear_out = nn.Linear(d_hidden, d_hidden, bias=True)

    #     self.linear_in = nn.Linear(d_in, d_hidden)
    #     self.linear_out = nn.Linear(d_hidden, d_out)

    #     self.normalize = normalize

    # def forward(self, input):
    #     # out = self.model(input)
    #     # if self.normalize:
    #     #     out = nn.functional.normalize(out, dim=1)

    #     # x = self.batch_norm_in(x)
    #     x = self.linear_in(input)

    #     # layers = self.layers

    #     # for layer in layers:
    #     #     if self.residual:
    #     #         x = x + layer(x)
    #     #     else:
    #     #         x = layer(x)

    #     x = self.linear_out(x)

    #     # x = self.linear(input)

    #     if self.normalize:
    #         x = F.normalize(x, p=2, dim=1)

    #     return x
    #     # return out
