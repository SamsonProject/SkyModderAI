"""
Database Migration: Add Business Community Tables

Adds:
- businesses: Business directory listings
- business_trust_scores: Trust score components
- business_votes: Community votes
- business_flags: Community flags
- business_connections: B2B introductions
- hub_resources: Education hub resources

Run: python3 migrations/add_business_tables.py
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
    print("Starting business tables migration...")
    print(f"Database: {DATABASE_URL}")

    # Create engine
    engine = create_engine(DATABASE_URL, echo=True)

    print("\nCreating business tables...")
    with engine.connect() as conn:
        # Businesses table
        conn.execute(
            text("""
            CREATE TABLE IF NOT EXISTS businesses (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                slug TEXT UNIQUE NOT NULL,
                tagline TEXT,
                description TEXT,
                website TEXT NOT NULL,
                logo_url TEXT,
                contact_email TEXT NOT NULL,
                public_contact_method TEXT DEFAULT 'form',
                public_contact_value TEXT,
                primary_category TEXT NOT NULL,
                secondary_categories TEXT,
                relevant_games TEXT,
                status TEXT DEFAULT 'pending',
                verified INTEGER DEFAULT 0,
                verified_at TIMESTAMP,
                owner_email TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                approved_at TIMESTAMP,
                last_active TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        )

        # Business trust scores table
        conn.execute(
            text("""
            CREATE TABLE IF NOT EXISTS business_trust_scores (
                business_id TEXT PRIMARY KEY,
                community_vote_score REAL DEFAULT 0.0,
                sponsor_performance_score REAL DEFAULT 0.0,
                community_participation_score REAL DEFAULT 0.0,
                longevity_score REAL DEFAULT 0.0,
                flag_penalty REAL DEFAULT 0.0,
                trust_score REAL DEFAULT 0.0,
                trust_tier TEXT DEFAULT 'new',
                total_votes INTEGER DEFAULT 0,
                positive_votes INTEGER DEFAULT 0,
                total_flags INTEGER DEFAULT 0,
                resolved_flags INTEGER DEFAULT 0,
                ama_count INTEGER DEFAULT 0,
                hub_contributions INTEGER DEFAULT 0,
                months_active INTEGER DEFAULT 0,
                last_calculated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (business_id) REFERENCES businesses(id)
            )
        """)
        )

        # Business votes table
        conn.execute(
            text("""
            CREATE TABLE IF NOT EXISTS business_votes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                business_id TEXT NOT NULL,
                voter_user_id TEXT NOT NULL,
                score INTEGER NOT NULL CHECK(score >= 1 AND score <= 5),
                context TEXT,
                voted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (business_id) REFERENCES businesses(id),
                UNIQUE(business_id, voter_user_id)
            )
        """)
        )

        # Business flags table
        conn.execute(
            text("""
            CREATE TABLE IF NOT EXISTS business_flags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                business_id TEXT NOT NULL,
                reporter_user_id TEXT NOT NULL,
                reason TEXT NOT NULL,
                detail TEXT,
                status TEXT DEFAULT 'open',
                reported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                reviewed_at TIMESTAMP,
                reviewed_by TEXT,
                FOREIGN KEY (business_id) REFERENCES businesses(id)
            )
        """)
        )

        # Business connections table
        conn.execute(
            text("""
            CREATE TABLE IF NOT EXISTS business_connections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                requester_id TEXT NOT NULL,
                target_id TEXT NOT NULL,
                message TEXT,
                status TEXT DEFAULT 'pending',
                requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                responded_at TIMESTAMP,
                FOREIGN KEY (requester_id) REFERENCES businesses(id),
                FOREIGN KEY (target_id) REFERENCES businesses(id),
                UNIQUE(requester_id, target_id)
            )
        """)
        )

        # Hub resources table
        conn.execute(
            text("""
            CREATE TABLE IF NOT EXISTS hub_resources (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                category TEXT NOT NULL,
                resource_type TEXT NOT NULL,
                content TEXT,
                author TEXT,
                contributed_by_business_id TEXT,
                upvotes INTEGER DEFAULT 0,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (contributed_by_business_id) REFERENCES businesses(id)
            )
        """)
        )

        # Create indexes
        conn.execute(
            text("""
            CREATE INDEX IF NOT EXISTS idx_businesses_status ON businesses(status)
        """)
        )
        conn.execute(
            text("""
            CREATE INDEX IF NOT EXISTS idx_businesses_category ON businesses(primary_category)
        """)
        )
        conn.execute(
            text("""
            CREATE INDEX IF NOT EXISTS idx_business_votes_business ON business_votes(business_id)
        """)
        )
        conn.execute(
            text("""
            CREATE INDEX IF NOT EXISTS idx_business_flags_business ON business_flags(business_id)
        """)
        )
        conn.execute(
            text("""
            CREATE INDEX IF NOT EXISTS idx_hub_resources_category ON hub_resources(category)
        """)
        )

        # Seed sample businesses
        print("\nSeeding sample businesses...")
        sample_businesses = [
            {
                "id": str(uuid.uuid4()),
                "name": "Nexus Mods",
                "slug": "nexus-mods",
                "tagline": "The largest modding community",
                "description": "Nexus Mods is a site that allows users to upload and download modification files (mods) for video games.",
                "website": "https://www.nexusmods.com/",
                "logo_url": "/static/icons/nexus.svg",
                "contact_email": "support@nexusmods.com",
                "public_contact_method": "form",
                "primary_category": "community_platform",
                "secondary_categories": '["modding_tools"]',
                "relevant_games": '["skyrimse", "fallout4", "starfield"]',
                "status": "active",
                "verified": 1,
            },
            {
                "id": str(uuid.uuid4()),
                "name": "LOOT",
                "slug": "loot",
                "tagline": "Load Order Optimisation Tool",
                "description": "A plugin load order optimiser for games made by Bethesda.",
                "website": "https://loot.github.io/",
                "logo_url": "/static/icons/loot.svg",
                "contact_email": "loot@github.com",
                "public_contact_method": "email",
                "public_contact_value": "loot@github.com",
                "primary_category": "modding_tools",
                "secondary_categories": "[]",
                "relevant_games": '["skyrimse", "fallout4", "oblivion"]',
                "status": "active",
                "verified": 1,
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Wabbajack",
                "slug": "wabbajack",
                "tagline": "Automated modlist installer",
                "description": "Wabbajack is an automated modlist installer that allows users to install and update modpacks.",
                "website": "https://www.wabbajack.org/",
                "logo_url": "/static/icons/wabbajack.svg",
                "contact_email": "info@wabbajack.org",
                "public_contact_method": "discord",
                "public_contact_value": "wabbajack#1234",
                "primary_category": "modding_tools",
                "secondary_categories": "[]",
                "relevant_games": '["skyrimse", "fallout4"]',
                "status": "active",
                "verified": 1,
            },
        ]

        for biz in sample_businesses:
            conn.execute(
                text("""
                INSERT OR IGNORE INTO businesses 
                (id, name, slug, tagline, description, website, logo_url, contact_email, 
                 public_contact_method, public_contact_value, primary_category, 
                 secondary_categories, relevant_games, status, verified)
                VALUES (:id, :name, :slug, :tagline, :description, :website, :logo_url, 
                        :contact_email, :public_contact_method, :public_contact_value, 
                        :primary_category, :secondary_categories, :relevant_games, :status, :verified)
            """),
                {
                    **biz,
                    "public_contact_value": biz.get("public_contact_value", ""),  # Ensure it's set
                },
            )

            # Create trust score for each business
            conn.execute(
                text("""
                INSERT OR IGNORE INTO business_trust_scores (business_id, trust_score, trust_tier, total_votes, positive_votes)
                VALUES (:id, 85.0, 'trusted', 50, 48)
            """),
                {"id": biz["id"]},
            )

        conn.commit()

    print("\n✅ Migration completed successfully!")
    print("\nTables created:")
    print("  - businesses")
    print("  - business_trust_scores")
    print("  - business_votes")
    print("  - business_flags")
    print("  - business_connections")
    print("  - hub_resources")
    print("\nIndexes created:")
    print("  - idx_businesses_status")
    print("  - idx_businesses_category")
    print("  - idx_business_votes_business")
    print("  - idx_business_flags_business")
    print("  - idx_hub_resources_category")
    print("\nSample data seeded:")
    print("  - 3 sample businesses (Nexus Mods, LOOT, Wabbajack)")


if __name__ == "__main__":
    migrate()
