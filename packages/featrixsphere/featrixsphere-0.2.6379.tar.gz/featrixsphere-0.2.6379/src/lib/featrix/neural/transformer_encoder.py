import math
from dataclasses import dataclass
from typing import Optional, Dict
import logging

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.checkpoint import checkpoint

from featrix.neural.featrix_module_dict import FeatrixModuleDict
from featrix.neural.model_config import JointEncoderConfig
from featrix.neural.simple_mlp import SimpleMLP
from featrix.neural.relationship_extractor import RelationshipFeatureExtractor
from featrix.neural.gpu_utils import is_gpu_available, get_gpu_memory_allocated, get_gpu_memory_reserved

logger = logging.getLogger(__name__)

def _log_gpu_memory_transformer(context: str = ""):
    """Quick GPU memory logging for tracing memory usage in transformer_encoder."""
    try:
        if not is_gpu_available():
            return
        allocated = get_gpu_memory_allocated()
        reserved = get_gpu_memory_reserved()
        logger.info(f"📊 GPU [{context}]: Alloc={allocated:.2f}GB Reserved={reserved:.2f}GB")
    except Exception:
        pass


class AddCLSToken(nn.Module):
    def __init__(self, d_model):
        super().__init__()

        self.d_model = d_model

        # Initialize the [CLS] token as a learnable parameter
        self.cls_token = nn.Parameter(
            torch.randn(self.d_model) / math.sqrt(self.d_model)
        )

    def forward(self, x):
        # x has shape (B, S, F)

        # Replicate the [CLS] token for all sequences in the batch
        # self.cls_token has shape (F,)
        cls_tokens = self.cls_token.repeat(x.size(0), 1, 1)  # Shape: (B, 1, F)

        # Concatenate the [CLS] token with sequences
        x = torch.cat([cls_tokens, x], dim=1)  # Shape: (B, S+1, F)

        return x


class ColumnEncoding(nn.Module):
    def __init__(self, d_model, seq_len):
        super().__init__()

        #  we add an encoding for the cls token, which always gets prepended as the 0th element
        n_encodings = seq_len

        # Initialize a tensor for positional encodings and set it as a learnable parameter
        # NOTE: this assumes the input comes in the form (sequence, feature)
        self.pos_embedding = nn.Parameter(
            torch.randn(n_encodings, d_model) / math.sqrt(d_model)
        )

        # NOTE: this could be accomplished with an Embedding module, but that would get more
        # cumbersome. Going with a simple single parameter as above is much better.

    def forward(self, x):
        # assume x is in the format (batch, seq, feat)
        # the positional embedding_space gets broadcast across the batch dimension

        return x + self.pos_embedding


