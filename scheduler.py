"""
Scheduler Service - Scheduled intelligence jobs for SkyModderAI.

Provides:
- 2 AM daily curation job (clustering, compaction, trash audit)
- Weekly report generation (Mondays at 3 AM)
- Model retraining scheduling
- Research pipeline scheduling

Usage:
    from scheduler import get_scheduler, schedule_job
    
    scheduler = get_scheduler()
    
    # Schedule a job
    scheduler.schedule_daily("curation", run_curation_job, hour=2, minute=0)
    scheduler.schedule_weekly("weekly_report", run_weekly_report, day="monday", hour=3, minute=0)
    
    # Start scheduler (call once at app startup)
    scheduler.start()
"""

import logging
import os
import sys
from datetime import datetime, time
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

# APScheduler availability check
try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.triggers.interval import IntervalTrigger
    APSCHEDULER_AVAILABLE = True
except ImportError:
    APSCHEDULER_AVAILABLE = False
    logger.warning("APScheduler not installed. Scheduler will use basic threading fallback.")


class BasicScheduler:
    """Basic threading-based scheduler fallback."""
    
    def __init__(self):
        self._jobs: Dict[str, dict] = {}
        self._running = False
    
    def schedule_daily(self, name: str, func: Callable, hour: int = 2, minute: int = 0):
        """Schedule a job to run daily."""
        self._jobs[name] = {
            "func": func,
            "trigger": "daily",
            "hour": hour,
            "minute": minute,
            "enabled": True
        }
        logger.info(f"Scheduled daily job: {name} at {hour:02d}:{minute:02d}")
    
    def schedule_weekly(self, name: str, func: Callable, day: str = "monday", hour: int = 3, minute: int = 0):
        """Schedule a job to run weekly."""
        self._jobs[name] = {
            "func": func,
            "trigger": "weekly",
            "day": day,
            "hour": hour,
            "minute": minute,
            "enabled": True
        }
        logger.info(f"Scheduled weekly job: {name} on {day} at {hour:02d}:{minute:02d}")
    
    def schedule_interval(self, name: str, func: Callable, seconds: int):
        """Schedule a job to run at an interval."""
        self._jobs[name] = {
            "func": func,
            "trigger": "interval",
            "seconds": seconds,
            "enabled": True
        }
        logger.info(f"Scheduled interval job: {name} every {seconds}s")
    
    def start(self):
        """Start the scheduler (no-op for basic scheduler)."""
        self._running = True
        logger.warning("Basic scheduler started - jobs are registered but not executed. Install APScheduler for full functionality.")
    
    def shutdown(self, wait: bool = True):
        """Stop the scheduler."""
        self._running = False
    
    def get_job(self, name: str) -> Optional[dict]:
        """Get job info."""
        return self._jobs.get(name)
    
    def remove_job(self, name: str) -> bool:
        """Remove a scheduled job."""
        if name in self._jobs:
            del self._jobs[name]
            return True
        return False
    
    def list_jobs(self) -> List[Dict[str, Any]]:
        """List all scheduled jobs."""
        return [
            {"name": name, **info}
            for name, info in self._jobs.items()
        ]


class APScheduler:
    """APScheduler-backed scheduler with full cron support."""
    
    def __init__(self):
        self._scheduler = BackgroundScheduler(
            timezone='UTC',
            job_defaults={
                'coalesce': True,
                'max_instances': 1,
                'misfire_grace_time': 3600  # 1 hour grace for missed jobs
            }
        )
    
    def schedule_daily(self, name: str, func: Callable, hour: int = 2, minute: int = 0):
        """Schedule a job to run daily."""
        trigger = CronTrigger(hour=hour, minute=minute, timezone='UTC')
        self._scheduler.add_job(func, trigger, id=name, name=name, replace_existing=True)
        logger.info(f"Scheduled daily job: {name} at {hour:02d}:{minute:02d} UTC")
    
    def schedule_weekly(self, name: str, func: Callable, day: str = "monday", hour: int = 3, minute: int = 0):
        """Schedule a job to run weekly."""
        trigger = CronTrigger(day_of_week=day, hour=hour, minute=minute, timezone='UTC')
        self._scheduler.add_job(func, trigger, id=name, name=name, replace_existing=True)
        logger.info(f"Scheduled weekly job: {name} on {day} at {hour:02d}:{minute:02d} UTC")
    
    def schedule_interval(self, name: str, func: Callable, seconds: int):
        """Schedule a job to run at an interval."""
        trigger = IntervalTrigger(seconds=seconds)
        self._scheduler.add_job(func, trigger, id=name, name=name, replace_existing=True)
        logger.info(f"Scheduled interval job: {name} every {seconds}s")
    
    def start(self):
        """Start the scheduler."""
        self._scheduler.start()
        logger.info("APScheduler started")
    
    def shutdown(self, wait: bool = True):
        """Stop the scheduler."""
        self._scheduler.shutdown(wait=wait)
        logger.info("APScheduler stopped")
    
    def get_job(self, name: str) -> Optional[Dict[str, Any]]:
        """Get job info."""
        job = self._scheduler.get_job(name)
        if job:
            return {
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            }
        return None
    
    def remove_job(self, name: str) -> bool:
        """Remove a scheduled job."""
        try:
            self._scheduler.remove_job(name)
            return True
        except Exception:
            return False
    
    def list_jobs(self) -> List[Dict[str, Any]]:
        """List all scheduled jobs."""
        return [
            {
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            }
            for job in self._scheduler.get_jobs()
        ]


