"""
Business Service - Business directory and trust score management.

Handles:
- Business registration and approval
- Trust score calculation
- Voting and flagging
- B2B connections
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any, Optional

from db import get_db

logger = logging.getLogger(__name__)


class BusinessService:
    """Business directory service."""

    # Trust score weights
    WEIGHTS = {
        "community_votes": 0.40,
        "sponsor_performance": 0.20,
        "participation": 0.20,
        "longevity": 0.15,
        "flag_penalty": -0.05,
    }

    # Trust tiers
    TIERS = [
        (0, 20, "new", "New member, no track record yet"),
        (20, 40, "rising", "Building reputation"),
        (40, 65, "established", "Consistent positive presence"),
        (65, 85, "trusted", "Strong community trust"),
        (85, 100, "flagship", "Exceptional standing"),
    ]

    def register_business(
        self, data: dict[str, Any], owner_email: Optional[str] = None
    ) -> Optional[str]:
        """
        Register a new business.

        Args:
            data: Business data (name, website, category, etc.)
            owner_email: Email of business owner (optional)

        Returns:
            Business ID if successful, None otherwise
        """
        try:
            db = get_db()
            business_id = str(uuid.uuid4())

            # Create slug from name
            slug = data["name"].lower().replace(" ", "-").replace(".", "")

            db.execute(
                """
                INSERT INTO businesses (
                    id, name, slug, tagline, description, website, logo_url,
                    contact_email, public_contact_method, public_contact_value,
                    primary_category, secondary_categories, relevant_games,
                    owner_email, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
            """,
                (
                    business_id,
                    data["name"],
                    slug,
                    data.get("tagline", ""),
                    data.get("description", ""),
                    data["website"],
                    data.get("logo_url", ""),
                    data.get("contact_email", ""),
                    data.get("public_contact_method", "form"),
                    data.get("public_contact_value", ""),
                    data["category"],
                    str(data.get("secondary_categories", [])),
                    str(data.get("relevant_games", [])),
                    owner_email,
                ),
            )

            # Initialize trust score
            db.execute(
                """
                INSERT INTO business_trust_scores (business_id)
                VALUES (?)
            """,
                (business_id,),
            )

            db.commit()
            logger.info(f"Registered business: {business_id} ({data['name']})")
            return business_id

        except Exception as e:
            logger.error(f"Failed to register business: {e}")
            return None

    def get_business_by_slug(self, slug: str) -> Optional[dict[str, Any]]:
        """Get business by slug."""
        try:
            db = get_db()
            row = db.execute(
                """
                SELECT * FROM businesses WHERE slug = ? AND status = 'active'
            """,
                (slug,),
            ).fetchone()

            if row:
                return dict(row)
            return None
        except Exception as e:
            logger.error(f"Failed to get business: {e}")
            return None

    def get_directory(self, filters: dict[str, Any] = None) -> list[dict[str, Any]]:
        """
        Get business directory with optional filters.

        Args:
            filters: category, game, tier, search query

        Returns:
            List of businesses with trust scores
        """
        try:
            db = get_db()

            # Build query
            query = """
                SELECT b.*, ts.trust_score, ts.trust_tier, ts.total_votes
                FROM businesses b
                LEFT JOIN business_trust_scores ts ON b.id = ts.business_id
                WHERE b.status = 'active'
            """
            params = []

            if filters:
                if filters.get("category"):
                    query += " AND b.primary_category = ?"
                    params.append(filters["category"])

                if filters.get("game"):
                    query += " AND b.relevant_games LIKE ?"
                    params.append(f"%{filters['game']}%")

                if filters.get("q"):
                    query += " AND (b.name LIKE ? OR b.description LIKE ?)"
                    params.extend([f"%{filters['q']}%", f"%{filters['q']}%"])

            query += " ORDER BY ts.trust_score DESC, b.name"

            rows = db.execute(query, params).fetchall()

            return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Failed to get directory: {e}")
            return []

    def vote(self, business_id: str, voter_id: str, score: int, context: str = None) -> bool:
        """
        Vote on a business.

        Args:
            business_id: Business to vote on
            voter_id: User ID of voter
            score: 1-5 score
            context: Optional comment

        Returns:
            True if successful
        """
        try:
            db = get_db()

            # Insert or replace vote
            db.execute(
                """
                INSERT OR REPLACE INTO business_votes (business_id, voter_user_id, score, context, voted_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
                (business_id, voter_id, score, context),
            )

            # Recalculate trust score
            self._recalculate_trust_score(business_id)

            db.commit()
            logger.info(f"Vote recorded: {business_id} by {voter_id} = {score}")
            return True

        except Exception as e:
            logger.error(f"Failed to record vote: {e}")
            return False

    def flag(self, business_id: str, reporter_id: str, reason: str, detail: str = None) -> bool:
        """
        Flag a business for review.

        Args:
            business_id: Business to flag
            reporter_id: User ID of reporter
            reason: Reason for flag
            detail: Optional details

        Returns:
            True if successful
        """
        try:
            db = get_db()

            db.execute(
                """
                INSERT INTO business_flags (business_id, reporter_user_id, reason, detail, reported_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
                (business_id, reporter_id, reason, detail),
            )

            db.commit()
            logger.info(f"Flag recorded: {business_id} by {reporter_id} - {reason}")
            return True

        except Exception as e:
            logger.error(f"Failed to record flag: {e}")
            return False

    def _recalculate_trust_score(self, business_id: str):
        """Recalculate trust score for a business."""
        try:
            db = get_db()

            # Get votes
            votes = db.execute(
                """
                SELECT score, COUNT(*) as count
                FROM business_votes
                WHERE business_id = ?
                GROUP BY score
            """,
                (business_id,),
            ).fetchall()

            total_votes = sum(v["count"] for v in votes)
            positive_votes = sum(v["count"] for v in votes if v["score"] >= 4)

            # Calculate vote score
            vote_score = (positive_votes / total_votes) if total_votes > 0 else 0.5
            vote_score *= min(1.0, total_votes / 100)  # Volume multiplier

            # Get flags
            flags = db.execute(
                """
                SELECT COUNT(*) as total, SUM(CASE WHEN status = 'open' THEN 1 ELSE 0 END) as open
                FROM business_flags
                WHERE business_id = ?
            """,
                (business_id,),
            ).fetchone()

            flag_penalty = (flags["open"] / flags["total"]) * 15 if flags["total"] > 0 else 0

            # Get business age
            business = db.execute(
                """
                SELECT created_at FROM businesses WHERE id = ?
            """,
                (business_id,),
            ).fetchone()

            months_active = ((datetime.now() - business["created_at"]).days / 30) if business else 0
            longevity_score = min(1.0, months_active / 12)

            # Calculate composite score
            composite = (
                vote_score * self.WEIGHTS["community_votes"]
                + 0.5 * self.WEIGHTS["sponsor_performance"]  # Placeholder
                + 0.5 * self.WEIGHTS["participation"]  # Placeholder
                + longevity_score * self.WEIGHTS["longevity"]
            ) * 100

            composite = max(0, composite - flag_penalty)

            # Assign tier
            tier = "new"
            for low, high, name, _ in self.TIERS:
                if low <= composite < high:
                    tier = name
                    break

            # Update trust score
            db.execute(
                """
                UPDATE business_trust_scores
                SET trust_score = ?, trust_tier = ?, total_votes = ?, positive_votes = ?,
                    community_vote_score = ?, longevity_score = ?, flag_penalty = ?,
                    last_calculated = CURRENT_TIMESTAMP
                WHERE business_id = ?
            """,
                (
                    round(composite, 1),
                    tier,
                    total_votes,
                    positive_votes,
                    round(vote_score, 3),
                    round(longevity_score, 3),
                    round(flag_penalty, 1),
                    business_id,
                ),
            )

            db.commit()

        except Exception as e:
            logger.error(f"Failed to recalculate trust score: {e}")

    def get_trust_score(self, business_id: str) -> dict[str, Any]:
        """Get trust score for a business."""
        try:
            db = get_db()
            row = db.execute(
                """
                SELECT * FROM business_trust_scores WHERE business_id = ?
            """,
                (business_id,),
            ).fetchone()

            if row:
                return dict(row)
            return {}
        except Exception as e:
            logger.error(f"Failed to get trust score: {e}")
            return {}

    def approve_business(self, business_id: str, approved_by: str) -> bool:
        """Approve a business for listing."""
        try:
            db = get_db()
            db.execute(
                """
                UPDATE businesses
                SET status = 'active', approved_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """,
                (business_id,),
            )
            db.commit()
            logger.info(f"Business approved: {business_id} by {approved_by}")
            return True
        except Exception as e:
            logger.error(f"Failed to approve business: {e}")
            return False

    def reject_business(self, business_id: str, reason: str) -> bool:
        """Reject a business application."""
        try:
            db = get_db()
            db.execute(
                """
                UPDATE businesses
                SET status = 'rejected'
                WHERE id = ?
            """,
                (business_id,),
            )
            db.commit()
            logger.info(f"Business rejected: {business_id} - {reason}")
            return True
        except Exception as e:
            logger.error(f"Failed to reject business: {e}")
            return False

    def get_hub_resources(self, category: Optional[str] = None) -> list[dict[str, Any]]:
        """
        Get education hub resources, optionally filtered by category.

        Args:
            category: Category ID to filter by

        Returns:
            List of resources with game analogies and metadata
        """
        try:
            db = get_db()
            if category:
                resources = db.execute(
                    """
                    SELECT id, title, description, category, resource_type,
                           url, analogy, game_reference, difficulty_level, order_index,
                           is_free, created_at
                    FROM hub_resources
                    WHERE category = ?
                    ORDER BY order_index ASC, difficulty_level ASC
                """,
                    (category,),
                ).fetchall()
            else:
                resources = db.execute(
                    """
                    SELECT id, title, description, category, resource_type,
                           url, analogy, game_reference, difficulty_level, order_index,
                           is_free, created_at
                    FROM hub_resources
                    ORDER BY category, order_index ASC
                """
                ).fetchall()

            return [dict(row) for row in resources]
        except Exception as e:
            logger.error(f"Failed to get hub resources: {e}")
            return []

    def add_hub_resource(self, data: dict[str, Any], submitted_by: str) -> Optional[str]:
        """
        Add a new hub resource (requires approval).

        Args:
            data: Resource data (category, title, description, content, type)
            submitted_by: Email of person submitting

        Returns:
            Resource ID if successful, None otherwise
        """
        try:
            db = get_db()
            resource_id = str(uuid.uuid4())

            db.execute(
                """
                INSERT INTO hub_resources
                (id, category, title, description, content, resource_type, author,
                 contributed_by_business_id, upvotes, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, NULL, 0, 'pending', CURRENT_TIMESTAMP)
            """,
                (
                    resource_id,
                    data.get("category"),
                    data.get("title"),
                    data.get("description", ""),
                    data.get("content", ""),
                    data.get("resource_type", "article"),
                    submitted_by,
                ),
            )
            db.commit()

            logger.info(f"Hub resource submitted: {resource_id} by {submitted_by}")
            return resource_id
        except Exception as e:
            logger.error(f"Failed to add hub resource: {e}")
            return None

    def approve_hub_resource(self, resource_id: str, approved_by: str) -> bool:
        """Approve a hub resource for publication."""
        try:
            db = get_db()
            db.execute(
                """
                UPDATE hub_resources
                SET status = 'active', author = ?
                WHERE id = ?
            """,
                (approved_by, resource_id),
            )
            db.commit()
            logger.info(f"Hub resource approved: {resource_id} by {approved_by}")
            return True
        except Exception as e:
            logger.error(f"Failed to approve hub resource: {e}")
            return False


# Singleton instance
_business_service: Optional[BusinessService] = None


def get_business_service() -> BusinessService:
    """Get or create business service singleton."""
    global _business_service
    if _business_service is None:
        _business_service = BusinessService()
    return _business_service
