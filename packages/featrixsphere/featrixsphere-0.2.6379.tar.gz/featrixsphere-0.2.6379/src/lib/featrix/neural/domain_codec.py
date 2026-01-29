#  -*- coding: utf-8 -*-
#
#  Copyright Featrix, Inc 2023-2025
#
#  Proprietary and Confidential.  Unauthorized use, copying or dissemination
#  of these materials is strictly prohibited.
"""
Domain Codec and Encoder

Encodes domain names by combining:
- Subdomain (string embedding)
- Domain main part (string embedding)
- TLD (categorical embedding)
- TLD type (categorical: generic/country/new)
- Is free email domain (binary flag)
"""
import logging
import ipaddress
import torch
import torch.nn as nn
import torch.nn.functional as F

from typing import Optional, List, Tuple

from featrix.neural.gpu_utils import get_device
from featrix.neural.featrix_token import Token, TokenStatus
from featrix.neural.model_config import ColumnType, SimpleMLPConfig
from featrix.neural.simple_mlp import SimpleMLP
from featrix.neural.simple_string_cache import SimpleStringCache as StringCache
from featrix.neural.url_parser import parse_domain_parts, classify_tld
from featrix.neural.hubspot_free_domains_list_may_2025 import is_free_email_domain
from featrix.neural.world_data import get_or_lookup_dns

logger = logging.getLogger(__name__)


