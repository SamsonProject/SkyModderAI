"""
SkyModderAI - Export Blueprint

Export endpoints:
- POST /api/export/pdf - Export guide as PDF
- POST /api/export/html - Export guide as HTML
- POST /api/export/latex - Export guide as LaTeX
- GET /api/export/templates - Get available templates
"""

from __future__ import annotations

import logging
import os
import tempfile
from datetime import datetime
from typing import Any

from flask import Blueprint, jsonify, request, send_file

logger = logging.getLogger(__name__)

# Create blueprint
export_bp = Blueprint("export", __name__, url_prefix="/api/export")


@export_bp.route("/pdf", methods=["POST"])
def export_pdf():
    """
    Export guide as PDF.

    Request JSON:
    {
        "title": "My Modding Guide",
        "summary": "Executive summary...",
        "sections": [...],
        "warnings": [...],
        "recommendations": [...],
        "sources": [...]
    }

    Returns: PDF file download
    """
    try:
        data = request.get_json() or {}

        if not data.get("title"):
            return jsonify({"error": "Guide title is required"}), 400

        # Generate PDF
        from presentation_service import create_guide_content, format_as_pdf

        content = create_guide_content(
            title=data.get("title", "SkyModderAI Guide"),
            summary=data.get("summary", ""),
            sections=data.get("sections", []),
            warnings=data.get("warnings", []),
            recommendations=data.get("recommendations", []),
            sources=data.get("sources", []),
        )

        # Create temp file
        fd, temp_path = tempfile.mkstemp(suffix=".pdf")
        os.close(fd)

        # Generate PDF
        success = format_as_pdf(content, temp_path)

        if not success:
            # Fallback: return HTML instead
            return (
                jsonify(
                    {
                        "error": "PDF generation not available (WeasyPrint not installed)",
                        "fallback": "html",
                    }
                ),
                503,
            )

        # Send file
        filename = f"{data.get('title', 'guide').replace(' ', '_').lower()}_{datetime.now().strftime('%Y%m%d')}.pdf"

        return send_file(
            temp_path, mimetype="application/pdf", as_attachment=True, download_name=filename
        )

    except Exception as e:
        logger.exception("PDF export failed")
        return jsonify({"error": f"Export failed: {str(e)}"}), 500


