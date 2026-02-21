"""
SkyModderAI - Compatibility Database Routes

Search, view, and submit compatibility reports between mods.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from flask import Blueprint, jsonify, redirect, render_template, request, session, url_for

from exceptions import AuthenticationError, ValidationError
from security_utils import rate_limit

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# Create blueprint
compatibility_bp = Blueprint("compatibility", __name__, url_prefix="/compatibility")


# =============================================================================
# Search & Browse Routes
# =============================================================================


@compatibility_bp.route("/search")
def search() -> Any:
    """Compatibility search page."""
    query = request.args.get("q", "")
    game = request.args.get("game", "skyrimse")
    limit = request.args.get("limit", "20")

    try:
        limit_int = int(limit)
        limit_int = max(1, min(limit_int, 100))
    except ValueError:
        limit_int = 20

    results = []
    if query:
        from compatibility_service import get_compatibility_service

        service = get_compatibility_service()
        results = service.search_compatibility(query, game if game != "all" else None, limit_int)

    if request.is_json:
        return jsonify({"success": True, "query": query, "results": results})

    return render_template(
        "compatibility/search.html",
        results=results,
        query=query,
        game=game,
    )


@compatibility_bp.route("/<mod_a>/vs/<mod_b>")
def compatibility_detail(mod_a: str, mod_b: str) -> Any:
    """Detail page for compatibility between two mods."""
    game = request.args.get("game", "skyrimse")

    from compatibility_service import get_compatibility_service

    service = get_compatibility_service()
    compatibility = service.get_compatibility_status(mod_a, mod_b, game)

    # Get mod details if available
    from search_engine import get_search_engine

    search_engine = get_search_engine(game)
    mod_a_info = search_engine.search(mod_a, limit=1)
    mod_b_info = search_engine.search(mod_b, limit=1)

    if request.is_json:
        return jsonify(
            {
                "success": True,
                "mod_a": mod_a,
                "mod_b": mod_b,
                "game": game,
                "compatibility": compatibility,
                "mod_a_info": mod_a_info[0] if mod_a_info else None,
                "mod_b_info": mod_b_info[0] if mod_b_info else None,
            }
        )

    return render_template(
        "compatibility/detail.html",
        mod_a=mod_a,
        mod_b=mod_b,
        game=game,
        compatibility=compatibility,
        mod_a_info=mod_a_info[0] if mod_a_info else None,
        mod_b_info=mod_b_info[0] if mod_b_info else None,
    )


@compatibility_bp.route("/mod/<mod_name>")
def mod_compatibility(mod_name: str) -> Any:
    """All compatibility reports for a specific mod."""
    game = request.args.get("game", "skyrimse")
    limit = request.args.get("limit", "50")

    try:
        limit_int = int(limit)
    except ValueError:
        limit_int = 50

    from db import get_db

    db = get_db()

    # Get all reports involving this mod
    reports = db.execute(
        """
        SELECT * FROM compatibility_reports
        WHERE (mod_a = ? OR mod_b = ?) AND game = ?
        ORDER BY upvotes - downvotes DESC, created_at DESC
        LIMIT ?
    """,
        (mod_name.lower(), mod_name.lower(), game, limit_int),
    ).fetchall()

    # Calculate summary stats
    total_reports = len(reports)
    compatible_count = sum(1 for r in reports if r["status"] == "compatible")
    incompatible_count = sum(1 for r in reports if r["status"] == "incompatible")
    needs_patch_count = sum(1 for r in reports if r["status"] == "needs_patch")

    # Get unique mod pairs
    mod_pairs = set()
    for report in reports:
        other_mod = report["mod_b"] if report["mod_a"] == mod_name.lower() else report["mod_a"]
        mod_pairs.add(other_mod)

    if request.is_json:
        return jsonify(
            {
                "success": True,
                "mod_name": mod_name,
                "game": game,
                "reports": [dict(r) for r in reports],
                "stats": {
                    "total_reports": total_reports,
                    "compatible": compatible_count,
                    "incompatible": incompatible_count,
                    "needs_patch": needs_patch_count,
                    "unique_mods": len(mod_pairs),
                },
            }
        )

    return render_template(
        "compatibility/mod.html",
        mod_name=mod_name,
        game=game,
        reports=[dict(r) for r in reports],
        stats={
            "total_reports": total_reports,
            "compatible": compatible_count,
            "incompatible": incompatible_count,
            "needs_patch": needs_patch_count,
            "unique_mods": len(mod_pairs),
        },
    )


# =============================================================================
# Submit Report Routes
# =============================================================================


@compatibility_bp.route("/submit", methods=["GET"])
def submit_form() -> Any:
    """Show compatibility report submission form."""
    if "user_email" not in session:
        return redirect(url_for("auth.login"))

    mod_a = request.args.get("mod_a", "")
    mod_b = request.args.get("mod_b", "")
    game = request.args.get("game", "skyrimse")

    return render_template(
        "compatibility/submit.html",
        mod_a=mod_a,
        mod_b=mod_b,
        game=game,
    )


@compatibility_bp.route("/submit", methods=["POST"])
@rate_limit(limit=10, window=300)  # 10 reports per 5 minutes
def submit_report() -> Any:
    """Submit a compatibility report."""
    if "user_email" not in session:
        raise AuthenticationError("Authentication required")

    try:
        data = request.get_json() or request.form
        mod_a = data.get("mod_a", "").strip()
        mod_b = data.get("mod_b", "").strip()
        game = data.get("game", "skyrimse").strip()
        status = data.get("status", "").strip()
        description = data.get("description", "").strip()

        if not mod_a or not mod_b:
            raise ValidationError("Both mod names are required")
        if not game:
            raise ValidationError("Game is required")
        if not status:
            raise ValidationError("Compatibility status is required")
        if status not in ("compatible", "incompatible", "needs_patch"):
            raise ValidationError(
                "Invalid status. Must be compatible, incompatible, or needs_patch"
            )
        if not description:
            raise ValidationError("Description is required")
        if len(description) > 2000:
            raise ValidationError("Description too long (max 2000 characters)")

        from compatibility_service import get_compatibility_service

        service = get_compatibility_service()
        report_id = service.submit_compatibility_report(
            mod_a=mod_a,
            mod_b=mod_b,
            game=game,
            status=status,
            description=description,
            user_email=session["user_email"],
        )

        if not report_id:
            raise ValidationError("Failed to submit report. Please try again.")

        logger.info(f"Compatibility report submitted: {report_id} by {session['user_email']}")

        # Notify mod authors if they have webhooks
        _notify_authors_of_report(mod_a, mod_b, game, status, report_id)

        if request.is_json:
            return jsonify(
                {
                    "success": True,
                    "report_id": report_id,
                    "message": "Compatibility report submitted!",
                }
            )

        return redirect(
            url_for("compatibility.compatibility_detail", mod_a=mod_a, mod_b=mod_b, game=game)
        )

    except ValidationError as e:
        if request.is_json:
            return jsonify({"success": False, "error": str(e)}), 400
        return render_template("error.html", error=str(e))
    except Exception as e:
        logger.error(f"Failed to submit compatibility report: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


def _notify_authors_of_report(
    mod_a: str, mod_b: str, game: str, status: str, report_id: int
) -> None:
    """Notify mod authors of new compatibility report (if they have webhooks)."""
    try:
        from db import get_db

        db = get_db()

        # Get webhooks for both mods
        webhooks = db.execute(
            """
            SELECT * FROM mod_webhooks
            WHERE (mod_name = ? OR mod_name = ?) AND game = ? AND is_active = 1
        """,
            (mod_a.lower(), mod_b.lower(), game),
        ).fetchall()

        if not webhooks:
            return

        # Prepare webhook payload
        payload = {
            "event": "compatibility_report",
            "report_id": report_id,
            "mod_a": mod_a,
            "mod_b": mod_b,
            "game": game,
            "status": status,
        }

        import requests

        for webhook in webhooks:
            try:
                requests.post(webhook["webhook_url"], json=payload, timeout=10)
                # Update last_triggered
                db.execute(
                    "UPDATE mod_webhooks SET last_triggered = CURRENT_TIMESTAMP WHERE id = ?",
                    (webhook["id"],),
                )
                db.commit()
            except Exception as e:
                logger.error(f"Failed to trigger webhook {webhook['id']}: {e}")

    except Exception as e:
        logger.error(f"Failed to notify authors: {e}")


# =============================================================================
# Voting Routes
# =============================================================================


@compatibility_bp.route("/report/<int:report_id>/vote", methods=["POST"])
def vote_report(report_id: int) -> Any:
    """Vote on a compatibility report."""
    if "user_email" not in session:
        raise AuthenticationError("Authentication required")

    try:
        data = request.get_json() or request.form
        vote = int(data.get("vote", 0))

        if vote not in (-1, 1):
            raise ValidationError("Vote must be -1 (downvote) or 1 (upvote)")

        from compatibility_service import get_compatibility_service

        service = get_compatibility_service()
        success = service.vote_report(report_id, session["user_email"], vote)

        if success:
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": "Failed to vote"}), 500

    except ValidationError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        logger.error(f"Failed to vote on report: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


# =============================================================================
# Browse & Discovery Routes
# =============================================================================


@compatibility_bp.route("/browse")
def browse() -> Any:
    """Browse compatibility reports."""
    game = request.args.get("game", "skyrimse")
    status = request.args.get("status", "")
    sort = request.args.get("sort", "top")  # top, new, controversial
    limit = request.args.get("limit", "50")

    try:
        limit_int = int(limit)
        limit_int = max(1, min(limit_int, 100))
    except ValueError:
        limit_int = 50

    from db import get_db

    db = get_db()

    # Build query
    query = """
        SELECT * FROM compatibility_reports
        WHERE game = ?
    """
    params = [game]

    if status:
        query += " AND status = ?"
        params.append(status)

    # Sort
    if sort == "top":
        query += " ORDER BY upvotes - downvotes DESC"
    elif sort == "new":
        query += " ORDER BY created_at DESC"
    elif sort == "controversial":
        query += " ORDER BY (upvotes + downvotes) DESC"
    else:
        query += " ORDER BY upvotes - downvotes DESC"

    query += " LIMIT ?"
    params.append(limit_int)

    reports = db.execute(query, params).fetchall()

    if request.is_json:
        return jsonify(
            {
                "success": True,
                "reports": [dict(r) for r in reports],
                "game": game,
                "status": status,
                "sort": sort,
            }
        )

    return render_template(
        "compatibility/browse.html",
        reports=[dict(r) for r in reports],
        game=game,
        status=status,
        sort=sort,
    )


@compatibility_bp.route("/recent")
def recent_reports() -> Any:
    """Recently submitted compatibility reports."""
    limit = request.args.get("limit", "20")

    try:
        limit_int = int(limit)
        limit_int = max(1, min(limit_int, 50))
    except ValueError:
        limit_int = 20

    from db import get_db

    db = get_db()
    reports = db.execute(
        """
        SELECT * FROM compatibility_reports
        ORDER BY created_at DESC
        LIMIT ?
    """,
        (limit_int,),
    ).fetchall()

    if request.is_json:
        return jsonify({"success": True, "reports": [dict(r) for r in reports]})

    return render_template("compatibility/recent.html", reports=[dict(r) for r in reports])
