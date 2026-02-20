"""
Database helper functions for user and session management.
This module provides core database operations used across the application.

Supports both SQLite (development) and PostgreSQL (production).
"""

from __future__ import annotations

import logging
import secrets
import sqlite3
import time
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Callable, Optional, TypeVar, Union

from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from werkzeug.security import generate_password_hash

logger = logging.getLogger(__name__)

# Type alias for database rows
Row = TypeVar("Row", bound=Union[sqlite3.Row, dict, Any])

# Database engine for PostgreSQL (lazy-initialized)
_engine = None
_db_type = None  # 'sqlite' or 'postgresql'


def _get_db_type() -> str:
    """Determine database type from connection."""
    global _db_type
    if _db_type is not None:
        return _db_type

    try:
        from config import config

        uri = config.SQLALCHEMY_DATABASE_URI or ""
        if uri.startswith("postgresql://") or uri.startswith("postgres://"):
            _db_type = "postgresql"
        else:
            _db_type = "sqlite"
    except Exception:
        _db_type = "sqlite"

    return _db_type


def _get_engine():
    """Get or create SQLAlchemy engine for PostgreSQL."""
    global _engine

    if _engine is not None:
        return _engine

    try:
        from config import config

        uri = config.SQLALCHEMY_DATABASE_URI or ""
        if uri.startswith("postgresql://") or uri.startswith("postgres://"):
            # Convert postgres:// to postgresql:// if needed
            if uri.startswith("postgres://"):
                uri = uri.replace("postgres://", "postgresql://", 1)

            # Create engine with connection pooling
            _engine = create_engine(
                uri,
                pool_pre_ping=True,
                pool_recycle=300,
                pool_size=5,
                max_overflow=10,
                echo=False,
            )
            logger.info("PostgreSQL engine initialized with connection pooling")
        else:
            _engine = None
    except Exception as e:
        logger.error(f"Failed to create database engine: {e}")
        _engine = None

    return _engine


