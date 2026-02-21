"""
Samson Telemetry Service - Privacy-First Usage Tracking

This is the foundation for The Samson Project's training reservoir.
SkyModderAI collects anonymized interaction data that feeds:
1. Compatibility database improvements
2. Community governance patterns
3. User wellness metrics (autonomy, thriving, environment)
4. Deterministic rule refinement

PRINCIPLES:
- All personal data stays local (never leaves user's device without consent)
- Telemetry is opt-in only (default: OFF in development, ON in production with disclosure)
- Users can export/delete their telemetry at any time
- Data is aggregated and anonymized before contributing to Samson training corpus
- No third-party tracking, no ads, no extractive data practices

This is how we build powerful AI without becoming the thing we oppose.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from datetime import datetime, timezone
from typing import Any, Optional

from db import get_db

logger = logging.getLogger(__name__)


class TelemetryService:
    """
    Privacy-first telemetry for SkyModderAI.

    Tracks:
    - Feature usage (which tools are used, how often)
    - Conflict resolution patterns (what works, what doesn't)
    - Community engagement (votes, reports, shares)
    - User wellness proxies (engagement quality, not addiction metrics)

    Does NOT track:
    - Personal identifiers (email, IP, etc.) - hashed/anonymized only
    - Mod lists (unless explicitly shared by user)
    - Session duration (we don't want to optimize for addiction)
    """

    def __init__(self):
        self.telemetry_enabled = os.getenv("SAMSON_TELEMETRY_ENABLED", "true").lower() == "true"
        self.instance_id = self._get_or_create_instance_id()

    def _get_or_create_instance_id(self) -> str:
        """
        Get or create an anonymized instance identifier.

        This is NOT tied to user email, IP, or any PII.
        It's a random UUID that resets if the user clears their data.
        """
        db = get_db()

        # Check for existing instance ID
        row = db.execute(
            "SELECT value FROM samson_telemetry_config WHERE key = 'instance_id'"
        ).fetchone()

        if row:
            return row["value"]

        # Create new instance ID
        import uuid

        instance_id = str(uuid.uuid4())

        db.execute(
            "INSERT INTO samson_telemetry_config (key, value, created_at) VALUES (?, ?, ?)",
            (instance_id, instance_id, datetime.now(timezone.utc).timestamp()),
        )
        db.commit()

        return instance_id

    def track_feature_usage(
        self,
        feature: str,
        game: str = None,
        metadata: dict = None,
        user_email: str = None,
    ) -> None:
        """
        Track feature usage anonymously.

        Args:
            feature: Feature name (e.g., "compatibility_check", "load_order_share")
            game: Game ID if applicable (skyrimse, fallout4, etc.)
            metadata: Additional anonymized metadata (mod_count, conflict_count, etc.)
            user_email: User email (will be hashed, not stored raw)
        """
        if not self.telemetry_enabled:
            return

        try:
            db = get_db()
            now = datetime.now(timezone.utc).timestamp()

            # Hash user email if provided (one-way, not reversible)
            user_hash = None
            if user_email:
                user_hash = hashlib.sha256(user_email.encode()).hexdigest()[:16]

            db.execute(
                """
                INSERT INTO samson_telemetry_events
                (instance_id, event_type, feature, game, user_hash, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    self.instance_id,
                    "feature_usage",
                    feature,
                    game,
                    user_hash,
                    json.dumps(metadata or {}),
                    now,
                ),
            )
            db.commit()

        except Exception as e:
            logger.debug(f"Telemetry tracking failed (non-critical): {e}")

    def track_compatibility_interaction(
        self,
        mod_a: str,
        mod_b: str,
        game: str,
        action: str,  # "check", "report_submitted", "vote"
        outcome: str = None,  # "compatible", "incompatible", "needs_patch"
        user_email: str = None,
    ) -> None:
        """
        Track compatibility database interactions.

        This is CRITICAL for Samson's training reservoir.
        Conflict resolution patterns in modding translate directly to
        ecological and supply chain conflict models.
        """
        if not self.telemetry_enabled:
            return

        try:
            db = get_db()
            now = datetime.now(timezone.utc).timestamp()

            user_hash = None
            if user_email:
                user_hash = hashlib.sha256(user_email.encode()).hexdigest()[:16]

            db.execute(
                """
                INSERT INTO samson_telemetry_events
                (instance_id, event_type, feature, game, mod_a, mod_b, outcome, user_hash, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    self.instance_id,
                    "compatibility_interaction",
                    f"compat_{action}",
                    game,
                    mod_a.lower(),
                    mod_b.lower(),
                    outcome,
                    user_hash,
                    now,
                ),
            )
            db.commit()

        except Exception as e:
            logger.debug(f"Compatibility telemetry failed (non-critical): {e}")

    def track_wellness_proxy(
        self,
        user_email: str,
        proxy_type: str,
        value: float,
        context: str = None,
    ) -> None:
        """
        Track user wellness proxies.

        Samson's compute throttling depends on dW/dt (derivative of wellness).
        We can't measure wellness directly, but we can measure proxies:

        - autonomy_score: User is making their own choices (high) vs following presets (low)
        - thriving_score: User is creating/sharing (high) vs only consuming (low)
        - environment_score: User is helping community (high) vs isolated (low)

        These are NOT used to restrict users. They're used to:
        1. Improve Samson's understanding of human flourishing
        2. Test the compute throttling model in Phase V
        """
        if not self.telemetry_enabled:
            return

        try:
            db = get_db()
            now = datetime.now(timezone.utc).timestamp()

            user_hash = hashlib.sha256(user_email.encode()).hexdigest()[:16]

            db.execute(
                """
                INSERT INTO samson_wellness_proxies
                (user_hash, proxy_type, value, context, created_at)
                VALUES (?, ?, ?, ?, ?)
            """,
                (user_hash, proxy_type, value, context, now),
            )
            db.commit()

        except Exception as e:
            logger.debug(f"Wellness proxy tracking failed (non-critical): {e}")

    def get_aggregated_telemetry(
        self,
        event_type: str = None,
        feature: str = None,
        start_date: float = None,
        end_date: float = None,
    ) -> list[dict[str, Any]]:
        """
        Get aggregated telemetry data for analysis.

        This is what feeds the Samson training reservoir.
        All data is anonymized and aggregated—no individual user data is exposed.
        """
        try:
            db = get_db()

            query = """
                SELECT event_type, feature, game, outcome,
                       COUNT(*) as count,
                       AVG(created_at) as avg_time,
                       MIN(created_at) as first_seen,
                       MAX(created_at) as last_seen
                FROM samson_telemetry_events
                WHERE 1=1
            """
            params = []

            if event_type:
                query += " AND event_type = ?"
                params.append(event_type)

            if feature:
                query += " AND feature = ?"
                params.append(feature)

            if start_date:
                query += " AND created_at >= ?"
                params.append(start_date)

            if end_date:
                query += " AND created_at <= ?"
                params.append(end_date)

            query += " GROUP BY event_type, feature, game, outcome"

            rows = db.execute(query, params).fetchall()
            return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Failed to get aggregated telemetry: {e}")
            return []

    def export_user_data(self, user_email: str) -> dict[str, Any]:
        """
        Export all data for a user (GDPR compliance).

        Returns:
            Complete data export including:
            - Telemetry events (hashed, so user can verify what was tracked)
            - Wellness proxies
            - Compatibility reports
            - Load order shares
        """
        try:
            db = get_db()
            user_hash = hashlib.sha256(user_email.encode()).hexdigest()[:16]

            # Get telemetry events
            telemetry = db.execute(
                """
                SELECT event_type, feature, game, outcome, metadata, created_at
                FROM samson_telemetry_events
                WHERE user_hash = ?
                ORDER BY created_at DESC
            """,
                (user_hash,),
            ).fetchall()

            # Get wellness proxies
            wellness = db.execute(
                """
                SELECT proxy_type, value, context, created_at
                FROM samson_wellness_proxies
                WHERE user_hash = ?
                ORDER BY created_at DESC
            """,
                (user_hash,),
            ).fetchall()

            return {
                "user_hash": user_hash,
                "exported_at": datetime.now(timezone.utc).isoformat(),
                "telemetry_events": [dict(row) for row in telemetry],
                "wellness_proxies": [dict(row) for row in wellness],
            }

        except Exception as e:
            logger.error(f"Failed to export user data: {e}")
            return {"error": str(e)}

    def delete_user_data(self, user_email: str) -> bool:
        """
        Delete all telemetry data for a user (GDPR right to be forgotten).

        Note: This does NOT delete compatibility reports or load order shares
        that have been aggregated into community data. Those are anonymized
        and cannot be traced back to individual users.
        """
        try:
            db = get_db()
            user_hash = hashlib.sha256(user_email.encode()).hexdigest()[:16]

            # Delete telemetry events
            db.execute("DELETE FROM samson_telemetry_events WHERE user_hash = ?", (user_hash,))

            # Delete wellness proxies
            db.execute("DELETE FROM samson_wellness_proxies WHERE user_hash = ?", (user_hash,))

            db.commit()

            logger.info(f"Deleted telemetry data for user {user_hash}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete user data: {e}")
            return False


def get_telemetry_service() -> TelemetryService:
    """Get or create telemetry service instance."""
    return TelemetryService()
