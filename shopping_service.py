"""
Shopping Service - Business Advertising with Pay-Per-Click

Features:
- First month FREE for new businesses (automatic upon approval)
- After first month: $5 per 1,000 clicks ($0.005 per click)
- Simple meter charge (no packages)
- Server-side click tracking with fraud protection
- Automatic ad placement on directory and shopping pages
- Democratic ranking (community score + CTR)

Privacy-first: User data never sold, only used for ad relevance.
"""

from __future__ import annotations

import hashlib
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class AdCampaign:
    """An advertising campaign for a business."""

    id: int
    business_id: str
    name: str
    status: str = "draft"  # draft, active, paused, ended
    budget_type: str = "prepaid"  # prepaid, monthly
    budget_amount: float = 0.0
    spent_amount: float = 0.0
    click_credits: int = 0
    click_price_per_thousand: float = 5.00

    # First month free tracking
    first_month_free: bool = False
    first_month_start: Optional[datetime] = None
    first_month_end: Optional[datetime] = None

    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Computed fields
    total_impressions: int = 0
    total_clicks: int = 0
    ctr: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "business_id": self.business_id,
            "name": self.name,
            "status": self.status,
            "budget_type": self.budget_type,
            "budget_amount": self.budget_amount,
            "spent_amount": self.spent_amount,
            "click_credits": self.click_credits,
            "click_price_per_thousand": self.click_price_per_thousand,
            "first_month_free": self.first_month_free,
            "first_month_start": (
                self.first_month_start.isoformat() if self.first_month_start else None
            ),
            "first_month_end": self.first_month_end.isoformat() if self.first_month_end else None,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "total_impressions": self.total_impressions,
            "total_clicks": self.total_clicks,
            "ctr": self.ctr,
        }


@dataclass
class AdCreative:
    """An ad creative asset."""

    id: int
    campaign_id: int
    name: str
    image_url: Optional[str] = None
    headline: str = ""
    body_copy: Optional[str] = None
    cta_text: str = "Learn More"
    landing_url: str = ""
    status: str = "draft"  # draft, active, paused, rejected
    impressions: int = 0
    clicks: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "campaign_id": self.campaign_id,
            "name": self.name,
            "image_url": self.image_url,
            "headline": self.headline,
            "body_copy": self.body_copy,
            "cta_text": self.cta_text,
            "landing_url": self.landing_url,
            "status": self.status,
            "impressions": self.impressions,
            "clicks": self.clicks,
            "ctr": (self.clicks / self.impressions * 100) if self.impressions > 0 else 0.0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


@dataclass
class AdClick:
    """A tracked click for billing."""

    id: int
    creative_id: int
    campaign_id: int
    business_id: str
    user_id: Optional[str]
    fingerprint_hash: str
    billable: bool
    rejection_reason: Optional[str]
    cost: float
    timestamp: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "creative_id": self.creative_id,
            "campaign_id": self.campaign_id,
            "business_id": self.business_id,
            "user_id": self.user_id,
            "fingerprint_hash": self.fingerprint_hash,
            "billable": self.billable,
            "rejection_reason": self.rejection_reason,
            "cost": self.cost,
            "timestamp": self.timestamp,
        }


