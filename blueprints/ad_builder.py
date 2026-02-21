"""
SkyModderAI - Ad Builder Blueprint

The People's Ad Tool - Free, powerful, accessible advertising creation.

Routes:
- /ad-builder/ — Home/editor (guest or account)
- /ad-builder/templates — Template library
- /ad-builder/templates/<id> — Template detail + customize
- /ad-builder/designs — User's designs (account only)
- /ad-builder/designs/<id> — Edit design
- /ad-builder/brand-kits — Brand kit management
- /ad-builder/export/<id> — Export design
- /ad-builder/api/* — API endpoints

Guest Access:
- Guests can create and edit designs
- Designs saved to session (7-day expiry)
- Export includes watermark
- Account required to save designs permanently
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from flask import (
    Blueprint,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)

from ad_builder_service import AdDesign, get_ad_builder_service

logger = logging.getLogger(__name__)

# Create blueprint
ad_builder_bp = Blueprint("ad_builder", __name__, url_prefix="/ad-builder")


# =============================================================================
# Main Editor
# =============================================================================


@ad_builder_bp.route("/")
def editor_home():
    """
    Ad Builder home/editor.

    Accessible to guests and authenticated users.
    Guests get a session ID for saving designs temporarily.
    """
    # Check if user is authenticated
    user_email = session.get("user_email")

    # Check if user has a guest session
    guest_session_id = session.get("ad_builder_guest_session")

    if not user_email and not guest_session_id:
        # Create new guest session
        service = get_ad_builder_service()
        guest_session_id = service.create_guest_session()
        session["ad_builder_guest_session"] = guest_session_id

    # Get user's designs if authenticated
    designs = []
    if user_email:
        service = get_ad_builder_service()
        designs = service.get_user_designs(user_email, limit=10)

    # Get popular templates
    service = get_ad_builder_service()
    templates = service.get_templates(limit=12)

    return render_template(
        "ad_builder/home.html",
        user_email=user_email,
        guest_session_id=guest_session_id,
        designs=designs,
        templates=templates,
    )


@ad_builder_bp.route("/editor/new")
def new_design():
    """
    Start a new design (blank canvas).

    Query params:
    - format: Format type (instagram_post, flyer_a4, etc.)
    - width: Custom width (optional)
    - height: Custom height (optional)
    """
    format_type = request.args.get("format", "custom")
    width = request.args.get("width", 1080, type=int)
    height = request.args.get("height", 1080, type=int)

    # Set dimensions based on format
    format_dimensions = {
        "instagram_post": (1080, 1080),
        "instagram_story": (1080, 1920),
        "facebook_post": (1200, 630),
        "twitter_post": (1200, 675),
        "pinterest_pin": (1000, 1500),
        "flyer_a4": (2480, 3508),
        "business_card": (1050, 600),
        "youtube_thumbnail": (1280, 720),
    }

    if format_type in format_dimensions:
        width, height = format_dimensions[format_type]

    return render_template(
        "ad_builder/editor.html",
        design=None,
        width=width,
        height=height,
        format_type=format_type,
    )


@ad_builder_bp.route("/editor/<design_id>")
def edit_design(design_id: str):
    """
    Edit existing design.

    Accessible to:
    - Owner (authenticated)
    - Guest who created it (session match)
    """
    service = get_ad_builder_service()
    design = service.get_design(design_id)

    if not design:
        flash("Design not found", "error")
        return redirect(url_for("ad_builder.editor_home"))

    user_email = session.get("user_email")
    guest_session_id = session.get("ad_builder_guest_session")

    # Check ownership
    if design.user_id and design.user_id != user_email:
        flash("You don't have permission to edit this design", "error")
        return redirect(url_for("ad_builder.editor_home"))

    if design.guest_session_id and design.guest_session_id != guest_session_id:
        flash("This design was created in another session", "error")
        return redirect(url_for("ad_builder.editor_home"))

    return render_template(
        "ad_builder/editor.html",
        mode="edit",
        design=design,
        format_type=design.format_type,
        width=design.width,
        height=design.height,
        user_email=user_email,
        guest_session_id=guest_session_id,
    )


# =============================================================================
# Templates
# =============================================================================


@ad_builder_bp.route("/templates")
def templates_library():
    """Template library with filters."""
    category = request.args.get("category")
    format_type = request.args.get("format")
    tags = request.args.get("tags", "").split(",") if request.args.get("tags") else None

    service = get_ad_builder_service()
    templates = service.get_templates(
        category=category,
        format_type=format_type,
        tags=tags,
        limit=50,
    )

    # Get format categories for filter UI
    format_categories = {
        "social": "Social Media",
        "display": "Digital Ads",
        "print": "Print",
        "video": "Video",
    }

    return render_template(
        "ad_builder/templates.html",
        templates=templates,
        format_categories=format_categories,
        selected_category=category,
        selected_format=format_type,
    )


@ad_builder_bp.route("/templates/<template_id>")
def template_detail(template_id: str):
    """Template detail page with preview."""
    service = get_ad_builder_service()
    template = service.get_template(template_id)

    if not template:
        flash("Template not found", "error")
        return redirect(url_for("ad_builder.templates_library"))

    # Get related templates
    related = service.get_templates(category=template.category, limit=6)

    return render_template(
        "ad_builder/template_detail.html",
        template=template,
        related_templates=related,
    )


@ad_builder_bp.route("/templates/<template_id>/use", methods=["POST"])
def use_template(template_id: str):
    """Create design from template."""
    service = get_ad_builder_service()
    template = service.get_template(template_id)

    if not template:
        return jsonify({"error": "Template not found"}), 404

    user_email = session.get("user_email")
    guest_session_id = session.get("ad_builder_guest_session")

    # Create design from template
    design = service.create_design(
        name=f"{template.name} (Copy)",
        design_data=template.template_data,
        user_id=user_email,
        guest_session_id=guest_session_id,
        template_id=template_id,
        format_type=template.format_type,
    )

    if design:
        # Increment template download count
        service.increment_template_download(template_id)

        return jsonify(
            {
                "success": True,
                "design_id": design.id,
                "redirect": url_for("ad_builder.edit_design", design_id=design.id),
            }
        )
    else:
        return jsonify({"error": "Failed to create design"}), 500


# =============================================================================
# Design Management
# =============================================================================


@ad_builder_bp.route("/designs")
def designs_list():
    """User's designs (account only)."""
    user_email = session.get("user_email")

    if not user_email:
        flash("Please log in to view your designs", "warning")
        return redirect(url_for("ad_builder.editor_home"))

    service = get_ad_builder_service()
    designs = service.get_user_designs(user_email, limit=50)

    return render_template(
        "ad_builder/designs.html",
        designs=designs,
    )


