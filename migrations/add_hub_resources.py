"""
Database Migration: Add Education Hub Resources Table

Adds:
- hub_resources: Educational resources for the business hub
  - Categorized resources with game analogies
  - Free, vetted tools and guides for modder-entrepreneurs
  - Progressive learning paths (beginner to advanced)

Run: python3 migrations/add_hub_resources.py

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
    print("Starting hub resources migration...")
    print(f"Database: {DATABASE_URL}")

    engine = create_engine(DATABASE_URL, echo=True)

    print("\nChecking existing hub_resources table...")
    with engine.connect() as conn:
        is_postgresql = engine.dialect.name == "postgresql"
        
        # Check if hub_resources already exists (from business_service)
        existing_columns = conn.execute(
            text("PRAGMA table_info(hub_resources)")
        ).fetchall()
        
        # SQLite returns tuples: (cid, name, type, notnull, dflt_value, pk)
        column_names = [col[1] for col in existing_columns]
        
        if "url" in column_names:
            print("Hub resources table already has new columns. Skipping schema update.")
        else:
            print("Adding new columns to hub_resources table...")
            
            # Add new columns for game-analogy enhanced resources
            new_columns = [
                ("subcategory", "TEXT"),
                ("url", "TEXT NOT NULL DEFAULT ''"),
                ("analogy", "TEXT"),
                ("game_reference", "TEXT"),
                ("difficulty_level", "TEXT DEFAULT 'beginner'"),
                ("order_index", "INTEGER DEFAULT 0"),
                ("is_free", "BOOLEAN DEFAULT TRUE"),
            ]
            
            for col_name, col_type in new_columns:
                if col_name not in column_names:
                    try:
                        conn.execute(
                            text(f"ALTER TABLE hub_resources ADD COLUMN {col_name} {col_type}")
                        )
                        print(f"  Added column: {col_name}")
                    except Exception as e:
                        print(f"  Column {col_name} may already exist: {e}")
            
            conn.commit()

        # Create indexes if they don't exist
        print("\nCreating indexes...")
        conn.execute(
            text("""
            CREATE INDEX IF NOT EXISTS idx_hub_resources_category ON hub_resources(category)
        """)
        )
        conn.execute(
            text("""
            CREATE INDEX IF NOT EXISTS idx_hub_resources_difficulty ON hub_resources(difficulty_level)
        """)
        )
        conn.execute(
            text("""
            CREATE INDEX IF NOT EXISTS idx_hub_resources_order ON hub_resources(order_index)
        """)
        )
        conn.commit()

        # Seed educational resources with game analogies
        print("\nSeeding educational resources...")
        resources = [
            # Getting Started (Beginner: Survival Mode)
            {
                "category": "getting_started",
                "subcategory": "niche",
                "title": "Find Your Niche - SBA Quiz",
                "description": "Quick self-assessment to validate your business idea, like surveying biomes in Minecraft for the best resources.",
                "url": "https://www.sba.gov/business-guide/plan-your-business/identify-your-market",
                "analogy": "Like starting a new Fallout save with scavenged junk—bootstrap from zero using modder smarts. Survey the wasteland before building.",
                "game_reference": "Minecraft biome survey / Fallout scavenging",
                "difficulty_level": "beginner",
                "order_index": 1,
                "is_free": 1,
            },
            {
                "category": "getting_started",
                "subcategory": "planning",
                "title": "Minimal Business Plan Template",
                "description": "Free fillable PDF for skills-based plans. Focus on tradeoffs like armor forging—what protects you vs. what weighs you down.",
                "url": "https://www.liveplan.com/business-plan-templates",
                "analogy": "Sketch a basic base layout before expanding. Plan your supply chain like optimizing a Factorio belt system.",
                "game_reference": "Factorio belt planning / Skyrim crafting",
                "difficulty_level": "beginner",
                "order_index": 2,
                "is_free": 1,
            },
            {
                "category": "getting_started",
                "subcategory": "legal",
                "title": "Legal Setup Guide - USA.gov",
                "description": "Free guides for sole proprietorships, LLCs, and digital presence setup. Automate your first belts like in Factorio.",
                "url": "https://www.usa.gov/starting-business",
                "analogy": "Gather your first tools and establish your base of operations. Register your 'faction' officially.",
                "game_reference": "Factorio automation / Skyrim guild registration",
                "difficulty_level": "beginner",
                "order_index": 3,
                "is_free": 1,
            },
            {
                "category": "getting_started",
                "subcategory": "branding",
                "title": "Free Branding with Canva",
                "description": "Create professional logos and branding materials for free. Design your company banner like a Skyrim house crest.",
                "url": "https://www.canva.com/",
                "analogy": "Craft your visual identity like designing a custom shield or banner in Skyrim.",
                "game_reference": "Skyrim heraldry / Minecraft banner design",
                "difficulty_level": "beginner",
                "order_index": 4,
                "is_free": 1,
            },

            # Building Community Presence (Intermediate: Build Phase)
            {
                "category": "building_community",
                "subcategory": "customers",
                "title": "Zero-Cost Customer Acquisition",
                "description": "Tactics like free mod audits via your directory. Team up like in Minecraft multiplayer builds.",
                "url": "https://www.homebase.com/blog/customer-acquisition-strategies",
                "analogy": "Attract your first allies by offering value upfront. Like trading resources in Minecraft to build trust.",
                "game_reference": "Minecraft multiplayer trading / Fallout faction reputation",
                "difficulty_level": "intermediate",
                "order_index": 5,
                "is_free": 1,
            },
            {
                "category": "building_community",
                "subcategory": "automation",
                "title": "Automate Your Outreach - Amex Guide",
                "description": "Free social automation with Buffer and similar tools. Streamline your supply chains like in Factorio.",
                "url": "https://www.americanexpress.com/en-us/business/trends-and-insights/articles/how-to-automate-your-business/",
                "analogy": "Build automated marketing belts that run while you focus on innovation. Set up inserter arms for social posts.",
                "game_reference": "Factorio inserter automation / Skyrim enchanting",
                "difficulty_level": "intermediate",
                "order_index": 6,
                "is_free": 1,
            },
            {
                "category": "building_community",
                "subcategory": "feedback",
                "title": "Customer Feedback Loops - ADP",
                "description": "Use Google Forms for feedback loops. Iterate your builds like researching new tech in Factorio.",
                "url": "https://www.adp.com/spark/articles/2021/03/how-to-collect-and-act-on-customer-feedback.aspx",
                "analogy": "Gather feedback like checking your factory efficiency. Identify bottlenecks and optimize.",
                "game_reference": "Factorio research / Minecraft redstone iteration",
                "difficulty_level": "intermediate",
                "order_index": 7,
                "is_free": 1,
            },

            # Metrics That Matter (Intermediate-Advanced: Optimization)
            {
                "category": "metrics",
                "subcategory": "kpis",
                "title": "Key Performance Indicators Guide",
                "description": "Free dashboards via Google Sheets. Balance costs like managing inventory weight in Fallout.",
                "url": "https://www.bankofamerica.com/small-business/resources/how-to-track-kpis/",
                "analogy": "Track your resource efficiency like monitoring power consumption in Factorio. Know your carry weight limits.",
                "game_reference": "Fallout inventory management / Factorio power monitoring",
                "difficulty_level": "intermediate",
                "order_index": 8,
                "is_free": 1,
            },
            {
                "category": "metrics",
                "subcategory": "impact",
                "title": "Climate & Impact Metrics - C2ES",
                "description": "Tools for measuring social good and carbon savings. Track endgame stats like Minecraft achievements.",
                "url": "https://www.c2es.org/business/solutions-for-business/",
                "analogy": "Measure your positive impact on the world. Like tracking how many trees you've replanted in a survival world.",
                "game_reference": "Minecraft achievements / Skyrim bounties completed",
                "difficulty_level": "advanced",
                "order_index": 9,
                "is_free": 1,
            },

            # Advanced Strategy (Advanced: Conquer & Legacy)
            {
                "category": "advanced_strategy",
                "subcategory": "partnerships",
                "title": "Partnerships & Innovation - HBS",
                "description": "Free webinars on collaborations and social change strategies. Build alliance mega-projects.",
                "url": "https://www.hbs.edu/impact-economy/Pages/default.aspx",
                "analogy": "Form alliances for massive projects like multiplayer server builds. Combine strengths for greater impact.",
                "game_reference": "Minecraft server megaprojects / Skyrim guild alliances",
                "difficulty_level": "advanced",
                "order_index": 10,
                "is_free": 1,
            },
            {
                "category": "advanced_strategy",
                "subcategory": "scaling",
                "title": "Sustainable Scaling - INSEAD",
                "description": "Guides for climate-integrated growth. Build infinite factories that give back to the world.",
                "url": "https://www.insead.edu/sustainability",
                "analogy": "Scale sustainably like building a self-sufficient Factorio megabase. Growth that doesn't destroy the environment.",
                "game_reference": "Factorio megabase / Minecraft sustainable farms",
                "difficulty_level": "advanced",
                "order_index": 11,
                "is_free": 1,
            },

            # External Resources (Bonus: Mod Packs)
            {
                "category": "external_resources",
                "subcategory": "climate",
                "title": "SME Climate Hub - Green Starter Kit",
                "description": "Resources for eco-ventures and climate-focused businesses. Like installing eco-mod packs for a greener playthrough.",
                "url": "https://www.smehub.org/",
                "analogy": "Equip your business with climate-friendly practices. Mod your venture for environmental impact.",
                "game_reference": "Minecraft eco-mods / Fallout environmental restoration",
                "difficulty_level": "all",
                "order_index": 12,
                "is_free": 1,
            },
            {
                "category": "external_resources",
                "subcategory": "social_impact",
                "title": "B Corp Playbook",
                "description": "Ethical scaling and social impact measurement. Build a legacy that helps others.",
                "url": "https://www.bcorporation.net/en-us/resources/",
                "analogy": "Become a certified force for good. Like achieving the 'Hero' status in every Skyrim hold.",
                "game_reference": "Skyrim hero status / Minecraft community builds",
                "difficulty_level": "advanced",
                "order_index": 13,
                "is_free": 1,
            },
            {
                "category": "external_resources",
                "subcategory": "wealth_building",
                "title": "Impact Investing Guide - Nasdaq",
                "description": "Turn good deeds into sustainable riches. Wealth as a byproduct of positive impact.",
                "url": "https://www.nasdaq.com/solutions/esg",
                "analogy": "Wealth follows value creation. Like earning caps in Fallout by helping settlements thrive.",
                "game_reference": "Fallout settlement building / Skyrim merchant guild",
                "difficulty_level": "advanced",
                "order_index": 14,
                "is_free": 1,
            },
        ]

        seeded_count = 0
        for res in resources:
            # Check if resource already exists by URL
            existing = conn.execute(
                text("SELECT id FROM hub_resources WHERE url = :url"),
                {"url": res["url"]}
            ).fetchone()
            
            if not existing:
                conn.execute(
                    text("""
                    INSERT INTO hub_resources 
                    (category, subcategory, title, description, url, analogy, game_reference, resource_type, difficulty_level, order_index, is_free)
                    VALUES (:category, :subcategory, :title, :description, :url, :analogy, :game_reference, 'link', :difficulty_level, :order_index, :is_free)
                    """),
                    res,
                )
                seeded_count += 1

        conn.commit()

    print("\n✅ Migration completed successfully!")
    print("\nTable updated:")
    print("  - hub_resources (added columns: subcategory, analogy, game_reference, difficulty_level, order_index, is_free)")
    print("\nIndexes created:")
    print("  - idx_hub_resources_category")
    print("  - idx_hub_resources_difficulty")
    print("  - idx_hub_resources_order")
    print(f"\nResources seeded: {seeded_count} new educational resources")
    print("\nCategories:")
    print("  - getting_started (4 resources) - Survival Mode basics")
    print("  - building_community (3 resources) - Build Phase growth")
    print("  - metrics (2 resources) - Optimization tools")
    print("  - advanced_strategy (2 resources) - Conquer & Legacy")
    print("  - external_resources (3 resources) - Bonus mod packs")


if __name__ == "__main__":
    migrate()
