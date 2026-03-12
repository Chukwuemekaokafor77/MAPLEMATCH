"""Hybrid recommender that combines rule-based, semantic, and feature-based scoring.

Three scoring components are blended with configurable weights:
1. Rule-based eligibility score (from eligibility engine)
2. Semantic similarity score (from sentence-transformer embeddings)
3. Feature-based ML score (from trained LightGBM model, when available)

The final score is a weighted combination of all available components.
"""

import logging
from dataclasses import dataclass, field

from app.models import EligibilityProfile, Listing
from app.services.eligibility import EligibilityResult, check_eligibility

logger = logging.getLogger(__name__)

# Scoring weights (must sum to 1.0)
WEIGHT_RULES = 0.50
WEIGHT_SEMANTIC = 0.30
WEIGHT_ML = 0.20


@dataclass
class MatchFactor:
    """A single scoring factor with its contribution to the final score."""

    name: str
    score: float  # 0.0 to 1.0
    weight: float
    details: str


@dataclass
class HybridMatchResult:
    """Result of hybrid matching with full explainability."""

    eligible: bool
    final_score: float  # 0.0 to 1.0
    rule_score: float
    semantic_score: float
    ml_score: float
    factors: list[MatchFactor] = field(default_factory=list)
    explanation: str = ""


def hybrid_match(
    profile: EligibilityProfile,
    listing: Listing,
    use_semantic: bool = True,
    use_ml: bool = True,
) -> HybridMatchResult:
    """Run the hybrid matching engine on a profile-listing pair.

    Args:
        profile: Applicant's eligibility profile.
        listing: Housing listing to match against.
        use_semantic: Whether to include semantic similarity scoring.
        use_ml: Whether to include ML feature-based scoring.

    Returns:
        HybridMatchResult with scores, factors, and explanation.
    """
    # --- Component 1: Rule-based eligibility ---
    eligibility = check_eligibility(profile, listing)

    if not eligibility.eligible:
        return HybridMatchResult(
            eligible=False,
            final_score=0.0,
            rule_score=0.0,
            semantic_score=0.0,
            ml_score=0.0,
            factors=[
                MatchFactor(
                    name="Rule-Based Eligibility",
                    score=0.0,
                    weight=WEIGHT_RULES,
                    details="; ".join(eligibility.reasons),
                )
            ],
            explanation="Not eligible: " + "; ".join(
                r for r in eligibility.reasons if "exceeds" in r.lower() or "outside" in r.lower() or "required" in r.lower()
            ),
        )

    rule_score = eligibility.score
    factors = [
        MatchFactor(
            name="Rule-Based Eligibility",
            score=rule_score,
            weight=WEIGHT_RULES,
            details="; ".join(eligibility.reasons),
        )
    ]

    # --- Component 2: Semantic similarity ---
    semantic_score = 0.0
    if use_semantic:
        try:
            from app.services.embeddings import compute_profile_listing_similarity

            semantic_score = compute_profile_listing_similarity(profile, listing)
            factors.append(
                MatchFactor(
                    name="Semantic Similarity",
                    score=semantic_score,
                    weight=WEIGHT_SEMANTIC,
                    details=f"Profile-listing text similarity: {semantic_score:.1%}",
                )
            )
        except Exception:
            logger.warning("Semantic scoring unavailable, falling back to rules-only")
            semantic_score = rule_score  # fallback to rule score
            factors.append(
                MatchFactor(
                    name="Semantic Similarity",
                    score=semantic_score,
                    weight=WEIGHT_SEMANTIC,
                    details="Fallback to rule-based score (embedding model unavailable)",
                )
            )

    # --- Component 3: Feature-based ML ---
    ml_score = 0.0
    if use_ml:
        ml_score = _compute_feature_score(profile, listing)
        factors.append(
            MatchFactor(
                name="Feature-Based ML",
                score=ml_score,
                weight=WEIGHT_ML,
                details=_explain_feature_score(profile, listing, ml_score),
            )
        )

    # --- Blend scores ---
    if use_semantic and use_ml:
        final_score = (
            WEIGHT_RULES * rule_score
            + WEIGHT_SEMANTIC * semantic_score
            + WEIGHT_ML * ml_score
        )
    elif use_semantic:
        w_total = WEIGHT_RULES + WEIGHT_SEMANTIC
        final_score = (WEIGHT_RULES * rule_score + WEIGHT_SEMANTIC * semantic_score) / w_total
    elif use_ml:
        w_total = WEIGHT_RULES + WEIGHT_ML
        final_score = (WEIGHT_RULES * rule_score + WEIGHT_ML * ml_score) / w_total
    else:
        final_score = rule_score

    final_score = round(max(0.0, min(1.0, final_score)), 3)

    explanation = _build_explanation(factors, final_score)

    return HybridMatchResult(
        eligible=True,
        final_score=final_score,
        rule_score=round(rule_score, 3),
        semantic_score=round(semantic_score, 3),
        ml_score=round(ml_score, 3),
        factors=factors,
        explanation=explanation,
    )


