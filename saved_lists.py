"""
User Saved Lists — Server-side storage for Pro users.
Syncs mod lists across devices with full analysis snapshots.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from flask import g

logger = logging.getLogger(__name__)


def get_saved_lists(
    user_email: str,
    game: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """
    Get user's saved lists with optional filtering.
    
    Args:
        user_email: User's email
        game: Filter by game (optional)
        search: Search in name/tags/notes (optional)
        limit: Max results (default 50)
        offset: Pagination offset
    
    Returns:
        List of saved list metadata
    """
    db = get_db()
    
    # Build query
    query = """
        SELECT id, name, game, game_version, masterlist_version,
               tags, notes, source, list_text, saved_at, updated_at,
               analysis_snapshot
        FROM user_saved_lists
        WHERE user_email = ?
    """
    params = [user_email]
    
    # Add filters
    if game:
        query += " AND game = ?"
        params.append(game)
    
    if search:
        query += """
            AND (
                name LIKE ? OR
                tags LIKE ? OR
                notes LIKE ?
            )
        """
        search_term = f"%{search}%"
        params.extend([search_term, search_term, search_term])
    
    # Order and limit
    query += " ORDER BY updated_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    rows = db.execute(query, params)
    
    lists = []
    for row in rows:
        list_data = {
            "id": row["id"],
            "name": row["name"],
            "game": row["game"],
            "game_version": row["game_version"],
            "masterlist_version": row["masterlist_version"],
            "tags": row["tags"].split(",") if row["tags"] else [],
            "notes": row["notes"],
            "source": row["source"],
            "list_text": row["list_text"],
            "saved_at": row["saved_at"],
            "updated_at": row["updated_at"],
            "has_analysis": bool(row["analysis_snapshot"]),
        }
        
        # Parse analysis snapshot if present
        if row["analysis_snapshot"]:
            try:
                list_data["analysis"] = json.loads(row["analysis_snapshot"])
            except Exception as e:
                logger.warning(f"Failed to parse analysis snapshot for list {row['id']}: {e}")
                list_data["analysis"] = None
        
        lists.append(list_data)
    
    return lists


def save_list(
    user_email: str,
    name: str,
    list_text: str,
    game: str,
    game_version: Optional[str] = None,
    masterlist_version: Optional[str] = None,
    tags: Optional[List[str]] = None,
    notes: Optional[str] = None,
    analysis_snapshot: Optional[Dict] = None,
    source: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Save or update a mod list.
    
    Args:
        user_email: User's email
        name: List name
        list_text: Raw mod list text
        game: Game ID
        game_version: Game version (optional)
        masterlist_version: LOOT masterlist version (optional)
        tags: List of tags (optional)
        notes: User notes (optional)
        analysis_snapshot: Full analysis results (optional)
        source: Source (e.g., "build", "analyze", "import")
    
    Returns:
        Saved list data with ID
    """
    db = get_db()
    
    # Convert tags to comma-separated string
    tags_str = ",".join(tags) if tags else None
    
    # Convert analysis to JSON string
    analysis_json = json.dumps(analysis_snapshot) if analysis_snapshot else None
    
    try:
        # Try to update existing
        result = db.execute("""
            UPDATE user_saved_lists
            SET list_text = ?,
                game = ?,
                game_version = ?,
                masterlist_version = ?,
                tags = ?,
                notes = ?,
                analysis_snapshot = ?,
                source = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_email = ? AND name = ?
            RETURNING id
        """, (
            list_text, game, game_version, masterlist_version,
            tags_str, notes, analysis_json, source,
            user_email, name
        ))
        
        row = result.fetchone()
        
        if row:
            # Updated existing
            list_id = row["id"]
            action = "updated"
        else:
            # Insert new
            result = db.execute("""
                INSERT INTO user_saved_lists (
                    user_email, name, game, game_version, masterlist_version,
                    tags, notes, source, list_text, analysis_snapshot
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                RETURNING id
            """, (
                user_email, name, game, game_version, masterlist_version,
                tags_str, notes, source, list_text, analysis_json
            ))
            
            row = result.fetchone()
            list_id = row["id"]
            action = "created"
        
        db.commit()
        
        return {
            "id": list_id,
            "name": name,
            "action": action,
            "success": True,
        }
        
    except Exception as e:
        db.rollback()
        logger.exception(f"Failed to save list: {e}")
        return {
            "success": False,
            "error": str(e),
        }


