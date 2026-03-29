"""Eligibility check, AI matching, and wait-time prediction endpoints."""

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.auth import get_current_user, require_role
from app.db import get_session
from app.models import (
    EligibilityProfile,
    Listing,
    ListingStatus,
    Match,
    MatchStatus,
    User,
    UserRole,
)
from app.schemas import (
    EligibilityCheckRequest,
    EligibilityCheckResult,
    MatchFactorRead,
    MatchRead,
    MatchStatusUpdate,
    SmartMatchResult,
    WaitTimeResponse,
)
from app.services.eligibility import check_eligibility

router = APIRouter(tags=["matching"])


@router.post("/eligibility/check", response_model=EligibilityCheckResult)
async def check_listing_eligibility(
    data: EligibilityCheckRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> EligibilityCheckResult:
    """Check if the current user is eligible for a specific listing."""
    # Get user's eligibility profile
    result = await session.execute(
        select(EligibilityProfile).where(EligibilityProfile.user_id == user.id)
    )
    profile = result.scalar_one_or_none()
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Complete your eligibility profile first.",
        )

    # Get the listing
    result = await session.execute(
        select(Listing).where(Listing.id == data.listing_id)
    )
    listing = result.scalar_one_or_none()
    if listing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found",
        )

    eligibility = check_eligibility(profile, listing)

    return EligibilityCheckResult(
        eligible=eligibility.eligible,
        score=eligibility.score,
        reasons=eligibility.reasons,
        listing_id=listing.id,
        listing_title=listing.title,
    )


@router.post(
    "/matches/generate",
    response_model=list[MatchRead],
    status_code=status.HTTP_201_CREATED,
)
async def generate_matches(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[Match]:
    """Generate matches for the current user against all active listings.

    Runs the eligibility engine against every active listing and creates
    Match records for eligible ones, sorted by score descending.
    """
    # Get user's eligibility profile
    result = await session.execute(
        select(EligibilityProfile).where(EligibilityProfile.user_id == user.id)
    )
    profile = result.scalar_one_or_none()
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Complete your eligibility profile first.",
        )

    # Fetch active listings
    result = await session.execute(
        select(Listing).where(Listing.status == ListingStatus.active)
    )
    listings = list(result.scalars().all())

    # Get existing match listing IDs to avoid duplicates
    result = await session.execute(
        select(Match.listing_id).where(Match.user_id == user.id)
    )
    existing_listing_ids = {row[0] for row in result.all()}

    new_matches: list[Match] = []
    for listing in listings:
        if listing.id in existing_listing_ids:
            continue

        eligibility = check_eligibility(profile, listing)
        if not eligibility.eligible:
            continue

        match = Match(
            user_id=user.id,
            listing_id=listing.id,
            score=eligibility.score,
            explanation="; ".join(eligibility.reasons),
        )
        session.add(match)
        new_matches.append(match)

    await session.commit()
    for m in new_matches:
        await session.refresh(m)

    # Return sorted by score descending
    new_matches.sort(key=lambda m: m.score, reverse=True)
    return new_matches


@router.get("/matches", response_model=list[MatchRead])
async def list_my_matches(
    status_filter: MatchStatus | None = None,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[Match]:
    """List all matches for the current user, sorted by score descending."""
    query = select(Match).where(Match.user_id == user.id)
    if status_filter is not None:
        query = query.where(Match.status == status_filter)
    query = query.order_by(Match.score.desc())  # type: ignore[union-attr]

    result = await session.execute(query)
    return list(result.scalars().all())


@router.patch("/matches/{match_id}", response_model=MatchRead)
async def update_match_status(
    match_id: uuid.UUID,
    data: MatchStatusUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Match:
    """Update a match status (accept/decline)."""
    result = await session.execute(
        select(Match).where(Match.id == match_id)
    )
    match = result.scalar_one_or_none()
    if match is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found",
        )
    if match.user_id != user.id and user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    match.status = data.status
    match.updated_at = datetime.utcnow()
    session.add(match)
    await session.commit()
    await session.refresh(match)
    return match


# === Helpers ===


async def _get_user_profile(
    user: User, session: AsyncSession
) -> EligibilityProfile:
    """Get user's eligibility profile or raise 400."""
    result = await session.execute(
        select(EligibilityProfile).where(EligibilityProfile.user_id == user.id)
    )
    profile = result.scalar_one_or_none()
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Complete your eligibility profile first.",
        )
    return profile