def batch_hybrid_match(
    profile: EligibilityProfile,
    listings: list[Listing],
    use_semantic: bool = True,
    use_ml: bool = True,
) -> list[tuple[Listing, HybridMatchResult]]:
    """Run hybrid matching against multiple listings efficiently.

    Uses batch embedding computation for semantic scoring.
    Returns list of (listing, result) tuples sorted by final_score descending.
    """
    if not listings:
        return []

    # First pass: rule-based filtering
    eligible_listings: list[tuple[Listing, EligibilityResult]] = []
    for listing in listings:
        eligibility = check_eligibility(profile, listing)
        if eligibility.eligible:
            eligible_listings.append((listing, eligibility))

    if not eligible_listings:
        return []

    # Batch semantic scoring
    semantic_scores: list[float] = []
    if use_semantic:
        try:
            from app.services.embeddings import batch_compute_similarities

            eligible_only = [l for l, _ in eligible_listings]
            semantic_scores = batch_compute_similarities(profile, eligible_only)
        except Exception:
            logger.warning("Batch semantic scoring unavailable, using fallback")
            semantic_scores = [er.score for _, er in eligible_listings]
    else:
        semantic_scores = [0.0] * len(eligible_listings)

    # Assemble results
    results: list[tuple[Listing, HybridMatchResult]] = []
    for i, (listing, eligibility) in enumerate(eligible_listings):
        rule_score = eligibility.score
        semantic_score = semantic_scores[i] if i < len(semantic_scores) else 0.0

        ml_score = 0.0
        if use_ml:
            ml_score = _compute_feature_score(profile, listing)

        factors = [
            MatchFactor(
                name="Rule-Based Eligibility",
                score=rule_score,
                weight=WEIGHT_RULES,
                details="; ".join(eligibility.reasons),
            ),
        ]
        if use_semantic:
            factors.append(
                MatchFactor(
                    name="Semantic Similarity",
                    score=semantic_score,
                    weight=WEIGHT_SEMANTIC,
                    details=f"Profile-listing text similarity: {semantic_score:.1%}",
                )
            )
        if use_ml:
            factors.append(
                MatchFactor(
                    name="Feature-Based ML",
                    score=ml_score,
                    weight=WEIGHT_ML,
                    details=_explain_feature_score(profile, listing, ml_score),
                )
            )

        # Blend
        if use_semantic and use_ml:
            final_score = (
                WEIGHT_RULES * rule_score
                + WEIGHT_SEMANTIC * semantic_score
                + WEIGHT_ML * ml_score
            )
        elif use_semantic:
            w_total = WEIGHT_RULES + WEIGHT_SEMANTIC
            final_score = (WEIGHT_RULES * rule_score + WEIGHT_SEMANTIC * semantic_score) / w_total
        elif use_ml:
            w_total = WEIGHT_RULES + WEIGHT_ML
            final_score = (WEIGHT_RULES * rule_score + WEIGHT_ML * ml_score) / w_total
        else:
            final_score = rule_score

        final_score = round(max(0.0, min(1.0, final_score)), 3)
        explanation = _build_explanation(factors, final_score)

        result = HybridMatchResult(
            eligible=True,
            final_score=final_score,
            rule_score=round(rule_score, 3),
            semantic_score=round(semantic_score, 3),
            ml_score=round(ml_score, 3),
            factors=factors,
            explanation=explanation,
        )
        results.append((listing, result))

    # Sort by final_score descending
    results.sort(key=lambda x: x[1].final_score, reverse=True)
    return results


