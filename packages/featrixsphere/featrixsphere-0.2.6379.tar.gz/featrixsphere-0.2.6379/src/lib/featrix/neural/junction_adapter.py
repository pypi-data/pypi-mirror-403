#  -*- coding: utf-8 -*-
#
#  Copyright Featrix, Inc 2023-2025
#
#  Proprietary and Confidential.  Unauthorized use, copying or dissemination
#  of these materials is strictly prohibited.
#
"""
Junction Adapter: Impedance matching between encoder and predictor.

The encoder produces embeddings with potentially large magnitudes and gradients,
while the predictor may be initialized with small weights producing small gradients.
This creates gradient imbalance where encoder gradients overwhelm predictor gradients.

The JunctionAdapter normalizes the encoder output and applies a learnable gain,
acting as "impedance matching" between the two modules.

Key features:
- RMSNorm normalizes forward pass magnitudes
- Gradient scaling (grad_scale) attenuates backward gradients to encoder
- Detach-mix (detach_alpha) blends detached/attached paths for gradient control
- Low init_gain (0.3) prevents early encoder gradient explosion
"""
import torch
import torch.nn as nn


class _GradientScale(torch.autograd.Function):
    """Scale gradients during backward pass only."""
    @staticmethod
    def forward(ctx, x, scale):
        ctx.scale = scale
        return x

    @staticmethod
    def backward(ctx, grad_output):
        return grad_output * ctx.scale, None


def gradient_scale(x, scale):
    """Scale gradients flowing back through x by `scale` factor."""
    return _GradientScale.apply(x, scale)


class RMSNorm(nn.Module):
    """
    Root Mean Square Layer Normalization.

    Unlike LayerNorm, RMSNorm doesn't re-center (no mean subtraction).
    This preserves the distribution shape while only scaling magnitude.
    Often better for scale matching since it doesn't shift activations.
    """
    def __init__(self, d_model: int, eps: float = 1e-8):
        super().__init__()
        self.eps = eps
        self.weight = nn.Parameter(torch.ones(d_model))

    def forward(self, x):
        rms = x.pow(2).mean(dim=-1, keepdim=True).sqrt()
        x_normed = x / (rms + self.eps)
        return self.weight * x_normed


class JunctionAdapter(nn.Module):
    """
    Impedance matching layer between encoder and predictor.

    Args:
        d_model: Embedding dimension
        init_gain: Initial gain value (default 0.3 - low to prevent early gradient explosion)
        norm_type: 'layer_norm', 'rms_norm', or None (default 'rms_norm')
        grad_scale: Scale factor for gradients flowing back to encoder (default 0.1)
        detach_alpha: Blend factor for detach-mix: output = alpha*detached + (1-alpha)*attached
                      0.0 = fully attached (normal), 1.0 = fully detached (no encoder grads)
                      Default 0.0 (disabled, using grad_scale instead)
    """
    def __init__(self, d_model: int, init_gain: float = 0.3, norm_type: str = 'rms_norm',
                 grad_scale: float = 0.1, detach_alpha: float = 0.0):
        super().__init__()
        self.norm_type = norm_type
        self.grad_scale = grad_scale
        self.detach_alpha = detach_alpha

        if norm_type == 'layer_norm':
            self.norm = nn.LayerNorm(d_model)
        elif norm_type == 'rms_norm':
            self.norm = RMSNorm(d_model)
        else:
            self.norm = None

        self.gain = nn.Parameter(torch.tensor(init_gain))

    def forward(self, x):
        # Optional detach-mix: blend detached and attached paths
        if self.detach_alpha > 0.0:
            x = self.detach_alpha * x.detach() + (1.0 - self.detach_alpha) * x

        if self.norm is not None:
            x = self.norm(x)

        out = self.gain * x

        # Apply gradient scaling AFTER everything - this scales gradients flowing back to encoder
        # Must be last so it attenuates the amplified gradients from RMSNorm's backward pass
        if self.grad_scale != 1.0:
            out = gradient_scale(out, self.grad_scale)

        return out
