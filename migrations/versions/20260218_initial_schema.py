"""Initial schema migration for SkyModderAI

Revision ID: initial
Revises:
Create Date: 2026-02-18

"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial database schema."""

    # Users table
    op.create_table(
        "users",
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("tier", sa.String(50), nullable=True, default="free"),
        sa.Column("customer_id", sa.String(255), nullable=True),
        sa.Column("subscription_id", sa.String(255), nullable=True),
        sa.Column("email_verified", sa.Boolean, default=False),
        sa.Column("password_hash", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=True),
        sa.Column("last_updated", sa.DateTime, nullable=True),
        sa.PrimaryKeyConstraint("email"),
    )

    # User sessions table
    op.create_table(
        "user_sessions",
        sa.Column("token", sa.String(255), nullable=False),
        sa.Column("display_id", sa.String(50), nullable=False),
        sa.Column("user_email", sa.String(255), nullable=False),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=True),
        sa.Column("last_seen", sa.DateTime, nullable=True),
        sa.Column("expires_at", sa.Integer, nullable=False),
        sa.PrimaryKeyConstraint("token"),
        sa.UniqueConstraint("display_id"),
        sa.ForeignKeyConstraint(["user_email"], ["users.email"]),
    )

    # API keys table
    op.create_table(
        "api_keys",
        sa.Column("id", sa.Integer, nullable=False),
        sa.Column("user_email", sa.String(255), nullable=False),
        sa.Column("key_hash", sa.String(255), nullable=False),
        sa.Column("key_prefix", sa.String(20), nullable=False),
        sa.Column("label", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key_hash"),
        sa.ForeignKeyConstraint(["user_email"], ["users.email"]),
    )

    # Saved mod lists table
    op.create_table(
        "user_saved_lists",
        sa.Column("id", sa.Integer, nullable=False),
        sa.Column("user_email", sa.String(255), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("game", sa.String(50), nullable=True),
        sa.Column("game_version", sa.String(50), nullable=True),
        sa.Column("masterlist_version", sa.String(50), nullable=True),
        sa.Column("tags", sa.Text, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("preferences_json", sa.Text, nullable=True),
        sa.Column("source", sa.String(50), nullable=True),
        sa.Column("list_text", sa.Text, nullable=False),
        sa.Column("analysis_snapshot", sa.Text, nullable=True),
        sa.Column("saved_at", sa.DateTime, nullable=True),
        sa.Column("updated_at", sa.DateTime, nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_email", "name", name="uq_user_list_name"),
        sa.ForeignKeyConstraint(["user_email"], ["users.email"]),
    )

    # Community posts table
    op.create_table(
        "community_posts",
        sa.Column("id", sa.Integer, nullable=False),
        sa.Column("user_email", sa.String(255), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("tag", sa.String(50), nullable=True, default="general"),
        sa.Column("created_at", sa.DateTime, nullable=True),
        sa.Column("moderated", sa.Boolean, default=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_email"], ["users.email"]),
    )

    # Community replies table
    op.create_table(
        "community_replies",
        sa.Column("id", sa.Integer, nullable=False),
        sa.Column("post_id", sa.Integer, nullable=False),
        sa.Column("user_email", sa.String(255), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=True),
        sa.Column("moderated", sa.Boolean, default=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["post_id"], ["community_posts.id"]),
        sa.ForeignKeyConstraint(["user_email"], ["users.email"]),
    )

    # Community votes table
    op.create_table(
        "community_votes",
        sa.Column("post_id", sa.Integer, nullable=False),
        sa.Column("user_email", sa.String(255), nullable=False),
        sa.Column("vote", sa.Integer, nullable=False),
        sa.PrimaryKeyConstraint("post_id", "user_email"),
        sa.ForeignKeyConstraint(["post_id"], ["community_posts.id"]),
        sa.ForeignKeyConstraint(["user_email"], ["users.email"]),
    )

    # Community reports table
    op.create_table(
        "community_reports",
        sa.Column("id", sa.Integer, nullable=False),
        sa.Column("post_id", sa.Integer, nullable=True),
        sa.Column("reply_id", sa.Integer, nullable=True),
        sa.Column("reporter_email", sa.String(255), nullable=True),
        sa.Column("reason", sa.Text, nullable=False),
        sa.Column("details", sa.Text, nullable=True),
        sa.Column("status", sa.String(50), nullable=True, default="open"),
        sa.Column("created_at", sa.DateTime, nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["post_id"], ["community_posts.id"]),
        sa.ForeignKeyConstraint(["reporter_email"], ["users.email"]),
    )

    # OpenCLAW grants table
    op.create_table(
        "openclaw_grants",
        sa.Column("id", sa.Integer, nullable=False),
        sa.Column("user_email", sa.String(255), nullable=False),
        sa.Column("token_hash", sa.String(255), nullable=False),
        sa.Column("workspace_rel", sa.String(500), nullable=False),
        sa.Column("ip_hash", sa.String(100), nullable=True),
        sa.Column("acknowledged_at", sa.DateTime, nullable=True),
        sa.Column("expires_at", sa.Integer, nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
        sa.ForeignKeyConstraint(["user_email"], ["users.email"]),
    )

    # OpenCLAW events table
    op.create_table(
        "openclaw_events",
        sa.Column("id", sa.Integer, nullable=False),
        sa.Column("user_email", sa.String(255), nullable=True),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("operation", sa.String(50), nullable=True),
        sa.Column("rel_path", sa.String(500), nullable=True),
        sa.Column("allowed", sa.Boolean, nullable=True, default=False),
        sa.Column("reasons_json", sa.Text, nullable=True),
        sa.Column("ip_hash", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_email"], ["users.email"]),
    )

    # OpenCLAW permissions table
    op.create_table(
        "openclaw_permissions",
        sa.Column("user_email", sa.String(255), nullable=False),
        sa.Column("scope", sa.String(100), nullable=False),
        sa.Column("granted", sa.Boolean, nullable=True, default=False),
        sa.Column("granted_at", sa.DateTime, nullable=True),
        sa.PrimaryKeyConstraint("user_email", "scope"),
        sa.ForeignKeyConstraint(["user_email"], ["users.email"]),
    )

    # OpenCLAW plan runs table
    op.create_table(
        "openclaw_plan_runs",
        sa.Column("id", sa.Integer, nullable=False),
        sa.Column("user_email", sa.String(255), nullable=False),
        sa.Column("plan_id", sa.String(100), nullable=False),
        sa.Column("game", sa.String(50), nullable=False),
        sa.Column("objective", sa.Text, nullable=True),
        sa.Column("status", sa.String(50), nullable=True, default="proposed"),
        sa.Column("plan_json", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=True),
        sa.Column("executed_at", sa.DateTime, nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("plan_id"),
        sa.ForeignKeyConstraint(["user_email"], ["users.email"]),
    )

    # OpenCLAW feedback table
    op.create_table(
        "openclaw_feedback",
        sa.Column("id", sa.Integer, nullable=False),
        sa.Column("user_email", sa.String(255), nullable=False),
        sa.Column("game", sa.String(50), nullable=False),
        sa.Column("fps_avg", sa.Integer, nullable=True),
        sa.Column("crashes", sa.Integer, nullable=True, default=0),
        sa.Column("stutter_events", sa.Integer, nullable=True, default=0),
        sa.Column("enjoyment_score", sa.Integer, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("feedback_json", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_email"], ["users.email"]),
    )

    # User feedback table
    op.create_table(
        "user_feedback",
        sa.Column("id", sa.Integer, nullable=False),
        sa.Column("user_email", sa.String(255), nullable=True),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("context_json", sa.Text, nullable=True),
        sa.Column("status", sa.String(50), nullable=True, default="open"),
        sa.Column("priority", sa.Integer, nullable=True, default=0),
        sa.Column("created_at", sa.DateTime, nullable=True),
        sa.Column("resolved_at", sa.DateTime, nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_email"], ["users.email"]),
    )

    # User activity table
    op.create_table(
        "user_activity",
        sa.Column("id", sa.Integer, nullable=False),
        sa.Column("user_email", sa.String(255), nullable=True),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("event_data", sa.Text, nullable=True),
        sa.Column("session_id", sa.String(100), nullable=True),
        sa.Column("ip_hash", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_email"], ["users.email"]),
    )

    # Satisfaction surveys table
    op.create_table(
        "satisfaction_surveys",
        sa.Column("id", sa.Integer, nullable=False),
        sa.Column("user_email", sa.String(255), nullable=True),
        sa.Column("rating", sa.Integer, nullable=False),
        sa.Column("feedback_text", sa.Text, nullable=True),
        sa.Column("context_json", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_email"], ["users.email"]),
    )

    # Conflict stats table
    op.create_table(
        "conflict_stats",
        sa.Column("id", sa.Integer, nullable=False),
        sa.Column("game", sa.String(50), nullable=True),
        sa.Column("mod_a", sa.String(255), nullable=True),
        sa.Column("mod_b", sa.String(255), nullable=True),
        sa.Column("conflict_type", sa.String(100), nullable=True),
        sa.Column("last_seen", sa.DateTime, nullable=True),
        sa.Column("occurrence_count", sa.Integer, nullable=True, default=1),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("game", "mod_a", "mod_b", "conflict_type", name="uq_conflict_stat"),
    )


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table("conflict_stats")
    op.drop_table("satisfaction_surveys")
    op.drop_table("user_activity")
    op.drop_table("user_feedback")
    op.drop_table("openclaw_feedback")
    op.drop_table("openclaw_plan_runs")
    op.drop_table("openclaw_permissions")
    op.drop_table("openclaw_events")
    op.drop_table("openclaw_grants")
    op.drop_table("community_reports")
    op.drop_table("community_votes")
    op.drop_table("community_replies")
    op.drop_table("community_posts")
    op.drop_table("user_saved_lists")
    op.drop_table("api_keys")
    op.drop_table("user_sessions")
    op.drop_table("users")
