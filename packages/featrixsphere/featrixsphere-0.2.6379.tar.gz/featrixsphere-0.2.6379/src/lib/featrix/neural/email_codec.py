#  -*- coding: utf-8 -*-
#
#  Copyright Featrix, Inc 2023-2025
#
#  Proprietary and Confidential.  Unauthorized use, copying or dissemination
#  of these materials is strictly prohibited.
"""
Email Codec and Encoder

Encodes email addresses by combining:
- Local part (string embedding) - the part before @
- Domain components (reuses DomainCodec logic)

Token value is a tensor of 227 floats:
- local_part embedding (64): truncated string embedding
- subdomain embedding (32): truncated string embedding (usually empty for emails)
- domain_main embedding (128): truncated string embedding
- tld_idx (1): TLD vocabulary index
- tld_type_idx (1): TLD type index
- is_free (1): free email domain flag
"""
import logging
import torch
import torch.nn as nn
import torch.nn.functional as F

from typing import Optional

from featrix.neural.gpu_utils import get_device
from featrix.neural.featrix_token import Token, TokenStatus
from featrix.neural.model_config import ColumnType, SimpleMLPConfig
from featrix.neural.simple_mlp import SimpleMLP
from featrix.neural.simple_string_cache import SimpleStringCache as StringCache
from featrix.neural.domain_codec import (
    DomainCodec,
    DOMAIN_SUBDOMAIN_DIM,
    DOMAIN_MAIN_DIM,
    DOMAIN_TOKEN_DIM,
    DOMAIN_TLDS,
    DOMAIN_TLD_TO_IDX,
    DOMAIN_TLD_TYPES,
    DOMAIN_TLD_TYPE_TO_IDX,
)
from featrix.neural.url_parser import parse_domain_parts, classify_tld
from featrix.neural.hubspot_free_domains_list_may_2025 import is_free_email_domain

logger = logging.getLogger(__name__)

# Email token layout:
# - local_part_emb: 64 floats (first 64 of string embedding)
# - subdomain_emb: 32 floats (first 32 of string embedding, usually zeros for email)
# - domain_main_emb: 128 floats (first 128 of string embedding)
# - tld_idx: 1 float
# - tld_type_idx: 1 float
# - is_free: 1 float
# Total: 227 floats
EMAIL_LOCAL_PART_DIM = 64
EMAIL_TOKEN_DIM = EMAIL_LOCAL_PART_DIM + DOMAIN_TOKEN_DIM  # 64 + 163 = 227


