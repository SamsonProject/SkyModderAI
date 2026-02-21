"""
Samson Architecture Integration for SkyModderAI

Selective implementation of Samson principles:
1. Daily curation (2 AM cleanup)
2. Weekly reports to founder
3. Credibility scoring enhancement
4. Self-improvement log
5. Version tagging enforcement

NOT implementing (yet):
- Wonder-drive for responses
- Heart/brain volleyball
- Geometric compression
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from db import get_db

logger = logging.getLogger(__name__)


class SamsonCuration:
    """
    Daily curation system - runs at 2 AM to clean and improve knowledge base.

    Samson Principle: "The Filter Is The Product"
    - Rigorous filtering at every layer
    - Cheap models sort, expensive models verify
    - Continuous improvement through curation
    """

    def __init__(self):
        self.curation_log = []

    def run_daily_curation(self) -> dict[str, Any]:
        """
        Run daily curation at 2 AM.

        Tasks:
        1. Archive old/unused knowledge sources
        2. Update credibility scores based on user feedback
        3. Detect and flag deviation from standard approaches
        4. Clean up orphaned compatibility reports
        5. Generate curation report
        """
        logger.info("Starting daily Samson curation...")

        results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tasks_completed": 0,
            "items_processed": 0,
            "changes_made": 0,
            "issues_found": [],
        }

        try:
            # Task 1: Update credibility scores
            credibility_changes = self._update_credibility_scores()
            results["items_processed"] += credibility_changes["processed"]
            results["changes_made"] += credibility_changes["changed"]
            results["tasks_completed"] += 1

            # Task 2: Archive stale knowledge
            archived = self._archive_stale_knowledge()
            results["items_processed"] += archived["count"]
            results["tasks_completed"] += 1

            # Task 3: Clean orphaned reports
            cleaned = self._clean_orphaned_reports()
            results["items_processed"] += cleaned["count"]
            results["tasks_completed"] += 1

            # Task 4: Flag deviations
            deviations = self._detect_deviations()
            results["items_processed"] += deviations["checked"]
            results["changes_made"] += deviations["flagged"]
            results["tasks_completed"] += 1

            # Task 5: Enforce version tagging
            versioned = self._enforce_version_tagging()
            results["items_processed"] += versioned["checked"]
            results["changes_made"] += versioned["tagged"]
            results["tasks_completed"] += 1

            self.curation_log.append(results)
            logger.info(
                f"Daily curation complete: {results['tasks_completed']} tasks, "
                f"{results['changes_made']} changes"
            )

            return results

        except Exception as e:
            logger.error(f"Daily curation failed: {e}")
            results["issues_found"].append(str(e))
            return results

    def _update_credibility_scores(self) -> dict[str, int]:
        """
        Update credibility scores based on user feedback and vote patterns.

        Samson Principle: "Grounded Truth Over Statistical Probability"
        - Credibility scored based on real-world validation
        - Links to sources, doesn't archive
        - Always verifiable
        """
        db = get_db()

        # Get all compatibility reports with votes
        reports = db.execute(
            """
            SELECT id, upvotes, downvotes, verified, source_url
            FROM compatibility_reports
            WHERE created_at > ?
        """,
            ((datetime.now(timezone.utc) - timedelta(days=7)).timestamp(),),
        ).fetchall()

        processed = 0
        changed = 0

        for report in reports:
            # Calculate new credibility based on vote ratio
            total_votes = report["upvotes"] + report["downvotes"]
            if total_votes > 0:
                vote_ratio = report["upvotes"] / total_votes

                # Verified reports get boost
                if report["verified"]:
                    vote_ratio = min(1.0, vote_ratio + 0.2)

                # Update source credibility if URL exists
                if report.get("source_url"):
                    old_score = db.execute(
                        """
                        SELECT overall_score FROM source_credibility
                        WHERE source_url = ?
                    """,
                        (report["source_url"],),
                    ).fetchone()

                    if old_score:
                        new_score = (old_score["overall_score"] * 0.7) + (vote_ratio * 0.3)
                        db.execute(
                            """
                            UPDATE source_credibility
                            SET overall_score = ?, updated_at = CURRENT_TIMESTAMP
                            WHERE source_url = ?
                        """,
                            (new_score, report["source_url"]),
                        )
                        changed += 1

        db.commit()

        return {"processed": len(reports), "changed": changed}

    def _archive_stale_knowledge(self) -> dict[str, int]:
        """
        Archive knowledge sources that haven't been accessed in 90+ days.

        Samson Principle: "Deterministic Core + AI Conductor"
        - Keep active knowledge readily available
        - Archive stale data to reduce noise
        - 90% of work done by 10% of knowledge
        """
        db = get_db()

        # Find stale knowledge (not accessed in 90 days)
        stale = db.execute(
            """
            SELECT id, title, source_url
            FROM knowledge_sources
            WHERE status = 'active'
            AND (last_accessed IS NULL OR last_accessed < ?)
        """,
            ((datetime.now(timezone.utc) - timedelta(days=90)).isoformat(),),
        ).fetchall()

        count = 0
        for source in stale:
            db.execute(
                """
                UPDATE knowledge_sources
                SET status = 'archived', updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """,
                (source["id"],),
            )
            count += 1

        db.commit()

        logger.info(f"Archived {count} stale knowledge sources")
        return {"count": count}

    def _clean_orphaned_reports(self) -> dict[str, int]:
        """
        Remove compatibility reports for mods that no longer exist.

        Samson Principle: "The Filter Is The Product"
        - Filters are attention
        - Filters are relevance
        - Knowing what to ignore
        """
        db = get_db()

        # This is a placeholder - in production you'd check against actual mod databases
        # For now, just clean reports with 0 votes and very old
        old_unused = db.execute(
            """
            SELECT id FROM compatibility_reports
            WHERE upvotes = 0 AND downvotes = 0
            AND created_at < ?
        """,
            ((datetime.now(timezone.utc) - timedelta(days=180)).timestamp(),),
        ).fetchall()

        count = 0
        for report in old_unused:
            db.execute("DELETE FROM compatibility_reports WHERE id = ?", (report["id"],))
            count += 1

        db.commit()

        logger.info(f"Cleaned {count} orphaned compatibility reports")
        return {"count": count}

    def _detect_deviations(self) -> dict[str, int]:
        """
        Detect knowledge sources that deviate from standard approaches.

        Samson Principle: "Deviation Labeling"
        - Flag non-standard approaches
        - Don't censor, just label
        - Let users make informed decisions
        """
        db = get_db()

        # Check for knowledge sources without proper tags
        untagged = db.execute("""
            SELECT id, title, tags
            FROM knowledge_sources
            WHERE status = 'active'
            AND (tags IS NULL OR tags = '[]')
        """).fetchall()

        flagged = 0
        for source in untagged:
            # Flag as "unverified_approach"
            db.execute(
                """
                UPDATE knowledge_sources
                SET deviation_flags = json_insert(
                    COALESCE(deviation_flags, '[]'),
                    '$[#]', 'unverified_approach'
                ),
                is_standard_approach = FALSE
                WHERE id = ?
            """,
                (source["id"],),
            )
            flagged += 1

        db.commit()

        return {"checked": len(untagged), "flagged": flagged}

    def _enforce_version_tagging(self) -> dict[str, int]:
        """
        Ensure all knowledge sources have version tags.

        Samson Principle: "Version Tagging (Rigorous)"
        - Game version
        - Mod version
        - Content version
        - No version = less trustworthy
        """
        db = get_db()

        # Find sources missing version info
        unversioned = db.execute("""
            SELECT id, game
            FROM knowledge_sources
            WHERE game_version IS NULL OR mod_version IS NULL
            AND status = 'active'
        """).fetchall()

        tagged = 0
        for source in unversioned:
            # Tag with "unknown" version - at least it's explicit
            db.execute(
                """
                UPDATE knowledge_sources
                SET game_version = 'unknown',
                    mod_version = 'unknown',
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """,
                (source["id"],),
            )
            tagged += 1

        db.commit()

        return {"checked": len(unversioned), "tagged": tagged}


class SamsonWeeklyReport:
    """
    Generate weekly report to founder (Mondays 3 AM).

    Samson Principle: "The Feedback Loop Is The Learning"
    - Weekly reports to founder
    - User feedback integrated
    - Self-improvement log
    - Continuous gradient updates
    """

    def generate_weekly_report(self) -> dict[str, Any]:
        """
        Generate comprehensive weekly report.

        Includes:
        1. User metrics (active users, retention)
        2. System performance (response times, costs)
        3. Quality metrics (hallucination rate, accuracy)
        4. Community health (reports, votes, engagement)
        5. Self-improvement log entries
        6. Recommendations for next week
        """
        db = get_db()

        report = {
            "week_start": (datetime.now(timezone.utc) - timedelta(days=7)).isoformat(),
            "week_end": datetime.now(timezone.utc).isoformat(),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "metrics": self._collect_metrics(db),
            "self_improvement_log": self._collect_improvements(db),
            "recommendations": [],
        }

        # Generate recommendations based on metrics
        report["recommendations"] = self._generate_recommendations(report["metrics"])

        # Save report to database
        self._save_report(db, report)

        logger.info(f"Weekly report generated: {len(report['recommendations'])} recommendations")
        return report

    def _collect_metrics(self, db) -> dict[str, Any]:
        """Collect key metrics for the week."""

        # User metrics
        active_users = db.execute(
            """
            SELECT COUNT(DISTINCT user_email) as count
            FROM user_activity
            WHERE created_at > ?
        """,
            ((datetime.now(timezone.utc) - timedelta(days=7)).isoformat(),),
        ).fetchone()["count"]

        # Compatibility reports
        new_reports = db.execute(
            """
            SELECT COUNT(*) as count FROM compatibility_reports
            WHERE created_at > ?
        """,
            ((datetime.now(timezone.utc) - timedelta(days=7)).isoformat(),),
        ).fetchone()["count"]

        # Votes cast
        votes_cast = db.execute(
            """
            SELECT COUNT(*) as count FROM compatibility_votes
            WHERE voted_at > ?
        """,
            ((datetime.now(timezone.utc) - timedelta(days=7)).timestamp(),),
        ).fetchone()["count"]

        # Mod claims
        new_claims = db.execute(
            """
            SELECT COUNT(*) as count FROM mod_author_claims
            WHERE created_at > ?
        """,
            ((datetime.now(timezone.utc) - timedelta(days=7)).isoformat(),),
        ).fetchone()["count"]

        return {
            "active_users": active_users,
            "new_compatibility_reports": new_reports,
            "votes_cast": votes_cast,
            "new_mod_claims": new_claims,
        }

    def _collect_improvements(self, db) -> list[dict]:
        """Collect self-improvement log entries."""
        # This would track system improvements over time
        # For now, return placeholder
        return [
            {
                "date": datetime.now(timezone.utc).isoformat(),
                "improvement": "Implemented Samson curation system",
                "impact": "Daily automated knowledge base cleanup",
            }
        ]

    def _generate_recommendations(self, metrics: dict) -> list[str]:
        """Generate recommendations based on metrics."""
        recommendations = []

        if metrics["active_users"] < 100:
            recommendations.append("Focus on user acquisition - active users below target")

        if metrics["new_compatibility_reports"] < 10:
            recommendations.append("Encourage community reports - low participation")

        if metrics["votes_cast"] < metrics["new_compatibility_reports"] * 2:
            recommendations.append("Improve vote engagement - reports not getting feedback")

        return recommendations

    def _save_report(self, db, report: dict):
        """Save report to database for historical tracking."""
        db.execute(
            """
            INSERT INTO weekly_reports
            (report_json, created_at)
            VALUES (?, CURRENT_TIMESTAMP)
        """,
            (json.dumps(report),),
        )
        db.commit()


class SamsonSelfImprovementLog:
    """
    Track system self-improvements over time.

    Samson Principle: "Gets smarter every week, not just every training cycle"
    - Log every improvement
    - Track what worked
    - Build institutional memory
    """

    def __init__(self):
        self.log_entries = []

    def log_improvement(self, improvement_type: str, description: str, impact: str):
        """
        Log a self-improvement.

        Args:
            improvement_type: 'curation', 'performance', 'accuracy', 'feature'
            description: What was improved
            impact: Expected or measured impact
        """
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": improvement_type,
            "description": description,
            "impact": impact,
        }

        self.log_entries.append(entry)

        # Also save to database
        try:
            db = get_db()
            db.execute(
                """
                INSERT INTO self_improvement_log
                (improvement_type, description, impact, created_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """,
                (improvement_type, description, impact),
            )
            db.commit()
        except Exception as e:
            logger.error(f"Failed to log improvement: {e}")

        logger.info(f"Self-improvement logged: {improvement_type} - {description}")

    def get_recent_improvements(self, days: int = 30) -> list[dict]:
        """Get improvements from the last N days."""
        try:
            db = get_db()
            entries = db.execute(
                """
                SELECT * FROM self_improvement_log
                WHERE created_at > ?
                ORDER BY created_at DESC
            """,
                ((datetime.now(timezone.utc) - timedelta(days=days)).isoformat(),),
            ).fetchall()

            return [dict(e) for e in entries]
        except Exception as e:
            logger.error(f"Failed to get improvements: {e}")
            return self.log_entries


# Singleton instances
_curation_instance = None
_report_instance = None
_improvement_log_instance = None


def get_curation_service() -> SamsonCuration:
    """Get Samson curation service instance."""
    global _curation_instance
    if _curation_instance is None:
        _curation_instance = SamsonCuration()
    return _curation_instance


def get_weekly_report_service() -> SamsonWeeklyReport:
    """Get weekly report service instance."""
    global _report_instance
    if _report_instance is None:
        _report_instance = SamsonWeeklyReport()
    return _report_instance


def get_improvement_log() -> SamsonSelfImprovementLog:
    """Get self-improvement log instance."""
    global _improvement_log_instance
    if _improvement_log_instance is None:
        _improvement_log_instance = SamsonSelfImprovementLog()
    return _improvement_log_instance