class SchedulerService:
    """Unified scheduler service with automatic fallback."""
    
    def __init__(self):
        """Initialize scheduler with APScheduler or basic fallback."""
        self._scheduler = None
        
        if APSCHEDULER_AVAILABLE:
            self._scheduler = APScheduler()
            logger.info("Using APScheduler backend")
        else:
            self._scheduler = BasicScheduler()
            logger.info("Using basic scheduler fallback")
    
    def schedule_daily(self, name: str, func: Callable, hour: int = 2, minute: int = 0):
        """Schedule a job to run daily."""
        self._scheduler.schedule_daily(name, func, hour, minute)
    
    def schedule_weekly(self, name: str, func: Callable, day: str = "monday", hour: int = 3, minute: int = 0):
        """Schedule a job to run weekly."""
        self._scheduler.schedule_weekly(name, func, day, hour, minute)
    
    def schedule_interval(self, name: str, func: Callable, seconds: int):
        """Schedule a job to run at an interval."""
        self._scheduler.schedule_interval(name, func, seconds)
    
    def start(self):
        """Start the scheduler."""
        self._scheduler.start()
    
    def shutdown(self, wait: bool = True):
        """Stop the scheduler."""
        self._scheduler.shutdown(wait)
    
    def get_job(self, name: str) -> Optional[Dict[str, Any]]:
        """Get job info."""
        return self._scheduler.get_job(name)
    
    def remove_job(self, name: str) -> bool:
        """Remove a scheduled job."""
        return self._scheduler.remove_job(name)
    
    def list_jobs(self) -> List[Dict[str, Any]]:
        """List all scheduled jobs."""
        return self._scheduler.list_jobs()


# Singleton instance
_scheduler_service: Optional[SchedulerService] = None


def get_scheduler() -> SchedulerService:
    """Get or create scheduler service singleton."""
    global _scheduler_service
    if _scheduler_service is None:
        _scheduler_service = SchedulerService()
    return _scheduler_service


# =============================================================================
# Scheduled Job Implementations
# =============================================================================

def run_daily_curation():
    """
    Daily curation job (2 AM UTC).
    
    Tasks:
    - Semantic clustering of new knowledge
    - Information compaction (remove duplicates)
    - Cross-linking related entries
    - Trash bin audit
    - Category discovery
    """
    logger.info("Starting daily curation job...")
    start_time = datetime.now()
    
    try:
        # Import here to avoid circular dependencies
        from curation_service import run_curation_pipeline
        
        results = run_curation_pipeline()
        
        logger.info(f"Daily curation completed in {(datetime.now() - start_time).total_seconds():.2f}s")
        logger.info(f"Results: {results}")
        
        # Log to activity tracking
        track_curation_run(results)
        
    except Exception as e:
        logger.exception(f"Daily curation job failed: {e}")
        raise


def run_weekly_report():
    """
    Weekly self-improvement report (Mondays 3 AM UTC).
    
    Sends email to chris@skymoddereai.com with:
    - What worked well
    - What broke / needs improvement
    - System optimization suggestions
    - New knowledge added
    - Questions for Chris
    """
    logger.info("Starting weekly report job...")
    start_time = datetime.now()
    
    try:
        from weekly_report import generate_weekly_report
        
        report = generate_weekly_report()
        
        # Send email
        send_weekly_email(report)
        
        logger.info(f"Weekly report completed in {(datetime.now() - start_time).total_seconds():.2f}s")
        logger.info(f"Report sent to chris@skymoddereai.com")
        
    except Exception as e:
        logger.exception(f"Weekly report job failed: {e}")
        raise


def run_research_pipeline():
    """
    Research pipeline job (every 6 hours).

    Tasks:
    - Scrape Nexus Mods API for new/updated mods
    - Scrape Reddit (r/skyrimmods, r/fo4mods)
    - Process and score new sources
    - Add to knowledge base
    """
    logger.info("Starting research pipeline job...")
    start_time = datetime.now()

    try:
        from research_pipeline import run_research_cycle

        results = run_research_cycle()

        logger.info(f"Research pipeline completed in {(datetime.now() - start_time).total_seconds():.2f}s")
        logger.info(f"Results: {results}")

    except Exception as e:
        logger.exception(f"Research pipeline job failed: {e}")
        raise


