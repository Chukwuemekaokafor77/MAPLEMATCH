from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.auth import get_current_user, require_role
from app.db import get_session
from app.models import EligibilityProfile, User, UserRole
from app.schemas import (
    EligibilityProfileCreate,
    EligibilityProfileRead,
    EligibilityProfileUpdate,
    UserCreate,
    UserRead,
    UserUpdate,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register_user(
    data: UserCreate,
    session: AsyncSession = Depends(get_session),
) -> User:
    """Register a new user after Clerk sign-up (called from frontend webhook/callback)."""
    result = await session.execute(
        select(User).where(User.clerk_id == data.clerk_id)
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already registered",
        )

    user = User(
        clerk_id=data.clerk_id,
        email=data.email,
        first_name=data.first_name,
        last_name=data.last_name,
        role=data.role,
        preferred_language=data.preferred_language,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@router.get("/me", response_model=UserRead)
async def get_me(user: User = Depends(get_current_user)) -> User:
    """Get the current authenticated user."""
    return user


@router.patch("/me", response_model=UserRead)
async def update_me(
    data: UserUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> User:
    """Update the current user's profile fields."""
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    user.updated_at = datetime.utcnow()
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


# === Eligibility Profile ===


@router.post("/me/eligibility", response_model=EligibilityProfileRead, status_code=status.HTTP_201_CREATED)
async def create_eligibility_profile(
    data: EligibilityProfileCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> EligibilityProfile:
    """Create the eligibility profile for the current user."""
    result = await session.execute(
        select(EligibilityProfile).where(EligibilityProfile.user_id == user.id)
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Eligibility profile already exists. Use PATCH to update.",
        )

    profile = EligibilityProfile(user_id=user.id, **data.model_dump())
    if profile.consent_given:
        profile.consent_date = datetime.utcnow()

    session.add(profile)
    await session.commit()
    await session.refresh(profile)
    return profile


@router.get("/me/eligibility", response_model=EligibilityProfileRead)
async def get_eligibility_profile(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> EligibilityProfile:
    """Get the current user's eligibility profile."""
    result = await session.execute(
        select(EligibilityProfile).where(EligibilityProfile.user_id == user.id)
    )
    profile = result.scalar_one_or_none()
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Eligibility profile not found",
        )
    return profile


@router.patch("/me/eligibility", response_model=EligibilityProfileRead)
async def update_eligibility_profile(
    data: EligibilityProfileUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> EligibilityProfile:
    """Update the current user's eligibility profile."""
    result = await session.execute(
        select(EligibilityProfile).where(EligibilityProfile.user_id == user.id)
    )
    profile = result.scalar_one_or_none()
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Eligibility profile not found",
        )

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)

    if "consent_given" in update_data and update_data["consent_given"]:
        profile.consent_date = datetime.utcnow()

    profile.updated_at = datetime.utcnow()
    session.add(profile)
    await session.commit()
    await session.refresh(profile)
    return profile


# === Admin: list users ===


@router.get("/", response_model=list[UserRead])
async def list_users(
    skip: int = 0,
    limit: int = 50,
    _admin: User = Depends(require_role(UserRole.admin)),
    session: AsyncSession = Depends(get_session),
) -> list[User]:
    """List all users (admin only)."""
    result = await session.execute(
        select(User).offset(skip).limit(min(limit, 100))
    )
    return list(result.scalars().all())
