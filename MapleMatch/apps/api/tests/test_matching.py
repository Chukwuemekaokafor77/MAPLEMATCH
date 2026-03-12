"""Tests for the eligibility engine and matching endpoints."""

import pytest
from httpx import AsyncClient

from app.models import EligibilityProfile, Listing, PriorityGroup
from app.services.eligibility import check_eligibility


# === Unit tests for eligibility engine ===


def _make_profile(**kwargs) -> EligibilityProfile:
    """Helper to create a test eligibility profile."""
    defaults = {
        "annual_income": 35000.0,
        "household_size": 3,
        "priority_group": PriorityGroup.newcomer,
        "province": "ON",
        "city": "Toronto",
        "max_rent": 1500.0,
        "needs_accessible_unit": False,
        "consent_given": True,
    }
    defaults.update(kwargs)
    return EligibilityProfile(**defaults)


def _make_listing(**kwargs) -> Listing:
    """Helper to create a test listing."""
    defaults = {
        "title": "Test Listing",
        "city": "Toronto",
        "province": "ON",
        "rent_amount": 1200.0,
        "max_income": 50000.0,
        "min_household_size": 1,
        "max_household_size": 4,
        "priority_groups": "newcomer,senior",
        "is_rgi": False,
        "is_accessible": False,
    }
    defaults.update(kwargs)
    return Listing(**defaults)


def test_eligible_applicant():
    profile = _make_profile()
    listing = _make_listing()
    result = check_eligibility(profile, listing)
    assert result.eligible is True
    assert result.score > 0.5
    assert len(result.reasons) > 0


def test_income_too_high():
    profile = _make_profile(annual_income=60000.0)
    listing = _make_listing(max_income=50000.0)
    result = check_eligibility(profile, listing)
    assert result.eligible is False
    assert result.score == 0.0
    assert any("exceeds" in r.lower() for r in result.reasons)


def test_household_size_out_of_range():
    profile = _make_profile(household_size=6)
    listing = _make_listing(min_household_size=1, max_household_size=4)
    result = check_eligibility(profile, listing)
    assert result.eligible is False


def test_rgi_without_income():
    profile = _make_profile(annual_income=None)
    listing = _make_listing(is_rgi=True, max_income=None)
    result = check_eligibility(profile, listing)
    assert result.eligible is False
    assert any("income" in r.lower() for r in result.reasons)


def test_accessibility_match():
    profile = _make_profile(needs_accessible_unit=True)
    listing = _make_listing(is_accessible=True)
    result = check_eligibility(profile, listing)
    assert result.eligible is True
    assert any("accessible" in r.lower() for r in result.reasons)


def test_accessibility_mismatch():
    profile = _make_profile(needs_accessible_unit=True)
    listing = _make_listing(is_accessible=False)
    result = check_eligibility(profile, listing)
    # Still eligible, but lower score
    assert result.eligible is True
    assert any("not accessible" in r.lower() for r in result.reasons)


def test_priority_group_match():
    profile = _make_profile(priority_group=PriorityGroup.newcomer)
    listing = _make_listing(priority_groups="newcomer,senior")
    result = check_eligibility(profile, listing)
    assert result.eligible is True
    assert any("newcomer" in r.lower() for r in result.reasons)


def test_rent_within_budget():
    profile = _make_profile(max_rent=1500.0)
    listing = _make_listing(rent_amount=1200.0)
    result = check_eligibility(profile, listing)
    assert result.eligible is True
    assert any("within budget" in r.lower() for r in result.reasons)


def test_rent_over_budget():
    profile = _make_profile(max_rent=1000.0)
    listing = _make_listing(rent_amount=1500.0)
    result = check_eligibility(profile, listing)
    assert result.eligible is True  # soft factor, not disqualifying
    assert any("exceeds budget" in r.lower() for r in result.reasons)


def test_no_listing_restrictions():
    """When a listing has no income/household restrictions, should be eligible."""
    profile = _make_profile()
    listing = _make_listing(
        max_income=None,
        min_household_size=None,
        max_household_size=None,
        priority_groups="",
    )
    result = check_eligibility(profile, listing)
    assert result.eligible is True


# === Integration tests for matching endpoints ===