class ShoppingService:
    """Manage business advertising campaigns and pay-per-click billing."""

    # Pricing: $5 per 1,000 clicks
    CPM_RATE = 5.00
    METER_MODEL = True  # Simple meter charge, no packages

    # Fraud protection: 24-hour dedup window
    FRAUD_WINDOW = 86400  # seconds

    # First month free period
    FIRST_MONTH_DAYS = 30

    def __init__(self):
        """Initialize shopping service."""
        self._db = None

    def _get_db(self):
        """Get database connection from Flask g object."""
        from db import get_db

        return get_db()

    def _hash_fingerprint(self, ip: str, user_agent: str) -> str:
        """Create SHA256 hash of IP + User Agent."""
        data = f"{ip}:{user_agent}"
        return hashlib.sha256(data.encode()).hexdigest()

    def _calculate_click_cost(self) -> float:
        """Calculate cost per click."""
        return self.CPM_RATE / self.CLICKS_PER_PLAN

    def _is_first_month_free(self, campaign: AdCampaign) -> bool:
        """Check if campaign is still in first month free period."""
        if not campaign.first_month_free or not campaign.first_month_end:
            return False
        return datetime.now() < campaign.first_month_end

    # ==================== Campaign Management ====================

    def create_campaign(
        self,
        business_id: str,
        name: str,
        budget_type: str = "prepaid",
        budget_amount: float = 50.00,
        first_month_free: bool = True,
    ) -> Optional[AdCampaign]:
        """
        Create a new ad campaign for a business.

        First month is FREE - automatic upon business approval.
        """
        now = datetime.now()
        first_month_end = now + timedelta(days=self.FIRST_MONTH_DAYS) if first_month_free else None

        # Calculate click credits based on budget
        click_credits = int((budget_amount / self.CPM_RATE) * 1000) if budget_amount > 0 else 0

        campaign = AdCampaign(
            id=0,  # Will be set by DB
            business_id=business_id,
            name=name,
            status="active" if first_month_free else "draft",
            budget_type=budget_type,
            budget_amount=budget_amount,
            click_credits=click_credits,
            first_month_free=first_month_free,
            first_month_start=now if first_month_free else None,
            first_month_end=first_month_end,
            created_at=now,
            updated_at=now,
        )

        try:
            db = self._get_db()
            cursor = db.execute(
                """
                INSERT INTO ad_campaigns (
                    business_id, name, status, budget_type, budget_amount,
                    click_credits, first_month_free, first_month_start, first_month_end,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    business_id,
                    name,
                    campaign.status,
                    budget_type,
                    budget_amount,
                    click_credits,
                    1 if first_month_free else 0,
                    now,
                    first_month_end,
                    now,
                    now,
                ),
            )
            campaign.id = cursor.lastrowid
            db.commit()
            logger.info(f"Created ad campaign {campaign.id} for business {business_id}")
            return campaign
        except Exception as e:
            logger.error(f"Failed to create campaign: {e}")
            return None

    def get_campaign(self, campaign_id: int) -> Optional[AdCampaign]:
        """Get campaign by ID."""
        db = self._get_db()
        row = db.execute("SELECT * FROM ad_campaigns WHERE id = ?", (campaign_id,)).fetchone()

        if not row:
            return None

        return self._row_to_campaign(row)

    def get_campaigns_for_business(self, business_id: str) -> list[AdCampaign]:
        """Get all campaigns for a business."""
        db = self._get_db()
        rows = db.execute(
            """
            SELECT * FROM ad_campaigns
            WHERE business_id = ?
            ORDER BY created_at DESC
            """,
            (business_id,),
        ).fetchall()

        campaigns = [self._row_to_campaign(row) for row in rows]

        # Update stats for each campaign
        for campaign in campaigns:
            stats = self.get_campaign_stats(campaign.id)
            campaign.total_impressions = stats.get("impressions", 0)
            campaign.total_clicks = stats.get("clicks", 0)
            if campaign.total_impressions > 0:
                campaign.ctr = (campaign.total_clicks / campaign.total_impressions) * 100

        return campaigns

    def _row_to_campaign(self, row) -> AdCampaign:
        """Convert database row to AdCampaign."""
        return AdCampaign(
            id=row["id"],
            business_id=row["business_id"],
            name=row["name"],
            status=row["status"],
            budget_type=row["budget_type"],
            budget_amount=row["budget_amount"],
            spent_amount=row["spent_amount"],
            click_credits=row["click_credits"],
            click_price_per_thousand=row["click_price_per_thousand"],
            first_month_free=bool(row["first_month_free"]),
            first_month_start=(
                datetime.fromisoformat(row["first_month_start"])
                if row.get("first_month_start")
                else None
            ),
            first_month_end=(
                datetime.fromisoformat(row["first_month_end"])
                if row.get("first_month_end")
                else None
            ),
            start_date=datetime.fromisoformat(row["start_date"]) if row.get("start_date") else None,
            end_date=datetime.fromisoformat(row["end_date"]) if row.get("end_date") else None,
            created_at=datetime.fromisoformat(row["created_at"]) if row.get("created_at") else None,
            updated_at=datetime.fromisoformat(row["updated_at"]) if row.get("updated_at") else None,
        )

    def update_campaign_status(self, campaign_id: int, status: str) -> bool:
        """Update campaign status (active, paused, ended)."""
        db = self._get_db()
        db.execute(
            """
            UPDATE ad_campaigns
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (status, campaign_id),
        )
        db.commit()
        return db.total_changes > 0

    def add_click_credits(self, campaign_id: int, amount: float) -> bool:
        """
        Add click credits to a campaign.

        Simple meter charge: $5 per 1,000 clicks.
        """
        click_credits_to_add = int((amount / self.CPM_RATE) * 1000)

        db = self._get_db()
        db.execute(
            """
            UPDATE ad_campaigns
            SET click_credits = click_credits + ?,
                budget_amount = budget_amount + ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (click_credits_to_add, amount, campaign_id),
        )
        db.commit()
        return db.total_changes > 0

    def get_campaign_stats(self, campaign_id: int) -> dict[str, Any]:
        """Get campaign statistics."""
        db = self._get_db()

        # Get impressions count
        impressions = db.execute(
            "SELECT COUNT(*) as count FROM ad_impressions WHERE campaign_id = ?",
            (campaign_id,),
        ).fetchone()["count"]

        # Get clicks count
        clicks = db.execute(
            "SELECT COUNT(*) as count FROM ad_clicks WHERE campaign_id = ?",
            (campaign_id,),
        ).fetchone()["count"]

        # Get billable clicks and total cost
        billable = db.execute(
            """
            SELECT COUNT(*) as count, SUM(cost) as total_cost
            FROM ad_clicks
            WHERE campaign_id = ? AND billable = 1
            """,
            (campaign_id,),
        ).fetchone()

        return {
            "impressions": impressions,
            "clicks": clicks,
            "billable_clicks": billable["count"] or 0,
            "total_cost": billable["total_cost"] or 0.0,
        }

    # ==================== Creative Management ====================

    def create_creative(
        self,
        campaign_id: int,
        name: str,
        headline: str,
        landing_url: str,
        image_url: str = None,
        body_copy: str = None,
        cta_text: str = "Learn More",
    ) -> Optional[AdCreative]:
        """Create a new ad creative."""
        now = datetime.now()

        creative = AdCreative(
            id=0,
            campaign_id=campaign_id,
            name=name,
            image_url=image_url,
            headline=headline,
            body_copy=body_copy,
            cta_text=cta_text,
            landing_url=landing_url,
            status="active",
            created_at=now,
            updated_at=now,
        )

        try:
            db = self._get_db()
            cursor = db.execute(
                """
                INSERT INTO ad_creatives (
                    campaign_id, name, image_url, headline, body_copy,
                    cta_text, landing_url, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    campaign_id,
                    name,
                    image_url,
                    headline,
                    body_copy,
                    cta_text,
                    landing_url,
                    "active",
                    now,
                    now,
                ),
            )
            creative.id = cursor.lastrowid
            db.commit()
            logger.info(f"Created ad creative {creative.id} for campaign {campaign_id}")
            return creative
        except Exception as e:
            logger.error(f"Failed to create creative: {e}")
            return None

    def get_creatives(self, campaign_id: int, status: str = None) -> list[AdCreative]:
        """Get all creatives for a campaign."""
        db = self._get_db()

        if status:
            rows = db.execute(
                """
                SELECT * FROM ad_creatives
                WHERE campaign_id = ? AND status = ?
                ORDER BY impressions ASC
                """,
                (campaign_id, status),
            ).fetchall()
        else:
            rows = db.execute(
                """
                SELECT * FROM ad_creatives
                WHERE campaign_id = ?
                ORDER BY impressions ASC
                """,
                (campaign_id,),
            ).fetchall()

        return [self._row_to_creative(row) for row in rows]

    def _row_to_creative(self, row) -> AdCreative:
        """Convert database row to AdCreative."""
        return AdCreative(
            id=row["id"],
            campaign_id=row["campaign_id"],
            name=row["name"],
            image_url=row.get("image_url"),
            headline=row["headline"],
            body_copy=row.get("body_copy"),
            cta_text=row.get("cta_text", "Learn More"),
            landing_url=row["landing_url"],
            status=row["status"],
            impressions=row["impressions"],
            clicks=row["clicks"],
            created_at=datetime.fromisoformat(row["created_at"]) if row.get("created_at") else None,
            updated_at=datetime.fromisoformat(row["updated_at"]) if row.get("updated_at") else None,
        )

    def get_next_creative(self, campaign_id: int) -> Optional[AdCreative]:
        """Get the next creative to serve (lowest impressions first)."""
        db = self._get_db()
        row = db.execute(
            """
            SELECT * FROM ad_creatives
            WHERE campaign_id = ? AND status = 'active'
            ORDER BY impressions ASC
            LIMIT 1
            """,
            (campaign_id,),
        ).fetchone()

        if not row:
            return None

        return self._row_to_creative(row)

    def update_creative_status(self, creative_id: int, status: str) -> bool:
        """Update creative status."""
        db = self._get_db()
        db.execute(
            """
            UPDATE ad_creatives
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (status, creative_id),
        )
        db.commit()
        return db.total_changes > 0

    # ==================== Impression & Click Tracking ====================

    def record_impression(
        self,
        creative_id: int,
        campaign_id: int,
        business_id: str,
        placement: str = None,
        user_id: str = None,
        session_id: str = None,
    ) -> bool:
        """Record an ad impression."""
        now = time.time()

        db = self._get_db()

        # Log impression
        db.execute(
            """
            INSERT INTO ad_impressions (
                creative_id, campaign_id, business_id, placement,
                user_id, session_id, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (creative_id, campaign_id, business_id, placement, user_id, session_id, now),
        )

        # Update creative impressions
        db.execute(
            """
            UPDATE ad_creatives
            SET impressions = impressions + 1
            WHERE id = ?
            """,
            (creative_id,),
        )

        db.commit()
        return True

    def record_click(
        self,
        creative_id: int,
        campaign_id: int,
        business_id: str,
        user_id: str = None,
        request=None,
    ) -> tuple[bool, str, Optional[AdClick]]:
        """
        Record click with fraud protection.

        Returns:
            (is_billable, message, click_record)
            - True, "Click recorded", AdClick(billable=True) = billable click
            - False, "Duplicate click", AdClick(billable=False) = filtered
        """
        # Get fingerprint (IP + User Agent)
        ip = request.remote_addr if request else "0.0.0.0"
        user_agent = request.headers.get("User-Agent", "") if request else ""
        fingerprint_hash = self._hash_fingerprint(ip, user_agent)

        now = time.time()
        cost = self._calculate_click_cost()

        db = self._get_db()

        # Check for duplicate within 24h window
        last_click = db.execute(
            """
            SELECT timestamp FROM ad_clicks
            WHERE fingerprint_hash = ? AND campaign_id = ?
            AND timestamp > ?
            ORDER BY timestamp DESC
            LIMIT 1
            """,
            (fingerprint_hash, campaign_id, now - self.FRAUD_WINDOW),
        ).fetchone()

        if last_click:
            # Duplicate click - log but mark as non-billable
            click = AdClick(
                id=0,
                creative_id=creative_id,
                campaign_id=campaign_id,
                business_id=business_id,
                user_id=user_id,
                fingerprint_hash=fingerprint_hash,
                billable=False,
                rejection_reason="Duplicate click (24h window)",
                cost=0.0,
                timestamp=now,
            )
            self._log_click(click)
            logger.debug(f"Duplicate click filtered: campaign {campaign_id}")
            return False, "Duplicate click (24h window)", click

        # Check if campaign has credits or is in first month free
        campaign = self.get_campaign(campaign_id)
        if not campaign:
            return False, "Campaign not found", None

        is_free_click = self._is_first_month_free(campaign)
        has_credits = campaign.click_credits > 0

        if not is_free_click and not has_credits:
            # No credits and not in free period - log but don't bill
            click = AdClick(
                id=0,
                creative_id=creative_id,
                campaign_id=campaign_id,
                business_id=business_id,
                user_id=user_id,
                fingerprint_hash=fingerprint_hash,
                billable=False,
                rejection_reason="No click credits remaining",
                cost=0.0,
                timestamp=now,
            )
            self._log_click(click)
            logger.warning(f"Click rejected: campaign {campaign_id} has no credits")
            return False, "No click credits remaining", click

        # Valid billable click
        click = AdClick(
            id=0,
            creative_id=creative_id,
            campaign_id=campaign_id,
            business_id=business_id,
            user_id=user_id,
            fingerprint_hash=fingerprint_hash,
            billable=True,
            rejection_reason=None,
            cost=cost if not is_free_click else 0.0,
            timestamp=now,
        )
        self._log_click(click)

        # Update creative clicks
        db.execute(
            """
            UPDATE ad_creatives
            SET clicks = clicks + 1
            WHERE id = ?
            """,
            (creative_id,),
        )

        # Deduct credits if not free
        if not is_free_click:
            db.execute(
                """
                UPDATE ad_campaigns
                SET click_credits = click_credits - 1,
                    spent_amount = spent_amount + ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (cost, campaign_id),
            )

        db.commit()

        logger.info(f"Click recorded: campaign {campaign_id} (free: {is_free_click})")
        return True, "Click recorded", click

    def _log_click(self, click: AdClick):
        """Log click to database."""
        db = self._get_db()
        db.execute(
            """
            INSERT INTO ad_clicks (
                creative_id, campaign_id, business_id, user_id,
                fingerprint_hash, billable, rejection_reason, cost, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                click.creative_id,
                click.campaign_id,
                click.business_id,
                click.user_id,
                click.fingerprint_hash,
                1 if click.billable else 0,
                click.rejection_reason,
                click.cost,
                click.timestamp,
            ),
        )
        db.commit()

    # ==================== Ad Serving ====================

    def get_featured_ads(self, limit: int = 6, placement: str = None) -> list[dict[str, Any]]:
        """
        Get featured ads for display.

        Returns active ads from businesses with good standing,
        prioritizing those with remaining credits or in first month free.
        """
        db = self._get_db()

        # Get active campaigns with remaining credits or in first month free
        rows = db.execute(
            """
            SELECT
                c.id as campaign_id,
                c.business_id,
                c.name as campaign_name,
                c.click_credits,
                c.first_month_free,
                c.first_month_end,
                b.name as business_name,
                b.website,
                b.slug as business_slug,
                cr.id as creative_id,
                cr.headline,
                cr.body_copy,
                cr.cta_text,
                cr.landing_url,
                cr.image_url,
                cr.impressions,
                cr.clicks
            FROM ad_campaigns c
            JOIN businesses b ON c.business_id = b.id
            JOIN ad_creatives cr ON cr.campaign_id = c.id
            WHERE c.status = 'active'
                AND cr.status = 'active'
                AND (c.click_credits > 0 OR c.first_month_free = 1)
            ORDER BY
                c.first_month_free DESC,
                c.click_credits DESC,
                cr.impressions ASC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

        ads = []
        for row in rows:
            ads.append(
                {
                    "campaign_id": row["campaign_id"],
                    "business_id": row["business_id"],
                    "business_name": row["business_name"],
                    "business_slug": row["business_slug"],
                    "business_website": row["website"],
                    "campaign_name": row["campaign_name"],
                    "creative_id": row["creative_id"],
                    "headline": row["headline"],
                    "body_copy": row["body_copy"],
                    "cta_text": row["cta_text"],
                    "landing_url": row["landing_url"],
                    "image_url": row["image_url"],
                    "first_month_free": bool(row["first_month_free"]),
                }
            )

        return ads

    def get_ads_for_business_slug(self, business_slug: str, limit: int = 3) -> list[dict[str, Any]]:
        """Get ads to display on a business profile page (competitors)."""
        db = self._get_db()

        # Get ads from same category (excluding the current business)
        rows = db.execute(
            """
            SELECT
                c.id as campaign_id,
                c.business_id,
                b.name as business_name,
                b.website,
                b.slug as business_slug,
                cr.headline,
                cr.landing_url,
                cr.image_url
            FROM ad_campaigns c
            JOIN businesses b ON c.business_id = b.id
            JOIN ad_creatives cr ON cr.campaign_id = c.id
            WHERE c.status = 'active'
                AND cr.status = 'active'
                AND b.slug != ?
                AND (c.click_credits > 0 OR c.first_month_free = 1)
            ORDER BY RANDOM()
            LIMIT ?
            """,
            (business_slug, limit),
        ).fetchall()

        ads = []
        for row in rows:
            ads.append(
                {
                    "campaign_id": row["campaign_id"],
                    "business_id": row["business_id"],
                    "business_name": row["business_name"],
                    "business_slug": row["business_slug"],
                    "business_website": row["website"],
                    "headline": row["headline"],
                    "landing_url": row["landing_url"],
                    "image_url": row["image_url"],
                }
            )

        return ads


# Singleton instance
_shopping_service: Optional[ShoppingService] = None


def get_shopping_service() -> ShoppingService:
    """Get or create shopping service singleton."""
    global _shopping_service
    if _shopping_service is None:
        _shopping_service = ShoppingService()
    return _shopping_service
