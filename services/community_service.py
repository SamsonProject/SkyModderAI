"""
SkyModderAI - Community Service

Handles community posts, replies, voting, and reports.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from db import (
    create_community_post,
    create_community_reply,
    create_community_report,
    get_community_posts,
    get_community_stats,
    vote_community_post,
)
from exceptions import ValidationError

logger = logging.getLogger(__name__)


class CommunityService:
    """Service for community operations."""

    def __init__(self, db_connection: Any) -> None:
        """
        Initialize community service.

        Args:
            db_connection: Database connection object
        """
        self.db = db_connection

    def create_post(
        self,
        email: str,
        content: str,
        tag: str = "general",
    ) -> int:
        """
        Create a new community post.

        Args:
            email: User email
            content: Post content
            tag: Post tag

        Returns:
            Post ID

        Raises:
            ValidationError: If validation fails
        """
        if not content or not content.strip():
            raise ValidationError("Post content is required")

        content = content.strip()
        if len(content) > 5000:
            raise ValidationError("Post content too long (max 5000 characters)")

        post_id = create_community_post(
            email=email,
            content=content,
            tag=tag,
        )

        logger.info(f"Community post created: {post_id} by {email}")

        return post_id

    def create_reply(
        self,
        post_id: int,
        email: str,
        content: str,
    ) -> int:
        """
        Create a reply to a post.

        Args:
            post_id: Post ID
            email: User email
            content: Reply content

        Returns:
            Reply ID

        Raises:
            ValidationError: If validation fails
        """
        if not content or not content.strip():
            raise ValidationError("Reply content is required")

        content = content.strip()
        if len(content) > 2000:
            raise ValidationError("Reply content too long (max 2000 characters)")

        reply_id = create_community_reply(
            post_id=post_id,
            email=email,
            content=content,
        )

        logger.info(f"Community reply created: {reply_id} by {email}")

        return reply_id

    def vote(
        self,
        post_id: int,
        email: str,
        vote: int,
    ) -> bool:
        """
        Vote on a post.

        Args:
            post_id: Post ID
            email: User email
            vote: Vote value (-1, 0, or 1)

        Returns:
            True if successful

        Raises:
            ValidationError: If vote invalid
        """
        if vote not in (-1, 0, 1):
            raise ValidationError("Vote must be -1, 0, or 1")

        vote_community_post(
            post_id=post_id,
            email=email,
            vote=vote,
        )

        return True

    def report(
        self,
        post_id: int,
        reporter_email: str,
        reason: str,
    ) -> int:
        """
        Report a post.

        Args:
            post_id: Post ID
            reporter_email: Reporter email
            reason: Report reason

        Returns:
            Report ID

        Raises:
            ValidationError: If reason invalid
        """
        if not reason or not reason.strip():
            raise ValidationError("Report reason is required")

        report_id = create_community_report(
            post_id=post_id,
            reporter_email=reporter_email,
            reason=reason,
        )

        logger.info(f"Community post reported: {post_id} by {reporter_email}")

        return report_id

    def get_posts(
        self,
        limit: int = 50,
        tag: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get community posts.

        Args:
            limit: Max posts
            tag: Filter by tag

        Returns:
            List of posts
        """
        return get_community_posts(limit=limit, tag=tag)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get community statistics.

        Returns:
            Stats dictionary
        """
        return get_community_stats()
