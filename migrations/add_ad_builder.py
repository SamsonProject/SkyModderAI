"""
Database Migration: Add Ad Builder Tables

Adds tables for the Ad Builder system:
- ad_designs: User and guest ad designs
- ad_templates: Template library (official + community)
- ad_assets: Asset library (images, fonts, logos)
- brand_kits: User brand kits
- guest_ad_sessions: Guest user sessions
- ad_analytics: Design analytics (Pro feature)

Features:
- Guest access (no account required)
- Account-based saving and analytics
- Template library with community contributions
- Brand kit management
- Multi-format support

Run: python3 migrations/add_ad_builder.py

PostgreSQL compatible.
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text

# Database URL from environment or default
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///instance/app.db")


def migrate():
    """Run database migration."""
    print("Starting Ad Builder migration...")
    print(f"Database: {DATABASE_URL}")

    # Create engine
    engine = create_engine(DATABASE_URL, echo=True)

    print("\nCreating Ad Builder tables...")
    with engine.connect() as conn:
        # Check if PostgreSQL
        is_postgresql = engine.dialect.name == "postgresql"

        if is_postgresql:
            id_type = "SERIAL PRIMARY KEY"
            uuid_type = "UUID PRIMARY KEY"
            timestamp_type = "TIMESTAMP"
            boolean_type = "BOOLEAN"
            true_value = "TRUE"
            false_value = "FALSE"
            json_type = "JSONB"
        else:
            id_type = "INTEGER PRIMARY KEY AUTOINCREMENT"
            uuid_type = "TEXT PRIMARY KEY"
            timestamp_type = "TIMESTAMP"
            boolean_type = "INTEGER"
            true_value = "1"
            false_value = "0"
            json_type = "TEXT"

        # Ad designs table
        conn.execute(
            text(
                f"""
            CREATE TABLE IF NOT EXISTS ad_designs (
                id {uuid_type},
                user_id TEXT,
                guest_session_id TEXT,
                name TEXT NOT NULL,
                description TEXT,
                template_id TEXT,
                design_data {json_type} NOT NULL,
                brand_kit {json_type},
                format_type TEXT DEFAULT 'custom',
                width INTEGER DEFAULT 1080,
                height INTEGER DEFAULT 1080,
                status TEXT DEFAULT 'draft',
                is_public {boolean_type} DEFAULT {false_value},
                created_at {timestamp_type} DEFAULT CURRENT_TIMESTAMP,
                updated_at {timestamp_type} DEFAULT CURRENT_TIMESTAMP,
                published_at {timestamp_type},
                view_count INTEGER DEFAULT 0,
                download_count INTEGER DEFAULT 0
            )
        """
            )
        )

        # Ad templates table
        conn.execute(
            text(
                f"""
            CREATE TABLE IF NOT EXISTS ad_templates (
                id {uuid_type},
                name TEXT NOT NULL,
                description TEXT,
                category TEXT,
                format_type TEXT NOT NULL,
                thumbnail_url TEXT,
                template_data {json_type} NOT NULL,
                preview_data {json_type},
                tags TEXT,
                difficulty TEXT DEFAULT 'easy',
                estimated_time INTEGER DEFAULT 5,
                is_official {boolean_type} DEFAULT {true_value},
                author_id TEXT,
                download_count INTEGER DEFAULT 0,
                favorite_count INTEGER DEFAULT 0,
                status TEXT DEFAULT 'active',
                created_at {timestamp_type} DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (author_id) REFERENCES users(id)
            )
        """
            )
        )

        # Ad assets table
        conn.execute(
            text(
                f"""
            CREATE TABLE IF NOT EXISTS ad_assets (
                id {uuid_type},
                user_id TEXT,
                name TEXT NOT NULL,
                asset_type TEXT,
                file_url TEXT NOT NULL,
                thumbnail_url TEXT,
                file_size INTEGER,
                dimensions {json_type},
                tags TEXT,
                is_premium {boolean_type} DEFAULT {false_value},
                license_type TEXT DEFAULT 'free',
                created_at {timestamp_type} DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """
            )
        )

        # Brand kits table
        conn.execute(
            text(
                f"""
            CREATE TABLE IF NOT EXISTS brand_kits (
                id {uuid_type},
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                primary_color TEXT DEFAULT '#3B82F6',
                secondary_color TEXT DEFAULT '#1E40AF',
                accent_color TEXT DEFAULT '#10B981',
                text_color TEXT DEFAULT '#1F2937',
                heading_font TEXT DEFAULT 'Inter',
                body_font TEXT DEFAULT 'Inter',
                logo_url TEXT,
                logo_square_url TEXT,
                brand_voice TEXT,
                is_default {boolean_type} DEFAULT {false_value},
                created_at {timestamp_type} DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """
            )
        )

        # Guest ad sessions table
        conn.execute(
            text(
                f"""
            CREATE TABLE IF NOT EXISTS guest_ad_sessions (
                session_id TEXT PRIMARY KEY,
                fingerprint_hash TEXT,
                design_data {json_type},
                created_at {timestamp_type} DEFAULT CURRENT_TIMESTAMP,
                expires_at {timestamp_type} NOT NULL,
                last_accessed {timestamp_type} DEFAULT CURRENT_TIMESTAMP
            )
        """
            )
        )

        # Ad analytics table (Pro feature)
        conn.execute(
            text(
                f"""
            CREATE TABLE IF NOT EXISTS ad_analytics (
                id {uuid_type},
                design_id TEXT,
                variant_id TEXT,
                test_id TEXT,
                views INTEGER DEFAULT 0,
                clicks INTEGER DEFAULT 0,
                downloads INTEGER DEFAULT 0,
                shares INTEGER DEFAULT 0,
                date DATE NOT NULL,
                UNIQUE(design_id, date, variant_id),
                FOREIGN KEY (design_id) REFERENCES ad_designs(id)
            )
        """
            )
        )

        # Create indexes for performance
        print("\nCreating indexes...")

        conn.execute(
            text(
                """
            CREATE INDEX IF NOT EXISTS idx_ad_designs_user_id
            ON ad_designs(user_id)
        """
            )
        )

        conn.execute(
            text(
                """
            CREATE INDEX IF NOT EXISTS idx_ad_designs_guest_session
            ON ad_designs(guest_session_id)
        """
            )
        )

        conn.execute(
            text(
                """
            CREATE INDEX IF NOT EXISTS idx_ad_designs_status
            ON ad_designs(status)
        """
            )
        )

        conn.execute(
            text(
                """
            CREATE INDEX IF NOT EXISTS idx_ad_templates_category
            ON ad_templates(category)
        """
            )
        )

        conn.execute(
            text(
                """
            CREATE INDEX IF NOT EXISTS idx_ad_templates_format
            ON ad_templates(format_type)
        """
            )
        )

        conn.execute(
            text(
                """
            CREATE INDEX IF NOT EXISTS idx_ad_assets_user_id
            ON ad_assets(user_id)
        """
            )
        )

        conn.execute(
            text(
                """
            CREATE INDEX IF NOT EXISTS idx_brand_kits_user_id
            ON brand_kits(user_id)
        """
            )
        )

        conn.execute(
            text(
                """
            CREATE INDEX IF NOT EXISTS idx_guest_sessions_expires
            ON guest_ad_sessions(expires_at)
        """
            )
        )

        conn.execute(
            text(
                """
            CREATE INDEX IF NOT EXISTS idx_ad_analytics_design_date
            ON ad_analytics(design_id, date)
        """
            )
        )

        conn.commit()

    print("\n✅ Ad Builder migration complete!")
    print("\nTables created:")
    print("  - ad_designs")
    print("  - ad_templates")
    print("  - ad_assets")
    print("  - brand_kits")
    print("  - guest_ad_sessions")
    print("  - ad_analytics")
    print("\nIndexes created for performance optimization.")


if __name__ == "__main__":
    migrate()
