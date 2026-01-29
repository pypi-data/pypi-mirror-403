#  -*- coding: utf-8 -*-
#
#  Copyright Featrix, Inc 2023-2025
#
#  Proprietary and Confidential. Unauthorized use, copying or dissemination
#  of these materials is strictly prohibited.
"""
URL Relationship Operations

Type-aware relationship operations for URL columns.
Includes:
- URL × URL: Same domain, path overlap, query param patterns
- URL × Set/Scalar/Timestamp/String: Cross-type relationships

URL-specific features:
   - has_url (presence)
   - is_https (security)
   - path_depth (complexity)
   - has_query_params (richness)
   - endpoint_semantics (path meaning)

Examples:
- "same domain between source_url and referrer_url"
- "premium product pages use HTTPS more often"
- "deeper path URLs correlate with lower bounce rates"
"""
import logging
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from featrix.neural.type_aware_ops_config import TypeAwareOpsConfig

logger = logging.getLogger(__name__)

# TLD categories (same as email_domain_ops for consistency)
TLD_CATEGORIES = {
    'generic': {'com', 'net', 'org', 'biz', 'info'},
    'country': {'uk', 'de', 'fr', 'ca', 'au', 'jp', 'cn', 'us', 'in', 'br'},
    'education': {'edu', 'ac'},
    'government': {'gov', 'mil'},
    'tech': {'io', 'ai', 'dev', 'app', 'tech', 'cloud', 'digital'},
    'other': set(),  # Catch-all
}
N_TLD_CATEGORIES = len(TLD_CATEGORIES)

# Protocol categories
PROTOCOL_CATEGORIES = {
    'secure': {'https', 'ftps', 'wss'},
    'insecure': {'http', 'ftp', 'ws'},
    'file': {'file'},
    'other': set(),
}
N_PROTOCOL_CATEGORIES = len(PROTOCOL_CATEGORIES)


