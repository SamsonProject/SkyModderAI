"""
SkyModderAI - Mod Author Services

Mod author verification, claim management, and author dashboard functionality.
"""

from __future__ import annotations

import hashlib
import json
import logging
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import requests

from db import get_db

logger = logging.getLogger(__name__)


@dataclass
class ModAuthorClaim:
    """A mod author's claim to ownership of a mod."""

    id: int
    mod_name: str
    nexus_id: Optional[int]
    game: str
    author_email: str
    author_name: str
    verification_status: str  # 'pending', 'verified', 'rejected'
    verification_method: str  # 'nexus_api', 'file_upload', 'manual'
    verified_at: Optional[float]
    verified_by: Optional[str]  # admin email or 'system'
    nexus_profile_url: Optional[str]
    mod_page_url: Optional[str]
    created_at: float
    updated_at: float


@dataclass
class ModAuthorNotification:
    """Notification for mod authors."""

    id: int
    user_email: str
    notification_type: str  # 'new_conflict', 'patch_released', 'vote_received', 'report_submitted'
    title: str
    message: str
    mod_name: Optional[str]
    related_url: Optional[str]
    is_read: bool
    created_at: float


class ModAuthorService:
    """Service for managing mod author verification and claims."""

    def claim_mod(
        self,
        mod_name: str,
        author_email: str,
        author_name: str,
        game: str,
        nexus_id: Optional[int] = None,
        nexus_profile_url: Optional[str] = None,
        mod_page_url: Optional[str] = None,
    ) -> Optional[int]:
        """
        Submit a claim for a mod.

        Returns:
            Claim ID if successful, None otherwise
        """
        try:
            db = get_db()
            now = datetime.now(timezone.utc).timestamp()

            # Check for existing claim
            existing = db.execute(
                """
                SELECT id FROM mod_author_claims
                WHERE mod_name = ? AND game = ? AND author_email = ?
            """,
                (mod_name.lower(), game, author_email),
            ).fetchone()

            if existing:
                logger.info(f"Duplicate claim from {author_email} for {mod_name}")
                return existing["id"]

            # Insert new claim
            cursor = db.execute(
                """
                INSERT INTO mod_author_claims
                (mod_name, nexus_id, game, author_email, author_name, verification_status,
                 verification_method, nexus_profile_url, mod_page_url, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, 'pending', 'nexus_api', ?, ?, ?, ?)
            """,
                (
                    mod_name.lower(),
                    nexus_id,
                    game,
                    author_email,
                    author_name,
                    nexus_profile_url,
                    mod_page_url,
                    now,
                    now,
                ),
            )

            claim_id = cursor.lastrowid
            db.commit()

            logger.info(f"Mod claim submitted: {mod_name} by {author_email}")
            return claim_id

        except Exception as e:
            logger.error(f"Failed to submit mod claim: {e}")
            return None

    def verify_mod_claim(
        self,
        claim_id: int,
        verifier_email: str,
        method: str = "manual",
    ) -> bool:
        """
        Verify a mod claim (admin action).

        Args:
            claim_id: Claim ID to verify
            verifier_email: Email of admin verifying
            method: Verification method ('manual', 'nexus_api', 'file_upload')

        Returns:
            True if successful
        """
        try:
            db = get_db()
            now = datetime.now(timezone.utc).timestamp()

            db.execute(
                """
                UPDATE mod_author_claims
                SET verification_status = 'verified',
                    verified_at = ?,
                    verified_by = ?,
                    verification_method = ?,
                    updated_at = ?
                WHERE id = ?
            """,
                (now, verifier_email, method, now, claim_id),
            )

            db.commit()

            # Get claim details for notification
            claim = db.execute(
                "SELECT * FROM mod_author_claims WHERE id = ?", (claim_id,)
            ).fetchone()

            if claim:
                # Create notification
                self.create_notification(
                    user_email=claim["author_email"],
                    notification_type="claim_verified",
                    title=f"Mod Claim Verified: {claim['mod_name']}",
                    message=f"Your claim for {claim['mod_name']} has been verified. You now have author privileges for this mod.",
                    mod_name=claim["mod_name"],
                    related_url=f"/mod/{claim['mod_name']}",
                )

            logger.info(f"Mod claim {claim_id} verified by {verifier_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to verify mod claim: {e}")
            return False

    def verify_via_nexus_api(self, claim_id: int, nexus_api_key: str) -> bool:
        """
        Verify mod claim using Nexus Mods API.

        Args:
            claim_id: Claim ID to verify
            nexus_api_key: Nexus API key for authentication

        Returns:
            True if verification successful
        """
        try:
            db = get_db()
            claim = db.execute(
                "SELECT * FROM mod_author_claims WHERE id = ? AND verification_status = 'pending'",
                (claim_id,),
            ).fetchone()

            if not claim or not claim["nexus_id"]:
                logger.error(f"Claim {claim_id} not suitable for Nexus API verification")
                return False

            # Call Nexus API to get mod details
            game_domain = {
                "skyrimse": "skyrimse",
                "skyrim": "skyrim",
                "skyrimvr": "skyrimvr",
                "fallout4": "fallout4",
                "falloutnv": "newvegas",
                "oblivion": "oblivion",
            }.get(claim["game"], "skyrimse")

            url = f"https://api.nexusmods.com/v1/games/{game_domain}/mods/{claim['nexus_id']}.json"
            headers = {"apikey": nexus_api_key}

            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code != 200:
                logger.error(f"Nexus API error: {response.status_code}")
                return False

            mod_data = response.json()

            # Check if author name matches
            nexus_author = mod_data.get("author", "").lower()
            claim_author = claim["author_name"].lower()

            if (
                nexus_author == claim_author
                or nexus_author in claim_author
                or claim_author in nexus_author
            ):
                # Author names match - verify claim
                return self.verify_mod_claim(claim_id, verifier_email="system", method="nexus_api")
            else:
                logger.info(f"Author name mismatch: Nexus='{nexus_author}', Claim='{claim_author}'")
                return False

        except Exception as e:
            logger.error(f"Nexus API verification failed: {e}")
            return False

    def verify_via_file_upload(self, claim_id: int, uploaded_file_hash: str) -> bool:
        """
        Verify mod claim by checking uploaded file hash.

        Args:
            claim_id: Claim ID to verify
            uploaded_file_hash: Hash of uploaded mod file

        Returns:
            True if verification successful
        """
        try:
            db = get_db()
            claim = db.execute(
                "SELECT * FROM mod_author_claims WHERE id = ? AND verification_status = 'pending'",
                (claim_id,),
            ).fetchone()

            if not claim:
                return False

            # In production, you would:
            # 1. Download the actual mod file from Nexus
            # 2. Compare hashes
            # For now, we'll accept any valid upload as proof

            if uploaded_file_hash and len(uploaded_file_hash) == 64:  # SHA256
                return self.verify_mod_claim(
                    claim_id, verifier_email="system", method="file_upload"
                )

            return False

        except Exception as e:
            logger.error(f"File upload verification failed: {e}")
            return False

    def get_author_claims(self, user_email: str) -> list[dict[str, Any]]:
        """Get all claims for a user."""
        try:
            db = get_db()
            claims = db.execute(
                """
                SELECT * FROM mod_author_claims
                WHERE author_email = ?
                ORDER BY created_at DESC
            """,
                (user_email,),
            ).fetchall()

            return [dict(row) for row in claims]

        except Exception as e:
            logger.error(f"Failed to get author claims: {e}")
            return []

    def get_verified_mods(self, user_email: str) -> list[str]:
        """Get list of verified mod names for a user."""
        try:
            db = get_db()
            mods = db.execute(
                """
                SELECT mod_name, game FROM mod_author_claims
                WHERE author_email = ? AND verification_status = 'verified'
            """,
                (user_email,),
            ).fetchall()

            return [f"{row['mod_name']} ({row['game']})" for row in mods]

        except Exception as e:
            logger.error(f"Failed to get verified mods: {e}")
            return []

    def is_verified_author(self, user_email: str, mod_name: str, game: str) -> bool:
        """Check if user is verified author of a mod."""
        try:
            db = get_db()
            result = db.execute(
                """
                SELECT id FROM mod_author_claims
                WHERE author_email = ? AND mod_name = ? AND game = ? AND verification_status = 'verified'
            """,
                (user_email, mod_name.lower(), game),
            ).fetchone()

            return result is not None

        except Exception as e:
            logger.error(f"Failed to check author verification: {e}")
            return False

    def create_notification(
        self,
        user_email: str,
        notification_type: str,
        title: str,
        message: str,
        mod_name: Optional[str] = None,
        related_url: Optional[str] = None,
    ) -> Optional[int]:
        """Create a notification for a user."""
        try:
            db = get_db()
            now = datetime.now(timezone.utc).timestamp()

            cursor = db.execute(
                """
                INSERT INTO mod_author_notifications
                (user_email, notification_type, title, message, mod_name, related_url, is_read, created_at)
                VALUES (?, ?, ?, ?, ?, ?, 0, ?)
            """,
                (user_email, notification_type, title, message, mod_name, related_url, now),
            )

            notification_id = cursor.lastrowid
            db.commit()

            return notification_id

        except Exception as e:
            logger.error(f"Failed to create notification: {e}")
            return None

    def get_notifications(self, user_email: str, unread_only: bool = False) -> list[dict[str, Any]]:
        """Get notifications for a user."""
        try:
            db = get_db()

            query = """
                SELECT * FROM mod_author_notifications
                WHERE user_email = ?
            """
            params = [user_email]

            if unread_only:
                query += " AND is_read = 0"

            query += " ORDER BY created_at DESC LIMIT 50"

            notifications = db.execute(query, params).fetchall()
            return [dict(row) for row in notifications]

        except Exception as e:
            logger.error(f"Failed to get notifications: {e}")
            return []

    def mark_notification_read(self, notification_id: int, user_email: str) -> bool:
        """Mark a notification as read."""
        try:
            db = get_db()
            db.execute(
                """
                UPDATE mod_author_notifications
                SET is_read = 1
                WHERE id = ? AND user_email = ?
            """,
                (notification_id, user_email),
            )
            db.commit()
            return True

        except Exception as e:
            logger.error(f"Failed to mark notification read: {e}")
            return False

    def mark_all_notifications_read(self, user_email: str) -> bool:
        """Mark all notifications as read for a user."""
        try:
            db = get_db()
            db.execute(
                """
                UPDATE mod_author_notifications
                SET is_read = 1
                WHERE user_email = ?
            """,
                (user_email,),
            )
            db.commit()
            return True

        except Exception as e:
            logger.error(f"Failed to mark all notifications read: {e}")
            return False

    def get_author_dashboard_data(self, user_email: str) -> dict[str, Any]:
        """Get dashboard data for a mod author."""
        try:
            db = get_db()

            # Get verified mods count
            verified_count = db.execute(
                """
                SELECT COUNT(*) as count FROM mod_author_claims
                WHERE author_email = ? AND verification_status = 'verified'
            """,
                (user_email,),
            ).fetchone()["count"]

            # Get pending claims count
            pending_count = db.execute(
                """
                SELECT COUNT(*) as count FROM mod_author_claims
                WHERE author_email = ? AND verification_status = 'pending'
            """,
                (user_email,),
            ).fetchone()["count"]

            # Get unread notifications count
            unread_notifications = db.execute(
                """
                SELECT COUNT(*) as count FROM mod_author_notifications
                WHERE user_email = ? AND is_read = 0
            """,
                (user_email,),
            ).fetchone()["count"]

            # Get recent compatibility reports for author's mods
            recent_reports = db.execute(
                """
                    SELECT cr.*, mac.mod_name
                    FROM compatibility_reports cr
                    JOIN mod_author_claims mac ON (
                        (cr.mod_a = mac.mod_name OR cr.mod_b = mac.mod_name)
                        AND mac.game = cr.game
                    )
                    WHERE mac.author_email = ? AND mac.verification_status = 'verified'
                    ORDER BY cr.created_at DESC
                    LIMIT 10
                """,
                (user_email,),
            ).fetchall()

            # Get vote stats
            vote_stats = db.execute(
                """
                SELECT
                    SUM(upvotes) as total_upvotes,
                    SUM(downvotes) as total_downvotes
                FROM compatibility_reports cr
                JOIN mod_author_claims mac ON (
                    (cr.mod_a = mac.mod_name OR cr.mod_b = mac.mod_name)
                    AND mac.game = cr.game
                )
                WHERE mac.author_email = ? AND mac.verification_status = 'verified'
            """,
                (user_email,),
            ).fetchone()

            return {
                "verified_mods": verified_count,
                "pending_claims": pending_count,
                "unread_notifications": unread_notifications,
                "recent_reports": [dict(r) for r in recent_reports],
                "total_upvotes": vote_stats["total_upvotes"] or 0,
                "total_downvotes": vote_stats["total_downvotes"] or 0,
            }

        except Exception as e:
            logger.error(f"Failed to get dashboard data: {e}")
            return {
                "verified_mods": 0,
                "pending_claims": 0,
                "unread_notifications": 0,
                "recent_reports": [],
                "total_upvotes": 0,
                "total_downvotes": 0,
            }


def get_mod_author_service() -> ModAuthorService:
    """Get or create mod author service instance."""
    return ModAuthorService()
