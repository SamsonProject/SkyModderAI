"""
Tests for security and logging utilities.
"""

import pytest
from flask import Flask

from logging_utils import (
    SensitiveDataFilter,
    redact_api_key,
    redact_customer_id,
    redact_email,
    redact_password,
)
from security_utils import (
    RateLimiter,
    constant_time_compare,
    generate_secure_token,
    get_key_prefix,
    hash_api_key,
    mask_sensitive_data,
    rate_limit,
    sanitize_user_agent,
    validate_email,
    validate_game_id,
    validate_mod_list,
    validate_password,
    validate_search_query,
)

# =============================================================================
# Rate Limiter Tests
# =============================================================================


class TestRateLimiter:
    """Tests for RateLimiter class."""

    def test_rate_limiter_allows_under_limit(self) -> None:
        """Test that requests under limit are allowed."""
        limiter = RateLimiter()
        identifier = "test_user_1"

        # Should not be rate limited
        assert not limiter.is_rate_limited(identifier, limit=5, window=60)
        assert not limiter.is_rate_limited(identifier, limit=5, window=60)
        assert not limiter.is_rate_limited(identifier, limit=5, window=60)

    def test_rate_limiter_blocks_over_limit(self) -> None:
        """Test that requests over limit are blocked."""
        limiter = RateLimiter()
        identifier = "test_user_2"

        # Make 5 requests
        for _ in range(5):
            limiter.is_rate_limited(identifier, limit=5, window=60)

        # 6th request should be blocked
        assert limiter.is_rate_limited(identifier, limit=5, window=60)

    def test_rate_limiter_clear(self) -> None:
        """Test clearing rate limit data."""
        limiter = RateLimiter()
        identifier = "test_user_3"

        # Make some requests
        limiter.is_rate_limited(identifier, limit=2, window=60)
        limiter.is_rate_limited(identifier, limit=2, window=60)

        # Clear and verify
        limiter.clear(identifier)
        assert not limiter.is_rate_limited(identifier, limit=2, window=60)

    def test_retry_after(self) -> None:
        """Test retry after calculation."""
        limiter = RateLimiter()
        identifier = "test_user_4"

        # Initially should be 0
        assert limiter.get_retry_after(identifier) == 0

        # Make requests until limited
        for _ in range(3):
            limiter.is_rate_limited(identifier, limit=3, window=60)

        # Should have a retry after value
        retry_after = limiter.get_retry_after(identifier, window=60)
        assert 0 <= retry_after <= 60


# =============================================================================
# Email Validation Tests
# =============================================================================


class TestValidateEmail:
    """Tests for email validation."""

    def test_valid_email(self) -> None:
        """Test valid email addresses."""
        valid_emails = [
            "user@example.com",
            "user.name@example.com",
            "user+tag@example.co.uk",
            "user123@test.org",
        ]

        for email in valid_emails:
            is_valid, error = validate_email(email)
            assert is_valid, f"Expected {email} to be valid, got error: {error}"

    def test_invalid_email(self) -> None:
        """Test invalid email addresses."""
        invalid_emails = [
            None,
            "",
            "notanemail",
            "@example.com",
            "user@",
            "user@.com",
            "user@example",
        ]

        for email in invalid_emails:
            is_valid, error = validate_email(email)
            assert not is_valid, f"Expected {email} to be invalid"

    def test_email_too_long(self) -> None:
        """Test email that exceeds max length."""
        long_email = "a" * 300 + "@example.com"
        is_valid, error = validate_email(long_email)
        assert not is_valid
        assert "too long" in error.lower()


# =============================================================================
# Password Validation Tests
# =============================================================================