@ad_builder_bp.route("/designs/<design_id>/save", methods=["POST"])
def save_design(design_id: str):
    """Save design updates."""
    user_email = session.get("user_email")

    if not user_email:
        return jsonify({"error": "Authentication required"}), 401

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    service = get_ad_builder_service()

    # Verify ownership
    design = service.get_design(design_id)
    if not design or design.user_id != user_email:
        return jsonify({"error": "Design not found"}), 404

    # Update design
    updates = {
        "name": data.get("name"),
        "design_data": data.get("design_data"),
        "status": data.get("status"),
    }

    if service.update_design(design_id, updates):
        return jsonify({"success": True})
    else:
        return jsonify({"error": "Failed to save design"}), 500


@ad_builder_bp.route("/designs/<design_id>/delete", methods=["POST"])
def delete_design(design_id: str):
    """Delete a design."""
    user_email = session.get("user_email")

    if not user_email:
        return jsonify({"error": "Authentication required"}), 401

    service = get_ad_builder_service()

    # Verify ownership
    design = service.get_design(design_id)
    if not design or design.user_id != user_email:
        return jsonify({"error": "Design not found"}), 404

    if service.delete_design(design_id):
        return jsonify({"success": True})
    else:
        return jsonify({"error": "Failed to delete design"}), 500