@pytest.mark.anyio
async def test_check_eligibility_endpoint(
    client: AsyncClient, admin_client: AsyncClient, mock_user
):
    # Register user and create profile
    await client.post(
        "/users/register",
        json={
            "clerk_id": mock_user.clerk_id,
            "email": mock_user.email,
            "first_name": mock_user.first_name,
            "last_name": mock_user.last_name,
        },
    )
    await client.post(
        "/users/me/eligibility",
        json={
            "annual_income": 35000.0,
            "household_size": 3,
            "priority_group": "newcomer",
            "province": "ON",
            "city": "Toronto",
            "max_rent": 1500.0,
            "consent_given": True,
        },
    )

    # Create listing as admin
    listing_resp = await admin_client.post(
        "/listings/",
        json={
            "title": "Matching Test Listing",
            "city": "Toronto",
            "province": "ON",
            "rent_amount": 1200.0,
            "max_income": 50000.0,
        },
    )
    listing_id = listing_resp.json()["id"]

    # Check eligibility
    response = await client.post(
        "/eligibility/check",
        json={"listing_id": listing_id},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["eligible"] is True
    assert data["score"] > 0
    assert data["listing_title"] == "Matching Test Listing"


@pytest.mark.anyio
async def test_check_eligibility_no_profile(
    client: AsyncClient, admin_client: AsyncClient
):
    # Create listing
    listing_resp = await admin_client.post(
        "/listings/",
        json={
            "title": "Test",
            "city": "Toronto",
            "province": "ON",
            "rent_amount": 1000.0,
        },
    )
    listing_id = listing_resp.json()["id"]

    # Check eligibility without profile
    response = await client.post(
        "/eligibility/check",
        json={"listing_id": listing_id},
    )
    assert response.status_code == 400


@pytest.mark.anyio
async def test_generate_matches(
    client: AsyncClient, admin_client: AsyncClient, mock_user
):
    # Register + profile
    await client.post(
        "/users/register",
        json={
            "clerk_id": mock_user.clerk_id,
            "email": mock_user.email,
            "first_name": mock_user.first_name,
            "last_name": mock_user.last_name,
        },
    )
    await client.post(
        "/users/me/eligibility",
        json={
            "annual_income": 35000.0,
            "household_size": 2,
            "province": "ON",
            "city": "Toronto",
            "max_rent": 1500.0,
            "consent_given": True,
        },
    )

    # Create two listingsls
    await admin_client.post(
        "/listings/",
        json={
            "title": "Listing A",
            "city": "Toronto",
            "province": "ON",
            "rent_amount": 1200.0,
            "max_income": 50000.0,
        },
    )
    await admin_client.post(
        "/listings/",
        json={
            "title": "Listing B",
            "city": "Toronto",
            "province": "ON",
            "rent_amount": 1400.0,
        },
    )

    # Generate matches
    response = await client.post("/matches/generate")
    assert response.status_code == 201
    matches = response.json()
    assert len(matches) >= 1
    # Matches should be sorted by score descending
    scores = [m["score"] for m in matches]
    assert scores == sorted(scores, reverse=True)


@pytest.mark.anyio
async def test_list_my_matches(
    client: AsyncClient, admin_client: AsyncClient, mock_user
):
    # Setup
    await client.post(
        "/users/register",
        json={
            "clerk_id": mock_user.clerk_id,
            "email": mock_user.email,
            "first_name": mock_user.first_name,
            "last_name": mock_user.last_name,
        },
    )
    await client.post(
        "/users/me/eligibility",
        json={
            "annual_income": 35000.0,
            "household_size": 2,
            "province": "ON",
            "city": "Toronto",
            "max_rent": 1500.0,
            "consent_given": True,
        },
    )
    await admin_client.post(
        "/listings/",
        json={
            "title": "Match List Test",
            "city": "Toronto",
            "province": "ON",
            "rent_amount": 1200.0,
        },
    )
    await client.post("/matches/generate")

    response = await client.get("/matches")
    assert response.status_code == 200
    assert len(response.json()) >= 1


@pytest.mark.anyio
async def test_update_match_status(
    client: AsyncClient, admin_client: AsyncClient, mock_user
):
    # Setup
    await client.post(
        "/users/register",
        json={
            "clerk_id": mock_user.clerk_id,
            "email": mock_user.email,
            "first_name": mock_user.first_name,
            "last_name": mock_user.last_name,
        },
    )
    await client.post(
        "/users/me/eligibility",
        json={
            "annual_income": 35000.0,
            "household_size": 2,
            "province": "ON",
            "city": "Toronto",
            "max_rent": 1500.0,
            "consent_given": True,
        },
    )
    await admin_client.post(
        "/listings/",
        json={
            "title": "Status Update Test",
            "city": "Toronto",
            "province": "ON",
            "rent_amount": 1200.0,
        },
    )
    await client.post("/matches/generate")

    matches_resp = await client.get("/matches")
    match_id = matches_resp.json()[0]["id"]

    response = await client.patch(
        f"/matches/{match_id}",
        json={"status": "accepted"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "accepted"
