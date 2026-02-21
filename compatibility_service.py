"""
Compatibility Database - Crowdsourced mod compatibility data

This is SkyModderAI's MOAT:
- Users submit load orders with compatibility status
- Upvote working combinations, flag conflicts
- Search: "Does Mod A work with Mod B?"
- Authors can verify/claim their mods

Nobody else can do this. LOOT can't (rules, not community).
Nexus can't (hosting, not compatibility). ChatGPT can't (no real-time data).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

from db import get_db

logger = logging.getLogger(__name__)


@dataclass
class CompatibilityReport:
    """A user-reported compatibility status between mods."""

    id: int
    mod_a: str  # First mod name
    mod_b: str  # Second mod name
    game: str  # skyrimse, fallout4, etc.
    status: str  # 'compatible', 'incompatible', 'needs_patch'
    description: str  # User's description of the issue/solution
    user_email: str
    upvotes: int
    downvotes: int
    verified: bool  # Verified by mod author or trusted user
    created_at: float
    updated_at: float


@dataclass
class LoadOrderShare:
    """A shared load order from a user."""

    id: int
    name: str  # "Vanilla+ Skyrim SE 2026"
    description: str
    game: str
    mod_count: int
    mods_json: str  # JSON array of mod names
    load_order_json: str  # JSON array of load order positions
    user_email: str
    upvotes: int
    downvotes: int
    downloads: int
    game_version: str
    enb: Optional[str]
    screenshots_json: Optional[str]  # JSON array of screenshot URLs
    created_at: float
    updated_at: float


class CompatibilityService:
    """Manage compatibility reports and load order shares."""

    def submit_compatibility_report(
        self,
        mod_a: str,
        mod_b: str,
        game: str,
        status: str,
        description: str,
        user_email: str,
    ) -> Optional[int]:
        """
        Submit a compatibility report between two mods.

        Returns:
            Report ID if successful, None otherwise
        """
        try:
            db = get_db()

            # Check for duplicate report from same user
            existing = db.execute(
                """
                SELECT id FROM compatibility_reports
                WHERE mod_a = ? AND mod_b = ? AND game = ? AND user_email = ?
            """,
                (mod_a.lower(), mod_b.lower(), game, user_email),
            ).fetchone()

            if existing:
                logger.info(f"Duplicate report from {user_email} for {mod_a} + {mod_b}")
                return existing["id"]

            # Insert new report
            now = datetime.now(timezone.utc).timestamp()
            cursor = db.execute(
                """
                INSERT INTO compatibility_reports
                (mod_a, mod_b, game, status, description, user_email, upvotes, downvotes, verified, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, 0, 0, 0, ?, ?)
            """,
                (mod_a.lower(), mod_b.lower(), game, status, description, user_email, now, now),
            )

            report_id = cursor.lastrowid
            db.commit()

            logger.info(f"Compatibility report submitted: {mod_a} + {mod_b} = {status}")
            return report_id

        except Exception as e:
            logger.error(f"Failed to submit compatibility report: {e}")
            return None

    def vote_report(self, report_id: int, user_email: str, vote: int) -> bool:
        """
        Upvote or downvote a compatibility report.

        Args:
            report_id: Report ID
            user_email: User voting
            vote: 1 for upvote, -1 for downvote

        Returns:
            True if successful
        """
        try:
            db = get_db()
            now = datetime.now(timezone.utc).timestamp()

            # Check if user already voted
            existing = db.execute(
                """
                SELECT vote FROM compatibility_votes
                WHERE report_id = ? AND user_email = ?
            """,
                (report_id, user_email),
            ).fetchone()

            if existing:
                # Update vote
                if existing["vote"] == vote:
                    # Remove vote (toggle off)
                    db.execute(
                        "DELETE FROM compatibility_votes WHERE report_id = ? AND user_email = ?",
                        (report_id, user_email),
                    )
                    if vote > 0:
                        db.execute(
                            "UPDATE compatibility_reports SET upvotes = upvotes - 1 WHERE id = ?",
                            (report_id,),
                        )
                    else:
                        db.execute(
                            "UPDATE compatibility_reports SET downvotes = downvotes - 1 WHERE id = ?",
                            (report_id,),
                        )
                else:
                    # Change vote
                    db.execute(
                        """
                        UPDATE compatibility_votes SET vote = ?, voted_at = ?
                        WHERE report_id = ? AND user_email = ?
                    """,
                        (vote, now, report_id, user_email),
                    )
                    if vote > 0:
                        db.execute(
                            "UPDATE compatibility_reports SET upvotes = upvotes + 1, downvotes = downvotes - 1 WHERE id = ?",
                            (report_id,),
                        )
                    else:
                        db.execute(
                            "UPDATE compatibility_reports SET downvotes = downvotes + 1, upvotes = upvotes - 1 WHERE id = ?",
                            (report_id,),
                        )
            else:
                # New vote
                db.execute(
                    """
                    INSERT INTO compatibility_votes (report_id, user_email, vote, voted_at)
                    VALUES (?, ?, ?, ?)
                """,
                    (report_id, user_email, vote, now),
                )
                if vote > 0:
                    db.execute(
                        "UPDATE compatibility_reports SET upvotes = upvotes + 1 WHERE id = ?",
                        (report_id,),
                    )
                else:
                    db.execute(
                        "UPDATE compatibility_reports SET downvotes = downvotes + 1 WHERE id = ?",
                        (report_id,),
                    )

            db.commit()
            return True

        except Exception as e:
            logger.error(f"Failed to vote on report: {e}")
            return False

    def get_compatibility_status(self, mod_a: str, mod_b: str, game: str) -> dict[str, Any]:
        """
        Get compatibility status between two mods.

        Returns:
            {
                "status": "compatible" | "incompatible" | "needs_patch" | "unknown",
                "confidence": 0.0-1.0,
                "reports": [...],
                "total_reports": int
            }
        """
        try:
            db = get_db()

            # Get all reports for this mod pair (both directions)
            reports = db.execute(
                """
                SELECT id, mod_a, mod_b, status, description, user_email,
                       upvotes, downvotes, verified, created_at
                FROM compatibility_reports
                WHERE (mod_a = ? AND mod_b = ?) OR (mod_a = ? AND mod_b = ?)
                AND game = ?
                ORDER BY verified DESC, upvotes - downvotes DESC, created_at DESC
                LIMIT 50
            """,
                (mod_a.lower(), mod_b.lower(), mod_b.lower(), mod_a.lower(), game),
            ).fetchall()

            if not reports:
                return {"status": "unknown", "confidence": 0.0, "reports": [], "total_reports": 0}

            # Calculate weighted status
            status_weights = {"compatible": 1, "needs_patch": 0, "incompatible": -1}
            total_weight = 0
            status_counts = {"compatible": 0, "needs_patch": 0, "incompatible": 0}

            for report in reports:
                weight = (report["upvotes"] - report["downvotes"]) + 1
                if report["verified"]:
                    weight *= 3  # Verified reports count 3x

                total_weight += weight
                status_counts[report["status"]] += weight

            # Determine overall status
            if status_counts["compatible"] > total_weight * 0.6:
                overall_status = "compatible"
            elif status_counts["incompatible"] > total_weight * 0.4:
                overall_status = "incompatible"
            elif status_counts["needs_patch"] > total_weight * 0.3:
                overall_status = "needs_patch"
            else:
                overall_status = "compatible"  # Default to compatible if no strong signal

            confidence = min(
                1.0, total_weight / 100
            )  # Cap at 100 weighted votes for full confidence

            return {
                "status": overall_status,
                "confidence": confidence,
                "reports": [dict(r) for r in reports[:10]],  # Return top 10
                "total_reports": len(reports),
            }

        except Exception as e:
            logger.error(f"Failed to get compatibility status: {e}")
            return {"status": "unknown", "confidence": 0.0, "reports": [], "total_reports": 0}

    def share_load_order(
        self,
        name: str,
        description: str,
        game: str,
        mods: list[str],
        load_order: list[int],
        user_email: str,
        game_version: str = "",
        enb: str = "",
        screenshots: list[str] = None,
    ) -> Optional[int]:
        """
        Share a load order with the community.

        Returns:
            Load order ID if successful
        """
        import json

        try:
            db = get_db()
            now = datetime.now(timezone.utc).timestamp()

            cursor = db.execute(
                """
                INSERT INTO load_order_shares
                (name, description, game, mod_count, mods_json, load_order_json, user_email,
                 upvotes, downvotes, downloads, game_version, enb, screenshots_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 0, 0, 0, ?, ?, ?, ?, ?)
            """,
                (
                    name,
                    description,
                    game,
                    len(mods),
                    json.dumps(mods),
                    json.dumps(load_order),
                    user_email,
                    game_version,
                    enb,
                    json.dumps(screenshots or []),
                    now,
                    now,
                ),
            )

            share_id = cursor.lastrowid
            db.commit()

            logger.info(f"Load order shared: {name} by {user_email} ({len(mods)} mods)")
            return share_id

        except Exception as e:
            logger.error(f"Failed to share load order: {e}")
            return None

    def get_shared_load_orders(
        self,
        game: str = None,
        limit: int = 50,
        offset: int = 0,
        sort: str = "top",  # top, new, downloads
    ) -> list[dict[str, Any]]:
        """Get shared load orders with optional filters."""
        try:
            db = get_db()

            # Build query
            query = """
                SELECT id, name, description, game, mod_count, user_email,
                       upvotes, downvotes, downloads, game_version, enb, created_at
                FROM load_order_shares
                WHERE 1=1
            """
            params = []

            if game:
                query += " AND game = ?"
                params.append(game)

            # Sort
            if sort == "top":
                query += " ORDER BY upvotes - downvotes DESC"
            elif sort == "new":
                query += " ORDER BY created_at DESC"
            elif sort == "downloads":
                query += " ORDER BY downloads DESC"
            else:
                query += " ORDER BY upvotes - downvotes DESC"

            query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            rows = db.execute(query, params).fetchall()
            return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Failed to get load orders: {e}")
            return []

    def search_compatibility(
        self, query: str, game: str = None, limit: int = 20
    ) -> list[dict[str, Any]]:
        """
        Search for compatibility reports by mod name.

        Example: Search "USSEP" → find all reports involving USSEP
        """
        try:
            db = get_db()

            query_sql = """
                SELECT DISTINCT mod_a, mod_b, game,
                       (SELECT status FROM compatibility_reports r2
                        WHERE (r2.mod_a = r.mod_a AND r2.mod_b = r.mod_b) OR (r2.mod_a = r.mod_b AND r2.mod_b = r.mod_a)
                        ORDER BY upvotes - downvotes DESC LIMIT 1) as status,
                       (SELECT COUNT(*) FROM compatibility_reports r2
                        WHERE (r2.mod_a = r.mod_a AND r2.mod_b = r.mod_b) OR (r2.mod_a = r.mod_b AND r2.mod_b = r.mod_a)) as report_count
                FROM compatibility_reports r
                WHERE (mod_a LIKE ? OR mod_b LIKE ?)
            """
            params = [f"%{query}%", f"%{query}%"]

            if game:
                query_sql += " AND game = ?"
                params.append(game)

            query_sql += " ORDER BY report_count DESC LIMIT ?"
            params.append(limit)

            rows = db.execute(query_sql, params).fetchall()
            return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Failed to search compatibility: {e}")
            return []


def get_compatibility_service() -> CompatibilityService:
    """Get or create compatibility service instance."""
    return CompatibilityService()
