"""
Database Migration: Add Reliability & Credibility Tables
Migration Date: February 18, 2026

Adds:
- source_credibility: Track reliability scores for information sources
- knowledge_sources: Indexed knowledge with version tagging
- trash_bin: Quarantine for items pending review/deletion

Also adds indexes for frequently queried columns.
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text

from models import Base

# Database URL from environment or default
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///instance/app.db")


def migrate():
    """Run database migration."""
    print("Starting migration...")
    print(f"Database: {DATABASE_URL}")

    # Create engine
    engine = create_engine(DATABASE_URL, echo=True)

    # Create all tables (including new ones)
    print("\nCreating new tables...")
    Base.metadata.create_all(engine)

    # Add indexes for frequently queried columns
    print("\nCreating indexes...")
    with engine.connect() as conn:
        # Index for knowledge source lookups by game + version
        conn.execute(
            text("""
            CREATE INDEX IF NOT EXISTS idx_knowledge_game_version 
            ON knowledge_sources(game, game_version)
        """)
        )

        # Index for knowledge source category lookups
        conn.execute(
            text("""
            CREATE INDEX IF NOT EXISTS idx_knowledge_category 
            ON knowledge_sources(category, subcategory)
        """)
        )

        # Index for trash bin status
        conn.execute(
            text("""
            CREATE INDEX IF NOT EXISTS idx_trash_status 
            ON trash_bin(item_type, reviewed, created_at)
        """)
        )

        # Index for source credibility lookups
        conn.execute(
            text("""
            CREATE INDEX IF NOT EXISTS idx_source_credibility_score 
            ON source_credibility(overall_score, confidence)
        """)
        )

        # Index for mod database name lookups (frequently searched)
        conn.execute(
            text("""
            CREATE INDEX IF NOT EXISTS idx_mods_clean_name 
            ON mod_database(clean_name)
        """)
        )

        # Index for conflicts by type
        conn.execute(
            text("""
            CREATE INDEX IF NOT EXISTS idx_conflicts_type 
            ON conflicts(conflict_type)
        """)
        )

        # Index for user sessions by email
        conn.execute(
            text("""
            CREATE INDEX IF NOT EXISTS idx_sessions_email 
            ON user_sessions(user_email)
        """)
        )

        conn.commit()

    print("\n✅ Migration completed successfully!")
    print("\nNew tables created:")
    print("  - source_credibility")
    print("  - knowledge_sources")
    print("  - trash_bin")
    print("\nIndexes created:")
    print("  - idx_knowledge_game_version")
    print("  - idx_knowledge_category")
    print("  - idx_trash_status")
    print("  - idx_source_credibility_score")
    print("  - idx_mods_clean_name")
    print("  - idx_conflicts_type")
    print("  - idx_sessions_email")
    print("  - idx_user_activity")


if __name__ == "__main__":
    migrate()
