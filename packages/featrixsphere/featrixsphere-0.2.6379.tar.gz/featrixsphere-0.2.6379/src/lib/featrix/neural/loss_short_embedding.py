#!/usr/bin/env python3
"""
Short Embedding Loss Functions

Loss functions specifically for 3D short embeddings to prevent collapse.
These are critical because 3D space is much more constrained than 256D space,
and without proper regularization, embeddings collapse to a single point.

Feature flags (in sphere_config):
- enable_short_uniformity_loss: Log-sum-exp uniformity (Wang & Isola 2020)
- enable_short_diversity_loss: Per-dimension std enforcement
- enable_short_repulsion_loss: Pairwise repulsion for points too close
- enable_short_spread_loss: Bounding box coverage on sphere
- enable_short_cap_overlap_loss: Spherical cap overlap for label separation (requires labels)
"""

import logging
import torch
import torch.nn.functional as F
from typing import Dict, Tuple, Optional

logger = logging.getLogger(__name__)


def compute_short_uniformity_loss(
    short_embeddings: torch.Tensor,
    temperature: float = 2.0,
) -> Tuple[torch.Tensor, Dict]:
    """
    Compute uniformity loss for short embeddings on unit sphere.

    Uses log-sum-exp of pairwise distances (Wang & Isola 2020).
    Lower loss = more uniform distribution on sphere surface.

    Args:
        short_embeddings: (B, 3) tensor of L2-normalized short embeddings
        temperature: Temperature parameter for distance weighting

    Returns:
        loss: Scalar tensor
        metrics: Dict with diagnostic info
    """
    device = short_embeddings.device

    # Ensure normalized
    short_emb = F.normalize(short_embeddings, dim=1, eps=1e-8)  # (B, 3)
    B = short_emb.shape[0]

    if B < 2:
        return torch.tensor(0.0, device=device), {"n_samples": B}

    # Pairwise squared Euclidean distances
    # ||a - b||^2 = ||a||^2 + ||b||^2 - 2*a.b = 2 - 2*a.b (for unit vectors)
    pairwise_sim = short_emb @ short_emb.T  # (B, B)
    pairwise_dist_sq = 2.0 - 2.0 * pairwise_sim  # (B, B)

    # Mask out diagonal (self-similarity)
    mask = ~torch.eye(B, dtype=torch.bool, device=device)
    pairwise_dist_sq_offdiag = pairwise_dist_sq[mask].view(B, B - 1)

    # Log-sum-exp for numerical stability
    # This penalizes points being close together (small distances)
    loss = torch.logsumexp(-temperature * pairwise_dist_sq_offdiag, dim=1).mean()

    metrics = {
        "n_samples": B,
        "mean_dist_sq": pairwise_dist_sq_offdiag.mean().item(),
        "min_dist_sq": pairwise_dist_sq_offdiag.min().item(),
    }

    return loss, metrics


def compute_short_diversity_loss(
    short_embeddings: torch.Tensor,
    target_std: Optional[float] = None,
) -> Tuple[torch.Tensor, Dict]:
    """
    Compute diversity loss based on per-dimension standard deviation.

    For uniform distribution on unit sphere, each dimension should have
    std ≈ 1/sqrt(d) where d=3 for short embeddings (≈0.577).

    Penalizes dimensions with std below target (collapsed dimensions).

    Args:
        short_embeddings: (B, 3) tensor of L2-normalized short embeddings
        target_std: Target std per dimension (default: 1/sqrt(3) ≈ 0.577)

    Returns:
        loss: Scalar tensor
        metrics: Dict with std_x, std_y, std_z, target_std
    """
    device = short_embeddings.device

    # Ensure normalized
    short_emb = F.normalize(short_embeddings, dim=1, eps=1e-8)  # (B, 3)
    B, d = short_emb.shape

    if B < 2:
        return torch.tensor(0.0, device=device), {"n_samples": B}

    # Default target std for uniform on unit sphere
    if target_std is None:
        target_std = 1.0 / (d ** 0.5)  # ~0.577 for d=3

    # Compute per-dimension std
    std_per_dim = short_emb.std(dim=0)  # (3,)

    # Penalize dimensions below target (collapsed)
    std_deficit = torch.clamp(target_std - std_per_dim, min=0.0)
    loss = (std_deficit ** 2).mean()

    metrics = {
        "std_x": std_per_dim[0].item(),
        "std_y": std_per_dim[1].item(),
        "std_z": std_per_dim[2].item(),
        "target_std": target_std,
        "mean_std": std_per_dim.mean().item(),
        "min_std": std_per_dim.min().item(),
    }

    return loss, metrics


