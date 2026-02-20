"""
Mod Repository - Data access layer for mod management.

Handles database operations for mods, mod lists, and mod metadata.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from db import get_db

logger = logging.getLogger(__name__)


class ModRepository:
    """Repository for mod-related database operations."""

    def __init__(self) -> None:
        """Initialize the mod repository."""
        self._db = None

    def _get_db(self):
        """Get database connection."""
        if self._db is None:
            self._db = get_db()
        return self._db

    def get_mod_by_id(self, mod_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a mod by ID.

        Args:
            mod_id: Mod ID

        Returns:
            Mod dict if found, None otherwise
        """
        db = self._get_db()
        query = "SELECT * FROM mods WHERE id = ?"
        row = db.execute(query, (mod_id,)).fetchone()

        if row:
            return dict(row)
        return None

    def get_mods_by_game(
        self,
        game_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Get mods for a specific game.

        Args:
            game_id: Game ID (e.g., 'skyrimse')
            limit: Maximum mods to return
            offset: Pagination offset

        Returns:
            List of mods
        """
        db = self._get_db()
        query = """
            SELECT * FROM mods
            WHERE game_id = ?
            ORDER BY name ASC
            LIMIT ? OFFSET ?
        """
        cursor = db.execute(query, (game_id, limit, offset))
        cursor.row_factory = sqlite3.Row
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def search_mods(
        self,
        query: str,
        game_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Search mods by name or description.

        Args:
            query: Search query
            game_id: Filter by game (optional)
            limit: Maximum results

        Returns:
            List of matching mods
        """
        db = self._get_db()

        if game_id:
            sql = """
                SELECT * FROM mods
                WHERE game_id = ? AND (name LIKE ? OR description LIKE ?)
                ORDER BY name ASC
                LIMIT ?
            """
            params: tuple = (game_id, f"%{query}%", f"%{query}%", limit)
        else:
            sql = """
                SELECT * FROM mods
                WHERE name LIKE ? OR description LIKE ?
                ORDER BY name ASC
                LIMIT ?
            """
            params = (f"%{query}%", f"%{query}%", limit)

        cursor = db.execute(sql, params)
        cursor.row_factory = sqlite3.Row
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def create_mod(
        self,
        name: str,
        game_id: str,
        author: Optional[str] = None,
        description: Optional[str] = None,
        url: Optional[str] = None,
        version: Optional[str] = None,
    ) -> Optional[int]:
        """
        Create a new mod entry.

        Args:
            name: Mod name
            game_id: Game ID
            author: Mod author (optional)
            description: Mod description (optional)
            url: Mod URL (optional)
            version: Mod version (optional)

        Returns:
            New mod ID if successful, None otherwise
        """
        db = self._get_db()
        query = """
            INSERT INTO mods (name, game_id, author, description, url, version)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        try:
            cursor = db.execute(query, (name, game_id, author, description, url, version))
            db.commit()
            return cursor.lastrowid
        except Exception as e:
            logger.error(f"Failed to create mod: {e}")
            return None

    def update_mod(
        self,
        mod_id: int,
        **kwargs: Any,
    ) -> bool:
        """
        Update mod fields.

        Args:
            mod_id: Mod ID to update
            **kwargs: Fields to update (name, author, description, etc.)

        Returns:
            True if successful, False otherwise
        """
        db = self._get_db()

        allowed_fields = {"name", "author", "description", "url", "version", "game_id"}
        updates = []
        params: list = []

        for field, value in kwargs.items():
            if field in allowed_fields and value is not None:
                updates.append(f"{field} = ?")
                params.append(value)

        if not updates:
            return False

        params.append(mod_id)
        query = f"UPDATE mods SET {', '.join(updates)} WHERE id = ?"

        try:
            db.execute(query, params)
            db.commit()
            return db.total_changes > 0
        except Exception as e:
            logger.error(f"Failed to update mod: {e}")
            return False

    def delete_mod(self, mod_id: int) -> bool:
        """
        Delete a mod.

        Args:
            mod_id: Mod ID to delete

        Returns:
            True if deleted, False otherwise
        """
        db = self._get_db()
        query = "DELETE FROM mods WHERE id = ?"

        try:
            db.execute(query, (mod_id,))
            db.commit()
            return db.total_changes > 0
        except Exception as e:
            logger.error(f"Failed to delete mod: {e}")
            return False

    def get_mod_list(self, list_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a mod list by ID.

        Args:
            list_id: List ID

        Returns:
            List dict if found, None otherwise
        """
        db = self._get_db()
        query = "SELECT * FROM mod_lists WHERE id = ?"
        row = db.execute(query, (list_id,)).fetchone()

        if row:
            return dict(row)
        return None

    def get_mod_lists_by_user(
        self,
        user_email: str,
        game_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get mod lists created by a user.

        Args:
            user_email: User's email
            game_id: Filter by game (optional)

        Returns:
            List of mod lists
        """
        db = self._get_db()

        if game_id:
            query = """
                SELECT * FROM mod_lists
                WHERE user_email = ? AND game_id = ?
                ORDER BY created_at DESC
            """
            params: tuple = (user_email, game_id)
        else:
            query = """
                SELECT * FROM mod_lists
                WHERE user_email = ?
                ORDER BY created_at DESC
            """
            params = (user_email,)

        cursor = db.execute(query, params)
        cursor.row_factory = sqlite3.Row
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def create_mod_list(
        self,
        user_email: str,
        name: str,
        game_id: str,
        description: Optional[str] = None,
        is_public: bool = True,
    ) -> Optional[int]:
        """
        Create a new mod list.

        Args:
            user_email: Creator's email
            name: List name
            game_id: Game ID
            description: List description (optional)
            is_public: Whether list is public (default True)

        Returns:
            New list ID if successful, None otherwise
        """
        db = self._get_db()
        query = """
            INSERT INTO mod_lists (user_email, name, game_id, description, is_public)
            VALUES (?, ?, ?, ?, ?)
        """
        try:
            cursor = db.execute(query, (user_email, name, game_id, description, is_public))
            db.commit()
            return cursor.lastrowid
        except Exception as e:
            logger.error(f"Failed to create mod list: {e}")
            return None

    def add_mod_to_list(
        self,
        list_id: int,
        mod_id: int,
        load_order: Optional[int] = None,
    ) -> bool:
        """
        Add a mod to a list.

        Args:
            list_id: List ID
            mod_id: Mod ID
            load_order: Load order position (optional)

        Returns:
            True if successful, False otherwise
        """
        db = self._get_db()
        query = """
            INSERT INTO mod_list_items (list_id, mod_id, load_order)
            VALUES (?, ?, ?)
        """
        try:
            db.execute(query, (list_id, mod_id, load_order))
            db.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to add mod to list: {e}")
            return False

    def remove_mod_from_list(self, list_id: int, mod_id: int) -> bool:
        """
        Remove a mod from a list.

        Args:
            list_id: List ID
            mod_id: Mod ID

        Returns:
            True if removed, False otherwise
        """
        db = self._get_db()
        query = "DELETE FROM mod_list_items WHERE list_id = ? AND mod_id = ?"

        try:
            db.execute(query, (list_id, mod_id))
            db.commit()
            return db.total_changes > 0
        except Exception as e:
            logger.error(f"Failed to remove mod from list: {e}")
            return False

    def get_mods_in_list(self, list_id: int) -> List[Dict[str, Any]]:
        """
        Get all mods in a list with their load order.

        Args:
            list_id: List ID

        Returns:
            List of mods with load order
        """
        db = self._get_db()
        query = """
            SELECT m.*, li.load_order
            FROM mods m
            INNER JOIN mod_list_items li ON m.id = li.mod_id
            WHERE li.list_id = ?
            ORDER BY li.load_order ASC
        """
        cursor = db.execute(query, (list_id,))
        cursor.row_factory = sqlite3.Row
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def delete_mod_list(self, list_id: int) -> bool:
        """
        Delete a mod list and all its items.

        Args:
            list_id: List ID to delete

        Returns:
            True if deleted, False otherwise
        """
        db = self._get_db()

        try:
            # First delete all items
            db.execute("DELETE FROM mod_list_items WHERE list_id = ?", (list_id,))
            # Then delete the list
            db.execute("DELETE FROM mod_lists WHERE id = ?", (list_id,))
            db.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to delete mod list: {e}")
            return False
