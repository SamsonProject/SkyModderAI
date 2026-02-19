"""
Database Migration: Add Sponsor Tables

Adds:
- sponsors: Sponsor information
- sponsor_creatives: Multiple ad creatives per sponsor
- sponsor_clicks: Click tracking for billing (audit trail)
- sponsor_votes: Community voting

Run: python3 migrations/add_sponsor_tables.py

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
    print("Starting sponsor tables migration...")
    print(f"Database: {DATABASE_URL}")

    # Create engine with PostgreSQL-compatible settings
    engine = create_engine(DATABASE_URL, echo=True)

    # Create tables
    print("\nCreating sponsor tables...")
    with engine.connect() as conn:
        # Check if PostgreSQL
        is_postgresql = engine.dialect.name == "postgresql"
        serial_type = "SERIAL" if is_postgresql else "INTEGER"
        auto_increment = "" if is_postgresql else "AUTOINCREMENT"
        boolean_type = "BOOLEAN" if is_postgresql else "INTEGER"
        true_value = "TRUE" if is_postgresql else "1"
        false_value = "FALSE" if is_postgresql else "0"

        # Sponsors table
        conn.execute(
            text(f"""
            CREATE TABLE IF NOT EXISTS sponsors (
                id {serial_type} {auto_increment} PRIMARY KEY,
                sponsor_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                website TEXT NOT NULL,
                contact_email TEXT,
                product_description TEXT,
                logo_url TEXT,
                landing_url TEXT,
                description TEXT,
                category TEXT NOT NULL,

                -- Pricing
                pricing_model TEXT DEFAULT 'pay_per_click',
                cpm_rate REAL DEFAULT 5.00,
                plan_clicks {serial_type} {auto_increment} DEFAULT 10000,
                plan_price REAL DEFAULT 50.00,
                click_credits {serial_type} {auto_increment} DEFAULT 0,

                -- Performance
                impressions {serial_type} {auto_increment} DEFAULT 0,
                clicks {serial_type} {auto_increment} DEFAULT 0,
                ctr REAL DEFAULT 0.0,
                monthly_spend REAL DEFAULT 0.0,
                billable_clicks {serial_type} {auto_increment} DEFAULT 0,

                -- Community score (separate from CTR)
                community_score REAL DEFAULT 0.0,
                community_votes {serial_type} {auto_increment} DEFAULT 0,

                -- Ranking score (computed: community * 0.6 + normalized_ctr * 0.4)
                ranking_score REAL DEFAULT 0.0,

                -- Status
                status TEXT DEFAULT 'pending',
                verified_date TIMESTAMP,
                approved_at TIMESTAMP,
                approved_by TEXT,
                rejected_at TIMESTAMP,
                rejected_reason TEXT,

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        )

        # Sponsor creatives table (multiple ads per sponsor)
        conn.execute(
            text(f"""
            CREATE TABLE IF NOT EXISTS sponsor_creatives (
                id {serial_type} {auto_increment} PRIMARY KEY,
                creative_id TEXT UNIQUE NOT NULL,
                sponsor_id TEXT NOT NULL,
                name TEXT,
                image_url TEXT,
                headline TEXT,
                body_copy TEXT,
                landing_url TEXT,
                status TEXT DEFAULT 'active',
                impressions {serial_type} {auto_increment} DEFAULT 0,
                clicks {serial_type} {auto_increment} DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                paused_at TIMESTAMP,

                FOREIGN KEY (sponsor_id) REFERENCES sponsors(sponsor_id)
            )
        """)
        )

        # Index for creative rotation (find lowest impressions)
        conn.execute(
            text("""
            CREATE INDEX IF NOT EXISTS idx_sponsor_creatives_rotation
            ON sponsor_creatives(sponsor_id, status, impressions)
        """)
        )

        # Sponsor clicks table (billing audit trail)
        conn.execute(
            text(f"""
            CREATE TABLE IF NOT EXISTS sponsor_clicks (
                id {serial_type} {auto_increment} PRIMARY KEY,
                sponsor_id TEXT NOT NULL,
                creative_id TEXT,
                user_id TEXT,
                fingerprint_hash TEXT NOT NULL,
                billable {boolean_type} DEFAULT {false_value},
                rejection_reason TEXT,
                timestamp REAL NOT NULL,

                FOREIGN KEY (sponsor_id) REFERENCES sponsors(sponsor_id),
                FOREIGN KEY (creative_id) REFERENCES sponsor_creatives(creative_id)
            )
        """)
        )

        # Index for fraud detection
        conn.execute(
            text("""
            CREATE INDEX IF NOT EXISTS idx_sponsor_clicks_fingerprint
            ON sponsor_clicks(fingerprint_hash, sponsor_id, timestamp)
        """)
        )

        # Index for billing queries
        conn.execute(
            text("""
            CREATE INDEX IF NOT EXISTS idx_sponsor_clicks_billable
            ON sponsor_clicks(billable, sponsor_id, timestamp)
        """)
        )

        # Sponsor votes table (community ranking)
        conn.execute(
            text(f"""
            CREATE TABLE IF NOT EXISTS sponsor_votes (
                user_id TEXT NOT NULL,
                sponsor_id TEXT NOT NULL,
                score INTEGER NOT NULL CHECK(score >= 1 AND score <= 5),
                voted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (sponsor_id) REFERENCES sponsors(sponsor_id),
                PRIMARY KEY (user_id, sponsor_id)
            )
        """)
        )

        # Index for community score calculation
        conn.execute(
            text("""
            CREATE INDEX IF NOT EXISTS idx_sponsor_votes_sponsor
            ON sponsor_votes(sponsor_id, score)
        """)
        )

        conn.commit()

    print("\n✅ Migration completed successfully!")
    print("\nTables created:")
    print("  - sponsors")
    print("  - sponsor_creatives (multiple ads per sponsor)")
    print("  - sponsor_clicks (billing audit trail)")
    print("  - sponsor_votes (community ranking)")
    print("\nIndexes created:")
    print("  - idx_sponsor_creatives_rotation (creative rotation)")
    print("  - idx_sponsor_clicks_fingerprint (fraud detection)")
    print("  - idx_sponsor_clicks_billable (billing)")
    print("  - idx_sponsor_votes_sponsor (community score)")


if __name__ == "__main__":
    migrate()
