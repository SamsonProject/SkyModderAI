"""
SkyModderAI - Community Blueprint

Handles community posts, replies, voting, and reports.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from flask import Blueprint, jsonify, redirect, render_template, request, session, url_for

from exceptions import AuthenticationError, ValidationError
from logging_utils import get_request_id
from security_utils import rate_limit

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# Create blueprint
community_bp = Blueprint("community", __name__, url_prefix="/community")


@community_bp.route("/")
def community_index() -> Any:
    """Display community posts."""
    from db import get_community_posts

    posts = get_community_posts(limit=50)
    return render_template("community.html", posts=posts)


@community_bp.route("/post", methods=["POST"])
@rate_limit(limit=5, window=300)  # 5 posts per 5 minutes
def create_post() -> Any:
    """Create a new community post."""
    if "user_email" not in session:
        if request.is_json:
            raise AuthenticationError()
        return redirect(url_for("auth.login"))

    try:
        data = request.get_json() or request.form
        content = data.get("content", "").strip()
        tag = data.get("tag", "general")

        if not content:
            raise ValidationError("Post content is required")
        if len(content) > 5000:
            raise ValidationError("Post content too long (max 5000 characters)")

        from db import create_community_post

        post_id = create_community_post(
            email=session["user_email"],
            content=content,
            tag=tag,
        )

        logger.info(
            f"Community post created: {post_id} by {session['user_email']}",
            extra={"request_id": get_request_id()},
        )

        if request.is_json:
            return jsonify({"success": True, "post_id": post_id})

        return redirect(url_for("community.community_index"))

    except ValidationError as e:
        if request.is_json:
            return jsonify({"success": False, "error": str(e)}), 400
        return render_template("error.html", error=str(e)), 400


@community_bp.route("/post/<int:post_id>/reply", methods=["POST"])
@rate_limit(limit=10, window=300)  # 10 replies per 5 minutes
def create_reply(post_id: int) -> Any:
    """Create a reply to a post."""
    if "user_email" not in session:
        if request.is_json:
            raise AuthenticationError()
        return redirect(url_for("auth.login"))

    try:
        data = request.get_json() or request.form
        content = data.get("content", "").strip()

        if not content:
            raise ValidationError("Reply content is required")
        if len(content) > 2000:
            raise ValidationError("Reply content too long (max 2000 characters)")

        from db import create_community_reply

        reply_id = create_community_reply(
            post_id=post_id,
            email=session["user_email"],
            content=content,
        )

        logger.info(
            f"Community reply created: {reply_id} by {session['user_email']}",
            extra={"request_id": get_request_id()},
        )

        if request.is_json:
            return jsonify({"success": True, "reply_id": reply_id})

        return redirect(url_for("community.community_index"))

    except ValidationError as e:
        if request.is_json:
            return jsonify({"success": False, "error": str(e)}), 400
        return render_template("error.html", error=str(e)), 400


@community_bp.route("/post/<int:post_id>/vote", methods=["POST"])
def vote_post(post_id: int) -> Any:
    """Vote on a community post."""
    if "user_email" not in session:
        if request.is_json:
            raise AuthenticationError()
        return redirect(url_for("auth.login"))

    try:
        data = request.get_json() or request.form
        vote = int(data.get("vote", 0))

        if vote not in (-1, 0, 1):
            raise ValidationError("Vote must be -1, 0, or 1")

        from db import vote_community_post

        vote_community_post(
            post_id=post_id,
            email=session["user_email"],
            vote=vote,
        )

        if request.is_json:
            return jsonify({"success": True})

        return redirect(url_for("community.community_index"))

    except ValidationError as e:
        if request.is_json:
            return jsonify({"success": False, "error": str(e)}), 400
        return render_template("error.html", error=str(e)), 400


@community_bp.route("/post/<int:post_id>/report", methods=["POST"])
def report_post(post_id: int) -> Any:
    """Report a community post."""
    if "user_email" not in session:
        if request.is_json:
            raise AuthenticationError()
        return redirect(url_for("auth.login"))

    try:
        data = request.get_json() or request.form
        reason = data.get("reason", "").strip()

        if not reason:
            raise ValidationError("Reason is required")

        from db import create_community_report

        create_community_report(
            post_id=post_id,
            reporter_email=session["user_email"],
            reason=reason,
        )

        logger.info(
            f"Community post reported: {post_id} by {session['user_email']}",
            extra={"request_id": get_request_id()},
        )

        if request.is_json:
            return jsonify({"success": True, "message": "Report submitted"})

        return redirect(url_for("community.community_index"))

    except ValidationError as e:
        if request.is_json:
            return jsonify({"success": False, "error": str(e)}), 400
        return render_template("error.html", error=str(e)), 400


@community_bp.route("/health")
def community_health() -> Any:
    """Get community health metrics."""
    from db import get_community_stats

    stats = get_community_stats()
    return jsonify({"success": True, "stats": stats})
