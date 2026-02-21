"""
SkyModderAI - Shopping/Advertising Blueprint

Business advertising with pay-per-click:
- First month FREE (automatic upon business approval)
- After first month: $5/1000 clicks ($0.005 per click)
- Prepaid credits: $50 = 10,000 clicks
- Automatic ad placement on directory and shopping pages
- Server-side click tracking with fraud protection
"""

from __future__ import annotations

from flask import Blueprint, flash, jsonify, redirect, render_template, request, session, url_for

from shopping_service import get_shopping_service

shopping_bp = Blueprint("shopping", __name__, url_prefix="/shopping")


@shopping_bp.route("/")
def shopping_home():
    """Shopping/Advertising home page with all ads."""
    shopping_service = get_shopping_service()

    # Get featured ads (top 6)
    featured_ads = shopping_service.get_featured_ads(limit=6)

    # Get all active ads for directory below
    all_ads = shopping_service.get_featured_ads(limit=20)

    # Pricing info
    pricing = {
        "first_month": "FREE",
        "cpm_rate": 5.00,  # $5 per 1,000 clicks
        "plan_clicks": 10000,
        "plan_price": 50.00,
        "cost_per_click": 0.005,
    }

    return render_template(
        "shopping/home.html",
        featured_ads=featured_ads,
        all_ads=all_ads,
        pricing=pricing,
    )


@shopping_bp.route("/ads")
def ads_directory():
    """Directory of all active ads."""
    shopping_service = get_shopping_service()

    # Get all active ads
    all_ads = shopping_service.get_featured_ads(limit=20)

    return render_template("shopping/ads_directory.html", ads=all_ads)


@shopping_bp.route("/click/<int:creative_id>")
def track_click(creative_id):
    """Track ad click and redirect to landing page."""
    shopping_service = get_shopping_service()

    # Get creative info
    creative = shopping_service._row_to_creative(
        shopping_service._get_db()
        .execute("SELECT * FROM ad_creatives WHERE id = ?", (creative_id,))
        .fetchone()
    )

    if not creative:
        return redirect(url_for("shopping.shopping_home"))

    # Get campaign info
    campaign = shopping_service.get_campaign(creative.campaign_id)
    if not campaign:
        return redirect(url_for("shopping.shopping_home"))

    # Record click
    is_valid, message, _ = shopping_service.record_click(
        creative_id=creative.id,
        campaign_id=campaign.id,
        business_id=campaign.business_id,
        user_id=session.get("user_email"),
        request=request,
    )

    # Record impression as well
    shopping_service.record_impression(
        creative_id=creative.id,
        campaign_id=campaign.id,
        business_id=campaign.business_id,
        placement="click_through",
        user_id=session.get("user_email"),
    )

    # Redirect to landing page
    return redirect(creative.landing_url)


@shopping_bp.route("/impression/<int:creative_id>")
def track_impression(creative_id):
    """Track ad impression (pixel tracking)."""
    shopping_service = get_shopping_service()

    # Get creative info
    db = shopping_service._get_db()
    row = db.execute("SELECT * FROM ad_creatives WHERE id = ?", (creative_id,)).fetchone()

    if row:
        creative = shopping_service._row_to_creative(row)
        campaign = shopping_service.get_campaign(creative.campaign_id)

        if campaign:
            shopping_service.record_impression(
                creative_id=creative.id,
                campaign_id=campaign.id,
                business_id=campaign.business_id,
                placement="pixel",
                user_id=session.get("user_email"),
            )

    # Return 1x1 transparent pixel
    from flask import Response

    return Response(
        b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\xff\xff\xff\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b",
        mimetype="image/gif",
        headers={"Cache-Control": "no-cache"},
    )