class EmailEncoder(nn.Module):
    """
    Encodes email features using an MLP.

    Input: TokenBatch with tensor values of shape [batch, 227]:
    - local_part_emb (64): truncated string embedding
    - subdomain_emb (32): truncated string embedding (usually zeros)
    - domain_main_emb (128): truncated string embedding
    - tld_idx (1): TLD vocabulary index
    - tld_type_idx (1): TLD type index
    - is_free (1): free email domain flag

    Output: (short_vec, full_vec) embeddings
    """

    def __init__(self, config: SimpleMLPConfig, string_cache: StringCache, column_name: Optional[str] = None):
        super().__init__()
        self.config = config
        self.string_cache = string_cache  # Kept for backward compat
        self.column_name = column_name
        self.d_model = config.d_out

        # Project truncated local_part embedding (64 -> 128)
        self.local_part_proj = nn.Linear(EMAIL_LOCAL_PART_DIM, 128, bias=False)
        nn.init.xavier_uniform_(self.local_part_proj.weight, gain=1.0)

        # Project truncated subdomain embedding (32 -> 32)
        self.subdomain_proj = nn.Linear(DOMAIN_SUBDOMAIN_DIM, 32, bias=False)
        nn.init.xavier_uniform_(self.subdomain_proj.weight, gain=0.5)

        # Project truncated domain_main embedding (128 -> 128)
        self.domain_proj = nn.Linear(DOMAIN_MAIN_DIM, 128, bias=False)
        nn.init.xavier_uniform_(self.domain_proj.weight, gain=1.0)

        # TLD embedding (index -> 32)
        self.tld_embedding = nn.Embedding(len(DOMAIN_TLDS), 32)
        nn.init.xavier_uniform_(self.tld_embedding.weight)

        # TLD type embedding (index -> 16)
        self.tld_type_embedding = nn.Embedding(len(DOMAIN_TLD_TYPES), 16)
        nn.init.xavier_uniform_(self.tld_type_embedding.weight)

        # Binary flag for free email domain (1 -> 8)
        self.free_domain_mlp = nn.Linear(1, 8, bias=False)
        nn.init.xavier_uniform_(self.free_domain_mlp.weight, gain=0.5)

        # Total input dimension to MLP:
        # local_part(128) + subdomain(32) + domain(128) + tld(32) + tld_type(16) + free(8) = 344
        mlp_input_dim = 128 + 32 + 128 + 32 + 16 + 8

        # Final combination MLP
        self.combine_mlp = SimpleMLP(
            SimpleMLPConfig(
                d_in=mlp_input_dim,
                d_out=config.d_out,
                d_hidden=config.d_hidden if hasattr(config, 'd_hidden') else 256,
                n_hidden_layers=2,
                dropout=config.dropout if hasattr(config, 'dropout') else 0.2,
                normalize=config.normalize if hasattr(config, 'normalize') else True,
                residual=True,
                use_batch_norm=config.use_batch_norm if hasattr(config, 'use_batch_norm') else True,
            )
        )

        # Replacement embedding for unknown/not present tokens
        self._replacement_embedding = nn.Parameter(torch.randn(config.d_out))

    @property
    def marginal_embedding(self):
        """Return the marginal embedding (same as replacement for masked/not present)."""
        if self.config.normalize:
            return F.normalize(self._replacement_embedding, dim=-1)
        return self._replacement_embedding

    def forward(self, token_batch):
        """
        Encode email token batch into embeddings.

        Args:
            token_batch: TokenBatch with value tensor of shape [batch, 227]:
                - [:, 0:64] local_part embedding
                - [:, 64:96] subdomain embedding
                - [:, 96:224] domain_main embedding
                - [:, 224] tld_idx
                - [:, 225] tld_type_idx
                - [:, 226] is_free

        Returns:
            (short_vec, full_vec) tuple of embeddings
        """
        values = token_batch.value
        batch_size = values.shape[0]
        device = values.device

        # Extract components from token values
        local_part_raw = values[:, :EMAIL_LOCAL_PART_DIM]  # [batch, 64]
        subdomain_raw = values[:, EMAIL_LOCAL_PART_DIM:EMAIL_LOCAL_PART_DIM + DOMAIN_SUBDOMAIN_DIM]  # [batch, 32]
        domain_main_raw = values[:, EMAIL_LOCAL_PART_DIM + DOMAIN_SUBDOMAIN_DIM:EMAIL_LOCAL_PART_DIM + DOMAIN_SUBDOMAIN_DIM + DOMAIN_MAIN_DIM]  # [batch, 128]

        idx_offset = EMAIL_LOCAL_PART_DIM + DOMAIN_SUBDOMAIN_DIM + DOMAIN_MAIN_DIM
        tld_idx = values[:, idx_offset].long().clamp(0, len(DOMAIN_TLDS) - 1)  # [batch]
        tld_type_idx = values[:, idx_offset + 1].long().clamp(0, len(DOMAIN_TLD_TYPES) - 1)  # [batch]
        is_free = values[:, idx_offset + 2:idx_offset + 3]  # [batch, 1]

        # Project embeddings
        local_part_emb = self.local_part_proj(local_part_raw)  # [batch, 128]
        subdomain_emb = self.subdomain_proj(subdomain_raw)  # [batch, 32]
        domain_main_emb = self.domain_proj(domain_main_raw)  # [batch, 128]

        # TLD and TLD type embeddings
        tld_emb = self.tld_embedding(tld_idx)  # [batch, 32]
        tld_type_emb = self.tld_type_embedding(tld_type_idx)  # [batch, 16]

        # Free domain flag
        free_emb = self.free_domain_mlp(is_free)  # [batch, 8]

        # Concatenate all features
        features = torch.cat([
            local_part_emb,
            subdomain_emb,
            domain_main_emb,
            tld_emb,
            tld_type_emb,
            free_emb,
        ], dim=-1)  # [batch, 344]

        # Encode through MLP
        out = self.combine_mlp(features)

        # Check for NaN in output
        if torch.isnan(out).any() or torch.isinf(out).any():
            logger.error(f"💥 EmailEncoder output contains NaN/Inf!")
            out = self._replacement_embedding.unsqueeze(0).expand(batch_size, -1).to(out.dtype)

        # Override embeddings for special tokens
        # Cast _replacement_embedding to match out.dtype (may be BFloat16 under autocast)
        status = token_batch.status.to(device)
        out = out.clone()
        replacement = self._replacement_embedding.to(out.dtype)
        out[status == TokenStatus.NOT_PRESENT] = replacement
        out[status == TokenStatus.UNKNOWN] = replacement
        out[status == TokenStatus.MARGINAL] = replacement

        # Normalize if configured
        if self.config.normalize:
            short_vec = F.normalize(out[:, 0:3], dim=1, eps=1e-8)
            full_vec = F.normalize(out, dim=1, eps=1e-8)
        else:
            short_vec = out[:, 0:3]
            full_vec = out

        return short_vec, full_vec


