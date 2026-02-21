"""
Database Migration: Samson Telemetry Tables

Adds:
- samson_telemetry_config: Instance configuration (anonymized ID)
- samson_telemetry_events: Anonymized usage events
- samson_wellness_proxies: User wellness proxy metrics

This is the foundation for The Samson Project's training reservoir.
All data is anonymized, aggregated, and opt-in.

Run: python3 migrations/add_samson_telemetry.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///users.db")


def migrate():
    """Run database migration."""
    print("Starting Samson telemetry migration...")
    print(f"Database: {DATABASE_URL}")

    engine = create_engine(DATABASE_URL)

    with engine.connect() as conn:
        print("\nCreating telemetry tables...")

        # Telemetry Config Table (instance ID)
        conn.execute(
            text("""
            CREATE TABLE IF NOT EXISTS samson_telemetry_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT NOT NULL UNIQUE,
                value TEXT NOT NULL,
                created_at REAL NOT NULL
            )
        """)
        )

        # Telemetry Events Table (anonymized usage tracking)
        conn.execute(
            text("""
            CREATE TABLE IF NOT EXISTS samson_telemetry_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                instance_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                feature TEXT NOT NULL,
                game TEXT,
                mod_a TEXT,
                mod_b TEXT,
                outcome TEXT,
                user_hash TEXT,
                metadata TEXT,
                created_at REAL NOT NULL
            )
        """)
        )

        # Wellness Proxies Table (user flourishing metrics)
        conn.execute(
            text("""
            CREATE TABLE IF NOT EXISTS samson_wellness_proxies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_hash TEXT NOT NULL,
                proxy_type TEXT NOT NULL CHECK(proxy_type IN ('autonomy', 'thriving', 'environment')),
                value REAL NOT NULL CHECK(value >= 0 AND value <= 1),
                context TEXT,
                created_at REAL NOT NULL
            )
        """)
        )

        # Create indexes for performance
        print("\nCreating indexes...")
        conn.execute(
            text("""
            CREATE INDEX IF NOT EXISTS idx_telemetry_event_type ON samson_telemetry_events(event_type, feature)
        """)
        )
        conn.execute(
            text("""
            CREATE INDEX IF NOT EXISTS idx_telemetry_created ON samson_telemetry_events(created_at DESC)
        """)
        )
        conn.execute(
            text("""
            CREATE INDEX IF NOT EXISTS idx_telemetry_user ON samson_telemetry_events(user_hash, created_at)
        """)
        )
        conn.execute(
            text("""
            CREATE INDEX IF NOT EXISTS idx_wellness_user ON samson_wellness_proxies(user_hash, proxy_type)
        """)
        )
        conn.execute(
            text("""
            CREATE INDEX IF NOT EXISTS idx_wellness_created ON samson_wellness_proxies(created_at DESC)
        """)
        )

        conn.commit()

    print("\n✅ Migration completed successfully!")
    print("\nTables created:")
    print("  - samson_telemetry_config (instance configuration)")
    print("  - samson_telemetry_events (anonymized usage tracking)")
    print("  - samson_wellness_proxies (user flourishing metrics)")
    print("\nIndexes created:")
    print("  - idx_telemetry_event_type (fast event filtering)")
    print("  - idx_telemetry_created (time-series queries)")
    print("  - idx_telemetry_user (per-user export/delete)")
    print("  - idx_wellness_user (wellness tracking per user)")
    print("  - idx_wellness_created (wellness trends over time)")
    print("\n🔒 Privacy Guarantees:")
    print("  - No PII stored (user_email is hashed, not stored)")
    print("  - Instance ID is random UUID, not tied to device/user")
    print("  - Users can export/delete their data at any time")
    print("  - Telemetry is opt-in (SAMSON_TELEMETRY_ENABLED env var)")
    print("\n🎯 This feeds The Samson Project's training reservoir.")
    print("   Conflict patterns → Ecological models")
    print("   Community voting → Democratic governance")
    print("   Wellness proxies → Compute throttling (Phase V)")


if __name__ == "__main__":
    migrate()
