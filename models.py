"""
SkyModderAI - SQLAlchemy Models

Professional-grade ORM models for database operations.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()


# =============================================================================
# User Models
# =============================================================================


class User(Base):
    """User account model."""

    __tablename__ = "users"

    email = Column(String(255), primary_key=True)
    tier = Column(String(50), default="free")
    customer_id = Column(String(255), nullable=True)
    subscription_id = Column(String(255), nullable=True)
    email_verified = Column(Boolean, default=False)
    password_hash = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_updated = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    saved_lists = relationship("SavedModList", back_populates="user", cascade="all, delete-orphan")
    posts = relationship("CommunityPost", back_populates="user", cascade="all, delete-orphan")
    replies = relationship("CommunityReply", back_populates="user", cascade="all, delete-orphan")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "email": self.email,
            "tier": self.tier,
            "email_verified": self.email_verified,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class UserSession(Base):
    """User session model for device management."""

    __tablename__ = "user_sessions"

    token = Column(String(255), primary_key=True)
    display_id = Column(String(50), unique=True, nullable=False)
    user_email = Column(String(255), ForeignKey("users.email"), nullable=False)
    user_agent = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_seen = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(Integer, nullable=False)

    # Relationships
    user = relationship("User", back_populates="sessions")

    def is_expired(self) -> bool:
        """Check if session is expired."""
        from time import time

        return int(time()) > self.expires_at


class APIKey(Base):
    """API key model for developer access."""

    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_email = Column(String(255), ForeignKey("users.email"), nullable=False)
    key_hash = Column(String(255), unique=True, nullable=False)
    key_prefix = Column(String(20), nullable=False)
    label = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="api_keys")


# =============================================================================
# Content Models
# =============================================================================


class SavedModList(Base):
    """Saved mod list model."""

    __tablename__ = "user_saved_lists"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_email = Column(String(255), ForeignKey("users.email"), nullable=False)
    name = Column(String(100), nullable=False)
    game = Column(String(50), nullable=True)
    game_version = Column(String(50), nullable=True)
    masterlist_version = Column(String(50), nullable=True)
    tags = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    preferences_json = Column(Text, nullable=True)
    source = Column(String(50), nullable=True)
    list_text = Column(Text, nullable=False)
    analysis_snapshot = Column(Text, nullable=True)
    saved_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (UniqueConstraint("user_email", "name", name="uq_user_list_name"),)

    # Relationships
    user = relationship("User", back_populates="saved_lists")


class CommunityPost(Base):
    """Community post model."""

    __tablename__ = "community_posts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_email = Column(String(255), ForeignKey("users.email"), nullable=False)
    content = Column(Text, nullable=False)
    tag = Column(String(50), default="general")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    moderated = Column(Boolean, default=False)

    # Relationships
    user = relationship("User", back_populates="posts")
    replies = relationship("CommunityReply", back_populates="post", cascade="all, delete-orphan")
    votes = relationship("CommunityVote", back_populates="post", cascade="all, delete-orphan")
    reports = relationship("CommunityReport", back_populates="post", cascade="all, delete-orphan")

    @property
    def vote_score(self) -> int:
        """Calculate vote score."""
        return sum(v.vote for v in self.votes)


class CommunityReply(Base):
    """Community reply model."""

    __tablename__ = "community_replies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(Integer, ForeignKey("community_posts.id"), nullable=False)
    user_email = Column(String(255), ForeignKey("users.email"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    moderated = Column(Boolean, default=False)

    # Relationships
    post = relationship("CommunityPost", back_populates="replies")
    user = relationship("User", back_populates="replies")


class CommunityVote(Base):
    """Community vote model."""

    __tablename__ = "community_votes"

    post_id = Column(Integer, ForeignKey("community_posts.id"), primary_key=True)
    user_email = Column(String(255), ForeignKey("users.email"), primary_key=True)
    vote = Column(Integer, nullable=False)

    # Relationships
    post = relationship("CommunityPost", back_populates="votes")


class CommunityReport(Base):
    """Community report model."""

    __tablename__ = "community_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(Integer, ForeignKey("community_posts.id"), nullable=True)
    reply_id = Column(Integer, nullable=True)
    reporter_email = Column(String(255), ForeignKey("users.email"), nullable=True)
    reason = Column(Text, nullable=False)
    details = Column(Text, nullable=True)
    status = Column(String(50), default="open")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    post = relationship("CommunityPost", back_populates="reports")


# =============================================================================
# OpenCLAW Models
# =============================================================================


class OpenClawGrant(Base):
    """OpenCLAW permission grant model."""

    __tablename__ = "openclaw_grants"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_email = Column(String(255), ForeignKey("users.email"), nullable=False)
    token_hash = Column(String(255), unique=True, nullable=False)
    workspace_rel = Column(String(500), nullable=False)
    ip_hash = Column(String(100), nullable=True)
    acknowledged_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(Integer, nullable=False)

    def is_expired(self) -> bool:
        """Check if grant is expired."""
        from time import time

        return int(time()) > self.expires_at


class OpenClawEvent(Base):
    """OpenCLAW event log model."""

    __tablename__ = "openclaw_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_email = Column(String(255), ForeignKey("users.email"), nullable=True)
    event_type = Column(String(100), nullable=False)
    operation = Column(String(50), nullable=True)
    rel_path = Column(String(500), nullable=True)
    allowed = Column(Boolean, default=False)
    reasons_json = Column(Text, nullable=True)
    ip_hash = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class OpenClawPermission(Base):
    """OpenCLAW permission model."""

    __tablename__ = "openclaw_permissions"

    user_email = Column(String(255), ForeignKey("users.email"), primary_key=True)
    scope = Column(String(100), primary_key=True)
    granted = Column(Boolean, default=False)
    granted_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class OpenClawPlanRun(Base):
    """OpenCLAW plan run model."""

    __tablename__ = "openclaw_plan_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_email = Column(String(255), ForeignKey("users.email"), nullable=False)
    plan_id = Column(String(100), unique=True, nullable=False)
    game = Column(String(50), nullable=False)
    objective = Column(Text, nullable=True)
    status = Column(String(50), default="proposed")
    plan_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    executed_at = Column(DateTime, nullable=True)


class OpenClawFeedback(Base):
    """OpenCLAW feedback model."""

    __tablename__ = "openclaw_feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_email = Column(String(255), ForeignKey("users.email"), nullable=False)
    game = Column(String(50), nullable=False)
    fps_avg = Column(Integer, nullable=True)
    crashes = Column(Integer, default=0)
    stutter_events = Column(Integer, default=0)
    enjoyment_score = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)
    feedback_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


# =============================================================================
# Analytics Models
# =============================================================================


class UserFeedback(Base):
    """User feedback model."""

    __tablename__ = "user_feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_email = Column(String(255), ForeignKey("users.email"), nullable=True)
    type = Column(String(50), nullable=False)
    category = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    context_json = Column(Text, nullable=True)
    status = Column(String(50), default="open")
    priority = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    resolved_at = Column(DateTime, nullable=True)


class UserActivity(Base):
    """User activity tracking model."""

    __tablename__ = "user_activity"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_email = Column(String(255), ForeignKey("users.email"), nullable=True)
    event_type = Column(String(100), nullable=False)
    event_data = Column(Text, nullable=True)
    session_id = Column(String(100), nullable=True)
    ip_hash = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class SatisfactionSurvey(Base):
    """User satisfaction survey model."""

    __tablename__ = "satisfaction_surveys"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_email = Column(String(255), ForeignKey("users.email"), nullable=True)
    rating = Column(Integer, nullable=False)
    feedback_text = Column(Text, nullable=True)
    context_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ConflictStat(Base):
    """Conflict statistics model."""

    __tablename__ = "conflict_stats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    game = Column(String(50), nullable=True)
    mod_a = Column(String(255), nullable=True)
    mod_b = Column(String(255), nullable=True)
    conflict_type = Column(String(100), nullable=True)
    last_seen = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    occurrence_count = Column(Integer, default=1)

    __table_args__ = (
        UniqueConstraint("game", "mod_a", "mod_b", "conflict_type", name="uq_conflict_stat"),
    )


# =============================================================================
# Reliability & Credibility Models
# =============================================================================


class SourceCredibility(Base):
    """Source credibility tracking for reliability weighting."""

    __tablename__ = "source_credibility"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_url = Column(String(500), unique=True, nullable=False)
    source_type = Column(String(50), nullable=False)  # nexus, reddit, forum, github, youtube
    
    # Credibility scores (0.0-1.0)
    overall_score = Column(Float, default=0.5)
    source_credibility = Column(Float, default=0.5)
    content_freshness = Column(Float, default=0.5)
    community_validation = Column(Float, default=0.5)
    technical_accuracy = Column(Float, default=0.5)
    author_reputation = Column(Float, default=0.5)
    
    # Metadata
    confidence = Column(Float, default=0.0)
    game_version = Column(String(50), nullable=True)
    content_type = Column(String(50), nullable=True)  # mod, guide, fix, news
    
    # Tracking
    last_verified = Column(DateTime, nullable=True)
    verification_count = Column(Integer, default=0)
    flags = Column(Text, nullable=True)  # JSON array of flags
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        import json
        return {
            "source_url": self.source_url,
            "source_type": self.source_type,
            "overall_score": round(self.overall_score, 3) if self.overall_score else None,
            "confidence": round(self.confidence, 3) if self.confidence else None,
            "dimensions": {
                "source_credibility": round(self.source_credibility, 3) if self.source_credibility else None,
                "content_freshness": round(self.content_freshness, 3) if self.content_freshness else None,
                "community_validation": round(self.community_validation, 3) if self.community_validation else None,
                "technical_accuracy": round(self.technical_accuracy, 3) if self.technical_accuracy else None,
                "author_reputation": round(self.author_reputation, 3) if self.author_reputation else None,
            },
            "flags": json.loads(self.flags) if self.flags else [],
            "last_verified": self.last_verified.isoformat() if self.last_verified else None,
        }


class KnowledgeSource(Base):
    """Indexed knowledge source with version tagging and categorization."""

    __tablename__ = "knowledge_sources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_url = Column(String(500), nullable=False)
    title = Column(String(500), nullable=False)
    content_hash = Column(String(64), nullable=True)  # SHA256 of content
    
    # Version tagging (rigorous)
    game = Column(String(50), nullable=False)  # skyrimse, fallout4, etc.
    game_version = Column(String(50), nullable=True)  # 1.6.1170, etc.
    mod_version = Column(String(50), nullable=True)
    
    # Categorization (AI-discoverable)
    category = Column(String(100), nullable=True)
    subcategory = Column(String(100), nullable=True)
    tags = Column(Text, nullable=True)  # JSON array
    
    # Reliability
    credibility_id = Column(Integer, ForeignKey("source_credibility.id"), nullable=True)
    credibility = relationship("SourceCredibility", backref="knowledge_sources")
    
    # Content summary (shorthand, not full content)
    summary = Column(Text, nullable=True)
    key_points = Column(Text, nullable=True)  # JSON array of key points
    
    # Linking
    conflicts_with = Column(Text, nullable=True)  # JSON array of mod IDs
    requires = Column(Text, nullable=True)  # JSON array of requirements
    compatible_with = Column(Text, nullable=True)  # JSON array
    
    # Deviation tracking
    deviation_flags = Column(Text, nullable=True)  # JSON array
    is_standard_approach = Column(Boolean, default=True)
    
    # Status
    status = Column(String(50), default="active")  # active, trash, archived
    trash_reason = Column(String(200), nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    last_accessed = Column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint("source_url", "game", name="uq_knowledge_source"),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        import json
        return {
            "id": self.id,
            "source_url": self.source_url,
            "title": self.title,
            "game": self.game,
            "game_version": self.game_version,
            "category": self.category,
            "subcategory": self.subcategory,
            "tags": json.loads(self.tags) if self.tags else [],
            "summary": self.summary,
            "key_points": json.loads(self.key_points) if self.key_points else [],
            "credibility": self.credibility.to_dict() if self.credibility else None,
            "deviation_flags": json.loads(self.deviation_flags) if self.deviation_flags else [],
            "is_standard_approach": self.is_standard_approach,
            "status": self.status,
        }


class TrashBinItem(Base):
    """Quarantined items pending review/deletion."""

    __tablename__ = "trash_bin"

    id = Column(Integer, primary_key=True, autoincrement=True)
    item_type = Column(String(50), nullable=False)  # knowledge_source, conflict, category
    item_id = Column(Integer, nullable=True)
    original_data = Column(Text, nullable=False)  # JSON of original data
    
    # Reason for trashing
    reason = Column(String(200), nullable=False)
    auto_classified = Column(Boolean, default=False)
    
    # Actions taken
    action_taken = Column(String(50), default="quarantine")  # quarantine, compacted, re-routed
    action_data = Column(Text, nullable=True)  # JSON of action result
    
    # Review
    reviewed = Column(Boolean, default=False)
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by = Column(String(255), nullable=True)  # user email or "system"
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime, nullable=True)  # Auto-delete after this date

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        import json
        return {
            "id": self.id,
            "item_type": self.item_type,
            "item_id": self.item_id,
            "reason": self.reason,
            "auto_classified": self.auto_classified,
            "action_taken": self.action_taken,
            "reviewed": self.reviewed,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }


# =============================================================================
# Database Engine
# =============================================================================


def create_database_engine(database_url: str) -> Any:
    """
    Create database engine.

    Args:
        database_url: Database connection URL

    Returns:
        SQLAlchemy engine
    """
    return create_engine(
        database_url,
        echo=False,
        pool_pre_ping=True,
        pool_recycle=3600,
    )


def create_session_factory(engine: Any) -> Any:
    """
    Create session factory.

    Args:
        engine: Database engine

    Returns:
        Session factory
    """
    return sessionmaker(bind=engine)


def init_db(database_url: str) -> None:
    """
    Initialize database schema.

    Args:
        database_url: Database connection URL
    """
    engine = create_database_engine(database_url)
    Base.metadata.create_all(engine)
