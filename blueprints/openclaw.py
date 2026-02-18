"""
SkyModderAI - OpenCLAW Blueprint

Handles OpenCLAW automation, sandbox operations, and plan execution.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from flask import Blueprint, current_app, jsonify, render_template, request, session

from exceptions import (
    AuthenticationError,
    AuthorizationError,
    InvalidGameIDError,
    PermissionDeniedError,
    PlanExecutionError,
    SafetyViolationError,
    ValidationError,
)
from logging_utils import get_request_id
from openclaw_engine import (
    OPENCLAW_PERMISSION_SCOPES,
    build_openclaw_plan,
    get_permission_descriptions,
    validate_permissions,
)
from security_utils import rate_limit, validate_game_id

if TYPE_CHECKING:
    from sqlite3 import Connection

logger = logging.getLogger(__name__)

# Create blueprint
openclaw_bp = Blueprint("openclaw", __name__, url_prefix="/openclaw")


def openclaw_enabled_check() -> bool:
    """Check if OpenCLAW is enabled."""
    import os

    return os.environ.get("SKYMODDERAI_OPENCLAW_ENABLED", "0").lower() in ("1", "true", "yes")


@openclaw_bp.route("/")
def openclaw_index() -> Any:
    """OpenCLAW dashboard."""
    if not openclaw_enabled_check():
        return render_template("error.html", error="OpenCLAW is not enabled"), 403

    if "user_email" not in session:
        return redirect(url_for("auth.login"))

    # Get user's OpenCLAW permissions
    from db import get_user_openclaw_permissions

    permissions = get_user_openclaw_permissions(session["user_email"])

    # Get permission descriptions
    perm_descriptions = get_permission_descriptions()

    return render_template(
        "openclaw.html",
        permissions=permissions,
        permission_descriptions=perm_descriptions,
        enabled=True,
    )


@openclaw_bp.route("/plan/propose", methods=["POST"])
@rate_limit(limit=5, window=60)  # 5 plans per minute
def propose_plan() -> Any:
    """
    Propose an OpenCLAW improvement plan.

    Request Body:
        {
            "game": "string",
            "objective": "string",
            "playstyle": "string" (optional)
        }
    """
    if not openclaw_enabled_check():
        raise AuthorizationError("OpenCLAW is not enabled")

    if "user_email" not in session:
        raise AuthenticationError()

    try:
        data = request.get_json()
        if not data:
            raise ValidationError("Request body required")

        game = data.get("game", "skyrimse")
        objective = data.get("objective", "")
        playstyle = data.get("playstyle", "balanced")

        if not objective:
            raise ValidationError("Objective is required")

        try:
            game = validate_game_id(game)
        except ValueError as e:
            raise InvalidGameIDError(str(e))

        # Check permissions
        from db import get_user_openclaw_permission

        if not get_user_openclaw_permission(session["user_email"], "launch_intents"):
            raise PermissionDeniedError("Plan proposal requires launch_intents permission")

        # Build plan
        plan = build_openclaw_plan(
            game=game,
            objective=objective,
            playstyle=playstyle,
            permissions={},  # Check actual permissions in validation
        )

        # Validate plan safety
        from openclaw_engine import validate_plan_safety

        is_safe, violations = validate_plan_safety(plan)
        if not is_safe:
            raise SafetyViolationError("Plan failed safety validation", details={"violations": violations})

        logger.info(
            f"OpenCLAW plan proposed: {plan.plan_id} by {session['user_email']}",
            extra={"request_id": get_request_id()},
        )

        return jsonify(
            {
                "success": True,
                "plan": plan.to_dict(),
                "message": "Plan proposed. Review and execute to apply changes.",
            }
        )

    except (ValidationError, InvalidGameIDError, PermissionDeniedError, SafetyViolationError) as e:
        raise e
    except Exception as e:
        logger.error(f"Plan proposal failed: {e}", extra={"request_id": get_request_id()})
        raise PlanExecutionError(str(e))


@openclaw_bp.route("/plan/execute", methods=["POST"])
@rate_limit(limit=3, window=300)  # 3 executions per 5 minutes
def execute_plan() -> Any:
    """
    Execute an OpenCLAW plan.

    Request Body:
        {
            "plan_id": "string"
        }
    """
    if not openclaw_enabled_check():
        raise AuthorizationError("OpenCLAW is not enabled")

    if "user_email" not in session:
        raise AuthenticationError()

    try:
        data = request.get_json()
        if not data:
            raise ValidationError("Request body required")

        plan_id = data.get("plan_id", "")
        if not plan_id:
            raise ValidationError("Plan ID required")

        # Get plan from database
        from db import get_openclaw_plan

        plan_record = get_openclaw_plan(plan_id)
        if not plan_record:
            raise ValidationError("Plan not found")
        if plan_record["user_email"] != session["user_email"]:
            raise PermissionDeniedError("Not your plan")

        # Check permissions
        from db import get_user_openclaw_permission

        if not get_user_openclaw_permission(session["user_email"], "write_sandbox_files"):
            raise PermissionDeniedError("Plan execution requires write_sandbox_files permission")

        # Execute plan
        from dev.openclaw import execute_plan as execute_openclaw_plan
        from db import get_db

        db = get_db()
        result = execute_openclaw_plan(
            db=db,
            plan_id=plan_id,
            user_email=session["user_email"],
        )

        logger.info(
            f"OpenCLAW plan executed: {plan_id} by {session['user_email']}",
            extra={"request_id": get_request_id()},
        )

        return jsonify(
            {
                "success": True,
                "result": result.to_dict(),
                "message": "Plan executed successfully",
            }
        )

    except (ValidationError, PermissionDeniedError) as e:
        raise e
    except Exception as e:
        logger.error(f"Plan execution failed: {e}", extra={"request_id": get_request_id()})
        raise PlanExecutionError(str(e))


@openclaw_bp.route("/permissions", methods=["GET", "POST"])
def manage_permissions() -> Any:
    """Get or grant OpenCLAW permissions."""
    if not openclaw_enabled_check():
        raise AuthorizationError("OpenCLAW is not enabled")

    if "user_email" not in session:
        raise AuthenticationError()

    if request.method == "GET":
        from db import get_user_openclaw_permissions

        permissions = get_user_openclaw_permissions(session["user_email"])
        return jsonify(
            {
                "success": True,
                "permissions": permissions,
                "available_scopes": list(OPENCLAW_PERMISSION_SCOPES.keys()),
            }
        )

    # POST: Grant permission
    try:
        data = request.get_json()
        if not data:
            raise ValidationError("Request body required")

        scope = data.get("scope", "")
        granted = data.get("granted", False)

        if scope not in OPENCLAW_PERMISSION_SCOPES:
            raise ValidationError(f"Invalid scope: {scope}")

        from db import set_user_openclaw_permission

        set_user_openclaw_permission(
            email=session["user_email"],
            scope=scope,
            granted=granted,
        )

        logger.info(
            f"OpenCLAW permission updated: {scope}={granted} for {session['user_email']}",
            extra={"request_id": get_request_id()},
        )

        return jsonify({"success": True, "message": "Permission updated"})

    except ValidationError as e:
        raise e
    except Exception as e:
        logger.error(f"Permission update failed: {e}", extra={"request_id": get_request_id()})
        raise ValidationError(str(e))


@openclaw_bp.route("/sandbox/info")
def sandbox_info() -> Any:
    """Get sandbox usage information."""
    if not openclaw_enabled_check():
        raise AuthorizationError("OpenCLAW is not enabled")

    if "user_email" not in session:
        raise AuthenticationError()

    try:
        from dev.openclaw import get_sandbox_info

        info = get_sandbox_info(session["user_email"])

        return jsonify(
            {
                "success": True,
                "sandbox": info,
            }
        )

    except Exception as e:
        logger.error(f"Sandbox info failed: {e}", extra={"request_id": get_request_id()})
        raise ValidationError(str(e))


@openclaw_bp.route("/loop/feedback", methods=["POST"])
@rate_limit(limit=5, window=300)
def submit_loop_feedback() -> Any:
    """
    Submit post-run feedback for the dev loop.

    Request Body:
        {
            "fps_avg": number (optional),
            "crashes": number (optional),
            "stutter_events": number (optional),
            "enjoyment_score": number (optional),
            "notes": "string" (optional)
        }
    """
    if "user_email" not in session:
        raise AuthenticationError()

    try:
        data = request.get_json()
        if not data:
            raise ValidationError("Request body required")

        from db import save_openclaw_feedback

        save_openclaw_feedback(
            email=session["user_email"],
            game=data.get("game", "skyrimse"),
            fps_avg=data.get("fps_avg"),
            crashes=data.get("crashes", 0),
            stutter_events=data.get("stutter_events", 0),
            enjoyment_score=data.get("enjoyment_score"),
            notes=data.get("notes", ""),
        )

        logger.info(
            f"OpenCLAW feedback submitted by {session['user_email']}",
            extra={"request_id": get_request_id()},
        )

        # Get loop suggestions
        from dev.openclaw import suggest_loop_adjustments

        suggestions = suggest_loop_adjustments(
            email=session["user_email"],
            fps_avg=data.get("fps_avg"),
            crashes=data.get("crashes", 0),
        )

        return jsonify(
            {
                "success": True,
                "message": "Feedback submitted",
                "suggestions": suggestions,
            }
        )

    except ValidationError as e:
        raise e
    except Exception as e:
        logger.error(f"Feedback submission failed: {e}", extra={"request_id": get_request_id()})
        raise ValidationError(str(e))


@openclaw_bp.route("/safety-status")
def safety_status() -> Any:
    """Get OpenCLAW safety status and hardening score."""
    if not openclaw_enabled_check():
        raise AuthorizationError("OpenCLAW is not enabled")

    try:
        from dev.openclaw import get_safety_status

        status = get_safety_status()

        return jsonify(
            {
                "success": True,
                "safety": status,
            }
        )

    except Exception as e:
        logger.error(f"Safety status check failed: {e}", extra={"request_id": get_request_id()})
        raise ValidationError(str(e))
