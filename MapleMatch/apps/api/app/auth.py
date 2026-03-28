from datetime import UTC, datetime

import httpx
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.config import settings
from app.db import get_session
from app.models import User, UserRole

security = HTTPBearer()

_jwks_cache: dict | None = None


async def _get_clerk_jwks() -> dict:
    """Fetch Clerk's JWKS (JSON Web Key Set) for JWT verification."""
    global _jwks_cache
    if _jwks_cache is not None:
        return _jwks_cache

    clerk_domain = settings.clerk_publishable_key.split("_")[-1]
    jwks_url = f"https://{clerk_domain}.clerk.accounts.dev/.well-known/jwks.json"

    async with httpx.AsyncClient() as client:
        response = await client.get(jwks_url)
        response.raise_for_status()
        _jwks_cache = response.json()
        return _jwks_cache


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_session),
) -> User:
    """Verify Clerk JWT and return the matching User from the database."""
    token = credentials.credentials

    try:
        jwks = await _get_clerk_jwks()
        public_keys = {}
        for key_data in jwks.get("keys", []):
            kid = key_data["kid"]
            public_keys[kid] = jwt.algorithms.RSAAlgorithm.from_jwk(key_data)

        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        if kid not in public_keys:
            # Invalidate cache and retry once
            global _jwks_cache
            _jwks_cache = None
            jwks = await _get_clerk_jwks()
            for key_data in jwks.get("keys", []):
                public_keys[key_data["kid"]] = (
                    jwt.algorithms.RSAAlgorithm.from_jwk(key_data)
                )
            if kid not in public_keys:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token signing key",
                )

        payload = jwt.decode(
            token,
            key=public_keys[kid],
            algorithms=["RS256"],
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    clerk_id = payload.get("sub")
    if not clerk_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject",
        )

    result = await session.execute(select(User).where(User.clerk_id == clerk_id))
    user = result.scalar_one_or_none()

    if user is None:
        # Auto-provision user from JWT claims on first sign-in
        email = payload.get("email") or f"{clerk_id}@placeholder.maplematch"
        first_name = payload.get("first_name") or payload.get("given_name") or ""
        last_name = payload.get("last_name") or payload.get("family_name") or ""
        user = User(
            clerk_id=clerk_id,
            email=email,
            first_name=first_name,
            last_name=last_name,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )

    return user


def require_role(*roles: UserRole):
    """Dependency that restricts access to specific user roles."""

    async def _check_role(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of: {', '.join(r.value for r in roles)}",
            )
        return user

    return _check_role
