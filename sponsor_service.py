"""
Sponsor Service - Ethical, Pay-Per-Click Sponsorship System

Features:
- $5 CPM (cost per 1,000 clicks)
- $50 prepaid plan (10,000 clicks)
- Server-side click tracking with fraud protection
- Ad creative rotation (lowest-impressions first)
- Separate community score + CTR in ranking
- Democratic ranking formula: (community * 0.6) + (normalized_ctr * 0.4)

Privacy-first: User data never sold, only used for relevant sponsor matching.
"""

import hashlib
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class SponsorCreative:
    """An ad creative for a sponsor."""

    id: str
    sponsor_id: str
    name: str
    image_url: str
    headline: str
    body_copy: str
    landing_url: str
    status: str = "active"  # active, paused
    impressions: int = 0
    clicks: int = 0
    created_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "sponsor_id": self.sponsor_id,
            "name": self.name,
            "image_url": self.image_url,
            "headline": self.headline,
            "body_copy": self.body_copy,
            "landing_url": self.landing_url,
            "status": self.status,
            "impressions": self.impressions,
            "clicks": self.clicks,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


@dataclass
class Sponsor:
    """A sponsor in the system."""

    id: str
    name: str
    website: str
    contact_email: str
    product_description: str
    category: str
    logo_url: str = ""
    landing_url: str = ""
    description: str = ""

    # Pricing
    pricing_model: str = "pay_per_click"
    cpm_rate: float = 5.00
    plan_clicks: int = 10000
    plan_price: float = 50.00
    click_credits: int = 0

    # Performance
    impressions: int = 0
    clicks: int = 0
    ctr: float = 0.0
    monthly_spend: float = 0.0
    billable_clicks: int = 0

    # Community score (separate from CTR)
    community_score: float = 0.0
    community_votes: int = 0

    # Ranking score (computed)
    ranking_score: float = 0.0

    # Status
    status: str = "pending"  # pending, active, paused, rejected
    verified_date: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    rejected_at: Optional[datetime] = None
    rejected_reason: Optional[str] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "website": self.website,
            "contact_email": self.contact_email,
            "product_description": self.product_description,
            "category": self.category,
            "logo_url": self.logo_url,
            "landing_url": self.landing_url,
            "description": self.description,
            "pricing": {
                "model": self.pricing_model,
                "cpm_rate": self.cpm_rate,
                "plan_clicks": self.plan_clicks,
                "plan_price": self.plan_price,
                "click_credits": self.click_credits
            },
            "performance": {
                "impressions": self.impressions,
                "clicks": self.clicks,
                "ctr": self.ctr,
                "monthly_spend": self.monthly_spend,
                "billable_clicks": self.billable_clicks
            },
            "community": {
                "score": self.community_score,
                "votes": self.community_votes
            },
            "ranking_score": self.ranking_score,
            "status": self.status,
            "verified_date": self.verified_date.isoformat() if self.verified_date else None,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "approved_by": self.approved_by,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


@dataclass
class ClickRecord:
    """A tracked click for billing audit."""

    sponsor_id: str
    creative_id: Optional[str]
    user_id: Optional[str]
    fingerprint_hash: str
    billable: bool
    rejection_reason: Optional[str]
    timestamp: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sponsor_id": self.sponsor_id,
            "creative_id": self.creative_id,
            "user_id": self.user_id,
            "fingerprint_hash": self.fingerprint_hash,
            "billable": self.billable,
            "rejection_reason": self.rejection_reason,
            "timestamp": self.timestamp
        }