@export_bp.route("/html", methods=["POST"])
def export_html():
    """
    Export guide as HTML.

    Request JSON: Same as PDF export

    Returns: HTML file download
    """
    try:
        data = request.get_json() or {}

        if not data.get("title"):
            return jsonify({"error": "Guide title is required"}), 400

        # Generate HTML
        from presentation_service import create_guide_content, format_as_html

        content = create_guide_content(
            title=data.get("title", "SkyModderAI Guide"),
            summary=data.get("summary", ""),
            sections=data.get("sections", []),
            warnings=data.get("warnings", []),
            recommendations=data.get("recommendations", []),
            sources=data.get("sources", []),
        )

        html_content = format_as_html(content)

        # Create temp file
        fd, temp_path = tempfile.mkstemp(suffix=".html")
        os.close(fd)

        with open(temp_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        # Send file
        filename = f"{data.get('title', 'guide').replace(' ', '_').lower()}_{datetime.now().strftime('%Y%m%d')}.html"

        return send_file(
            temp_path, mimetype="text/html", as_attachment=True, download_name=filename
        )

    except Exception as e:
        logger.exception("HTML export failed")
        return jsonify({"error": f"Export failed: {str(e)}"}), 500


@export_bp.route("/latex", methods=["POST"])
def export_latex():
    """
    Export guide as LaTeX source.

    Request JSON: Same as PDF export

    Returns: LaTeX .tex file download
    """
    try:
        data = request.get_json() or {}

        if not data.get("title"):
            return jsonify({"error": "Guide title is required"}), 400

        # Generate LaTeX
        from presentation_service import create_guide_content, format_as_latex

        content = create_guide_content(
            title=data.get("title", "SkyModderAI Guide"),
            summary=data.get("summary", ""),
            sections=data.get("sections", []),
            warnings=data.get("warnings", []),
            recommendations=data.get("recommendations", []),
            sources=data.get("sources", []),
        )

        latex_content = format_as_latex(content)

        # Create temp file
        fd, temp_path = tempfile.mkstemp(suffix=".tex")
        os.close(fd)

        with open(temp_path, "w", encoding="utf-8") as f:
            f.write(latex_content)

        # Send file
        filename = f"{data.get('title', 'guide').replace(' ', '_').lower()}_{datetime.now().strftime('%Y%m%d')}.tex"

        return send_file(
            temp_path, mimetype="application/x-tex", as_attachment=True, download_name=filename
        )

    except Exception as e:
        logger.exception("LaTeX export failed")
        return jsonify({"error": f"Export failed: {str(e)}"}), 500


@export_bp.route("/markdown", methods=["POST"])
def export_markdown():
    """
    Export guide as Markdown.

    Request JSON: Same as PDF export

    Returns: Markdown .md file download
    """
    try:
        data = request.get_json() or {}

        if not data.get("title"):
            return jsonify({"error": "Guide title is required"}), 400

        # Generate Markdown
        from presentation_service import create_guide_content

        content = create_guide_content(
            title=data.get("title", "SkyModderAI Guide"),
            summary=data.get("summary", ""),
            sections=data.get("sections", []),
            warnings=data.get("warnings", []),
            recommendations=data.get("recommendations", []),
            sources=data.get("sources", []),
        )

        md_content = _format_as_markdown(content)

        # Create temp file
        fd, temp_path = tempfile.mkstemp(suffix=".md")
        os.close(fd)

        with open(temp_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        # Send file
        filename = f"{data.get('title', 'guide').replace(' ', '_').lower()}_{datetime.now().strftime('%Y%m%d')}.md"

        return send_file(
            temp_path, mimetype="text/markdown", as_attachment=True, download_name=filename
        )

    except Exception as e:
        logger.exception("Markdown export failed")
        return jsonify({"error": f"Export failed: {str(e)}"}), 500


@export_bp.route("/templates", methods=["GET"])
def get_templates():
    """
    Get available export templates.

    Returns: List of template info
    """
    templates = [
        {
            "id": "modding_guide",
            "name": "Modding Guide",
            "description": "Standard modding guide with warnings and recommendations",
            "formats": ["pdf", "html", "latex", "markdown"],
        },
        {
            "id": "conflict_report",
            "name": "Conflict Report",
            "description": "Detailed conflict analysis with resolution steps",
            "formats": ["pdf", "html", "latex"],
        },
        {
            "id": "load_order",
            "name": "Load Order Guide",
            "description": "Optimized load order with explanations",
            "formats": ["pdf", "html", "markdown"],
        },
        {
            "id": "build_list",
            "name": "Build List",
            "description": "Curated mod list with categories and rationale",
            "formats": ["pdf", "html", "markdown"],
        },
    ]

    return jsonify({"templates": templates})


def _format_as_markdown(content: dict[str, Any]) -> str:
    """Format content as Markdown."""
    md = []

    # Title
    md.append(f"# {content.get('title', 'SkyModderAI Guide')}\n")
    md.append(f"*Generated by SkyModderAI on {datetime.now().strftime('%B %d, %Y')}*\n")

    # Summary
    if content.get("summary"):
        md.append("## Executive Summary\n")
        md.append(f"{content['summary']}\n")

    # Warnings
    if content.get("warnings"):
        md.append("## ⚠️ Important Warnings\n")
        for warning in content["warnings"]:
            level = warning.get("level", "warning")
            icon = "❌" if level == "high" else "⚠️" if level == "medium" else "ℹ️"
            md.append(f"### {icon} {warning.get('message', '')}\n")
            if warning.get("details"):
                for detail in warning["details"]:
                    md.append(f"- {detail}")
                md.append("")

    # Sections
    for section in content.get("sections", []):
        heading = "###" if section.get("subsection") else "##"
        md.append(f"{heading} {section.get('title', 'Section')}\n")
        md.append(f"{section.get('content', '')}\n")

    # Recommendations
    if content.get("recommendations"):
        md.append("## ✅ Recommendations\n")
        for i, rec in enumerate(content["recommendations"], 1):
            priority = rec.get("priority", "normal")
            prefix = "🔴" if priority == "high" else "🟡" if priority == "medium" else "🔵"
            md.append(f"{i}. {prefix} {rec.get('content', '')}")
        md.append("")

    # Sources
    if content.get("sources"):
        md.append("## 📚 Sources\n")
        for source in content["sources"]:
            credibility = source.get("credibility_score", 0)
            stars = "★★★" if credibility >= 0.8 else "★★☆" if credibility >= 0.6 else "★☆☆"
            title = source.get("title", "Unknown")
            url = source.get("url", "")
            md.append(f"- {stars} {title}" + (f" - [{url}]({url})" if url else ""))
        md.append("")

    return "\n".join(md)


# Register blueprint exports
def register_exports(app):
    """Register export blueprints with app."""
    from blueprints import export_bp

    app.register_blueprint(export_bp)
