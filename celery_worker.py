"""
Celery Configuration for SkyModderAI

Background job processing for:
- Research pipeline (Nexus/Reddit/GitHub scraping)
- LOOT masterlist downloads
- Email sending
- AI analysis (async)
- Database cleanup

Usage:
    celery -A celery_worker.celery worker --loglevel=info
    celery -A celery_worker.celery beat --loglevel=info  # Scheduled tasks

At 1M users: Run 5+ workers with auto-scaling
"""

import logging
import os

from celery import Celery
from celery.schedules import crontab

# Redis URL from environment
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Initialize Celery
celery = Celery(
    "skymodderai",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        "celery_worker",
    ],
)

# Configuration
celery.conf.update(
    # Task serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    # Timezone
    timezone="UTC",
    enable_utc=True,
    # Task execution
    task_track_started=True,
    task_time_limit=300,  # 5 minutes max per task
    task_soft_time_limit=240,  # 4 minutes soft limit
    # Results
    result_expires=3600,  # 1 hour
    # Rate limiting
    worker_prefetch_multiplier=1,  # Fair task distribution
    # Retries
    task_acks_late=True,
    task_reject_on_worker_or_memloss=True,
    # Connection pool
    broker_pool_limit=10,
    broker_connection_timeout=10,
)

# Scheduled tasks (Celery Beat)
celery.conf.beat_schedule = {
    # Cleanup old sessions every hour
    "cleanup-sessions": {
        "task": "cleanup_old_sessions",
        "schedule": crontab(minute=0),  # Every hour
    },
    # Cleanup old cache entries every 6 hours
    "cleanup-cache": {
        "task": "cleanup_old_cache",
        "schedule": crontab(minute=0, hour="*/6"),
    },
    # Refresh LOOT masterlists daily
    "refresh-loot-masterlists": {
        "task": "refresh_loot_masterlists",
        "schedule": crontab(minute=0, hour=3),  # 3 AM UTC
    },
    # Generate weekly reports
    "generate-weekly-reports": {
        "task": "generate_weekly_reports",
        "schedule": crontab(minute=0, hour=0, day_of_week=0),  # Sunday midnight
    },
    # Calculate trust scores daily
    "calculate-trust-scores": {
        "task": "calculate_business_trust_scores",
        "schedule": crontab(minute=0, hour=2),  # 2 AM UTC
    },
}

# Logging
logger = logging.getLogger(__name__)


# =============================================================================
# Background Tasks
# =============================================================================


@celery.task(bind=True, max_retries=3)
def cleanup_old_sessions(self):
    """Delete expired user sessions from database."""
    import time

    from db import get_db

    try:
        db = get_db()
        now = int(time.time())

        result = db.execute("DELETE FROM user_sessions WHERE expires_at < ?", (now,))
        db.commit()

        deleted = result.rowcount
        logger.info(f"Cleaned up {deleted} expired sessions")
        return {"deleted": deleted}

    except Exception as e:
        logger.error(f"Session cleanup failed: {e}")
        raise self.retry(exc=e, countdown=60)


@celery.task(bind=True, max_retries=3)
def cleanup_old_cache(self):
    """Clean up old cache entries (Redis TTL handles most, this is for safety)."""
    from cache_service import get_cache

    try:
        cache = get_cache()
        # Redis handles TTL automatically, this is just for stats
        stats = cache.get_stats()
        logger.info(f"Cache stats: {stats}")
        return stats

    except Exception as e:
        logger.error(f"Cache cleanup failed: {e}")
        raise self.retry(exc=e, countdown=60)


@celery.task(bind=True, max_retries=5)
def refresh_loot_masterlists(self):
    """Download latest LOOT masterlists for all games."""
    from loot_parser import LOOTParser

    games = ["skyrimse", "skyrim", "skyrimvr", "fallout4", "falloutnv", "oblivion"]

    try:
        for game in games:
            try:
                parser = LOOTParser(game)
                parser.download_masterlist(force_refresh=True)
                logger.info(f"Refreshed LOOT masterlist for {game}")
            except Exception as e:
                logger.warning(f"Failed to refresh {game}: {e}")

        return {"success": True, "games": games}

    except Exception as e:
        logger.error(f"LOOT refresh failed: {e}")
        raise self.retry(exc=e, countdown=300)


@celery.task(bind=True, max_retries=3)
def send_email_async(self, to: str, subject: str, body: str, html: bool = False):
    """Send email asynchronously."""
    from email_utils import send_email

    try:
        send_email(to, subject, body, html=html)
        logger.info(f"Email sent to {to}: {subject}")
        return {"success": True}

    except Exception as e:
        logger.error(f"Email send failed: {e}")
        raise self.retry(exc=e, countdown=60)


@celery.task(bind=True, max_retries=3)
def analyze_mod_list_async(self, mod_list: list, game: str, user_email: str = None):
    """
    Analyze mod list asynchronously.

    For 1M users: Queue all complex analyses, return job ID immediately.
    User polls for results or gets webhook notification.
    """
    from analysis_service import analyze_mod_list

    try:
        result = analyze_mod_list(mod_list, game)

        # Store result for retrieval
        from cache_service import get_cache

        cache = get_cache()

        result_key = f"analysis:{user_email}:{game}:{hash(str(mod_list))}"
        cache.set(result_key, result, ttl=3600)  # 1 hour

        logger.info(f"Analysis complete for {user_email}: {game}")
        return {"success": True, "result_key": result_key}

    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise self.retry(exc=e, countdown=60)


@celery.task(bind=True, max_retries=3)
def calculate_business_trust_scores(self):
    """Calculate trust scores for all businesses."""
    from business_service import get_business_service

    try:
        service = get_business_service()
        result = service.calculate_all_trust_scores()

        logger.info(f"Trust scores calculated: {result}")
        return result

    except Exception as e:
        logger.error(f"Trust score calculation failed: {e}")
        raise self.retry(exc=e, countdown=300)


@celery.task(bind=True, max_retries=3)
def generate_weekly_reports(self):
    """Generate weekly analytics reports."""
    from weekly_report import generate_report

    try:
        report = generate_report()
        logger.info(f"Weekly report generated: {report}")
        return report

    except Exception as e:
        logger.error(f"Weekly report generation failed: {e}")
        raise self.retry(exc=e, countdown=600)


# =============================================================================
# Startup Check
# =============================================================================

if __name__ == "__main__":
    # Test connection
    try:
        celery.connection().ensure_connection(max_retries=3)
        logger.info("✓ Celery connected to Redis broker")
        logger.info("✓ Scheduled tasks configured:")
        for task_name, config in celery.conf.beat_schedule.items():
            logger.info(f"  - {task_name}: {config['schedule']}")
    except Exception as e:
        logger.exception("✗ Celery connection failed")
        logger.error("Make sure Redis is running and REDIS_URL is set")
