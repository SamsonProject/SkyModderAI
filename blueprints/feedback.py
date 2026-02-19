"""
SkyModderAI - Feedback Blueprint

User feedback collection endpoints:
- POST /api/feedback/rating - Submit 1-5 rating
- POST /api/feedback/submit - Submit detailed feedback
- POST /api/feedback/session - Save session data
- GET /api/feedback/summary - Get feedback summary (admin)
"""

import logging

from flask import Blueprint, jsonify, request, session

from db import get_db_session
from models import SatisfactionSurvey, UserActivity, UserFeedback

logger = logging.getLogger(__name__)

# Create blueprint
feedback_bp = Blueprint("feedback", __name__, url_prefix="/api/feedback")


@feedback_bp.route("/rating", methods=["POST"])
def submit_rating():
    """
    Submit a 1-5 rating.

    Request JSON:
    {
        "rating": 5,
        "context": {
            "category": "conflict_detection",
            "page": "/analyze"
        },
        "session_id": "sess_xxx"
    }
    """
    try:
        data = request.get_json() or {}
        rating = data.get("rating")
        context = data.get("context", {})
        session_id = data.get("session_id")

        # Validate rating
        if not rating or not isinstance(rating, int) or rating < 1 or rating > 5:
            return jsonify({"error": "Rating must be between 1 and 5"}), 400

        # Get user email if logged in
        user_email = session.get("user_email")

        # Save to database
        db_session = get_db_session()

        survey = SatisfactionSurvey(
            user_email=user_email,
            rating=rating,
            feedback_text=f"User rated {rating}/5",
            context_json=str(context),
        )
        db_session.add(survey)

        # Also log as activity
        activity = UserActivity(
            user_email=user_email,
            event_type="rating",
            event_data=str({"rating": rating, "context": context, "session_id": session_id}),
            session_id=session_id,
        )
        db_session.add(activity)
        db_session.commit()

        # Log to self-improvement
        if rating >= 4:
            log_win(context.get("category", "general"), f"User rated {rating}/5")
        elif rating <= 2:
            log_issue(
                context.get("category", "general"), f"User rated {rating}/5 - potential issue"
            )

        return jsonify({"success": True, "message": "Rating submitted"})

    except Exception:
        logger.exception("Failed to submit rating")
        return jsonify({"error": "Failed to submit rating"}), 500


@feedback_bp.route("/submit", methods=["POST"])
def submit_feedback():
    """
    Submit detailed feedback.

    Request JSON:
    {
        "type": "bug|suggestion|confusion|praise|other",
        "category": "ui|performance|accuracy|etc",
        "content": "Feedback text",
        "anonymous": false,
        "context": {...},
        "session_id": "sess_xxx"
    }
    """
    try:
        data = request.get_json() or {}
        feedback_type = data.get("type", "other")
        category = data.get("category", "general")
        content = data.get("content", "")
        anonymous = data.get("anonymous", False)
        context = data.get("context", {})
        session_id = data.get("session_id")

        # Validate
        if not content or len(content.strip()) == 0:
            return jsonify({"error": "Feedback content is required"}), 400

        # Get user email if logged in and not anonymous
        user_email = None if anonymous else session.get("user_email")

        # Determine priority
        priority_map = {
            "bug": 3,
            "suggestion": 1,
            "confusion": 2,
            "praise": 0,
            "other": 0,
        }
        priority = priority_map.get(feedback_type, 0)

        # Boost priority for critical categories
        if category in ["crash", "data_loss", "security"]:
            priority = 5

        # Save to database
        db_session = get_db_session()

        feedback = UserFeedback(
            user_email=user_email,
            type=feedback_type,
            category=category,
            content=content,
            context_json=str(context),
            status="open",
            priority=priority,
        )
        db_session.add(feedback)
        db_session.commit()

        # Log to self-improvement
        if feedback_type == "bug":
            log_issue(
                category,
                f"Bug report: {content[:100]}...",
                severity="high" if priority >= 4 else "medium",
            )
        elif feedback_type == "suggestion":
            log_suggestion(category, f"Feature request: {content[:100]}...")
        elif feedback_type == "praise":
            log_win(category, f"User praise: {content[:100]}...")

        logger.info(f"Feedback submitted: {feedback_type}/{category}")

        return jsonify({"success": True, "message": "Feedback submitted", "id": feedback.id})

    except Exception:
        logger.exception("Failed to submit feedback")
        return jsonify({"error": "Failed to submit feedback"}), 500


@feedback_bp.route("/session", methods=["POST"])
def save_session():
    """
    Save session data (called async on page unload).

    Request JSON:
    {
        "session_id": "sess_xxx",
        "user_email": "user@example.com",
        "duration_seconds": 300,
        "query_count": 5,
        "resolution_count": 3,
        "queries": [...],
        "resolutions": [...],
        "events": [...]
    }
    """
    try:
        data = request.get_json() or {}
        session_id = data.get("session_id")
        user_email = data.get("user_email")

        if not session_id:
            return jsonify({"error": "Session ID required"}), 400

        # Save to database
        db_session = get_db_session()

        activity = UserActivity(
            user_email=user_email,
            event_type="session_complete",
            event_data=str(data),
            session_id=session_id,
        )
        db_session.add(activity)
        db_session.commit()

        # Trigger post-session curation (async)
        from feedback_service import curate_after_session

        curate_after_session(data)

        logger.debug(f"Session saved: {session_id}")

        return jsonify({"success": True})

    except Exception:
        logger.exception("Failed to save session")
        # Don't return error - this is async and shouldn't affect user
        return jsonify({"success": True})


@feedback_bp.route("/summary", methods=["GET"])
def get_feedback_summary():
    """
    Get feedback summary (admin only).

    Query params:
    - days: Number of days to include (default: 7)
    """
    try:
        # Check if admin (simple check - improve with proper auth)
        user_email = session.get("user_email")
        if not user_email:
            return jsonify({"error": "Authentication required"}), 401

        # Get days parameter
        days = int(request.args.get("days", 7))

        # Import feedback service
        from feedback_service import get_feedback_summary as get_summary

        summary = get_summary(days)

        return jsonify(summary)

    except Exception:
        logger.exception("Failed to get feedback summary")
        return jsonify({"error": "Failed to get feedback summary"}), 500


# =============================================================================
# Helper Functions (imported from feedback_service)
# =============================================================================

from feedback_service import log_issue, log_suggestion, log_win