class TestValidatePassword:
    """Tests for password validation."""

    def test_valid_password(self) -> None:
        """Test valid passwords."""
        valid_passwords = ["password123", "SecurePass1", "abc12345678"]

        for password in valid_passwords:
            is_valid, error = validate_password(password)
            assert is_valid, f"Expected {password} to be valid, got error: {error}"

    def test_password_too_short(self) -> None:
        """Test passwords that are too short."""
        short_passwords = ["abc12", "pass1", "1234567"]

        for password in short_passwords:
            is_valid, error = validate_password(password)
            assert not is_valid
            assert "at least" in error.lower()

    def test_password_too_long(self) -> None:
        """Test password that exceeds max length."""
        long_password = "a" * 200
        is_valid, error = validate_password(long_password)
        assert not is_valid
        assert "too long" in error.lower()

    def test_password_complexity(self) -> None:
        """Test password complexity requirements."""
        # No letters
        is_valid, error = validate_password("12345678")
        assert not is_valid

        # No numbers
        is_valid, error = validate_password("abcdefgh")
        assert not is_valid


# =============================================================================
# Search Query Validation Tests
# =============================================================================


class TestValidateSearchQuery:
    """Tests for search query validation."""

    def test_valid_query(self) -> None:
        """Test valid search queries."""
        valid_queries = ["skyrim", "mod name", "USSEP", "test123"]

        for query in valid_queries:
            is_valid, sanitized, error = validate_search_query(query)
            assert is_valid, f"Expected {query} to be valid, got error: {error}"
            assert sanitized == query

    def test_invalid_query(self) -> None:
        """Test invalid search queries."""
        invalid_queries = [None, "", "   "]

        for query in invalid_queries:
            is_valid, sanitized, error = validate_search_query(query)
            assert not is_valid

    def test_query_sanitization(self) -> None:
        """Test that harmful characters are removed."""
        query = 'test<script>alert("xss")</script>'
        is_valid, sanitized, error = validate_search_query(query)
        assert is_valid
        assert "<" not in sanitized
        assert ">" not in sanitized


# =============================================================================
# Mod List Validation Tests
# =============================================================================


class TestValidateModList:
    """Tests for mod list validation."""

    def test_valid_mod_list(self) -> None:
        """Test valid mod list."""
        mod_list = "USSEP.esp\nSkyUI.esp\nOrdinator.esp"
        is_valid, sanitized, error = validate_mod_list(mod_list)
        assert is_valid
        assert sanitized == mod_list

    def test_empty_mod_list(self) -> None:
        """Test empty mod list."""
        is_valid, sanitized, error = validate_mod_list(None)
        assert not is_valid

    def test_mod_list_sanitization(self) -> None:
        """Test that control characters are removed."""
        mod_list = "USSEP.esp\x00\x01\x02SkyUI.esp"
        is_valid, sanitized, error = validate_mod_list(mod_list)
        assert is_valid
        assert "\x00" not in sanitized


# =============================================================================
# Game ID Validation Tests
# =============================================================================


class TestValidateGameId:
    """Tests for game ID validation."""

    def test_valid_game_id(self) -> None:
        """Test valid game IDs."""
        allowed = {"skyrimse", "fallout4", "oblivion"}

        for game_id in ["skyrimse", "SKYRIMSE", "  fallout4  "]:
            is_valid, normalized, error = validate_game_id(game_id, allowed)
            assert is_valid, f"Expected {game_id} to be valid, got error: {error}"
            assert normalized == normalized.lower().strip()

    def test_invalid_game_id(self) -> None:
        """Test invalid game IDs."""
        allowed = {"skyrimse", "fallout4"}

        is_valid, normalized, error = validate_game_id("invalid_game", allowed)
        assert not is_valid
        assert normalized == ""


# =============================================================================
# Security Helpers Tests
# =============================================================================


