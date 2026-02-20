"""
Community Repository - Data access layer for community features.

Handles database operations for community posts, comments, and votes.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from db import get_db

logger = logging.getLogger(__name__)


class CommunityRepository:
    """Repository for community-related database operations."""

    def __init__(self) -> None:
        """Initialize the community repository."""
        self._db = None

    def _get_db(self):
        """Get database connection."""
        if self._db is None:
            self._db = get_db()
        return self._db

    def get_posts(
        self,
        limit: int = 50,
        offset: int = 0,
        game: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get community posts with optional filtering.

        Args:
            limit: Maximum number of posts to return
            offset: Pagination offset
            game: Filter by game ID (optional)

        Returns:
            List of community posts
        """
        db = self._get_db()

        if game:
            query = """
                SELECT * FROM community_posts
                WHERE game_id = ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """
            params: tuple = (game, limit, offset)
        else:
            query = """
                SELECT * FROM community_posts
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """
            params = (limit, offset)

        cursor = db.execute(query, params)
        cursor.row_factory = sqlite3.Row
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_post_by_id(self, post_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a single post by ID.

        Args:
            post_id: Post ID

        Returns:
            Post dict if found, None otherwise
        """
        db = self._get_db()
        query = "SELECT * FROM community_posts WHERE id = ?"
        row = db.execute(query, (post_id,)).fetchone()

        if row:
            row.row_factory = sqlite3.Row
            return dict(row)
        return None

    def create_post(
        self,
        user_email: str,
        title: str,
        content: str,
        game_id: Optional[str] = None,
        tags: Optional[str] = None,
    ) -> Optional[int]:
        """
        Create a new community post.

        Args:
            user_email: Author's email
            title: Post title
            content: Post content
            game_id: Associated game ID (optional)
            tags: Comma-separated tags (optional)

        Returns:
            New post ID if successful, None otherwise
        """
        db = self._get_db()
        query = """
            INSERT INTO community_posts (user_email, title, content, game_id, tags)
            VALUES (?, ?, ?, ?, ?)
        """
        try:
            cursor = db.execute(query, (user_email, title, content, game_id, tags))
            db.commit()
            return cursor.lastrowid
        except Exception as e:
            logger.error(f"Failed to create post: {e}")
            return None

    def update_post(
        self,
        post_id: int,
        title: Optional[str] = None,
        content: Optional[str] = None,
        tags: Optional[str] = None,
    ) -> bool:
        """
        Update an existing post.

        Args:
            post_id: Post ID to update
            title: New title (optional)
            content: New content (optional)
            tags: New tags (optional)

        Returns:
            True if successful, False otherwise
        """
        db = self._get_db()

        updates = []
        params: list = []

        if title is not None:
            updates.append("title = ?")
            params.append(title)
        if content is not None:
            updates.append("content = ?")
            params.append(content)
        if tags is not None:
            updates.append("tags = ?")
            params.append(tags)

        if not updates:
            return False

        params.append(post_id)
        query = f"UPDATE community_posts SET {', '.join(updates)} WHERE id = ?"

        try:
            db.execute(query, params)
            db.commit()
            return db.total_changes > 0
        except Exception as e:
            logger.error(f"Failed to update post: {e}")
            return False

    def delete_post(self, post_id: int) -> bool:
        """
        Delete a post.

        Args:
            post_id: Post ID to delete

        Returns:
            True if deleted, False otherwise
        """
        db = self._get_db()
        query = "DELETE FROM community_posts WHERE id = ?"

        try:
            db.execute(query, (post_id,))
            db.commit()
            return db.total_changes > 0
        except Exception as e:
            logger.error(f"Failed to delete post: {e}")
            return False

    def get_comments(self, post_id: int, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get comments for a post.

        Args:
            post_id: Post ID
            limit: Maximum comments to return

        Returns:
            List of comments
        """
        db = self._get_db()
        query = """
            SELECT * FROM community_comments
            WHERE post_id = ?
            ORDER BY created_at ASC
            LIMIT ?
        """
        cursor = db.execute(query, (post_id, limit))
        cursor.row_factory = sqlite3.Row
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def add_comment(
        self,
        post_id: int,
        user_email: str,
        content: str,
        parent_id: Optional[int] = None,
    ) -> Optional[int]:
        """
        Add a comment to a post.

        Args:
            post_id: Post ID
            user_email: Author's email
            content: Comment content
            parent_id: Parent comment ID for replies (optional)

        Returns:
            New comment ID if successful, None otherwise
        """
        db = self._get_db()
        query = """
            INSERT INTO community_comments (post_id, user_email, content, parent_id)
            VALUES (?, ?, ?, ?)
        """
        try:
            cursor = db.execute(query, (post_id, user_email, content, parent_id))
            db.commit()
            return cursor.lastrowid
        except Exception as e:
            logger.error(f"Failed to add comment: {e}")
            return None

    def get_vote_count(self, post_id: int) -> int:
        """
        Get vote count for a post.

        Args:
            post_id: Post ID

        Returns:
            Vote count (upvotes - downvotes)
        """
        db = self._get_db()
        query = """
            SELECT COALESCE(SUM(vote_type), 0) as vote_count
            FROM community_votes
            WHERE post_id = ?
        """
        row = db.execute(query, (post_id,)).fetchone()
        return row[0] if row else 0

    def vote(
        self,
        post_id: int,
        user_email: str,
        vote_type: int,
    ) -> bool:
        """
        Vote on a post (1 for upvote, -1 for downvote).

        Args:
            post_id: Post ID
            user_email: Voter's email
            vote_type: 1 for upvote, -1 for downvote

        Returns:
            True if successful, False otherwise
        """
        db = self._get_db()

        # Check if user already voted
        existing = db.execute(
            "SELECT id FROM community_votes WHERE post_id = ? AND user_email = ?",
            (post_id, user_email),
        ).fetchone()

        try:
            if existing:
                # Update existing vote
                query = "UPDATE community_votes SET vote_type = ? WHERE post_id = ? AND user_email = ?"
                db.execute(query, (vote_type, post_id, user_email))
            else:
                # Insert new vote
                query = """
                    INSERT INTO community_votes (post_id, user_email, vote_type)
                    VALUES (?, ?, ?)
                """
                db.execute(query, (post_id, user_email, vote_type))

            db.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to vote: {e}")
            return False
