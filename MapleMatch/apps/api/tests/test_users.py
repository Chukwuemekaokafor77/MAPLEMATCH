"""Tests for user registration, profile, and eligibility endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_register_user(client: AsyncClient):
    response = await client.post(
        "/users/register",
        json={
            "clerk_id": "clerk_new_user",
            "email": "newuser@example.com",
            "first_name": "New",
            "last_name": "User",
            "role": "applicant",
            "preferred_language": "en",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["role"] == "applicant"
    assert data["first_name"] == "New"


@pytest.mark.anyio
async def test_register_duplicate_user(client: AsyncClient):
    payload = {
        "clerk_id": "clerk_dup_user",
        "email": "dup@example.com",
        "first_name": "Dup",
        "last_name": "User",
    }
    response1 = await client.post("/users/register", json=payload)
    assert response1.status_code == 201

    response2 = await client.post("/users/register", json=payload)
    assert response2.status_code == 409


@pytest.mark.anyio
async def test_get_me(client: AsyncClient):
    response = await client.get("/users/me")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["role"] == "applicant"


@pytest.mark.anyio
async def test_update_me(client: AsyncClient):
    response = await client.patch(
        "/users/me",
        json={"first_name": "Updated", "preferred_language": "fr"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == "Updated"
    assert data["preferred_language"] == "fr"


@pytest.mark.anyio
async def test_create_eligibility_profile(client: AsyncClient, mock_user):
    # Ensure user exists in DB first
    response = await client.post(
        "/users/register",
        json={
            "clerk_id": mock_user.clerk_id,
            "email": mock_user.email,
            "first_name": mock_user.first_name,
            "last_name": mock_user.last_name,
        },
    )

    response = await client.post(
        "/users/me/eligibility",
        json={
            "annual_income": 35000.0,
            "household_size": 3,
            "priority_group": "newcomer",
            "province": "ON",
            "city": "Toronto",
            "postal_code": "M5V 1A1",
            "max_rent": 1500.0,
            "consent_given": True,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["annual_income"] == 35000.0
    assert data["household_size"] == 3
    assert data["priority_group"] == "newcomer"
    assert data["consent_given"] is True
    assert data["consent_date"] is not None


@pytest.mark.anyio
async def test_get_eligibility_profile_not_found(client: AsyncClient):
    response = await client.get("/users/me/eligibility")
    assert response.status_code == 404


@pytest.mark.anyio
async def test_list_users_forbidden_for_applicant(client: AsyncClient):
    response = await client.get("/users/")
    assert response.status_code == 403


@pytest.mark.anyio
async def test_list_users_allowed_for_admin(admin_client: AsyncClient):
    response = await admin_client.get("/users/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
