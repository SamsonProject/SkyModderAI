"""
SkyModderAI - RSS Feed Service

Generate RSS feeds for mods, compatibility reports, and author updates.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional
from xml.etree import ElementTree as ET

from flask import Response, request

logger = logging.getLogger(__name__)


class RSSFeedService:
    """Service for generating RSS feeds."""

    def generate_mod_feed(self, mod_name: str, game: str, limit: int = 50) -> str:
        """Generate RSS feed for a specific mod."""
        try:
            from db import get_db

            db = get_db()

            # Get mod details
            mod_detail = db.execute(
                """
                SELECT * FROM mod_details
                WHERE mod_name = ? AND game = ?
            """,
                (mod_name.lower(), game),
            ).fetchone()

            # Get recent compatibility reports
            reports = db.execute(
                """
                SELECT * FROM compatibility_reports
                WHERE (mod_a = ? OR mod_b = ?) AND game = ?
                ORDER BY created_at DESC
                LIMIT ?
            """,
                (mod_name.lower(), mod_name.lower(), game, limit),
            ).fetchall()

            # Build RSS feed
            root = ET.Element("rss", version="2.0")
            channel = ET.SubElement(root, "channel")

            # Channel info
            ET.SubElement(channel, "title").text = f"SkyModderAI - {mod_name} Compatibility"
            ET.SubElement(
                channel, "link"
            ).text = f"https://skymodderai.com/mod/{mod_name}?game={game}"
            ET.SubElement(
                channel, "description"
            ).text = f"Compatibility reports for {mod_name} ({game})"
            ET.SubElement(channel, "language").text = "en-us"
            ET.SubElement(channel, "lastBuildDate").text = datetime.now(timezone.utc).strftime(
                "%a, %d %b %Y %H:%M:%S GMT"
            )

            # Add items for each report
            for report in reports:
                item = ET.SubElement(channel, "item")

                # Determine other mod in report
                other_mod = (
                    report["mod_b"] if report["mod_a"] == mod_name.lower() else report["mod_a"]
                )

                ET.SubElement(
                    item, "title"
                ).text = f"{report['status'].replace('_', ' ').title()}: {mod_name} + {other_mod}"
                ET.SubElement(
                    item, "link"
                ).text = (
                    f"https://skymodderai.com/compatibility/{mod_name}/vs/{other_mod}?game={game}"
                )
                ET.SubElement(item, "guid").text = f"report-{report['id']}"
                ET.SubElement(item, "pubDate").text = datetime.fromtimestamp(
                    report["created_at"], timezone.utc
                ).strftime("%a, %d %b %Y %H:%M:%S GMT")
                ET.SubElement(item, "description").text = report["description"]

                # Category (status)
                ET.SubElement(item, "category").text = report["status"]

            return ET.tostring(root, encoding="unicode", xml_declaration=True)

        except Exception as e:
            logger.error(f"Failed to generate mod RSS feed: {e}")
            return ""

    def generate_compatibility_feed(
        self, game: str = None, status: str = None, limit: int = 50
    ) -> str:
        """Generate RSS feed for compatibility reports."""
        try:
            from db import get_db

            db = get_db()

            # Build query
            query = """
                SELECT * FROM compatibility_reports
                WHERE 1=1
            """
            params = []

            if game:
                query += " AND game = ?"
                params.append(game)

            if status:
                query += " AND status = ?"
                params.append(status)

            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)

            reports = db.execute(query, params).fetchall()

            # Build RSS feed
            root = ET.Element("rss", version="2.0")
            channel = ET.SubElement(root, "channel")

            # Channel info
            title = "SkyModderAI - Compatibility Reports"
            if game:
                title += f" ({game})"
            if status:
                title += f" - {status.replace('_', ' ').title()}"

            ET.SubElement(channel, "title").text = title
            ET.SubElement(channel, "link").text = "https://skymodderai.com/compatibility/browse"
            ET.SubElement(
                channel, "description"
            ).text = "Latest compatibility reports from SkyModderAI"
            ET.SubElement(channel, "language").text = "en-us"
            ET.SubElement(channel, "lastBuildDate").text = datetime.now(timezone.utc).strftime(
                "%a, %d %b %Y %H:%M:%S GMT"
            )

            # Add items
            for report in reports:
                item = ET.SubElement(channel, "item")

                ET.SubElement(item, "title").text = f"{report['mod_a']} ↔ {report['mod_b']}"
                ET.SubElement(
                    item, "link"
                ).text = f"https://skymodderai.com/compatibility/{report['mod_a']}/vs/{report['mod_b']}?game={report['game']}"
                ET.SubElement(item, "guid").text = f"report-{report['id']}"
                ET.SubElement(item, "pubDate").text = datetime.fromtimestamp(
                    report["created_at"], timezone.utc
                ).strftime("%a, %d %b %Y %H:%M:%S GMT")
                ET.SubElement(item, "description").text = report["description"]

                # Categories
                ET.SubElement(item, "category").text = report["status"]
                ET.SubElement(item, "category").text = report["game"]

            return ET.tostring(root, encoding="unicode", xml_declaration=True)

        except Exception as e:
            logger.error(f"Failed to generate compatibility RSS feed: {e}")
            return ""

    def generate_author_feed(self, user_email: str, limit: int = 50) -> str:
        """Generate RSS feed for a mod author's updates."""
        try:
            from db import get_db

            db = get_db()

            # Get author's verified mods
            claims = db.execute(
                """
                SELECT mod_name, game FROM mod_author_claims
                WHERE author_email = ? AND verification_status = 'verified'
            """,
                (user_email,),
            ).fetchall()

            if not claims:
                return ""

            # Get recent reports for author's mods
            mod_conditions = " OR ".join(
                [
                    f"(mod_a = '{c['mod_name']}' OR mod_b = '{c['mod_name']}') AND game = '{c['game']}'"
                    for c in claims
                ]
            )

            query = f"""
                SELECT * FROM compatibility_reports
                WHERE {mod_conditions}
                ORDER BY created_at DESC
                LIMIT ?
            """

            reports = db.execute(query, (limit,)).fetchall()

            # Build RSS feed
            root = ET.Element("rss", version="2.0")
            channel = ET.SubElement(root, "channel")

            # Channel info
            ET.SubElement(channel, "title").text = "SkyModderAI - Your Mod Updates"
            ET.SubElement(channel, "link").text = "https://skymodderai.com/mod-author/dashboard"
            ET.SubElement(channel, "description").text = "Updates for your verified mods"
            ET.SubElement(channel, "language").text = "en-us"
            ET.SubElement(channel, "lastBuildDate").text = datetime.now(timezone.utc).strftime(
                "%a, %d %b %Y %H:%M:%S GMT"
            )

            # Add items
            for report in reports:
                item = ET.SubElement(channel, "item")

                ET.SubElement(
                    item, "title"
                ).text = f"New Report: {report['mod_a']} + {report['mod_b']}"
                ET.SubElement(
                    item, "link"
                ).text = f"https://skymodderai.com/compatibility/{report['mod_a']}/vs/{report['mod_b']}?game={report['game']}"
                ET.SubElement(item, "guid").text = f"report-{report['id']}"
                ET.SubElement(item, "pubDate").text = datetime.fromtimestamp(
                    report["created_at"], timezone.utc
                ).strftime("%a, %d %b %Y %H:%M:%S GMT")
                ET.SubElement(item, "description").text = report["description"]

            return ET.tostring(root, encoding="unicode", xml_declaration=True)

        except Exception as e:
            logger.error(f"Failed to generate author RSS feed: {e}")
            return ""


