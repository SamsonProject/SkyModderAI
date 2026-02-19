"""
Feedback Service - User feedback collection and session tracking for SkyModderAI.

Provides:
- Session tracking (queries, resolutions, time spent)
- Post-session curation (async, after sign-out)
- Feedback collection (ratings, issues, suggestions)
- Self-improvement log (running shorthand for weekly reports)

All feedback feeds into the weekly report to chris@skymoddereai.com.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import uuid4

from db import get_db_session
from models import UserFeedback, UserActivity, SatisfactionSurvey, KnowledgeSource

logger = logging.getLogger(__name__)


class SessionTracker:
    """Track user session for feedback collection."""
    
    def __init__(self, user_email: Optional[str] = None, session_id: Optional[str] = None):
        self.user_email = user_email
        self.session_id = session_id or str(uuid4())
        self.start_time = datetime.now()
        self.events: List[Dict[str, Any]] = []
        self.queries: List[Dict[str, Any]] = []
        self.resolutions: List[Dict[str, Any]] = []
        
    def track_query(self, query_type: str, query_data: Dict[str, Any]):
        """Track a user query."""
        self.queries.append({
            "type": query_type,
            "data": query_data,
            "timestamp": datetime.now().isoformat()
        })
        
        self.events.append({
            "event": "query",
            "type": query_type,
            "timestamp": datetime.now().isoformat()
        })
    
    def track_resolution(self, resolution_type: str, resolution_data: Dict[str, Any], helpful: bool = True):
        """Track a resolution provided to user."""
        self.resolutions.append({
            "type": resolution_type,
            "data": resolution_data,
            "helpful": helpful,
            "timestamp": datetime.now().isoformat()
        })
    
    def track_action(self, action: str, details: Optional[Dict[str, Any]] = None):
        """Track a user action."""
        self.events.append({
            "event": "action",
            "action": action,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get session summary for curation."""
        duration = (datetime.now() - self.start_time).total_seconds()
        
        return {
            "session_id": self.session_id,
            "user_email": self.user_email,
            "start_time": self.start_time.isoformat(),
            "end_time": datetime.now().isoformat(),
            "duration_seconds": duration,
            "query_count": len(self.queries),
            "resolution_count": len(self.resolutions),
            "event_count": len(self.events),
            "queries": self.queries,
            "resolutions": self.resolutions,
            "events": self.events
        }
    
    def save_session(self):
        """Save session to database."""
        try:
            session = get_db_session()
            
            # Save as user activity
            activity = UserActivity(
                user_email=self.user_email,
                event_type="session_complete",
                event_data=json.dumps(self.get_session_summary()),
                session_id=self.session_id
            )
            session.add(activity)
            session.commit()
            
            logger.debug(f"Session {self.session_id} saved for {self.user_email}")
            
        except Exception as e:
            logger.debug(f"Failed to save session: {e}")


def track_analysis(user_email: Optional[str], game: str, mod_count: int, conflict_count: int):
    """Track an analysis request."""
    try:
        session = get_db_session()
        activity = UserActivity(
            user_email=user_email,
            event_type="analysis",
            event_data=json.dumps({
                "game": game,
                "mod_count": mod_count,
                "conflict_count": conflict_count
            }),
            session_id=session.get("session_id", "anonymous") if hasattr(session, 'get') else "anonymous"
        )
        session.add(activity)
        session.commit()
    except Exception as e:
        logger.debug(f"Failed to track analysis: {e}")


def track_search(user_email: Optional[str], query: str, game: str, results_count: int):
    """Track a search request."""
    try:
        session = get_db_session()
        activity = UserActivity(
            user_email=user_email,
            event_type="search",
            event_data=json.dumps({
                "query": query,
                "game": game,
                "results_count": results_count
            }),
            session_id="anonymous"
        )
        session.add(activity)
        session.commit()
    except Exception as e:
        logger.debug(f"Failed to track search: {e}")


