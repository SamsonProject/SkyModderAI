"""
SkyModderAI - Sponsors Blueprint (DEPRECATED)

⚠️  DEPRECATED: This blueprint is being phased out.
Use /shopping instead for all advertising functionality.

Redirects:
- /sponsors/ → /shopping/
- /sponsors/apply → /shopping/apply
- /sponsors/charter → /shopping/charter
- /sponsors/click/<id> → /shopping/click/<id>

This file will be removed after full migration.
"""

from __future__ import annotations

from flask import Blueprint, redirect, url_for

sponsors_bp = Blueprint("sponsors", __name__, url_prefix="/sponsors")


@sponsors_bp.route("/")
def sponsors_list():
    """Redirect to shopping home."""
    return redirect(url_for("shopping.shopping_home"))


@sponsors_bp.route("/apply", methods=["GET", "POST"])
def apply():
    """Redirect to shopping apply."""
    return redirect(url_for("shopping.shopping_home"))


@sponsors_bp.route("/applied")
def applied():
    """Redirect to shopping applied."""
    return redirect(url_for("shopping.shopping_home"))


@sponsors_bp.route("/dashboard")
def dashboard():
    """Redirect to shopping dashboard."""
    return redirect(url_for("shopping.shopping_home"))


@sponsors_bp.route("/click/<sponsor_id>")
def track_click(sponsor_id):
    """Redirect to shopping click tracking."""
    return redirect(url_for("shopping.shopping_home"))


@sponsors_bp.route("/charter")
def charter():
    """Redirect to shopping charter."""
    return redirect(url_for("shopping.shopping_home"))