@shopping_bp.route("/dashboard")
def dashboard():
    """Business advertising dashboard."""
    if "user_email" not in session:
        return redirect(url_for("auth.login", next="/shopping/dashboard"))

    shopping_service = get_shopping_service()
    db = shopping_service._get_db()

    # Get user's business
    business = db.execute(
        "SELECT * FROM businesses WHERE owner_email = ?",
        (session["user_email"],),
    ).fetchone()

    if not business:
        flash("You need to register a business first.", "warning")
        return redirect(url_for("business.join"))

    # Get user's campaigns
    campaigns = shopping_service.get_campaigns_for_business(business["id"])

    # Get pricing info
    pricing = {
        "cpm_rate": 5.00,
        "plan_clicks": 10000,
        "plan_price": 50.00,
        "cost_per_click": 0.005,
    }

    return render_template(
        "shopping/dashboard.html",
        business=business,
        campaigns=campaigns,
        pricing=pricing,
    )


@shopping_bp.route("/campaign/create", methods=["GET", "POST"])
def create_campaign():
    """Create a new ad campaign."""
    if "user_email" not in session:
        return redirect(url_for("auth.login", next="/shopping/campaign/create"))

    shopping_service = get_shopping_service()
    db = shopping_service._get_db()

    # Get user's business
    business = db.execute(
        "SELECT * FROM businesses WHERE owner_email = ?",
        (session["user_email"],),
    ).fetchone()

    if not business:
        flash("You need to register a business first.", "warning")
        return redirect(url_for("business.join"))

    if request.method == "POST":
        # Check if business is eligible for first month free
        existing_campaigns = shopping_service.get_campaigns_for_business(business["id"])
        first_month_free = len(existing_campaigns) == 0  # First campaign is free

        # Create campaign
        campaign = shopping_service.create_campaign(
            business_id=business["id"],
            name=request.form.get("campaign_name", f"{business['name']} Campaign"),
            budget_type="prepaid",
            budget_amount=50.00 if not first_month_free else 0.00,
            first_month_free=first_month_free,
        )

        if campaign:
            flash(
                "Campaign created! "
                + ("First month is FREE!" if first_month_free else "Please add credits to start."),
                "success",
            )
            return redirect(url_for("shopping.create_creative", campaign_id=campaign.id))
        else:
            flash("Failed to create campaign.", "error")

    # Check eligibility for first month free
    existing_campaigns = shopping_service.get_campaigns_for_business(business["id"])
    first_month_free = len(existing_campaigns) == 0

    return render_template(
        "shopping/create_campaign.html",
        business=business,
        first_month_free=first_month_free,
    )


@shopping_bp.route("/campaign/<int:campaign_id>")
def view_campaign(campaign_id):
    """View campaign details."""
    if "user_email" not in session:
        return redirect(url_for("auth.login", next=f"/shopping/campaign/{campaign_id}"))

    shopping_service = get_shopping_service()
    campaign = shopping_service.get_campaign(campaign_id)

    if not campaign:
        flash("Campaign not found.", "error")
        return redirect(url_for("shopping.dashboard"))

    # Verify ownership
    db = shopping_service._get_db()
    business = db.execute(
        "SELECT * FROM businesses WHERE id = ?",
        (campaign.business_id,),
    ).fetchone()

    if not business or business.get("owner_email") != session["user_email"]:
        flash("You don't have permission to view this campaign.", "error")
        return redirect(url_for("shopping.dashboard"))

    # Get campaign stats
    stats = shopping_service.get_campaign_stats(campaign_id)

    # Get creatives
    creatives = shopping_service.get_creatives(campaign_id)

    return render_template(
        "shopping/campaign_detail.html",
        campaign=campaign,
        stats=stats,
        creatives=creatives,
    )


