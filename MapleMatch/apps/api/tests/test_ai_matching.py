"""Tests for AI matching engine: embeddings, recommender, wait-time, and endpoints."""

from unittest.mock import patch

import numpy as np
import pytest
from httpx import AsyncClient

from app.models import EligibilityProfile, Listing, PriorityGroup
from app.services.embeddings import (
    batch_compute_similarities,
    compute_similarity,
    listing_to_text,
    profile_to_text,
)
from app.services.recommender import (
    HybridMatchResult,
    MatchFactor,
    batch_hybrid_match,
    hybrid_match,
)
from app.services.wait_time import WaitTimeEstimate, predict_wait_time


# === Helpers ===


def _make_profile(**kwargs) -> EligibilityProfile:
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
    defaults = {
        "title": "Test Listing",
        "description": "Affordable housing in Toronto",
        "city": "Toronto",
        "province": "ON",
        "rent_amount": 1200.0,
        "bedrooms": 2,
        "max_income": 50000.0,
        "min_household_size": 1,
        "max_household_size": 5,
        "priority_groups": "newcomer,senior",
        "is_rgi": False,
        "is_accessible": False,
        "amenities": "laundry,parking",
    }
    defaults.update(kwargs)
    return Listing(**defaults)


# === Embedding Service Tests ===


class TestProfileToText:
    def test_full_profile(self):
        profile = _make_profile()
        text = profile_to_text(profile)
        assert "35,000" in text
        assert "household of 3" in text
        assert "newcomer" in text
        assert "ON" in text
        assert "1,500" in text

    def test_accessible_profile(self):
        profile = _make_profile(needs_accessible_unit=True)
        text = profile_to_text(profile)
        assert "accessible" in text.lower()

    def test_empty_profile(self):
        profile = _make_profile(
            annual_income=None,
            household_size=None,
            priority_group=PriorityGroup.none,
            province=None,
            city=None,
            max_rent=None,
            needs_accessible_unit=False,
        )
        text = profile_to_text(profile)
        assert "Applicant" in text


class TestListingToText:
    def test_full_listing(self):
        listing = _make_listing()
        text = listing_to_text(listing)
        assert "Test Listing" in text
        assert "Toronto" in text
        assert "1,200" in text
        assert "2 bedroom" in text

    def test_rgi_listing(self):
        listing = _make_listing(is_rgi=True)
        text = listing_to_text(listing)
        assert "rent geared to income" in text.lower()

    def test_accessible_listing(self):
        listing = _make_listing(is_accessible=True)
        text = listing_to_text(listing)
        assert "accessible" in text.lower()


class TestComputeSimilarity:
    def test_identical_vectors(self):
        vec = np.array([1.0, 0.0, 0.0])
        assert compute_similarity(vec, vec) == pytest.approx(1.0)

    def test_orthogonal_vectors(self):
        a = np.array([1.0, 0.0, 0.0])
        b = np.array([0.0, 1.0, 0.0])
        assert compute_similarity(a, b) == pytest.approx(0.0)

    def test_clamped_to_zero(self):
        a = np.array([1.0, 0.0])
        b = np.array([-1.0, 0.0])
        assert compute_similarity(a, b) == 0.0


# === Recommender Tests ===


class TestHybridMatch:
    """Test the hybrid recommender with semantic/ML disabled (rules-only)."""

    def test_eligible_match_rules_only(self):
        profile = _make_profile()
        listing = _make_listing()
        result = hybrid_match(profile, listing, use_semantic=False, use_ml=False)
        assert result.eligible is True
        assert result.final_score > 0
        assert result.rule_score > 0
        assert result.semantic_score == 0.0
        assert result.ml_score == 0.0
        assert len(result.explanation) > 0

    def test_ineligible_match(self):
        profile = _make_profile(annual_income=100000.0)
        listing = _make_listing(max_income=50000.0)
        result = hybrid_match(profile, listing, use_semantic=False, use_ml=False)
        assert result.eligible is False
        assert result.final_score == 0.0

    def test_with_ml_features(self):
        profile = _make_profile()
        listing = _make_listing()
        result = hybrid_match(profile, listing, use_semantic=False, use_ml=True)
        assert result.eligible is True
        assert result.ml_score > 0
        assert len(result.factors) >= 2  # rules + ML

    def test_factors_have_details(self):
        profile = _make_profile()
        listing = _make_listing()
        result = hybrid_match(profile, listing, use_semantic=False, use_ml=True)
        for factor in result.factors:
            assert factor.name
            assert 0 <= factor.score <= 1
            assert factor.weight > 0
            assert factor.details

    def test_explanation_includes_score(self):
        profile = _make_profile()
        listing = _make_listing()
        result = hybrid_match(profile, listing, use_semantic=False, use_ml=False)
        assert "Match score:" in result.explanation


