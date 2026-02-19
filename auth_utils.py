"""
Authentication utility functions for OAuth state management.
This module is designed to avoid circular imports.
"""

from __future__ import annotations

import secrets
from typing import Any, Optional

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer


def make_state_token(
    secret_key: str, salt: str, next_url: str = ""
) -> str:
    """
    Generate a signed state token for OAuth.

    Args:
        secret_key: Application secret key
        salt: Salt for the token
        next_url: URL to redirect to after OAuth completion

    Returns:
        Signed state token string
    """
    s = URLSafeTimedSerializer(secret_key, salt=salt)
    return s.dumps({"rnd": secrets.token_hex(16), "next": next_url[:200]})


def verify_state_token(
    secret_key: str, salt: str, state: Optional[str], max_age: int = 600
) -> Optional[dict[str, Any]]:
    """
    Verify the state token from OAuth.

    Args:
        secret_key: Application secret key
        salt: Salt for the token
        state: State token to verify
        max_age: Maximum age of token in seconds

    Returns:
        Decoded token data if valid, None otherwise
    """
    if not state:
        return None

    s = URLSafeTimedSerializer(secret_key, salt=salt)
    try:
        return s.loads(state, max_age=max_age)  # type: ignore[no-any-return]
    except (BadSignature, SignatureExpired):
        return None
    except Exception:
        return None


# Aliases for compatibility with existing code
def generate_verification_token(secret_key: str, email: str) -> str:
    """Generate a verification token for email confirmation."""
    s = URLSafeTimedSerializer(secret_key, salt="email-verification")
    return s.dumps(email)


def verify_verification_token(
    token: str, secret_key: str, max_age: int = 86400
) -> Optional[str]:
    """Verify an email verification token. Returns email if valid."""
    s = URLSafeTimedSerializer(secret_key, salt="email-verification")
    try:
        return s.loads(token, max_age=max_age)  # type: ignore[no-any-return]
    except (BadSignature, SignatureExpired):
        return None
    except Exception:
        return None