def get_rss_feed_service() -> RSSFeedService:
    """Get or create RSS feed service instance."""
    return RSSFeedService()


# Flask routes for RSS feeds
def create_rss_routes(app):
    """Register RSS feed routes with Flask app."""

    @app.route("/feed/mod/<path:mod_name>.xml")
    def mod_feed(mod_name: str):
        """RSS feed for a specific mod."""
        game = request.args.get("game", "skyrimse")
        limit = request.args.get("limit", "50")

        try:
            limit_int = int(limit)
        except ValueError:
            limit_int = 50

        service = get_rss_feed_service()
        feed_content = service.generate_mod_feed(mod_name, game, limit_int)

        if feed_content:
            return Response(
                feed_content,
                mimetype="application/rss+xml",
                headers={"Content-Disposition": f"attachment; filename={mod_name}_feed.xml"},
            )
        else:
            return Response("Failed to generate feed", status=500)

    @app.route("/feed/compatibility.xml")
    def compatibility_feed():
        """RSS feed for compatibility reports."""
        game = request.args.get("game", None)
        status = request.args.get("status", None)
        limit = request.args.get("limit", "50")

        try:
            limit_int = int(limit)
        except ValueError:
            limit_int = 50

        service = get_rss_feed_service()
        feed_content = service.generate_compatibility_feed(game, status, limit_int)

        if feed_content:
            filename = "compatibility_feed"
            if game:
                filename += f"_{game}"
            if status:
                filename += f"_{status}"

            return Response(
                feed_content,
                mimetype="application/rss+xml",
                headers={"Content-Disposition": f"attachment; filename={filename}.xml"},
            )
        else:
            return Response("Failed to generate feed", status=500)

    @app.route("/feed/author.xml")
    def author_feed():
        """RSS feed for mod author updates (requires auth)."""
        from flask import session

        if "user_email" not in session:
            return Response("Authentication required", status=401)

        limit = request.args.get("limit", "50")

        try:
            limit_int = int(limit)
        except ValueError:
            limit_int = 50

        service = get_rss_feed_service()
        feed_content = service.generate_author_feed(session["user_email"], limit_int)

        if feed_content:
            return Response(
                feed_content,
                mimetype="application/rss+xml",
                headers={"Content-Disposition": "attachment; filename=author_feed.xml"},
            )
        else:
            return Response("No verified mods or failed to generate feed", status=404)