def compute_short_repulsion_loss(
    short_embeddings: torch.Tensor,
    similarity_threshold: float = 0.7,
) -> Tuple[torch.Tensor, Dict]:
    """
    Compute pairwise repulsion loss to push apart points that are too close.

    Uses softplus penalty on cosine similarities above threshold.
    Threshold of 0.7 corresponds to ~45° angle between vectors.

    Args:
        short_embeddings: (B, 3) tensor of L2-normalized short embeddings
        similarity_threshold: Penalize pairs with similarity > threshold

    Returns:
        loss: Scalar tensor
        metrics: Dict with avg_sim, max_sim, n_violations
    """
    device = short_embeddings.device

    # Ensure normalized
    short_emb = F.normalize(short_embeddings, dim=1, eps=1e-8)  # (B, 3)
    B = short_emb.shape[0]

    if B < 2:
        return torch.tensor(0.0, device=device), {"n_samples": B}

    # Compute all pairwise cosine similarities
    pairwise_sim = short_emb @ short_emb.T  # (B, B)

    # Mask out diagonal (self-similarity = 1.0)
    mask = ~torch.eye(B, dtype=torch.bool, device=device)
    off_diag_sim = pairwise_sim[mask]  # (B*(B-1),)

    # Repulsion: penalize high similarity (points too close)
    # softplus(sim - threshold) = log(1 + exp(sim - threshold))
    # This is 0 when sim << threshold, grows smoothly when sim > threshold
    loss = F.softplus(off_diag_sim - similarity_threshold).mean()

    # Metrics
    avg_sim = off_diag_sim.mean().item()
    max_sim = off_diag_sim.max().item()
    n_violations = (off_diag_sim > similarity_threshold).sum().item()
    n_pairs = B * (B - 1)

    metrics = {
        "avg_pairwise_sim": avg_sim,
        "max_pairwise_sim": max_sim,
        "n_violations": n_violations,
        "pct_violations": 100.0 * n_violations / n_pairs if n_pairs > 0 else 0.0,
        "threshold": similarity_threshold,
    }

    return loss, metrics


