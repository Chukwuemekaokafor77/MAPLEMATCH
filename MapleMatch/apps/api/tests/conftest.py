"""Shared test fixtures."""

import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from app.auth import get_current_user
from app.db import get_session
from app.main import app
from app.models import User, UserRole


# In-memory SQLite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def test_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def test_session(test_engine):
    async_session = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session


@pytest.fixture
def mock_user():
    """A test user object."""
    return User(
        id=uuid.uuid4(),
        clerk_id="test_clerk_user_001",
        email="test@example.com",
        first_name="Test",
        last_name="User",
        role=UserRole.applicant,
        preferred_language="en",
        is_active=True,
    )


@pytest.fixture
def mock_admin():
    """A test admin user object."""
    return User(
        id=uuid.uuid4(),
        clerk_id="clerk_admin_456",
        email="admin@example.com",
        first_name="Admin",
        last_name="User",
        role=UserRole.admin,
        preferred_language="en",
        is_active=True,
    )


@pytest.fixture
def mock_nonprofit():
    """A test nonprofit user object."""
    return User(
        id=uuid.uuid4(),
        clerk_id="clerk_nonprofit_789",
        email="nonprofit@example.com",
        first_name="Nonprofit",
        last_name="User",
        role=UserRole.nonprofit,
        preferred_language="en",
        is_active=True,
    )


@pytest.fixture
async def client(test_engine, test_session, mock_user):
    """HTTP client with auth overridden to return mock_user."""

    async def _override_session():
        yield test_session

    async def _override_user():
        return mock_user

    app.dependency_overrides[get_session] = _override_session
    app.dependency_overrides[get_current_user] = _override_user

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def admin_client(test_engine, test_session, mock_admin):
    """HTTP client with auth overridden to return mock_admin."""

    async def _override_session():
        yield test_session

    async def _override_admin():
        return mock_admin

    app.dependency_overrides[get_session] = _override_session
    app.dependency_overrides[get_current_user] = _override_admin

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def nonprofit_client(test_engine, test_session, mock_nonprofit):
    """HTTP client with auth overridden to return mock_nonprofit."""

    async def _override_session():
        yield test_session

    async def _override_nonprofit():
        return mock_nonprofit

    app.dependency_overrides[get_session] = _override_session
    app.dependency_overrides[get_current_user] = _override_nonprofit

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
