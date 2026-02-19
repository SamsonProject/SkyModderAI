"""
Database Migration: Add Shopping/Advertising Tables

Adds tables for the pay-per-click advertising system:
- ad_campaigns: Business ad campaigns with budget/credits
- ad_creatives: Ad creative assets (images, copy)
- ad_clicks: Click tracking for billing (audit trail)
- ad_impressions: Impression tracking for analytics

Businesses get:
- First month FREE (automatic upon approval)
- After first month: $5/1000 clicks (pay-per-click)
- Automatic ad placement on directory and shopping pages

Run: python3 migrations/add_shopping_ads.py

PostgreSQL compatible.
"""

import os
import sys
import uuid

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text

# Database URL from environment or default
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///instance/app.db")


def migrate():
    """Run database migration."""
    print("Starting shopping ads migration...")
    print(f"Database: {DATABASE_URL}")

    # Create engine with PostgreSQL-compatible settings
    engine = create_engine(DATABASE_URL, echo=True)

    print("\nCreating shopping ads tables...")
    with engine.connect() as conn:
        # Check if PostgreSQL
        is_postgresql = engine.dialect.name == "postgresql"
        
        if is_postgresql:
            # PostgreSQL uses SERIAL for auto-increment
            id_type = "SERIAL PRIMARY KEY"
            boolean_type = "BOOLEAN"
            true_value = "TRUE"
            false_value = "FALSE"
        else:
            # SQLite uses INTEGER PRIMARY KEY for auto-increment
            id_type = "INTEGER PRIMARY KEY AUTOINCREMENT"
            boolean_type = "INTEGER"
            true_value = "1"
            false_value = "0"

        # Ad campaigns table
        conn.execute(
            text(f"""
            CREATE TABLE IF NOT EXISTS ad_campaigns (
                id {id_type},
                business_id TEXT NOT NULL,
                name TEXT NOT NULL,
                status TEXT DEFAULT 'draft',
                budget_type TEXT DEFAULT 'prepaid',
                budget_amount REAL DEFAULT 0.0,
                spent_amount REAL DEFAULT 0.0,
                click_credits INTEGER DEFAULT 0,
                click_price_per_thousand REAL DEFAULT 5.00,
                start_date TIMESTAMP,
                end_date TIMESTAMP,
                first_month_free {boolean_type} DEFAULT {false_value},
                first_month_start TIMESTAMP,
                first_month_end TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (business_id) REFERENCES businesses(id)
            )
        """)
        )

        # Ad creatives table
        conn.execute(
            text(f"""
            CREATE TABLE IF NOT EXISTS ad_creatives (
                id {id_type},
                campaign_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                image_url TEXT,
                headline TEXT NOT NULL,
                body_copy TEXT,
                cta_text TEXT DEFAULT 'Learn More',
                landing_url TEXT NOT NULL,
                status TEXT DEFAULT 'draft',
                impressions INTEGER DEFAULT 0,
                clicks INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (campaign_id) REFERENCES ad_campaigns(id)
            )
        """)
        )

        # Ad impressions table
        conn.execute(
            text(f"""
            CREATE TABLE IF NOT EXISTS ad_impressions (
                id {id_type},
                creative_id INTEGER NOT NULL,
                campaign_id INTEGER NOT NULL,
                business_id TEXT NOT NULL,
                placement TEXT,
                user_id TEXT,
                session_id TEXT,
                timestamp REAL NOT NULL,
                FOREIGN KEY (creative_id) REFERENCES ad_creatives(id),
                FOREIGN KEY (campaign_id) REFERENCES ad_campaigns(id),
                FOREIGN KEY (business_id) REFERENCES businesses(id)
            )
        """)
        )

        # Ad clicks table
        conn.execute(
            text(f"""
            CREATE TABLE IF NOT EXISTS ad_clicks (
                id {id_type},
                creative_id INTEGER NOT NULL,
                campaign_id INTEGER NOT NULL,
                business_id TEXT NOT NULL,
                user_id TEXT,
                fingerprint_hash TEXT NOT NULL,
                billable {boolean_type} DEFAULT {true_value},
                rejection_reason TEXT,
                cost REAL DEFAULT 0.0,
                timestamp REAL NOT NULL,
                FOREIGN KEY (creative_id) REFERENCES ad_creatives(id),
                FOREIGN KEY (campaign_id) REFERENCES ad_campaigns(id),
                FOREIGN KEY (business_id) REFERENCES businesses(id)
            )
        """)
        )

        # Create indexes for performance
        conn.execute(
            text("""
            CREATE INDEX IF NOT EXISTS idx_ad_campaigns_business ON ad_campaigns(business_id)
        """)
        )
        conn.execute(
            text("""
            CREATE INDEX IF NOT EXISTS idx_ad_campaigns_status ON ad_campaigns(status)
        """)
        )
        conn.execute(
            text("""
            CREATE INDEX IF NOT EXISTS idx_ad_creatives_campaign ON ad_creatives(campaign_id)
        """)
        )
        conn.execute(
            text("""
            CREATE INDEX IF NOT EXISTS idx_ad_creatives_status ON ad_creatives(status)
        """)
        )
        conn.execute(
            text("""
            CREATE INDEX IF NOT EXISTS idx_ad_impressions_timestamp ON ad_impressions(timestamp)
        """)
        )
        conn.execute(
            text("""
            CREATE INDEX IF NOT EXISTS idx_ad_clicks_fingerprint ON ad_clicks(fingerprint_hash, timestamp)
        """)
        )
        conn.execute(
            text("""
            CREATE INDEX IF NOT EXISTS idx_ad_clicks_billable ON ad_clicks(billable, timestamp)
        """)
        )

        # Seed sample ad campaigns for existing businesses
        print("\nSeeding sample ad campaigns...")
        
        # Get existing businesses
        businesses = conn.execute(
            text("SELECT id, name FROM businesses WHERE status = 'active'")
        ).fetchall()

        for biz in businesses:
            biz_id, biz_name = biz[0], biz[1]
            
            # Create a sample campaign for each business
            conn.execute(
                text(
                    "INSERT INTO ad_campaigns "
                    "(business_id, name, status, budget_type, budget_amount, click_credits, first_month_free) "
                    "VALUES (:business_id, :name, 'active', 'prepaid', 50.00, 10000, 1)"
                ),
                {"business_id": biz_id, "name": f"{biz_name} - Launch Campaign"},
            )

        conn.commit()

    print("\n✅ Migration completed successfully!")
    print("\nTables created:")
    print("  - ad_campaigns")
    print("  - ad_creatives")
    print("  - ad_impressions")
    print("  - ad_clicks")
    print("\nIndexes created:")
    print("  - idx_ad_campaigns_business")
    print("  - idx_ad_campaigns_status")
    print("  - idx_ad_creatives_campaign")
    print("  - idx_ad_creatives_status")
    print("  - idx_ad_impressions_timestamp")
    print("  - idx_ad_clicks_fingerprint (fraud detection)")
    print("  - idx_ad_clicks_billable (billing)")
    print("\nSample data seeded:")
    print("  - Ad campaigns for existing businesses (first month free)")


if __name__ == "__main__":
    migrate()