def compute_sphere_coverage_metrics(
    short_embeddings: torch.Tensor,
) -> Dict:
    """
    Compute metrics showing how well embeddings cover the unit sphere.

    Returns bounding box metrics and surface density information.

    Args:
        short_embeddings: (B, 3) tensor of L2-normalized short embeddings

    Returns:
        Dict with:
        - bounding_box: {min_x, max_x, min_y, max_y, min_z, max_z, volume, diagonal}
        - sphere_coverage: {volume_ratio, diagonal_ratio} - how much of sphere is used
        - surface_density: angular distribution metrics
    """
    # Ensure normalized
    short_emb = F.normalize(short_embeddings, dim=1, eps=1e-8)  # (B, 3)
    B = short_emb.shape[0]

    if B < 2:
        return {"n_samples": B, "error": "too_few_samples"}

    # Extract x, y, z coordinates
    x = short_emb[:, 0]
    y = short_emb[:, 1]
    z = short_emb[:, 2]

    # BOUNDING BOX metrics
    min_x, max_x = x.min().item(), x.max().item()
    min_y, max_y = y.min().item(), y.max().item()
    min_z, max_z = z.min().item(), z.max().item()

    # Box dimensions
    width = max_x - min_x
    height = max_y - min_y
    depth = max_z - min_z

    # Box volume and diagonal
    box_volume = width * height * depth
    box_diagonal = (width**2 + height**2 + depth**2) ** 0.5

    # Unit sphere bounding box: [-1,1] in each dimension
    # Volume = 2*2*2 = 8, diagonal = sqrt(12) ≈ 3.46
    sphere_box_volume = 8.0
    sphere_box_diagonal = 12 ** 0.5  # ~3.464

    # Coverage ratios (0 = collapsed, 1 = full sphere coverage)
    volume_ratio = box_volume / sphere_box_volume
    diagonal_ratio = box_diagonal / sphere_box_diagonal

    # ANGULAR DISTRIBUTION metrics (latitude/longitude coverage)
    # Convert to spherical coordinates
    # theta = azimuthal angle in xy-plane from x-axis [0, 2π]
    # phi = polar angle from z-axis [0, π]
    theta = torch.atan2(y, x)  # [-π, π]
    # CRITICAL FIX: Clamp to (-1+eps, 1-eps) to avoid infinite gradients from acos
    phi = torch.acos(torch.clamp(z, -1.0 + 1e-6, 1.0 - 1e-6))  # [0, π]

    # Angular ranges
    theta_range = (theta.max() - theta.min()).item()
    phi_range = (phi.max() - phi.min()).item()

    # Ideal ranges: theta = 2π, phi = π
    theta_coverage = theta_range / (2 * 3.14159)
    phi_coverage = phi_range / 3.14159

    # DENSITY metrics - how uniformly spread across the sphere
    # Compute centroid and distances from it
    centroid = short_emb.mean(dim=0)  # (3,)
    centroid_norm = centroid.norm().item()  # 0 = uniform, 1 = all same point

    # Average pairwise distance (on sphere, ideal ~1.0 for random uniform)
    pairwise_dist = torch.cdist(short_emb, short_emb)  # (B, B)
    mask = ~torch.eye(B, dtype=torch.bool, device=short_emb.device)
    avg_pairwise_dist = pairwise_dist[mask].mean().item()
    min_pairwise_dist = pairwise_dist[mask].min().item()
    max_pairwise_dist = pairwise_dist[mask].max().item()

    return {
        "n_samples": B,
        "bounding_box": {
            "min": [min_x, min_y, min_z],
            "max": [max_x, max_y, max_z],
            "dimensions": [width, height, depth],
            "volume": box_volume,
            "diagonal": box_diagonal,
        },
        "sphere_coverage": {
            "volume_ratio": volume_ratio,  # 0-1, ideal ~0.5-0.8
            "diagonal_ratio": diagonal_ratio,  # 0-1, ideal ~0.8-1.0
            "theta_coverage": theta_coverage,  # 0-1, azimuthal (longitude)
            "phi_coverage": phi_coverage,  # 0-1, polar (latitude)
        },
        "density": {
            "centroid_norm": centroid_norm,  # 0 = uniform, 1 = collapsed
            "avg_pairwise_dist": avg_pairwise_dist,  # ideal ~1.0
            "min_pairwise_dist": min_pairwise_dist,  # should be > 0
            "max_pairwise_dist": max_pairwise_dist,  # max is 2.0 (opposite poles)
        },
    }


