"""
Database helper functions for user and session management.
This module provides core database operations used across the application.
"""

import logging
import secrets
from datetime import datetime
from typing import Optional, Tuple

from werkzeug.security import generate_password_hash

logger = logging.getLogger(__name__)


def get_db():
    """Get the database connection from Flask g object."""
    from flask import g

    return g.db


def ensure_user_unverified(email: str, password: Optional[str] = None):
    """Create user record with email_verified=0 for signup flow. Optionally set password. Idempotent."""
    try:
        db = get_db()
        email = email.lower()
        pwhash = generate_password_hash(password, method="pbkdf2:sha256") if password else None
        db.execute(
            """
            INSERT OR IGNORE INTO users (email, tier, customer_id, subscription_id, email_verified, password_hash, last_updated)
            VALUES (?, 'free', NULL, NULL, 0, ?, CURRENT_TIMESTAMP)
        """,
            (email, pwhash),
        )
        if password and db.total_changes == 0:
            db.execute(
                "UPDATE users SET password_hash = ?, last_updated = CURRENT_TIMESTAMP WHERE email = ?",
                (pwhash, email),
            )
        db.commit()
    except Exception as e:
        logger.error(f"ensure_user_unverified: {e}")


def set_user_verified(email: str):
    """Mark user as email-verified after they click the link."""
    try:
        db = get_db()
        db.execute("UPDATE users SET email_verified = 1 WHERE email = ?", (email.lower(),))
        db.commit()
    except Exception as e:
        logger.error(f"set_user_verified: {e}")


def is_user_verified(email: str) -> bool:
    """Return True if user has verified their email."""
    if not email:
        return False
    try:
        db = get_db()
        row = db.execute(
            "SELECT email_verified FROM users WHERE email = ?", (email.lower(),)
        ).fetchone()
        return bool(row and row[0])
    except Exception:
        return False


def get_user_row(email: str):
    """Return the user row (with password_hash, customer_id, subscription_id) or None."""
    if not email:
        return None
    try:
        db = get_db()
        return db.execute(
            "SELECT email, tier, email_verified, password_hash, customer_id, subscription_id FROM users WHERE email = ?",
            (email.lower(),),
        ).fetchone()
    except Exception:
        return None


def _utc_ts() -> int:
    """Return current UTC timestamp as integer."""
    return int((datetime.utcnow() - datetime(1970, 1, 1)).total_seconds())


def session_create(
    user_email: str, remember_me: bool = False, user_agent: Optional[str] = None
) -> Tuple[Optional[str], int]:
    """Create a session row and return (token, max_age)."""
    from config import config

    token = secrets.token_urlsafe(32)
    display_id = secrets.token_urlsafe(8)
    max_age = config.SESSION_LONG_LIFETIME if remember_me else config.SESSION_SHORT_LIFETIME
    expires_ts = _utc_ts() + max_age
    try:
        db = get_db()
        db.execute(
            "INSERT INTO user_sessions (token, display_id, user_email, user_agent, last_seen, expires_at) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, ?)",
            (token, display_id, user_email.lower(), (user_agent or "")[:512], expires_ts),
        )
        db.commit()
        return token, max_age
    except Exception as e:
        logger.error(f"session_create: {e}")
        return None, max_age


def session_get(token: str):
    """Return session row (with user_email) if token valid and not expired; else None. Updates last_seen."""
    if not token:
        return None
    try:
        db = get_db()
        now_ts = _utc_ts()
        row = db.execute(
            "SELECT token, user_email, user_agent, created_at, last_seen, expires_at FROM user_sessions WHERE token = ?",
            (token,),
        ).fetchone()
        if not row or (row["expires_at"] or 0) < now_ts:
            return None
        db.execute(
            "UPDATE user_sessions SET last_seen = CURRENT_TIMESTAMP WHERE token = ?", (token,)
        )
        db.commit()
        return row
    except Exception as e:
        logger.error(f"session_get: {e}")
        return None


def session_delete(token: str):
    """Delete a session row by token."""
    if not token:
        return
    try:
        db = get_db()
        db.execute("DELETE FROM user_sessions WHERE token = ?", (token,))
        db.commit()
    except Exception as e:
        logger.error(f"session_delete: {e}")


def session_cleanup(user_email: str, keep_token: Optional[str] = None):
    """Delete all sessions for a user, optionally keeping one token."""
    if not user_email:
        return
    try:
        db = get_db()
        if keep_token:
            db.execute(
                "DELETE FROM user_sessions WHERE user_email = ? AND token != ?",
                (user_email.lower(), keep_token),
            )
        else:
            db.execute("DELETE FROM user_sessions WHERE user_email = ?", (user_email.lower(),))
        db.commit()
    except Exception as e:
        logger.error(f"session_cleanup: {e}")
