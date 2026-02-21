"""
Database Migration: Compatibility Database Tables

Adds:
- compatibility_reports: User-submitted mod compatibility status
- compatibility_votes: Upvotes/downvotes on reports
- load_order_shares: Shared load orders from users

This is SkyModderAI's MOAT - crowdsourced compatibility data
that nobody else can replicate.

Run: python3 migrations/add_compatibility_database.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///users.db")


def migrate():
    """Run database migration."""
    print("Starting compatibility database migration...")
    print(f"Database: {DATABASE_URL}")

    is_postgresql = "postgresql" in DATABASE_URL.lower()

    engine = create_engine(DATABASE_URL)

    with engine.connect() as conn:
        print("\nCreating compatibility tables...")

        # Compatibility Reports Table
        conn.execute(
            text("""
            CREATE TABLE IF NOT EXISTS compatibility_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mod_a TEXT NOT NULL,
                mod_b TEXT NOT NULL,
                game TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('compatible', 'incompatible', 'needs_patch')),
                description TEXT,
                user_email TEXT NOT NULL,
                upvotes INTEGER DEFAULT 0,
                downvotes INTEGER DEFAULT 0,
                verified INTEGER DEFAULT 0,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            )
        """)
        )

        # Compatibility Votes Table
        conn.execute(
            text("""
            CREATE TABLE IF NOT EXISTS compatibility_votes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_id INTEGER NOT NULL,
                user_email TEXT NOT NULL,
                vote INTEGER NOT NULL CHECK(vote IN (1, -1)),
                voted_at REAL NOT NULL,
                FOREIGN KEY (report_id) REFERENCES compatibility_reports(id) ON DELETE CASCADE,
                UNIQUE(report_id, user_email)
            )
        """)
        )

        # Load Order Shares Table
        conn.execute(
            text("""
            CREATE TABLE IF NOT EXISTS load_order_shares (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                game TEXT NOT NULL,
                mod_count INTEGER NOT NULL,
                mods_json TEXT NOT NULL,
                load_order_json TEXT NOT NULL,
                user_email TEXT NOT NULL,
                upvotes INTEGER DEFAULT 0,
                downvotes INTEGER DEFAULT 0,
                downloads INTEGER DEFAULT 0,
                game_version TEXT,
                enb TEXT,
                screenshots_json TEXT,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            )
        """)
        )

        # Load Order Downloads Table (track who downloaded)
        conn.execute(
            text("""
            CREATE TABLE IF NOT EXISTS load_order_downloads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                share_id INTEGER NOT NULL,
                user_email TEXT,
                downloaded_at REAL NOT NULL,
                FOREIGN KEY (share_id) REFERENCES load_order_shares(id) ON DELETE CASCADE,
                UNIQUE(share_id, user_email)
            )
        """)
        )

        # Create indexes for performance
        print("\nCreating indexes...")
        conn.execute(
            text("""
            CREATE INDEX IF NOT EXISTS idx_compat_mods ON compatibility_reports(mod_a, mod_b, game)
        """)
        )
        conn.execute(
            text("""
            CREATE INDEX IF NOT EXISTS idx_compat_status ON compatibility_reports(status, verified)
        """)
        )
        conn.execute(
            text("""
            CREATE INDEX IF NOT EXISTS idx_compat_created ON compatibility_reports(created_at DESC)
        """)
        )
        conn.execute(
            text("""
            CREATE INDEX IF NOT EXISTS idx_compat_votes ON compatibility_votes(report_id, user_email)
        """)
        )
        conn.execute(
            text("""
            CREATE INDEX IF NOT EXISTS idx_load_order_game ON load_order_shares(game, upvotes - downvotes DESC)
        """)
        )
        conn.execute(
            text("""
            CREATE INDEX IF NOT EXISTS idx_load_order_created ON load_order_shares(created_at DESC)
        """)
        )
        conn.execute(
            text("""
            CREATE INDEX IF NOT EXISTS idx_load_order_downloads ON load_order_downloads(share_id)
        """)
        )

        conn.commit()

    print("\n✅ Migration completed successfully!")
    print("\nTables created:")
    print("  - compatibility_reports (crowdsourced mod compatibility)")
    print("  - compatibility_votes (user votes on reports)")
    print("  - load_order_shares (shared load orders)")
    print("  - load_order_downloads (download tracking)")
    print("\nIndexes created:")
    print("  - idx_compat_mods (fast mod pair lookups)")
    print("  - idx_compat_status (filter by compatibility)")
    print("  - idx_compat_created (recent reports)")
    print("  - idx_compat_votes (prevent duplicate votes)")
    print("  - idx_load_order_game (filter by game + sort by votes)")
    print("  - idx_load_order_created (newest first)")
    print("  - idx_load_order_downloads (download tracking)")
    print("\n🎯 This is SkyModderAI's MOAT.")
    print("   LOOT can't do this (rules, not community).")
    print("   Nexus can't do this (hosting, not compatibility).")
    print("   ChatGPT can't do this (no real-time data).")


if __name__ == "__main__":
    migrate()