class TestBatchHybridMatch:
    def test_empty_listings(self):
        profile = _make_profile()
        results = batch_hybrid_match(profile, [], use_semantic=False, use_ml=False)
        assert results == []

    def test_filters_ineligible(self):
        profile = _make_profile(annual_income=100000.0)
        listings = [_make_listing(max_income=50000.0)]
        results = batch_hybrid_match(
            profile, listings, use_semantic=False, use_ml=False
        )
        assert len(results) == 0

    def test_sorts_by_score(self):
        profile = _make_profile()
        listings = [
            _make_listing(title="A", rent_amount=1200.0),
            _make_listing(title="B", rent_amount=800.0),
            _make_listing(title="C", rent_amount=1000.0),
        ]
        results = batch_hybrid_match(
            profile, listings, use_semantic=False, use_ml=True
        )
        scores = [r[1].final_score for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_multiple_eligible(self):
        profile = _make_profile()
        listings = [
            _make_listing(title=f"Listing {i}") for i in range(5)
        ]
        results = batch_hybrid_match(
            profile, listings, use_semantic=False, use_ml=False
        )
        assert len(results) == 5


# === Wait-Time Tests ===


class TestWaitTime:
    def test_basic_prediction(self):
        profile = _make_profile()
        listing = _make_listing()
        wt = predict_wait_time(profile, listing)
        assert wt.estimated_days > 0
        assert wt.lower_bound_days <= wt.estimated_days
        assert wt.upper_bound_days >= wt.estimated_days
        assert 0 < wt.confidence <= 1.0
        assert wt.method == "heuristic"
        assert len(wt.factors) > 0

    def test_priority_group_reduces_wait(self):
        profile_priority = _make_profile(priority_group=PriorityGroup.fleeing_violence)
        profile_none = _make_profile(priority_group=PriorityGroup.none)
        listing = _make_listing()

        wt_priority = predict_wait_time(profile_priority, listing)
        wt_none = predict_wait_time(profile_none, listing)
        assert wt_priority.estimated_days < wt_none.estimated_days

    def test_rgi_increases_wait(self):
        profile = _make_profile(priority_group=PriorityGroup.none)
        listing_rgi = _make_listing(is_rgi=True)
        listing_no_rgi = _make_listing(is_rgi=False)

        wt_rgi = predict_wait_time(profile, listing_rgi)
        wt_no_rgi = predict_wait_time(profile, listing_no_rgi)
        assert wt_rgi.estimated_days > wt_no_rgi.estimated_days

    def test_large_household_longer_wait(self):
        profile_large = _make_profile(
            household_size=6, priority_group=PriorityGroup.none
        )
        profile_small = _make_profile(
            household_size=1, priority_group=PriorityGroup.none
        )
        listing = _make_listing()

        wt_large = predict_wait_time(profile_large, listing)
        wt_small = predict_wait_time(profile_small, listing)
        assert wt_large.estimated_days > wt_small.estimated_days

    def test_custom_listing_wait(self):
        """If listing has estimated_wait_days set, use it as base."""
        profile = _make_profile(priority_group=PriorityGroup.none)
        listing = _make_listing(estimated_wait_days=30)
        wt = predict_wait_time(profile, listing)
        assert any("30" in f for f in wt.factors)

    def test_province_affects_wait(self):
        profile = _make_profile(priority_group=PriorityGroup.none)
        listing_on = _make_listing(province="ON")
        listing_yt = _make_listing(province="YT")

        wt_on = predict_wait_time(profile, listing_on)
        wt_yt = predict_wait_time(profile, listing_yt)
        assert wt_on.estimated_days > wt_yt.estimated_days


# === Integration Tests for AI Endpoints ===


async def _setup_user_and_profile(
    client: AsyncClient, admin_client: AsyncClient, mock_user
) -> str:
    """Helper: register user, create profile, create listing. Returns listing_id."""
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
    listing_resp = await admin_client.post(
        "/listings/",
        json={
            "title": "AI Match Test Listing",
            "description": "Affordable housing in Toronto",
            "city": "Toronto",
            "province": "ON",
            "rent_amount": 1200.0,
            "max_income": 50000.0,
            "bedrooms": 2,
        },
    )
    return listing_resp.json()["id"]


@pytest.mark.anyio
async def test_smart_match_endpoint(
    client: AsyncClient, admin_client: AsyncClient, mock_user
):
    await _setup_user_and_profile(client, admin_client, mock_user)

    response = await client.post(
        "/matches/smart?use_semantic=false&use_ml=true&limit=10"
    )
    assert response.status_code == 200
    results = response.json()
    assert len(results) >= 1

    r = results[0]
    assert r["eligible"] is True
    assert r["final_score"] > 0
    assert "factors" in r
    assert "explanation" in r
    assert r["listing_title"] == "AI Match Test Listing"
    assert r["wait_time_days"] > 0
    assert r["wait_time_confidence"] > 0


@pytest.mark.anyio
async def test_smart_match_no_profile(client: AsyncClient):
    response = await client.post("/matches/smart?use_semantic=false")
    assert response.status_code == 400


@pytest.mark.anyio
async def test_smart_match_no_listings(
    client: AsyncClient, admin_client: AsyncClient, mock_user
):
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
            "consent_given": True,
        },
    )
    response = await client.post("/matches/smart?use_semantic=false&use_ml=false")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.anyio
