"""
SkyModderAI - Integration Tests

End-to-end tests for critical user journeys and API endpoints.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from collections.abc import Generator
from typing import Any
from unittest.mock import patch

import pytest

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine

from app import app
from models import Base

# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture(scope="module")
def test_database() -> Generator[str, None, None]:
    """Create a temporary test database."""
    # Create temporary SQLite database
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)

    database_url = f"sqlite:///{db_path}"

    # Create tables
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)

    yield database_url

    # Cleanup
    os.unlink(db_path)


@pytest.fixture(scope="module")
def test_app(test_database: str) -> Generator[Any, None, None]:
    """Create test Flask application."""
    # Configure app for testing
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    app.config["SECRET_KEY"] = "test-secret-key-for-integration-testing"
    app.config["DATABASE_URL"] = test_database
    app.config["SESSION_COOKIE_SECURE"] = False

    # Override DB_FILE to use test database
    import db as db_module

    db_path = test_database.replace("sqlite:///", "")
    db_module.DB_FILE = db_path

    # Also override app.py's DB_FILE
    import app as app_module

    app_module.DB_FILE = db_path

    with app.app_context():
        yield app


@pytest.fixture(scope="function")
def client(test_app: Any) -> Generator[Any, None, None]:
    """Create test client."""
    with test_app.test_client() as client:
        yield client


@pytest.fixture(scope="function")
def authenticated_client(client: Any) -> Generator[Any, None, None]:
    """Create authenticated test client."""
    test_email = "test@example.com"

    # Register and login a test user
    # Patch email sending to avoid SMTP errors in tests
    with patch("app.make_verification_token", return_value="test-token"):
        with patch("app.send_verification_email"):
            client.post(
                "/auth/signup",
                data={
                    "email": test_email,
                    "password": "TestPassword123!",
                    "confirm_password": "TestPassword123!",
                },
                follow_redirects=True,
            )

    # Manually verify the user
    from db import set_user_verified

    set_user_verified(test_email)

    # Login
    client.post(
        "/auth/login",
        data={"email": test_email, "password": "TestPassword123!"},
        follow_redirects=True,
    )

    yield client


@pytest.fixture(scope="function")
def api_client(client: Any) -> Generator[Any, None, None]:
    """Create API client with API key."""
    test_email = "api-test@example.com"

    # Register and login (patch email sending)
    with patch("app.make_verification_token", return_value="test-token"):
        with patch("app.send_verification_email"):
            client.post(
                "/auth/signup",
                data={
                    "email": test_email,
                    "password": "TestPassword123!",
                    "confirm_password": "TestPassword123!",
                },
                follow_redirects=True,
            )

    # Manually verify the user
    from db import set_user_verified

    set_user_verified(test_email)

    # Login
    client.post(
        "/auth/login",
        data={"email": test_email, "password": "TestPassword123!"},
        follow_redirects=True,
    )

    # Create API key
    response = client.post(
        "/api/keys",
        data={"label": "Test API Key"},
        content_type="application/json",
    )

    if response.status_code == 200:
        api_key = json.loads(response.data)["key"]
        client.environ_base["HTTP_AUTHORIZATION"] = f"Bearer {api_key}"

    yield client


# =============================================================================
# Authentication Integration Tests
# =============================================================================


class TestAuthenticationIntegration:
    """Integration tests for authentication flow."""

    def test_user_registration(self, client: Any) -> None:
        """Test complete user registration flow."""
        # Patch email sending to avoid SMTP errors in tests
        with patch("app.make_verification_token", return_value="test-token"):
            with patch("app.send_verification_email"):
                response = client.post(
                    "/auth/signup",
                    data={
                        "email": "newuser@example.com",
                        "password": "SecurePassword123!",
                        "confirm_password": "SecurePassword123!",
                    },
                    follow_redirects=True,
                )

        assert response.status_code == 200
        # Should redirect to login or show verification message

    def test_user_login(self, client: Any) -> None:
        """Test user login flow."""
        test_email = "login-test@example.com"

        # First register (patch email sending)
        with patch("app.make_verification_token", return_value="test-token"):
            with patch("app.send_verification_email"):
                client.post(
                    "/auth/signup",
                    data={
                        "email": test_email,
                        "password": "TestPassword123!",
                        "confirm_password": "TestPassword123!",
                    },
                    follow_redirects=True,
                )

        # Manually verify the user in the database
        from db import set_user_verified

        set_user_verified(test_email)

        # Then login
        response = client.post(
            "/auth/login",
            data={"email": test_email, "password": "TestPassword123!"},
            follow_redirects=True,
        )

        assert response.status_code == 200

    def test_invalid_login(self, client: Any) -> None:
        """Test login with invalid credentials."""
        response = client.post(
            "/auth/login",
            data={"email": "nonexistent@example.com", "password": "WrongPassword"},
            follow_redirects=True,
        )

        assert response.status_code == 401

    def test_password_validation(self, client: Any) -> None:
        """Test password validation during registration."""
        # Weak password
        response = client.post(
            "/auth/signup",
            data={
                "email": "weak@example.com",
                "password": "123",
                "confirm_password": "123",
            },
            follow_redirects=True,
        )

        assert response.status_code == 400

    def test_duplicate_registration(self, client: Any) -> None:
        """Test duplicate email registration."""
        # First registration (patch email sending)
        with patch("app.make_verification_token", return_value="test-token"):
            with patch("app.send_verification_email"):
                client.post(
                    "/auth/signup",
                    data={
                        "email": "duplicate@example.com",
                        "password": "TestPassword123!",
                        "confirm_password": "TestPassword123!",
                    },
                    follow_redirects=True,
                )

        # Second registration with same email
        response = client.post(
            "/auth/signup",
            data={
                "email": "duplicate@example.com",
                "password": "TestPassword123!",
                "confirm_password": "TestPassword123!",
            },
            follow_redirects=True,
        )

        assert response.status_code == 400


# =============================================================================
# API Integration Tests
# =============================================================================


class TestAPIIntegration:
    """Integration tests for API endpoints."""

    def test_analyze_endpoint(self, api_client: Any) -> None:
        """Test mod list analysis via API."""
        mod_list = """
        Skyrim.esm
        Update.esm
        Dawnguard.esm
        HearthFires.esm
        Dragonborn.esm
        USSEP.esp
        SkyUI.esp
        """

        response = api_client.post(
            "/api/v1/analyze",
            data=json.dumps(
                {
                    "mod_list": mod_list.strip(),
                    "game": "skyrimse",
                }
            ),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert "mod_count" in data
        assert "conflicts" in data

    def test_search_endpoint(self, api_client: Any) -> None:
        """Test mod search via API."""
        response = api_client.get("/api/v1/search?q=USSEP&game=skyrimse")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert "results" in data

    def test_health_endpoint(self, client: Any) -> None:
        """Test API health check."""
        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["status"] == "healthy"

    def test_platform_capabilities(self, client: Any) -> None:
        """Test platform capabilities endpoint."""
        response = client.get("/api/v1/platform-capabilities")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert "capabilities" in data

    def test_unauthorized_api_access(self, client: Any) -> None:
        """Test API access without authentication."""
        response = client.post(
            "/api/v1/analyze",
            data=json.dumps({"mod_list": "test.esp", "game": "skyrimse"}),
            content_type="application/json",
        )

        assert response.status_code == 401


# =============================================================================
# Analysis Integration Tests
# =============================================================================


class TestAnalysisIntegration:
    """Integration tests for analysis functionality."""

    def test_full_analysis_flow(self, authenticated_client: Any) -> None:
        """Test complete analysis flow from input to results."""
        mod_list = """
        Skyrim.esm
        Update.esm
        USSEP.esp
        SkyUI.esp
        Ordinator - Perks of Skyrim.esp
        Apocalypse - Magic of Skyrim.esp
        """

        response = authenticated_client.post(
            "/analysis/",
            data={"mod_list": mod_list.strip(), "game": "skyrimse"},
            follow_redirects=True,
        )

        assert response.status_code == 200

    def test_invalid_game_id(self, authenticated_client: Any) -> None:
        """Test analysis with invalid game ID."""
        response = authenticated_client.post(
            "/analysis/",
            data={"mod_list": "test.esp", "game": "invalid_game"},
            follow_redirects=True,
        )

        assert response.status_code == 400

    def test_empty_mod_list(self, authenticated_client: Any) -> None:
        """Test analysis with empty mod list."""
        response = authenticated_client.post(
            "/analysis/",
            data={"mod_list": "", "game": "skyrimse"},
            follow_redirects=True,
        )

        assert response.status_code == 400


# =============================================================================
# Community Integration Tests
# =============================================================================


class TestCommunityIntegration:
    """Integration tests for community features."""

    def test_create_post(self, authenticated_client: Any) -> None:
        """Test creating a community post."""
        response = authenticated_client.post(
            "/community/post",
            data={
                "content": "Test post content",
                "tag": "general",
            },
            follow_redirects=True,
        )

        assert response.status_code == 200

    def test_create_reply(self, authenticated_client: Any) -> None:
        """Test creating a community reply."""
        # First create a post
        authenticated_client.post(
            "/community/post",
            data={
                "content": "Test post for reply",
                "tag": "general",
            },
            follow_redirects=True,
        )

        # Then create a reply
        response = authenticated_client.post(
            "/community/post/1/reply",
            data={"content": "Test reply content"},
            follow_redirects=True,
        )

        assert response.status_code == 200

    def test_vote_post(self, authenticated_client: Any) -> None:
        """Test voting on a post."""
        # Create a post first
        authenticated_client.post(
            "/community/post",
            data={
                "content": "Test post for voting",
                "tag": "general",
            },
            follow_redirects=True,
        )

        # Vote on the post
        response = authenticated_client.post(
            "/community/post/1/vote",
            data={"vote": "1"},
            follow_redirects=True,
        )

        assert response.status_code == 200


# =============================================================================
# Error Handling Integration Tests
# =============================================================================


class TestErrorHandlingIntegration:
    """Integration tests for error handling."""

    def test_404_error(self, client: Any) -> None:
        """Test 404 error handling."""
        response = client.get("/nonexistent-page")
        assert response.status_code == 404

    def test_500_error_handling(self, client: Any) -> None:
        """Test that 500 errors are handled gracefully."""
        # This would require mocking a failure scenario
        pass

    def test_validation_error_response(self, api_client: Any) -> None:
        """Test validation error response format."""
        response = api_client.post(
            "/api/v1/analyze",
            data=json.dumps({"mod_list": "", "game": "skyrimse"}),
            content_type="application/json",
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data or "success" in data


# =============================================================================
# Performance Integration Tests
# =============================================================================


class TestPerformanceIntegration:
    """Integration tests for performance."""

    def test_large_mod_list_analysis(self, api_client: Any) -> None:
        """Test analysis of large mod list (performance test)."""
        # Generate 500 mod entries
        mods = [f"Mod_{i:04d}.esp" for i in range(500)]
        mod_list = "\n".join(mods)

        import time

        start = time.time()

        response = api_client.post(
            "/api/v1/analyze",
            data=json.dumps(
                {
                    "mod_list": mod_list,
                    "game": "skyrimse",
                }
            ),
            content_type="application/json",
        )

        elapsed = time.time() - start

        assert response.status_code == 200
        # Should complete in under 5 seconds for 500 mods
        assert elapsed < 5.0, f"Performance regression: {elapsed:.2f}s > 5s budget"


# =============================================================================
# Main Test Runner
# =============================================================================


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
