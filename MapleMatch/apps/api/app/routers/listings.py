"""Listings CRUD + search endpoints."""

import math
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.auth import get_current_user, require_role
from app.db import get_session
from app.models import Listing, ListingStatus, User, UserRole
from app.schemas import ListingCreate, ListingRead, ListingUpdate

router = APIRouter(prefix="/listings", tags=["listings"])


@router.post("/", response_model=ListingRead, status_code=status.HTTP_201_CREATED)
async def create_listing(
    data: ListingCreate,
    user: User = Depends(require_role(UserRole.admin, UserRole.nonprofit)),
    session: AsyncSession = Depends(get_session),
) -> Listing:
    """Create a new housing listing (admin/nonprofit only)."""
    listing = Listing(organization_id=user.id, **data.model_dump())
    session.add(listing)
    await session.commit()
    await session.refresh(listing)
    return listing


@router.get("/", response_model=list[ListingRead])
async def search_listings(
    city: str | None = None,
    province: str | None = None,
    min_rent: float | None = None,
    max_rent: float | None = None,
    bedrooms: int | None = None,
    is_accessible: bool | None = None,
    is_rgi: bool | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    radius_km: float | None = Query(default=None, gt=0, le=500),
    skip: int = 0,
    limit: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
) -> list[Listing]:
    """Search listings with filters. Open to all authenticated users.

    Supports geographic proximity search via lat/lng + radius_km using
    the Haversine formula (computed in-app until PostGIS is available).
    """
    query = select(Listing).where(Listing.status == ListingStatus.active)

    if city:
        query = query.where(Listing.city.ilike(f"%{city}%"))  # type: ignore[union-attr]
    if province:
        query = query.where(Listing.province.ilike(province))  # type: ignore[union-attr]
    if min_rent is not None:
        query = query.where(Listing.rent_amount >= min_rent)
    if max_rent is not None:
        query = query.where(Listing.rent_amount <= max_rent)
    if bedrooms is not None:
        query = query.where(Listing.bedrooms == bedrooms)
    if is_accessible is not None:
        query = query.where(Listing.is_accessible == is_accessible)
    if is_rgi is not None:
        query = query.where(Listing.is_rgi == is_rgi)

    query = query.offset(skip).limit(limit)
    result = await session.execute(query)
    listings = list(result.scalars().all())

    # Apply Haversine distance filter in-app when lat/lng + radius are provided.
    # This will be replaced with PostGIS ST_DWithin once the extension is enabled.
    if latitude is not None and longitude is not None and radius_km is not None:
        listings = [
            listing
            for listing in listings
            if listing.latitude is not None
            and listing.longitude is not None
            and _haversine_km(latitude, longitude, listing.latitude, listing.longitude)
            <= radius_km
        ]

    return listings


@router.get("/{listing_id}", response_model=ListingRead)
async def get_listing(
    listing_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> Listing:
    """Get a single listing by ID."""
    result = await session.execute(select(Listing).where(Listing.id == listing_id))
    listing = result.scalar_one_or_none()
    if listing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found",
        )
    return listing


@router.patch("/{listing_id}", response_model=ListingRead)
async def update_listing(
    listing_id: uuid.UUID,
    data: ListingUpdate,
    user: User = Depends(require_role(UserRole.admin, UserRole.nonprofit)),
    session: AsyncSession = Depends(get_session),
) -> Listing:
    """Update a listing (admin/nonprofit only, must own listing or be admin)."""
    result = await session.execute(select(Listing).where(Listing.id == listing_id))
    listing = result.scalar_one_or_none()
    if listing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found",
        )

    # Nonprofits can only update their own listings
    if user.role == UserRole.nonprofit and listing.organization_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own listings",
        )

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(listing, field, value)
    listing.updated_at = datetime.utcnow()
    session.add(listing)
    await session.commit()
    await session.refresh(listing)
    return listing


@router.delete("/{listing_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_listing(
    listing_id: uuid.UUID,
    user: User = Depends(require_role(UserRole.admin)),
    session: AsyncSession = Depends(get_session),
) -> None:
    """Soft-delete a listing by setting status to inactive (admin only)."""
    result = await session.execute(select(Listing).where(Listing.id == listing_id))
    listing = result.scalar_one_or_none()
    if listing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found",
        )
    listing.status = ListingStatus.inactive
    listing.updated_at = datetime.utcnow()
    session.add(listing)
    await session.commit()


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two coordinates in kilometres using Haversine formula."""
    R = 6371.0  # Earth radius in km
    lat1_r, lat2_r = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