@ad_builder_bp.route("/designs/<design_id>/duplicate", methods=["POST"])
def duplicate_design(design_id: str):
    """Duplicate a design."""
    user_email = session.get("user_email")

    if not user_email:
        return jsonify({"error": "Authentication required"}), 401

    service = get_ad_builder_service()

    # Get original design
    design = service.get_design(design_id)
    if not design or design.user_id != user_email:
        return jsonify({"error": "Design not found"}), 404

    # Create duplicate
    new_design = service.create_design(
        name=f"{design.name} (Copy)",
        design_data=design.design_data.copy(),
        user_id=user_email,
        template_id=design.template_id,
        format_type=design.format_type,
        width=design.width,
        height=design.height,
    )

    if new_design:
        return jsonify(
            {
                "success": True,
                "design_id": new_design.id,
                "redirect": url_for("ad_builder.edit_design", design_id=new_design.id),
            }
        )
    else:
        return jsonify({"error": "Failed to duplicate design"}), 500


@ad_builder_bp.route("/designs/<design_id>/resize", methods=["POST"])
def resize_design(design_id: str):
    """Resize design to new format."""
    user_email = session.get("user_email")

    if not user_email:
        return jsonify({"error": "Authentication required"}), 401

    data = request.get_json()
    target_format = data.get("format") if data else None

    if not target_format:
        return jsonify({"error": "Target format required"}), 400

    service = get_ad_builder_service()

    # Verify ownership
    design = service.get_design(design_id)
    if not design or design.user_id != user_email:
        return jsonify({"error": "Design not found"}), 404

    # Resize
    new_design = service.resize_design(design_id, target_format)

    if new_design:
        return jsonify(
            {
                "success": True,
                "design_id": new_design.id,
                "redirect": url_for("ad_builder.edit_design", design_id=new_design.id),
            }
        )
    else:
        return jsonify({"error": "Failed to resize design"}), 500


# =============================================================================
# Export
# =============================================================================


@ad_builder_bp.route("/export/<design_id>")
def export_design(design_id: str):
    """Export design to file."""
    format = request.args.get("format", "png")
    quality = request.args.get("quality", 90, type=int)

    user_email = session.get("user_email")
    guest_session_id = session.get("ad_builder_guest_session")

    service = get_ad_builder_service()
    design = service.get_design(design_id)

    if not design:
        flash("Design not found", "error")
        return redirect(url_for("ad_builder.editor_home"))

    # Check ownership (user or guest)
    if design.user_id and design.user_id != user_email:
        flash("You don't have permission to export this design", "error")
        return redirect(url_for("ad_builder.editor_home"))

    if design.guest_session_id and design.guest_session_id != guest_session_id:
        flash("This design was created in another session", "error")
        return redirect(url_for("ad_builder.editor_home"))

    # Determine if watermark is needed
    watermark = not user_email  # Guests get watermarked exports

    # Export
    file_data = service.export_design(
        design_id=design_id,
        format=format,
        quality=quality,
        watermark=watermark,
    )

    if file_data:
        # Send file
        filename = f"{design.name.replace(' ', '_')}.{format}"
        return send_file(
            file_data,
            mimetype=f"image/{format}",
            as_attachment=True,
            download_name=filename,
        )
    else:
        flash("Export failed", "error")
        return redirect(url_for("ad_builder.edit_design", design_id=design_id))


# =============================================================================
# Brand Kits
# =============================================================================


@ad_builder_bp.route("/brand-kits")
def brand_kits():
    """User's brand kits (account only)."""
    user_email = session.get("user_email")

    if not user_email:
        flash("Please log in to manage brand kits", "warning")
        return redirect(url_for("ad_builder.editor_home"))

    service = get_ad_builder_service()
    brand_kits = service.get_user_brand_kits(user_email)

    return render_template(
        "ad_builder/brand_kits.html",
        brand_kits=brand_kits,
    )


