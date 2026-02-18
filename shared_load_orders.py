"""
Shared Load Orders functionality for SkyModderAI.
Allows users to create and share links to their mod lists and analysis results.
"""

import json
import secrets
import string
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from flask import current_app as app

from db import get_db


def generate_share_id() -> str:
    """Generate a random URL-safe ID for shared load orders."""
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(12))


def create_shared_load_order(
    game: str,
    mod_list: List[Dict[str, Any]],
    analysis_results: Dict[str, Any],
    user_email: Optional[str] = None,
    title: Optional[str] = None,
    notes: Optional[str] = None,
    is_public: bool = True,
    days_until_expiry: int = 30,
) -> Optional[str]:
    """
    Create a new shared load order entry in the database.

    Args:
        game: Game identifier (e.g., 'skyrimse', 'fallout4')
        mod_list: List of mods with their details
        analysis_results: Results from the mod analysis
        user_email: Email of the user creating the share (optional)
        title: Optional title for the shared load order
        notes: Optional notes or description
        is_public: Whether the share is public or unlisted
        days_until_expiry: Number of days until the share expires (default 30)

    Returns:
        Share ID if successful, None otherwise
    """
    share_id = generate_share_id()
    expires_at = datetime.now(timezone.utc) + timedelta(days=days_until_expiry)

    try:
        db = get_db()
        db.execute(
            """
            INSERT INTO shared_load_orders (
                id, expires_at, game, mod_list, analysis_results,
                user_email, title, notes, is_public
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                share_id,
                expires_at,
                game,
                json.dumps(mod_list),
                json.dumps(analysis_results),
                user_email,
                title,
                notes,
                is_public,
            ),
        )
        db.commit()
        return share_id
    except Exception as e:
        app.logger.error(f"Error creating shared load order: {e}")
        return None


def get_shared_load_order(share_id: str, increment_view: bool = True) -> Optional[Dict[str, Any]]:
    """
    Retrieve a shared load order by its ID.

    Args:
        share_id: The share ID to look up
        increment_view: Whether to increment the view counter

    Returns:
        The shared load order data, or None if not found/expired
    """
    try:
        db = get_db()

        # First, check if the share exists and is not expired
        now = datetime.now(timezone.utc)
        row = db.execute(
            """
            SELECT * FROM shared_load_orders
            WHERE id = ? AND expires_at > ?
            """,
            (share_id, now),
        ).fetchone()

        if not row:
            return None

        # Increment view count if requested
        if increment_view:
            db.execute(
                """
                UPDATE shared_load_orders
                SET view_count = view_count + 1, last_viewed_at = ?
                WHERE id = ?
                """,
                (now, share_id),
            )
            db.commit()

        # Convert row to dict and parse JSON fields
        result = dict(row)
        result["mod_list"] = json.loads(result["mod_list"])
        result["analysis_results"] = json.loads(result["analysis_results"])
        return result

    except Exception as e:
        app.logger.error(f"Error retrieving shared load order {share_id}: {e}")
        return None


def get_user_shared_load_orders(user_email: str) -> List[Dict[str, Any]]:
    """
    Get all shared load orders for a specific user.

    Args:
        user_email: The email of the user

    Returns:
        List of shared load orders, most recent first
    """
    try:
        db = get_db()
        now = datetime.now(timezone.utc)

        rows = db.execute(
            """
            SELECT id, created_at, expires_at, game, title, view_count, is_public
            FROM shared_load_orders
            WHERE user_email = ? AND expires_at > ?
            ORDER BY created_at DESC
            """,
            (user_email, now),
        ).fetchall()

        return [dict(row) for row in rows]

    except Exception as e:
        app.logger.error(f"Error retrieving shared load orders for {user_email}: {e}")
        return []


def delete_expired_shared_load_orders() -> int:
    """
    Delete all expired shared load orders.

    Returns:
        Number of deleted rows
    """
    try:
        db = get_db()
        result = db.execute(
            "DELETE FROM shared_load_orders WHERE expires_at <= ?", (datetime.now(timezone.utc),)
        )
        db.commit()
        return result.rowcount
    except Exception as e:
        app.logger.error(f"Error deleting expired shared load orders: {e}")
        return 0