def compute_short_spread_loss(
    short_embeddings: torch.Tensor,
    target_diagonal_ratio: float = 0.8,
) -> Tuple[torch.Tensor, Dict]:
    """
    Compute spread loss based on bounding box coverage of the unit sphere.

    Penalizes embeddings that don't cover enough of the sphere's bounding box.
    The unit sphere has a bounding box of [-1,1]^3 with diagonal sqrt(12) ≈ 3.46.

    Args:
        short_embeddings: (B, 3) tensor of L2-normalized short embeddings
        target_diagonal_ratio: Target diagonal ratio (0-1, default 0.8 = 80% coverage)

    Returns:
        loss: Scalar tensor
        metrics: Dict with bounding box and coverage info
    """
    device = short_embeddings.device

    # Ensure normalized
    short_emb = F.normalize(short_embeddings, dim=1, eps=1e-8)  # (B, 3)
    B = short_emb.shape[0]

    if B < 2:
        return torch.tensor(0.0, device=device), {"n_samples": B}

    # Compute bounding box
    min_coords = short_emb.min(dim=0).values  # (3,)
    max_coords = short_emb.max(dim=0).values  # (3,)
    dimensions = max_coords - min_coords  # (3,)

    # Box diagonal
    box_diagonal = torch.sqrt((dimensions ** 2).sum())

    # Sphere bounding box diagonal
    sphere_diagonal = 12.0 ** 0.5  # sqrt(12) ≈ 3.464

    # Diagonal ratio
    diagonal_ratio = box_diagonal / sphere_diagonal

    # Loss: penalize when diagonal ratio is below target
    # Use squared deficit for smooth gradient
    deficit = torch.clamp(target_diagonal_ratio - diagonal_ratio, min=0.0)
    loss = deficit ** 2

    # Also compute volume ratio for metrics
    box_volume = dimensions.prod()
    sphere_volume = 8.0  # 2*2*2
    volume_ratio = box_volume / sphere_volume

    metrics = {
        "dimensions": dimensions.detach().cpu().tolist(),
        "box_diagonal": box_diagonal.item(),
        "diagonal_ratio": diagonal_ratio.item(),
        "volume_ratio": volume_ratio.item(),
        "target_diagonal_ratio": target_diagonal_ratio,
        "deficit": deficit.item(),
    }

    return loss, metrics


def compute_coverage_loss(
    embeddings: torch.Tensor,
    temperature: float = 2.0,
) -> Tuple[torch.Tensor, Dict]:
    """
    Compute coverage loss for full d_model embeddings (e.g., 128D) on unit sphere.

    Uses COSINE SIMILARITY based repulsion - penalizes high similarity between
    different embeddings, pushing them apart on the sphere surface.

    For unit vectors: cos_sim = dot(a, b), and we want this to be low (near 0)
    for different samples, meaning they're spread across the sphere.

    Args:
        embeddings: (B, d_model) tensor of L2-normalized embeddings
        temperature: Temperature for log-sum-exp (higher = gentler repulsion)

    Returns:
        loss: Scalar tensor
        metrics: Dict with similarity info
    """
    device = embeddings.device
    B, d = embeddings.shape

    if B < 2:
        return torch.tensor(0.0, device=device), {"n_samples": B, "d_model": d}

    # Ensure normalized (should already be, but be safe)
    emb = F.normalize(embeddings, dim=1, eps=1e-8)

    # Compute pairwise cosine similarity (for unit vectors, this is just dot product)
    cos_sim = emb @ emb.T  # (B, B), values in [-1, 1]

    # Mask out diagonal (self-similarity = 1.0)
    mask = ~torch.eye(B, dtype=torch.bool, device=device)
    cos_sim_offdiag = cos_sim[mask].view(B, B - 1)

    # Log-sum-exp of similarities - penalizes HIGH similarity (close points)
    # We want cos_sim to be LOW (spread out), so we penalize positive values
    # Loss = log(sum(exp(cos_sim / temp))) - higher when points are similar
    loss = torch.logsumexp(cos_sim_offdiag / temperature, dim=1).mean()

    # Compute metrics for logging
    with torch.no_grad():
        mean_cos_sim = cos_sim_offdiag.mean().item()
        max_cos_sim = cos_sim_offdiag.max().item()
        min_cos_sim = cos_sim_offdiag.min().item()

        # Bounding box diagonal (for comparison with old metric)
        min_coords = emb.min(dim=0).values
        max_coords = emb.max(dim=0).values
        dimensions = max_coords - min_coords
        box_diagonal = torch.sqrt((dimensions ** 2).sum()).item()
        max_diagonal = 2.0 * (d ** 0.5)  # Max possible on unit sphere
        diagonal_ratio = box_diagonal / max_diagonal

    metrics = {
        "n_samples": B,
        "d_model": d,
        "mean_cos_sim": mean_cos_sim,
        "max_cos_sim": max_cos_sim,
        "min_cos_sim": min_cos_sim,
        "box_diagonal": box_diagonal,
        "diagonal_ratio": diagonal_ratio,
    }

    return loss, metrics


