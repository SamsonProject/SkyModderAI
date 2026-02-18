"""
Security utilities for SkyModderAI.
Provides rate limiting, input validation, and security helpers.
"""

from __future__ import annotations

import hashlib
import hmac
import re
import time
from collections import defaultdict
from functools import wraps
from typing import Any, Callable, Optional

from flask import Request, request

from constants import (
    MAX_EMAIL_LENGTH,
    MAX_LIST_NAME_LENGTH,
    MAX_MOD_LIST_SIZE,
    MAX_PASSWORD_LENGTH,
    MAX_SEARCH_QUERY_LENGTH,
    MIN_PASSWORD_LENGTH,
    RATE_LIMIT_ANALYZE,
    RATE_LIMIT_API,
    RATE_LIMIT_AUTH,
    RATE_LIMIT_DEFAULT,
    RATE_LIMIT_SEARCH,
    RATE_LIMIT_WINDOW,
)


# =============================================================================
# Rate Limiting
# =============================================================================


class RateLimiter:
    """
    Simple in-memory rate limiter.
    For production, consider using Redis-backed rate limiting.
    """

    def __init__(self) -> None:
        # Structure: {identifier: [(timestamp, count)]}
        self._requests: dict[str, list[tuple[float, int]]] = defaultdict(list)
        self._lock = False

    def _clean_old_requests(self, identifier: str, window: int) -> None:
        """Remove requests older than the window."""
        now = time.time()
        cutoff = now - window
        self._requests[identifier] = [
            (ts, count) for ts, count in self._requests[identifier] if ts > cutoff
        ]

    def is_rate_limited(
        self, identifier: str, limit: int, window: int = RATE_LIMIT_WINDOW
    ) -> bool:
        """
        Check if an identifier has exceeded the rate limit.

        Args:
            identifier: Unique identifier (e.g., IP, user ID, API key)
            limit: Maximum requests allowed in the window
            window: Time window in seconds

        Returns:
            True if rate limited, False otherwise
        """
        now = time.time()
        self._clean_old_requests(identifier, window)

        # Count current requests in window
        total_requests = sum(count for _, count in self._requests[identifier])

        if total_requests >= limit:
            return True

        # Record this request
        self._requests[identifier].append((now, 1))
        return False

    def get_retry_after(self, identifier: str, window: int = RATE_LIMIT_WINDOW) -> int:
        """Get seconds until the rate limit resets."""
        if identifier not in self._requests:
            return 0

        now = time.time()
        oldest_request = min(ts for ts, _ in self._requests[identifier])
        retry_after = int((oldest_request + window) - now)
        return max(0, retry_after)

    def clear(self, identifier: str) -> None:
        """Clear rate limit data for an identifier."""
        self._requests.pop(identifier, None)


# Global rate limiter instance
_rate_limiter = RateLimiter()


def rate_limit(
    limit: int = RATE_LIMIT_DEFAULT,
    window: int = RATE_LIMIT_WINDOW,
    key_func: Optional[Callable[[], str]] = None,
) -> Callable:
    """
    Decorator for rate limiting Flask routes.

    Args:
        limit: Maximum requests allowed
        window: Time window in seconds
        key_func: Function to get the rate limit key (default: remote address)

    Returns:
        Decorated function
    """

    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapped(*args: Any, **kwargs: Any) -> Any:
            from flask import jsonify, make_response

            # Get identifier
            if key_func:
                identifier = key_func()
            else:
                identifier = request.remote_addr or "unknown"

            # Check rate limit
            if _rate_limiter.is_rate_limited(identifier, limit, window):
                retry_after = _rate_limiter.get_retry_after(identifier, window)
                response = make_response(
                    jsonify(
                        {
                            "success": False,
                            "error": "Rate limit exceeded. Please try again later.",
                        }
                    ),
                    429,
                )
                response.headers["Retry-After"] = str(retry_after)
                return response

            return f(*args, **kwargs)

        return wrapped

    return decorator


# =============================================================================
# Input Validation
# =============================================================================


def validate_email(email: Optional[str]) -> tuple[bool, str]:
    """
    Validate email format and length.

    Args:
        email: Email to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not email:
        return False, "Email is required"

    email = str(email).strip().lower()

    if len(email) > MAX_EMAIL_LENGTH:
        return False, f"Email too long (max {MAX_EMAIL_LENGTH} characters)"

    # RFC 5322 compliant regex (simplified but practical)
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(pattern, email):
        return False, "Invalid email format"

    return True, ""


def validate_password(password: Optional[str]) -> tuple[bool, str]:
    """
    Validate password strength.

    Args:
        password: Password to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not password:
        return False, "Password is required"

    if len(password) < MIN_PASSWORD_LENGTH:
        return False, f"Password must be at least {MIN_PASSWORD_LENGTH} characters"

    if len(password) > MAX_PASSWORD_LENGTH:
        return False, f"Password too long (max {MAX_PASSWORD_LENGTH} characters)"

    # Check for basic complexity (at least letters and numbers)
    has_letter = bool(re.search(r"[a-zA-Z]", password))
    has_number = bool(re.search(r"\d", password))

    if not (has_letter and has_number):
        return False, "Password must contain both letters and numbers"

    return True, ""