class DomainEncoder(nn.Module):
    """
    Encodes domain features using an MLP.

    Input: TokenBatch with tensor values of shape [batch, 163]:
    - subdomain_emb (32): truncated string embedding
    - domain_main_emb (128): truncated string embedding
    - tld_idx (1): TLD vocabulary index
    - tld_type_idx (1): TLD type index
    - is_free (1): free email domain flag

    Output: (short_vec, full_vec) embeddings
    """

    def __init__(self, config: SimpleMLPConfig, string_cache: StringCache, column_name: Optional[str] = None):
        super().__init__()
        self.config = config
        self.string_cache = string_cache  # Kept for backward compat, not used in forward
        self.column_name = column_name
        self.d_model = config.d_out

        # Project truncated subdomain embedding (32 -> 64)
        self.subdomain_proj = nn.Linear(DOMAIN_SUBDOMAIN_DIM, 64, bias=False)
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
        # subdomain(64) + domain(128) + tld(32) + tld_type(16) + free_domain(8) = 248
        mlp_input_dim = 64 + 128 + 32 + 16 + 8

        # Create MLP encoder
        self.mlp_encoder = SimpleMLP(
            SimpleMLPConfig(
                d_in=mlp_input_dim,
                d_out=config.d_out,
                d_hidden=config.d_hidden if hasattr(config, 'd_hidden') else 256,
                n_hidden_layers=config.n_hidden_layers if hasattr(config, 'n_hidden_layers') else 2,
                dropout=config.dropout if hasattr(config, 'dropout') else 0.3,
                normalize=config.normalize if hasattr(config, 'normalize') else True,
                residual=config.residual if hasattr(config, 'residual') else True,
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

    def _get_string_embedding_truncated(self, text: str, dim: int) -> torch.Tensor:
        """Get first `dim` floats of string embedding from cache."""
        if not text or not self.string_cache:
            return torch.zeros(dim, dtype=torch.float32)

        try:
            emb = self.string_cache.get_embedding(text)
            if emb is not None:
                if hasattr(emb, 'numpy'):
                    emb = emb[:dim]
                else:
                    emb = torch.tensor(emb[:dim], dtype=torch.float32)
                if len(emb) < dim:
                    padded = torch.zeros(dim, dtype=torch.float32)
                    padded[:len(emb)] = emb
                    return padded
                return emb.float() if hasattr(emb, 'float') else torch.tensor(emb, dtype=torch.float32)
        except Exception as e:
            logger.debug(f"Failed to get string embedding for '{text}': {e}")

        return torch.zeros(dim, dtype=torch.float32)

    def encode_domain_components(self, domain_comp: dict) -> torch.Tensor:
        """
        Encode domain components directly (without TokenBatch).
        Used by URLEncoder to encode a single domain.

        Args:
            domain_comp: Dictionary with domain components (subdomain, domain_main, tld, etc.)

        Returns:
            Domain embedding tensor of shape [d_model]
        """
        # Get truncated string embeddings
        subdomain_emb = self._get_string_embedding_truncated(
            domain_comp.get('subdomain', ''), DOMAIN_SUBDOMAIN_DIM
        )
        domain_main_emb = self._get_string_embedding_truncated(
            domain_comp.get('domain_main', ''), DOMAIN_MAIN_DIM
        )

        # Get TLD index
        tld = domain_comp.get('tld', '')
        tld_clean = tld.lower() if tld else ''
        tld_idx = DOMAIN_TLD_TO_IDX.get(tld_clean, len(DOMAIN_TLDS) - 1)

        # Get TLD type index
        tld_type = domain_comp.get('tld_type', 'generic')
        tld_type_idx = DOMAIN_TLD_TYPE_TO_IDX.get(tld_type, 0)

        # Is free email domain
        is_free = 1.0 if domain_comp.get('is_free_email_domain', False) else 0.0

        # Project embeddings (add batch dim, then squeeze)
        subdomain_proj = self.subdomain_proj(subdomain_emb.unsqueeze(0)).squeeze(0)  # [64]
        domain_main_proj = self.domain_proj(domain_main_emb.unsqueeze(0)).squeeze(0)  # [128]

        # TLD and TLD type embeddings
        tld_emb = self.tld_embedding(torch.tensor(tld_idx))  # [32]
        tld_type_emb = self.tld_type_embedding(torch.tensor(tld_type_idx))  # [16]

        # Free domain flag
        free_emb = self.free_domain_mlp(torch.tensor([[is_free]])).squeeze(0)  # [8]

        # Concatenate all features
        features = torch.cat([
            subdomain_proj,
            domain_main_proj,
            tld_emb,
            tld_type_emb,
            free_emb,
        ]).unsqueeze(0)  # [1, 248]

        # Encode through MLP
        out = self.mlp_encoder(features)

        return out.squeeze(0)  # [d_model]

    def forward(self, token_batch):
        """
        Encode domain token batch into embeddings.

        Args:
            token_batch: TokenBatch with value tensor of shape [batch, 163]:
                - [:, 0:32] subdomain embedding
                - [:, 32:160] domain_main embedding
                - [:, 160] tld_idx
                - [:, 161] tld_type_idx
                - [:, 162] is_free

        Returns:
            (short_vec, full_vec) tuple of embeddings
        """
        # token_batch.value is [batch_size, 163]
        values = token_batch.value
        batch_size = values.shape[0]
        device = values.device

        # Extract components from token values
        subdomain_raw = values[:, :DOMAIN_SUBDOMAIN_DIM]  # [batch, 32]
        domain_main_raw = values[:, DOMAIN_SUBDOMAIN_DIM:DOMAIN_SUBDOMAIN_DIM + DOMAIN_MAIN_DIM]  # [batch, 128]
        tld_idx = values[:, DOMAIN_SUBDOMAIN_DIM + DOMAIN_MAIN_DIM].long().clamp(0, len(DOMAIN_TLDS) - 1)  # [batch]
        tld_type_idx = values[:, DOMAIN_SUBDOMAIN_DIM + DOMAIN_MAIN_DIM + 1].long().clamp(0, len(DOMAIN_TLD_TYPES) - 1)  # [batch]
        is_free = values[:, DOMAIN_SUBDOMAIN_DIM + DOMAIN_MAIN_DIM + 2:DOMAIN_SUBDOMAIN_DIM + DOMAIN_MAIN_DIM + 3]  # [batch, 1]

        # Project embeddings
        subdomain_emb = self.subdomain_proj(subdomain_raw)  # [batch, 64]
        domain_main_emb = self.domain_proj(domain_main_raw)  # [batch, 128]

        # TLD and TLD type embeddings
        tld_emb = self.tld_embedding(tld_idx)  # [batch, 32]
        tld_type_emb = self.tld_type_embedding(tld_type_idx)  # [batch, 16]

        # Free domain flag
        free_emb = self.free_domain_mlp(is_free)  # [batch, 8]

        # Concatenate all features
        features = torch.cat([
            subdomain_emb,
            domain_main_emb,
            tld_emb,
            tld_type_emb,
            free_emb,
        ], dim=-1)  # [batch, 248]

        # Encode through MLP
        out = self.mlp_encoder(features)

        # Check for NaN in output
        if torch.isnan(out).any() or torch.isinf(out).any():
            logger.error(f"💥 DomainEncoder output contains NaN/Inf!")
            out = self._replacement_embedding.to(out.dtype).unsqueeze(0).expand(batch_size, -1)

        # Override embeddings for special tokens
        status = token_batch.status.to(device)
        out = out.clone()  # Avoid in-place modification
        # Cast replacement embedding to match output dtype (handles bfloat16 mixed precision)
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

    @staticmethod
    def get_default_config(d_model: int, dropout: float):
        """Get default config for domain encoder."""
        from featrix.neural.sphere_config import get_config
        normalize_column_encoders = get_config().get_normalize_column_encoders()

        return SimpleMLPConfig(
            d_in=248,  # subdomain(64) + domain(128) + tld(32) + tld_type(16) + free_domain(8)
            d_out=d_model,
            d_hidden=256,
            n_hidden_layers=2,
            dropout=dropout,
            normalize=normalize_column_encoders,
            residual=True,
            use_batch_norm=True,
        )


# Domain token layout:
# - subdomain_emb: 32 floats (first 32 of string embedding)
# - domain_main_emb: 128 floats (first 128 of string embedding)
# - tld_idx: 1 float
# - tld_type_idx: 1 float
# - is_free: 1 float
# Total: 163 floats
DOMAIN_SUBDOMAIN_DIM = 32
DOMAIN_MAIN_DIM = 128
DOMAIN_TOKEN_DIM = DOMAIN_SUBDOMAIN_DIM + DOMAIN_MAIN_DIM + 3  # 163

# TLD vocabulary
DOMAIN_TLDS = [
    'com', 'net', 'org', 'edu', 'gov', 'mil',
    'uk', 'de', 'fr', 'ca', 'au', 'jp', 'cn', 'ru',
    'io', 'ai', 'app', 'dev', 'tech', 'online',
    'other'
]
DOMAIN_TLD_TO_IDX = {t: i for i, t in enumerate(DOMAIN_TLDS)}

# TLD type vocabulary
DOMAIN_TLD_TYPES = ['generic', 'country', 'new']
DOMAIN_TLD_TYPE_TO_IDX = {t: i for i, t in enumerate(DOMAIN_TLD_TYPES)}


class DomainCodec(nn.Module):
    """
    Codec for domain columns.

    Parses domain names into components and tokenizes them.
    Token value is a tensor of 163 floats:
    - subdomain embedding (32)
    - domain_main embedding (128)
    - tld_idx (1)
    - tld_type_idx (1)
    - is_free (1)
    """

    def __init__(self, enc_dim: int, string_cache: StringCache, debugName: str = "domain_col"):
        super().__init__()
        self._is_decodable = False  # Domains are not directly decodable
        self.enc_dim = enc_dim
        self.string_cache = string_cache
        self.debugName = debugName
        
    def get_codec_name(self):
        return ColumnType.DOMAIN
    
    def get_codec_info(self):
        return {
            "enc_dim": self.enc_dim,
            "features": [
                "subdomain", "domain_main", "tld", "tld_type", "is_free_email_domain"
            ]
        }
    
    def get_not_present_token(self):
        """Return token for missing domain values."""
        return Token(
            value=torch.zeros(DOMAIN_TOKEN_DIM, dtype=torch.float32),
            status=TokenStatus.NOT_PRESENT,
        )

    def get_marginal_token(self):
        """Return token for masked domain values."""
        return Token(
            value=torch.zeros(DOMAIN_TOKEN_DIM, dtype=torch.float32),
            status=TokenStatus.MARGINAL,
        )
    
    def _parse_domain(self, domain_str: str) -> dict:
        """
        Parse domain string into components and perform DNS lookup using world data cache.
        
        Returns:
            Dictionary with subdomain, domain_main, tld, tld_type, is_free_email_domain,
            ip_addresses, has_ipv6
        """
        if not domain_str or not isinstance(domain_str, str):
            return {
                'subdomain': '',
                'domain_main': '',
                'tld': '',
                'tld_type': 'generic',
                'is_free_email_domain': False,
                'ip_addresses': [],
                'has_ipv6': False
            }
        
        # Remove protocol if present
        domain_str = domain_str.strip()
        if domain_str.startswith('http://'):
            domain_str = domain_str[7:]
        elif domain_str.startswith('https://'):
            domain_str = domain_str[8:]
        
        # Remove leading/trailing slashes
        domain_str = domain_str.strip('/')
        
        # Parse domain parts
        subdomain, domain_main, tld = parse_domain_parts(domain_str)
        
        # Classify TLD
        tld_type = classify_tld(tld) if tld else 'generic'
        
        # Check if free email domain
        is_free = False
        ip_addresses = []
        has_ipv6 = False
        
        if domain_main and tld:
            full_domain = f"{domain_main}.{tld}"
            try:
                is_free = is_free_email_domain(full_domain)
            except Exception as e:
                logger.debug(f"Error checking free email domain for {full_domain}: {e}")
            
            # Perform DNS lookup using world data cache
            try:
                dns_info = get_or_lookup_dns(full_domain, force_refresh=False)
                ip_addresses = dns_info.get('ip_addresses', [])
                has_ipv6 = dns_info.get('has_ipv6', False)
            except Exception as e:
                logger.debug(f"Error performing DNS lookup for {full_domain}: {e}")
        
        return {
            'subdomain': subdomain,
            'domain_main': domain_main,
            'tld': tld,
            'tld_type': tld_type,
            'is_free_email_domain': is_free,
            'ip_addresses': ip_addresses,
            'has_ipv6': has_ipv6
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
        Tokenize a domain value into a Token.

        Args:
            value: Domain string

        Returns:
            Token with tensor value of shape [163]:
            - subdomain_emb (32)
            - domain_main_emb (128)
            - tld_idx (1)
            - tld_type_idx (1)
            - is_free (1)
        """
        try:
            domain_str = str(value) if value is not None else ''

            # Parse domain
            domain_comp = self._parse_domain(domain_str)

            # Check if valid
            if not domain_comp['domain_main']:
                return Token(
                    value=torch.zeros(DOMAIN_TOKEN_DIM, dtype=torch.float32),
                    status=TokenStatus.UNKNOWN,
                )

            # Get truncated string embeddings
            subdomain_emb = self._get_string_embedding_truncated(
                domain_comp['subdomain'], DOMAIN_SUBDOMAIN_DIM
            )
            domain_main_emb = self._get_string_embedding_truncated(
                domain_comp['domain_main'], DOMAIN_MAIN_DIM
            )

            # Get TLD index
            tld = domain_comp['tld'].lower() if domain_comp['tld'] else ''
            tld_idx = float(DOMAIN_TLD_TO_IDX.get(tld, len(DOMAIN_TLDS) - 1))

            # Get TLD type index
            tld_type = domain_comp['tld_type'] if domain_comp['tld_type'] else 'generic'
            tld_type_idx = float(DOMAIN_TLD_TYPE_TO_IDX.get(tld_type, 0))

            # Is free email domain
            is_free = 1.0 if domain_comp['is_free_email_domain'] else 0.0

            # Concatenate all features
            token_value = torch.cat([
                subdomain_emb,
                domain_main_emb,
                torch.tensor([tld_idx, tld_type_idx, is_free], dtype=torch.float32)
            ])

            return Token(
                value=token_value,
                status=TokenStatus.OK,
            )

        except Exception as e:
            logger.debug(f"DomainCodec.tokenize failed for value {value}: {e}")
            return Token(
                value=torch.zeros(DOMAIN_TOKEN_DIM, dtype=torch.float32),
                status=TokenStatus.UNKNOWN,
            )

    @property
    def token_dtype(self):
        return torch.Tensor

