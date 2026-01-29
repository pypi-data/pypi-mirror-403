#  -*- coding: utf-8 -*-
#
#  Copyright Featrix, Inc 2023-2025
#
#  Proprietary and Confidential. Unauthorized use, copying or dissemination
#  of these materials is strictly prohibited.
"""
Email/Domain Relationship Operations

Type-aware relationship operations for Email/Domain columns.
Includes:
- Email × Email: Same domain, both free, TLD matching, etc.
- Email/Domain × Set/Scalar/Timestamp/String: Cross-type relationships

Key Features:
1. Free/Corporate domain segmentation - binary split for B2B vs B2C
2. TLD category patterns - .edu, .gov, .io have distinct behaviors
3. Domain main embedding - company/org name semantics
4. Same-domain detection for Email × Email pairs
"""
import logging
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, TYPE_CHECKING

from featrix.neural.hubspot_free_domains_list_may_2025 import is_free_email_domain

if TYPE_CHECKING:
    from featrix.neural.type_aware_ops_config import TypeAwareOpsConfig

logger = logging.getLogger(__name__)

# TLD categories for one-hot encoding
TLD_CATEGORIES = {
    'generic': ['com', 'net', 'org', 'biz', 'info'],
    'country': ['uk', 'de', 'fr', 'ca', 'au', 'jp', 'cn', 'ru', 'br', 'in'],
    'education': ['edu'],
    'government': ['gov', 'mil'],
    'tech': ['io', 'ai', 'app', 'dev', 'tech', 'co'],
    'other': []  # Catch-all
}

# Number of TLD category one-hot dimensions
N_TLD_CATEGORIES = len(TLD_CATEGORIES)  # 6