# === AI-Powered Smart Matching ===


@router.post("/matches/smart", response_model=list[SmartMatchResult])
async def smart_match(
    use_semantic: bool = Query(default=True, description="Include semantic similarity"),
    use_ml: bool = Query(default=True, description="Include ML feature scoring"),
    limit: int = Query(default=20, ge=1, le=100),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[SmartMatchResult]:
    """Run the hybrid AI matching engine.

    Combines rule-based eligibility, semantic similarity, and ML scoring
    to find the best matches. Returns ranked results with explainability
    and wait-time estimates.
    """
    from app.services.recommender import batch_hybrid_match
    from app.services.wait_time import predict_wait_time

    profile = await _get_user_profile(user, session)

    result = await session.execute(
        select(Listing).where(Listing.status == ListingStatus.active)
    )
    listings = list(result.scalars().all())
    if not listings:
        return []

    match_results = batch_hybrid_match(
        profile, listings, use_semantic=use_semantic, use_ml=use_ml
    )

    smart_results: list[SmartMatchResult] = []
    for listing, hr in match_results[:limit]:
        wt = predict_wait_time(profile, listing)
        smart_results.append(
            SmartMatchResult(
                listing_id=listing.id,
                listing_title=listing.title,
                eligible=hr.eligible,
                final_score=hr.final_score,
                rule_score=hr.rule_score,
                semantic_score=hr.semantic_score,
                ml_score=hr.ml_score,
                factors=[
                    MatchFactorRead(
                        name=f.name, score=f.score, weight=f.weight, details=f.details
                    )
                    for f in hr.factors
                ],
                explanation=hr.explanation,
                wait_time_days=wt.estimated_days,
                wait_time_lower=wt.lower_bound_days,
                wait_time_upper=wt.upper_bound_days,
                wait_time_confidence=wt.confidence,
                wait_time_factors=wt.factors,
            )
        )
    return smart_results


@router.post(
    "/matches/smart/save",
    response_model=list[MatchRead],
    status_code=status.HTTP_201_CREATED,
)
async def smart_match_and_save(
    use_semantic: bool = Query(default=True),
    use_ml: bool = Query(default=True),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[Match]:
    """Run smart matching and persist results as Match records.

    Only creates new matches for listings not already matched.
    """
    from app.services.recommender import batch_hybrid_match

    profile = await _get_user_profile(user, session)

    result = await session.execute(
        select(Listing).where(Listing.status == ListingStatus.active)
    )
    listings = list(result.scalars().all())

    # Existing matches
    result = await session.execute(
        select(Match.listing_id).where(Match.user_id == user.id)
    )
    existing_ids = {row[0] for row in result.all()}

    filtered = [l for l in listings if l.id not in existing_ids]
    if not filtered:
        return []

    match_results = batch_hybrid_match(
        profile, filtered, use_semantic=use_semantic, use_ml=use_ml
    )

    new_matches: list[Match] = []
    for listing, hr in match_results:
        if not hr.eligible:
            continue
        m = Match(
            user_id=user.id,
            listing_id=listing.id,
            score=hr.final_score,
            explanation=hr.explanation,
        )
        session.add(m)
        new_matches.append(m)

    await session.commit()
    for m in new_matches:
        await session.refresh(m)

    new_matches.sort(key=lambda m: m.score, reverse=True)
    return new_matches


# === Wait-Time Prediction ===


@router.post("/wait-time/estimate", response_model=WaitTimeResponse)
async def estimate_wait_time(
    data: EligibilityCheckRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> WaitTimeResponse:
    """Estimate wait time for the current user on a specific listing."""
    from app.services.wait_time import predict_wait_time

    profile = await _get_user_profile(user, session)

    result = await session.execute(
        select(Listing).where(Listing.id == data.listing_id)
    )
    listing = result.scalar_one_or_none()
    if listing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found",
        )

    wt = predict_wait_time(profile, listing)
    return WaitTimeResponse(
        listing_id=listing.id,
        listing_title=listing.title,
        estimated_days=wt.estimated_days,
        lower_bound_days=wt.lower_bound_days,
        upper_bound_days=wt.upper_bound_days,
        confidence=wt.confidence,
        factors=wt.factors,
        method=wt.method,
    )
