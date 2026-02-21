"""
Ad Builder Service - The People's Ad Tool

A powerful, accessible advertising creation tool for everyone.
Free for basic use, with optional Pro features for power users.

Core Principles:
- No account required for basic ad creation
- Professional templates for all formats (social, print, video, display)
- Smart resizing (one design → all formats)
- AI-assisted features (copywriting, design suggestions)
- Community-first monetization (never gate essential features)

Features:
- Guest sessions (7-day expiry)
- Account-based saving and analytics
- Template library (official + community)
- Asset management (upload + stock integration)
- Brand kits (colors, fonts, logos)
- Multi-format export (PNG, JPG, PDF, SVG, MP4)
- A/B testing (Pro)
- Analytics (Pro)
"""

from __future__ import annotations

import logging
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)


# =============================================================================
# Data Classes
# =============================================================================


class AdDesign:
    """An ad design in the system."""

    def __init__(
        self,
        id: str,
        name: str,
        design_data: dict[str, Any],
        user_id: Optional[str] = None,
        guest_session_id: Optional[str] = None,
        template_id: Optional[str] = None,
        brand_kit: Optional[dict[str, Any]] = None,
        format_type: str = "custom",
        width: int = 1080,
        height: int = 1080,
        status: str = "draft",
        is_public: bool = False,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        self.id = id
        self.name = name
        self.design_data = design_data
        self.user_id = user_id
        self.guest_session_id = guest_session_id
        self.template_id = template_id
        self.brand_kit = brand_kit or {}
        self.format_type = format_type
        self.width = width
        self.height = height
        self.status = status
        self.is_public = is_public
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "design_data": self.design_data,
            "user_id": self.user_id,
            "guest_session_id": self.guest_session_id,
            "template_id": self.template_id,
            "brand_kit": self.brand_kit,
            "format_type": self.format_type,
            "width": self.width,
            "height": self.height,
            "status": self.status,
            "is_public": self.is_public,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AdDesign:
        return cls(
            id=data["id"],
            name=data["name"],
            design_data=data["design_data"],
            user_id=data.get("user_id"),
            guest_session_id=data.get("guest_session_id"),
            template_id=data.get("template_id"),
            brand_kit=data.get("brand_kit"),
            format_type=data.get("format_type", "custom"),
            width=data.get("width", 1080),
            height=data.get("height", 1080),
            status=data.get("status", "draft"),
            is_public=data.get("is_public", False),
            created_at=(
                datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None
            ),
            updated_at=(
                datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None
            ),
        )


class AdTemplate:
    """An ad template in the library."""

    def __init__(
        self,
        id: str,
        name: str,
        description: str,
        category: str,
        format_type: str,
        template_data: dict[str, Any],
        thumbnail_url: Optional[str] = None,
        tags: Optional[list[str]] = None,
        difficulty: str = "easy",
        estimated_time: int = 5,
        is_official: bool = True,
        author_id: Optional[str] = None,
        download_count: int = 0,
        favorite_count: int = 0,
        status: str = "active",
        created_at: Optional[datetime] = None,
    ):
        self.id = id
        self.name = name
        self.description = description
        self.category = category
        self.format_type = format_type
        self.template_data = template_data
        self.thumbnail_url = thumbnail_url
        self.tags = tags or []
        self.difficulty = difficulty
        self.estimated_time = estimated_time
        self.is_official = is_official
        self.author_id = author_id
        self.download_count = download_count
        self.favorite_count = favorite_count
        self.status = status
        self.created_at = created_at or datetime.now(timezone.utc)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "format_type": self.format_type,
            "template_data": self.template_data,
            "thumbnail_url": self.thumbnail_url,
            "tags": self.tags,
            "difficulty": self.difficulty,
            "estimated_time": self.estimated_time,
            "is_official": self.is_official,
            "author_id": self.author_id,
            "download_count": self.download_count,
            "favorite_count": self.favorite_count,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class BrandKit:
    """A brand kit for consistent branding."""

    def __init__(
        self,
        id: str,
        user_id: str,
        name: str,
        primary_color: str = "#3B82F6",
        secondary_color: str = "#1E40AF",
        accent_color: str = "#10B981",
        text_color: str = "#1F2937",
        heading_font: str = "Inter",
        body_font: str = "Inter",
        logo_url: Optional[str] = None,
        logo_square_url: Optional[str] = None,
        brand_voice: Optional[str] = None,
        is_default: bool = False,
        created_at: Optional[datetime] = None,
    ):
        self.id = id
        self.user_id = user_id
        self.name = name
        self.primary_color = primary_color
        self.secondary_color = secondary_color
        self.accent_color = accent_color
        self.text_color = text_color
        self.heading_font = heading_font
        self.body_font = body_font
        self.logo_url = logo_url
        self.logo_square_url = logo_square_url
        self.brand_voice = brand_voice
        self.is_default = is_default
        self.created_at = created_at or datetime.now(timezone.utc)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "primary_color": self.primary_color,
            "secondary_color": self.secondary_color,
            "accent_color": self.accent_color,
            "text_color": self.text_color,
            "heading_font": self.heading_font,
            "body_font": self.body_font,
            "logo_url": self.logo_url,
            "logo_square_url": self.logo_square_url,
            "brand_voice": self.brand_voice,
            "is_default": self.is_default,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# =============================================================================
# Ad Builder Service
# =============================================================================


class AdBuilderService:
    """
    Ad Builder Service - Core business logic.

    Handles:
    - Design CRUD (with guest session support)
    - Template management
    - Asset management
    - Brand kits
    - Export generation
    - Smart resizing
    """

    # Predefined format sizes
    FORMAT_SIZES = {
        # Social Media
        "instagram_post": (1080, 1080),
        "instagram_story": (1080, 1920),
        "instagram_reel": (1080, 1920),
        "facebook_post": (1200, 630),
        "facebook_story": (1080, 1920),
        "facebook_cover": (820, 312),
        "twitter_post": (1200, 675),
        "twitter_header": (1500, 500),
        "linkedin_post": (1200, 627),
        "linkedin_cover": (1584, 396),
        "pinterest_pin": (1000, 1500),
        "tiktok": (1080, 1920),
        # Digital Ads
        "google_display_square": (250, 250),
        "google_display_small": (200, 200),
        "google_display_medium": (300, 250),
        "google_display_large": (336, 280),
        "google_display_leaderboard": (728, 90),
        "google_display_banner": (468, 60),
        "google_display_skyscraper": (120, 600),
        "youtube_banner": (2560, 1440),
        "youtube_thumbnail": (1280, 720),
        # Print
        "flyer_a4": (2480, 3508),  # 300 DPI
        "flyer_letter": (2550, 3300),  # 300 DPI
        "business_card": (1050, 600),  # 300 DPI
        "postcard_4x6": (1200, 1800),  # 300 DPI
        "poster_a3": (3508, 4960),  # 300 DPI
        "poster_a2": (4960, 7016),  # 300 DPI
        # Video
        "youtube_short": (1080, 1920),
        "youtube_video": (1920, 1080),
        "facebook_video": (1920, 1080),
        "instagram_video": (1080, 1920),
    }

    # Format categories
    FORMAT_CATEGORIES = {
        "instagram_post": "social",
        "instagram_story": "social",
        "instagram_reel": "social",
        "facebook_post": "social",
        "facebook_story": "social",
        "facebook_cover": "social",
        "twitter_post": "social",
        "twitter_header": "social",
        "linkedin_post": "social",
        "linkedin_cover": "social",
        "pinterest_pin": "social",
        "tiktok": "social",
        "google_display_square": "display",
        "google_display_small": "display",
        "google_display_medium": "display",
        "google_display_large": "display",
        "google_display_leaderboard": "display",
        "google_display_banner": "display",
        "google_display_skyscraper": "display",
        "youtube_banner": "video",
        "youtube_thumbnail": "video",
        "flyer_a4": "print",
        "flyer_letter": "print",
        "business_card": "print",
        "postcard_4x6": "print",
        "poster_a3": "print",
        "poster_a2": "print",
        "youtube_short": "video",
        "youtube_video": "video",
        "facebook_video": "video",
        "instagram_video": "video",
    }

    def __init__(self):
        """Initialize the Ad Builder service."""
        self._db = None
        logger.info("Ad Builder Service initialized")

    def _get_db(self):
        """Get database connection."""
        if self._db is None:
            from db import get_db

            self._db = get_db()
        return self._db

    # =========================================================================
    # Guest Session Management
    # =========================================================================

    def create_guest_session(self) -> str:
        """
        Create a new guest session for non-authenticated users.

        Returns:
            Session ID (64-character hex string)
        """
        session_id = secrets.token_hex(32)
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)

        db = self._get_db()
        db.execute(
            """
            INSERT INTO guest_ad_sessions (session_id, expires_at)
            VALUES (?, ?)
        """,
            (session_id, expires_at),
        )
        db.commit()

        logger.info(f"Created guest session: {session_id[:16]}...")
        return session_id

    def get_guest_session(self, session_id: str) -> Optional[dict[str, Any]]:
        """
        Get guest session data.

        Args:
            session_id: Session ID

        Returns:
            Session data or None if not found/expired
        """
        db = self._get_db()
        row = db.execute(
            """
            SELECT session_id, design_data, created_at, expires_at, last_accessed
            FROM guest_ad_sessions
            WHERE session_id = ? AND expires_at > ?
        """,
            (session_id, datetime.now(timezone.utc)),
        ).fetchone()

        if row:
            # Update last accessed
            db.execute(
                """
                UPDATE guest_ad_sessions
                SET last_accessed = ?
                WHERE session_id = ?
            """,
                (datetime.now(timezone.utc), session_id),
            )
            db.commit()

            return {
                "session_id": row["session_id"],
                "design_data": row["design_data"],
                "created_at": row["created_at"],
                "expires_at": row["expires_at"],
                "last_accessed": row["last_accessed"],
            }

        return None

    def save_guest_design(self, session_id: str, design_data: dict[str, Any]) -> bool:
        """
        Save design data to guest session.

        Args:
            session_id: Session ID
            design_data: Design JSON data

        Returns:
            True if successful
        """
        db = self._get_db()
        try:
            import json

            db.execute(
                """
                UPDATE guest_ad_sessions
                SET design_data = ?, last_accessed = ?
                WHERE session_id = ? AND expires_at > ?
            """,
                (
                    json.dumps(design_data),
                    datetime.now(timezone.utc),
                    session_id,
                    datetime.now(timezone.utc),
                ),
            )
            db.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to save guest design: {e}")
            return False

    # =========================================================================
    # Design Management
    # =========================================================================

    def create_design(
        self,
        name: str,
        design_data: dict[str, Any],
        user_id: Optional[str] = None,
        guest_session_id: Optional[str] = None,
        template_id: Optional[str] = None,
        format_type: str = "custom",
        width: Optional[int] = None,
        height: Optional[int] = None,
    ) -> Optional[AdDesign]:
        """
        Create a new ad design.

        Args:
            name: Design name
            design_data: Canvas state (layers, elements, etc.)
            user_id: User ID (optional, None for guest)
            guest_session_id: Guest session ID (if guest)
            template_id: Template ID (if created from template)
            format_type: Format type (instagram_post, flyer_a4, etc.)
            width: Custom width (uses format default if not specified)
            height: Custom height (uses format default if not specified)

        Returns:
            AdDesign object or None if failed
        """
        # Get dimensions from format if not specified
        if format_type in self.FORMAT_SIZES and (width is None or height is None):
            default_width, default_height = self.FORMAT_SIZES[format_type]
            if width is None:
                width = default_width
            if height is None:
                height = default_height

        design = AdDesign(
            id=str(uuid.uuid4()),
            name=name,
            design_data=design_data,
            user_id=user_id,
            guest_session_id=guest_session_id,
            template_id=template_id,
            format_type=format_type,
            width=width or 1080,
            height=height or 1080,
        )

        db = self._get_db()
        try:
            import json

            db.execute(
                """
                INSERT INTO ad_designs (
                    id, name, design_data, user_id, guest_session_id,
                    template_id, format_type, width, height, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'draft')
            """,
                (
                    design.id,
                    design.name,
                    json.dumps(design.design_data),
                    design.user_id,
                    design.guest_session_id,
                    design.template_id,
                    design.format_type,
                    design.width,
                    design.height,
                ),
            )
            db.commit()
            logger.info(f"Created design: {design.id} ({design.name})")
            return design
        except Exception as e:
            logger.error(f"Failed to create design: {e}")
            return None

    def get_design(self, design_id: str) -> Optional[AdDesign]:
        """
        Get a design by ID.

        Args:
            design_id: Design ID

        Returns:
            AdDesign object or None
        """
        db = self._get_db()
        row = db.execute(
            """
            SELECT * FROM ad_designs WHERE id = ?
        """,
            (design_id,),
        ).fetchone()

        if row:
            import json

            design_data = row["design_data"]
            if isinstance(design_data, str):
                design_data = json.loads(design_data)

            return AdDesign(
                id=row["id"],
                name=row["name"],
                design_data=design_data,
                user_id=row["user_id"],
                guest_session_id=row["guest_session_id"],
                template_id=row["template_id"],
                format_type=row["format_type"],
                width=row["width"],
                height=row["height"],
                status=row["status"],
                is_public=row["is_public"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )

        return None

    def update_design(self, design_id: str, updates: dict[str, Any]) -> bool:
        """
        Update a design.

        Args:
            design_id: Design ID
            updates: Fields to update (name, design_data, status, etc.)

        Returns:
            True if successful
        """
        db = self._get_db()
        try:
            import json

            # Build update query dynamically
            set_clauses = []
            values = []

            for field, value in updates.items():
                if field in ["design_data", "brand_kit"] and isinstance(value, dict):
                    set_clauses.append(f"{field} = ?")
                    values.append(json.dumps(value))
                elif field in ["name", "format_type", "status"]:
                    set_clauses.append(f"{field} = ?")
                    values.append(value)
                elif field in ["width", "height", "is_public"]:
                    set_clauses.append(f"{field} = ?")
                    values.append(value)

            if not set_clauses:
                return False

            set_clauses.append("updated_at = ?")
            values.append(datetime.now(timezone.utc))
            values.append(design_id)

            query = f"""
                UPDATE ad_designs
                SET {", ".join(set_clauses)}
                WHERE id = ?
            """

            db.execute(query, values)
            db.commit()
            logger.info(f"Updated design: {design_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to update design: {e}")
            return False

    def delete_design(self, design_id: str) -> bool:
        """
        Delete a design.

        Args:
            design_id: Design ID

        Returns:
            True if successful
        """
        db = self._get_db()
        try:
            db.execute("DELETE FROM ad_designs WHERE id = ?", (design_id,))
            db.commit()
            logger.info(f"Deleted design: {design_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete design: {e}")
            return False

    def get_user_designs(
        self, user_id: str, status: Optional[str] = None, limit: int = 50
    ) -> list[AdDesign]:
        """
        Get all designs for a user.

        Args:
            user_id: User ID
            status: Filter by status (optional)
            limit: Maximum results

        Returns:
            List of AdDesign objects
        """
        db = self._get_db()

        query = """
            SELECT * FROM ad_designs
            WHERE user_id = ?
        """
        params: list[Any] = [user_id]

        if status:
            query += " AND status = ?"
            params.append(status)

        query += " ORDER BY updated_at DESC LIMIT ?"
        params.append(limit)

        rows = db.execute(query, params).fetchall()

        designs = []
        for row in rows:
            import json

            design_data = row["design_data"]
            if isinstance(design_data, str):
                design_data = json.loads(design_data)

            designs.append(
                AdDesign(
                    id=row["id"],
                    name=row["name"],
                    design_data=design_data,
                    user_id=row["user_id"],
                    format_type=row["format_type"],
                    width=row["width"],
                    height=row["height"],
                    status=row["status"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
            )

        return designs

    # =========================================================================
    # Template Management
    # =========================================================================

    def get_templates(
        self,
        category: Optional[str] = None,
        format_type: Optional[str] = None,
        tags: Optional[list[str]] = None,
        limit: int = 50,
    ) -> list[AdTemplate]:
        """
        Get templates with optional filters.

        Args:
            category: Filter by category (social, print, video, display)
            format_type: Filter by specific format (instagram_post, etc.)
            tags: Filter by tags (optional)
            limit: Maximum results

        Returns:
            List of AdTemplate objects
        """
        db = self._get_db()

        query = """
            SELECT * FROM ad_templates
            WHERE status = 'active'
        """
        params: list[Any] = []

        if category:
            query += " AND category = ?"
            params.append(category)

        if format_type:
            query += " AND format_type = ?"
            params.append(format_type)

        query += " ORDER BY download_count DESC, favorite_count DESC LIMIT ?"
        params.append(limit)

        rows = db.execute(query, params).fetchall()

        templates = []
        for row in rows:
            import json

            template_data = row["template_data"]
            if isinstance(template_data, str):
                template_data = json.loads(template_data)

            templates.append(
                AdTemplate(
                    id=row["id"],
                    name=row["name"],
                    description=row["description"],
                    category=row["category"],
                    format_type=row["format_type"],
                    template_data=template_data,
                    thumbnail_url=row["thumbnail_url"],
                    tags=row["tags"] if row["tags"] else [],
                    difficulty=row["difficulty"],
                    estimated_time=row["estimated_time"],
                    is_official=row["is_official"],
                    created_at=row["created_at"],
                )
            )

        return templates

    def get_template(self, template_id: str) -> Optional[AdTemplate]:
        """
        Get a template by ID.

        Args:
            template_id: Template ID

        Returns:
            AdTemplate object or None
        """
        db = self._get_db()
        row = db.execute(
            """
            SELECT * FROM ad_templates WHERE id = ?
        """,
            (template_id,),
        ).fetchone()

        if row:
            import json

            template_data = row["template_data"]
            if isinstance(template_data, str):
                template_data = json.loads(template_data)

            return AdTemplate(
                id=row["id"],
                name=row["name"],
                description=row["description"],
                category=row["category"],
                format_type=row["format_type"],
                template_data=template_data,
                thumbnail_url=row["thumbnail_url"],
                tags=row["tags"] if row["tags"] else [],
                difficulty=row["difficulty"],
                estimated_time=row["estimated_time"],
                is_official=row["is_official"],
                created_at=row["created_at"],
            )

        return None

    def increment_template_download(self, template_id: str) -> bool:
        """
        Increment template download count.

        Args:
            template_id: Template ID

        Returns:
            True if successful
        """
        db = self._get_db()
        try:
            db.execute(
                """
                UPDATE ad_templates
                SET download_count = download_count + 1
                WHERE id = ?
            """,
                (template_id,),
            )
            db.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to increment template download: {e}")
            return False

    # =========================================================================
    # Brand Kit Management
    # =========================================================================

    def create_brand_kit(self, user_id: str, data: dict[str, Any]) -> Optional[BrandKit]:
        """
        Create a new brand kit.

        Args:
            user_id: User ID
            data: Brand kit data

        Returns:
            BrandKit object or None
        """
        brand_kit = BrandKit(
            id=str(uuid.uuid4()),
            user_id=user_id,
            name=data.get("name", "My Brand"),
            primary_color=data.get("primary_color", "#3B82F6"),
            secondary_color=data.get("secondary_color", "#1E40AF"),
            accent_color=data.get("accent_color", "#10B981"),
            text_color=data.get("text_color", "#1F2937"),
            heading_font=data.get("heading_font", "Inter"),
            body_font=data.get("body_font", "Inter"),
            logo_url=data.get("logo_url"),
            logo_square_url=data.get("logo_square_url"),
            brand_voice=data.get("brand_voice"),
            is_default=data.get("is_default", False),
        )

        db = self._get_db()
        try:
            db.execute(
                """
                INSERT INTO brand_kits (
                    id, user_id, name, primary_color, secondary_color,
                    accent_color, text_color, heading_font, body_font,
                    logo_url, logo_square_url, brand_voice, is_default
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    brand_kit.id,
                    brand_kit.user_id,
                    brand_kit.name,
                    brand_kit.primary_color,
                    brand_kit.secondary_color,
                    brand_kit.accent_color,
                    brand_kit.text_color,
                    brand_kit.heading_font,
                    brand_kit.body_font,
                    brand_kit.logo_url,
                    brand_kit.logo_square_url,
                    brand_kit.brand_voice,
                    brand_kit.is_default,
                ),
            )
            db.commit()
            logger.info(f"Created brand kit: {brand_kit.id} ({brand_kit.name})")
            return brand_kit
        except Exception as e:
            logger.error(f"Failed to create brand kit: {e}")
            return None

    def get_user_brand_kits(self, user_id: str) -> list[BrandKit]:
        """
        Get all brand kits for a user.

        Args:
            user_id: User ID

        Returns:
            List of BrandKit objects
        """
        db = self._get_db()
        rows = db.execute(
            """
            SELECT * FROM brand_kits
            WHERE user_id = ?
            ORDER BY is_default DESC, created_at DESC
        """,
            (user_id,),
        ).fetchall()

        brand_kits = []
        for row in rows:
            brand_kits.append(
                BrandKit(
                    id=row["id"],
                    user_id=row["user_id"],
                    name=row["name"],
                    primary_color=row["primary_color"],
                    secondary_color=row["secondary_color"],
                    accent_color=row["accent_color"],
                    text_color=row["text_color"],
                    heading_font=row["heading_font"],
                    body_font=row["body_font"],
                    logo_url=row["logo_url"],
                    logo_square_url=row["logo_square_url"],
                    brand_voice=row["brand_voice"],
                    is_default=row["is_default"],
                    created_at=row["created_at"],
                )
            )

        return brand_kits

    def update_brand_kit(self, brand_kit_id: str, user_id: str, updates: dict[str, Any]) -> bool:
        """
        Update a brand kit.

        Args:
            brand_kit_id: Brand kit ID
            user_id: User ID (for ownership check)
            updates: Fields to update

        Returns:
            True if successful
        """
        db = self._get_db()
        try:
            set_clauses = []
            values = []

            for field, value in updates.items():
                if field in [
                    "name",
                    "primary_color",
                    "secondary_color",
                    "accent_color",
                    "text_color",
                    "heading_font",
                    "body_font",
                    "logo_url",
                    "logo_square_url",
                    "brand_voice",
                    "is_default",
                ]:
                    set_clauses.append(f"{field} = ?")
                    values.append(value)

            if not set_clauses:
                return False

            values.append(brand_kit_id)
            values.append(user_id)

            query = f"""
                UPDATE brand_kits
                SET {", ".join(set_clauses)}
                WHERE id = ? AND user_id = ?
            """

            db.execute(query, values)
            db.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to update brand kit: {e}")
            return False

    def delete_brand_kit(self, brand_kit_id: str, user_id: str) -> bool:
        """
        Delete a brand kit.

        Args:
            brand_kit_id: Brand kit ID
            user_id: User ID (for ownership check)

        Returns:
            True if successful
        """
        db = self._get_db()
        try:
            db.execute(
                """
                DELETE FROM brand_kits
                WHERE id = ? AND user_id = ?
            """,
                (brand_kit_id, user_id),
            )
            db.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to delete brand kit: {e}")
            return False

    # =========================================================================
    # Smart Resizing
    # =========================================================================

    def resize_design(self, design_id: str, target_format: str) -> Optional[AdDesign]:
        """
        Resize a design to a new format.

        Args:
            design_id: Source design ID
            target_format: Target format (instagram_post, flyer_a4, etc.)

        Returns:
            New AdDesign object or None
        """
        if target_format not in self.FORMAT_SIZES:
            logger.error(f"Unknown format: {target_format}")
            return None

        # Get source design
        design = self.get_design(design_id)
        if not design:
            logger.error(f"Design not found: {design_id}")
            return None

        # Get target dimensions
        target_width, target_height = self.FORMAT_SIZES[target_format]

        # Smart resize logic (simplified - would need more sophisticated algorithm)
        resized_data = design.design_data.copy()
        resized_data["width"] = target_width
        resized_data["height"] = target_height

        # Scale elements proportionally
        if "elements" in resized_data:
            scale_x = target_width / design.width
            scale_y = target_height / design.height

            for element in resized_data["elements"]:
                if "x" in element:
                    element["x"] = int(element["x"] * scale_x)
                if "y" in element:
                    element["y"] = int(element["y"] * scale_y)
                if "width" in element:
                    element["width"] = int(element["width"] * scale_x)
                if "height" in element:
                    element["height"] = int(element["height"] * scale_y)

        # Create new design
        new_design = self.create_design(
            name=f"{design.name} ({target_format})",
            design_data=resized_data,
            user_id=design.user_id,
            template_id=design.template_id,
            format_type=target_format,
            width=target_width,
            height=target_height,
        )

        logger.info(
            f"Resized design {design_id} to {target_format}: {new_design.id if new_design else 'FAILED'}"
        )
        return new_design

    # =========================================================================
    # Export Service
    # =========================================================================

    def export_design(
        self,
        design_id: str,
        format: str = "png",
        quality: int = 90,
        watermark: bool = False,
    ) -> Optional[bytes]:
        """
        Export design to specified format.

        Args:
            design_id: Design ID
            format: Export format (png, jpg, pdf, svg)
            quality: Quality (1-100 for jpg)
            watermark: Add SkyModderAI watermark

        Returns:
            Exported file bytes or None
        """
        design = self.get_design(design_id)
        if not design:
            logger.error(f"Design not found: {design_id}")
            return None

        # Export logic would use a library like:
        # - PNG/JPG: Pillow or cairosvg
        # - PDF: ReportLab or WeasyPrint
        # - SVG: Direct from canvas data
        # - MP4: FFmpeg (for video templates)

        # For now, return placeholder
        logger.info(f"Exporting design {design_id} to {format}")

        # TODO: Implement actual export
        # This would render the canvas data to the specified format

        return b""  # Placeholder


# =============================================================================
# Service Factory
# =============================================================================


def get_ad_builder_service() -> AdBuilderService:
    """Get Ad Builder service instance."""
    return AdBuilderService()