def _compute_feature_score(profile: EligibilityProfile, listing: Listing) -> float:
    """Compute a feature-based score using hand-crafted features.

    This serves as a baseline ML scorer. When a trained LightGBM model is
    available, this will be replaced with model.predict().

    Features used:
    - Income-to-rent ratio (affordability)
    - Household size fit (bedrooms per person)
    - Geographic proximity indicator
    - Priority group alignment
    - Accessibility alignment
    """
    score = 0.0
    n_features = 5

    # Feature 1: Income-to-rent ratio (ideal: rent < 30% of income / 12)
    if profile.annual_income and listing.rent_amount > 0:
        monthly_income = profile.annual_income / 12
        rent_ratio = listing.rent_amount / monthly_income
        if rent_ratio <= 0.30:
            score += 1.0  # Ideal affordability
        elif rent_ratio <= 0.50:
            score += 0.6
        else:
            score += 0.2
    else:
        score += 0.5  # neutral

    # Feature 2: Bedrooms per person
    if profile.household_size and listing.bedrooms > 0:
        ratio = listing.bedrooms / profile.household_size
        if 0.5 <= ratio <= 1.0:
            score += 1.0  # Good fit
        elif ratio > 1.0:
            score += 0.7  # Spacious
        else:
            score += 0.3  # Cramped
    else:
        score += 0.5

    # Feature 3: Geographic match
    if profile.province and listing.province:
        if profile.province.upper() == listing.province.upper():
            if profile.city and listing.city and profile.city.lower() == listing.city.lower():
                score += 1.0
            else:
                score += 0.6
        else:
            score += 0.2
    else:
        score += 0.5

    # Feature 4: Priority group match
    if profile.priority_group and profile.priority_group.value != "none" and listing.priority_groups:
        if profile.priority_group.value in listing.priority_groups:
            score += 1.0
        else:
            score += 0.3
    else:
        score += 0.5

    # Feature 5: Accessibility alignment
    if profile.needs_accessible_unit:
        score += 1.0 if listing.is_accessible else 0.1
    else:
        score += 0.7  # slight bonus for any unit

    return round(score / n_features, 3)


def _explain_feature_score(
    profile: EligibilityProfile, listing: Listing, score: float
) -> str:
    """Generate human-readable explanation of the feature-based score."""
    parts = []

    if profile.annual_income and listing.rent_amount > 0:
        monthly_income = profile.annual_income / 12
        rent_ratio = listing.rent_amount / monthly_income
        parts.append(f"Rent-to-income ratio: {rent_ratio:.0%}")

    if profile.household_size and listing.bedrooms > 0:
        parts.append(f"{listing.bedrooms} bed for {profile.household_size} people")

    if profile.province and listing.province:
        same = profile.province.upper() == listing.province.upper()
        parts.append(f"{'Same' if same else 'Different'} province")

    parts.append(f"ML feature score: {score:.1%}")
    return "; ".join(parts)


def _build_explanation(factors: list[MatchFactor], final_score: float) -> str:
    """Build a human-readable match explanation from scoring factors."""
    lines = [f"Match score: {final_score:.1%}"]
    for factor in factors:
        contribution = factor.score * factor.weight
        lines.append(
            f"  {factor.name}: {factor.score:.1%} "
            f"(weight {factor.weight:.0%}, contributes {contribution:.1%})"
        )
    return "\n".join(lines)