@shopping_bp.route("/campaign/<int:campaign_id>/creative", methods=["POST"])
def create_creative(campaign_id):
    """Create a new ad creative for a campaign."""
    if "user_email" not in session:
        return redirect(url_for("auth.login", next=f"/shopping/campaign/{campaign_id}/creative"))

    shopping_service = get_shopping_service()
    campaign = shopping_service.get_campaign(campaign_id)

    if not campaign:
        flash("Campaign not found.", "error")
        return redirect(url_for("shopping.dashboard"))

    # Verify ownership
    db = shopping_service._get_db()
    business = db.execute(
        "SELECT * FROM businesses WHERE id = ?",
        (campaign.business_id,),
    ).fetchone()

    if not business or business.get("owner_email") != session["user_email"]:
        flash("You don't have permission to modify this campaign.", "error")
        return redirect(url_for("shopping.dashboard"))

    if request.method == "POST":
        creative = shopping_service.create_creative(
            campaign_id=campaign_id,
            name=request.form.get("creative_name", "Ad Creative"),
            headline=request.form.get("headline", ""),
            landing_url=request.form.get("landing_url", business["website"]),
            image_url=request.form.get("image_url"),
            body_copy=request.form.get("body_copy"),
            cta_text=request.form.get("cta_text", "Learn More"),
        )

        if creative:
            flash("Ad creative created!", "success")
            return redirect(url_for("shopping.view_campaign", campaign_id=campaign_id))
        else:
            flash("Failed to create creative.", "error")

    return render_template(
        "shopping/create_creative.html",
        campaign=campaign,
        business=business,
    )


@shopping_bp.route("/campaign/<int:campaign_id>/pause", methods=["POST"])
def pause_campaign(campaign_id):
    """Pause a campaign."""
    if "user_email" not in session:
        return jsonify({"error": "Login required"}), 401

    shopping_service = get_shopping_service()
    success = shopping_service.update_campaign_status(campaign_id, "paused")

    if success:
        return jsonify({"success": True, "status": "paused"})
    else:
        return jsonify({"error": "Failed to pause campaign"}), 500


@shopping_bp.route("/campaign/<int:campaign_id>/activate", methods=["POST"])
def activate_campaign(campaign_id):
    """Activate a paused campaign."""
    if "user_email" not in session:
        return jsonify({"error": "Login required"}), 401

    shopping_service = get_shopping_service()
    success = shopping_service.update_campaign_status(campaign_id, "active")

    if success:
        return jsonify({"success": True, "status": "active"})
    else:
        return jsonify({"error": "Failed to activate campaign"}), 500


@shopping_bp.route("/campaign/<int:campaign_id>/add_credits", methods=["POST"])
def add_credits(campaign_id):
    """Add click credits to a campaign."""
    if "user_email" not in session:
        return jsonify({"error": "Login required"}), 401

    shopping_service = get_shopping_service()

    # Get amount from request
    data = request.get_json() or {}
    amount = float(data.get("amount", 50.00))

    success = shopping_service.add_click_credits(campaign_id, amount)

    if success:
        return jsonify(
            {
                "success": True,
                "message": f"Added ${amount:.2f} in credits ({int((amount / 5.00) * 1000)} clicks)",
            }
        )
    else:
        return jsonify({"error": "Failed to add credits"}), 500


@shopping_bp.route("/creative/<int:creative_id>/pause", methods=["POST"])
def pause_creative(creative_id):
    """Pause a creative."""
    if "user_email" not in session:
        return jsonify({"error": "Login required"}), 401

    shopping_service = get_shopping_service()
    success = shopping_service.update_creative_status(creative_id, "paused")

    if success:
        return jsonify({"success": True, "status": "paused"})
    else:
        return jsonify({"error": "Failed to pause creative"}), 500


@shopping_bp.route("/creative/<int:creative_id>/activate", methods=["POST"])
def activate_creative(creative_id):
    """Activate a paused creative."""
    if "user_email" not in session:
        return jsonify({"error": "Login required"}), 401

    shopping_service = get_shopping_service()
    success = shopping_service.update_creative_status(creative_id, "active")

    if success:
        return jsonify({"success": True, "status": "active"})
    else:
        return jsonify({"error": "Failed to activate creative"}), 500


# Helper functions


def get_pricing_info():
    """Get pricing information."""
    return {
        "first_month": "FREE",
        "cpm_rate": 5.00,  # $5 per 1,000 clicks
        "plan_clicks": 10000,
        "plan_price": 50.00,
        "cost_per_click": 0.005,
    }