def validate_search_query(query: Optional[str]) -> tuple[bool, str, str]:
    """
    Validate and sanitize search query.

    Args:
        query: Search query to validate

    Returns:
        Tuple of (is_valid, sanitized_query, error_message)
    """
    if not query:
        return False, "", "Search query is required"

    query = str(query).strip()

    if len(query) < 1:
        return False, "", "Search query must be at least 1 character"

    if len(query) > MAX_SEARCH_QUERY_LENGTH:
        return False, "", f"Search query too long (max {MAX_SEARCH_QUERY_LENGTH} characters)"

    # Remove potentially harmful characters
    sanitized = re.sub(r'[<>"\'\\;]', "", query)

    if not sanitized:
        return False, "", "Search query contains no valid characters"

    return True, sanitized, ""


def validate_mod_list(mod_list: Optional[str]) -> tuple[bool, str, str]:
    """
    Validate mod list input.

    Args:
        mod_list: Mod list to validate

    Returns:
        Tuple of (is_valid, sanitized_list, error_message)
    """
    if not mod_list:
        return False, "", "Mod list is required"

    mod_list = str(mod_list).strip()

    if len(mod_list) > MAX_MOD_LIST_SIZE:
        return (
            False,
            "",
            f"Mod list too large (max {MAX_MOD_LIST_SIZE // 1024}KB)",
        )

    # Basic sanitization - remove null bytes and control characters
    sanitized = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", mod_list)

    return True, sanitized, ""


def validate_list_name(name: Optional[str]) -> tuple[bool, str, str]:
    """
    Validate saved list name.

    Args:
        name: List name to validate

    Returns:
        Tuple of (is_valid, sanitized_name, error_message)
    """
    if not name:
        return False, "", "List name is required"

    name = str(name).strip()

    if len(name) < 1:
        return False, "", "List name cannot be empty"

    if len(name) > MAX_LIST_NAME_LENGTH:
        return False, "", f"List name too long (max {MAX_LIST_NAME_LENGTH} characters)"

    # Remove potentially harmful characters
    sanitized = re.sub(r'[<>"\'\\]', "", name)

    if not sanitized:
        return False, "", "List name contains no valid characters"

    return True, sanitized, ""


def validate_game_id(game_id: Optional[str], allowed_games: set[str]) -> tuple[bool, str, str]:
    """
    Validate and normalize game ID.

    Args:
        game_id: Game ID to validate
        allowed_games: Set of allowed game IDs

    Returns:
        Tuple of (is_valid, normalized_game_id, error_message)
    """
    if not game_id:
        return False, "", "Game ID is required"

    game_id = str(game_id).strip().lower()

    if not game_id:
        return False, "", "Game ID cannot be empty"

    if game_id not in allowed_games:
        return (
            False,
            "",
            f"Invalid game ID. Must be one of: {', '.join(sorted(allowed_games))}",
        )

    return True, game_id, ""


# =============================================================================
# Security Helpers
# =============================================================================


def constant_time_compare(a: str, b: str) -> bool:
    """
    Compare two strings in constant time to prevent timing attacks.

    Args:
        a: First string
        b: Second string

    Returns:
        True if strings are equal, False otherwise
    """
    return hmac.compare_digest(a.encode("utf-8"), b.encode("utf-8"))


def hash_api_key(key: str) -> str:
    """
    Hash an API key for storage.

    Args:
        key: Plain text API key

    Returns:
        Hashed API key
    """
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def get_key_prefix(key: str) -> str:
    """
    Get the prefix of an API key for display.

    Args:
        key: Plain text API key

    Returns:
        First N characters of the key
    """
    from constants import API_KEY_PREFIX_LENGTH

    return key[:API_KEY_PREFIX_LENGTH] if len(key) > API_KEY_PREFIX_LENGTH else key


def sanitize_user_agent(user_agent: Optional[str]) -> str:
    """
    Sanitize user agent string for storage.

    Args:
        user_agent: User agent string

    Returns:
        Sanitized user agent (truncated and cleaned)
    """
    from constants import MAX_USER_AGENT_LENGTH

    if not user_agent:
        return ""

    # Remove control characters and truncate
    sanitized = re.sub(r"[\x00-\x1f\x7f]", "", user_agent)
    return sanitized[:MAX_USER_AGENT_LENGTH]


def get_client_ip(req: Optional[Request] = None) -> str:
    """
    Get client IP address, respecting reverse proxy headers.

    Args:
        req: Flask request object (uses global request if None)

    Returns:
        Client IP address
    """
    if req is None:
        req = request

    # Check for reverse proxy headers (in order of trust)
    if req.headers.get("X-Forwarded-For"):
        # Take the first IP in the chain
        return req.headers.get("X-Forwarded-For").split(",")[0].strip()

    if req.headers.get("X-Real-IP"):
        return req.headers.get("X-Real-IP")

    return req.remote_addr or "unknown"


def generate_secure_token(length: int = 32) -> str:
    """
    Generate a cryptographically secure random token.

    Args:
        length: Length of the token in bytes

    Returns:
        Hex-encoded secure token
    """
    import secrets

    return secrets.token_hex(length)


def mask_sensitive_data(data: str, visible_chars: int = 4) -> str:
    """
    Mask sensitive data for logging.

    Args:
        data: Sensitive data to mask
        visible_chars: Number of characters to show at the start

    Returns:
        Masked string (e.g., "abc1***")
    """
    if not data or len(data) <= visible_chars:
        return "***"

    return data[:visible_chars] + "***"
