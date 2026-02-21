"""Tests for authentication endpoints."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test health check endpoint."""
    response = await client.get("/api/v1/auth/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    """Test successful user registration."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "password123",
        },
    )
    
    assert response.status_code == 201
    data = response.json()
    assert "user" in data
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["email"] == "newuser@example.com"


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    """Test registration with duplicate email."""
    # First registration
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "duplicate@example.com",
            "password": "password123",
        },
    )
    
    # Second registration with same email
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "duplicate@example.com",
            "password": "password123",
        },
    )
    
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_register_weak_password(client: AsyncClient):
    """Test registration with weak password."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "short",
        },
    )
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    """Test successful login."""
    # Register user
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "login@example.com",
            "password": "password123",
        },
    )
    
    # Login
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "login@example.com",
            "password": "password123",
        },
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient):
    """Test login with invalid credentials."""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "wrongpassword",
        },
    )
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token(client: AsyncClient):
    """Test token refresh."""
    # Register user
    register_response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "refresh@example.com",
            "password": "password123",
        },
    )
    
    refresh_token = register_response.json()["refresh_token"]
    
    # Refresh token
    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_logout(client: AsyncClient, auth_headers: dict[str, str]):
    """Test logout."""
    response = await client.post(
        "/api/v1/auth/logout",
        headers=auth_headers,
    )
    
    assert response.status_code == 204