def delete_list(user_email: str, list_id: int) -> Dict[str, Any]:
    """Delete a saved list."""
    db = get_db()
    
    result = db.execute("""
        DELETE FROM user_saved_lists
        WHERE id = ? AND user_email = ?
    """, (list_id, user_email))
    
    db.commit()
    
    if result.rowcount > 0:
        return {"success": True, "deleted": True}
    else:
        return {"success": False, "deleted": False, "error": "List not found"}


def get_list_by_id(user_email: str, list_id: int) -> Optional[Dict[str, Any]]:
    """Get a specific saved list by ID."""
    db = get_db()
    
    row = db.execute("""
        SELECT * FROM user_saved_lists
        WHERE id = ? AND user_email = ?
    """, (list_id, user_email)).fetchone()
    
    if not row:
        return None
    
    list_data = {
        "id": row["id"],
        "name": row["name"],
        "game": row["game"],
        "game_version": row["game_version"],
        "masterlist_version": row["masterlist_version"],
        "tags": row["tags"].split(",") if row["tags"] else [],
        "notes": row["notes"],
        "source": row["source"],
        "list_text": row["list_text"],
        "saved_at": row["saved_at"],
        "updated_at": row["updated_at"],
    }
    
    if row["analysis_snapshot"]:
        try:
            list_data["analysis"] = json.loads(row["analysis_snapshot"])
        except Exception as e:
            logger.warning(f"Failed to parse analysis snapshot: {e}")
            list_data["analysis"] = None
    
    return list_data


def update_list_metadata(
    user_email: str,
    list_id: int,
    name: Optional[str] = None,
    tags: Optional[List[str]] = None,
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    """Update list metadata (name, tags, notes) without changing the list."""
    db = get_db()
    
    # Build update query dynamically
    updates = []
    params = []
    
    if name:
        updates.append("name = ?")
        params.append(name)
    
    if tags is not None:
        updates.append("tags = ?")
        params.append(",".join(tags))
    
    if notes is not None:
        updates.append("notes = ?")
        params.append(notes)
    
    if not updates:
        return {"success": False, "error": "No fields to update"}
    
    updates.append("updated_at = CURRENT_TIMESTAMP")
    params.extend([list_id, user_email])
    
    query = f"""
        UPDATE user_saved_lists
        SET {', '.join(updates)}
        WHERE id = ? AND user_email = ?
    """
    
    try:
        result = db.execute(query, params)
        db.commit()
        
        if result.rowcount > 0:
            return {"success": True, "updated": True}
        else:
            return {"success": False, "updated": False, "error": "List not found"}
            
    except Exception as e:
        db.rollback()
        logger.exception(f"Failed to update list metadata: {e}")
        return {"success": False, "error": str(e)}


def get_list_stats(user_email: str) -> Dict[str, Any]:
    """Get statistics about user's saved lists."""
    db = get_db()
    
    # Total count
    total = db.execute("""
        SELECT COUNT(*) as count
        FROM user_saved_lists
        WHERE user_email = ?
    """, (user_email,)).fetchone()["count"]
    
    # Count by game
    by_game = db.execute("""
        SELECT game, COUNT(*) as count
        FROM user_saved_lists
        WHERE user_email = ?
        GROUP BY game
    """, (user_email,))
    
    game_counts = {row["game"]: row["count"] for row in by_game}
    
    # Recently updated
    recent = db.execute("""
        SELECT name, game, updated_at
        FROM user_saved_lists
        WHERE user_email = ?
        ORDER BY updated_at DESC
        LIMIT 5
    """, (user_email,))
    
    recent_lists = [
        {"name": row["name"], "game": row["game"], "updated_at": row["updated_at"]}
        for row in recent
    ]
    
    return {
        "total": total,
        "by_game": game_counts,
        "recent": recent_lists,
    }


def get_db():
    """Get database connection from Flask g."""
    if "db" not in g:
        from flask import current_app
        import sqlite3
        
        g.db = sqlite3.connect("users.db")
        g.db.row_factory = sqlite3.Row
    
    return g.db