class URLURLOps(nn.Module):
    """
    Type-aware operations for URL × URL column pairs.

    Features (18 total):
    - same_domain: Both URLs share the same full domain
    - same_domain_main: Both share the domain main part (company name)
    - same_tld: Both share the same TLD
    - same_tld_category: Both in same TLD category
    - same_protocol: Both use same protocol (http/https)
    - both_secure: Both use HTTPS
    - both_insecure: Both use HTTP
    - lhs_secure: Left is HTTPS, right is HTTP
    - rhs_secure: Right is HTTPS, left is HTTP
    - same_path: Exact path match
    - path_prefix_match: One path is prefix of other
    - same_leaf: Same final path segment (endpoint)
    - same_path_depth: Same number of path segments
    - path_depth_diff: Difference in path depths (normalized)
    - both_have_query: Both have query parameters
    - query_overlap: Shared query parameter keys
    - same_port: Both use same port (or both default)
    - path_similarity: Learned path semantic similarity

    Use cases:
    - Navigation analysis: source_url → destination_url patterns
    - Referrer analysis: same-site vs cross-site
    - Duplicate detection: same content at different URLs
    - Link analysis: internal vs external links
    """

    N_URL_FEATURES = 18

    def __init__(
        self,
        d_model: int,
        config: Optional["TypeAwareOpsConfig"] = None,
    ):
        super().__init__()
        self.d_model = d_model
        self.config = config

        # Raw feature processing
        self.feature_mlp = nn.Sequential(
            nn.Linear(self.N_URL_FEATURES, d_model // 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model // 2, d_model),
        )

        # Embedding interaction (captures URL semantic similarity)
        self.interaction_mlp = nn.Sequential(
            nn.Linear(d_model * 3, d_model),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model, d_model),
        )

        # Path alignment (for navigation pattern detection)
        self.path_alignment_mlp = nn.Sequential(
            nn.Linear(d_model * 2, d_model),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model, d_model),
        )

        # Fusion
        self.fusion_mlp = nn.Sequential(
            nn.Linear(d_model * 3, d_model),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model, d_model),
        )

        self.output_norm = nn.LayerNorm(d_model)

        logger.debug(f"   URLURLOps initialized: d_model={d_model}")

    def _get_tld_category_idx(self, tld: str) -> int:
        """Get TLD category index (0-5)."""
        tld = tld.lower()
        for idx, (cat_name, cat_tlds) in enumerate(TLD_CATEGORIES.items()):
            if tld in cat_tlds:
                return idx
        return 5  # 'other'

    def _get_protocol_category_idx(self, protocol: str) -> int:
        """Get protocol category index (0-3)."""
        protocol = protocol.lower()
        for idx, (cat_name, cat_protocols) in enumerate(PROTOCOL_CATEGORIES.items()):
            if protocol in cat_protocols:
                return idx
        return 3  # 'other'

    def _get_path_segments(self, path: str) -> List[str]:
        """Split path into non-empty segments."""
        return [s for s in path.split('/') if s]

    def _parse_query_keys(self, query: str) -> set:
        """Extract query parameter keys."""
        if not query:
            return set()
        keys = set()
        for param in query.split('&'):
            if '=' in param:
                keys.add(param.split('=')[0])
            else:
                keys.add(param)
        return keys

    def compute_url_features(
        self,
        metadata_a: list,
        metadata_b: list,
        device: torch.device,
    ) -> torch.Tensor:
        """
        Compute raw URL comparison features.

        Args:
            metadata_a: List of URL metadata dicts for column A
            metadata_b: List of URL metadata dicts for column B
            device: Target device

        Returns:
            Features tensor (batch, N_URL_FEATURES)
        """
        if not isinstance(metadata_a, list):
            metadata_a = [metadata_a]
        if not isinstance(metadata_b, list):
            metadata_b = [metadata_b]

        features = []

        for ma, mb in zip(metadata_a, metadata_b):
            # Extract components
            domain_a = ma.get('domain', '') if ma else ''
            domain_b = mb.get('domain', '') if mb else ''
            domain_main_a = ma.get('domain_main', '') if ma else ''
            domain_main_b = mb.get('domain_main', '') if mb else ''
            tld_a = ma.get('tld', '') if ma else ''
            tld_b = mb.get('tld', '') if mb else ''
            protocol_a = ma.get('protocol', '') if ma else ''
            protocol_b = mb.get('protocol', '') if mb else ''
            path_a = ma.get('path', '/') if ma else '/'
            path_b = mb.get('path', '/') if mb else '/'
            query_a = ma.get('query_params', '') if ma else ''
            query_b = mb.get('query_params', '') if mb else ''
            port_a = ma.get('port', '') if ma else ''
            port_b = mb.get('port', '') if mb else ''

            # Domain features
            same_domain = float(domain_a.lower() == domain_b.lower() and domain_a != '')
            same_domain_main = float(
                domain_main_a.lower() == domain_main_b.lower()
                and domain_main_a != ''
            )
            same_tld = float(tld_a.lower() == tld_b.lower() and tld_a != '')
            tld_cat_a = self._get_tld_category_idx(tld_a)
            tld_cat_b = self._get_tld_category_idx(tld_b)
            same_tld_category = float(tld_cat_a == tld_cat_b)

            # Protocol features
            same_protocol = float(protocol_a.lower() == protocol_b.lower() and protocol_a != '')
            is_secure_a = protocol_a.lower() in {'https', 'ftps', 'wss'}
            is_secure_b = protocol_b.lower() in {'https', 'ftps', 'wss'}
            both_secure = float(is_secure_a and is_secure_b)
            both_insecure = float(not is_secure_a and not is_secure_b and protocol_a != '' and protocol_b != '')
            lhs_secure = float(is_secure_a and not is_secure_b)
            rhs_secure = float(not is_secure_a and is_secure_b)

            # Path features
            same_path = float(path_a == path_b and path_a != '/')
            segments_a = self._get_path_segments(path_a)
            segments_b = self._get_path_segments(path_b)
            depth_a = len(segments_a)
            depth_b = len(segments_b)

            # Path prefix match (one is prefix of other)
            min_len = min(depth_a, depth_b)
            path_prefix_match = float(
                min_len > 0 and
                segments_a[:min_len] == segments_b[:min_len]
            )

            # Same leaf (final segment)
            same_leaf = float(
                depth_a > 0 and depth_b > 0 and
                segments_a[-1] == segments_b[-1]
            )

            same_path_depth = float(depth_a == depth_b)
            path_depth_diff = abs(depth_a - depth_b) / max(depth_a + depth_b, 1)

            # Query features
            has_query_a = query_a != ''
            has_query_b = query_b != ''
            both_have_query = float(has_query_a and has_query_b)

            # Query key overlap
            keys_a = self._parse_query_keys(query_a)
            keys_b = self._parse_query_keys(query_b)
            if keys_a and keys_b:
                query_overlap = len(keys_a & keys_b) / len(keys_a | keys_b)
            else:
                query_overlap = 0.0

            # Port match
            same_port = float(port_a == port_b)  # Both empty counts as match

            # Placeholder for embedding-based similarity
            path_sim_placeholder = 0.0

            features.append([
                same_domain,
                same_domain_main,
                same_tld,
                same_tld_category,
                same_protocol,
                both_secure,
                both_insecure,
                lhs_secure,
                rhs_secure,
                same_path,
                path_prefix_match,
                same_leaf,
                same_path_depth,
                path_depth_diff,
                both_have_query,
                query_overlap,
                same_port,
                path_sim_placeholder,
            ])

        return torch.tensor(features, device=device, dtype=torch.float32)

    def forward(
        self,
        url_embedding_a: torch.Tensor,  # (batch, d_model)
        url_embedding_b: torch.Tensor,  # (batch, d_model)
        metadata_a: Optional[list] = None,
        metadata_b: Optional[list] = None,
    ) -> torch.Tensor:
        """
        Compute relationship embedding for URL × URL pair.

        Args:
            url_embedding_a: Embedding from URLEncoder for column A
            url_embedding_b: Embedding from URLEncoder for column B
            metadata_a: List of URL metadata dicts for A
            metadata_b: List of URL metadata dicts for B

        Returns:
            Relationship embedding (batch, d_model)
        """
        batch_size = url_embedding_a.shape[0]
        device = url_embedding_a.device

        # Compute raw features
        if metadata_a is not None and metadata_b is not None:
            features = self.compute_url_features(metadata_a, metadata_b, device)
        else:
            features = torch.zeros(batch_size, self.N_URL_FEATURES, device=device)

        # Process raw features
        feature_emb = self.feature_mlp(features)

        # Embedding interaction (captures learned URL similarity)
        interaction = self.interaction_mlp(torch.cat([
            url_embedding_a,
            url_embedding_b,
            url_embedding_a * url_embedding_b,
        ], dim=-1))

        # Path alignment
        alignment = self.path_alignment_mlp(torch.cat([
            url_embedding_a,
            url_embedding_b,
        ], dim=-1))

        # Fusion
        combined = torch.cat([feature_emb, interaction, alignment], dim=-1)
        return self.output_norm(self.fusion_mlp(combined))


