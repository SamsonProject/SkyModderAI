"""
Community Builds Service - Manages user-submitted mod lists.

This service replaces hardcoded mod recommendations with community-driven builds.
All builds are transparently sourced and voted on by the community.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

from db import get_db

logger = logging.getLogger(__name__)


class CommunityBuildsService:
    """Community builds management service."""

    def get_builds(
        self,
        game: Optional[str] = None,
        playstyle: Optional[str] = None,
        performance_tier: Optional[str] = None,
        limit: int = 50,
        include_seed: bool = True,
    ) -> list[dict[str, Any]]:
        """
        Get community builds with optional filters.

        Args:
            game: Filter by game (skyrimse, fallout4, etc.)
            playstyle: Filter by playstyle tag (vanilla_plus, hardcore, etc.)
            performance_tier: Filter by performance tier (low, mid, high)
            limit: Maximum number of builds to return
            include_seed: Whether to include seeded builds (default True)

        Returns:
            List of community builds with vote counts
        """
        try:
            db = get_db()

            # Build query
            query = """
                SELECT
                    id, game, name, description, author, source, source_url,
                    wiki_url, mod_count, playstyle_tags, performance_tier,
                    upvotes, downvotes, is_seed, seed_note, created_at, updated_at
                FROM community_builds
                WHERE 1=1
            """
            params = []

            if game:
                query += " AND game = ?"
                params.append(game)

            if playstyle:
                # Search within JSON tags
                query += " AND playstyle_tags LIKE ?"
                params.append(f"%{playstyle}%")

            if performance_tier:
                query += " AND performance_tier = ?"
                params.append(performance_tier)

            if not include_seed:
                query += " AND is_seed = 0"

            # Order by net votes (upvotes - downvotes), then by mod_count
            query += """
                ORDER BY (upvotes - downvotes) DESC, mod_count ASC
                LIMIT ?
            """
            params.append(limit)

            rows = db.execute(query, params).fetchall()

            builds = []
            for row in rows:
                build = dict(row)
                # Parse JSON tags
                if build.get("playstyle_tags"):
                    try:
                        build["playstyle_tags"] = json.loads(build["playstyle_tags"])
                    except (json.JSONDecodeError, TypeError):
                        build["playstyle_tags"] = []
                else:
                    build["playstyle_tags"] = []

                # Calculate net score
                build["net_votes"] = build.get("upvotes", 0) - build.get("downvotes", 0)

                builds.append(build)

            return builds

        except Exception as e:
            logger.error(f"Failed to get community builds: {e}")
            return []

    def get_build_by_id(self, build_id: int) -> Optional[dict[str, Any]]:
        """Get a specific build by ID."""
        try:
            db = get_db()
            row = db.execute(
                """
                    SELECT
                        id, game, name, description, author, source, source_url,
                        wiki_url, mod_count, playstyle_tags, performance_tier,
                        upvotes, downvotes, is_seed, seed_note, created_at, updated_at
                    FROM community_builds
                    WHERE id = ?
                """,
                (build_id,),
            ).fetchone()

            if row:
                build = dict(row)
                if build.get("playstyle_tags"):
                    try:
                        build["playstyle_tags"] = json.loads(build["playstyle_tags"])
                    except (json.JSONDecodeError, TypeError):
                        build["playstyle_tags"] = []
                build["net_votes"] = build.get("upvotes", 0) - build.get("downvotes", 0)
                return build
            return None

        except Exception as e:
            logger.error(f"Failed to get build: {e}")
            return None

    def submit_build(
        self,
        data: dict[str, Any],
        user_email: str,
    ) -> Optional[int]:
        """
        Submit a new community build.

        Args:
            data: Build data (game, name, description, mod_list, etc.)
            user_email: Email of submitting user

        Returns:
            Build ID if successful, None otherwise
        """
        try:
            db = get_db()

            # Validate required fields
            required = ["game", "name", "description", "mod_list"]
            for field in required:
                if field not in data or not data[field]:
                    logger.error(f"Missing required field: {field}")
                    return None

            # Parse playstyle tags
            playstyle_tags = data.get("playstyle_tags", [])
            if isinstance(playstyle_tags, list):
                playstyle_tags_json = json.dumps(playstyle_tags)
            else:
                playstyle_tags_json = "[]"

            # Insert build
            cursor = db.execute(
                """
                    INSERT INTO community_builds (
                        game, name, description, author, source, source_url,
                        wiki_url, mod_count, playstyle_tags, performance_tier,
                        is_seed, seed_note
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, NULL)
                """,
                (
                    data["game"],
                    data["name"],
                    data["description"],
                    data.get("author", "Anonymous"),
                    data.get("source", "Community"),
                    data.get("source_url"),
                    data.get("wiki_url"),
                    data.get("mod_count"),
                    playstyle_tags_json,
                    data.get("performance_tier", "mid"),
                ),
            )

            build_id = cursor.lastrowid
            db.commit()

            logger.info(f"Community build submitted: {build_id} by {user_email}")
            return build_id

        except Exception as e:
            logger.error(f"Failed to submit build: {e}")
            return None

    def vote(self, build_id: int, user_email: str, vote: int) -> bool:
        """
        Vote on a community build.

        Args:
            build_id: Build to vote on
            user_email: Email of voting user
            vote: 1 for upvote, -1 for downvote

        Returns:
            True if successful
        """
        try:
            db = get_db()

            # Check if build exists
            build = db.execute(
                "SELECT id FROM community_builds WHERE id = ?", (build_id,)
            ).fetchone()

            if not build:
                logger.error(f"Build not found: {build_id}")
                return False

            # Check if user already voted
            existing = db.execute(
                """
                    SELECT vote FROM community_build_votes
                    WHERE build_id = ? AND user_email = ?
                """,
                (build_id, user_email),
            ).fetchone()

            if existing:
                # Update existing vote
                if existing["vote"] == vote:
                    # Remove vote (toggle off)
                    db.execute(
                        """
                            DELETE FROM community_build_votes
                            WHERE build_id = ? AND user_email = ?
                        """,
                        (build_id, user_email),
                    )
                    # Adjust counts
                    if vote == 1:
                        db.execute(
                            "UPDATE community_builds SET upvotes = upvotes - 1 WHERE id = ?",
                            (build_id,),
                        )
                    else:
                        db.execute(
                            "UPDATE community_builds SET downvotes = downvotes - 1 WHERE id = ?",
                            (build_id,),
                        )
                else:
                    # Change vote
                    db.execute(
                        """
                            UPDATE community_build_votes
                            SET vote = ?, created_at = CURRENT_TIMESTAMP
                            WHERE build_id = ? AND user_email = ?
                        """,
                        (vote, build_id, user_email),
                    )
                    # Adjust counts
                    if vote == 1:
                        db.execute(
                            """
                                UPDATE community_builds
                                SET upvotes = upvotes + 1, downvotes = downvotes - 1
                                WHERE id = ?
                            """,
                            (build_id,),
                        )
                    else:
                        db.execute(
                            """
                                UPDATE community_builds
                                SET downvotes = downvotes + 1, upvotes = upvotes - 1
                                WHERE id = ?
                            """,
                            (build_id,),
                        )
            else:
                # Insert new vote
                db.execute(
                    """
                        INSERT INTO community_build_votes (build_id, user_email, vote)
                        VALUES (?, ?, ?)
                    """,
                    (build_id, user_email, vote),
                )
                # Adjust counts
                if vote == 1:
                    db.execute(
                        "UPDATE community_builds SET upvotes = upvotes + 1 WHERE id = ?",
                        (build_id,),
                    )
                else:
                    db.execute(
                        "UPDATE community_builds SET downvotes = downvotes + 1 WHERE id = ?",
                        (build_id,),
                    )

            db.commit()
            logger.info(f"Vote recorded: build {build_id} by {user_email} = {vote}")
            return True

        except Exception as e:
            logger.error(f"Failed to record vote: {e}")
            return False

    def get_user_vote(self, build_id: int, user_email: str) -> int:
        """Get user's vote on a build (1, -1, or 0 if no vote)."""
        try:
            db = get_db()
            row = db.execute(
                """
                    SELECT vote FROM community_build_votes
                    WHERE build_id = ? AND user_email = ?
                """,
                (build_id, user_email),
            ).fetchone()

            return row["vote"] if row else 0

        except Exception as e:
            logger.error(f"Failed to get user vote: {e}")
            return 0

    def delete_build(self, build_id: int, user_email: str) -> bool:
        """
        Delete a community build (only by author or admin).

        Args:
            build_id: Build to delete
            user_email: Email of requesting user

        Returns:
            True if successful
        """
        try:
            db = get_db()

            # Check if user is author (for now, we'll allow any logged-in user)
            # In production, add proper authorization
            db.execute("DELETE FROM community_build_votes WHERE build_id = ?", (build_id,))
            db.execute("DELETE FROM community_builds WHERE id = ?", (build_id,))

            db.commit()
            logger.info(f"Build deleted: {build_id} by {user_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete build: {e}")
            return False

    def get_stats(self) -> dict[str, Any]:
        """Get community builds statistics."""
        try:
            db = get_db()

            stats = {}

            # Total builds
            row = db.execute(
                "SELECT COUNT(*) as total, SUM(is_seed) as seed_count FROM community_builds"
            ).fetchone()
            stats["total_builds"] = row["total"] or 0
            stats["seed_builds"] = row["seed_count"] or 0
            stats["community_builds"] = stats["total_builds"] - stats["seed_builds"]

            # Builds by game
            rows = db.execute("""
                    SELECT game, COUNT(*) as count
                    FROM community_builds
                    GROUP BY game
                    ORDER BY count DESC
                """).fetchall()
            stats["by_game"] = {row["game"]: row["count"] for row in rows}

            # Total votes
            row = db.execute("""
                    SELECT SUM(upvotes) as total_up, SUM(downvotes) as total_down
                    FROM community_builds
                """).fetchone()
            stats["total_upvotes"] = row["total_up"] or 0
            stats["total_downvotes"] = row["total_down"] or 0

            return stats

        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {}


# Singleton instance
_community_builds_service: Optional[CommunityBuildsService] = None


def get_community_builds_service() -> CommunityBuildsService:
    """Get or create community builds service singleton."""
    global _community_builds_service
    if _community_builds_service is None:
        _community_builds_service = CommunityBuildsService()
    return _community_builds_service