def compute_spherical_cap_overlap_loss(
    short_embeddings: torch.Tensor,
    labels: torch.Tensor,
    margin: float = 0.1,
) -> Tuple[torch.Tensor, Dict]:
    """
    Compute spherical cap overlap loss for label separation on the unit sphere.

    For each label, we approximate its territory as a spherical cap:
    - Centroid: mean of normalized points with that label
    - Angular radius: max angle from centroid to any point with that label

    The loss penalizes overlap between caps of different labels, encouraging
    the embedding to place different classes in separate regions of the sphere.

    Args:
        short_embeddings: (B, 3) tensor of L2-normalized short embeddings
        labels: (B,) tensor of integer labels (class assignments)
        margin: Angular margin (radians) to add between caps (default: 0.1 ≈ 6°)

    Returns:
        loss: Scalar tensor (sum of pairwise cap overlaps)
        metrics: Dict with per-label cap info and overlap details
    """
    device = short_embeddings.device

    # Ensure normalized
    short_emb = F.normalize(short_embeddings, dim=1, eps=1e-8)  # (B, 3)
    B = short_emb.shape[0]

    if B < 2:
        return torch.tensor(0.0, device=device), {"n_samples": B, "n_labels": 0}

    # Get unique labels
    unique_labels = torch.unique(labels)
    n_labels = len(unique_labels)

    if n_labels < 2:
        return torch.tensor(0.0, device=device), {"n_samples": B, "n_labels": n_labels}

    # Compute spherical cap for each label
    # Cap is defined by: centroid (unit vector) and angular radius (radians)
    centroids = []
    radii = []
    label_counts = []

    for label in unique_labels:
        mask = labels == label
        label_points = short_emb[mask]  # (n_i, 3)
        n_i = label_points.shape[0]

        if n_i == 0:
            continue

        # Centroid: mean of points, then normalize to sphere surface
        centroid = label_points.mean(dim=0)  # (3,)
        centroid = F.normalize(centroid.unsqueeze(0), dim=1, eps=1e-8).squeeze(0)  # (3,)

        # Angular radius: max angle from centroid to any point in this class
        # cos(angle) = dot(centroid, point), angle = acos(dot)
        cos_angles = (label_points @ centroid)  # (n_i,)
        # CRITICAL FIX: Clamp to (-1+eps, 1-eps) to avoid infinite gradients
        # acos has gradient -1/sqrt(1-x^2) which is inf at x=±1
        cos_angles = torch.clamp(cos_angles, -1.0 + 1e-6, 1.0 - 1e-6)
        angles = torch.acos(cos_angles)  # (n_i,) in radians
        radius = angles.max()  # Max angle = radius of cap

        centroids.append(centroid)
        radii.append(radius)
        label_counts.append(n_i)

    if len(centroids) < 2:
        return torch.tensor(0.0, device=device), {"n_samples": B, "n_labels": len(centroids)}

    centroids = torch.stack(centroids)  # (K, 3)
    radii = torch.stack(radii)  # (K,)
    K = len(centroids)

    # Compute pairwise cap overlaps
    # Two caps overlap if: angular_distance(c1, c2) < r1 + r2 + margin
    # Overlap amount (soft): max(0, r1 + r2 + margin - angular_dist)

    # Pairwise angular distances between centroids
    centroid_dots = centroids @ centroids.T  # (K, K)
    # CRITICAL FIX: Clamp to (-1+eps, 1-eps) to avoid infinite gradients
    # acos has gradient -1/sqrt(1-x^2) which is inf at x=±1
    centroid_dots = torch.clamp(centroid_dots, -1.0 + 1e-6, 1.0 - 1e-6)
    angular_dists = torch.acos(centroid_dots)  # (K, K) in radians

    # Sum of radii for each pair
    # radii_sum[i,j] = radii[i] + radii[j]
    radii_sum = radii.unsqueeze(1) + radii.unsqueeze(0)  # (K, K)

    # Overlap: how much the caps intrude into each other's territory
    # Positive when caps overlap, zero when separated
    overlap = torch.clamp(radii_sum + margin - angular_dists, min=0.0)  # (K, K)

    # Zero out diagonal (self-overlap)
    mask = ~torch.eye(K, dtype=torch.bool, device=device)
    overlap = overlap * mask.float()

    # Loss: sum of all pairwise overlaps (each pair counted twice, so divide by 2)
    loss = overlap.sum() / 2.0

    # Normalize by number of pairs to make loss scale-invariant
    n_pairs = K * (K - 1) / 2
    if n_pairs > 0:
        loss = loss / n_pairs

    # Compute metrics
    overlap_offdiag = overlap[mask]
    n_overlapping = (overlap_offdiag > 0).sum().item()

    metrics = {
        "n_samples": B,
        "n_labels": K,
        "label_counts": label_counts,
        "mean_radius": radii.mean().item(),
        "max_radius": radii.max().item(),
        "min_radius": radii.min().item(),
        "mean_centroid_dist": angular_dists[mask].mean().item(),
        "min_centroid_dist": angular_dists[mask].min().item(),
        "n_overlapping_pairs": n_overlapping,
        "total_pairs": int(n_pairs),
        "pct_overlapping": 100.0 * n_overlapping / n_pairs if n_pairs > 0 else 0.0,
        "mean_overlap": overlap_offdiag.mean().item() if len(overlap_offdiag) > 0 else 0.0,
        "max_overlap": overlap_offdiag.max().item() if len(overlap_offdiag) > 0 else 0.0,
        "margin": margin,
    }

    return loss, metrics


