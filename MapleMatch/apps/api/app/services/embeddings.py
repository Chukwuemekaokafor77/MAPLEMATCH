"""Embedding service for semantic similarity between profiles and listings.

Uses sentence-transformers to generate dense vector embeddings from
textual representations of eligibility profiles and listings, enabling
semantic matching beyond simple rule-based checks.
"""

import logging
from functools import lru_cache

import numpy as np

from app.models import EligibilityProfile, Listing

logger = logging.getLogger(__name__)

# Lazy-loaded model singleton
_model = None


def _get_model():
    """Lazy-load the sentence-transformer model (downloads on first use)."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        # all-MiniLM-L6-v2: fast, 384-dim, good for semantic similarity
        _model = SentenceTransformer("all-MiniLM-L6-v2")
        logger.info("Loaded sentence-transformer model: all-MiniLM-L6-v2")
    return _model


def profile_to_text(profile: EligibilityProfile) -> str:
    """Convert an eligibility profile to a natural-language description for embedding."""
    parts = []

    if profile.annual_income is not None:
        parts.append(f"Annual income ${profile.annual_income:,.0f}")
    if profile.household_size is not None:
        parts.append(f"household of {profile.household_size}")
    if profile.priority_group and profile.priority_group.value != "none":
        parts.append(f"priority group {profile.priority_group.value.replace('_', ' ')}")
    if profile.province:
        parts.append(f"in {profile.city or ''} {profile.province}".strip())
    if profile.max_rent is not None:
        parts.append(f"max rent ${profile.max_rent:,.0f}")
    if profile.needs_accessible_unit:
        parts.append("needs accessible unit")

    return "Applicant: " + ", ".join(parts) if parts else "Applicant seeking affordable housing"


def listing_to_text(listing: Listing) -> str:
    """Convert a listing to a natural-language description for embedding."""
    parts = [listing.title]

    if listing.description:
        parts.append(listing.description)
    parts.append(f"in {listing.city} {listing.province}")
    parts.append(f"${listing.rent_amount:,.0f}/month")
    parts.append(f"{listing.bedrooms} bedroom{'s' if listing.bedrooms != 1 else ''}")

    if listing.is_rgi:
        parts.append("rent geared to income")
    if listing.is_accessible:
        parts.append("accessible unit")
    if listing.priority_groups:
        groups = listing.priority_groups.replace(",", ", ").replace("_", " ")
        parts.append(f"priority for {groups}")
    if listing.amenities:
        parts.append(f"amenities: {listing.amenities}")

    return " | ".join(parts)


def compute_embedding(text: str) -> np.ndarray:
    """Compute a dense vector embedding for a text string."""
    model = _get_model()
    return model.encode(text, normalize_embeddings=True)


def compute_similarity(embedding_a: np.ndarray, embedding_b: np.ndarray) -> float:
    """Compute cosine similarity between two normalized embeddings."""
    # Since embeddings are L2-normalized, dot product = cosine similarity
    similarity = float(np.dot(embedding_a, embedding_b))
    # Clamp to [0, 1] range for scoring
    return max(0.0, min(1.0, similarity))


def compute_profile_listing_similarity(
    profile: EligibilityProfile, listing: Listing
) -> float:
    """Compute semantic similarity between a profile and a listing."""
    profile_text = profile_to_text(profile)
    listing_text = listing_to_text(listing)

    profile_emb = compute_embedding(profile_text)
    listing_emb = compute_embedding(listing_text)

    return compute_similarity(profile_emb, listing_emb)


def batch_compute_similarities(
    profile: EligibilityProfile, listings: list[Listing]
) -> list[float]:
    """Compute semantic similarity between one profile and multiple listings.

    More efficient than calling compute_profile_listing_similarity in a loop
    because the profile embedding is computed only once and listing embeddings
    are batched.
    """
    if not listings:
        return []

    model = _get_model()
    profile_text = profile_to_text(profile)
    listing_texts = [listing_to_text(l) for l in listings]

    # Batch encode for efficiency
    all_texts = [profile_text] + listing_texts
    all_embeddings = model.encode(all_texts, normalize_embeddings=True, batch_size=64)

    profile_emb = all_embeddings[0]
    listing_embs = all_embeddings[1:]

    similarities = []
    for listing_emb in listing_embs:
        sim = float(np.dot(profile_emb, listing_emb))
        similarities.append(max(0.0, min(1.0, sim)))

    return similarities