def get_email_encoder_config(d_model: int) -> SimpleMLPConfig:
    """Get default config for EmailEncoder."""
    from featrix.neural.sphere_config import get_config
    normalize_column_encoders = get_config().get_normalize_column_encoders()

    return SimpleMLPConfig(
        d_in=344,  # local_part(128) + subdomain(32) + domain(128) + tld(32) + tld_type(16) + free(8)
        d_out=d_model,
        d_hidden=256,
        n_hidden_layers=2,
        dropout=0.2,
        normalize=normalize_column_encoders,
        residual=True,
        use_batch_norm=True,
    )


class EmailCodec(DomainCodec):
    """
    Codec for email columns.

    Inherits from DomainCodec and extends it to handle email-specific parsing.
    Token value is a tensor of 227 floats:
    - local_part embedding (64)
    - subdomain embedding (32)
    - domain_main embedding (128)
    - tld_idx (1)
    - tld_type_idx (1)
    - is_free (1)
    """

    def __init__(self, enc_dim: int, string_cache: StringCache, debugName: str = "email_col"):
        # Initialize parent DomainCodec
        super().__init__(enc_dim=enc_dim, string_cache=string_cache, debugName=debugName)

    def get_codec_name(self):
        return ColumnType.EMAIL

    def get_codec_info(self):
        return {
            "enc_dim": self.enc_dim,
            "features": [
                "local_part", "subdomain", "domain_main", "tld", "tld_type", "is_free_email_domain"
            ]
        }

    def get_not_present_token(self):
        """Return token for missing email values."""
        return Token(
            value=torch.zeros(EMAIL_TOKEN_DIM, dtype=torch.float32),
            status=TokenStatus.NOT_PRESENT,
        )

    def get_marginal_token(self):
        """Return token for masked email values."""
        return Token(
            value=torch.zeros(EMAIL_TOKEN_DIM, dtype=torch.float32),
            status=TokenStatus.MARGINAL,
        )

    def _parse_email(self, email_str: str) -> dict:
        """
        Parse email string into components.

        Returns:
            Dictionary with local_part, domain_main, tld, tld_type, is_free_email_domain
        """
        if not email_str or not isinstance(email_str, str):
            return {
                'local_part': '',
                'subdomain': '',
                'domain_main': '',
                'tld': '',
                'tld_type': 'generic',
                'is_free_email_domain': False,
            }

        email_str = email_str.strip().lower()

        # Split by @
        if '@' not in email_str:
            return {
                'local_part': email_str,
                'subdomain': '',
                'domain_main': '',
                'tld': '',
                'tld_type': 'generic',
                'is_free_email_domain': False,
            }

        parts = email_str.split('@')
        local_part = parts[0] if parts else ''
        domain_part = parts[1] if len(parts) > 1 else ''

        # Parse domain parts using URL parser
        subdomain, domain_main, tld = parse_domain_parts(domain_part)

        # Classify TLD
        tld_type = classify_tld(tld) if tld else 'generic'

        # Check if free email domain
        is_free = False
        if domain_main and tld:
            full_domain = f"{domain_main}.{tld}"
            try:
                is_free = is_free_email_domain(full_domain)
            except Exception as e:
                logger.debug(f"Error checking free email domain for {full_domain}: {e}")

        return {
            'local_part': local_part,
            'subdomain': subdomain,
            'domain_main': domain_main,
            'tld': tld,
            'tld_type': tld_type,
            'is_free_email_domain': is_free,
        }

    def _get_string_embedding_truncated(self, text: str, dim: int) -> torch.Tensor:
        """Get first `dim` floats of string embedding from cache."""
        if not text or not self.string_cache:
            return torch.zeros(dim, dtype=torch.float32)

        try:
            emb = self.string_cache.get_embedding(text)
            if emb is not None:
                # Take first `dim` dimensions
                if hasattr(emb, 'numpy'):
                    emb = emb[:dim]
                else:
                    emb = torch.tensor(emb[:dim], dtype=torch.float32)
                if len(emb) < dim:
                    # Pad if embedding is shorter than expected
                    padded = torch.zeros(dim, dtype=torch.float32)
                    padded[:len(emb)] = emb
                    return padded
                return emb.float() if hasattr(emb, 'float') else torch.tensor(emb, dtype=torch.float32)
        except Exception as e:
            logger.debug(f"Failed to get string embedding for '{text}': {e}")

        return torch.zeros(dim, dtype=torch.float32)

    def tokenize(self, value):
        """
        Tokenize an email value into a Token.

        Args:
            value: Email string

        Returns:
            Token with tensor value of shape [227]:
            - local_part_emb (64)
            - subdomain_emb (32)
            - domain_main_emb (128)
            - tld_idx (1)
            - tld_type_idx (1)
            - is_free (1)
        """
        try:
            email_str = str(value) if value is not None else ''

            # Parse email
            email_comp = self._parse_email(email_str)

            # Check if valid
            if not email_comp['local_part'] or not email_comp['domain_main']:
                return Token(
                    value=torch.zeros(EMAIL_TOKEN_DIM, dtype=torch.float32),
                    status=TokenStatus.UNKNOWN,
                )

            # Get truncated string embeddings
            local_part_emb = self._get_string_embedding_truncated(
                email_comp['local_part'], EMAIL_LOCAL_PART_DIM
            )
            subdomain_emb = self._get_string_embedding_truncated(
                email_comp['subdomain'], DOMAIN_SUBDOMAIN_DIM
            )
            domain_main_emb = self._get_string_embedding_truncated(
                email_comp['domain_main'], DOMAIN_MAIN_DIM
            )

            # Get TLD index
            tld = email_comp['tld'].lower() if email_comp['tld'] else ''
            tld_idx = float(DOMAIN_TLD_TO_IDX.get(tld, len(DOMAIN_TLDS) - 1))

            # Get TLD type index
            tld_type = email_comp['tld_type'] if email_comp['tld_type'] else 'generic'
            tld_type_idx = float(DOMAIN_TLD_TYPE_TO_IDX.get(tld_type, 0))

            # Is free email domain
            is_free = 1.0 if email_comp['is_free_email_domain'] else 0.0

            # Concatenate all features
            token_value = torch.cat([
                local_part_emb,
                subdomain_emb,
                domain_main_emb,
                torch.tensor([tld_idx, tld_type_idx, is_free], dtype=torch.float32)
            ])

            return Token(
                value=token_value,
                status=TokenStatus.OK,
            )
        except Exception as e:
            logger.debug(f"Error tokenizing email '{value}': {e}")
            return self.get_not_present_token()

    @property
    def token_dtype(self):
        return torch.Tensor


def create_email_codec(df_col, detector, embed_dim, string_cache):
    """
    Create EmailCodec for email columns.

    Args:
        df_col: DataFrame column containing email addresses
        detector: Column detector
        embed_dim: Embedding dimension
        string_cache: StringCache for encoding string components
    """
    col_name = detector._debugColName
    logger.info(f"📧 Creating email codec for column: '{col_name}'")

    # EmailCodec needs a StringCache instance
    if isinstance(string_cache, str):
        from featrix.neural.simple_string_cache import SimpleStringCache as StringCache
        cache_instance = StringCache(string_cache_filename=string_cache, readonly=False)
    else:
        cache_instance = string_cache

    codec = EmailCodec(
        enc_dim=embed_dim,
        string_cache=cache_instance,
        debugName=col_name
    )

    return codec