class GroupBiasedTransformerLayer(nn.Module):
    """
    Transformer encoder layer with additive attention bias for hybrid column groups.

    This allows columns in the same group to attend to each other more strongly,
    creating an explicit inductive bias for related columns.

    The bias is added to attention scores BEFORE softmax:
        attention_probs = softmax(Q @ K^T / sqrt(d_k) + group_bias)

    Where group_bias[i,j] = learned_bias[g] if columns i,j are in same group g, else 0.
    """

    def __init__(
        self,
        d_model: int,
        n_heads: int,
        dim_feedforward: int,
        dropout: float = 0.1,
        n_groups: int = 0,
        col_to_group: Optional[Dict[int, int]] = None,
        seq_len: int = 0,
    ):
        super().__init__()

        self.d_model = d_model
        self.n_heads = n_heads
        self.dropout = dropout
        self.n_groups = n_groups
        self.col_to_group = col_to_group or {}
        self.seq_len = seq_len  # Including CLS token

        # Standard transformer components
        self.self_attn = nn.MultiheadAttention(
            embed_dim=d_model,
            num_heads=n_heads,
            dropout=dropout,
            batch_first=True,
        )

        # Feedforward network
        self.linear1 = nn.Linear(d_model, dim_feedforward)
        self.linear2 = nn.Linear(dim_feedforward, d_model)

        # Layer norms
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)

        # Dropout
        self.dropout1 = nn.Dropout(dropout)
        self.dropout2 = nn.Dropout(dropout)
        self.dropout_ff = nn.Dropout(dropout)

        # Activation
        self.activation = nn.GELU()

        # ====================================================================
        # GROUP ATTENTION BIAS
        # ====================================================================
        # Learned bias per group - how much to boost intra-group attention
        # Initialized to small positive value to encourage group cohesion
        if n_groups > 0 and col_to_group:
            self.group_bias = nn.Parameter(torch.ones(n_groups) * 0.5)  # Start with mild boost

            # Pre-compute group membership matrix for efficiency
            # group_mask[i,j] = group_idx if same group, else -1
            # Note: seq_len includes CLS token at position 0
            self.register_buffer('_group_mask', self._build_group_mask(seq_len, col_to_group))
            logger.info(f"   GroupBiasedTransformerLayer: {n_groups} groups, seq_len={seq_len}")
        else:
            self.group_bias = None
            self.register_buffer('_group_mask', None)

    def _build_group_mask(self, seq_len: int, col_to_group: Dict[int, int]) -> torch.Tensor:
        """
        Build a [seq_len, seq_len] matrix where:
        - mask[i,j] = group_idx if columns i-1 and j-1 are in same group (offset by 1 for CLS)
        - mask[i,j] = -1 otherwise

        CLS token (position 0) is not in any group.
        """
        mask = torch.full((seq_len, seq_len), -1, dtype=torch.long)

        # col_to_group maps column index (0-based, no CLS) to group index
        # In the sequence, CLS is at 0, so column i is at position i+1
        for col_i, group_i in col_to_group.items():
            pos_i = col_i + 1  # Offset for CLS token
            if pos_i >= seq_len:
                continue
            for col_j, group_j in col_to_group.items():
                pos_j = col_j + 1
                if pos_j >= seq_len:
                    continue
                if group_i == group_j:
                    mask[pos_i, pos_j] = group_i

        return mask

    def _compute_attention_bias(self, batch_size: int, device: torch.device, dtype: torch.dtype) -> Optional[torch.Tensor]:
        """
        Compute the attention bias matrix from group memberships.

        Returns:
            Tensor of shape [batch_size * n_heads, seq_len, seq_len] or None
        """
        if self.group_bias is None or self._group_mask is None:
            return None

        # Build bias matrix: [seq_len, seq_len]
        # For each position pair, look up if they share a group and add the group's bias
        seq_len = self._group_mask.shape[0]
        bias_matrix = torch.zeros(seq_len, seq_len, device=device, dtype=dtype)

        for group_idx in range(self.n_groups):
            # Find all positions in this group
            group_positions = (self._group_mask == group_idx)  # [seq_len, seq_len] bool
            # Add the learned bias for this group
            bias_matrix = bias_matrix + group_positions.to(dtype) * self.group_bias[group_idx]

        # Expand for batch and heads: [1, seq_len, seq_len] -> broadcast to [B*H, seq_len, seq_len]
        # MultiheadAttention expects attn_mask of shape [L, S] or [N*num_heads, L, S]
        # We'll return [seq_len, seq_len] and let it broadcast
        return bias_matrix

    def forward(
        self,
        src: torch.Tensor,
        src_mask: Optional[torch.Tensor] = None,
        src_key_padding_mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """
        Forward pass with group-biased attention.

        Args:
            src: [batch_size, seq_len, d_model]
            src_mask: Optional attention mask
            src_key_padding_mask: Optional key padding mask

        Returns:
            [batch_size, seq_len, d_model]
        """
        # Compute group attention bias
        group_bias = self._compute_attention_bias(src.shape[0], src.device, src.dtype)

        # Combine with any existing mask
        if group_bias is not None:
            if src_mask is not None:
                # src_mask is typically additive (0 = attend, -inf = mask)
                # Our group_bias is additive (positive = boost attention)
                attn_mask = src_mask + group_bias
            else:
                attn_mask = group_bias
        else:
            attn_mask = src_mask

        # Self-attention with group bias
        src2, attn_weights = self.self_attn(
            src, src, src,
            attn_mask=attn_mask,
            key_padding_mask=src_key_padding_mask,
            need_weights=False,
        )
        src = src + self.dropout1(src2)
        src = self.norm1(src)

        # Feedforward
        src2 = self.linear2(self.dropout_ff(self.activation(self.linear1(src))))
        src = src + self.dropout2(src2)
        src = self.norm2(src)

        return src


class GroupBiasedTransformerEncoder(nn.Module):
    """
    Stack of GroupBiasedTransformerLayer modules.

    Drop-in replacement for nn.TransformerEncoder but with group attention bias.
    """

    def __init__(
        self,
        d_model: int,
        n_heads: int,
        n_layers: int,
        dim_feedforward: int,
        dropout: float = 0.1,
        n_groups: int = 0,
        col_to_group: Optional[Dict[int, int]] = None,
        seq_len: int = 0,
    ):
        super().__init__()

        self.n_layers = n_layers
        self.layers = nn.ModuleList([
            GroupBiasedTransformerLayer(
                d_model=d_model,
                n_heads=n_heads,
                dim_feedforward=dim_feedforward,
                dropout=dropout,
                n_groups=n_groups,
                col_to_group=col_to_group,
                seq_len=seq_len,
            )
            for _ in range(n_layers)
        ])

        # Share group bias across layers? Or let each layer learn its own?
        # Current: each layer has its own bias (more expressive)
        # Alternative: share via a single Parameter and pass to layers

        if n_groups > 0:
            logger.info(f"🔗 GroupBiasedTransformerEncoder: {n_layers} layers, {n_groups} groups")

    def forward(
        self,
        src: torch.Tensor,
        mask: Optional[torch.Tensor] = None,
        src_key_padding_mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """
        Forward pass through all layers.

        Args:
            src: [batch_size, seq_len, d_model]
            mask: Optional attention mask
            src_key_padding_mask: Optional key padding mask

        Returns:
            [batch_size, seq_len, d_model]
        """
        output = src
        for layer in self.layers:
            output = layer(output, src_mask=mask, src_key_padding_mask=src_key_padding_mask)
        return output


# def apply_network_to_tensor(data, network):
#     N, M, K = data.shape

#     # Reshape data to (N*M, K) for batch processing
#     data_reshaped = data.view(N * M, K)

#     # Apply network
#     output = network(data_reshaped)

#     # Reshape output back to (N, M, output_dim)
#     # Assuming output dimension is the same as input K for simplicity
#     output_dim = output.shape[-1]
#     output_reshaped = output.view(N, M, output_dim)

#     return output_reshaped


class JointEncoder(nn.Module):
    def __init__(self, d_embed, col_names_in_order, config: JointEncoderConfig, hybrid_groups=None, enable_gradient_checkpointing: bool = True, col_types: Optional[Dict[str, str]] = None):
        super().__init__()

        self.d_embed = d_embed
        self.config = config
        self.enable_gradient_checkpointing = enable_gradient_checkpointing
        self.col_types = col_types or {}  # Column types for temporal relationship ops

        # Once-per-epoch logging flags (initialized here to satisfy pylint)
        self._var_track_epoch = -1
        self._norm_track_epoch = -1

        self.col_names_in_order = col_names_in_order
        self.hybrid_groups = hybrid_groups or {}
        
        # Create in_converters, handling hybrid group names
        in_converters_dict = {}
        for col_name in col_names_in_order:
            # Check if this is a hybrid group name
            if col_name in self.hybrid_groups:
                # For hybrid groups, use the config from the first original column
                group_info = self.hybrid_groups[col_name]
                original_columns = group_info.get('columns', [])
                if original_columns:
                    # Use config from first column in the group
                    original_col_name = original_columns[0]
                    if original_col_name in config.in_converter_configs:
                        in_converters_dict[col_name] = SimpleMLP(config.in_converter_configs[original_col_name])
                    else:
                        raise KeyError(f"Hybrid group '{col_name}' references column '{original_col_name}' which is not in in_converter_configs. Available keys: {list(config.in_converter_configs.keys())}")
                else:
                    raise ValueError(f"Hybrid group '{col_name}' has no columns defined")
            else:
                # Regular column, use its config directly
                if col_name in config.in_converter_configs:
                    in_converters_dict[col_name] = SimpleMLP(config.in_converter_configs[col_name])
                else:
                    raise KeyError(f"Column '{col_name}' not found in in_converter_configs. Available keys: {list(config.in_converter_configs.keys())}")
        
        self.in_converters = FeatrixModuleDict(in_converters_dict)

        self.out_converter = SimpleMLP(config=config.out_converter_config)
        self.batch_norm_out = nn.BatchNorm1d(d_embed)

        # Dynamic Relationship Extractor (always enabled if relationship_features config exists)
        self.relationship_extractor = None
        # Use getattr for backward compatibility with old pickles that don't have relationship_features
        relationship_features = getattr(config, 'relationship_features', None)
        if relationship_features is not None:
            from featrix.neural.dynamic_relationship_extractor import DynamicRelationshipExtractor
            
            rel_config = relationship_features
            exploration_epochs = getattr(rel_config, 'exploration_epochs', 5)
            top_k_fraction = getattr(rel_config, 'top_k_fraction', 0.25)
            
            self.relationship_extractor = DynamicRelationshipExtractor(
                d_model=config.d_model,
                col_names_in_order=col_names_in_order,
                exploration_epochs=exploration_epochs,
                top_k_fraction=top_k_fraction,
                col_types=self.col_types,  # Pass column types for temporal ops
            )
            logger.info(
                f"🔗 JointEncoder: Dynamic relationship extractor enabled "
                f"(exploration_epochs={exploration_epochs}, "
                f"top_k_fraction={top_k_fraction}, "
                f"operations=6 per pair: *, +, -, /, both directions)"
            )

        # Trainable Positional Encoding
        # NOTE: Positional encoding needs to account for:
        # - Column tokens (positions 0 to n_cols-1) - ColumnEncoding receives input BEFORE CLS token
        # - CLS token (position n_cols) - added after ColumnEncoding
        # - Relationship tokens (positions n_cols+1 onwards, variable count)
        # ColumnEncoding is called BEFORE CLS token is added, so it only needs n_cols positions
        # Relationship tokens get positional encodings manually from the extended embedding
        col_seq_len = config.n_cols  # Columns only (CLS added later)
        
        # Calculate max sequence length for positional embedding
        # With POOLED RELATIONSHIP INJECTION, we no longer concatenate relationship tokens
        # to the sequence, so seq_len = 1 (CLS) + n_cols only
        # This is the key to scaling: attention is O(N²) not O((N + N²)²)
        max_seq_len = 1 + config.n_cols  # CLS + columns only
        
        if getattr(self, 'relationship_extractor', None):
            # Relationship tokens are now pooled and injected into CLS, not concatenated
            # Log the relationship token count for debugging purposes
            n_pairs = config.n_cols * (config.n_cols - 1) // 2
            # Query ops_per_pair from extractor (1 if fused, 9 if unfused)
            operations_per_pair = getattr(self.relationship_extractor, 'ops_per_pair', 1)
            n_rel_tokens = n_pairs * operations_per_pair
            fusion_mode = "FUSED" if operations_per_pair == 1 else "UNFUSED"
            logger.info(f"   Relationship tokens: {n_rel_tokens} ({fusion_mode}, pooled, not in sequence)")
            logger.info(f"   Sequence length: {max_seq_len} (CLS + {config.n_cols} cols) - SCALABLE")
        
        if config.use_col_encoding:
            # ColumnEncoding receives columns BEFORE CLS token, so use col_seq_len
            self.col_encoder = ColumnEncoding(self.config.d_model, col_seq_len)
            # Store max_seq_len for relationship token positional encoding
            self.max_seq_len = max_seq_len

        # simple module to add the cls token to create the joint encoding for the whole sequence
        self.add_cls_token = AddCLSToken(self.config.d_model)

        # HYBRID COLUMN SUPPORT: Setup hybrid relationships (hybrid_groups already stored above)
        self._setup_hybrid_relationships()

        # Transformer Encoder - use GroupBiasedTransformerEncoder if we have relationship groups
        relationship_groups = {
            name: info for name, info in self.hybrid_groups.items()
            if info.get('strategy') == 'relationship'
        }

        if relationship_groups and len(self.col_to_group) > 0:
            # Use custom transformer with group attention bias
            n_groups = len(relationship_groups)
            logger.info(f"🔗 Using GroupBiasedTransformerEncoder ({n_groups} groups, {len(self.col_to_group)} columns)")
            self.transformer_encoder = GroupBiasedTransformerEncoder(
                d_model=self.config.d_model,
                n_heads=self.config.n_heads,
                n_layers=self.config.n_layers,
                dim_feedforward=self.config.d_model * self.config.dim_feedforward_factor,
                dropout=self.config.dropout,
                n_groups=n_groups,
                col_to_group=self.col_to_group,
                seq_len=max_seq_len,  # CLS + columns
            )
            self._use_group_biased_transformer = True
        else:
            # Standard PyTorch transformer
            encoder_layer = nn.TransformerEncoderLayer(
                self.config.d_model,
                self.config.n_heads,
                dim_feedforward=self.config.d_model * self.config.dim_feedforward_factor,
                dropout=self.config.dropout,
                batch_first=True,  # Enable nested tensor optimization
            )
            self.transformer_encoder = nn.TransformerEncoder(
                encoder_layer, num_layers=self.config.n_layers
            )
            self._use_group_biased_transformer = False
        
        # Enable gradient checkpointing to save memory (trades compute for memory)
        # This reduces activation memory by ~N_layers times at ~30% compute cost
        # Implemented using torch.utils.checkpoint.checkpoint() wrapper in forward()
        if self.enable_gradient_checkpointing and self.config.n_layers > 1:
            logger.info(f"🔋 Enabling gradient checkpointing on {self.config.n_layers}-layer transformer (saves ~{self.config.n_layers}× activation memory)")
        
        # ============================================================================
        # TIER 3: LOCAL ATTENTION FOR RELATIONSHIP SELECTION
        # ============================================================================
        # Local attention allows each column to selectively attend over its K relationship
        # candidates (exploit + explore + NULL) instead of pooling all relationships into CLS.
        # This enables per-column relationship selection and better scaling.
        # ============================================================================
        if self.relationship_extractor is not None:
            # Local attention for Tier 3 relationship selection
            self.local_attention = nn.MultiheadAttention(
                embed_dim=self.config.d_model,
                num_heads=self.config.n_heads,  # Use same number of heads as main transformer
                dropout=self.config.dropout if hasattr(self.config, 'dropout') else 0.1,
                batch_first=True,
            )
            self.local_attn_dropout = nn.Dropout(self.config.dropout if hasattr(self.config, 'dropout') else 0.1)

            # ============================================================================
            # RELATIONSHIP-TO-COLUMN ALIGNMENT PROJECTION
            # ============================================================================
            # Problem: Relationship tokens (from ScalarScalarOps etc.) live in a different
            # semantic space than column encodings. Q·K cosine is ~0 or negative.
            # Solution: Learn a projection that aligns relationship tokens with column space.
            # This projection transforms R from "relationship feature space" to "column space"
            # so that attention Q·K similarity becomes meaningful.
            self.rel_to_col_projection = nn.Sequential(
                nn.Linear(self.config.d_model, self.config.d_model),
                nn.GELU(),
                nn.Linear(self.config.d_model, self.config.d_model),
                nn.LayerNorm(self.config.d_model),
            )
            # Initialize to be close to identity so we don't break existing models
            # The final linear layer should start close to identity
            with torch.no_grad():
                # First linear: random init is fine
                # Second linear: initialize close to identity
                nn.init.eye_(self.rel_to_col_projection[2].weight)
                nn.init.zeros_(self.rel_to_col_projection[2].bias)

            # Gate for relationship injection (allows model to damp relationships early)
            self.local_attn_gate = nn.Sequential(
                nn.Linear(self.config.d_model, self.config.d_model),
                nn.Sigmoid()
            )
            logger.info(f"🔗 Tier 3 local attention enabled (per-column relationship selection)")
            logger.info(f"🔗 Relationship-to-column alignment projection added")
        else:
            self.local_attention = None
            self.local_attn_dropout = None
            self.local_attn_gate = None

        # ============================================================================
        # LEARNED SHORT PROJECTION
        # ============================================================================
        # Instead of just slicing joint[:, 0:3], we learn a projection from d_model -> 3
        # This allows the network to learn which linear combination of dimensions
        # best separates the data in 3D space for visualization.
        # ============================================================================
        self.short_projection = nn.Sequential(
            nn.Linear(self.config.d_model, self.config.d_model // 4),
            nn.GELU(),
            nn.Linear(self.config.d_model // 4, 3),
        )
        logger.info(f"📐 Learned short projection: {self.config.d_model} -> {self.config.d_model // 4} -> 3")

        # Storage for attention weights (for diagnostics)
        self._attention_weights = None
        self._enable_attention_capture = False

        # ============================================================================
        # PER-COLUMN RELATIONSHIP SELECTIVITY TRACKING
        # ============================================================================
        # Track per-column attention entropy to see which columns use relationships
        # selectively vs. uniformly. Low entropy = selective, high entropy = diffuse.
        # Accumulate across batches, log at epoch end.
        # ============================================================================
        self._col_entropy_sum = None  # (N,) - sum of entropies per column
        self._col_entropy_count = 0   # Number of batches accumulated
        self._col_null_attn_sum = None  # (N,) - sum of NULL attention per column
        self._col_rel_change_sum = None  # (N,) - sum of relative embedding changes per column
    
    def update_mi_estimates(
        self,
        col_mi_estimates: dict,
        joint_mi_estimate: Optional[float] = None,
    ):
        """Update mutual information estimates in relationship extractor."""
        relationship_extractor = getattr(self, 'relationship_extractor', None)
        if relationship_extractor and hasattr(relationship_extractor, 'update_mi_estimates'):
            relationship_extractor.update_mi_estimates(
                col_mi_estimates, joint_mi_estimate
            )
    
    def update_column_losses(self, col_losses_dict: dict):
        """Update per-column marginal losses in relationship extractor (for importance calculation)."""
        relationship_extractor = getattr(self, 'relationship_extractor', None)
        if relationship_extractor and hasattr(relationship_extractor, 'update_column_losses'):
            relationship_extractor.update_column_losses(col_losses_dict)

    def init_for_uniform_hypersphere(self):
        """
        Initialize encoder weights to produce uniformly distributed outputs on the hypersphere.

        By default, PyTorch uses Kaiming/Xavier init which doesn't guarantee uniform distribution
        of outputs on the unit hypersphere. This can cause embeddings to start clustered,
        making the separation loss work harder.

        This method reinitializes key output layers to produce more uniform initial outputs:
        1. out_converter final layer: orthogonal init + normalize rows
        2. Column encodings: orthogonal basis if possible
        3. in_converters: orthogonal init to preserve input diversity

        Note: CLS token is NOT initialized here because we use mean of column outputs
        (not CLS) for the final joint representation (see forward() around line 1665).

        Call this AFTER model construction but BEFORE training begins.

        Controlled by use_hypersphere_init flag in sphere_config.py.
        """
        # Check flag - if False, skip hypersphere init entirely (use default PyTorch init)
        from featrix.neural.sphere_config import get_config
        if not get_config().use_hypersphere_init():
            logger.info("⏭️ Skipping hypersphere init (use_hypersphere_init=False, using default PyTorch init)")
            return

        logger.info("🎲 Initializing encoder for uniform hypersphere distribution...")

        d_model = self.config.d_model

        # 1. Initialize out_converter for spread outputs
        # SimpleMLP.layers is ModuleList of nn.Sequential, so use .modules() to find Linear
        if hasattr(self, 'out_converter'):
            n_linear = 0
            for module in self.out_converter.modules():
                if isinstance(module, nn.Linear):
                    nn.init.orthogonal_(module.weight, gain=3.0)
                    if module.bias is not None:
                        nn.init.normal_(module.bias, mean=0.0, std=0.5)
                    n_linear += 1
            logger.info(f"   ✓ out_converter: orthogonal(gain=3) + random bias on {n_linear} Linear layers")

        # 2. Initialize column position encodings to be more spread out
        # NOTE: The attribute is 'pos_embedding', not 'encoding' (see ColumnEncoding class)
        if hasattr(self, 'col_encoder') and hasattr(self.col_encoder, 'pos_embedding'):
            with torch.no_grad():
                n_cols = self.col_encoder.pos_embedding.shape[0]
                # Use orthogonal vectors if n_cols <= d_model, else random unit vectors
                if n_cols <= d_model:
                    # Create orthogonal basis vectors
                    ortho = torch.zeros(n_cols, d_model)
                    # Use QR decomposition of random matrix for orthogonal vectors
                    random_mat = torch.randn(d_model, n_cols)
                    q, _ = torch.linalg.qr(random_mat)
                    ortho = q.T[:n_cols]  # Take first n_cols orthogonal vectors
                    # Scale to match expected norm
                    ortho = ortho / math.sqrt(d_model)
                    self.col_encoder.pos_embedding.data.copy_(ortho)
                    logger.info(f"   ✓ Column encodings: {n_cols} orthogonal vectors")
                else:
                    # More columns than dimensions - use random unit vectors
                    random_vecs = torch.randn(n_cols, d_model)
                    random_vecs = random_vecs / random_vecs.norm(dim=1, keepdim=True)
                    random_vecs = random_vecs / math.sqrt(d_model)
                    self.col_encoder.pos_embedding.data.copy_(random_vecs)
                    logger.info(f"   ✓ Column encodings: {n_cols} random unit vectors")

        # 3. Initialize in_converters with higher gain to preserve input diversity
        n_converters = 0
        n_linear_total = 0
        for col_name, converter in self.in_converters.items():
            for module in converter.modules():
                if isinstance(module, nn.Linear):
                    nn.init.orthogonal_(module.weight, gain=2.0)
                    if module.bias is not None:
                        nn.init.normal_(module.bias, mean=0.0, std=0.3)
                    n_linear_total += 1
            n_converters += 1
        logger.info(f"   ✓ in_converters: {n_converters} converters, {n_linear_total} Linear layers (gain=2.0)")

        # 4. Initialize transformer encoder layers to preserve diversity
        # The attention and FFN layers can collapse embeddings if not initialized properly
        if hasattr(self, 'encoder') and hasattr(self.encoder, 'layers'):
            for i, layer in enumerate(self.encoder.layers):
                # Self-attention: Q, K, V projections and output projection
                if hasattr(layer, 'self_attn'):
                    attn = layer.self_attn
                    # Initialize Q, K, V with orthogonal to preserve directions
                    if hasattr(attn, 'in_proj_weight') and attn.in_proj_weight is not None:
                        # Combined QKV weight - init orthogonally
                        nn.init.orthogonal_(attn.in_proj_weight)
                    else:
                        # Separate Q, K, V weights
                        for proj_name in ['q_proj_weight', 'k_proj_weight', 'v_proj_weight']:
                            if hasattr(attn, proj_name):
                                proj = getattr(attn, proj_name)
                                if proj is not None:
                                    nn.init.orthogonal_(proj)
                    # Output projection
                    if hasattr(attn, 'out_proj') and hasattr(attn.out_proj, 'weight'):
                        nn.init.orthogonal_(attn.out_proj.weight)
                        if attn.out_proj.bias is not None:
                            nn.init.zeros_(attn.out_proj.bias)

                # FFN layers - keep them small to not dominate
                if hasattr(layer, 'linear1'):
                    nn.init.orthogonal_(layer.linear1.weight, gain=0.5)
                    if layer.linear1.bias is not None:
                        nn.init.zeros_(layer.linear1.bias)
                if hasattr(layer, 'linear2'):
                    nn.init.orthogonal_(layer.linear2.weight, gain=0.5)
                    if layer.linear2.bias is not None:
                        nn.init.zeros_(layer.linear2.bias)
            logger.info(f"   ✓ Transformer layers: orthogonal init for attention and FFN")

        logger.info("🎲 Uniform hypersphere initialization complete")

    def get_per_column_selectivity_stats(self) -> Optional[Dict]:
        """
        Get accumulated per-column relationship selectivity statistics.

        Returns dict with:
            - col_entropy_mean: (N,) mean entropy per column (low=selective, high=diffuse)
            - col_null_attn_mean: (N,) mean NULL attention per column (high=ignoring relationships)
            - col_rel_change_mean: (N,) mean relative embedding change per column
            - n_batches: number of batches accumulated
            - col_names: column names in order

        Returns None if no stats accumulated yet.
        """
        if self._col_entropy_sum is None or self._col_entropy_count == 0:
            return None

        return {
            'col_entropy_mean': self._col_entropy_sum / self._col_entropy_count,
            'col_null_attn_mean': self._col_null_attn_sum / self._col_entropy_count,
            'col_rel_change_mean': self._col_rel_change_sum / self._col_entropy_count,
            'n_batches': self._col_entropy_count,
            'col_names': getattr(self, 'col_names_in_order', None),
        }

    def reset_per_column_selectivity_stats(self):
        """Reset per-column selectivity accumulators for a new epoch."""
        self._col_entropy_sum = None
        self._col_null_attn_sum = None
        self._col_rel_change_sum = None
        self._col_entropy_count = 0

    def log_per_column_selectivity(self, epoch: int = 0):
        """
        Log per-column relationship selectivity at epoch end.

        Shows which columns are using relationships selectively vs. uniformly.
        Low entropy = selective attention (peaked), high entropy = diffuse (uniform).
        """
        stats = self.get_per_column_selectivity_stats()
        if stats is None:
            logger.info(f"📊 [epoch={epoch}] No per-column selectivity stats accumulated yet")
            return

        col_names = stats['col_names'] or [f"col_{i}" for i in range(len(stats['col_entropy_mean']))]
        entropy = stats['col_entropy_mean']
        null_attn = stats['col_null_attn_mean']
        rel_change = stats['col_rel_change_mean']
        n_batches = stats['n_batches']

        # Calculate max entropy for normalization (uniform over K slots)
        K = 17  # Default, could compute from data
        max_entropy = math.log(K)

        logger.info(f"")
        logger.info(f"📊 PER-COLUMN RELATIONSHIP SELECTIVITY [epoch={epoch}, {n_batches} batches]:")
        logger.info(f"   Entropy: low=selective (peaked attention), high=diffuse (uniform)")
        logger.info(f"   NULL%: high means column ignores relationships, prefers NULL baseline")
        logger.info(f"   Δ%: relative embedding change from relationships")
        logger.info(f"")
        logger.info(f"   {'Column':<30} {'Entropy':>8} {'NormEnt':>8} {'NULL%':>8} {'Δ%':>8} {'Status'}")
        logger.info(f"   {'-'*30} {'-'*8} {'-'*8} {'-'*8} {'-'*8} {'-'*10}")

        # Sort by entropy ascending (most selective first)
        sorted_indices = entropy.argsort().tolist()

        selective_count = 0
        diffuse_count = 0
        null_dominated_count = 0

        for idx in sorted_indices:
            col_name = col_names[idx] if idx < len(col_names) else f"col_{idx}"
            col_name_display = col_name[:30] if len(col_name) <= 30 else col_name[:27] + "..."

            ent = entropy[idx].item()
            norm_ent = ent / max_entropy if max_entropy > 0 else 0
            null_pct = null_attn[idx].item() * 100
            rel_pct = rel_change[idx].item() * 100

            # Categorize
            if norm_ent < 0.5:
                status = "🎯 selective"
                selective_count += 1
            elif norm_ent > 0.9:
                status = "🌫️ diffuse"
                diffuse_count += 1
            else:
                status = "📊 moderate"

            if null_pct > 80:
                status = "⚪ NULL-dom"
                null_dominated_count += 1

            logger.info(f"   {col_name_display:<30} {ent:>8.3f} {norm_ent:>8.2f} {null_pct:>7.1f}% {rel_pct:>7.2f}% {status}")

        # Summary
        n_cols = len(entropy)
        logger.info(f"")
        logger.info(f"   SUMMARY: {selective_count}/{n_cols} selective, {diffuse_count}/{n_cols} diffuse, {null_dominated_count}/{n_cols} NULL-dominated")

        # Reset for next epoch
        self.reset_per_column_selectivity_stats()

    def _setup_hybrid_relationships(self):
        """
        Setup hybrid relationship embeddings and metadata.
        
        For RELATIONSHIP strategy groups, we add learned group embeddings
        that get added to related columns to help the transformer learn their relationships.
        """
        # Filter for RELATIONSHIP strategy groups only
        relationship_groups = {
            name: info for name, info in self.hybrid_groups.items()
            if info.get('strategy') == 'relationship'
        }
        
        if not relationship_groups:
            self.group_embeddings = None
            self.col_to_group = {}
            logger.debug("No RELATIONSHIP hybrid groups detected")
            return
        
        # Create learned group embeddings
        n_groups = len(relationship_groups)
        self.group_embeddings = nn.Parameter(
            torch.randn(n_groups, self.config.d_model) / math.sqrt(self.config.d_model)
        )
        
        # Create mapping from column index to group index
        self.col_to_group = {}
        for group_idx, (group_name, group_info) in enumerate(relationship_groups.items()):
            for col_name in group_info['columns']:
                if col_name in self.col_names_in_order:
                    col_idx = self.col_names_in_order.index(col_name)
                    self.col_to_group[col_idx] = group_idx
        
        logger.info(f"🔗 JointEncoder hybrid relationships: {n_groups} groups covering {len(self.col_to_group)} columns")
        for group_name, group_info in relationship_groups.items():
            logger.info(f"   {group_name}: {group_info['type']} - {group_info['columns']}")
    
    def enable_attention_capture(self):
        """Enable capturing attention weights for diagnostic analysis."""
        self._enable_attention_capture = True
    
    def disable_attention_capture(self):
        """Disable capturing attention weights (default, saves memory)."""
        self._enable_attention_capture = False
    
    def get_attention_weights(self):
        """Return captured attention weights. Returns None if capture is disabled."""
        return self._attention_weights

    def __getstate__(self):
        """
        Custom pickle state - clear temporary tensors that may be part of autograd graph.

        Tensors stored during forward pass (like _tier3_C, _tier3_R) are part of the
        computation graph and cannot be deepcopied. Clear them before pickling.
        """
        state = self.__dict__.copy()

        # Clear Tier 3 cached tensors (stored during training for gradient tracking)
        # These are computation graph tensors that fail deepcopy
        state['_tier3_C'] = None
        state['_tier3_R'] = None

        # Clear attention weights cache
        state['_attention_weights'] = None

        # Clear per-column statistics accumulators (will be recomputed)
        state['_col_entropy_sum'] = None
        state['_col_null_attn_sum'] = None
        state['_col_rel_change_sum'] = None
        state['_col_entropy_count'] = 0

        return state

    def __setstate__(self, state):
        """Restore state with backward compatibility for missing attributes."""
        self.__dict__.update(state)

        # Backward compatibility: add missing attributes from newer versions
        if not hasattr(self, 'enable_gradient_checkpointing'):
            self.enable_gradient_checkpointing = False  # Safe default for old checkpoints
        if not hasattr(self, '_attention_weights'):
            self._attention_weights = None
        if not hasattr(self, '_enable_attention_capture'):
            self._enable_attention_capture = False
        if not hasattr(self, 'local_attention'):
            self.local_attention = None
        if not hasattr(self, 'local_attn_dropout'):
            self.local_attn_dropout = None
        if not hasattr(self, 'local_attn_gate'):
            self.local_attn_gate = None
        if not hasattr(self, 'rel_to_col_projection'):
            self.rel_to_col_projection = None  # Old checkpoints don't have alignment projection
        if not hasattr(self, 'relationship_extractor'):
            self.relationship_extractor = None
        if not hasattr(self, 'hybrid_groups'):
            self.hybrid_groups = {}
        if not hasattr(self, 'group_embeddings'):
            self.group_embeddings = None
        if not hasattr(self, 'col_to_group'):
            self.col_to_group = {}
        if not hasattr(self, 'max_seq_len'):
            # Estimate from config if available
            n_cols = len(self.col_names_in_order) if hasattr(self, 'col_names_in_order') else 0
            self.max_seq_len = 1 + n_cols  # CLS + columns
        if not hasattr(self, 'col_types'):
            self.col_types = {}  # Old checkpoints don't have col_types
        # Backward compatibility for short_projection (added for better 3D embedding separation)
        # Old models will fall back to slicing joint[:, 0:3] in forward()
        if not hasattr(self, 'short_projection'):
            self.short_projection = None
        # Backward compatibility for group-biased transformer
        if not hasattr(self, '_use_group_biased_transformer'):
            self._use_group_biased_transformer = False

    def forward(
        self,
        x,
        mask: Optional[torch.Tensor] = None,
        raw_timestamp_features: Optional[Dict[int, torch.Tensor]] = None,
        strategy_encodings: Optional[Dict[int, torch.Tensor]] = None,
        strategy_masks: Optional[Dict[int, torch.Tensor]] = None,
    ):
        # NOTE: we're using a typical transformer encoder here, where all columns get their
        # own encoding. Then we throw away all encodings except the one for the [CLS] token.
        # A more efficient implementation would apply attention directly to inputs and produce
        # only one encoding.

        # FIXME: should the converter be the same for all variables, or should we use different converters for
        # different input variables?
        # ANSWER: using one encoder is fine, at least on smaller datasets.
        # On larger datasets we may want to revisit.

        # x: (batch_size, n_cols, d_model) - column encodings
        # mask: (batch_size, n_cols) - TokenStatus mask (optional)
        # raw_timestamp_features: {col_idx: (batch, 12)} - raw timestamp features for temporal ops
        
        # DEBUG: MPS INT_MAX - Track forward calls
        _debug_count = getattr(self, '_debug_forward_count', 0)
        self._debug_forward_count = _debug_count + 1
        _should_debug = _debug_count < 5  # Only first 5 calls
        
        if _should_debug:
            _log_gpu_memory_transformer(f"JointEncoder.forward #{_debug_count} START")
            logger.info(f"[DEBUG] JointEncoder.forward() #{_debug_count}")
            logger.info(f"[DEBUG]   Input x shape: {x.shape}, numel: {x.numel()}")

        col_x = []
        for i, col_name in enumerate(self.col_names_in_order):
            converter = self.in_converters[col_name]
            col_x.append(converter(x[:, i, :]))

        x = torch.stack(col_x, dim=1)  # (batch_size, n_cols, d_model)

        # Compute relationship features BEFORE positional encoding
        relationship_tokens = []
        relationship_extractor = getattr(self, 'relationship_extractor', None)
        if relationship_extractor is not None:
            # Check if we should evaluate NULL baseline this step
            # Only evaluate on first mask call (when flag is False)
            is_first_mask = not getattr(relationship_extractor, '_null_evaluation_pending', False)
            should_eval_func = getattr(relationship_extractor, 'should_evaluate_null_baseline', None)
            if should_eval_func:
                use_null_baseline = should_eval_func(is_first_mask)
            else:
                use_null_baseline = False

            # DEBUG: Log NULL baseline state (only once per step, on first mask)
            step = getattr(relationship_extractor, '_step_counter', 0)
            pending = getattr(relationship_extractor, '_null_evaluation_pending', False)
            if is_first_mask and (step < 10 or step % 500 == 0 or use_null_baseline):
                logger.info(f"[NULL_FLOW] step={step} is_first_mask={is_first_mask} "
                           f"use_null_baseline={use_null_baseline} pending_after={pending}")

            if use_null_baseline:
                # Run NULL-only forward for baseline evaluation
                relationship_tokens = relationship_extractor.forward(
                    x, mask, relationship_mode="null_only", raw_timestamp_features=raw_timestamp_features,
                    strategy_encodings=strategy_encodings, strategy_masks=strategy_masks
                )
                # Flag is already set by should_evaluate_null_baseline()
                # Track that this mask used NULL-only mode
                if not hasattr(relationship_extractor, '_null_batch_mask_modes'):
                    relationship_extractor._null_batch_mask_modes = []
                relationship_extractor._null_batch_mask_modes.append(True)
            else:
                relationship_tokens = relationship_extractor.forward(
                    x, mask, raw_timestamp_features=raw_timestamp_features,
                    strategy_encodings=strategy_encodings, strategy_masks=strategy_masks
                )
                # Track that this mask used normal mode
                if not hasattr(relationship_extractor, '_null_batch_mask_modes'):
                    relationship_extractor._null_batch_mask_modes = []
                relationship_extractor._null_batch_mask_modes.append(False)
            # relationship_tokens: List of (batch_size, d_model) tensors
            if _should_debug:
                logger.info(f"[DEBUG]   Relationship tokens: {len(relationship_tokens)} tokens")

        # Add column encodings first, then cls token
        # this means the cls token does not get a positional encoding, but
        # that's OK because only one token gets placed in that position anyway.
        # This simplifies things because this way the positional encoder does
        # not need to worry about adding a positional encoding for the cls token.
        if self.config.use_col_encoding:
            x = self.col_encoder(x)

        # HYBRID COLUMN SUPPORT: Add group embeddings for RELATIONSHIP strategy
        # Backwards compatibility: older models don't have group_embeddings
        if hasattr(self, 'group_embeddings') and self.group_embeddings is not None and len(getattr(self, 'col_to_group', {})) > 0:
            # Track for logging
            _hybrid_batch_count = getattr(self, '_hybrid_group_batch_count', 0)
            self._hybrid_group_batch_count = _hybrid_batch_count + 1
            _should_log_hybrid = (_hybrid_batch_count % 200 == 0)

            if _should_log_hybrid:
                with torch.no_grad():
                    # Snapshot before adding group embeddings
                    x_before = x.clone()

            for col_idx, group_idx in self.col_to_group.items():
                # Add group embedding to this column's encoding
                # This helps the transformer learn that these columns are related
                x[:, col_idx, :] = x[:, col_idx, :] + self.group_embeddings[group_idx]

            with torch.no_grad():
                # Compute impact of group embeddings
                n_groups = self.group_embeddings.shape[0]
                group_emb_norms = self.group_embeddings.norm(dim=-1)  # (n_groups,)

                # For columns in groups, measure the change
                affected_cols = list(self.col_to_group.keys())
                if affected_cols:
                    delta = x[:, affected_cols, :] - x_before[:, affected_cols, :]
                    delta_norm = delta.norm(dim=-1).mean().item()  # Average change magnitude

                    # Original column embedding magnitude (for relative comparison)
                    orig_norm = x_before[:, affected_cols, :].norm(dim=-1).mean().item()
                    relative_change = delta_norm / (orig_norm + 1e-6)

                    # Group embedding stats
                    group_emb_mean = group_emb_norms.mean().item()
                    group_emb_std = group_emb_norms.std().item() if n_groups > 1 else 0.0
                    group_emb_max = group_emb_norms.max().item()
                    group_emb_min = group_emb_norms.min().item()

                    # Cosine similarity between group embeddings (are they differentiated?)
                    if n_groups > 1:
                        cos_sims = []
                        for i in range(n_groups):
                            for j in range(i + 1, n_groups):
                                cos = F.cosine_similarity(
                                    self.group_embeddings[i].unsqueeze(0),
                                    self.group_embeddings[j].unsqueeze(0)
                                ).item()
                                cos_sims.append(cos)
                        inter_group_cos = sum(cos_sims) / len(cos_sims)
                    else:
                        inter_group_cos = 0.0

                    # ============================================================
                    # HEALTH CHECKS - warn/error when things go off the rails
                    # ============================================================
                    has_problems = False

                    # Check 1: Group embeddings exploded
                    if group_emb_max > 50.0:
                        logger.error(f"🚨 GROUP EMBEDDINGS EXPLODED: max_norm={group_emb_max:.2f} (>50)")
                        logger.error(f"   This will dominate column encodings and destabilize training")
                        has_problems = True

                    # Check 2: Group embeddings collapsed to near-zero
                    if group_emb_mean < 0.001 and _hybrid_batch_count > 100:
                        logger.warning(f"⚠️  GROUP EMBEDDINGS COLLAPSED: mean_norm={group_emb_mean:.6f} (~0)")
                        logger.warning(f"   Group embeddings are not contributing - may have been regularized away")
                        has_problems = True

                    # Check 3: Groups became identical (high cosine similarity)
                    if n_groups > 1 and inter_group_cos > 0.95:
                        logger.warning(f"⚠️  GROUP EMBEDDINGS COLLAPSED TO SAME DIRECTION: cos={inter_group_cos:.3f}")
                        logger.warning(f"   All groups point the same way - no differentiation between groups")
                        has_problems = True

                    # Check 4: NaN or Inf in embeddings
                    if torch.isnan(self.group_embeddings).any() or torch.isinf(self.group_embeddings).any():
                        logger.error(f"🚨 GROUP EMBEDDINGS HAVE NaN/Inf!")
                        has_problems = True

                    # Check 5: Relative change is tiny (embeddings not affecting anything)
                    if relative_change < 0.001 and _hybrid_batch_count > 100:
                        logger.warning(f"⚠️  GROUP EMBEDDINGS NOT AFFECTING COLUMNS: relative_change={relative_change*100:.4f}%")
                        logger.warning(f"   Column encodings are much larger than group embeddings")
                        has_problems = True

                    # Check 6: Relative change is huge (embeddings dominating)
                    if relative_change > 0.5:
                        logger.warning(f"⚠️  GROUP EMBEDDINGS DOMINATING: relative_change={relative_change*100:.1f}%")
                        logger.warning(f"   Group embeddings are >50% of column encoding magnitude")
                        has_problems = True

                    # Regular logging (every 200 batches, or immediately if problems)
                    if _should_log_hybrid or has_problems:
                        logger.info(f"🔗 HYBRID GROUP EMBEDDINGS [batch {_hybrid_batch_count}]:")
                        logger.info(f"   Groups: {n_groups}, Columns affected: {len(affected_cols)}/{x.shape[1]}")
                        logger.info(f"   Group embedding norms: mean={group_emb_mean:.4f} ± {group_emb_std:.4f}, range=[{group_emb_min:.4f}, {group_emb_max:.4f}]")
                        logger.info(f"   Inter-group cosine: {inter_group_cos:.4f} (lower=more differentiated)")
                        logger.info(f"   Column change: |Δ|={delta_norm:.4f}, relative={relative_change*100:.2f}%")

                        # Per-group breakdown
                        for gidx in range(n_groups):
                            cols_in_group = [c for c, g in self.col_to_group.items() if g == gidx]
                            col_names = [self.col_names_in_order[c] if c < len(self.col_names_in_order) else f"col_{c}"
                                        for c in cols_in_group]
                            logger.info(f"   Group {gidx}: norm={group_emb_norms[gidx].item():.4f}, cols={col_names}")

                        if not has_problems:
                            logger.info(f"   Status: ✅ healthy")

        # ============================================================================
        # TIER 3: LOCAL ATTENTION OVER RELATIONSHIP CANDIDATES
        # ============================================================================
        # Instead of pooling all relationships into CLS, each column selectively
        # attends over its K relationship candidates (exploit + explore + NULL).
        # This allows the model to learn which relationships matter per column.
        # ============================================================================
        
        # Extract shapes BEFORE adding CLS token (needed for Tier 3)
        B = x.shape[0]  # batch_size
        N = x.shape[1]  # n_cols (before CLS)
        d = x.shape[2]  # d_model
        C = x  # (B, N, d) - column encodings before CLS
        
        # Apply Tier 3 local attention if relationships are available
        if relationship_tokens and relationship_extractor is not None and self.local_attention is not None:
            # Get active directed pairs from extractor (stored during forward)
            active_directed_pairs = getattr(relationship_extractor, '_last_step_active_pairs', None)
            
            # Ensure active_directed_pairs is iterable (pylint type check)
            if active_directed_pairs is not None and len(active_directed_pairs) > 0:
                # DETERMINISM FIX: Sort pairs consistently to avoid set iteration order issues
                # Sets have undefined iteration order (based on hash), so we must sort
                active_directed_pairs = sorted(active_directed_pairs)
                # ========================================================================
                # STEP 1: Build IDX [N, K_total] - candidate indices per column
                # ========================================================================
                # Get K_exploit and K_explore from extractor
                log2_N = np.log2(max(2, N))
                E = max(1, min(32, int(np.ceil(log2_N))))
                K_exploit = E
                K_explore = E
                K_total = K_exploit + K_explore + 1  # +1 for NULL slot

                # Build IDX: [N, K_total] with NULL at slot 0
                IDX = torch.full((N, K_total), N, dtype=torch.long, device=x.device)  # N = NULL marker

                # VECTORIZED: Build IDX from active_directed_pairs
                # Convert pairs to tensor: (n_pairs, 2) where col 0 = src, col 1 = tgt
                pairs_tensor = torch.tensor(active_directed_pairs, dtype=torch.long, device=x.device)
                src_all = pairs_tensor[:, 0]  # (n_pairs,)
                tgt_all = pairs_tensor[:, 1]  # (n_pairs,)

                # Count edges per target column (vectorized)
                tgt_counts = torch.bincount(tgt_all, minlength=N)  # (N,)

                # For each target, we need to assign sources to slots 1:K_total
                # DETERMINISM FIX: Use stable sort to ensure consistent ordering when
                # multiple edges have the same target. Stable sort preserves the input
                # order for equal elements, which is now deterministic due to sorted() above.
                # Sort by (tgt, src) to get fully deterministic slot assignment
                sort_keys = tgt_all * N + src_all  # Composite key: tgt * N + src
                sort_idx = torch.argsort(sort_keys, stable=True)
                src_sorted = src_all[sort_idx]  # Sources sorted by (tgt, src)
                tgt_sorted = tgt_all[sort_idx]  # Targets sorted (for offset computation)

                # Compute within-target slot indices (0, 1, 2, ... for each target)
                # This gives us which slot each edge should go into
                cumsum = torch.cumsum(tgt_counts, dim=0)  # Cumulative count
                offsets = torch.zeros(N + 1, dtype=torch.long, device=x.device)
                offsets[1:] = cumsum  # offsets[tgt] = start index for target tgt

                # For each edge, compute its slot within its target group
                edge_positions = torch.arange(len(sort_idx), device=x.device)
                slot_within_tgt = edge_positions - offsets[tgt_sorted]  # 0-indexed slot for each edge

                # Only keep edges where slot < K_total - 1 (we have K_total-1 slots after NULL)
                valid_mask = slot_within_tgt < (K_total - 1)
                valid_tgt = tgt_sorted[valid_mask]
                valid_src = src_sorted[valid_mask]
                valid_slot = slot_within_tgt[valid_mask] + 1  # +1 because slot 0 is NULL

                # Scatter sources into IDX
                IDX[valid_tgt, valid_slot] = valid_src
                
                # ========================================================================
                # STEP 2: Build R [B, N, K_total, d] - relationship embeddings
                # ========================================================================
                # VECTORIZED: Stack tokens and use advanced indexing

                # pairs_to_compute MUST exist - no fallback, crash if missing
                pairs_to_compute = relationship_extractor._last_pairs_to_compute
                pairs_to_compute = sorted(pairs_to_compute)  # Sort for consistent indexing

                # Stack all relationship tokens: (n_tokens, B, d)
                # relationship_tokens is a list of (B, d) tensors
                rel_stack = torch.stack(relationship_tokens, dim=0)  # (n_tokens, B, d)

                # NaN ASSERTION: Check relationship tokens before using them
                assert not torch.isnan(rel_stack).any(), "NaN in relationship tokens! Check DynamicRelationshipExtractor."
                assert not torch.isinf(rel_stack).any(), "Inf in relationship tokens! Check DynamicRelationshipExtractor."

                # Build pair-to-token mapping as tensors for vectorized lookup
                # pairs_to_compute contains undirected pairs (i, j) where i < j
                use_fusion = relationship_extractor.use_fusion
                tokens_per_pair = 1 if use_fusion else 9

                # VECTORIZED: Create lookup tensor pair_lookup[i, j] = token_idx
                pair_lookup = torch.full((N, N), -1, dtype=torch.long, device=x.device)
                if len(pairs_to_compute) > 0:
                    pairs_tensor_lookup = torch.tensor(pairs_to_compute, dtype=torch.long, device=x.device)
                    i_indices = pairs_tensor_lookup[:, 0]
                    j_indices = pairs_tensor_lookup[:, 1]
                    token_indices = torch.arange(len(pairs_to_compute), device=x.device) * tokens_per_pair
                    # Set both (i,j) and (j,i) - symmetric
                    pair_lookup[i_indices, j_indices] = token_indices
                    pair_lookup[j_indices, i_indices] = token_indices

                # Get (src, tgt) pairs from IDX for slots 1:K_total
                # IDX shape: (N, K_total), IDX[:, 1:] are the relationship slots
                IDX_rel = IDX[:, 1:]  # (N, K_total-1) - relationship slots only

                # Create target indices tensor: (N, K_total-1)
                tgt_indices = torch.arange(N, device=x.device).unsqueeze(1).expand(-1, K_total - 1)

                # Flatten for lookup
                src_flat = IDX_rel.flatten()  # (N * (K_total-1),)
                tgt_flat = tgt_indices.flatten()  # (N * (K_total-1),)

                # Mask out NULL entries (where src == N)
                valid_mask = src_flat < N

                # Look up token indices (only for valid entries)
                # Clamp src to valid range for indexing, we'll mask out invalids anyway
                src_clamped = src_flat.clamp(0, N - 1)
                token_indices_flat = pair_lookup[src_clamped, tgt_flat]  # (N * (K_total-1),)

                # Combined mask: valid source AND has a token mapping
                combined_mask = valid_mask & (token_indices_flat >= 0)

                # Build R tensor: (B, N, K_total, d)
                R = torch.zeros(B, N, K_total, d, device=x.device, dtype=x.dtype)

                # Get the valid indices
                valid_indices = combined_mask.nonzero(as_tuple=True)[0]

                if len(valid_indices) > 0:
                    # Extract valid (tgt, slot, token_idx)
                    valid_tgt = tgt_flat[valid_indices]
                    valid_slot = (valid_indices % (K_total - 1)) + 1  # +1 for NULL slot offset
                    valid_token_idx = token_indices_flat[valid_indices]

                    # Gather tokens: rel_stack is (n_tokens, B, d)
                    # gathered_tokens shape: (n_valid, B, d)
                    gathered_tokens = rel_stack[valid_token_idx]

                    # VECTORIZED scatter into R using advanced indexing
                    # R shape: (B, N, K_total, d), gathered shape: (n_valid, B, d)
                    # Transpose gathered to (B, n_valid, d) for proper broadcasting
                    gathered_transposed = gathered_tokens.transpose(0, 1).to(dtype=x.dtype)  # (B, n_valid, d)

                    # Use deterministic index_put_ instead of scatter_
                    # scatter_ is non-deterministic on CUDA even with unique indices
                    # index_put_ with accumulate=False is deterministic when indices are unique

                    # R shape: (B, N, K_total, d), gathered_transposed shape: (B, n_valid, d)
                    # We need to assign: R[b, valid_tgt[i], valid_slot[i], :] = gathered_transposed[b, i, :]
                    # for all b in [0, B) and all i in [0, n_valid)

                    # Create batch indices: [0,0,...,0, 1,1,...,1, ..., B-1,B-1,...,B-1]
                    n_valid = len(valid_tgt)
                    batch_idx = torch.arange(B, device=x.device).unsqueeze(1).expand(B, n_valid).reshape(-1)
                    # Expand valid_tgt and valid_slot for all batches
                    tgt_idx = valid_tgt.unsqueeze(0).expand(B, n_valid).reshape(-1)
                    slot_idx = valid_slot.unsqueeze(0).expand(B, n_valid).reshape(-1)
                    # Flatten gathered_transposed: (B, n_valid, d) -> (B*n_valid, d)
                    values_flat = gathered_transposed.reshape(B * n_valid, d)

                    # Use non-in-place index_put (not index_put_) to maintain gradient flow
                    # index_put_ on a tensor without requires_grad breaks the gradient chain
                    R = R.index_put((batch_idx, tgt_idx, slot_idx), values_flat, accumulate=False)

                # NULL candidate at slot 0: use learned null_relationship_base
                null_base = relationship_extractor.null_relationship_base
                if null_base.dim() == 1:
                    null_base = null_base.unsqueeze(0).unsqueeze(0)  # [1, 1, d]
                # Use non-in-place index assignment for gradient flow
                null_expanded = null_base.expand(B, N, -1)  # [B, N, d]
                # Create index tensors for slot 0
                b_idx = torch.arange(B, device=x.device).view(B, 1).expand(B, N).reshape(-1)
                n_idx = torch.arange(N, device=x.device).view(1, N).expand(B, N).reshape(-1)
                slot_zero = torch.zeros(B * N, dtype=torch.long, device=x.device)
                R = R.index_put((b_idx, n_idx, slot_zero), null_expanded.reshape(B * N, d), accumulate=False)

                # ========================================================================
                # STEP 3: Apply Local Attention
                # ========================================================================
                # Query: column encodings C = x (B, N, d)
                # Keys/Values: relationship embeddings R = [B, N, K_total, d]
                # Each column attends over its K_total relationship candidates

                K = K_total

                # ========================================================================
                # APPLY RELATIONSHIP-TO-COLUMN ALIGNMENT PROJECTION
                # ========================================================================
                # Transform relationship tokens from "relationship feature space" to
                # "column embedding space" so Q·K similarity is meaningful.
                # R shape: (B, N, K, d) -> flatten -> project -> reshape
                if hasattr(self, 'rel_to_col_projection') and self.rel_to_col_projection is not None:
                    R_flat = R.reshape(B * N * K, d)  # (B*N*K, d)
                    R_projected = self.rel_to_col_projection(R_flat)  # (B*N*K, d)
                    R = R_projected.reshape(B, N, K, d)  # (B, N, K, d)

                # Reshape for batch*columns attention
                # [B*N, 1, d] for queries, [B*N, K, d] for keys/values
                q = C.reshape(B * N, 1, d)  # (B*N, 1, d)
                kv = R.reshape(B * N, K, d)  # (B*N, K, d)

                # ========================================================================
                # DEBUG: Log relationship tensor stats BEFORE attention
                # ========================================================================
                _rel_debug_count = getattr(self, '_rel_debug_count', 0)
                self._rel_debug_count = _rel_debug_count + 1
                _should_log_rel_debug = (_rel_debug_count <= 5)  # First 5 batches

                if _should_log_rel_debug:
                    with torch.no_grad():
                        logger.info(f"🔬 [TIER3 DEBUG] Batch #{_rel_debug_count}:")
                        logger.info(f"   Query C: shape={C.shape}, norm={C.norm(dim=-1).mean():.3f}, var={C.var(dim=-1).mean():.4f}")
                        logger.info(f"   R tensor: shape={R.shape}")
                        # Slot 0 is NULL, slots 1+ are relationships
                        null_slot = R[:, :, 0, :]  # (B, N, d)
                        rel_slots = R[:, :, 1:, :]  # (B, N, K-1, d)
                        logger.info(f"   NULL slot (0): norm={null_slot.norm(dim=-1).mean():.3f}, var={null_slot.var(dim=-1).mean():.4f}")
                        if rel_slots.numel() > 0:
                            logger.info(f"   REL slots (1:{K}): norm={rel_slots.norm(dim=-1).mean():.3f}, var={rel_slots.var(dim=-1).mean():.4f}")
                            # Check if all relationship slots are similar (collapsed)
                            rel_slot_means = rel_slots.mean(dim=(0, 1))  # (K-1, d)
                            if rel_slot_means.shape[0] > 1:
                                slot_similarity = F.cosine_similarity(rel_slot_means[0:1].expand(rel_slot_means.shape[0]-1, -1),
                                                                       rel_slot_means[1:], dim=-1).mean().item()
                                logger.info(f"   REL slot similarity (are they diverse?): {slot_similarity:.3f} (1.0=identical, 0=orthogonal)")
                        # Cosine similarity between query and keys
                        q_norm = q / (q.norm(dim=-1, keepdim=True) + 1e-8)  # (B*N, 1, d)
                        kv_norm = kv / (kv.norm(dim=-1, keepdim=True) + 1e-8)  # (B*N, K, d)
                        cos_qk = (q_norm @ kv_norm.transpose(-1, -2)).squeeze(1)  # (B*N, K)
                        cos_qk_null = cos_qk[:, 0].mean().item()
                        cos_qk_rel = cos_qk[:, 1:].mean().item() if K > 1 else 0
                        logger.info(f"   Q·K cosine: NULL={cos_qk_null:.3f}, REL={cos_qk_rel:.3f} (positive=aligned, neg=opposed)")

                # Local attention: each column attends over its K candidates
                # DETERMINISM FIX: Use deterministic SDPA backend during inference
                # Flash attention and memory-efficient attention are non-deterministic
                # The "math" backend is slower but fully deterministic
                if not self.training:
                    with torch.backends.cuda.sdp_kernel(
                        enable_flash=False,
                        enable_math=True,
                        enable_mem_efficient=False
                    ):
                        attn_out, attn_weights = self.local_attention(q, kv, kv)  # (B*N, 1, d), (B*N, 1, K)
                else:
                    attn_out, attn_weights = self.local_attention(q, kv, kv)  # (B*N, 1, d), (B*N, 1, K)
                attn_out = attn_out.reshape(B, N, d)  # (B, N, d)
                attn_weights = attn_weights.reshape(B, N, 1, K)  # (B, N, 1, K)

                # Gate: allow model to damp relationship injection
                gate_values = self.local_attn_gate(C)  # (B, N, d) - per-column gate
                attn_out_gated = gate_values * self.local_attn_dropout(attn_out)  # (B, N, d)

                # ========================================================================
                # DEBUG: Log attention and gate stats
                # ========================================================================
                if _should_log_rel_debug:
                    with torch.no_grad():
                        attn_probs = attn_weights.squeeze(2)  # (B, N, K)
                        null_attn_pct = attn_probs[:, :, 0].mean().item() * 100
                        rel_attn_pct = attn_probs[:, :, 1:].sum(dim=-1).mean().item() * 100 if K > 1 else 0

                        # Per-slot attention breakdown
                        slot_attn = attn_probs.mean(dim=(0, 1))  # (K,)
                        slot_attn_str = ", ".join([f"slot{i}={slot_attn[i].item()*100:.1f}%" for i in range(min(K, 5))])

                        logger.info(f"   Attention weights: NULL={null_attn_pct:.1f}%, REL={rel_attn_pct:.1f}%")
                        logger.info(f"   Per-slot: {slot_attn_str}")
                        logger.info(f"   attn_out (before gate): norm={attn_out.norm(dim=-1).mean():.3f}")
                        logger.info(f"   Gate values: mean={gate_values.mean():.3f}, min={gate_values.min():.3f}, max={gate_values.max():.3f}")
                        logger.info(f"   attn_out_gated: norm={attn_out_gated.norm(dim=-1).mean():.3f}")

                # Residual connection
                C2 = C + attn_out_gated  # (B, N, d)

                # DEBUG: Final injection stats
                if _should_log_rel_debug:
                    with torch.no_grad():
                        delta = C2 - C
                        delta_norm = delta.norm(dim=-1).mean().item()
                        c_norm = C.norm(dim=-1).mean().item()
                        c2_norm = C2.norm(dim=-1).mean().item()
                        cos_c_c2 = F.cosine_similarity(C.reshape(-1, d), C2.reshape(-1, d), dim=-1).mean().item()
                        logger.info(f"   C2 = C + gated_attn: |C|={c_norm:.3f}, |C2|={c2_norm:.3f}, |Δ|={delta_norm:.3f}, cos(C,C2)={cos_c_c2:.3f}")
                
                # Replace column encodings
                x = C2  # (B, N, d) - relationship-enhanced column encodings
                
                # Logging (vectorized, no Python loops)
                if _should_debug:
                    # Attention entropy (measure of selection sharpness)
                    # CORRECTED: low entropy = sharp/selective, high entropy = diffuse/averaging
                    attn_probs = attn_weights.squeeze(2)  # (B, N, K)
                    entropy = -(attn_probs * (attn_probs + 1e-10).log()).sum(dim=-1)  # (B, N)
                    attn_entropy_mean = entropy.mean().item()
                    attn_entropy_std = entropy.std().item()
                    
                    # NULL selection rate
                    null_attn = attn_probs[:, :, 0].mean().item()  # Average attention on NULL slot
                    
                    # Degree stats (vectorized, not Python loops)
                    # Count how often each source column appears across all targets
                    IDX_valid = IDX[:, 1:]  # [N, K] (exclude NULL slot)
                    source_counts = torch.bincount(IDX_valid.flatten(), minlength=N)  # [N] - vectorized!
                    degree_mean = source_counts.float().mean().item()
                    degree_max = source_counts.max().item()
                    degree_std = source_counts.float().std().item()
                    
                    # Gate statistics
                    gate_mean = gate_values.mean().item()
                    gate_std = gate_values.std().item()
                    
                    logger.info(f"[TIER3]   Local attention applied:")
                    logger.info(f"[TIER3]     Attention entropy: {attn_entropy_mean:.4f} ± {attn_entropy_std:.4f} (low=selective, high=diffuse)")
                    logger.info(f"[TIER3]     NULL selection rate: {null_attn*100:.1f}%")
                    logger.info(f"[TIER3]     Source degree: mean={degree_mean:.1f}, max={degree_max}, std={degree_std:.1f}")
                    logger.info(f"[TIER3]     Gate: mean={gate_mean:.3f} ± {gate_std:.3f} (higher=more relationship injection)")
                
                # Store for gradient tracking (if needed)
                if self.training:
                    self._tier3_C = C
                    self._tier3_R = R

                # ====================================================================
                # RELATIONSHIP UTILIZATION LOGGING (once per epoch, not every batch)
                # ====================================================================
                _batch_count = getattr(self, '_rel_util_batch_count', 0)
                self._rel_util_batch_count = _batch_count + 1
                _current_epoch = getattr(self, '_current_epoch', 0)
                _last_logged_epoch = getattr(self, '_rel_util_last_logged_epoch', -1)
                _should_log_util = (_current_epoch != _last_logged_epoch)

                with torch.no_grad():
                    # 1. How much did embeddings change? (C vs C2)
                    delta = C2 - C  # (B, N, d) - the relationship contribution
                    delta_norm = delta.norm(dim=-1)  # (B, N) - per-column change magnitude
                    delta_mean = delta_norm.mean().item()
                    delta_max = delta_norm.max().item()

                    # 2. Relative change (delta / original magnitude)
                    C_norm = C.norm(dim=-1).clamp(min=1e-6)  # (B, N)
                    relative_change = (delta_norm / C_norm).mean().item()

                    # 3. Gate analysis - is the gate letting relationships through?
                    gate_mean = gate_values.mean().item()
                    gate_min = gate_values.min().item()
                    gate_max = gate_values.max().item()

                    # 4. Attention on NULL vs actual relationships
                    attn_probs = attn_weights.squeeze(2)  # (B, N, K)
                    null_attn = attn_probs[:, :, 0].mean().item()
                    rel_attn = attn_probs[:, :, 1:].sum(dim=-1).mean().item()  # Sum of non-NULL attention

                    # ============================================================
                    # ACCUMULATE PER-COLUMN SELECTIVITY METRICS
                    # ============================================================
                    # Track across all batches, log at epoch end for stable statistics
                    # Entropy: low = selective (peaked attention), high = diffuse (uniform)
                    col_entropy = -(attn_probs * (attn_probs + 1e-10).log()).sum(dim=-1).mean(dim=0)  # (N,)
                    col_null_attn_batch = attn_probs[:, :, 0].mean(dim=0)  # (N,)
                    col_rel_change_batch = (delta_norm / C_norm).mean(dim=0)  # (N,)

                    # Initialize or accumulate
                    if self._col_entropy_sum is None or self._col_entropy_sum.shape[0] != N:
                        self._col_entropy_sum = col_entropy.cpu()
                        self._col_null_attn_sum = col_null_attn_batch.cpu()
                        self._col_rel_change_sum = col_rel_change_batch.cpu()
                        self._col_entropy_count = 1
                    else:
                        self._col_entropy_sum += col_entropy.cpu()
                        self._col_null_attn_sum += col_null_attn_batch.cpu()
                        self._col_rel_change_sum += col_rel_change_batch.cpu()
                        self._col_entropy_count += 1

                    # 5. Is attn_out meaningful before gating?
                    attn_out_norm = attn_out.norm(dim=-1).mean().item()
                    attn_out_gated_norm = attn_out_gated.norm(dim=-1).mean().item()

                    # 6. Cosine similarity between original and enhanced (are they still aligned?)
                    cos_sim = F.cosine_similarity(C.reshape(-1, d), C2.reshape(-1, d), dim=-1).mean().item()

                    # ============================================================
                    # HEALTH CHECKS - warn/error when things go off the rails
                    # ============================================================
                    has_problems = False

                    # Check 1: Gate is nearly closed (relationships blocked)
                    if gate_mean < 0.05 and _batch_count > 50:
                        logger.warning(f"⚠️  RELATIONSHIP GATE NEARLY CLOSED: mean={gate_mean:.4f}")
                        logger.warning(f"   Model learned to block relationship injection")
                        has_problems = True

                    # Check 2: NULL attention dominates (relationships ignored)
                    if null_attn > 0.9 and _batch_count > 50:
                        logger.warning(f"⚠️  NULL ATTENTION DOMINATES: {null_attn*100:.1f}%")
                        logger.warning(f"   Model prefers NULL over actual relationships")
                        has_problems = True

                    # Check 3: No change to embeddings (relationships not affecting anything)
                    if relative_change < 0.001 and _batch_count > 50:
                        logger.warning(f"⚠️  RELATIONSHIPS NOT AFFECTING EMBEDDINGS: relative_change={relative_change*100:.4f}%")
                        logger.warning(f"   Relationship features may be too weak or gated out")
                        has_problems = True

                    # Check 4: Relationship contribution exploded
                    if relative_change > 2.0:
                        logger.error(f"🚨 RELATIONSHIP CONTRIBUTION EXPLODED: relative_change={relative_change*100:.1f}%")
                        logger.error(f"   Relationship features are >200% of column encoding magnitude")
                        has_problems = True

                    # Check 5: NaN/Inf in attention or gate
                    if not math.isfinite(gate_mean) or not math.isfinite(null_attn):
                        logger.error(f"🚨 RELATIONSHIP ATTENTION/GATE HAS NaN/Inf!")
                        has_problems = True

                    # Check 6: Cosine similarity is negative (embeddings flipped direction)
                    if cos_sim < 0:
                        logger.warning(f"⚠️  EMBEDDINGS FLIPPED DIRECTION: cos_sim={cos_sim:.4f}")
                        logger.warning(f"   Relationship injection reversed embedding direction")
                        has_problems = True

                    # Log once per epoch (or immediately if problems)
                    if _should_log_util or has_problems:
                        self._rel_util_last_logged_epoch = _current_epoch

                        # Per-column stats
                        col_delta_mean = delta_norm.mean(dim=0)  # (N,) - average change per column
                        col_C_norm = C.norm(dim=-1).mean(dim=0)  # (N,) - original embedding norm per column
                        col_relative = (col_delta_mean / col_C_norm.clamp(min=1e-6))  # (N,) - relative change per column
                        # gate_values is (B, N, d_model), so mean over batch and d_model to get per-column scalar
                        col_gate_mean = gate_values.mean(dim=(0, 2))  # (N,) - gate per column
                        col_null_attn = attn_probs[:, :, 0].mean(dim=0)  # (N,) - null attention per column

                        status = "✅" if not has_problems else "⚠️"
                        logger.info(f"🔗 RELATIONSHIP INJECTION ({status} gate={gate_mean:.2f}, null={null_attn*100:.0f}%, Δ={relative_change*100:.1f}%):")
                        logger.info(f"   {'Column':<25} {'|Δ|':>8} {'Δ%':>8} {'Gate':>8} {'Null%':>8}")
                        logger.info(f"   {'-'*25} {'-'*8} {'-'*8} {'-'*8} {'-'*8}")

                        # Sort by relative change descending (most affected first)
                        sorted_indices = col_relative.argsort(descending=True).tolist()
                        for idx in sorted_indices:
                            col_name = self.col_names_in_order[idx] if idx < len(self.col_names_in_order) else f"col_{idx}"
                            col_name_display = col_name[:25] if len(col_name) <= 25 else col_name[:22] + "..."
                            logger.info(f"   {col_name_display:<25} {col_delta_mean[idx].item():>8.3f} {col_relative[idx].item()*100:>7.1f}% {col_gate_mean[idx].item():>8.2f} {col_null_attn[idx].item()*100:>7.1f}%")
            else:
                if _should_debug:
                    logger.info(f"[TIER3]   No active relationships, skipping local attention")
        
        # Add CLS token AFTER Tier 3 local attention (if applied)
        x = self.add_cls_token(x)  # (batch_size, 1 + n_cols, d_model)

        # NOTE: x now has relationship-enhanced column encodings (if Tier 3 was applied)
        # or original column encodings (if no relationships)

        # ============================================================================
        # VARIANCE TRACKING: Find where variance is being lost
        # ============================================================================
        current_epoch = getattr(self, '_current_epoch', 0)
        if not hasattr(self, '_var_track_epoch') or self._var_track_epoch != current_epoch:
            self._var_track_epoch = current_epoch
            with torch.no_grad():
                # Variance of column tokens BEFORE transformer (skip CLS at position 0)
                col_tokens_before = x[:, 1:, :]  # (B, n_cols, d_model)
                var_before = col_tokens_before.var(dim=0).mean().item()

                # Check transformer state
                is_training = self.transformer_encoder.training
                n_layers = len(self.transformer_encoder.layers)
                has_grad = x.requires_grad

                logger.info(f"🔍 [epoch={current_epoch}] VARIANCE TRACKING:")
                logger.info(f"   Before transformer: var={var_before:.6f}")
                logger.info(f"   Transformer: training={is_training}, n_layers={n_layers}, input.requires_grad={has_grad}")

                # Check weight stats for first layer
                layer0 = self.transformer_encoder.layers[0]
                q_weight = layer0.self_attn.in_proj_weight
                q_weight_std = q_weight.std().item()
                q_weight_mean = q_weight.mean().item()
                ff_weight = layer0.linear1.weight
                ff_weight_std = ff_weight.std().item()

                logger.info(f"   Layer0 weights: Q_proj std={q_weight_std:.6f} mean={q_weight_mean:.6f}, FF std={ff_weight_std:.6f}")

                # Run through layers one by one to see where variance dies
                # SKIP when gradient checkpointing is enabled - running layers here
                # messes up RNG state and causes checkpoint recompute mismatch
                if not (self.enable_gradient_checkpointing and self.training):
                    layer_input = x.clone()
                    for i, layer in enumerate(self.transformer_encoder.layers):
                        layer_output = layer(layer_input)
                        col_var = layer_output[:, 1:, :].var(dim=0).mean().item()
                        logger.info(f"   After layer {i}: var={col_var:.6f}")
                        layer_input = layer_output
                else:
                    logger.info(f"   (Per-layer variance tracking skipped - gradient checkpointing enabled)")

        # DEBUG: Log shape before transformer encoder - this is where MPS INT_MAX can overflow
        if _should_debug:
            batch_size_debug = x.shape[0]
            seq_len_debug = x.shape[1]
            d_model_debug = x.shape[2]
            n_heads = self.config.n_heads
            # Attention matrix size: (batch * n_heads, seq_len, seq_len)
            attn_matrix_size = batch_size_debug * n_heads * seq_len_debug * seq_len_debug
            INT_MAX = 2**31 - 1
            logger.info(f"[DEBUG]   Before transformer_encoder:")
            logger.info(f"[DEBUG]     x shape: {x.shape} (batch={batch_size_debug}, seq={seq_len_debug}, d_model={d_model_debug})")
            logger.info(f"[DEBUG]     n_heads: {n_heads}")
            logger.info(f"[DEBUG]     Attention matrix elements: {batch_size_debug} × {n_heads} × {seq_len_debug}² = {attn_matrix_size:,}")
            if attn_matrix_size > INT_MAX:
                logger.error(f"[DEBUG]   ⚠️ ATTENTION MATRIX EXCEEDS INT_MAX ({INT_MAX:,})!")
            logger.info(f"[DEBUG]     About to call transformer_encoder...")

        # Pass through the transformer encoder (now using batch_first=True)
        # Use gradient checkpointing if enabled to save memory
        if self.enable_gradient_checkpointing and self.training:
            x = checkpoint(self.transformer_encoder, x, use_reentrant=False)
        elif not self.training:
            # DETERMINISM FIX: Use deterministic SDPA backend during inference
            # Flash attention and memory-efficient attention are non-deterministic
            with torch.backends.cuda.sdp_kernel(
                enable_flash=False,
                enable_math=True,
                enable_mem_efficient=False
            ):
                x = self.transformer_encoder(x)
        else:
            x = self.transformer_encoder(x)

        if _should_debug:
            logger.info(f"[DEBUG]   After transformer_encoder: x shape = {x.shape}")

        # ====================================================================
        # GROUP ATTENTION BIAS LOGGING
        # ====================================================================
        # Log the learned group bias values periodically
        if getattr(self, '_use_group_biased_transformer', False):
            _group_bias_batch_count = getattr(self, '_group_bias_batch_count', 0)
            self._group_bias_batch_count = _group_bias_batch_count + 1
            _should_log_bias = (_group_bias_batch_count % 200 == 0)

            with torch.no_grad():
                # Collect bias values from all layers
                layer_biases = []
                for i, layer in enumerate(self.transformer_encoder.layers):
                    if hasattr(layer, 'group_bias') and layer.group_bias is not None:
                        bias_vals = layer.group_bias.detach().cpu().tolist()
                        layer_biases.append((i, bias_vals))

                if layer_biases:
                    # Aggregate stats across layers
                    all_biases = [b for _, biases in layer_biases for b in biases]
                    mean_bias = sum(all_biases) / len(all_biases)
                    min_bias = min(all_biases)
                    max_bias = max(all_biases)

                    # ============================================================
                    # HEALTH CHECKS - warn/error when things go off the rails
                    # ============================================================
                    has_problems = False

                    # Check 1: Bias exploded (> 10 is extreme, attention will be nearly deterministic)
                    if max_bias > 10.0:
                        logger.error(f"🚨 GROUP ATTENTION BIAS EXPLODED: max={max_bias:.2f} (>10)")
                        logger.error(f"   This will make intra-group attention nearly 100%, ignoring other columns")
                        logger.error(f"   Consider: gradient clipping, lower LR, or regularizing group_bias")
                        has_problems = True

                    # Check 2: Bias collapsed to near-zero (not learning anything useful)
                    if abs(mean_bias) < 0.01 and _group_bias_batch_count > 100:
                        logger.warning(f"⚠️  GROUP ATTENTION BIAS COLLAPSED: mean={mean_bias:.4f} (~0)")
                        logger.warning(f"   Group structure may not be helping - biases learned to be neutral")
                        has_problems = True

                    # Check 3: Bias went strongly negative (suppressing intra-group attention)
                    if min_bias < -2.0:
                        logger.warning(f"⚠️  GROUP ATTENTION BIAS NEGATIVE: min={min_bias:.2f}")
                        logger.warning(f"   Model is SUPPRESSING intra-group attention (unexpected)")
                        logger.warning(f"   This suggests group members may be redundant/competing")
                        has_problems = True

                    # Check 4: NaN or Inf
                    if any(not math.isfinite(b) for b in all_biases):
                        logger.error(f"🚨 GROUP ATTENTION BIAS HAS NaN/Inf!")
                        logger.error(f"   Values: {all_biases}")
                        has_problems = True

                    # Check 5: Huge variance between layers (unstable)
                    if len(all_biases) > 1:
                        bias_std = (sum((b - mean_bias) ** 2 for b in all_biases) / len(all_biases)) ** 0.5
                        if bias_std > 3.0:
                            logger.warning(f"⚠️  GROUP ATTENTION BIAS HIGH VARIANCE: std={bias_std:.2f}")
                            logger.warning(f"   Different layers have very different biases - may be unstable")
                            has_problems = True

                    # Regular logging (every 200 batches, or immediately if problems)
                    if _should_log_bias or has_problems:
                        logger.info(f"🔗 GROUP ATTENTION BIAS [batch {_group_bias_batch_count}]:")
                        for layer_idx, biases in layer_biases:
                            bias_strs = [f"g{i}={b:.3f}" for i, b in enumerate(biases)]
                            logger.info(f"   Layer {layer_idx}: {', '.join(bias_strs)}")
                        logger.info(f"   Overall: mean={mean_bias:.3f}, range=[{min_bias:.3f}, {max_bias:.3f}]")
                        if not has_problems:
                            logger.info(f"   Status: ✅ healthy (positive=boost intra-group attention)")

        # ============================================================================
        # JOINT POOLING: CLS TOKEN vs MEAN OF COLUMNS
        # ============================================================================
        # CLS token (use_cls_token_pooling=True):
        #   - Uses transformer's CLS output (position 0)
        #   - Properly handles variable-length rows (NOT_PRESENT columns excluded via attention)
        #   - The transformer learns to aggregate only present columns into CLS
        #
        # Mean pooling (use_cls_token_pooling=False):
        #   - Uses mean of column outputs (positions 1:)
        #   - Problem: NOT_PRESENT columns still contribute to mean
        #   - Was added to fix CLS variance collapse but breaks NULL handling
        # ============================================================================
        # x shape: (B, 1 + n_cols, d_model) where position 0 is CLS, 1: are columns
        from featrix.neural.sphere_config import get_config
        use_cls = get_config().use_cls_token_pooling()

        if use_cls:
            # CLS token approach - position 0 is the CLS token
            joint = x[:, 0, :]  # (B, d_model) - CLS token output
        else:
            # Mean of column outputs (legacy, broken for NULLs)
            joint = x[:, 1:, :].mean(dim=1)  # (B, d_model) - mean of column outputs

        # convert from transformer dim to embedding_space dim, and normalize
        joint = self.out_converter(joint)

        # ============================================================================
        # GLOBAL RESIDUAL: Add mean of input columns to output
        # ============================================================================
        # This makes the joint encoder less sensitive to small input changes.
        # With masking, we replace columns with marginal embeddings - this causes
        # drastic output changes because the transformer completely transforms inputs.
        # Adding input_mean as residual ensures small input changes → small output changes.
        #
        # C is defined earlier at line ~444: column encodings BEFORE transformer
        # We project it through out_converter to match dimensions
        # ============================================================================
        input_mean = C.mean(dim=1)  # (B, d_model) - mean of column encodings before transformer
        input_mean_projected = self.out_converter(input_mean)  # (B, embedding_dim)
        joint = joint + input_mean_projected  # Residual connection from input

        # ============================================================================
        # DIAGNOSTIC: Track variance before vs after normalization
        # ============================================================================
        current_epoch = getattr(self, '_current_epoch', 0)
        if not hasattr(self, '_norm_track_epoch') or self._norm_track_epoch != current_epoch:
            self._norm_track_epoch = current_epoch
            with torch.no_grad():
                var_before_norm = joint.var(dim=0).mean().item()
                # After normalization, all vectors are unit length
                # But variance across batch tells us if vectors point in different directions
                joint_normalized = nn.functional.normalize(joint, dim=1)
                var_after_norm = joint_normalized.var(dim=0).mean().item()

                # Check ANGULAR diversity: cosine similarity between all pairs
                # High avg cosine = vectors point same direction = collapse
                cos_sim_matrix = joint_normalized @ joint_normalized.T  # (B, B)
                # Exclude diagonal (self-similarity = 1.0)
                B = cos_sim_matrix.shape[0]
                mask = ~torch.eye(B, dtype=torch.bool, device=cos_sim_matrix.device)
                avg_cos_sim = cos_sim_matrix[mask].mean().item()

                # Also check norms before normalization
                norms = joint.norm(dim=1)
                norm_mean = norms.mean().item()
                norm_std = norms.std().item()

                logger.info(f"🔬 [epoch={current_epoch}] NORMALIZATION IMPACT:")
                logger.info(f"   Before normalize: var={var_before_norm:.6f}, norm={norm_mean:.4f}±{norm_std:.4f}")
                logger.info(f"   After normalize:  var={var_after_norm:.6f}")
                logger.info(f"   Avg pairwise cosine sim: {avg_cos_sim:.4f} (0=orthogonal, 1=identical)")
                if avg_cos_sim > 0.9:
                    logger.warning(f"   ⚠️  ANGULAR COLLAPSE: vectors point in same direction!")

        # LEARNED SHORT PROJECTION
        # Instead of slicing joint[:, 0:3], use learned projection for better 3D separation
        # The projection learns to combine all d_model dimensions optimally for 3D visualization
        short_projection = getattr(self, 'short_projection', None)
        if short_projection is not None:
            short_vec_raw = self.short_projection(joint)  # (B, 3) - learned projection
        else:
            # Fallback for old pickles that don't have short_projection
            short_vec_raw = joint[:, 0:3]

        # L2 normalize to unit sphere - required for stable training
        # Without normalization, gradients explode (275k+)
        # The 22% coverage issue is a separate problem to solve with regularization
        short_vec = F.normalize(short_vec_raw, p=2, dim=1, eps=1e-8)
        full_vec = F.normalize(joint, p=2, dim=1, eps=1e-8)

        return short_vec, full_vec
    
    def analyze_attention_head_redundancy(self, batch_data, top_k=5):
        """
        Analyze if attention heads are learning redundant patterns.
        
        This diagnostic helps determine if you need more attention heads:
        - High redundancy (>0.8 similarity) → heads are learning the same thing → need more heads
        - Low redundancy (<0.5 similarity) → heads are diverse → current head count is good
        
        Args:
            batch_data: Input tensor (batch_size, n_cols, d_model) 
            top_k: Number of top attention positions to consider per head
        
        Returns:
            dict with:
                - 'head_similarities': (n_heads, n_heads) pairwise cosine similarities
                - 'avg_similarity': Average pairwise similarity across all heads
                - 'max_similarity': Maximum pairwise similarity (most redundant pair)
                - 'redundant_pairs': List of (head_i, head_j, similarity) where sim > 0.7
                - 'diversity_score': 1 - avg_similarity (higher = more diverse)
                - 'recommendation': String suggesting if more heads are needed
        """
        if not self._enable_attention_capture:
            logger.warning("⚠️  Attention capture is disabled. Call enable_attention_capture() first.")
            return None
        
        # Run forward pass to populate attention weights
        self.eval()  # Set to eval mode to get consistent attention
        with torch.no_grad():
            _ = self.forward(batch_data)
        
        # NOTE: PyTorch's TransformerEncoder doesn't expose attention weights by default
        # We need to monkey-patch or use a custom implementation
        # For now, we'll extract attention from the encoder layers
        
        attention_patterns = []
        n_layers = self.config.n_layers
        n_heads = self.config.n_heads
        
        # Extract attention weights from each layer
        for layer_idx, layer in enumerate(self.transformer_encoder.layers):
            # Access the self-attention module
            self_attn = layer.self_attn
            
            # Need to hook into attention computation
            # This requires modifying the forward pass or using hooks
            # For now, we'll compute attention patterns manually
            pass
        
        # TODO: This requires deeper integration with PyTorch's attention mechanism
        # For now, return a placeholder
        logger.warning("⚠️  Full attention analysis requires attention weight extraction hooks.")
        logger.info("   Analyzing attention patterns via weight similarity instead...")
        
        # Alternative: Analyze attention weight matrices for similarity
        head_patterns = self._analyze_attention_weight_similarity()
        
        return head_patterns
    
    def _analyze_attention_weight_similarity(self):
        """
        Analyze similarity between attention heads by comparing their learned weight matrices.
        
        This is an approximation: instead of comparing attention patterns on specific inputs,
        we compare the learned Q, K, V projection matrices for each head.
        """
        n_heads = self.config.n_heads
        d_model = self.config.d_model
        
        # Collect Q, K, V weight matrices from first transformer layer
        first_layer = self.transformer_encoder.layers[0]
        
        # PyTorch's MultiheadAttention stores weights as (d_model, d_model)
        # Then splits into n_heads during forward pass
        q_weights = first_layer.self_attn.in_proj_weight[:d_model, :]  # Query weights
        k_weights = first_layer.self_attn.in_proj_weight[d_model:2*d_model, :]  # Key weights
        v_weights = first_layer.self_attn.in_proj_weight[2*d_model:, :]  # Value weights
        
        head_dim = d_model // n_heads
        
        # Split into per-head matrices
        q_heads = q_weights.reshape(n_heads, head_dim, d_model)
        k_heads = k_weights.reshape(n_heads, head_dim, d_model)
        v_heads = v_weights.reshape(n_heads, head_dim, d_model)
        
        # Compute pairwise similarities between heads
        # We'll use cosine similarity of flattened QK^T patterns
        head_similarities = torch.zeros(n_heads, n_heads)
        
        for i in range(n_heads):
            for j in range(i, n_heads):
                # Compute attention pattern similarity: compare QK^T for each head
                # QK^T shape would be (head_dim, head_dim) but we want to compare overall behavior
                # Simplified: compare Q and K weights directly
                
                q_i_flat = q_heads[i].flatten()
                q_j_flat = q_heads[j].flatten()
                k_i_flat = k_heads[i].flatten()
                k_j_flat = k_heads[j].flatten()
                
                # Cosine similarity of Q weights
                q_sim = F.cosine_similarity(q_i_flat.unsqueeze(0), q_j_flat.unsqueeze(0))
                
                # Cosine similarity of K weights  
                k_sim = F.cosine_similarity(k_i_flat.unsqueeze(0), k_j_flat.unsqueeze(0))
                
                # Average Q and K similarity
                sim = (q_sim + k_sim) / 2.0
                
                head_similarities[i, j] = sim.item()
                head_similarities[j, i] = sim.item()
        
        # Compute statistics
        # Exclude diagonal (self-similarity = 1.0)
        mask = ~torch.eye(n_heads, dtype=torch.bool)
        off_diagonal = head_similarities[mask]
        
        avg_similarity = off_diagonal.mean().item()
        max_similarity = off_diagonal.max().item()
        min_similarity = off_diagonal.min().item()
        
        # Find redundant pairs (similarity > 0.7)
        redundant_pairs = []
        for i in range(n_heads):
            for j in range(i+1, n_heads):
                sim = head_similarities[i, j].item()
                if sim > 0.7:
                    redundant_pairs.append((i, j, sim))
        
        # Sort by similarity (most redundant first)
        redundant_pairs.sort(key=lambda x: x[2], reverse=True)
        
        # Diversity score (higher = more diverse)
        diversity_score = 1.0 - avg_similarity
        
        # Generate recommendation
        if avg_similarity > 0.8:
            recommendation = "HIGH REDUNDANCY: Heads are learning very similar patterns. Consider increasing n_heads."
            status = "❌ REDUNDANT"
        elif avg_similarity > 0.6:
            recommendation = "MODERATE REDUNDANCY: Some overlap between heads. Current head count is okay, but could benefit from more."
            status = "⚠️  MODERATE"
        else:
            recommendation = "GOOD DIVERSITY: Heads are learning distinct patterns. Current head count is appropriate."
            status = "✅ DIVERSE"
        
        result = {
            'head_similarities': head_similarities.cpu().numpy(),
            'avg_similarity': avg_similarity,
            'max_similarity': max_similarity,
            'min_similarity': min_similarity,
            'redundant_pairs': redundant_pairs,
            'diversity_score': diversity_score,
            'recommendation': recommendation,
            'status': status,
            'n_heads': n_heads,
            'n_redundant_pairs': len(redundant_pairs),
        }
        
        return result
    
    def log_attention_analysis(self, batch_data=None):
        """
        Log attention head diversity analysis.
        
        Args:
            batch_data: Optional input batch. If None, only analyzes weight similarity.
        """
        logger.info("🔍 ATTENTION HEAD DIVERSITY ANALYSIS")
        logger.info(f"   Number of heads: {self.config.n_heads}")
        logger.info(f"   Number of layers: {self.config.n_layers}")
        logger.info(f"   Model dimension: {self.config.d_model}")
        logger.info(f"   Head dimension: {self.config.d_model // self.config.n_heads}")
        
        # Analyze weight similarity
        analysis = self._analyze_attention_weight_similarity()
        
        logger.info(f"\n{analysis['status']} Attention Head Diversity:")
        logger.info(f"   Average head similarity: {analysis['avg_similarity']:.3f}")
        logger.info(f"   Diversity score: {analysis['diversity_score']:.3f} (higher is better)")
        logger.info(f"   Min similarity: {analysis['min_similarity']:.3f}")
        logger.info(f"   Max similarity: {analysis['max_similarity']:.3f}")
        
        if analysis['redundant_pairs']:
            logger.info(f"\n⚠️  Found {len(analysis['redundant_pairs'])} redundant head pairs (>0.7 similarity):")
            for i, j, sim in analysis['redundant_pairs'][:5]:  # Show top 5
                logger.info(f"      Head {i} ↔ Head {j}: {sim:.3f}")
        else:
            logger.info("\n✅ No redundant head pairs found (all < 0.7 similarity)")
        
        logger.info(f"\n💡 {analysis['recommendation']}")
        
        return analysis
