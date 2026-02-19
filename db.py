"""
Database helper functions for user and session management.
This module provides core database operations used across the application.
"""

from __future__ import annotations

import logging
import secrets
import sqlite3
from datetime import datetime, timezone
from typing import Any, Optional, Tuple, TypeVar, Union

from werkzeug.security import generate_password_hash

logger = logging.getLogger(__name__)

# Type alias for database rows
Row = TypeVar("Row", bound=Union[sqlite3.Row, dict])


def get_db() -> sqlite3.Connection:
    """Get the database connection from Flask g object."""
    from flask import g

    if "db" not in g:
        raise RuntimeError("Database connection not initialized. Call init_db() first.")
    return g.db  # type: ignore[no-any-return]


def get_db_session():
    """
    Get a database session for use with SQLAlchemy models.
    Returns the Flask g.db connection for compatibility.
    """
    return get_db()


def ensure_user_unverified(email: str, password: Optional[str] = None) -> bool:
    """
    Create user record with email_verified=0 for signup flow.
    Optionally set password. Idempotent.

    Returns:
        True if operation succeeded, False otherwise
    """
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
        return True
    except sqlite3.Error as e:
        logger.error(f"ensure_user_unverified: Database error - {e}")
        return False
    except Exception as e:
        logger.error(f"ensure_user_unverified: Unexpected error - {e}")
        return False


def set_user_verified(email: str) -> bool:
    """
    Mark user as email-verified after they click the link.

    Returns:
        True if operation succeeded, False otherwise
    """
    try:
        db = get_db()
        db.execute("UPDATE users SET email_verified = 1 WHERE email = ?", (email.lower(),))
        db.commit()
        return db.total_changes > 0
    except sqlite3.Error as e:
        logger.error(f"set_user_verified: Database error - {e}")
        return False
    except Exception as e:
        logger.error(f"set_user_verified: Unexpected error - {e}")
        return False


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
    except sqlite3.Error as e:
        logger.error(f"is_user_verified: Database error - {e}")
        return False
    except Exception as e:
        logger.error(f"is_user_verified: Unexpected error - {e}")
        return False


def get_user_row(email: str) -> Optional[sqlite3.Row]:
    """
    Return the user row (with password_hash, customer_id, subscription_id) or None.

    Args:
        email: User email address

    Returns:
        sqlite3.Row if user exists, None otherwise
    """
    if not email:
        return None
    try:
        db = get_db()
        return db.execute(
            "SELECT email, tier, email_verified, password_hash, customer_id, subscription_id FROM users WHERE email = ?",
            (email.lower(),),
        ).fetchone()
    except sqlite3.Error as e:
        logger.error(f"get_user_row: Database error - {e}")
        return None
    except Exception as e:
        logger.error(f"get_user_row: Unexpected error - {e}")
        return None


def get_user_by_email(email: str) -> Optional[dict]:
    """
    Get user by email address.
    
    Args:
        email: User email address
        
    Returns:
        User dict if exists, None otherwise
    """
    row = get_user_row(email)
    if row:
        return dict(row)
    return None


def save_user_session(user_email: str, session_data: dict) -> bool:
    """
    Save user session data.
    
    Args:
        user_email: User email
        session_data: Session data to save
        
    Returns:
        True if successful
    """
    # This is a placeholder - actual implementation depends on session storage
    return True


def _utc_ts() -> int:
    """Return current UTC timestamp as integer."""
    return int((datetime.now(timezone.utc) - datetime(1970, 1, 1, tzinfo=timezone.utc)).total_seconds())


def session_create(
    user_email: str,
    remember_me: bool = False,
    user_agent: Optional[str] = None,
) -> Tuple[Optional[str], int]:
    """
    Create a session row and return (token, max_age).

    Args:
        user_email: User's email address
        remember_me: If True, use longer session lifetime
        user_agent: Optional user agent string

    Returns:
        Tuple of (session_token, max_age_seconds). Token is None if creation failed.
    """
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
    except sqlite3.Error as e:
        logger.error(f"session_create: Database error - {e}")
        return None, max_age
    except Exception as e:
        logger.error(f"session_create: Unexpected error - {e}")
        return None, max_age


def session_get(token: str) -> Optional[sqlite3.Row]:
    """
    Return session row (with user_email) if token valid and not expired.
    Updates last_seen timestamp.

    Args:
        token: Session token

    Returns:
        Session row if valid and not expired, None otherwise
    """
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
    except sqlite3.Error as e:
        logger.error(f"session_get: Database error - {e}")
        return None
    except Exception as e:
        logger.error(f"session_get: Unexpected error - {e}")
        return None


def session_delete(token: str) -> bool:
    """
    Delete a session row by token.

    Args:
        token: Session token to delete

    Returns:
        True if session was deleted, False otherwise
    """
    if not token:
        return False

    try:
        db = get_db()
        db.execute("DELETE FROM user_sessions WHERE token = ?", (token,))
        db.commit()
        return db.total_changes > 0
    except sqlite3.Error as e:
        logger.error(f"session_delete: Database error - {e}")
        return False
    except Exception as e:
        logger.error(f"session_delete: Unexpected error - {e}")
        return False


def session_cleanup(user_email: str, keep_token: Optional[str] = None) -> bool:
    """
    Delete all sessions for a user, optionally keeping one token.

    Args:
        user_email: User's email address
        keep_token: Optional token to preserve (e.g., current session)

    Returns:
        True if any sessions were deleted, False otherwise
    """
    if not user_email:
        return False

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
        return db.total_changes > 0
    except sqlite3.Error as e:
        logger.error(f"session_cleanup: Database error - {e}")
        return False
    except Exception as e:
        logger.error(f"session_cleanup: Unexpected error - {e}")
        return False


def execute_query(
    query: str,
    params: Optional[Tuple[Any, ...]] = None,
    fetch: bool = False,
    fetch_all: bool = False,
) -> Optional[Union[sqlite3.Row, list[sqlite3.Row]]]:
    """
    Execute a database query with optional fetching.

    Args:
        query: SQL query string
        params: Optional query parameters
        fetch: If True, fetch one row
        fetch_all: If True, fetch all rows

    Returns:
        Row, list of rows, or None depending on fetch parameters
    """
    try:
        db = get_db()
        cursor = db.execute(query, params or ())

        if fetch:
            return cursor.fetchone()
        elif fetch_all:
            return cursor.fetchall()
        else:
            db.commit()
            return None
    except sqlite3.Error as e:
        logger.error(f"execute_query: Database error - {e}")
        return None
    except Exception as e:
        logger.error(f"execute_query: Unexpected error - {e}")
        return None