def _retry_on_disconnect(max_retries: int = 3, delay: float = 1.0):
    """Decorator to retry database operations on connection loss."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            last_error = None

            while retries <= max_retries:
                try:
                    return func(*args, **kwargs)
                except OperationalError as e:
                    last_error = e
                    retries += 1
                    if retries <= max_retries:
                        logger.warning(
                            f"Database connection lost, retrying ({retries}/{max_retries})..."
                        )
                        time.sleep(delay * retries)  # Exponential backoff
                    else:
                        logger.error(f"Database operation failed after {max_retries} retries: {e}")
                except Exception as e:
                    logger.error(f"Database operation failed: {e}")
                    raise

            raise last_error or RuntimeError("Database operation failed")

        return wrapper

    return decorator


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

        db_type = _get_db_type()

        if db_type == "postgresql":
            # PostgreSQL uses ON CONFLICT DO NOTHING
            db.execute(
                """
                INSERT INTO users (email, tier, customer_id, subscription_id, email_verified, password_hash, last_updated)
                VALUES (%s, 'free', NULL, NULL, FALSE, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (email) DO NOTHING
            """,
                (email, pwhash),
            )
            if password:
                result = db.execute(
                    "UPDATE users SET password_hash = %s, last_updated = CURRENT_TIMESTAMP WHERE email = %s",
                    (pwhash, email),
                )
        else:
            # SQLite uses INSERT OR IGNORE
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


def save_user_session(
    email: str,
    user_agent: str = "",
    remember: bool = False,
) -> bool:
    """
    Save user session data to the database.
    Creates a new session token and stores it for device management.

    Args:
        email: User email
        user_agent: User agent string from request
        remember: If True, use longer session lifetime

    Returns:
        True if successful, False otherwise
    """
    try:
        # Use existing session_create function which handles all the logic
        token, _ = session_create(email, remember_me=remember, user_agent=user_agent)

        if token:
            # Store token in Flask session for immediate use
            from flask import session

            session["session_token"] = token
            return True
        return False
    except Exception as e:
        logger.error(f"save_user_session: Failed to save session - {e}")
        return False


def create_password_reset_token(email: str, token: str, expires_at: int) -> bool:
    """
    Create a password reset token for the given email.

    Args:
        email: User email address
        token: Secure random token string
        expires_at: Unix timestamp when token expires

    Returns:
        True if successful, False otherwise
    """
    try:
        db = get_db()
        # Invalidate any existing tokens for this email
        db.execute("UPDATE password_reset_tokens SET used = 1 WHERE email = ?", (email.lower(),))
        # Create new token
        db.execute(
            "INSERT INTO password_reset_tokens (email, token, expires_at) VALUES (?, ?, ?)",
            (email.lower(), token, expires_at),
        )
        db.commit()
        return True
    except sqlite3.Error as e:
        logger.error(f"create_password_reset_token: Database error - {e}")
        return False
    except Exception as e:
        logger.error(f"create_password_reset_token: Unexpected error - {e}")
        return False


def get_password_reset_token(token: str) -> Optional[sqlite3.Row]:
    """
    Get a password reset token if valid and not expired.

    Args:
        token: Token string to look up

    Returns:
        Token row if valid and not expired, None otherwise
    """
    try:
        db = get_db()
        import time

        now = int(time.time())
        row = db.execute(
            """SELECT email, token, expires_at, used
               FROM password_reset_tokens
               WHERE token = ? AND expires_at > ? AND used = 0""",
            (token, now),
        ).fetchone()
        return row
    except sqlite3.Error as e:
        logger.error(f"get_password_reset_token: Database error - {e}")
        return None
    except Exception as e:
        logger.error(f"get_password_reset_token: Unexpected error - {e}")
        return None


def use_password_reset_token(token: str) -> bool:
    """
    Mark a password reset token as used.

    Args:
        token: Token string to invalidate

    Returns:
        True if successful, False otherwise
    """
    try:
        db = get_db()
        db.execute("UPDATE password_reset_tokens SET used = 1 WHERE token = ?", (token,))
        db.commit()
        return db.total_changes > 0
    except sqlite3.Error as e:
        logger.error(f"use_password_reset_token: Database error - {e}")
        return False
    except Exception as e:
        logger.error(f"use_password_reset_token: Unexpected error - {e}")
        return False


def reset_user_password(email: str, new_password: str) -> bool:
    """
    Reset a user's password.

    Args:
        email: User email address
        new_password: New password to set

    Returns:
        True if successful, False otherwise
    """
    try:
        db = get_db()
        pwhash = generate_password_hash(new_password, method="pbkdf2:sha256")
        db.execute(
            "UPDATE users SET password_hash = ?, last_updated = CURRENT_TIMESTAMP WHERE email = ?",
            (pwhash, email.lower()),
        )
        db.commit()
        return db.total_changes > 0
    except sqlite3.Error as e:
        logger.error(f"reset_user_password: Database error - {e}")
        return False
    except Exception as e:
        logger.error(f"reset_user_password: Unexpected error - {e}")
        return False


def _utc_ts() -> int:
    """Return current UTC timestamp as integer."""
    return int(
        (datetime.now(timezone.utc) - datetime(1970, 1, 1, tzinfo=timezone.utc)).total_seconds()
    )


def session_create(
    user_email: str,
    remember_me: bool = False,
    user_agent: Optional[str] = None,
) -> tuple[Optional[str], int]:
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
        db_type = _get_db_type()

        if db_type == "postgresql":
            # PostgreSQL uses %s placeholders and CURRENT_TIMESTAMP
            db.execute(
                "INSERT INTO user_sessions (token, display_id, user_email, user_agent, last_seen, expires_at) VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP, %s)",
                (token, display_id, user_email.lower(), (user_agent or "")[:512], expires_ts),
            )
        else:
            # SQLite uses ? placeholders
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
        db_type = _get_db_type()
        now_ts = _utc_ts()

        if db_type == "postgresql":
            # PostgreSQL uses %s placeholders
            row = db.execute(
                "SELECT token, user_email, user_agent, created_at, last_seen, expires_at FROM user_sessions WHERE token = %s",
                (token,),
            ).fetchone()
        else:
            # SQLite uses ? placeholders
            row = db.execute(
                "SELECT token, user_email, user_agent, created_at, last_seen, expires_at FROM user_sessions WHERE token = ?",
                (token,),
            ).fetchone()

        if not row or (row["expires_at"] or 0) < now_ts:
            return None

        if db_type == "postgresql":
            db.execute(
                "UPDATE user_sessions SET last_seen = CURRENT_TIMESTAMP WHERE token = %s", (token,)
            )
        else:
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
        db_type = _get_db_type()

        if db_type == "postgresql":
            result = db.execute("DELETE FROM user_sessions WHERE token = %s", (token,))
            db.commit()
            return result.rowcount > 0
        else:
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
        db_type = _get_db_type()

        if db_type == "postgresql":
            if keep_token:
                result = db.execute(
                    "DELETE FROM user_sessions WHERE user_email = %s AND token != %s",
                    (user_email.lower(), keep_token),
                )
            else:
                result = db.execute(
                    "DELETE FROM user_sessions WHERE user_email = %s", (user_email.lower(),)
                )
            db.commit()
            return result.rowcount > 0
        else:
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
    params: Optional[tuple[Any, ...]] = None,
    fetch: bool = False,
    fetch_all: bool = False,
) -> Optional[Union[sqlite3.Row, list[sqlite3.Row], Any]]:
    """
    Execute a database query with optional fetching.

    Note: For PostgreSQL, use %s placeholders. For SQLite, use ? placeholders.
    The function will automatically convert placeholders based on the database type.

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
        db_type = _get_db_type()

        # Convert ? placeholders to %s for PostgreSQL
        if db_type == "postgresql" and params:
            query = query.replace("?", "%s")

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
