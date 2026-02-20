"""
SkyModderAI - Sponsors Blueprint

Ethical, pay-per-click advertising system.
- $5 CPM (cost per 1,000 clicks)
- Simple meter charge (no packages)
- Server-side click tracking
- Fraud protection (IP+UA dedup, 24h window)
- Community-curated, democratic ranking
"""

from __future__ import annotations

from flask import Blueprint, redirect, render_template, request, session, url_for

from sponsor_service import get_sponsor_service

sponsors_bp = Blueprint("sponsors", __name__, url_prefix="/sponsors")


@sponsors_bp.route("/")
def sponsors_list():
    """Sponsor showcase page."""
    # Get ranked sponsors
    sponsor_service = get_sponsor_service()
    sponsors = sponsor_service.get_ranked_sponsors(limit=10)

    return render_template("sponsors/list.html", sponsors=sponsors, charter=get_sponsor_charter())


@sponsors_bp.route("/apply", methods=["GET", "POST"])
def apply():
    """Sponsor application form."""
    if request.method == "POST":
        # Process application
        data = request.form
        sponsor_service = get_sponsor_service()

        # Register sponsor (pending approval)
        sponsor = sponsor_service.register_sponsor(
            sponsor_id=data.get("company_id", "").lower().replace(" ", "_"),
            name=data.get("company_name", ""),
            logo_url=data.get("logo_url", ""),
            landing_url=data.get("landing_url", ""),
            description=data.get("description", ""),
            category=data.get("category", ""),
        )

        # Redirect to applied confirmation
        return redirect(url_for("sponsors.applied"))

    categories = get_sponsor_categories()
    return render_template("sponsors/apply.html", categories=categories, pricing=get_pricing_info())


@sponsors_bp.route("/applied")
def applied():
    """Application submitted confirmation."""
    return render_template("sponsors/applied.html")


@sponsors_bp.route("/dashboard")
def dashboard():
    """Sponsor dashboard (authenticated)."""
    if "user_email" not in session:
        return redirect(url_for("auth.login", next="/sponsors/dashboard"))

    # Will show sponsor metrics, clicks, spend
    return render_template("sponsors/dashboard.html", sponsor=None, metrics={}, billing={})


@sponsors_bp.route("/click/<sponsor_id>")
def track_click(sponsor_id):
    """Track sponsor click (server-side)."""
    sponsor_service = get_sponsor_service()

    # Record click with fraud protection
    is_valid, message = sponsor_service.record_click(
        sponsor_id=sponsor_id, user_id=session.get("user_email"), request=request
    )

    # Redirect to sponsor landing page
    sponsor = sponsor_service.get_sponsor(sponsor_id)
    if sponsor:
        return redirect(sponsor.landing_url)

    return redirect(url_for("sponsors.sponsors_list"))


@sponsors_bp.route("/charter")
def charter():
    """Sponsor ethical charter - full documentation."""
    return render_template("sponsors/charter.html")


# Helper functions


def get_sponsor_charter():
    """Get sponsor ethical charter."""
    from config_loader import get_config_loader

    config = get_config_loader()
    charter_path = config.config_dir / "sponsor_charter.yaml"
    return config._load_yaml(charter_path)


def get_sponsor_categories():
    """Get approved sponsor categories."""
    charter = get_sponsor_charter()
    return charter.get("accepted", [])


def get_pricing_info():
    """Get pricing information."""
    return {
        "cpm_rate": 5.00,  # $5 per 1,000 clicks
        "cost_per_click": 0.005,  # $0.005 per click
        "meter_model": True,  # Simple meter charge, no packages
    }