async def test_smart_match_and_save(
    client: AsyncClient, admin_client: AsyncClient, mock_user
):
    await _setup_user_and_profile(client, admin_client, mock_user)

    response = await client.post(
        "/matches/smart/save?use_semantic=false&use_ml=true"
    )
    assert response.status_code == 201
    matches = response.json()
    assert len(matches) >= 1
    assert matches[0]["score"] > 0

    # Running again should return empty (no duplicates)
    response2 = await client.post(
        "/matches/smart/save?use_semantic=false&use_ml=true"
    )
    assert response2.status_code == 201
    assert response2.json() == []


@pytest.mark.anyio
async def test_wait_time_estimate_endpoint(
    client: AsyncClient, admin_client: AsyncClient, mock_user
):
    listing_id = await _setup_user_and_profile(client, admin_client, mock_user)

    response = await client.post(
        "/wait-time/estimate",
        json={"listing_id": listing_id},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["listing_id"] == listing_id
    assert data["estimated_days"] > 0
    assert data["lower_bound_days"] <= data["estimated_days"]
    assert data["upper_bound_days"] >= data["estimated_days"]
    assert data["confidence"] > 0
    assert data["method"] == "heuristic"
    assert len(data["factors"]) > 0


@pytest.mark.anyio
async def test_wait_time_listing_not_found(
    client: AsyncClient, admin_client: AsyncClient, mock_user
):
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
            "consent_given": True,
        },
    )
    response = await client.post(
        "/wait-time/estimate",
        json={"listing_id": "00000000-0000-0000-0000-000000000000"},
    )
    assert response.status_code == 404


@pytest.mark.anyio
async def test_wait_time_no_profile(client: AsyncClient):
    response = await client.post(
        "/wait-time/estimate",
        json={"listing_id": "00000000-0000-0000-0000-000000000000"},
    )
    assert response.status_code == 400