def track_chat(user_email: Optional[str], message: str, game: str, had_resolution: bool):
    """Track a chat interaction."""
    try:
        session = get_db_session()
        activity = UserActivity(
            user_email=user_email,
            event_type="chat",
            event_data=json.dumps({
                "message_len": len(message),
                "game": game,
                "had_resolution": had_resolution
            }),
            session_id="anonymous"
        )
        session.add(activity)
        session.commit()
    except Exception as e:
        logger.debug(f"Failed to track chat: {e}")


def submit_feedback(
    user_email: Optional[str],
    feedback_type: str,
    category: str,
    content: str,
    context: Optional[Dict[str, Any]] = None,
    rating: Optional[int] = None
) -> bool:
    """
    Submit user feedback.
    
    Args:
        user_email: User's email (optional for anonymous)
        feedback_type: "bug", "suggestion", "praise", "confusion", "other"
        category: Category like "ui", "conflict_detection", "recommendations", etc.
        content: Feedback text
        context: Additional context (page, action, etc.)
        rating: 1-5 rating if applicable
        
    Returns:
        True if saved successfully
    """
    try:
        session = get_db_session()
        
        # Determine priority based on type
        priority_map = {
            "bug": 3,
            "suggestion": 1,
            "praise": 0,
            "confusion": 2,
            "other": 0
        }
        priority = priority_map.get(feedback_type, 0)
        
        # Boost priority for certain categories
        if category in ["crash", "data_loss", "security"]:
            priority = 5
        
        feedback = UserFeedback(
            user_email=user_email,
            type=feedback_type,
            category=category,
            content=content,
            context_json=json.dumps(context) if context else None,
            status="open",
            priority=priority
        )
        session.add(feedback)
        
        # Also save as satisfaction survey if rating provided
        if rating:
            survey = SatisfactionSurvey(
                user_email=user_email,
                rating=rating,
                feedback_text=content,
                context_json=json.dumps(context) if context else None
            )
            session.add(survey)
        
        session.commit()
        
        # Log to self-improvement
        log_self_improvement(feedback_type, category, content, rating)
        
        logger.info(f"Feedback submitted: {feedback_type}/{category} from {user_email}")
        return True
        
    except Exception as e:
        logger.debug(f"Failed to submit feedback: {e}")
        return False


def submit_rating(user_email: Optional[str], rating: int, context: Dict[str, Any]):
    """Submit a simple 1-5 rating with context."""
    return submit_feedback(
        user_email=user_email,
        feedback_type="rating",
        category=context.get("category", "general"),
        content=f"User rated {rating}/5",
        context=context,
        rating=rating
    )


def submit_bug_report(user_email: Optional[str], description: str, context: Dict[str, Any]):
    """Submit a bug report."""
    return submit_feedback(
        user_email=user_email,
        feedback_type="bug",
        category=context.get("category", "technical"),
        content=description,
        context=context
    )


def submit_suggestion(user_email: Optional[str], suggestion: str, context: Dict[str, Any]):
    """Submit a feature suggestion."""
    return submit_feedback(
        user_email=user_email,
        feedback_type="suggestion",
        category=context.get("category", "feature"),
        content=suggestion,
        context=context
    )


# =============================================================================
# Self-Improvement Log
# =============================================================================

# In-memory log that accumulates during the week
# Flushed to database and included in weekly report
_self_improvement_log: List[Dict[str, Any]] = []


