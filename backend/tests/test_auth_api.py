"""
Tests for Authentication API — register, login, refresh, /me.
"""

import pytest


class TestAuthApi:
    """Auth endpoint tests."""

    def test_register_new_user(self, client):
        """Register a new user and receive tokens."""
        resp = client.post("/api/auth/register", json={
            "username": "newuser",
            "email": "newuser@test.com",
            "password": "securepass123",
            "full_name": "New User",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["user"]["email"] == "newuser@test.com"

    def test_register_duplicate_email(self, client):
        """Registering with an existing email should fail."""
        payload = {
            "username": "user1",
            "email": "dup@test.com",
            "password": "pass123",
        }
        client.post("/api/auth/register", json=payload)
        resp = client.post("/api/auth/register", json={
            "username": "user2",
            "email": "dup@test.com",
            "password": "pass456",
        })
        assert resp.status_code == 409

    def test_login_success(self, client):
        """Login with correct credentials."""
        client.post("/api/auth/register", json={
            "username": "loginuser",
            "email": "login@test.com",
            "password": "mypassword",
        })
        resp = client.post("/api/auth/login", json={
            "email": "login@test.com",
            "password": "mypassword",
        })
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_login_wrong_password(self, client):
        """Login with wrong password should fail."""
        client.post("/api/auth/register", json={
            "username": "wrongpw",
            "email": "wrongpw@test.com",
            "password": "correctpass",
        })
        resp = client.post("/api/auth/login", json={
            "email": "wrongpw@test.com",
            "password": "wrongpass",
        })
        assert resp.status_code == 401

    def test_refresh_token(self, client):
        """Refresh token should return a new access token."""
        reg = client.post("/api/auth/register", json={
            "username": "refreshuser",
            "email": "refresh@test.com",
            "password": "pass123",
        })
        refresh_token = reg.json()["refresh_token"]

        resp = client.post("/api/auth/refresh", json={
            "refresh_token": refresh_token,
        })
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_get_me(self, client, auth_headers):
        """GET /me should return current user profile."""
        resp = client.get("/api/auth/me", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "email" in data
        assert "username" in data
