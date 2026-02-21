"""
SkyModderAI - Mod Author Routes

Blueprint for mod author verification, claims, dashboard, and tools.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from flask import (
    Blueprint,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)

from exceptions import AuthenticationError, ValidationError
from security_utils import rate_limit

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# Create blueprint
mod_author_bp = Blueprint("mod_author", __name__, url_prefix="/mod-author")


# =============================================================================
# Dashboard & UI Routes
# =============================================================================


@mod_author_bp.route("/dashboard")
def dashboard() -> Any:
    """Mod author dashboard."""
    if "user_email" not in session:
        if request.is_json:
            raise AuthenticationError("Authentication required")
        return redirect(url_for("auth.login"))

    from db import get_mod_author_dashboard_data, get_mod_author_notifications

    dashboard_data = get_mod_author_dashboard_data(session["user_email"])
    notifications = get_mod_author_notifications(session["user_email"], unread_only=True)
    claims = get_mod_author_claims(session["user_email"])

    if request.is_json:
        return jsonify(
            {
                "success": True,
                "dashboard": dashboard_data,
                "notifications": notifications,
                "claims": claims,
            }
        )

    return render_template(
        "mod_author/dashboard.html",
        dashboard=dashboard_data,
        notifications=notifications,
        claims=claims,
    )


@mod_author_bp.route("/claims")
def claims_index() -> Any:
    """View all mod claims."""
    if "user_email" not in session:
        if request.is_json:
            raise AuthenticationError("Authentication required")
        return redirect(url_for("auth.login"))

    from db import get_mod_author_claims

    claims = get_mod_author_claims(session["user_email"])

    if request.is_json:
        return jsonify({"success": True, "claims": claims})

    return render_template("mod_author/claims.html", claims=claims)


@mod_author_bp.route("/notifications")
def notifications_index() -> Any:
    """View all notifications."""
    if "user_email" not in session:
        if request.is_json:
            raise AuthenticationError("Authentication required")
        return redirect(url_for("auth.login"))

    from db import get_mod_author_notifications

    notifications = get_mod_author_notifications(session["user_email"])

    if request.is_json:
        return jsonify({"success": True, "notifications": notifications})

    return render_template("mod_author/notifications.html", notifications=notifications)


# =============================================================================
# API Routes - Claims
# =============================================================================


@mod_author_bp.route("/api/claim", methods=["POST"])
@rate_limit(limit=5, window=300)  # 5 claims per 5 minutes
def submit_claim() -> Any:
    """Submit a mod author claim."""
    if "user_email" not in session:
        raise AuthenticationError("Authentication required")

    try:
        data = request.get_json() or request.form
        mod_name = data.get("mod_name", "").strip()
        author_name = data.get("author_name", "").strip()
        game = data.get("game", "").strip()
        nexus_id = data.get("nexus_id")
        nexus_profile_url = data.get("nexus_profile_url", "").strip()
        mod_page_url = data.get("mod_page_url", "").strip()

        if not mod_name:
            raise ValidationError("Mod name is required")
        if not author_name:
            raise ValidationError("Author name is required")
        if not game:
            raise ValidationError("Game is required")

        from db import create_mod_author_claim, is_verified_mod_author

        # Check if already verified for this mod
        if is_verified_mod_author(session["user_email"], mod_name, game):
            raise ValidationError("You are already verified as author of this mod")

        # Create claim
        claim_id = create_mod_author_claim(
            mod_name=mod_name,
            author_email=session["user_email"],
            author_name=author_name,
            game=game,
            nexus_id=nexus_id if nexus_id else None,
            nexus_profile_url=nexus_profile_url if nexus_profile_url else None,
            mod_page_url=mod_page_url if mod_page_url else None,
        )

        if not claim_id:
            raise ValidationError("Failed to submit claim. Please try again.")

        logger.info(f"Mod claim submitted: {mod_name} by {session['user_email']}")

        return jsonify(
            {
                "success": True,
                "claim_id": claim_id,
                "message": "Claim submitted. Verification pending.",
            }
        )

    except ValidationError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        logger.error(f"Failed to submit mod claim: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@mod_author_bp.route("/api/claim/<int:claim_id>/verify", methods=["POST"])
@rate_limit(limit=10, window=60)
def verify_claim(claim_id: int) -> Any:
    """Verify a mod claim via Nexus API or file upload."""
    if "user_email" not in session:
        raise AuthenticationError("Authentication required")

    try:
        from db import get_db, get_mod_author_claims

        db = get_db()
        claim = db.execute("SELECT * FROM mod_author_claims WHERE id = ?", (claim_id,)).fetchone()

        if not claim:
            raise ValidationError("Claim not found")

        if claim["author_email"] != session["user_email"]:
            raise ValidationError("Not authorized to verify this claim")

        if claim["verification_status"] == "verified":
            raise ValidationError("Claim already verified")

        data = request.get_json() or request.form
        method = data.get("method", "nexus_api")

        if method == "nexus_api":
            nexus_api_key = data.get("nexus_api_key", "").strip()
            if not nexus_api_key:
                raise ValidationError("Nexus API key required")

            # Verify via Nexus API
            from mod_author_service import get_mod_author_service

            service = get_mod_author_service()
            success = service.verify_via_nexus_api(claim_id, nexus_api_key)

            if success:
                return jsonify({"success": True, "message": "Claim verified via Nexus API"})
            else:
                return jsonify(
                    {
                        "success": False,
                        "error": "Nexus API verification failed. Author name mismatch?",
                    }
                ), 400

        elif method == "file_upload":
            # Handle file upload verification
            if "mod_file" not in request.files:
                raise ValidationError("Mod file required")

            file = request.files["mod_file"]
            if file.filename:
                # Calculate SHA256 hash of uploaded file
                file_content = file.read()
                file_hash = hashlib.sha256(file_content).hexdigest()

                from mod_author_service import get_mod_author_service

                service = get_mod_author_service()
                success = service.verify_via_file_upload(claim_id, file_hash)

                if success:
                    return jsonify({"success": True, "message": "Claim verified via file upload"})
                else:
                    return jsonify(
                        {"success": False, "error": "File upload verification failed"}
                    ), 400

        else:
            raise ValidationError("Invalid verification method")

    except ValidationError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        logger.error(f"Failed to verify mod claim: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


# =============================================================================
# API Routes - Notifications
# =============================================================================


@mod_author_bp.route("/api/notifications/read", methods=["POST"])
def mark_notifications_read() -> Any:
    """Mark all notifications as read."""
    if "user_email" not in session:
        raise AuthenticationError("Authentication required")

    try:
        from db import mark_all_notifications_read

        mark_all_notifications_read(session["user_email"])
        return jsonify({"success": True})

    except Exception as e:
        logger.error(f"Failed to mark notifications read: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@mod_author_bp.route("/api/notifications/<int:notification_id>/read", methods=["POST"])
def mark_notification_read(notification_id: int) -> Any:
    """Mark a specific notification as read."""
    if "user_email" not in session:
        raise AuthenticationError("Authentication required")

    try:
        from db import mark_notification_read

        mark_notification_read(notification_id, session["user_email"])
        return jsonify({"success": True})

    except Exception as e:
        logger.error(f"Failed to mark notification read: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


# =============================================================================
# Mod Author Tools
# =============================================================================


@mod_author_bp.route("/tools")
def tools_index() -> Any:
    """Mod author tools index."""
    if "user_email" not in session:
        return redirect(url_for("auth.login"))

    return render_template("mod_author/tools.html")


@mod_author_bp.route("/tools/batch-test", methods=["GET", "POST"])
def batch_test() -> Any:
    """Batch test mod against multiple load orders."""
    if "user_email" not in session:
        return redirect(url_for("auth.login"))

    results = None
    if request.method == "POST":
        try:
            data = request.get_json() or request.form
            mod_name = data.get("mod_name", "").strip()
            load_orders = data.get("load_orders", [])  # List of mod lists

            if not mod_name or not load_orders:
                raise ValidationError("Mod name and load orders required")

            # Perform batch analysis
            from deterministic_analysis import analyze_load_order_deterministic

            results = []
            for i, load_order in enumerate(load_orders):
                mod_list = load_order.split("\n") if isinstance(load_order, str) else load_order
                analysis = analyze_load_order_deterministic(mod_list, "skyrimse")
                results.append(
                    {
                        "load_order_name": f"Load Order {i + 1}",
                        "analysis": analysis,
                    }
                )

            if request.is_json:
                return jsonify({"success": True, "results": results})

            return render_template("mod_author/batch_test.html", results=results, mod_name=mod_name)

        except ValidationError as e:
            if request.is_json:
                return jsonify({"success": False, "error": str(e)}), 400
            return render_template("error.html", error=str(e))
        except Exception as e:
            logger.error(f"Batch test failed: {e}")
            return jsonify({"success": False, "error": "Internal error"}), 500

    return render_template("mod_author/batch_test.html", results=None, mod_name="")


# =============================================================================
# Webhook Management
# =============================================================================


@mod_author_bp.route("/api/webhooks", methods=["GET"])
def get_webhooks() -> Any:
    """Get all webhooks for user's mods."""
    if "user_email" not in session:
        raise AuthenticationError("Authentication required")

    try:
        from sqlalchemy import create_engine, inspect
        from sqlalchemy.orm import sessionmaker

        from models import ModWebhook

        # Check if webhooks table exists
        engine = create_engine("sqlite:///users.db")
        inspector = inspect(engine)

        if "mod_webhooks" not in inspector.get_table_names():
            return jsonify({"success": True, "webhooks": []})

        db_session = sessionmaker(bind=engine)()
        webhooks = (
            db_session.query(ModWebhook)
            .filter(ModWebhook.user_email == session["user_email"])
            .all()
        )

        return jsonify({"success": True, "webhooks": [webhook.to_dict() for webhook in webhooks]})

    except Exception as e:
        logger.error(f"Failed to get webhooks: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@mod_author_bp.route("/api/webhooks", methods=["POST"])
def create_webhook() -> Any:
    """Create a new webhook."""
    if "user_email" not in session:
        raise AuthenticationError("Authentication required")

    try:
        data = request.get_json()
        mod_name = data.get("mod_name", "").strip()
        game = data.get("game", "").strip()
        webhook_url = data.get("webhook_url", "").strip()
        events = data.get("events", [])

        if not mod_name or not game or not webhook_url:
            raise ValidationError("Mod name, game, and webhook URL required")

        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        from models import ModWebhook

        engine = create_engine("sqlite:///users.db")
        db_session = sessionmaker(bind=engine)()

        # Check if user is verified author
        from db import is_verified_mod_author

        if not is_verified_mod_author(session["user_email"], mod_name, game):
            raise ValidationError("You must be verified as author of this mod")

        webhook = ModWebhook(
            user_email=session["user_email"],
            mod_name=mod_name,
            game=game,
            webhook_url=webhook_url,
            events=json.dumps(events),
        )

        db_session.add(webhook)
        db_session.commit()

        return jsonify({"success": True, "webhook_id": webhook.id})

    except ValidationError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        logger.error(f"Failed to create webhook: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@mod_author_bp.route("/api/webhooks/<int:webhook_id>", methods=["DELETE"])
def delete_webhook(webhook_id: int) -> Any:
    """Delete a webhook."""
    if "user_email" not in session:
        raise AuthenticationError("Authentication required")

    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        from models import ModWebhook

        engine = create_engine("sqlite:///users.db")
        db_session = sessionmaker(bind=engine)()

        webhook = db_session.query(ModWebhook).filter_by(id=webhook_id).first()

        if not webhook or webhook.user_email != session["user_email"]:
            raise ValidationError("Webhook not found or not authorized")

        db_session.delete(webhook)
        db_session.commit()

        return jsonify({"success": True})

    except ValidationError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        logger.error(f"Failed to delete webhook: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500