def run_deviation_labeling():
    """
    Deviation labeling job (Sundays 5 AM UTC).

    Tasks:
    - Analyze all knowledge sources for deviations
    - Flag non-standard approaches
    - Update risk levels
    """
    logger.info("Starting deviation labeling job...")
    start_time = datetime.now()

    try:
        from deviation_labeler import analyze_deviations

        results = analyze_deviations()

        logger.info(f"Deviation labeling completed in {(datetime.now() - start_time).total_seconds():.2f}s")
        logger.info(f"Results: {results}")

    except Exception as e:
        logger.exception(f"Deviation labeling job failed: {e}")
        raise


def run_model_retraining():
    """
    Model retraining job (Sundays 4 AM UTC).
    
    Tasks:
    - Retrain conflict prediction models
    - Update embedding indexes
    - Optimize lookup tables
    """
    logger.info("Starting model retraining job...")
    start_time = datetime.now()
    
    try:
        from model_trainer import run_retraining_pipeline
        
        results = run_retraining_pipeline()
        
        logger.info(f"Model retraining completed in {(datetime.now() - start_time).total_seconds():.2f}s")
        logger.info(f"Results: {results}")
        
    except Exception as e:
        logger.exception(f"Model retraining job failed: {e}")
        raise


# =============================================================================
# Helper Functions
# =============================================================================

def track_curation_run(results: Dict[str, Any]):
    """Track curation run in database."""
    try:
        from db import get_db_session
        from models import UserActivity
        
        session = get_db_session()
        activity = UserActivity(
            event_type="curation_run",
            event_data=str(results),
            session_id="system"
        )
        session.add(activity)
        session.commit()
    except Exception as e:
        logger.debug(f"Failed to track curation run: {e}")


def send_weekly_email(report: Dict[str, Any]):
    """Send weekly report email."""
    try:
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        
        # Email configuration
        smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', 587))
        smtp_user = os.getenv('SMTP_USER')
        smtp_password = os.getenv('SMTP_PASSWORD')
        
        if not smtp_user or not smtp_password:
            logger.warning("SMTP not configured. Weekly report not sent.")
            return
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"SkyModderAI Weekly Report - {datetime.now().strftime('%Y-%m-%d')}"
        msg['From'] = smtp_user
        msg['To'] = 'chris@skymoddereai.com'
        
        # Build HTML content
        html = build_weekly_report_html(report)
        msg.attach(MIMEText(html, 'html'))
        
        # Send
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
        
        logger.info("Weekly report email sent successfully")
        
    except Exception as e:
        logger.exception(f"Failed to send weekly report email: {e}")


def build_weekly_report_html(report: Dict[str, Any]) -> str:
    """Build HTML email for weekly report."""
    return f"""
    <html>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6;">
        <h1 style="color: #333;">SkyModderAI Weekly Report</h1>
        <p style="color: #666;">{datetime.now().strftime('%Y-%m-%d')}</p>
        
        <h2 style="color: #2ecc71;">✅ What Worked Well</h2>
        <ul>
            {''.join(f'<li>{item}</li>' for item in report.get('worked_well', []))}
        </ul>
        
        <h2 style="color: #e74c3c;">⚠️ What Needs Improvement</h2>
        <ul>
            {''.join(f'<li>{item}</li>' for item in report.get('needs_improvement', []))}
        </ul>
        
        <h2 style="color: #3498db;">💡 Optimization Suggestions</h2>
        <ol>
            {''.join(f'<li>{item}</li>' for item in report.get('suggestions', []))}
        </ol>
        
        <h2 style="color: #9b59b6;">📊 New Knowledge Added</h2>
        <ul>
            {''.join(f'<li>{item}</li>' for item in report.get('new_knowledge', []))}
        </ul>
        
        <h2 style="color: #f39c12;">❓ Questions for Chris</h2>
        <ol>
            {''.join(f'<li>{item}</li>' for item in report.get('questions', []))}
        </ol>
        
        <hr style="border: none; border-top: 1px solid #ddd; margin: 2rem 0;">
        <p style="color: #999; font-size: 0.9rem;">
            This is an automated report from SkyModderAI. 
            To adjust report settings, modify the scheduler configuration.
        </p>
    </body>
    </html>
    """


def setup_default_jobs():
    """Set up all default scheduled jobs."""
    scheduler = get_scheduler()

    # Daily curation (2 AM UTC)
    scheduler.schedule_daily("daily_curation", run_daily_curation, hour=2, minute=0)

    # Weekly report (Mondays 3 AM UTC)
    scheduler.schedule_weekly("weekly_report", run_weekly_report, day="monday", hour=3, minute=0)

    # Research pipeline (every 6 hours)
    scheduler.schedule_interval("research_pipeline", run_research_pipeline, seconds=21600)

    # Deviation labeling (Sundays 5 AM UTC)
    scheduler.schedule_weekly("deviation_labeling", run_deviation_labeling, day="sunday", hour=5, minute=0)

    # Model retraining (Sundays 4 AM UTC)
    scheduler.schedule_weekly("model_retraining", run_model_retraining, day="sunday", hour=4, minute=0)

    logger.info("Default scheduled jobs configured")

    return scheduler