class TestSecurityHelpers:
    """Tests for security helper functions."""

    def test_constant_time_compare_equal(self) -> None:
        """Test constant time comparison with equal strings."""
        assert constant_time_compare("test", "test")
        assert constant_time_compare("abc123", "abc123")

    def test_constant_time_compare_not_equal(self) -> None:
        """Test constant time comparison with different strings."""
        assert not constant_time_compare("test", "Test")
        assert not constant_time_compare("abc", "def")

    def test_hash_api_key(self) -> None:
        """Test API key hashing."""
        key = "test_api_key_12345"
        hashed = hash_api_key(key)
        assert len(hashed) == 64  # SHA256 hex length
        assert hashed != key

    def test_get_key_prefix(self) -> None:
        """Test API key prefix extraction."""
        key = "abcd1234efgh5678"
        prefix = get_key_prefix(key)
        assert prefix == "abcd"

    def test_sanitize_user_agent(self) -> None:
        """Test user agent sanitization."""
        ua = "Mozilla/5.0\x00\x01 (Windows NT 10.0)"
        sanitized = sanitize_user_agent(ua)
        assert "\x00" not in sanitized
        assert "\x01" not in sanitized

    def test_generate_secure_token(self) -> None:
        """Test secure token generation."""
        token1 = generate_secure_token()
        token2 = generate_secure_token()

        assert len(token1) == 64  # 32 bytes hex = 64 chars
        assert token1 != token2

    def test_mask_sensitive_data(self) -> None:
        """Test sensitive data masking."""
        assert mask_sensitive_data("abc12345") == "abc1***"
        assert mask_sensitive_data("ab") == "***"
        assert mask_sensitive_data("") == "***"


# =============================================================================
# PII Redaction Tests
# =============================================================================


class TestPIIRedaction:
    """Tests for PII redaction functions."""

    def test_redact_email(self) -> None:
        """Test email redaction."""
        assert redact_email("user@example.com") == "u***@e***"
        assert redact_email("a@b.com") == "*@***"
        assert redact_email(None) == "***"
        assert redact_email("") == "***"

    def test_redact_api_key(self) -> None:
        """Test API key redaction."""
        assert redact_api_key("abcd1234567890") == "abcd***"
        assert redact_api_key("abc") == "***"
        assert redact_api_key(None) == "***"

    def test_redact_password(self) -> None:
        """Test password redaction."""
        assert redact_password("anypassword") == "***"
        assert redact_password(None) == "***"

    def test_redact_customer_id(self) -> None:
        """Test customer ID redaction."""
        assert redact_customer_id("cus_abc1234567890xyz") == "cus_***xyz"
        assert redact_customer_id("invalid") == "***"
        assert redact_customer_id(None) == "***"


# =============================================================================
# Sensitive Data Filter Tests
# =============================================================================


class TestSensitiveDataFilter:
    """Tests for SensitiveDataFilter."""

    def test_redact_email_in_message(self) -> None:
        """Test email redaction in log message."""
        filter_obj = SensitiveDataFilter()

        class MockRecord:
            msg = "User logged in: user@example.com"
            args = ()

        record = MockRecord()
        filter_obj.filter(record)  # type: ignore[arg-type]
        assert "[EMAIL_REDACTED]" in record.msg

    def test_redact_stripe_key_in_message(self) -> None:
        """Test Stripe key redaction in log message."""
        filter_obj = SensitiveDataFilter()

        class MockRecord:
            msg = "API key: sk_live_[REDACTED_FOR_TEST]"
            args = ()

        record = MockRecord()
        filter_obj.filter(record)  # type: ignore[arg-type]
        assert "[STRIPE_KEY_REDACTED]" in record.msg

    def test_redact_in_args_dict(self) -> None:
        """Test redaction in args dictionary."""
        filter_obj = SensitiveDataFilter()

        class MockRecord:
            msg = "User data: %s"
            args = {"email": "user@example.com", "name": "John"}

        record = MockRecord()
        filter_obj.filter(record)  # type: ignore[arg-type]
        assert record.args["email"] == "[EMAIL_REDACTED]"
        assert record.args["name"] == "John"


# =============================================================================
# Integration Tests
# =============================================================================


class TestRateLimitDecorator:
    """Tests for rate_limit decorator."""

    def test_rate_limit_decorator(self) -> None:
        """Test rate limiting decorator."""
        app = Flask(__name__)

        @app.route("/test")
        @rate_limit(limit=3, window=60)
        def test_route():
            return "OK"

        with app.test_client() as client:
            # First 3 requests should succeed
            for i in range(3):
                response = client.get("/test")
                assert response.status_code == 200

            # 4th request should be rate limited
            response = client.get("/test")
            assert response.status_code == 429
            assert "Retry-After" in response.headers


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