@ad_builder_bp.route("/brand-kits/create", methods=["POST"])
def create_brand_kit():
    """Create a new brand kit."""
    user_email = session.get("user_email")

    if not user_email:
        return jsonify({"error": "Authentication required"}), 401

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    service = get_ad_builder_service()
    brand_kit = service.create_brand_kit(user_email, data)

    if brand_kit:
        return jsonify(
            {
                "success": True,
                "brand_kit": brand_kit.to_dict(),
            }
        )
    else:
        return jsonify({"error": "Failed to create brand kit"}), 500


@ad_builder_bp.route("/brand-kits/<brand_kit_id>", methods=["PUT"])
def update_brand_kit(brand_kit_id: str):
    """Update a brand kit."""
    user_email = session.get("user_email")

    if not user_email:
        return jsonify({"error": "Authentication required"}), 401

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    service = get_ad_builder_service()

    if service.update_brand_kit(brand_kit_id, user_email, data):
        return jsonify({"success": True})
    else:
        return jsonify({"error": "Failed to update brand kit"}), 500


@ad_builder_bp.route("/brand-kits/<brand_kit_id>", methods=["DELETE"])
def delete_brand_kit(brand_kit_id: str):
    """Delete a brand kit."""
    user_email = session.get("user_email")

    if not user_email:
        return jsonify({"error": "Authentication required"}), 401

    service = get_ad_builder_service()

    if service.delete_brand_kit(brand_kit_id, user_email):
        return jsonify({"success": True})
    else:
        return jsonify({"error": "Failed to delete brand kit"}), 500


# =============================================================================
# API Endpoints (for frontend canvas editor)
# =============================================================================


@ad_builder_bp.route("/api/designs", methods=["POST"])
def api_create_design():
    """API: Create a new design."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    user_email = session.get("user_email")
    guest_session_id = session.get("ad_builder_guest_session")

    service = get_ad_builder_service()
    design = service.create_design(
        name=data.get("name", "Untitled Design"),
        design_data=data.get("design_data", {}),
        user_id=user_email,
        guest_session_id=guest_session_id,
        format_type=data.get("format_type", "custom"),
        width=data.get("width"),
        height=data.get("height"),
    )

    if design:
        return jsonify({"success": True, "design": design.to_dict()})
    else:
        return jsonify({"error": "Failed to create design"}), 500


@ad_builder_bp.route("/api/designs/<design_id>", methods=["GET"])
def api_get_design(design_id: str):
    """API: Get a design."""
    service = get_ad_builder_service()
    design = service.get_design(design_id)

    if design:
        return jsonify({"success": True, "design": design.to_dict()})
    else:
        return jsonify({"error": "Design not found"}), 404


@ad_builder_bp.route("/api/designs/<design_id>", methods=["PUT"])
def api_update_design(design_id: str):
    """API: Update a design."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    service = get_ad_builder_service()

    if service.update_design(design_id, data):
        return jsonify({"success": True})
    else:
        return jsonify({"error": "Failed to update design"}), 500


@ad_builder_bp.route("/api/formats")
def api_get_formats():
    """API: Get all available formats."""
    service = get_ad_builder_service()

    formats = []
    for format_type, (width, height) in service.FORMAT_SIZES.items():
        formats.append(
            {
                "type": format_type,
                "width": width,
                "height": height,
                "category": service.FORMAT_CATEGORIES.get(format_type, "custom"),
            }
        )

    return jsonify({"success": True, "formats": formats})


@ad_builder_bp.route("/api/templates")
def api_get_templates():
    """API: Get templates with filters."""
    category = request.args.get("category")
    format_type = request.args.get("format")

    service = get_ad_builder_service()
    templates = service.get_templates(
        category=category,
        format_type=format_type,
        limit=100,
    )

    return jsonify(
        {
            "success": True,
            "templates": [t.to_dict() for t in templates],
        }
    )
