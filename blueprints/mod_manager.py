"""
SkyModderAI - Mod Manager Integration

Download plugins for Mod Organizer 2, Vortex, and Wabbajack.
Export/import load orders directly to/from mod managers.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from flask import Blueprint, jsonify, render_template, request, send_file, url_for

from security_utils import rate_limit

logger = logging.getLogger(__name__)

# Create blueprint
mod_manager_bp = Blueprint("mod_manager", __name__, url_prefix="/mod-managers")


# =============================================================================
# Landing Page
# =============================================================================


@mod_manager_bp.route("/")
def index() -> Any:
    """Mod manager integration landing page."""
    return render_template(
        "mod_managers/index.html",
        managers=[
            {
                "id": "mo2",
                "name": "Mod Organizer 2",
                "description": "Popular mod manager with virtual file system",
                "icon": "🔧",
                "download_url": "/mod-managers/mo2/download",
                "install_guide": "/mod-managers/mo2/install",
                "features": [
                    "One-click analysis from within MO2",
                    "Automatic load order sync",
                    "Conflict detection in real-time",
                    "Profile sharing",
                ],
            },
            {
                "id": "vortex",
                "name": "Vortex",
                "description": "Nexus Mods' official mod manager",
                "icon": "🌀",
                "download_url": "/mod-managers/vortex/download",
                "install_guide": "/mod-managers/vortex/install",
                "features": [
                    "Integration with Nexus Mods",
                    "Automated conflict resolution",
                    "Cloud saves support",
                    "Extension-based architecture",
                ],
            },
            {
                "id": "wabbajack",
                "name": "Wabbajack",
                "description": "Automated mod list installer",
                "icon": "🎩",
                "download_url": "/mod-managers/wabbajack/download",
                "install_guide": "/mod-managers/wabbajack/install",
                "features": [
                    "Curated mod lists",
                    "Automated installation",
                    "Community-built lists",
                    "Version control",
                ],
            },
        ],
    )


# =============================================================================
# Mod Organizer 2 Routes
# =============================================================================


@mod_manager_bp.route("/mo2/download")
@rate_limit("api")
def mo2_download() -> Any:
    """Download MO2 plugin."""
    # Generate plugin file
    plugin_content = generate_mo2_plugin()

    return send_file(
        plugin_content,
        mimetype="application/zip",
        as_attachment=True,
        download_name="skymodderai-mo2-plugin.zip",
    )


@mod_manager_bp.route("/mo2/install")
def mo2_install() -> Any:
    """MO2 installation guide."""
    return render_template(
        "mod_managers/mo2_install.html",
        steps=[
            {
                "title": "Download the Plugin",
                "description": "Click the download button to get the plugin package.",
                "icon": "📥",
            },
            {
                "title": "Extract to MO2 Plugins",
                "description": "Extract the ZIP to your Mod Organizer 2/plugins/ folder.",
                "icon": "📁",
            },
            {
                "title": "Enable in MO2",
                "description": "Open MO2, go to Tools > Settings > Plugins, and enable SkyModderAI.",
                "icon": "✅",
            },
            {
                "title": "Configure API Key",
                "description": "Enter your SkyModderAI API key in the plugin settings.",
                "icon": "🔑",
            },
            {
                "title": "Start Analyzing",
                "description": "Right-click your mod list and select 'Analyze with SkyModderAI'.",
                "icon": "🚀",
            },
        ],
    )


@mod_manager_bp.route("/mo2/api/export", methods=["POST"])
@rate_limit("api")
def mo2_export() -> Any:
    """Export load order from MO2."""
    data = request.get_json()

    if not data:
        return jsonify({"success": False, "error": "No data provided"}), 400

    mod_list = data.get("mod_list", [])
    game = data.get("game", "skyrimse")

    # Validate mod list
    if not isinstance(mod_list, list):
        return jsonify({"success": False, "error": "Mod list must be an array"}), 400

    # Format for SkyModderAI
    formatted_list = "\n".join([f"*{mod}" if mod.endswith(".esp") else mod for mod in mod_list])

    return jsonify(
        {
            "success": True,
            "formatted_list": formatted_list,
            "game": game,
            "mod_count": len(mod_list),
        }
    )


@mod_manager_bp.route("/mo2/api/import", methods=["POST"])
@rate_limit("api")
def mo2_import() -> Any:
    """Import load order to MO2."""
    data = request.get_json()

    if not data:
        return jsonify({"success": False, "error": "No data provided"}), 400

    load_order = data.get("load_order", [])

    if not isinstance(load_order, list):
        return jsonify({"success": False, "error": "Load order must be an array"}), 400

    # In a real implementation, this would write to MO2's loadorder.txt
    return jsonify(
        {
            "success": True,
            "message": f"Imported {len(load_order)} mods to MO2 load order",
            "load_order": load_order,
        }
    )


# =============================================================================
# Vortex Routes
# =============================================================================


@mod_manager_bp.route("/vortex/download")
@rate_limit("api")
def vortex_download() -> Any:
    """Download Vortex extension."""
    extension_content = generate_vortex_extension()

    return send_file(
        extension_content,
        mimetype="application/zip",
        as_attachment=True,
        download_name="skymodderai-vortex-extension.zip",
    )


@mod_manager_bp.route("/vortex/install")
def vortex_install() -> Any:
    """Vortex installation guide."""
    return render_template(
        "mod_managers/vortex_install.html",
        steps=[
            {
                "title": "Download the Extension",
                "description": "Click the download button to get the extension package.",
                "icon": "📥",
            },
            {
                "title": "Open Vortex Extensions",
                "description": "In Vortex, go to Settings > Extensions > Install from file.",
                "icon": "🔌",
            },
            {
                "title": "Install Extension",
                "description": "Select the downloaded ZIP file and confirm installation.",
                "icon": "✅",
            },
            {
                "title": "Enable Extension",
                "description": "Toggle the SkyModderAI extension to enabled.",
                "icon": "⚡",
            },
            {
                "title": "Connect Account",
                "description": "Link your SkyModderAI account in the extension settings.",
                "icon": "🔗",
            },
        ],
    )


# =============================================================================
# Wabbajack Routes
# =============================================================================


@mod_manager_bp.route("/wabbajack/download")
@rate_limit("api")
def wabbajack_download() -> Any:
    """Download Wabbajack integration."""
    integration_content = generate_wabbajack_integration()

    return send_file(
        integration_content,
        mimetype="application/zip",
        as_attachment=True,
        download_name="skymodderai-wabbajack-integration.zip",
    )


@mod_manager_bp.route("/wabbajack/install")
def wabbajack_install() -> Any:
    """Wabbajack installation guide."""
    return render_template(
        "mod_managers/wabbajack_install.html",
        steps=[
            {
                "title": "Download Integration",
                "description": "Download the SkyModderAI integration package.",
                "icon": "📥",
            },
            {
                "title": "Add to Wabbajack",
                "description": "Place files in your Wabbajack/tools/SkyModderAI/ folder.",
                "icon": "📁",
            },
            {
                "title": "Configure in wabbajack.json",
                "description": "Add SkyModderAI validation step to your mod list config.",
                "icon": "⚙️",
            },
            {
                "title": "Validate Before Build",
                "description": "Run compatibility check before installing mod list.",
                "icon": "✓",
            },
        ],
    )


# =============================================================================
# API Endpoints
# =============================================================================


@mod_manager_bp.route("/api/v1/export/<manager>", methods=["POST"])
@rate_limit("api")
def export_to_manager(manager: str) -> Any:
    """Universal export endpoint for all managers."""
    data = request.get_json()

    if not data:
        return jsonify({"success": False, "error": "No data provided"}), 400

    mod_list = data.get("mod_list", [])
    game = data.get("game", "skyrimse")

    if manager == "mo2":
        export_data = format_for_mo2(mod_list, game)
    elif manager == "vortex":
        export_data = format_for_vortex(mod_list, game)
    elif manager == "wabbajack":
        export_data = format_for_wabbajack(mod_list, game)
    else:
        return jsonify({"success": False, "error": f"Unknown manager: {manager}"}), 400

    return jsonify({"success": True, "data": export_data})


@mod_manager_bp.route("/api/v1/import/<manager>", methods=["POST"])
@rate_limit("api")
def import_from_manager(manager: str) -> Any:
    """Universal import endpoint for all managers."""
    data = request.get_json()

    if not data:
        return jsonify({"success": False, "error": "No data provided"}), 400

    if manager == "mo2":
        mod_list = parse_mo2_export(data)
    elif manager == "vortex":
        mod_list = parse_vortex_export(data)
    elif manager == "wabbajack":
        mod_list = parse_wabbajack_export(data)
    else:
        return jsonify({"success": False, "error": f"Unknown manager: {manager}"}), 400

    return jsonify({"success": True, "mod_list": mod_list, "count": len(mod_list)})


# =============================================================================
# Helper Functions
# =============================================================================


def generate_mo2_plugin() -> bytes:
    """Generate MO2 plugin package."""
    # In production, this would create a real ZIP file
    import io

    buffer = io.BytesIO()
    buffer.write(b"MO2 Plugin Placeholder - Implement ZIP generation")
    buffer.seek(0)
    return buffer


def generate_vortex_extension() -> bytes:
    """Generate Vortex extension package."""
    import io

    buffer = io.BytesIO()
    buffer.write(b"Vortex Extension Placeholder - Implement ZIP generation")
    buffer.seek(0)
    return buffer


def generate_wabbajack_integration() -> bytes:
    """Generate Wabbajack integration package."""
    import io

    buffer = io.BytesIO()
    buffer.write(b"Wabbajack Integration Placeholder - Implement ZIP generation")
    buffer.seek(0)
    return buffer


def format_for_mo2(mod_list: list, game: str) -> dict:
    """Format mod list for MO2."""
    return {
        "format": "mo2",
        "game": game,
        "mods": mod_list,
        "load_order": [mod for mod in mod_list if mod.endswith((".esp", ".esm", ".esl"))],
    }


def format_for_vortex(mod_list: list, game: str) -> dict:
    """Format mod list for Vortex."""
    return {
        "format": "vortex",
        "game": game,
        "mods": mod_list,
        "deployment_order": list(enumerate(mod_list)),
    }


def format_for_wabbajack(mod_list: list, game: str) -> dict:
    """Format mod list for Wabbajack."""
    return {
        "format": "wabbajack",
        "game": game,
        "all_mods": mod_list,
        "prioritized_mods": mod_list,
    }


def parse_mo2_export(data: dict) -> list:
    """Parse MO2 export format."""
    return data.get("mods", [])


def parse_vortex_export(data: dict) -> list:
    """Parse Vortex export format."""
    return data.get("mods", [])


def parse_wabbajack_export(data: dict) -> list:
    """Parse Wabbajack export format."""
    return data.get("all_mods", [])


# =============================================================================
# Register Blueprint
# =============================================================================


def init_app(app):
    """Register the blueprint with the Flask app."""
    app.register_blueprint(mod_manager_bp)
