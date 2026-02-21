"""
SkyModderAI - Mod Detail Pages

Individual mod pages with aggregated compatibility data, author info, and more.
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

from flask import Blueprint, jsonify, render_template, request

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# Create blueprint
mod_detail_bp = Blueprint("mod_detail", __name__, url_prefix="/mod")


@mod_detail_bp.route("/<path:mod_name>")
def mod_page(mod_name: str) -> Any:
    """Individual mod detail page."""
    game = request.args.get("game", "skyrimse")

    from db import get_db

    db = get_db()

    # Get mod details from database (if exists)
    mod_detail = db.execute(
        """
        SELECT * FROM mod_details
        WHERE mod_name = ? AND game = ?
    """,
        (mod_name.lower(), game),
    ).fetchone()

    # Get compatibility reports involving this mod
    reports = db.execute(
        """
        SELECT * FROM compatibility_reports
        WHERE (mod_a = ? OR mod_b = ?) AND game = ?
        ORDER BY upvotes - downvotes DESC, created_at DESC
        LIMIT 50
    """,
        (mod_name.lower(), mod_name.lower(), game),
    ).fetchall()

    # Get author info if verified
    author_claim = db.execute(
        """
        SELECT * FROM mod_author_claims
        WHERE mod_name = ? AND game = ? AND verification_status = 'verified'
        LIMIT 1
    """,
        (mod_name.lower(), game),
    ).fetchone()

    # Calculate statistics
    total_reports = len(reports)
    compatible_count = sum(1 for r in reports if r["status"] == "compatible")
    incompatible_count = sum(1 for r in reports if r["status"] == "incompatible")
    needs_patch_count = sum(1 for r in reports if r["status"] == "needs_patch")

    # Get related mods (mods that appear in reports with this mod)
    related_mods = set()
    for report in reports:
        other_mod = report["mod_b"] if report["mod_a"] == mod_name.lower() else report["mod_a"]
        related_mods.add(other_mod)

    # Get patches for this mod
    patches = db.execute(
        """
        SELECT DISTINCT
            CASE WHEN mod_a = ? THEN mod_b ELSE mod_a END as patch_mod,
            description
        FROM compatibility_reports
        WHERE (mod_a = ? OR mod_b = ?)
        AND game = ?
        AND status = 'needs_patch'
        AND (description LIKE '%patch%' OR description LIKE '%compatibility%')
        LIMIT 20
    """,
        (mod_name.lower(), mod_name.lower(), mod_name.lower(), game),
    ).fetchall()

    # Build compatibility score (0-100)
    if total_reports > 0:
        compatible_weight = compatible_count * 1.0
        patch_weight = needs_patch_count * 0.5
        incompatible_weight = incompatible_count * 0.0
        total_weight = compatible_count + needs_patch_count + incompatible_count

        # Weight by votes
        weighted_score = 0
        total_votes = 0
        for report in reports:
            vote_weight = (report["upvotes"] - report["downvotes"]) + 1
            if report["status"] == "compatible":
                weighted_score += vote_weight * 1.0
            elif report["status"] == "needs_patch":
                weighted_score += vote_weight * 0.5
            total_votes += vote_weight

        compatibility_score = (weighted_score / total_votes * 100) if total_votes > 0 else 50
    else:
        compatibility_score = 75  # Default score for mods with no reports

    # Get load order rules if available
    loot_rules = db.execute(
        """
        SELECT * FROM loot_rules
        WHERE mod_name = ? OR mod_name LIKE ?
        LIMIT 10
    """,
        (mod_name.lower(), f"%{mod_name.lower()}%"),
    ).fetchall()

    response_data = {
        "mod_name": mod_name,
        "game": game,
        "mod_detail": dict(mod_detail) if mod_detail else None,
        "author_claim": dict(author_claim) if author_claim else None,
        "reports": [dict(r) for r in reports],
        "stats": {
            "total_reports": total_reports,
            "compatible": compatible_count,
            "incompatible": incompatible_count,
            "needs_patch": needs_patch_count,
            "related_mods_count": len(related_mods),
            "patches_count": len(patches),
        },
        "compatibility_score": round(compatibility_score, 1),
        "related_mods": list(related_mods)[:20],
        "patches": [dict(p) for p in patches],
        "loot_rules": [dict(r) for r in loot_rules],
    }

    if request.is_json:
        return jsonify({"success": True, **response_data})

    return render_template(
        "mod_detail/page.html",
        **response_data,
    )


@mod_detail_bp.route("/<path:mod_name>/compatibility")
def mod_compatibility_json(mod_name: str) -> Any:
    """Get compatibility data for a mod as JSON."""
    game = request.args.get("game", "skyrimse")
    include_reports = request.args.get("include_reports", "true").lower() == "true"

    from db import get_db

    db = get_db()

    # Get reports
    reports = []
    if include_reports:
        reports = db.execute(
            """
            SELECT * FROM compatibility_reports
            WHERE (mod_a = ? OR mod_b = ?) AND game = ?
            ORDER BY upvotes - downvotes DESC
            LIMIT 100
        """,
            (mod_name.lower(), mod_name.lower(), game),
        ).fetchall()

    # Build compatibility matrix
    compatibility_matrix = {}
    for report in reports:
        other_mod = report["mod_b"] if report["mod_a"] == mod_name.lower() else report["mod_a"]
        if other_mod not in compatibility_matrix:
            compatibility_matrix[other_mod] = []
        compatibility_matrix[other_mod].append(
            {
                "status": report["status"],
                "description": report["description"],
                "upvotes": report["upvotes"],
                "downvotes": report["downvotes"],
            }
        )

    # Calculate overall status per mod
    compatibility_summary = {}
    for other_mod, mod_reports in compatibility_matrix.items():
        total_upvotes = sum(r["upvotes"] for r in mod_reports)
        total_downvotes = sum(r["downvotes"] for r in mod_reports)

        # Weight statuses by votes
        status_weights = {"compatible": 0, "needs_patch": 0, "incompatible": 0}
        for report in mod_reports:
            vote_weight = (report["upvotes"] - report["downvotes"]) + 1
            status_weights[report["status"]] += vote_weight

        # Determine overall status
        if status_weights["incompatible"] > (total_upvotes + len(mod_reports)) * 0.3:
            overall_status = "incompatible"
        elif status_weights["needs_patch"] > (total_upvotes + len(mod_reports)) * 0.2:
            overall_status = "needs_patch"
        else:
            overall_status = "compatible"

        compatibility_summary[other_mod] = {
            "status": overall_status,
            "report_count": len(mod_reports),
            "net_votes": total_upvotes - total_downvotes,
        }

    return jsonify(
        {
            "success": True,
            "mod_name": mod_name,
            "game": game,
            "compatibility_summary": compatibility_summary,
            "reports": [dict(r) for r in reports] if include_reports else [],
        }
    )


@mod_detail_bp.route("/<path:mod_name>/embed")
def mod_embed_widget(mod_name: str) -> Any:
    """Embeddable compatibility widget for mod pages."""
    game = request.args.get("game", "skyrimse")
    theme = request.args.get("theme", "dark")  # dark, light

    from db import get_db

    db = get_db()

    # Get basic stats
    stats = db.execute(
        """
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN status = 'compatible' THEN 1 ELSE 0 END) as compatible,
            SUM(CASE WHEN status = 'incompatible' THEN 1 ELSE 0 END) as incompatible,
            SUM(CASE WHEN status = 'needs_patch' THEN 1 ELSE 0 END) as needs_patch
        FROM compatibility_reports
        WHERE (mod_a = ? OR mod_b = ?) AND game = ?
    """,
        (mod_name.lower(), mod_name.lower(), game),
    ).fetchone()

    # Calculate score
    total = stats["total"] or 0
    if total > 0:
        score = ((stats["compatible"] + stats["needs_patch"] * 0.5) / total) * 100
    else:
        score = 75

    widget_data = {
        "mod_name": mod_name,
        "game": game,
        "score": round(score, 1),
        "total_reports": total,
        "compatible": stats["compatible"] or 0,
        "incompatible": stats["incompatible"] or 0,
        "needs_patch": stats["needs_patch"] or 0,
        "theme": theme,
    }

    return render_template("mod_detail/embed.html", **widget_data)