class URLSetOps(nn.Module):
    """
    Type-aware operations for URL × Set column pairs.

    Computes relationship embeddings that capture:
    - Domain patterns × set values (via domain embedding)
    - URL presence patterns × set values
    - HTTPS usage × set values (security correlation)
    - Path depth × set values (complexity correlation)
    - Query params × set values (transaction patterns)

    Examples:
    - "premium category products more often have HTTPS"
    - "category='checkout' has more query params"
    - "category='blog' has deeper path structures"
    """

    def __init__(
        self,
        d_model: int,
        config: Optional["TypeAwareOpsConfig"] = None,
    ):
        super().__init__()
        self.d_model = d_model
        self.config = config

        # ============================================================================
        # Feature 1: URL Presence Gating
        # ============================================================================
        # Whether URL is present/valid modulates set embedding
        self.presence_gate = nn.Sequential(
            nn.Linear(d_model + 1, d_model // 2),  # +1 for has_url flag
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model // 2, d_model),
        )

        # ============================================================================
        # Feature 2: Protocol Security × Set
        # ============================================================================
        # HTTPS vs HTTP patterns × set values
        self.protocol_encoder = nn.Sequential(
            nn.Linear(N_PROTOCOL_CATEGORIES, d_model // 4),
            nn.ReLU(),
            nn.Linear(d_model // 4, d_model),
        )

        self.protocol_set_interaction = nn.Sequential(
            nn.Linear(d_model * 2, d_model),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model, d_model),
        )

        # ============================================================================
        # Feature 3: TLD Category × Set (reuse from domain ops)
        # ============================================================================
        self.tld_encoder = nn.Sequential(
            nn.Linear(N_TLD_CATEGORIES, d_model // 4),
            nn.ReLU(),
            nn.Linear(d_model // 4, d_model),
        )

        self.tld_set_interaction = nn.Sequential(
            nn.Linear(d_model * 2, d_model),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model, d_model),
        )

        # ============================================================================
        # Feature 4: Path Depth × Set
        # ============================================================================
        # Deeper paths may correlate with specific categories
        # path_depth is a scalar, we encode it as buckets
        self.n_depth_buckets = 5  # 0, 1, 2, 3, 4+
        self.depth_encoder = nn.Sequential(
            nn.Linear(self.n_depth_buckets, d_model // 4),
            nn.ReLU(),
            nn.Linear(d_model // 4, d_model),
        )

        self.depth_set_interaction = nn.Sequential(
            nn.Linear(d_model * 2, d_model),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model, d_model),
        )

        # ============================================================================
        # Feature 5: Query Params × Set
        # ============================================================================
        # Presence and count of query parameters
        self.query_encoder = nn.Sequential(
            nn.Linear(2, d_model // 4),  # has_params, param_count_bucket
            nn.ReLU(),
            nn.Linear(d_model // 4, d_model),
        )

        self.query_set_interaction = nn.Sequential(
            nn.Linear(d_model * 2, d_model),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model, d_model),
        )

        # ============================================================================
        # Feature 6: Set → URL Direction
        # ============================================================================
        # Given set value, what URL characteristics are likely?
        self.set_url_predictor = nn.Sequential(
            nn.Linear(d_model, d_model // 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model // 2, d_model),
        )

        # ============================================================================
        # Fusion
        # ============================================================================
        # presence + protocol + tld + depth + query + set_pred + symmetric = 7 * d_model
        self.fusion_mlp = nn.Sequential(
            nn.Linear(7 * d_model, d_model * 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model * 2, d_model),
        )

        self.output_norm = nn.LayerNorm(d_model)

        logger.debug(f"   URLSetOps initialized: d_model={d_model}")

    def _extract_url_features(
        self,
        url_metadata: list,
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        """Extract features from URL metadata list."""
        if not isinstance(url_metadata, list):
            url_metadata = [url_metadata]

        presence_flags = []
        protocol_onehots = []
        tld_onehots = []
        depth_onehots = []
        query_features = []

        for um in url_metadata:
            # Presence
            is_valid = um.get('is_valid', False) if um else False
            presence_flags.append(1.0 if is_valid else 0.0)

            # Protocol category
            protocol = um.get('protocol', '').lower() if um else ''
            protocol_idx = 3  # Default to 'other'
            for idx, (cat_name, cat_protocols) in enumerate(PROTOCOL_CATEGORIES.items()):
                if protocol in cat_protocols:
                    protocol_idx = idx
                    break
            protocol_oh = [0.0] * N_PROTOCOL_CATEGORIES
            protocol_oh[protocol_idx] = 1.0
            protocol_onehots.append(protocol_oh)

            # TLD category
            tld = um.get('tld', '').lower() if um else ''
            tld_idx = 5  # Default to 'other'
            for idx, (cat_name, cat_tlds) in enumerate(TLD_CATEGORIES.items()):
                if tld in cat_tlds:
                    tld_idx = idx
                    break
            tld_oh = [0.0] * N_TLD_CATEGORIES
            tld_oh[tld_idx] = 1.0
            tld_onehots.append(tld_oh)

            # Path depth
            path = um.get('path', '/') if um else '/'
            depth = len([p for p in path.split('/') if p])  # Count non-empty segments
            depth_bucket = min(depth, 4)  # 0, 1, 2, 3, 4+
            depth_oh = [0.0] * self.n_depth_buckets
            depth_oh[depth_bucket] = 1.0
            depth_onehots.append(depth_oh)

            # Query params
            query = um.get('query_params', '') if um else ''
            has_params = 1.0 if query else 0.0
            param_count = query.count('&') + 1 if query else 0
            param_bucket = min(param_count / 3.0, 1.0)  # Normalize to 0-1
            query_features.append([has_params, param_bucket])

        device = next(self.parameters()).device
        presence = torch.tensor(presence_flags, device=device).unsqueeze(-1)
        protocol = torch.tensor(protocol_onehots, device=device)
        tld = torch.tensor(tld_onehots, device=device)
        depth = torch.tensor(depth_onehots, device=device)
        query = torch.tensor(query_features, device=device)

        return presence, protocol, tld, depth, query

    def forward(
        self,
        url_embedding: torch.Tensor,    # (batch, d_model)
        set_embedding: torch.Tensor,    # (batch, d_model)
        url_metadata: Optional[list] = None,
    ) -> torch.Tensor:
        """
        Compute relationship embedding for URL × Set pair.

        Args:
            url_embedding: Embedding from URLEncoder
            set_embedding: Embedding from SetEncoder
            url_metadata: List of dicts with URL components

        Returns:
            Relationship embedding (batch, d_model)
        """
        batch_size = url_embedding.shape[0]

        # Extract URL features
        if url_metadata is not None:
            presence, protocol, tld, depth, query = self._extract_url_features(url_metadata)
        else:
            device = url_embedding.device
            presence = torch.zeros(batch_size, 1, device=device)
            protocol = torch.zeros(batch_size, N_PROTOCOL_CATEGORIES, device=device)
            protocol[:, 3] = 1.0  # 'other'
            tld = torch.zeros(batch_size, N_TLD_CATEGORIES, device=device)
            tld[:, 5] = 1.0  # 'other'
            depth = torch.zeros(batch_size, self.n_depth_buckets, device=device)
            depth[:, 0] = 1.0  # depth 0
            query = torch.zeros(batch_size, 2, device=device)

        # Feature 1: Presence gating
        presence_gated = self.presence_gate(
            torch.cat([set_embedding, presence], dim=-1)
        )

        # Feature 2: Protocol × Set
        protocol_enc = self.protocol_encoder(protocol)
        protocol_set = self.protocol_set_interaction(
            torch.cat([protocol_enc, set_embedding], dim=-1)
        )

        # Feature 3: TLD × Set
        tld_enc = self.tld_encoder(tld)
        tld_set = self.tld_set_interaction(
            torch.cat([tld_enc, set_embedding], dim=-1)
        )

        # Feature 4: Path Depth × Set
        depth_enc = self.depth_encoder(depth)
        depth_set = self.depth_set_interaction(
            torch.cat([depth_enc, set_embedding], dim=-1)
        )

        # Feature 5: Query × Set
        query_enc = self.query_encoder(query)
        query_set = self.query_set_interaction(
            torch.cat([query_enc, set_embedding], dim=-1)
        )

        # Feature 6: Set → URL prediction
        set_url_pred = self.set_url_predictor(set_embedding)

        # Symmetric
        symmetric = url_embedding * set_embedding

        # Fusion
        combined = torch.cat([
            presence_gated,
            protocol_set,
            tld_set,
            depth_set,
            query_set,
            set_url_pred,
            symmetric,
        ], dim=-1)

        return self.output_norm(self.fusion_mlp(combined))


class URLScalarOps(nn.Module):
    """
    Type-aware operations for URL × Scalar column pairs.

    Computes relationship embeddings that capture:
    - URL presence × scalar patterns
    - HTTPS × scalar correlation
    - Path depth × scalar correlation
    - Query complexity × scalar correlation

    Examples:
    - "HTTPS pages have higher conversion rates"
    - "Deep path URLs have lower bounce rates"
    - "More query params correlate with higher transaction values"
    """

    def __init__(
        self,
        d_model: int,
        config: Optional["TypeAwareOpsConfig"] = None,
    ):
        super().__init__()
        self.d_model = d_model
        self.config = config

        # Feature 1: URL Presence × Scalar
        self.presence_scalar_mlp = nn.Sequential(
            nn.Linear(d_model + 1, d_model // 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model // 2, d_model),
        )

        # Feature 2: Protocol × Scalar
        self.protocol_encoder = nn.Sequential(
            nn.Linear(N_PROTOCOL_CATEGORIES, d_model // 4),
            nn.ReLU(),
            nn.Linear(d_model // 4, d_model),
        )

        self.protocol_scalar_interaction = nn.Sequential(
            nn.Linear(d_model * 2, d_model),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model, d_model),
        )

        # Feature 3: TLD × Scalar
        self.tld_encoder = nn.Sequential(
            nn.Linear(N_TLD_CATEGORIES, d_model // 4),
            nn.ReLU(),
            nn.Linear(d_model // 4, d_model),
        )

        self.tld_scalar_interaction = nn.Sequential(
            nn.Linear(d_model * 2, d_model),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model, d_model),
        )

        # Feature 4: Path Depth × Scalar (direct scalar correlation)
        self.n_depth_buckets = 5
        self.depth_encoder = nn.Sequential(
            nn.Linear(self.n_depth_buckets, d_model // 4),
            nn.ReLU(),
            nn.Linear(d_model // 4, d_model),
        )

        self.depth_scalar_interaction = nn.Sequential(
            nn.Linear(d_model * 2, d_model),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model, d_model),
        )

        # Feature 5: Query Params × Scalar
        self.query_encoder = nn.Sequential(
            nn.Linear(2, d_model // 4),
            nn.ReLU(),
            nn.Linear(d_model // 4, d_model),
        )

        self.query_scalar_interaction = nn.Sequential(
            nn.Linear(d_model * 2, d_model),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model, d_model),
        )

        # Feature 6: Scalar → URL prediction
        self.scalar_url_predictor = nn.Sequential(
            nn.Linear(d_model, d_model // 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model // 2, d_model),
        )

        # Fusion: 6 features + symmetric = 7 * d_model
        self.fusion_mlp = nn.Sequential(
            nn.Linear(7 * d_model, d_model * 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model * 2, d_model),
        )

        self.output_norm = nn.LayerNorm(d_model)

        logger.debug(f"   URLScalarOps initialized: d_model={d_model}")

    def _extract_url_features(
        self,
        url_metadata: list,
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        """Extract features from URL metadata list."""
        if not isinstance(url_metadata, list):
            url_metadata = [url_metadata]

        presence_flags = []
        protocol_onehots = []
        tld_onehots = []
        depth_onehots = []
        query_features = []

        for um in url_metadata:
            is_valid = um.get('is_valid', False) if um else False
            presence_flags.append(1.0 if is_valid else 0.0)

            protocol = um.get('protocol', '').lower() if um else ''
            protocol_idx = 3
            for idx, (cat_name, cat_protocols) in enumerate(PROTOCOL_CATEGORIES.items()):
                if protocol in cat_protocols:
                    protocol_idx = idx
                    break
            protocol_oh = [0.0] * N_PROTOCOL_CATEGORIES
            protocol_oh[protocol_idx] = 1.0
            protocol_onehots.append(protocol_oh)

            tld = um.get('tld', '').lower() if um else ''
            tld_idx = 5
            for idx, (cat_name, cat_tlds) in enumerate(TLD_CATEGORIES.items()):
                if tld in cat_tlds:
                    tld_idx = idx
                    break
            tld_oh = [0.0] * N_TLD_CATEGORIES
            tld_oh[tld_idx] = 1.0
            tld_onehots.append(tld_oh)

            path = um.get('path', '/') if um else '/'
            depth = len([p for p in path.split('/') if p])
            depth_bucket = min(depth, 4)
            depth_oh = [0.0] * self.n_depth_buckets
            depth_oh[depth_bucket] = 1.0
            depth_onehots.append(depth_oh)

            query = um.get('query_params', '') if um else ''
            has_params = 1.0 if query else 0.0
            param_count = query.count('&') + 1 if query else 0
            param_bucket = min(param_count / 3.0, 1.0)
            query_features.append([has_params, param_bucket])

        device = next(self.parameters()).device
        presence = torch.tensor(presence_flags, device=device).unsqueeze(-1)
        protocol = torch.tensor(protocol_onehots, device=device)
        tld = torch.tensor(tld_onehots, device=device)
        depth = torch.tensor(depth_onehots, device=device)
        query = torch.tensor(query_features, device=device)

        return presence, protocol, tld, depth, query

    def forward(
        self,
        url_embedding: torch.Tensor,
        scalar_embedding: torch.Tensor,
        url_metadata: Optional[list] = None,
    ) -> torch.Tensor:
        batch_size = url_embedding.shape[0]

        if url_metadata is not None:
            presence, protocol, tld, depth, query = self._extract_url_features(url_metadata)
        else:
            device = url_embedding.device
            presence = torch.zeros(batch_size, 1, device=device)
            protocol = torch.zeros(batch_size, N_PROTOCOL_CATEGORIES, device=device)
            protocol[:, 3] = 1.0
            tld = torch.zeros(batch_size, N_TLD_CATEGORIES, device=device)
            tld[:, 5] = 1.0
            depth = torch.zeros(batch_size, self.n_depth_buckets, device=device)
            depth[:, 0] = 1.0
            query = torch.zeros(batch_size, 2, device=device)

        # Feature 1
        presence_scalar = self.presence_scalar_mlp(
            torch.cat([scalar_embedding, presence], dim=-1)
        )

        # Feature 2
        protocol_enc = self.protocol_encoder(protocol)
        protocol_scalar = self.protocol_scalar_interaction(
            torch.cat([protocol_enc, scalar_embedding], dim=-1)
        )

        # Feature 3
        tld_enc = self.tld_encoder(tld)
        tld_scalar = self.tld_scalar_interaction(
            torch.cat([tld_enc, scalar_embedding], dim=-1)
        )

        # Feature 4
        depth_enc = self.depth_encoder(depth)
        depth_scalar = self.depth_scalar_interaction(
            torch.cat([depth_enc, scalar_embedding], dim=-1)
        )

        # Feature 5
        query_enc = self.query_encoder(query)
        query_scalar = self.query_scalar_interaction(
            torch.cat([query_enc, scalar_embedding], dim=-1)
        )

        # Feature 6
        scalar_url_pred = self.scalar_url_predictor(scalar_embedding)

        # Symmetric
        symmetric = url_embedding * scalar_embedding

        combined = torch.cat([
            presence_scalar,
            protocol_scalar,
            tld_scalar,
            depth_scalar,
            query_scalar,
            scalar_url_pred,
            symmetric,
        ], dim=-1)

        return self.output_norm(self.fusion_mlp(combined))


class URLTimestampOps(nn.Module):
    """
    Type-aware operations for URL × Timestamp column pairs.

    Computes relationship embeddings that capture:
    - HTTPS adoption over time
    - URL patterns by time of day/week
    - Path patterns by temporal context

    Examples:
    - "HTTPS adoption increased after 2018"
    - "Checkout URLs more common during business hours"
    """

    def __init__(
        self,
        d_model: int,
        config: Optional["TypeAwareOpsConfig"] = None,
    ):
        super().__init__()
        self.d_model = d_model
        self.config = config

        # Temporal features: 37 dims from set/scalar timestamp ops
        self.n_temporal_features = 37

        # Feature 1: Protocol × Time
        self.protocol_encoder = nn.Sequential(
            nn.Linear(N_PROTOCOL_CATEGORIES, d_model // 4),
            nn.ReLU(),
            nn.Linear(d_model // 4, d_model),
        )

        self.protocol_temporal = nn.Sequential(
            nn.Linear(d_model + self.n_temporal_features, d_model),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model, d_model),
        )

        # Feature 2: TLD × Time
        self.tld_encoder = nn.Sequential(
            nn.Linear(N_TLD_CATEGORIES, d_model // 4),
            nn.ReLU(),
            nn.Linear(d_model // 4, d_model),
        )

        self.tld_temporal = nn.Sequential(
            nn.Linear(d_model + self.n_temporal_features, d_model),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model, d_model),
        )

        # Feature 3: URL presence × Time
        self.presence_temporal = nn.Sequential(
            nn.Linear(1 + self.n_temporal_features, d_model // 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model // 2, d_model),
        )

        # Feature 4: Path depth × Time
        self.n_depth_buckets = 5
        self.depth_encoder = nn.Sequential(
            nn.Linear(self.n_depth_buckets, d_model // 4),
            nn.ReLU(),
            nn.Linear(d_model // 4, d_model),
        )

        self.depth_temporal = nn.Sequential(
            nn.Linear(d_model + self.n_temporal_features, d_model),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model, d_model),
        )

        # Fusion: 4 features + symmetric = 5 * d_model
        self.fusion_mlp = nn.Sequential(
            nn.Linear(5 * d_model, d_model * 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model * 2, d_model),
        )

        self.output_norm = nn.LayerNorm(d_model)

        logger.debug(f"   URLTimestampOps initialized: d_model={d_model}")

    def _extract_url_features(self, url_metadata: list):
        """Extract URL features."""
        if not isinstance(url_metadata, list):
            url_metadata = [url_metadata]

        presence_flags = []
        protocol_onehots = []
        tld_onehots = []
        depth_onehots = []

        for um in url_metadata:
            is_valid = um.get('is_valid', False) if um else False
            presence_flags.append(1.0 if is_valid else 0.0)

            protocol = um.get('protocol', '').lower() if um else ''
            protocol_idx = 3
            for idx, (cat_name, cat_protocols) in enumerate(PROTOCOL_CATEGORIES.items()):
                if protocol in cat_protocols:
                    protocol_idx = idx
                    break
            protocol_oh = [0.0] * N_PROTOCOL_CATEGORIES
            protocol_oh[protocol_idx] = 1.0
            protocol_onehots.append(protocol_oh)

            tld = um.get('tld', '').lower() if um else ''
            tld_idx = 5
            for idx, (cat_name, cat_tlds) in enumerate(TLD_CATEGORIES.items()):
                if tld in cat_tlds:
                    tld_idx = idx
                    break
            tld_oh = [0.0] * N_TLD_CATEGORIES
            tld_oh[tld_idx] = 1.0
            tld_onehots.append(tld_oh)

            path = um.get('path', '/') if um else '/'
            depth = len([p for p in path.split('/') if p])
            depth_bucket = min(depth, 4)
            depth_oh = [0.0] * self.n_depth_buckets
            depth_oh[depth_bucket] = 1.0
            depth_onehots.append(depth_oh)

        device = next(self.parameters()).device
        presence = torch.tensor(presence_flags, device=device).unsqueeze(-1)
        protocol = torch.tensor(protocol_onehots, device=device)
        tld = torch.tensor(tld_onehots, device=device)
        depth = torch.tensor(depth_onehots, device=device)

        return presence, protocol, tld, depth

    def _extract_temporal_features(self, raw_timestamp: torch.Tensor) -> torch.Tensor:
        """Extract 37-dim temporal features from raw timestamp."""
        # Same extraction as set_timestamp_ops
        import math

        FEAT_HOURS = 2
        FEAT_DAY_OF_WEEK = 4
        FEAT_MONTH = 5
        FEAT_DAY_OF_MONTH = 3
        FEAT_DAY_OF_YEAR = 7

        hour = raw_timestamp[:, FEAT_HOURS]
        dow = raw_timestamp[:, FEAT_DAY_OF_WEEK]
        month = raw_timestamp[:, FEAT_MONTH]
        day_of_month = raw_timestamp[:, FEAT_DAY_OF_MONTH]
        day_of_year = raw_timestamp[:, FEAT_DAY_OF_YEAR]

        dow_idx = dow.round().long().clamp(0, 6)
        dow_onehot = F.one_hot(dow_idx, num_classes=7).float()

        hour_bucket = (hour.long() // 6).clamp(0, 3)
        hour_onehot = F.one_hot(hour_bucket, num_classes=4).float()

        month_idx = (month.round().long() - 1).clamp(0, 11)
        month_onehot = F.one_hot(month_idx, num_classes=12).float()

        is_weekend = (dow_idx >= 5).float().unsqueeze(-1)

        quarter_idx = (month_idx // 3).clamp(0, 3)
        quarter_onehot = F.one_hot(quarter_idx, num_classes=4).float()

        dom_bucket = ((day_of_month.round().long() - 1) // 7).clamp(0, 4)
        dom_onehot = F.one_hot(dom_bucket, num_classes=5).float()

        doy_bucket = ((day_of_year.round().long() - 1) // 92).clamp(0, 3)
        doy_onehot = F.one_hot(doy_bucket, num_classes=4).float()

        return torch.cat([
            dow_onehot,
            hour_onehot,
            month_onehot,
            is_weekend,
            quarter_onehot,
            dom_onehot,
            doy_onehot,
        ], dim=-1)

    def forward(
        self,
        url_embedding: torch.Tensor,
        timestamp_embedding: torch.Tensor,
        raw_timestamp: torch.Tensor,
        url_metadata: Optional[list] = None,
    ) -> torch.Tensor:
        batch_size = url_embedding.shape[0]

        # Extract temporal features
        temporal_features = self._extract_temporal_features(raw_timestamp)

        # Extract URL features
        if url_metadata is not None:
            presence, protocol, tld, depth = self._extract_url_features(url_metadata)
        else:
            device = url_embedding.device
            presence = torch.zeros(batch_size, 1, device=device)
            protocol = torch.zeros(batch_size, N_PROTOCOL_CATEGORIES, device=device)
            protocol[:, 3] = 1.0
            tld = torch.zeros(batch_size, N_TLD_CATEGORIES, device=device)
            tld[:, 5] = 1.0
            depth = torch.zeros(batch_size, self.n_depth_buckets, device=device)
            depth[:, 0] = 1.0

        # Feature 1: Protocol × Time
        protocol_enc = self.protocol_encoder(protocol)
        protocol_time = self.protocol_temporal(
            torch.cat([protocol_enc, temporal_features], dim=-1)
        )

        # Feature 2: TLD × Time
        tld_enc = self.tld_encoder(tld)
        tld_time = self.tld_temporal(
            torch.cat([tld_enc, temporal_features], dim=-1)
        )

        # Feature 3: Presence × Time
        presence_time = self.presence_temporal(
            torch.cat([presence, temporal_features], dim=-1)
        )

        # Feature 4: Depth × Time
        depth_enc = self.depth_encoder(depth)
        depth_time = self.depth_temporal(
            torch.cat([depth_enc, temporal_features], dim=-1)
        )

        # Symmetric
        symmetric = url_embedding * timestamp_embedding

        combined = torch.cat([
            protocol_time,
            tld_time,
            presence_time,
            depth_time,
            symmetric,
        ], dim=-1)

        return self.output_norm(self.fusion_mlp(combined))


class URLStringOps(nn.Module):
    """
    Type-aware operations for URL × Free String column pairs.

    Computes relationship embeddings that capture:
    - URL endpoint semantics × string content
    - Path tokens × string semantic similarity
    - Domain main part × string content

    Examples:
    - "URL path 'checkout' correlates with 'purchase' in description"
    - "Domain 'amazon.com' correlates with 'e-commerce' in text"
    """

    def __init__(
        self,
        d_model: int,
        config: Optional["TypeAwareOpsConfig"] = None,
    ):
        super().__init__()
        self.d_model = d_model
        self.config = config

        # Feature 1: URL semantics × String similarity
        # URL embedding already contains path/domain semantics
        self.url_string_similarity = nn.Sequential(
            nn.Linear(d_model * 2, d_model),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model, d_model),
        )

        # Feature 2: Protocol × String style
        self.protocol_encoder = nn.Sequential(
            nn.Linear(N_PROTOCOL_CATEGORIES, d_model // 4),
            nn.ReLU(),
            nn.Linear(d_model // 4, d_model),
        )

        self.protocol_string_mlp = nn.Sequential(
            nn.Linear(d_model * 2, d_model),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model, d_model),
        )

        # Feature 3: TLD × String topic
        self.tld_encoder = nn.Sequential(
            nn.Linear(N_TLD_CATEGORIES, d_model // 4),
            nn.ReLU(),
            nn.Linear(d_model // 4, d_model),
        )

        self.tld_string_mlp = nn.Sequential(
            nn.Linear(d_model * 2, d_model),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model, d_model),
        )

        # Feature 4: String → URL prediction
        self.string_url_predictor = nn.Sequential(
            nn.Linear(d_model, d_model // 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model // 2, d_model),
        )

        # Fusion: 4 features + symmetric = 5 * d_model
        self.fusion_mlp = nn.Sequential(
            nn.Linear(5 * d_model, d_model * 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model * 2, d_model),
        )

        self.output_norm = nn.LayerNorm(d_model)

        logger.debug(f"   URLStringOps initialized: d_model={d_model}")

    def _extract_url_features(self, url_metadata: list):
        if not isinstance(url_metadata, list):
            url_metadata = [url_metadata]

        protocol_onehots = []
        tld_onehots = []

        for um in url_metadata:
            protocol = um.get('protocol', '').lower() if um else ''
            protocol_idx = 3
            for idx, (cat_name, cat_protocols) in enumerate(PROTOCOL_CATEGORIES.items()):
                if protocol in cat_protocols:
                    protocol_idx = idx
                    break
            protocol_oh = [0.0] * N_PROTOCOL_CATEGORIES
            protocol_oh[protocol_idx] = 1.0
            protocol_onehots.append(protocol_oh)

            tld = um.get('tld', '').lower() if um else ''
            tld_idx = 5
            for idx, (cat_name, cat_tlds) in enumerate(TLD_CATEGORIES.items()):
                if tld in cat_tlds:
                    tld_idx = idx
                    break
            tld_oh = [0.0] * N_TLD_CATEGORIES
            tld_oh[tld_idx] = 1.0
            tld_onehots.append(tld_oh)

        device = next(self.parameters()).device
        protocol = torch.tensor(protocol_onehots, device=device)
        tld = torch.tensor(tld_onehots, device=device)

        return protocol, tld

    def forward(
        self,
        url_embedding: torch.Tensor,
        string_embedding: torch.Tensor,
        url_metadata: Optional[list] = None,
    ) -> torch.Tensor:
        batch_size = url_embedding.shape[0]

        if url_metadata is not None:
            protocol, tld = self._extract_url_features(url_metadata)
        else:
            device = url_embedding.device
            protocol = torch.zeros(batch_size, N_PROTOCOL_CATEGORIES, device=device)
            protocol[:, 3] = 1.0
            tld = torch.zeros(batch_size, N_TLD_CATEGORIES, device=device)
            tld[:, 5] = 1.0

        # Feature 1: URL × String similarity
        url_string_sim = self.url_string_similarity(
            torch.cat([url_embedding, string_embedding], dim=-1)
        )

        # Feature 2: Protocol × String
        protocol_enc = self.protocol_encoder(protocol)
        protocol_string = self.protocol_string_mlp(
            torch.cat([protocol_enc, string_embedding], dim=-1)
        )

        # Feature 3: TLD × String
        tld_enc = self.tld_encoder(tld)
        tld_string = self.tld_string_mlp(
            torch.cat([tld_enc, string_embedding], dim=-1)
        )

        # Feature 4: String → URL
        string_url_pred = self.string_url_predictor(string_embedding)

        # Symmetric
        symmetric = url_embedding * string_embedding

        combined = torch.cat([
            url_string_sim,
            protocol_string,
            tld_string,
            string_url_pred,
            symmetric,
        ], dim=-1)

        return self.output_norm(self.fusion_mlp(combined))