class SponsorService:
    """Manage sponsors, creatives, clicks, and billing."""

    # Pricing: $5 per 1,000 clicks
    CPM_RATE = 5.00
    CLICKS_PER_PLAN = 10000
    PLAN_PRICE = 50.00

    # Fraud protection: 24-hour dedup window
    FRAUD_WINDOW = 86400  # seconds

    # Storage limits (configurable, not hardcoded in production)
    MAX_CREATIVES_PER_SPONSOR = 100
    MAX_CREATIVE_SIZE_MB = 2
    ALLOWED_FORMATS = ["jpg", "png", "webp", "gif"]

    # Ranking weights
    COMMUNITY_WEIGHT = 0.6
    CTR_WEIGHT = 0.4
    CTR_NORMALIZATION_MAX = 5.0  # 5% CTR = 1.0 normalized

    def __init__(self):
        """Initialize sponsor service."""
        self._db = None

    def _get_db(self):
        """Get database connection from Flask g object."""
        from flask import g
        if 'db' not in g:
            from db import get_db
            g.db = get_db()
        return g.db

    def _hash_fingerprint(self, ip: str, user_agent: str) -> str:
        """Create SHA256 hash of IP + User Agent."""
        data = f"{ip}:{user_agent}"
        return hashlib.sha256(data.encode()).hexdigest()

    def _calculate_click_cost(self) -> float:
        """Calculate cost per click."""
        return self.CPM_RATE / self.CLICKS_PER_PLAN

    def _calculate_ranking_score(self, community_score: float, ctr: float) -> float:
        """
        Calculate ranking score using weighted formula.

        ranking_score = (community_score * 0.6) + (normalized_ctr * 0.4)
        """
        # Normalize CTR (assume 5% is excellent = 1.0)
        normalized_ctr = min(ctr / self.CTR_NORMALIZATION_MAX, 1.0)
        return (community_score * self.COMMUNITY_WEIGHT) + (normalized_ctr * self.CTR_WEIGHT)

    def create_sponsor(
        self,
        name: str,
        website: str,
        contact_email: str,
        product_description: str,
        category: str,
        description: str = "",
        landing_url: str = ""
    ) -> Optional[Sponsor]:
        """
        Create a new sponsor application.

        Returns Sponsor on success, None on failure.
        """
        sponsor_id = str(uuid.uuid4())[:8]
        now = datetime.now()

        sponsor = Sponsor(
            id=sponsor_id,
            name=name,
            website=website,
            contact_email=contact_email,
            product_description=product_description,
            category=category,
            description=description,
            landing_url=landing_url,
            status="pending",
            created_at=now,
            updated_at=now
        )

        try:
            db = self._get_db()
            db.execute("""
                INSERT INTO sponsors (
                    sponsor_id, name, website, contact_email, product_description,
                    category, description, landing_url, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                sponsor_id, name, website, contact_email, product_description,
                category, description, landing_url, "pending", now, now
            ))
            db.commit()
            logger.info(f"Created sponsor application: {sponsor_id} ({name})")
            return sponsor
        except Exception as e:
            logger.error(f"Failed to create sponsor: {e}")
            return None

    def get_sponsor(self, sponsor_id: str) -> Optional[Sponsor]:
        """Get sponsor by ID."""
        db = self._get_db()
        row = db.execute(
            "SELECT * FROM sponsors WHERE sponsor_id = ?", (sponsor_id,)
        ).fetchone()

        if not row:
            return None

        return self._row_to_sponsor(row)

    def _row_to_sponsor(self, row) -> Sponsor:
        """Convert database row to Sponsor object."""
        return Sponsor(
            id=row["sponsor_id"],
            name=row["name"],
            website=row["website"],
            contact_email=row.get("contact_email"),
            product_description=row.get("product_description"),
            category=row["category"],
            logo_url=row.get("logo_url", ""),
            landing_url=row.get("landing_url", ""),
            description=row.get("description", ""),
            pricing_model=row.get("pricing_model", "pay_per_click"),
            cpm_rate=row.get("cpm_rate", 5.00),
            plan_clicks=row.get("plan_clicks", 10000),
            plan_price=row.get("plan_price", 50.00),
            click_credits=row.get("click_credits", 0),
            impressions=row.get("impressions", 0),
            clicks=row.get("clicks", 0),
            ctr=row.get("ctr", 0.0),
            monthly_spend=row.get("monthly_spend", 0.0),
            billable_clicks=row.get("billable_clicks", 0),
            community_score=row.get("community_score", 0.0),
            community_votes=row.get("community_votes", 0),
            ranking_score=row.get("ranking_score", 0.0),
            status=row["status"],
            verified_date=datetime.fromisoformat(row["verified_date"]) if row.get("verified_date") else None,
            approved_at=datetime.fromisoformat(row["approved_at"]) if row.get("approved_at") else None,
            approved_by=row.get("approved_by"),
            rejected_at=datetime.fromisoformat(row["rejected_at"]) if row.get("rejected_at") else None,
            rejected_reason=row.get("rejected_reason"),
            created_at=datetime.fromisoformat(row["created_at"]) if row.get("created_at") else None,
            updated_at=datetime.fromisoformat(row["updated_at"]) if row.get("updated_at") else None
        )

    def get_all_sponsors(self, status: str = None) -> List[Sponsor]:
        """Get all sponsors, optionally filtered by status."""
        db = self._get_db()
        if status:
            rows = db.execute(
                "SELECT * FROM sponsors WHERE status = ? ORDER BY ranking_score DESC",
                (status,)
            ).fetchall()
        else:
            rows = db.execute(
                "SELECT * FROM sponsors ORDER BY ranking_score DESC"
            ).fetchall()

        return [self._row_to_sponsor(row) for row in rows]

    def get_ranked_sponsors(self, category: str = None, limit: int = 10) -> List[Sponsor]:
        """
        Get sponsors ranked by community score + CTR.

        Ranking formula:
        - 60% community score (trust)
        - 40% normalized CTR (relevance)
        """
        db = self._get_db()

        if category:
            rows = db.execute("""
                SELECT * FROM sponsors
                WHERE status = 'active' AND category = ?
                ORDER BY ranking_score DESC
                LIMIT ?
            """, (category, limit)).fetchall()
        else:
            rows = db.execute("""
                SELECT * FROM sponsors
                WHERE status = 'active'
                ORDER BY ranking_score DESC
                LIMIT ?
            """, (limit,)).fetchall()

        return [self._row_to_sponsor(row) for row in rows]

    # ==================== Creative Management ====================

    def create_creative(
        self,
        sponsor_id: str,
        name: str,
        image_url: str,
        headline: str,
        body_copy: str,
        landing_url: str
    ) -> Optional[SponsorCreative]:
        """
        Create a new ad creative for a sponsor.

        Returns SponsorCreative on success, None on failure.
        """
        # Check sponsor exists and is active
        sponsor = self.get_sponsor(sponsor_id)
        if not sponsor:
            logger.error(f"Sponsor not found: {sponsor_id}")
            return None

        # Check creative limit
        existing = self.get_creatives(sponsor_id)
        if len(existing) >= self.MAX_CREATIVES_PER_SPONSOR:
            logger.error(f"Sponsor {sponsor_id} has reached max creatives limit")
            return None

        creative_id = str(uuid.uuid4())[:8]
        now = datetime.now()

        creative = SponsorCreative(
            id=creative_id,
            sponsor_id=sponsor_id,
            name=name,
            image_url=image_url,
            headline=headline,
            body_copy=body_copy,
            landing_url=landing_url,
            status="active",
            created_at=now
        )

        try:
            db = self._get_db()
            db.execute("""
                INSERT INTO sponsor_creatives (
                    creative_id, sponsor_id, name, image_url, headline,
                    body_copy, landing_url, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                creative_id, sponsor_id, name, image_url, headline,
                body_copy, landing_url, "active", now
            ))
            db.commit()
            logger.info(f"Created creative {creative_id} for sponsor {sponsor_id}")
            return creative
        except Exception as e:
            logger.error(f"Failed to create creative: {e}")
            return None

    def get_creatives(self, sponsor_id: str, status: str = None) -> List[SponsorCreative]:
        """Get all creatives for a sponsor."""
        db = self._get_db()

        if status:
            rows = db.execute("""
                SELECT * FROM sponsor_creatives
                WHERE sponsor_id = ? AND status = ?
                ORDER BY impressions ASC
            """, (sponsor_id, status)).fetchall()
        else:
            rows = db.execute("""
                SELECT * FROM sponsor_creatives
                WHERE sponsor_id = ?
                ORDER BY impressions ASC
            """, (sponsor_id,)).fetchall()

        return [self._row_to_creative(row) for row in rows]

    def _row_to_creative(self, row) -> SponsorCreative:
        """Convert database row to SponsorCreative object."""
        return SponsorCreative(
            id=row["creative_id"],
            sponsor_id=row["sponsor_id"],
            name=row.get("name"),
            image_url=row.get("image_url"),
            headline=row.get("headline"),
            body_copy=row.get("body_copy"),
            landing_url=row.get("landing_url"),
            status=row.get("status", "active"),
            impressions=row.get("impressions", 0),
            clicks=row.get("clicks", 0),
            created_at=datetime.fromisoformat(row["created_at"]) if row.get("created_at") else None
        )

    def get_next_creative(self, sponsor_id: str) -> Optional[SponsorCreative]:
        """
        Get the next creative to serve for a sponsor.

        Rotation logic: serve the active creative with lowest impressions
        (equalizes exposure across creatives).
        """
        db = self._get_db()
        row = db.execute("""
            SELECT * FROM sponsor_creatives
            WHERE sponsor_id = ? AND status = 'active'
            ORDER BY impressions ASC
            LIMIT 1
        """, (sponsor_id,)).fetchone()

        if not row:
            return None

        return self._row_to_creative(row)

    def pause_creative(self, creative_id: str) -> bool:
        """Pause a creative."""
        now = datetime.now()
        db = self._get_db()
        db.execute("""
            UPDATE sponsor_creatives
            SET status = 'paused', paused_at = ?
            WHERE creative_id = ?
        """, (now, creative_id))
        db.commit()
        return db.total_changes > 0

    def activate_creative(self, creative_id: str) -> bool:
        """Activate a paused creative."""
        db = self._get_db()
        db.execute("""
            UPDATE sponsor_creatives
            SET status = 'active'
            WHERE creative_id = ?
        """, (creative_id,))
        db.commit()
        return db.total_changes > 0

    def record_creative_impression(self, creative_id: str) -> bool:
        """Record an impression for a creative."""
        db = self._get_db()

        # Update creative impressions
        db.execute("""
            UPDATE sponsor_creatives
            SET impressions = impressions + 1
            WHERE creative_id = ?
        """, (creative_id,))

        # Get sponsor_id and update sponsor impressions
        row = db.execute(
            "SELECT sponsor_id FROM sponsor_creatives WHERE creative_id = ?",
            (creative_id,)
        ).fetchone()

        if row:
            db.execute("""
                UPDATE sponsors
                SET impressions = impressions + 1
                WHERE sponsor_id = ?
            """, (row["sponsor_id"],))

        db.commit()
        return db.total_changes > 0

    # ==================== Click Tracking & Fraud Protection ====================

    def record_click(
        self,
        sponsor_id: str,
        creative_id: Optional[str],
        user_id: Optional[str],
        request
    ) -> Tuple[bool, str, ClickRecord]:
        """
        Record click with fraud protection.

        Args:
            sponsor_id: Sponsor ID
            creative_id: Creative ID (optional)
            user_id: User ID (optional for guests)
            request: Flask request object

        Returns:
            (is_billable, message, click_record)
            - True, "Click recorded", ClickRecord(billable=True) = billable click
            - False, "Duplicate click", ClickRecord(billable=False) = filtered
        """
        # Verify sponsor exists
        sponsor = self.get_sponsor(sponsor_id)
        if not sponsor:
            return False, "Sponsor not found", None

        # Get fingerprint (IP + User Agent) and hash it
        ip = request.remote_addr
        user_agent = request.headers.get('User-Agent', '')
        fingerprint_hash = self._hash_fingerprint(ip, user_agent)

        now = time.time()

        # Check for duplicate within 24h window
        db = self._get_db()
        last_click = db.execute("""
            SELECT timestamp FROM sponsor_clicks
            WHERE fingerprint_hash = ? AND sponsor_id = ?
            AND timestamp > ?
            ORDER BY timestamp DESC
            LIMIT 1
        """, (fingerprint_hash, sponsor_id, now - self.FRAUD_WINDOW)).fetchone()

        if last_click:
            # Duplicate click - log but mark as non-billable
            click_record = ClickRecord(
                sponsor_id=sponsor_id,
                creative_id=creative_id,
                user_id=user_id,
                fingerprint_hash=fingerprint_hash,
                billable=False,
                rejection_reason="Duplicate click (24h window)",
                timestamp=now
            )
            self._log_click(click_record)
            logger.debug(f"Duplicate click filtered: {sponsor_id} from {fingerprint_hash[:16]}...")
            return False, "Duplicate click (24h window)", click_record

        # Valid billable click
        click_record = ClickRecord(
            sponsor_id=sponsor_id,
            creative_id=creative_id,
            user_id=user_id,
            fingerprint_hash=fingerprint_hash,
            billable=True,
            rejection_reason=None,
            timestamp=now
        )
        self._log_click(click_record)

        # Update sponsor stats
        db.execute("""
            UPDATE sponsors
            SET clicks = clicks + 1, billable_clicks = billable_clicks + 1
            WHERE sponsor_id = ?
        """, (sponsor_id,))

        if creative_id:
            db.execute("""
                UPDATE sponsor_creatives
                SET clicks = clicks + 1
                WHERE creative_id = ?
            """, (creative_id,))

        # Update CTR
        if sponsor.impressions > 0:
            new_ctr = (sponsor.clicks / sponsor.impressions) * 100
            db.execute("""
                UPDATE sponsors SET ctr = ? WHERE sponsor_id = ?
            """, (new_ctr, sponsor_id))

            # Update ranking score
            new_ranking = self._calculate_ranking_score(sponsor.community_score, new_ctr)
            db.execute("""
                UPDATE sponsors SET ranking_score = ? WHERE sponsor_id = ?
            """, (new_ranking, sponsor_id))

        db.commit()

        logger.info(f"Billable click recorded: {sponsor_id} from {fingerprint_hash[:16]}...")
        return True, "Click recorded", click_record

    def _log_click(self, click: ClickRecord):
        """Log click to database for billing audit."""
        db = self._get_db()
        db.execute("""
            INSERT INTO sponsor_clicks (
                sponsor_id, creative_id, user_id, fingerprint_hash,
                billable, rejection_reason, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            click.sponsor_id,
            click.creative_id,
            click.user_id,
            click.fingerprint_hash,
            1 if click.billable else 0,
            click.rejection_reason,
            click.timestamp
        ))
        db.commit()

    # ==================== Community Voting ====================

    def vote(self, sponsor_id: str, user_id: str, score: int) -> Dict[str, Any]:
        """
        Vote on a sponsor (1-5 stars).

        Returns updated community score.
        """
        if score < 1 or score > 5:
            return {"error": "Score must be 1-5"}

        sponsor = self.get_sponsor(sponsor_id)
        if not sponsor:
            return {"error": "Sponsor not found"}

        db = self._get_db()
        now = datetime.now()

        # Insert or replace vote
        db.execute("""
            INSERT OR REPLACE INTO sponsor_votes (user_id, sponsor_id, score, voted_at)
            VALUES (?, ?, ?, ?)
        """, (user_id, sponsor_id, score, now))

        # Recalculate average score
        result = db.execute("""
            SELECT AVG(score) as avg_score, COUNT(*) as vote_count
            FROM sponsor_votes
            WHERE sponsor_id = ?
        """, (sponsor_id,)).fetchone()

        new_score = round(result["avg_score"], 2)
        new_votes = result["vote_count"]

        # Update sponsor
        db.execute("""
            UPDATE sponsors
            SET community_score = ?, community_votes = ?
            WHERE sponsor_id = ?
        """, (new_score, new_votes, sponsor_id))

        # Update ranking score
        new_ranking = self._calculate_ranking_score(new_score, sponsor.ctr)
        db.execute("""
            UPDATE sponsors SET ranking_score = ? WHERE sponsor_id = ?
        """, (new_ranking, sponsor_id))

        db.commit()

        logger.info(f"Vote recorded: user {user_id} gave {score} to sponsor {sponsor_id}")

        return {
            "score": new_score,
            "votes": new_votes,
            "ranking_score": new_ranking
        }

    def get_user_vote(self, sponsor_id: str, user_id: str) -> Optional[int]:
        """Get a user's vote for a sponsor."""
        db = self._get_db()
        row = db.execute("""
            SELECT score FROM sponsor_votes
            WHERE sponsor_id = ? AND user_id = ?
        """, (sponsor_id, user_id)).fetchone()
        return row["score"] if row else None

    # ==================== Admin Functions ====================

    def approve_sponsor(self, sponsor_id: str, approved_by: str) -> bool:
        """Approve a sponsor application."""
        now = datetime.now()
        db = self._get_db()
        db.execute("""
            UPDATE sponsors
            SET status = 'active', approved_at = ?, approved_by = ?
            WHERE sponsor_id = ?
        """, (now, approved_by, sponsor_id))
        db.commit()
        return db.total_changes > 0

    def reject_sponsor(self, sponsor_id: str, reason: str) -> bool:
        """Reject a sponsor application."""
        now = datetime.now()
        db = self._get_db()
        db.execute("""
            UPDATE sponsors
            SET status = 'rejected', rejected_at = ?, rejected_reason = ?
            WHERE sponsor_id = ?
        """, (now, reason, sponsor_id))
        db.commit()
        return db.total_changes > 0

    def get_pending_applications(self) -> List[Sponsor]:
        """Get all pending sponsor applications."""
        return self.get_all_sponsors(status="pending")

    def get_billing_summary(self, sponsor_id: str) -> Dict[str, Any]:
        """Get billing summary for a sponsor."""
        sponsor = self.get_sponsor(sponsor_id)
        if not sponsor:
            return {"error": "Sponsor not found"}

        db = self._get_db()

        # Get billable clicks count
        result = db.execute("""
            SELECT COUNT(*) as count, SUM(CASE WHEN billable THEN 1 ELSE 0 END) as billable
            FROM sponsor_clicks
            WHERE sponsor_id = ?
        """, (sponsor_id,)).fetchone()

        return {
            "sponsor_id": sponsor_id,
            "plan": {
                "clicks": self.CLICKS_PER_PLAN,
                "price": self.PLAN_PRICE,
                "cpm": self.CPM_RATE
            },
            "performance": {
                "impressions": sponsor.impressions,
                "clicks": sponsor.clicks,
                "billable_clicks": sponsor.billable_clicks,
                "ctr": sponsor.ctr,
                "monthly_spend": sponsor.monthly_spend
            },
            "community": {
                "score": sponsor.community_score,
                "votes": sponsor.community_votes
            },
            "ranking_score": sponsor.ranking_score,
            "cost_per_click": self._calculate_click_cost(),
            "click_credits_remaining": sponsor.click_credits,
            "audit": {
                "total_clicks_logged": result["count"],
                "billable_clicks": result["billable"] or 0
            }
        }


# ==================== Singleton ====================

_sponsor_service: Optional[SponsorService] = None


def get_sponsor_service() -> SponsorService:
    """Get or create sponsor service singleton."""
    global _sponsor_service
    if _sponsor_service is None:
        _sponsor_service = SponsorService()
    return _sponsor_service


# Convenience functions
def create_sponsor(*args, **kwargs) -> Optional[Sponsor]:
    return get_sponsor_service().create_sponsor(*args, **kwargs)


def get_sponsor(sponsor_id: str) -> Optional[Sponsor]:
    return get_sponsor_service().get_sponsor(sponsor_id)


def get_ranked_sponsors(category: str = None, limit: int = 10) -> List[Sponsor]:
    return get_sponsor_service().get_ranked_sponsors(category, limit)


def record_click(sponsor_id: str, creative_id: str, user_id: Optional[str], request) -> Tuple[bool, str, ClickRecord]:
    return get_sponsor_service().record_click(sponsor_id, creative_id, user_id, request)


def vote(sponsor_id: str, user_id: str, score: int) -> Dict[str, Any]:
    return get_sponsor_service().vote(sponsor_id, user_id, score)
