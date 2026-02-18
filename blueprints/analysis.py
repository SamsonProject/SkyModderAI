"""
SkyModderAI - Analysis Blueprint

Handles mod list analysis, conflict detection, and recommendations.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from flask import (
    Blueprint,
    current_app,
    jsonify,
    render_template,
    request,
    session,
)

from exceptions import (
    AnalysisError,
    DataNotAvailableError,
    InvalidGameIDError,
    InvalidModListError,
    ValidationError,
)
from logging_utils import get_request_id
from security_utils import rate_limit, validate_game_id, validate_mod_list

if TYPE_CHECKING:
    from sqlite3 import Connection

logger = logging.getLogger(__name__)

# Create blueprint
analysis_bp = Blueprint("analysis", __name__, url_prefix="/analysis")


# =============================================================================
# Analysis Routes
# =============================================================================


@analysis_bp.route("/", methods=["GET", "POST"])
@rate_limit(limit=10, window=60)  # 10 analyses per minute
def analyze() -> Any:
    """
    Main analysis endpoint - accepts mod list and returns conflict analysis.

    GET: Render analysis form
    POST: Analyze submitted mod list
    """
    if request.method == "GET":
        return render_template("analysis.html")

    # POST: Handle analysis
    try:
        data = request.get_json(silent=True) or request.form
        mod_list = data.get("mod_list", "")
        game = data.get("game", "skyrimse")

        # Validate inputs
        if not mod_list:
            raise InvalidModListError("Mod list is required")

        mod_list = validate_mod_list(mod_list)

        try:
            game = validate_game_id(game)
        except ValueError as e:
            raise InvalidGameIDError(str(e))

        # Perform analysis
        from conflict_detector import ConflictDetector, parse_mod_list_text

        mods = parse_mod_list_text(mod_list)
        detector = ConflictDetector(game)
        analysis_result = detector.analyze(mods)

        # Get recommendations
        from mod_recommendations import get_recommendations

        recommendations = get_recommendations(analysis_result, game)

        # Get system impact
        from system_impact import get_system_impact

        impact = get_system_impact(mods, game)

        logger.info(
            f"Analysis completed: {len(mods)} mods, {len(analysis_result.get('conflicts', []))} conflicts",
            extra={"request_id": get_request_id()},
        )

        # Track analysis activity
        if session.get("user_email"):
            from db import track_activity

            track_activity(
                session["user_email"],
                "analysis_performed",
                {"game": game, "mod_count": len(mods)},
            )

        if request.is_json:
            return jsonify(
                {
                    "success": True,
                    "analysis": analysis_result,
                    "recommendations": recommendations,
                    "system_impact": impact,
                    "mod_count": len(mods),
                    "game": game,
                }
            )

        return render_template(
            "analysis_result.html",
            analysis=analysis_result,
            recommendations=recommendations,
            system_impact=impact,
            mod_count=len(mods),
            game=game,
        )

    except (InvalidModListError, InvalidGameIDError, ValidationError) as e:
        if request.is_json:
            return jsonify({"success": False, "error": str(e)}), 400
        return render_template("error.html", error=str(e)), 400

    except Exception as e:
        logger.error(f"Analysis failed: {e}", extra={"request_id": get_request_id()})
        if request.is_json:
            return jsonify({"success": False, "error": "Analysis failed"}), 500
        return render_template("error.html", error="Analysis failed"), 500


@analysis_bp.route("/quick/<game_id>")
def quick_analyze(game_id: str) -> Any:
    """Quick analyze for a specific game."""
    try:
        game = validate_game_id(game_id)
    except ValueError as e:
        raise InvalidGameIDError(str(e))

    return render_template("analysis.html", game=game)


@analysis_bp.route("/history")
def analysis_history() -> Any:
    """View analysis history for logged-in users."""
    from blueprints.auth import login_required

    if "user_email" not in session:
        return render_template("error.html", error="Please log in to view history"), 401

    # Get user's saved analyses
    from db import get_user_saved_lists

    saved_lists = get_user_saved_lists(session["user_email"])

    return render_template("analysis_history.html", saved_lists=saved_lists)


@analysis_bp.route("/save", methods=["POST"])
def save_analysis() -> Any:
    """Save analysis results."""
    from blueprints.auth import login_required

    if "user_email" not in session:
        if request.is_json:
            return jsonify({"success": False, "error": "Authentication required"}), 401
        return render_template("error.html", error="Please log in to save analyses"), 401

    try:
        data = request.get_json() or request.form
        name = data.get("name", "")
        mod_list = data.get("mod_list", "")
        game = data.get("game", "skyrimse")
        analysis_snapshot = data.get("analysis_snapshot", "")

        if not name or not mod_list:
            raise ValidationError("Name and mod list are required")

        # Save to database
        from db import save_user_list

        save_user_list(
            email=session["user_email"],
            name=name,
            mod_list=mod_list,
            game=game,
            analysis_snapshot=analysis_snapshot,
        )

        logger.info(
            f"Analysis saved: {name} by {session['user_email']}",
            extra={"request_id": get_request_id()},
        )

        if request.is_json:
            return jsonify({"success": True, "message": "Analysis saved"})

        return redirect(url_for("analysis.analysis_history"))

    except ValidationError as e:
        if request.is_json:
            return jsonify({"success": False, "error": str(e)}), 400
        return render_template("error.html", error=str(e)), 400

    except Exception as e:
        logger.error(f"Failed to save analysis: {e}", extra={"request_id": get_request_id()})
        if request.is_json:
            return jsonify({"success": False, "error": "Failed to save"}), 500
        return render_template("error.html", error="Failed to save analysis"), 500
