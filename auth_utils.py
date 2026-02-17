"""
Authentication utility functions for OAuth state management.
This module is designed to avoid circular imports.
"""

import secrets

from itsdangerous import URLSafeTimedSerializer


def make_state_token(secret_key, salt, next_url=""):
    """Generate a signed state token for OAuth."""
    s = URLSafeTimedSerializer(secret_key, salt=salt)
    return s.dumps({"rnd": secrets.token_hex(16), "next": next_url[:200]})


def verify_state_token(secret_key, salt, state, max_age=600):
    """Verify the state token from OAuth."""
    if not state:
        return None
    s = URLSafeTimedSerializer(secret_key, salt=salt)
    try:
        return s.loads(state, max_age=max_age)
    except Exception:
        return None