def compute_combined_short_embedding_loss(
    short_embeddings: torch.Tensor,
    config: Optional[dict] = None,
    labels: Optional[torch.Tensor] = None,
) -> Tuple[torch.Tensor, Dict]:
    """
    Compute combined loss for short embeddings with configurable components.

    Uses feature flags from sphere_config to enable/disable each loss type.

    Args:
        short_embeddings: (B, 3) tensor of L2-normalized short embeddings
        config: Optional config dict (if None, loads from sphere_config)
        labels: Optional (B,) tensor of integer labels for cap overlap loss

    Returns:
        total_loss: Combined weighted loss
        metrics: Dict with all component losses and metrics
    """
    device = short_embeddings.device

    # Load config
    if config is None:
        try:
            from featrix.neural.sphere_config import get_config
            sphere_config = get_config()
            config = {
                "enable_short_uniformity_loss": sphere_config.get("enable_short_uniformity_loss", True),
                "short_uniformity_weight": sphere_config.get("short_uniformity_weight", 2.0),
                "enable_short_diversity_loss": sphere_config.get("enable_short_diversity_loss", True),
                "short_diversity_weight": sphere_config.get("short_diversity_weight", 5.0),
                "enable_short_repulsion_loss": sphere_config.get("enable_short_repulsion_loss", True),
                "short_repulsion_weight": sphere_config.get("short_repulsion_weight", 3.0),
                "short_repulsion_threshold": sphere_config.get("short_repulsion_threshold", 0.7),
                "enable_short_spread_loss": sphere_config.get("enable_short_spread_loss", True),
                "short_spread_weight": sphere_config.get("short_spread_weight", 10.0),
                "short_spread_target_diagonal": sphere_config.get("short_spread_target_diagonal", 0.8),
                "enable_short_cap_overlap_loss": sphere_config.get("enable_short_cap_overlap_loss", False),
                "short_cap_overlap_weight": sphere_config.get("short_cap_overlap_weight", 5.0),
                "short_cap_overlap_margin": sphere_config.get("short_cap_overlap_margin", 0.1),
            }
        except Exception:
            # Default config if sphere_config unavailable
            # NOTE: Keep weights LOW to prevent oscillation (gradient wars between losses)
            config = {
                "enable_short_uniformity_loss": True,
                "short_uniformity_weight": 0.2,  # Low to prevent oscillation
                "enable_short_diversity_loss": True,
                "short_diversity_weight": 0.5,  # Low to prevent oscillation
                "enable_short_repulsion_loss": True,
                "short_repulsion_weight": 0.3,  # Low to prevent oscillation
                "short_repulsion_threshold": 0.7,
                "enable_short_spread_loss": True,
                "short_spread_weight": 1.0,  # Low to prevent oscillation
                "short_spread_target_diagonal": 0.8,
                "enable_short_cap_overlap_loss": False,
                "short_cap_overlap_weight": 0.5,  # Low to prevent oscillation
                "short_cap_overlap_margin": 0.1,
            }

    total_loss = torch.tensor(0.0, device=device)
    metrics = {"config": config}

    # Uniformity loss
    if config.get("enable_short_uniformity_loss", True):
        uniformity_loss, uniformity_metrics = compute_short_uniformity_loss(short_embeddings)
        weight = config.get("short_uniformity_weight", 2.0)
        total_loss = total_loss + weight * uniformity_loss
        metrics["uniformity"] = {
            "loss": uniformity_loss.item(),
            "weight": weight,
            "weighted_loss": (weight * uniformity_loss).item(),
            **uniformity_metrics,
        }

    # Diversity loss
    if config.get("enable_short_diversity_loss", True):
        diversity_loss, diversity_metrics = compute_short_diversity_loss(short_embeddings)
        weight = config.get("short_diversity_weight", 5.0)
        total_loss = total_loss + weight * diversity_loss
        metrics["diversity"] = {
            "loss": diversity_loss.item(),
            "weight": weight,
            "weighted_loss": (weight * diversity_loss).item(),
            **diversity_metrics,
        }

    # Repulsion loss
    if config.get("enable_short_repulsion_loss", True):
        threshold = config.get("short_repulsion_threshold", 0.7)
        repulsion_loss, repulsion_metrics = compute_short_repulsion_loss(
            short_embeddings,
            similarity_threshold=threshold
        )
        weight = config.get("short_repulsion_weight", 3.0)
        total_loss = total_loss + weight * repulsion_loss
        metrics["repulsion"] = {
            "loss": repulsion_loss.item(),
            "weight": weight,
            "weighted_loss": (weight * repulsion_loss).item(),
            **repulsion_metrics,
        }

    # Spread loss (bounding box coverage)
    if config.get("enable_short_spread_loss", True):
        target_diagonal = config.get("short_spread_target_diagonal", 0.8)
        spread_loss, spread_metrics = compute_short_spread_loss(
            short_embeddings,
            target_diagonal_ratio=target_diagonal
        )
        weight = config.get("short_spread_weight", 10.0)
        total_loss = total_loss + weight * spread_loss
        metrics["spread"] = {
            "loss": spread_loss.item(),
            "weight": weight,
            "weighted_loss": (weight * spread_loss).item(),
            **spread_metrics,
        }

    # Cap overlap loss (label separation on sphere)
    if config.get("enable_short_cap_overlap_loss", False) and labels is not None:
        margin = config.get("short_cap_overlap_margin", 0.1)
        cap_overlap_loss, cap_overlap_metrics = compute_spherical_cap_overlap_loss(
            short_embeddings,
            labels=labels,
            margin=margin
        )
        weight = config.get("short_cap_overlap_weight", 5.0)
        total_loss = total_loss + weight * cap_overlap_loss
        metrics["cap_overlap"] = {
            "loss": cap_overlap_loss.item(),
            "weight": weight,
            "weighted_loss": (weight * cap_overlap_loss).item(),
            **cap_overlap_metrics,
        }

    metrics["total_loss"] = total_loss.item()

    # Add sphere coverage metrics (for monitoring/timeline)
    try:
        coverage_metrics = compute_sphere_coverage_metrics(short_embeddings)
        metrics["sphere_coverage"] = coverage_metrics
    except Exception:
        pass  # Don't fail if coverage metrics fail

    return total_loss, metrics