def log_self_improvement(
    event_type: str,
    category: str,
    description: str,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Log an event to the self-improvement log.
    
    This runs alongside normal operations and accumulates events
    for the weekly report to Chris.
    
    Args:
        event_type: "win", "issue", "suggestion", "observation", "metric"
        category: Category like "ui", "performance", "accuracy", etc.
        description: What happened
        metadata: Additional data (counts, percentages, etc.)
    """
    entry = {
        "timestamp": datetime.now().isoformat(),
        "event_type": event_type,
        "category": category,
        "description": description,
        "metadata": metadata or {}
    }
    
    _self_improvement_log.append(entry)
    
    # Also save to database for persistence
    try:
        session = get_db_session()
        activity = UserActivity(
            user_email="system",
            event_type="self_improvement_log",
            event_data=json.dumps(entry),
            session_id="system"
        )
        session.add(activity)
        session.commit()
    except Exception as e:
        logger.debug(f"Failed to log self-improvement event: {e}")


def log_win(category: str, description: str, impact: Optional[str] = None):
    """Log a win/success."""
    log_self_improvement(
        event_type="win",
        category=category,
        description=description,
        metadata={"impact": impact}
    )


def log_issue(category: str, description: str, severity: str = "medium"):
    """Log an issue/problem."""
    log_self_improvement(
        event_type="issue",
        category=category,
        description=description,
        metadata={"severity": severity}
    )


def log_suggestion(category: str, description: str, effort: str = "unknown"):
    """Log a suggestion for improvement."""
    log_self_improvement(
        event_type="suggestion",
        category=category,
        description=description,
        metadata={"effort": effort}
    )


def log_observation(category: str, description: str, data: Optional[Dict[str, Any]] = None):
    """Log an observation."""
    log_self_improvement(
        event_type="observation",
        category=category,
        description=description,
        metadata=data or {}
    )


def log_metric(name: str, value: float, unit: str = "", context: Optional[str] = None):
    """Log a metric."""
    log_self_improvement(
        event_type="metric",
        category="metrics",
        description=f"{name}: {value}{unit}",
        metadata={
            "metric_name": name,
            "value": value,
            "unit": unit,
            "context": context
        }
    )


def get_self_improvement_log(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> List[Dict[str, Any]]:
    """
    Get self-improvement log entries.
    
    Args:
        start_date: Filter from this date (default: 7 days ago)
        end_date: Filter to this date (default: now)
        
    Returns:
        List of log entries
    """
    if start_date is None:
        start_date = datetime.now() - timedelta(days=7)
    if end_date is None:
        end_date = datetime.now()
    
    # Filter in-memory log
    filtered = [
        entry for entry in _self_improvement_log
        if start_date <= datetime.fromisoformat(entry["timestamp"]) <= end_date
    ]
    
    # Also get from database
    try:
        session = get_db_session()
        activities = session.query(UserActivity).filter(
            UserActivity.event_type == "self_improvement_log",
            UserActivity.created_at >= start_date,
            UserActivity.created_at <= end_date
        ).all()
        
        for activity in activities:
            try:
                entry = json.loads(activity.event_data)
                if entry not in filtered:
                    filtered.append(entry)
            except (json.JSONDecodeError, TypeError):
                pass
        
        # Sort by timestamp
        filtered.sort(key=lambda x: x.get("timestamp", ""))
        
    except Exception as e:
        logger.debug(f"Failed to get self-improvement log from database: {e}")
    
    return filtered


def clear_self_improvement_log(before_date: Optional[datetime] = None):
    """
    Clear old log entries (after they've been included in weekly report).
    
    Args:
        before_date: Clear entries before this date (default: now)
    """
    global _self_improvement_log
    
    if before_date is None:
        before_date = datetime.now()
    
    # Clear in-memory log
    _self_improvement_log = [
        entry for entry in _self_improvement_log
        if datetime.fromisoformat(entry["timestamp"]) > before_date
    ]
    
    # Clear database entries
    try:
        session = get_db_session()
        activities = session.query(UserActivity).filter(
            UserActivity.event_type == "self_improvement_log",
            UserActivity.created_at < before_date
        ).all()
        
        for activity in activities:
            session.delete(activity)
        
        session.commit()
        
    except Exception as e:
        logger.debug(f"Failed to clear self-improvement log: {e}")


# =============================================================================
# Post-Session Curation
# =============================================================================

def curate_after_session(session_summary: Dict[str, Any]):
    """
    Curate learnings from a user session.
    
    This runs async after the user signs out (doesn't slow down sign-out).
    
    Tasks:
    - Identify successful resolutions
    - Flag confusing interactions
    - Extract new patterns
    - Update knowledge base if needed
    """
    logger.debug(f"Curating session {session_summary.get('session_id')}...")
    
    try:
        queries = session_summary.get("queries", [])
        resolutions = session_summary.get("resolutions", [])
        
        # Track successful patterns
        for resolution in resolutions:
            if resolution.get("helpful"):
                log_win(
                    category="resolution",
                    description=f"Successful resolution: {resolution.get('type')}",
                    impact=f"Helped user with {len(queries)} queries"
                )
        
        # Identify gaps (queries without resolutions)
        if len(queries) > len(resolutions):
            unanswered = len(queries) - len(resolutions)
            log_issue(
                category="coverage_gap",
                description=f"{unanswered} queries went unanswered",
                severity="medium"
            )
        
        # Track session metrics
        duration = session_summary.get("duration_seconds", 0)
        if duration > 0:
            log_metric(
                name="session_duration",
                value=duration,
                unit="s",
                context=f"{session_summary.get('query_count', 0)} queries"
            )
        
        # Save curation result
        session = get_db_session()
        activity = UserActivity(
            user_email=session_summary.get("user_email"),
            event_type="session_curated",
            event_data=json.dumps({
                "session_id": session_summary.get("session_id"),
                "curated_at": datetime.now().isoformat(),
                "wins": len([r for r in resolutions if r.get("helpful")]),
                "gaps": len(queries) - len(resolutions)
            }),
            session_id=session_summary.get("session_id")
        )
        session.add(activity)
        session.commit()
        
        logger.debug(f"Session curation complete")
        
    except Exception as e:
        logger.debug(f"Session curation failed: {e}")


def schedule_post_session_curation(session_tracker: SessionTracker):
    """
    Schedule curation to run after session ends.
    
    This should be called when user signs out, but the curation
    runs async so it doesn't block the sign-out process.
    """
    import threading
    
    session_summary = session_tracker.get_session_summary()
    
    # Run in background thread
    thread = threading.Thread(
        target=curate_after_session,
        args=(session_summary,),
        daemon=True
    )
    thread.start()
    
    logger.debug(f"Post-session curation scheduled for {session_tracker.session_id}")


# =============================================================================
# Feedback Analytics
# =============================================================================

def get_feedback_summary(days: int = 7) -> Dict[str, Any]:
    """
    Get feedback summary for the last N days.
    
    Returns:
        {
            "total_feedback": int,
            "by_type": {...},
            "by_category": {...},
            "average_rating": float,
            "top_issues": [...],
            "top_suggestions": [...]
        }
    """
    session = get_db_session()
    start_date = datetime.now() - timedelta(days=days)
    
    try:
        # Get all feedback
        feedback = session.query(UserFeedback).filter(
            UserFeedback.created_at >= start_date
        ).all()
        
        # Count by type
        by_type: Dict[str, int] = {}
        by_category: Dict[str, int] = {}
        top_issues = []
        top_suggestions = []
        
        for item in feedback:
            by_type[item.type] = by_type.get(item.type, 0) + 1
            by_category[item.category] = by_category.get(item.category, 0) + 1
            
            if item.type == "bug" and item.priority >= 3:
                top_issues.append({
                    "category": item.category,
                    "content": item.content,
                    "priority": item.priority
                })
            
            if item.type == "suggestion":
                top_suggestions.append({
                    "category": item.category,
                    "content": item.content
                })
        
        # Get average rating
        ratings = session.query(SatisfactionSurvey).filter(
            SatisfactionSurvey.created_at >= start_date
        ).all()
        
        avg_rating = 0.0
        if ratings:
            avg_rating = sum(r.rating for r in ratings) / len(ratings)
        
        # Sort by priority
        top_issues.sort(key=lambda x: -x["priority"])
        
        return {
            "total_feedback": len(feedback),
            "by_type": by_type,
            "by_category": by_category,
            "average_rating": round(avg_rating, 2),
            "top_issues": top_issues[:10],
            "top_suggestions": top_suggestions[:10]
        }
        
    except Exception as e:
        logger.debug(f"Failed to get feedback summary: {e}")
        return {
            "total_feedback": 0,
            "by_type": {},
            "by_category": {},
            "average_rating": 0.0,
            "top_issues": [],
            "top_suggestions": []
        }