class EmailEmailOps(nn.Module):
    """
    Type-aware operations for Email × Email column pairs.

    Features (14 total):
    - same_domain: Both emails share the same domain
    - same_tld: Both emails share the same TLD (.com, .edu, etc.)
    - same_tld_category: Both in same TLD category (generic, education, etc.)
    - both_free: Both are free email providers (gmail, yahoo, etc.)
    - both_corporate: Both are corporate/non-free email domains
    - lhs_free: Left email is free, right is not
    - rhs_free: Right email is free, left is not
    - same_domain_main: Domain main part matches (company name)
    - tld_a, tld_b: TLD category for each (normalized 0-1)
    - free_a, free_b: Free email indicator for each
    - domain_similarity: Learned domain semantic similarity

    Use cases:
    - Fraud detection: Multiple accounts with related email domains
    - User matching: Same person across systems
    - B2B analysis: Corporate vs personal email patterns
    """

    N_EMAIL_FEATURES = 14

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
            nn.Linear(self.N_EMAIL_FEATURES, d_model // 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model // 2, d_model),
        )

        # Embedding interaction (captures domain semantic similarity)
        self.interaction_mlp = nn.Sequential(
            nn.Linear(d_model * 3, d_model),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model, d_model),
        )

        # Domain alignment (for same-company detection)
        self.domain_alignment_mlp = nn.Sequential(
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

        logger.debug(f"   EmailEmailOps initialized: d_model={d_model}")

    def _get_tld_category_idx(self, tld: str) -> int:
        """Get TLD category index (0-5)."""
        tld = tld.lower()
        for idx, (cat_name, cat_tlds) in enumerate(TLD_CATEGORIES.items()):
            if tld in cat_tlds:
                return idx
        return 5  # 'other'

    def _is_free_domain(self, domain: str) -> bool:
        """Check if domain is a free email provider (uses Hubspot list)."""
        return is_free_email_domain(domain)

    def compute_email_features(
        self,
        metadata_a: list,
        metadata_b: list,
        device: torch.device,
    ) -> torch.Tensor:
        """
        Compute raw email comparison features.

        Args:
            metadata_a: List of email metadata dicts for column A
            metadata_b: List of email metadata dicts for column B
            device: Target device

        Returns:
            Features tensor (batch, N_EMAIL_FEATURES)
        """
        if not isinstance(metadata_a, list):
            metadata_a = [metadata_a]
        if not isinstance(metadata_b, list):
            metadata_b = [metadata_b]

        batch_size = len(metadata_a)
        features = []

        for ma, mb in zip(metadata_a, metadata_b):
            # Extract components
            domain_a = ma.get('domain', '') if ma else ''
            domain_b = mb.get('domain', '') if mb else ''
            tld_a = ma.get('tld', '') if ma else ''
            tld_b = mb.get('tld', '') if mb else ''
            domain_main_a = ma.get('domain_main', '') if ma else ''
            domain_main_b = mb.get('domain_main', '') if mb else ''
            is_free_a = ma.get('is_free_email_domain', False) if ma else self._is_free_domain(domain_a)
            is_free_b = mb.get('is_free_email_domain', False) if mb else self._is_free_domain(domain_b)

            # Compute features
            same_domain = float(domain_a.lower() == domain_b.lower() and domain_a != '')
            same_tld = float(tld_a.lower() == tld_b.lower() and tld_a != '')

            tld_cat_a = self._get_tld_category_idx(tld_a)
            tld_cat_b = self._get_tld_category_idx(tld_b)
            same_tld_category = float(tld_cat_a == tld_cat_b)

            both_free = float(is_free_a and is_free_b)
            both_corporate = float(not is_free_a and not is_free_b and domain_a != '' and domain_b != '')
            lhs_free = float(is_free_a and not is_free_b)
            rhs_free = float(not is_free_a and is_free_b)

            same_domain_main = float(
                domain_main_a.lower() == domain_main_b.lower()
                and domain_main_a != ''
            )

            # Normalized TLD categories (0-1)
            tld_a_norm = tld_cat_a / 5.0
            tld_b_norm = tld_cat_b / 5.0

            # Free indicators
            free_a_float = float(is_free_a)
            free_b_float = float(is_free_b)

            # Placeholder for embedding-based domain similarity (computed in forward)
            domain_sim_placeholder = 0.0

            features.append([
                same_domain,
                same_tld,
                same_tld_category,
                both_free,
                both_corporate,
                lhs_free,
                rhs_free,
                same_domain_main,
                tld_a_norm,
                tld_b_norm,
                free_a_float,
                free_b_float,
                domain_sim_placeholder,
                domain_sim_placeholder,  # Padding to 14
            ])

        return torch.tensor(features, device=device, dtype=torch.float32)

    def forward(
        self,
        email_embedding_a: torch.Tensor,  # (batch, d_model)
        email_embedding_b: torch.Tensor,  # (batch, d_model)
        metadata_a: Optional[list] = None,
        metadata_b: Optional[list] = None,
    ) -> torch.Tensor:
        """
        Compute relationship embedding for Email × Email pair.

        Args:
            email_embedding_a: Embedding from EmailEncoder for column A
            email_embedding_b: Embedding from EmailEncoder for column B
            metadata_a: List of email metadata dicts for A
            metadata_b: List of email metadata dicts for B

        Returns:
            Relationship embedding (batch, d_model)
        """
        batch_size = email_embedding_a.shape[0]
        device = email_embedding_a.device

        # Compute raw features
        if metadata_a is not None and metadata_b is not None:
            features = self.compute_email_features(metadata_a, metadata_b, device)
        else:
            features = torch.zeros(batch_size, self.N_EMAIL_FEATURES, device=device)

        # Process raw features
        feature_emb = self.feature_mlp(features)

        # Embedding interaction (captures learned domain similarity)
        interaction = self.interaction_mlp(torch.cat([
            email_embedding_a,
            email_embedding_b,
            email_embedding_a * email_embedding_b,
        ], dim=-1))

        # Domain alignment
        alignment = self.domain_alignment_mlp(torch.cat([
            email_embedding_a,
            email_embedding_b,
        ], dim=-1))

        # Fusion
        combined = torch.cat([feature_emb, interaction, alignment], dim=-1)
        return self.output_norm(self.fusion_mlp(combined))


class EmailDomainOps(nn.Module):
    """
    Type-aware operations for Email × Domain column pairs.

    Features (12 total):
    - same_domain: Email's domain matches the domain column exactly
    - same_domain_main: Domain main parts match (e.g., email@acme.com vs acme.org)
    - same_tld: TLDs match
    - same_tld_category: TLD categories match (generic, education, etc.)
    - email_is_free: Email is from free provider (gmail, yahoo)
    - domain_is_free: Domain is a free email provider domain
    - both_free: Both are free email provider domains
    - both_corporate: Both are corporate/non-free domains
    - tld_email_norm: Email's TLD category (normalized)
    - tld_domain_norm: Domain's TLD category (normalized)
    - subdomain_present: Domain has a subdomain (www, mail, etc.)
    - domain_similarity: Learned semantic similarity from embeddings

    Use cases:
    - CRM: Match contact email to company domain
    - Fraud: Verify email belongs to claimed company domain
    - Data enrichment: Link email addresses to organization domains
    """

    N_FEATURES = 12

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
            nn.Linear(self.N_FEATURES, d_model // 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model // 2, d_model),
        )

        # Embedding interaction (captures domain semantic similarity)
        self.interaction_mlp = nn.Sequential(
            nn.Linear(d_model * 3, d_model),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model, d_model),
        )

        # Domain alignment (for same-company detection)
        self.domain_alignment_mlp = nn.Sequential(
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

        logger.debug(f"   EmailDomainOps initialized: d_model={d_model}")

    def _get_tld_category_idx(self, tld: str) -> int:
        """Get TLD category index (0-5)."""
        tld = tld.lower() if tld else ''
        for idx, (cat_name, cat_tlds) in enumerate(TLD_CATEGORIES.items()):
            if tld in cat_tlds:
                return idx
        return 5  # 'other'

    def compute_features(
        self,
        email_metadata: list,
        domain_metadata: list,
        device: torch.device,
    ) -> torch.Tensor:
        """
        Compute raw Email × Domain comparison features.

        Args:
            email_metadata: List of email metadata dicts (from EmailCodec)
            domain_metadata: List of domain metadata dicts (from DomainCodec)
            device: Target device

        Returns:
            Features tensor (batch, N_FEATURES)
        """
        if not isinstance(email_metadata, list):
            email_metadata = [email_metadata]
        if not isinstance(domain_metadata, list):
            domain_metadata = [domain_metadata]

        batch_size = len(email_metadata)
        features = []

        for em, dm in zip(email_metadata, domain_metadata):
            # Extract email components
            email_domain_main = em.get('domain_main', '') if em else ''
            email_tld = em.get('tld', '') if em else ''
            email_is_free = em.get('is_free_email_domain', False) if em else False
            email_full_domain = f"{email_domain_main}.{email_tld}" if email_domain_main and email_tld else ''

            # Extract domain components
            domain_subdomain = dm.get('subdomain', '') if dm else ''
            domain_main = dm.get('domain_main', '') if dm else ''
            domain_tld = dm.get('tld', '') if dm else ''
            domain_is_free = dm.get('is_free_email_domain', False) if dm else False
            domain_full = f"{domain_main}.{domain_tld}" if domain_main and domain_tld else ''

            # Compute features
            # 1. Exact domain match (email's domain == domain column)
            same_domain = float(
                email_full_domain.lower() == domain_full.lower()
                and email_full_domain != ''
            )

            # 2. Domain main match (company name match, ignoring TLD)
            same_domain_main = float(
                email_domain_main.lower() == domain_main.lower()
                and email_domain_main != ''
            )

            # 3. TLD match
            same_tld = float(
                email_tld.lower() == domain_tld.lower()
                and email_tld != ''
            )

            # 4. TLD category match
            tld_cat_email = self._get_tld_category_idx(email_tld)
            tld_cat_domain = self._get_tld_category_idx(domain_tld)
            same_tld_category = float(tld_cat_email == tld_cat_domain)

            # 5-8. Free/corporate indicators
            email_is_free_float = float(email_is_free)
            domain_is_free_float = float(domain_is_free)
            both_free = float(email_is_free and domain_is_free)
            both_corporate = float(
                not email_is_free and not domain_is_free
                and email_full_domain != '' and domain_full != ''
            )

            # 9-10. Normalized TLD categories
            tld_email_norm = tld_cat_email / 5.0
            tld_domain_norm = tld_cat_domain / 5.0

            # 11. Subdomain present indicator
            subdomain_present = float(domain_subdomain != '')

            # 12. Placeholder for embedding-based similarity (computed in forward)
            domain_similarity_placeholder = 0.0

            features.append([
                same_domain,
                same_domain_main,
                same_tld,
                same_tld_category,
                email_is_free_float,
                domain_is_free_float,
                both_free,
                both_corporate,
                tld_email_norm,
                tld_domain_norm,
                subdomain_present,
                domain_similarity_placeholder,
            ])

        return torch.tensor(features, device=device, dtype=torch.float32)

    def forward(
        self,
        email_embedding: torch.Tensor,  # (batch, d_model)
        domain_embedding: torch.Tensor,  # (batch, d_model)
        email_metadata: Optional[list] = None,
        domain_metadata: Optional[list] = None,
    ) -> torch.Tensor:
        """
        Compute relationship embedding for Email × Domain pair.

        Args:
            email_embedding: Embedding from EmailEncoder
            domain_embedding: Embedding from DomainEncoder
            email_metadata: List of email metadata dicts
            domain_metadata: List of domain metadata dicts

        Returns:
            Relationship embedding (batch, d_model)
        """
        batch_size = email_embedding.shape[0]
        device = email_embedding.device

        # Compute raw features
        if email_metadata is not None and domain_metadata is not None:
            features = self.compute_features(email_metadata, domain_metadata, device)
        else:
            features = torch.zeros(batch_size, self.N_FEATURES, device=device)

        # Process raw features
        feature_emb = self.feature_mlp(features)

        # Embedding interaction (captures learned domain similarity)
        interaction = self.interaction_mlp(torch.cat([
            email_embedding,
            domain_embedding,
            email_embedding * domain_embedding,
        ], dim=-1))

        # Domain alignment
        alignment = self.domain_alignment_mlp(torch.cat([
            email_embedding,
            domain_embedding,
        ], dim=-1))

        # Fusion
        combined = torch.cat([feature_emb, interaction, alignment], dim=-1)
        return self.output_norm(self.fusion_mlp(combined))


class EmailDomainSetOps(nn.Module):
    """
    Type-aware operations for Email/Domain × Set column pairs.

    Computes relationship embeddings that capture:
    - Free vs corporate domain patterns per set category
    - TLD category × set value correlations
    - Domain name semantics × set value associations
    """

    def __init__(
        self,
        d_model: int,
        config: Optional["TypeAwareOpsConfig"] = None,
    ):
        """
        Args:
            d_model: Model dimension
            config: TypeAwareOpsConfig for granular feature control
        """
        super().__init__()
        self.d_model = d_model
        self.config = config

        # ============================================================================
        # Feature 1: Free/Corporate Domain Gating
        # ============================================================================
        # Binary feature that gates set embedding based on domain type
        # This is critical for B2B vs B2C segmentation
        self.free_domain_gate = nn.Sequential(
            nn.Linear(1, d_model // 4),
            nn.ReLU(),
            nn.Linear(d_model // 4, d_model),
        )

        # ============================================================================
        # Feature 2: TLD Category Interaction
        # ============================================================================
        # TLD category (edu, gov, tech, etc.) interacts with set value
        # 6 TLD categories → embedding
        self.tld_category_encoder = nn.Sequential(
            nn.Linear(N_TLD_CATEGORIES, d_model // 4),
            nn.ReLU(),
            nn.Linear(d_model // 4, d_model),
        )

        # TLD × Set interaction MLP
        self.tld_set_interaction = nn.Sequential(
            nn.Linear(d_model * 2, d_model),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model, d_model),
        )

        # ============================================================================
        # Feature 3: Domain Semantics × Set
        # ============================================================================
        # Domain embedding carries company/org semantics that may correlate with set values
        self.domain_set_mlp = nn.Sequential(
            nn.Linear(d_model * 2, d_model),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model, d_model),
        )

        # ============================================================================
        # Feature 4: Set → Domain Direction (predict domain category from set)
        # ============================================================================
        # "Given this set value, what type of domain is likely?"
        self.set_domain_predictor = nn.Sequential(
            nn.Linear(d_model, d_model // 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model // 2, d_model),
        )

        # ============================================================================
        # Fusion: Combine all features
        # ============================================================================
        # gated_set + tld_set + domain_set + set_domain_pred + symmetric = 5 * d_model
        self.fusion_mlp = nn.Sequential(
            nn.Linear(5 * d_model, d_model * 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model * 2, d_model),
        )

        # Output normalization
        self.output_norm = nn.LayerNorm(d_model)

        logger.debug(f"   EmailDomainSetOps initialized: d_model={d_model}")

    def _extract_domain_features(
        self,
        domain_metadata: dict,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """
        Extract features from domain metadata.

        Args:
            domain_metadata: Dict with is_free_email_domain, tld, tld_type

        Returns:
            free_flag: (batch, 1) binary free email domain flag
            tld_onehot: (batch, N_TLD_CATEGORIES) TLD category one-hot
        """
        batch_size = len(domain_metadata) if isinstance(domain_metadata, list) else 1

        if not isinstance(domain_metadata, list):
            domain_metadata = [domain_metadata]

        free_flags = []
        tld_onehots = []

        for dm in domain_metadata:
            # Free email domain flag
            is_free = dm.get('is_free_email_domain', False) if dm else False
            free_flags.append(1.0 if is_free else 0.0)

            # TLD category one-hot
            tld = dm.get('tld', '').lower() if dm else ''
            tld_cat_idx = 5  # Default to 'other'

            for idx, (cat_name, cat_tlds) in enumerate(TLD_CATEGORIES.items()):
                if tld in cat_tlds:
                    tld_cat_idx = idx
                    break

            onehot = [0.0] * N_TLD_CATEGORIES
            onehot[tld_cat_idx] = 1.0
            tld_onehots.append(onehot)

        # Convert to tensors
        device = next(self.parameters()).device
        free_flag = torch.tensor(free_flags, device=device).unsqueeze(-1)  # (batch, 1)
        tld_onehot = torch.tensor(tld_onehots, device=device)  # (batch, 6)

        return free_flag, tld_onehot

    def forward(
        self,
        domain_embedding: torch.Tensor,    # (batch, d_model) - encoded domain column
        set_embedding: torch.Tensor,       # (batch, d_model) - encoded set column
        domain_metadata: Optional[list] = None,  # List of domain metadata dicts
    ) -> torch.Tensor:
        """
        Compute relationship embedding for Email/Domain × Set pair.

        Captures BIDIRECTIONAL relationships:
        - Domain→Set: "gmail users tend to be in 'consumer' segment"
        - Set→Domain: "enterprise customers tend to have corporate domains"

        Args:
            domain_embedding: Embedding from DomainEncoder (batch, d_model)
            set_embedding: Embedding from SetEncoder (batch, d_model)
            domain_metadata: List of dicts with domain components (is_free_email_domain, tld, etc.)

        Returns:
            Relationship embedding of shape (batch, d_model)
        """
        batch_size = domain_embedding.shape[0]

        # Extract domain features if metadata provided
        if domain_metadata is not None:
            free_flag, tld_onehot = self._extract_domain_features(domain_metadata)
        else:
            # Fallback: use zeros if no metadata
            device = domain_embedding.device
            free_flag = torch.zeros(batch_size, 1, device=device)
            tld_onehot = torch.zeros(batch_size, N_TLD_CATEGORIES, device=device)
            tld_onehot[:, 5] = 1.0  # Default to 'other'

        # ============================================================================
        # Feature 1: Free/Corporate Domain Gating (Domain→Set direction)
        # ============================================================================
        # Free email domains (gmail, yahoo) vs corporate domains behave differently
        free_gate = self.free_domain_gate(free_flag)  # (batch, d_model)
        gated_set = set_embedding * torch.sigmoid(free_gate)

        # ============================================================================
        # Feature 2: TLD Category × Set Interaction
        # ============================================================================
        tld_encoding = self.tld_category_encoder(tld_onehot)  # (batch, d_model)
        tld_set = self.tld_set_interaction(
            torch.cat([tld_encoding, set_embedding], dim=-1)
        )

        # ============================================================================
        # Feature 3: Domain Semantics × Set
        # ============================================================================
        # Domain embedding contains company/org name semantics
        domain_set = self.domain_set_mlp(
            torch.cat([domain_embedding, set_embedding], dim=-1)
        )

        # ============================================================================
        # Feature 4: Set → Domain Prediction (Set→Domain direction)
        # ============================================================================
        # "Given this set value, predict domain characteristics"
        set_domain_pred = self.set_domain_predictor(set_embedding)

        # ============================================================================
        # Symmetric product (always included)
        # ============================================================================
        symmetric = domain_embedding * set_embedding

        # ============================================================================
        # Fusion: Combine all features (5 total)
        # ============================================================================
        combined = torch.cat([
            gated_set,         # Domain→Set: free/corporate gates set
            tld_set,           # Domain→Set: TLD category × set
            domain_set,        # Bidirectional: domain semantics × set
            set_domain_pred,   # Set→Domain: set predicts domain type
            symmetric,         # Generic: embedding product
        ], dim=-1)  # (batch, 5 * d_model)

        return self.output_norm(self.fusion_mlp(combined))


class EmailDomainScalarOps(nn.Module):
    """
    Type-aware operations for Email/Domain × Scalar column pairs.

    Computes relationship embeddings that capture:
    - Free vs corporate domain effect on scalar values
    - TLD category × scalar correlations (edu has lower price, etc.)
    - Domain semantics × scalar relationships
    """

    def __init__(
        self,
        d_model: int,
        config: Optional["TypeAwareOpsConfig"] = None,
    ):
        """
        Args:
            d_model: Model dimension
            config: TypeAwareOpsConfig for granular feature control
        """
        super().__init__()
        self.d_model = d_model
        self.config = config

        # ============================================================================
        # Feature 1: Free/Corporate Domain Effect on Scalar
        # ============================================================================
        # Free email domains may have different average values than corporate
        self.free_domain_scalar_mlp = nn.Sequential(
            nn.Linear(d_model + 1, d_model),  # scalar embedding + free flag
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model, d_model),
        )

        # ============================================================================
        # Feature 2: TLD Category × Scalar
        # ============================================================================
        # Different TLDs have different typical scalar values
        self.tld_category_encoder = nn.Sequential(
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

        # ============================================================================
        # Feature 3: Domain Semantics × Scalar
        # ============================================================================
        self.domain_scalar_mlp = nn.Sequential(
            nn.Linear(d_model * 2, d_model),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model, d_model),
        )

        # ============================================================================
        # Feature 4: Scalar → Domain Direction
        # ============================================================================
        # "Given this scalar value, what domain type is likely?"
        # e.g., high order value → corporate domain
        self.scalar_domain_predictor = nn.Sequential(
            nn.Linear(d_model, d_model // 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model // 2, d_model),
        )

        # ============================================================================
        # Fusion: Combine all features
        # ============================================================================
        # free_scalar + tld_scalar + domain_scalar + scalar_domain_pred + symmetric = 5 * d_model
        self.fusion_mlp = nn.Sequential(
            nn.Linear(5 * d_model, d_model * 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model * 2, d_model),
        )

        # Output normalization
        self.output_norm = nn.LayerNorm(d_model)

        logger.debug(f"   EmailDomainScalarOps initialized: d_model={d_model}")

    def _extract_domain_features(
        self,
        domain_metadata: dict,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Extract features from domain metadata."""
        batch_size = len(domain_metadata) if isinstance(domain_metadata, list) else 1

        if not isinstance(domain_metadata, list):
            domain_metadata = [domain_metadata]

        free_flags = []
        tld_onehots = []

        for dm in domain_metadata:
            # Free email domain flag
            is_free = dm.get('is_free_email_domain', False) if dm else False
            free_flags.append(1.0 if is_free else 0.0)

            # TLD category one-hot
            tld = dm.get('tld', '').lower() if dm else ''
            tld_cat_idx = 5  # Default to 'other'

            for idx, (cat_name, cat_tlds) in enumerate(TLD_CATEGORIES.items()):
                if tld in cat_tlds:
                    tld_cat_idx = idx
                    break

            onehot = [0.0] * N_TLD_CATEGORIES
            onehot[tld_cat_idx] = 1.0
            tld_onehots.append(onehot)

        device = next(self.parameters()).device
        free_flag = torch.tensor(free_flags, device=device).unsqueeze(-1)
        tld_onehot = torch.tensor(tld_onehots, device=device)

        return free_flag, tld_onehot

    def forward(
        self,
        domain_embedding: torch.Tensor,    # (batch, d_model) - encoded domain column
        scalar_embedding: torch.Tensor,    # (batch, d_model) - encoded scalar column
        domain_metadata: Optional[list] = None,
    ) -> torch.Tensor:
        """
        Compute relationship embedding for Email/Domain × Scalar pair.

        Captures BIDIRECTIONAL relationships:
        - Domain→Scalar: "free email users have lower order values"
        - Scalar→Domain: "high value orders predict corporate domains"

        Args:
            domain_embedding: Embedding from DomainEncoder (batch, d_model)
            scalar_embedding: Embedding from ScalarEncoder (batch, d_model)
            domain_metadata: List of dicts with domain components

        Returns:
            Relationship embedding of shape (batch, d_model)
        """
        batch_size = domain_embedding.shape[0]

        # Extract domain features
        if domain_metadata is not None:
            free_flag, tld_onehot = self._extract_domain_features(domain_metadata)
        else:
            device = domain_embedding.device
            free_flag = torch.zeros(batch_size, 1, device=device)
            tld_onehot = torch.zeros(batch_size, N_TLD_CATEGORIES, device=device)
            tld_onehot[:, 5] = 1.0

        # ============================================================================
        # Feature 1: Free/Corporate Domain Effect on Scalar
        # ============================================================================
        free_scalar = self.free_domain_scalar_mlp(
            torch.cat([scalar_embedding, free_flag], dim=-1)
        )

        # ============================================================================
        # Feature 2: TLD Category × Scalar
        # ============================================================================
        tld_encoding = self.tld_category_encoder(tld_onehot)
        tld_scalar = self.tld_scalar_interaction(
            torch.cat([tld_encoding, scalar_embedding], dim=-1)
        )

        # ============================================================================
        # Feature 3: Domain Semantics × Scalar
        # ============================================================================
        domain_scalar = self.domain_scalar_mlp(
            torch.cat([domain_embedding, scalar_embedding], dim=-1)
        )

        # ============================================================================
        # Feature 4: Scalar → Domain Prediction
        # ============================================================================
        scalar_domain_pred = self.scalar_domain_predictor(scalar_embedding)

        # ============================================================================
        # Symmetric product
        # ============================================================================
        symmetric = domain_embedding * scalar_embedding

        # ============================================================================
        # Fusion
        # ============================================================================
        combined = torch.cat([
            free_scalar,          # Domain→Scalar: free/corporate effect
            tld_scalar,           # Domain→Scalar: TLD category effect
            domain_scalar,        # Bidirectional: domain semantics × scalar
            scalar_domain_pred,   # Scalar→Domain: scalar predicts domain type
            symmetric,            # Generic: embedding product
        ], dim=-1)

        return self.output_norm(self.fusion_mlp(combined))


class EmailDomainTimestampOps(nn.Module):
    """
    Type-aware operations for Email/Domain × Timestamp column pairs.

    Computes relationship embeddings that capture:
    - Free vs corporate domains at different times (business hours vs weekend)
    - TLD category temporal patterns (.edu during school year, etc.)
    """

    def __init__(
        self,
        d_model: int,
        config: Optional["TypeAwareOpsConfig"] = None,
    ):
        super().__init__()
        self.d_model = d_model
        self.config = config

        # Temporal features: 28 dims (same as ScalarTimestampOps)
        self.n_temporal_features = 28

        # ============================================================================
        # Feature 1: Free/Corporate × Time Pattern
        # ============================================================================
        # Corporate domains might be more active during business hours
        self.free_temporal_mlp = nn.Sequential(
            nn.Linear(self.n_temporal_features + 1, d_model // 2),  # +1 for free flag
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model // 2, d_model),
        )

        # ============================================================================
        # Feature 2: TLD Category × Time Pattern
        # ============================================================================
        self.tld_temporal_mlp = nn.Sequential(
            nn.Linear(self.n_temporal_features + N_TLD_CATEGORIES, d_model // 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model // 2, d_model),
        )

        # ============================================================================
        # Feature 3: Domain × Timestamp embedding interaction
        # ============================================================================
        self.domain_timestamp_mlp = nn.Sequential(
            nn.Linear(d_model * 2, d_model),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model, d_model),
        )

        # ============================================================================
        # Fusion
        # ============================================================================
        self.fusion_mlp = nn.Sequential(
            nn.Linear(4 * d_model, d_model * 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model * 2, d_model),
        )

        self.output_norm = nn.LayerNorm(d_model)

        logger.debug(f"   EmailDomainTimestampOps initialized: d_model={d_model}")

    def _extract_temporal_features(
        self,
        raw_timestamp: torch.Tensor,
    ) -> torch.Tensor:
        """Extract 28-dim temporal features from raw timestamp."""
        import math

        # Feature indices
        FEAT_HOURS = 2
        FEAT_DAY_OF_WEEK = 4
        FEAT_MONTH = 5

        hour = raw_timestamp[:, FEAT_HOURS]
        dow = raw_timestamp[:, FEAT_DAY_OF_WEEK]
        month = raw_timestamp[:, FEAT_MONTH]

        # Hour bucket: 4 one-hot
        hour_bucket = (hour.long() // 6).clamp(0, 3)
        hour_onehot = F.one_hot(hour_bucket, num_classes=4).float()

        # Day of week: 7 one-hot
        dow_idx = dow.round().long().clamp(0, 6)
        dow_onehot = F.one_hot(dow_idx, num_classes=7).float()

        # Month: 12 one-hot
        month_idx = (month.round().long() - 1).clamp(0, 11)
        month_onehot = F.one_hot(month_idx, num_classes=12).float()

        # Weekend: 1 binary
        is_weekend = (dow_idx >= 5).float().unsqueeze(-1)

        # Quarter: 4 one-hot
        quarter_idx = (month_idx // 3).clamp(0, 3)
        quarter_onehot = F.one_hot(quarter_idx, num_classes=4).float()

        # Combine: 7 + 4 + 12 + 1 + 4 = 28
        temporal_features = torch.cat([
            dow_onehot,
            hour_onehot,
            month_onehot,
            is_weekend,
            quarter_onehot,
        ], dim=-1)

        return temporal_features

    def _extract_domain_features(self, domain_metadata: list) -> tuple[torch.Tensor, torch.Tensor]:
        """Extract free flag and TLD onehot from domain metadata."""
        if not isinstance(domain_metadata, list):
            domain_metadata = [domain_metadata]

        free_flags = []
        tld_onehots = []

        for dm in domain_metadata:
            is_free = dm.get('is_free_email_domain', False) if dm else False
            free_flags.append(1.0 if is_free else 0.0)

            tld = dm.get('tld', '').lower() if dm else ''
            tld_cat_idx = 5
            for idx, (cat_name, cat_tlds) in enumerate(TLD_CATEGORIES.items()):
                if tld in cat_tlds:
                    tld_cat_idx = idx
                    break

            onehot = [0.0] * N_TLD_CATEGORIES
            onehot[tld_cat_idx] = 1.0
            tld_onehots.append(onehot)

        device = next(self.parameters()).device
        free_flag = torch.tensor(free_flags, device=device).unsqueeze(-1)
        tld_onehot = torch.tensor(tld_onehots, device=device)

        return free_flag, tld_onehot

    def forward(
        self,
        domain_embedding: torch.Tensor,
        timestamp_embedding: torch.Tensor,
        raw_timestamp: torch.Tensor,
        domain_metadata: Optional[list] = None,
    ) -> torch.Tensor:
        """
        Compute relationship embedding for Email/Domain × Timestamp pair.

        Args:
            domain_embedding: (batch, d_model)
            timestamp_embedding: (batch, d_model)
            raw_timestamp: (batch, 12) raw timestamp features
            domain_metadata: List of domain component dicts

        Returns:
            Relationship embedding (batch, d_model)
        """
        batch_size = domain_embedding.shape[0]

        # Extract features
        temporal_features = self._extract_temporal_features(raw_timestamp)

        if domain_metadata is not None:
            free_flag, tld_onehot = self._extract_domain_features(domain_metadata)
        else:
            device = domain_embedding.device
            free_flag = torch.zeros(batch_size, 1, device=device)
            tld_onehot = torch.zeros(batch_size, N_TLD_CATEGORIES, device=device)
            tld_onehot[:, 5] = 1.0

        # ============================================================================
        # Feature 1: Free/Corporate × Time Pattern
        # ============================================================================
        free_temporal = self.free_temporal_mlp(
            torch.cat([temporal_features, free_flag], dim=-1)
        )

        # ============================================================================
        # Feature 2: TLD × Time Pattern
        # ============================================================================
        tld_temporal = self.tld_temporal_mlp(
            torch.cat([temporal_features, tld_onehot], dim=-1)
        )

        # ============================================================================
        # Feature 3: Domain × Timestamp embedding interaction
        # ============================================================================
        domain_timestamp = self.domain_timestamp_mlp(
            torch.cat([domain_embedding, timestamp_embedding], dim=-1)
        )

        # ============================================================================
        # Symmetric
        # ============================================================================
        symmetric = domain_embedding * timestamp_embedding

        # ============================================================================
        # Fusion
        # ============================================================================
        combined = torch.cat([
            free_temporal,
            tld_temporal,
            domain_timestamp,
            symmetric,
        ], dim=-1)

        return self.output_norm(self.fusion_mlp(combined))


class EmailDomainStringOps(nn.Module):
    """
    Type-aware operations for Email/Domain × Free String column pairs.

    Computes relationship embeddings that capture semantic similarity between:
    - Domain main part (company/org name) and free string content
    - TLD semantics and string content (e.g., ".edu" domain → academic text)

    Examples:
    - "company name 'google' in domain correlates with 'search' in description"
    - "domain 'harvard.edu' correlates with 'research' in notes"
    - "corporate domain correlates with 'enterprise', 'business' in text"
    """

    def __init__(
        self,
        d_model: int,
        config: Optional["TypeAwareOpsConfig"] = None,
    ):
        """
        Args:
            d_model: Model dimension
            config: TypeAwareOpsConfig for granular feature control
        """
        super().__init__()
        self.d_model = d_model
        self.config = config

        # ============================================================================
        # Feature 1: Domain Main Part × String Semantic Similarity
        # ============================================================================
        # Domain main part (company/org name) has semantic meaning
        # Compare with string column for entity/topic overlap
        self.domain_string_similarity = nn.Sequential(
            nn.Linear(d_model * 2, d_model),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model, d_model),
        )

        # ============================================================================
        # Feature 2: Free/Corporate × String Style
        # ============================================================================
        # Free email domains may correlate with informal text
        # Corporate domains may correlate with professional text
        self.free_string_mlp = nn.Sequential(
            nn.Linear(d_model + 1, d_model // 2),  # +1 for free flag
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model // 2, d_model),
        )

        # ============================================================================
        # Feature 3: TLD Category × String Topic
        # ============================================================================
        # .edu domains correlate with academic text
        # .gov domains correlate with official/policy text
        # .io/.tech domains correlate with technical text
        self.tld_category_encoder = nn.Sequential(
            nn.Linear(N_TLD_CATEGORIES, d_model // 4),
            nn.ReLU(),
            nn.Linear(d_model // 4, d_model),
        )

        self.tld_string_interaction = nn.Sequential(
            nn.Linear(d_model * 2, d_model),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model, d_model),
        )

        # ============================================================================
        # Feature 4: String → Domain Prediction
        # ============================================================================
        # "Given this string content, what domain type is likely?"
        # e.g., "technical jargon" → likely .io/.tech domain
        self.string_domain_predictor = nn.Sequential(
            nn.Linear(d_model, d_model // 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model // 2, d_model),
        )

        # ============================================================================
        # Fusion: Combine all features
        # ============================================================================
        # similarity + free_string + tld_string + string_pred + symmetric = 5 * d_model
        self.fusion_mlp = nn.Sequential(
            nn.Linear(5 * d_model, d_model * 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(d_model * 2, d_model),
        )

        # Output normalization
        self.output_norm = nn.LayerNorm(d_model)

        logger.debug(f"   EmailDomainStringOps initialized: d_model={d_model}")

    def _extract_domain_features(
        self,
        domain_metadata: list,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Extract features from domain metadata."""
        if not isinstance(domain_metadata, list):
            domain_metadata = [domain_metadata]

        free_flags = []
        tld_onehots = []

        for dm in domain_metadata:
            # Free email domain flag
            is_free = dm.get('is_free_email_domain', False) if dm else False
            free_flags.append(1.0 if is_free else 0.0)

            # TLD category one-hot
            tld = dm.get('tld', '').lower() if dm else ''
            tld_cat_idx = 5  # Default to 'other'

            for idx, (cat_name, cat_tlds) in enumerate(TLD_CATEGORIES.items()):
                if tld in cat_tlds:
                    tld_cat_idx = idx
                    break

            onehot = [0.0] * N_TLD_CATEGORIES
            onehot[tld_cat_idx] = 1.0
            tld_onehots.append(onehot)

        device = next(self.parameters()).device
        free_flag = torch.tensor(free_flags, device=device).unsqueeze(-1)
        tld_onehot = torch.tensor(tld_onehots, device=device)

        return free_flag, tld_onehot

    def forward(
        self,
        domain_embedding: torch.Tensor,    # (batch, d_model) - encoded domain column
        string_embedding: torch.Tensor,    # (batch, d_model) - encoded string column
        domain_metadata: Optional[list] = None,
    ) -> torch.Tensor:
        """
        Compute relationship embedding for Email/Domain × Free String pair.

        The domain embedding contains semantic information about the domain main part
        (company/org name) which can be compared with free string content.

        Captures BIDIRECTIONAL relationships:
        - Domain→String: "google.com domain correlates with 'search' in text"
        - String→Domain: "academic text predicts .edu domain"

        Args:
            domain_embedding: Embedding from DomainEncoder (batch, d_model)
                Contains: subdomain + domain_main + tld semantics
            string_embedding: Embedding from StringEncoder (batch, d_model)
            domain_metadata: List of dicts with domain components

        Returns:
            Relationship embedding of shape (batch, d_model)
        """
        batch_size = domain_embedding.shape[0]

        # Extract domain features
        if domain_metadata is not None:
            free_flag, tld_onehot = self._extract_domain_features(domain_metadata)
        else:
            device = domain_embedding.device
            free_flag = torch.zeros(batch_size, 1, device=device)
            tld_onehot = torch.zeros(batch_size, N_TLD_CATEGORIES, device=device)
            tld_onehot[:, 5] = 1.0

        # ============================================================================
        # Feature 1: Domain Main Part × String Semantic Similarity
        # ============================================================================
        # Domain embedding contains domain_main semantics (company/org name)
        # Compare with string embedding for entity/topic overlap
        domain_string_sim = self.domain_string_similarity(
            torch.cat([domain_embedding, string_embedding], dim=-1)
        )

        # ============================================================================
        # Feature 2: Free/Corporate × String Style
        # ============================================================================
        free_string = self.free_string_mlp(
            torch.cat([string_embedding, free_flag], dim=-1)
        )

        # ============================================================================
        # Feature 3: TLD Category × String Topic
        # ============================================================================
        tld_encoding = self.tld_category_encoder(tld_onehot)
        tld_string = self.tld_string_interaction(
            torch.cat([tld_encoding, string_embedding], dim=-1)
        )

        # ============================================================================
        # Feature 4: String → Domain Prediction
        # ============================================================================
        string_domain_pred = self.string_domain_predictor(string_embedding)

        # ============================================================================
        # Symmetric product
        # ============================================================================
        symmetric = domain_embedding * string_embedding

        # ============================================================================
        # Fusion
        # ============================================================================
        combined = torch.cat([
            domain_string_sim,    # Domain→String: semantic similarity
            free_string,          # Domain→String: free/corporate style
            tld_string,           # Domain→String: TLD topic correlation
            string_domain_pred,   # String→Domain: string predicts domain
            symmetric,            # Generic: embedding product
        ], dim=-1)

        return self.output_norm(self.fusion_mlp(combined))
