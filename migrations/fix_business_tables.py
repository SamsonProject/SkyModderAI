"""
Quick fix for business tables migration
SQLite doesn't support AUTOINCREMENT on non-primary key columns
"""

import sqlite3
from datetime import datetime

DB_PATH = "instance/app.db"

def fix_and_create_tables():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    print("Creating business tables (SQLite-compatible)...")
    
    # Businesses table
    c.execute("""
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
    
    # Business trust scores (removed AUTOINCREMENT from non-PK columns)
    c.execute("""
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
    
    # Business votes
    c.execute("""
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
    
    # Business flags
    c.execute("""
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
    
    # Business connections
    c.execute("""
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
    
    # Hub resources
    c.execute("""
        CREATE TABLE IF NOT EXISTS hub_resources (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            category TEXT NOT NULL,
            resource_type TEXT DEFAULT 'article',
            url TEXT,
            analogy TEXT,
            game_reference TEXT,
            difficulty_level TEXT DEFAULT 'beginner',
            order_index INTEGER DEFAULT 0,
            is_free INTEGER DEFAULT 1,
            author TEXT,
            contributed_by_business_id TEXT,
            upvotes INTEGER DEFAULT 0,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            approved_at TIMESTAMP,
            approved_by TEXT,
            FOREIGN KEY (contributed_by_business_id) REFERENCES businesses(id)
        )
    """)
    
    # Create indexes
    c.execute("CREATE INDEX IF NOT EXISTS idx_businesses_status ON businesses(status)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_businesses_category ON businesses(primary_category)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_business_votes_business ON business_votes(business_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_business_flags_business ON business_flags(business_id)")
    
    conn.commit()
    
    # Verify tables were created
    tables = c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'business%'").fetchall()
    print(f"\n✅ Business tables created: {[t[0] for t in tables]}")
    
    # Seed sample businesses if none exist
    existing = c.execute("SELECT COUNT(*) FROM businesses").fetchone()[0]
    if existing == 0:
        print("\nSeeding sample businesses...")
        now = datetime.now().isoformat()
        
        businesses = [
            ('54313d7a-b4ab-49f7-bc1f-bd389c1fe40f', 'Nexus Mods', 'nexus-mods', 'The largest modding community', 'https://nexusmods.com', 'modding_tools'),
            ('ec8c09dc-16bb-4fd0-be1f-4155f59561ec', 'LOOT', 'loot', 'Load Order Optimisation Tool', 'https://loot.github.io', 'modding_tools'),
            ('929385c2-2454-4900-b5aa-7c38b4a3660f', 'Wabbajack', 'wabbajack', 'Automated modlist installer', 'https://wabbajack.org', 'modding_tools'),
        ]
        
        for biz_id, name, slug, tagline, website, category in businesses:
            c.execute("""
                INSERT OR IGNORE INTO businesses (id, name, slug, tagline, website, primary_category, status, verified, created_at)
                VALUES (?, ?, ?, ?, ?, ?, 'active', 1, ?)
            """, (biz_id, name, slug, tagline, website, category, now))
            
            # Create trust score for each
            c.execute("""
                INSERT OR IGNORE INTO business_trust_scores (business_id, trust_score, trust_tier, total_votes)
                VALUES (?, 85.0, 'trusted', 100)
            """, (biz_id,))
        
        conn.commit()
        print(f"✅ Seeded {len(businesses)} businesses")
    
    conn.close()
    print("\n✅ Business tables migration complete!")

if __name__ == "__main__":
    fix_and_create_tables()
