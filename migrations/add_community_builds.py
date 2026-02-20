"""
Migration: Add community_builds table for user-submitted mod lists.

This replaces hardcoded mod recommendations with community-driven builds.
All builds are transparently sourced from popular free community modlists.
"""

import json
import sqlite3

DB_FILE = "users.db"

# Seed data from researched popular FREE modlists (Wabbajack, Nexus Collections)
# Sources: Wabbajack official modlists, Nexus Mods collections, community recommendations
# All builds are freely available, not for sale, community-created
SEED_BUILDS = [
    # SKYRIM SE - Vanilla+ Builds
    {
        "game": "skyrimse",
        "name": "Gate to Sovngarde",
        "description": "Vanilla+ experience with 1700+ mods. Adds quests, lands, armors, spells, and followers while maintaining the core Skyrim feel. One of the most popular community modlists.",
        "author": "JaySerpa / Community",
        "source": "Wabbajack",
        "source_url": "https://www.wabbajack.org/",
        "wiki_url": "https://gatetosovngarde.wiki.gg/",
        "mod_count": 1700,
        "playstyle_tags": json.dumps(
            ["vanilla_plus", "quest_rich", "visual_enhancement", "combat_overhaul"]
        ),
        "performance_tier": "mid_high",
        "upvotes": 0,
        "downvotes": 0,
        "is_seed": 1,
        "seed_note": "Seeded from popular Wabbajack modlist - will be replaced by community submissions",
    },
    {
        "game": "skyrimse",
        "name": "The Phoenix Flavour",
        "description": "700+ mods focused on coherent, stable experience. Improves all aspects while keeping core Skyrim intact. Excellent base for experimentation with 4K ultrawide support.",
        "author": "The Phoenix Flavour Team",
        "source": "Wabbajack",
        "source_url": "https://www.wabbajack.org/",
        "wiki_url": "",
        "mod_count": 700,
        "playstyle_tags": json.dumps(
            ["vanilla_plus", "stable", "visual_enhancement", "beginner_friendly"]
        ),
        "performance_tier": "mid",
        "upvotes": 0,
        "downvotes": 0,
        "is_seed": 1,
        "seed_note": "Seeded from popular Wabbajack modlist - will be replaced by community submissions",
    },
    {
        "game": "skyrimse",
        "name": "Nordic Souls",
        "description": "210 mods, beginner-friendly and extremely stable. Lore-friendly vanilla+ using SimonRim suite. Optimized for low-end PCs while maintaining visual quality.",
        "author": "Community",
        "source": "Wabbajack",
        "source_url": "https://www.wabbajack.org/",
        "wiki_url": "",
        "mod_count": 210,
        "playstyle_tags": json.dumps(["vanilla_plus", "lore_friendly", "low_end", "stable"]),
        "performance_tier": "low",
        "upvotes": 0,
        "downvotes": 0,
        "is_seed": 1,
        "seed_note": "Seeded from popular Wabbajack modlist - will be replaced by community submissions",
    },
    {
        "game": "skyrimse",
        "name": "Living Skyrim",
        "description": "350+ mods that breathe life into Skyrim. Adds NPCs, quests, dungeons, and followers to make the world feel alive. Slower-paced with larger perk trees and new spells.",
        "author": "inire / Community",
        "source": "Wabbajack",
        "source_url": "https://www.wabbajack.org/",
        "wiki_url": "https://github.com/inire/Living-Skyrim",
        "mod_count": 350,
        "playstyle_tags": json.dumps(["vanilla_plus", "quest_rich", "npc_overhaul", "immersive"]),
        "performance_tier": "mid",
        "upvotes": 0,
        "downvotes": 0,
        "is_seed": 1,
        "seed_note": "Seeded from popular Wabbajack modlist - will be replaced by community submissions",
    },
    {
        "game": "skyrimse",
        "name": "True North",
        "description": "1000+ mods celebrating 14 years of Skyrim modding community. Comprehensive overhaul with quests, visuals, and gameplay improvements. SFW and stable.",
        "author": "Rorax / Community",
        "source": "Wabbajack / Nexus",
        "source_url": "https://www.wabbajack.org/",
        "wiki_url": "",
        "mod_count": 1000,
        "playstyle_tags": json.dumps(
            ["comprehensive", "quest_rich", "visual_enhancement", "community_celebration"]
        ),
        "performance_tier": "high",
        "upvotes": 0,
        "downvotes": 0,
        "is_seed": 1,
        "seed_note": "Seeded from popular Wabbajack modlist - will be replaced by community submissions",
    },
    # SKYRIM SE - Hardcore/Survival Builds
    {
        "game": "skyrimse",
        "name": "Wildlander",
        "description": "Hardcore survival total conversion. Requiem-based with food/drink management, weather survival, and immersive adventurer experience. Highly optimized with ambitious roadmap.",
        "author": "Wildlander Team",
        "source": "Wabbajack",
        "source_url": "https://www.wabbajack.org/",
        "wiki_url": "",
        "mod_count": 400,
        "playstyle_tags": json.dumps(["hardcore", "survival", "requiem", "total_conversion"]),
        "performance_tier": "mid",
        "upvotes": 0,
        "downvotes": 0,
        "is_seed": 1,
        "seed_note": "Seeded from popular Wabbajack modlist - will be replaced by community submissions",
    },
    {
        "game": "skyrimse",
        "name": "Do Not Go Gentle",
        "description": "400+ mods balancing Requiem's harsh difficulty with neutral-tone visuals. Modern combat animations compatible with Requiem + large quest mods like VIGILANT.",
        "author": "Community",
        "source": "Wabbajack",
        "source_url": "https://www.wabbajack.org/",
        "wiki_url": "",
        "mod_count": 400,
        "playstyle_tags": json.dumps(["hardcore", "requiem", "combat_overhaul", "quest_rich"]),
        "performance_tier": "mid_high",
        "upvotes": 0,
        "downvotes": 0,
        "is_seed": 1,
        "seed_note": "Seeded from popular Wabbajack modlist - will be replaced by community submissions",
    },
    {
        "game": "skyrimse",
        "name": "Legends of the Frost",
        "description": "~300 mods, lightweight vanilla improvements. Bug fixes, visual improvements, DynDOLOD. Skyrim as it should have been at launch. Optional ENB/widescreen support.",
        "author": "Community",
        "source": "Wabbajack",
        "source_url": "https://www.wabbajack.org/",
        "wiki_url": "",
        "mod_count": 300,
        "playstyle_tags": json.dumps(["vanilla", "lightweight", "bug_fixes", "performance"]),
        "performance_tier": "low",
        "upvotes": 0,
        "downvotes": 0,
        "is_seed": 1,
        "seed_note": "Seeded from popular Wabbajack modlist - will be replaced by community submissions",
    },
    # SKYRIM SE - Power Fantasy Builds
    {
        "game": "skyrimse",
        "name": "Lost Legacy",
        "description": "335+ mods, power fantasy with 5000+ Legacy of the Dragonborn museum displays. Vokriinator + EnaiRim package. High fantasy visuals and vibrant gameplay.",
        "author": "Community",
        "source": "Wabbajack",
        "source_url": "https://www.wabbajack.org/",
        "wiki_url": "",
        "mod_count": 335,
        "playstyle_tags": json.dumps(["power_fantasy", "lotd", "high_fantasy", "collection"]),
        "performance_tier": "high",
        "upvotes": 0,
        "downvotes": 0,
        "is_seed": 1,
        "seed_note": "Seeded from popular Wabbajack modlist - will be replaced by community submissions",
    },
    {
        "game": "skyrimse",
        "name": "Apostasy",
        "description": "375+ mods by renowned modlist author. Custom mods not on Nexus. Stances combat system (4 movesets per weapon), custom animations, backstabs, status effects.",
        "author": "Aljo / Community",
        "source": "Wabbajack",
        "source_url": "https://www.wabbajack.org/",
        "wiki_url": "",
        "mod_count": 375,
        "playstyle_tags": json.dumps(
            ["power_fantasy", "combat_overhaul", "custom_content", "action"]
        ),
        "performance_tier": "high",
        "upvotes": 0,
        "downvotes": 0,
        "is_seed": 1,
        "seed_note": "Seeded from popular Wabbajack modlist - will be replaced by community submissions",
    },
    {
        "game": "skyrimse",
        "name": "Path of the Dovahkiin",
        "description": "ARPG power fantasy transforming Skyrim into Diablo-like experience. Massive perk trees, repeatable dungeons, increased enemy variety, loot-focused gameplay.",
        "author": "Community",
        "source": "Wabbajack",
        "source_url": "https://www.wabbajack.org/",
        "wiki_url": "",
        "mod_count": 350,
        "playstyle_tags": json.dumps(["power_fantasy", "arpg", "loot", "dungeon_crawler"]),
        "performance_tier": "mid_high",
        "upvotes": 0,
        "downvotes": 0,
        "is_seed": 1,
        "seed_note": "Seeded from popular Wabbajack modlist - will be replaced by community submissions",
    },
    # FALLOUT 4 Builds
    {
        "game": "fallout4",
        "name": "Magnum Opus",
        "description": "Expands Fallout 4 content while keeping original intact. Hundreds of new weapons/armors, dozens of quests, custom sorting, Sim Settlements 2. Moderate challenge.",
        "author": "Community",
        "source": "Wabbajack",
        "source_url": "https://www.wabbajack.org/",
        "wiki_url": "",
        "mod_count": 500,
        "playstyle_tags": json.dumps(["vanilla_plus", "quest_rich", "equipment", "settlements"]),
        "performance_tier": "mid",
        "upvotes": 0,
        "downvotes": 0,
        "is_seed": 1,
        "seed_note": "Seeded from popular Wabbajack modlist - will be replaced by community submissions",
    },
    {
        "game": "fallout4",
        "name": "FUSION",
        "description": "Best vanilla experience for PC. Improved ambiance/visuals, FallUI, DLC integration, FOLIP LOD. 16:9 only, stable and smooth.",
        "author": "Community",
        "source": "Wabbajack",
        "source_url": "https://www.wabbajack.org/",
        "wiki_url": "",
        "mod_count": 200,
        "playstyle_tags": json.dumps(["vanilla", "stable", "visual_enhancement", "ui_improvement"]),
        "performance_tier": "low",
        "upvotes": 0,
        "downvotes": 0,
        "is_seed": 1,
        "seed_note": "Seeded from popular Wabbajack modlist - will be replaced by community submissions",
    },
    {
        "game": "fallout4",
        "name": "Wasteland Reborn",
        "description": "730+ mods, fully-featured comprehensive overhaul. Combat, quests, settlements, dialogue revamps. Hundreds of new weapons and complete gameplay transformation.",
        "author": "Community",
        "source": "Wabbajack",
        "source_url": "https://www.wabbajack.org/",
        "wiki_url": "",
        "mod_count": 730,
        "playstyle_tags": json.dumps(
            ["overhaul", "combat_overhaul", "quest_rich", "comprehensive"]
        ),
        "performance_tier": "high",
        "upvotes": 0,
        "downvotes": 0,
        "is_seed": 1,
        "seed_note": "Seeded from popular Wabbajack modlist - will be replaced by community submissions",
    },
    {
        "game": "fallout4",
        "name": "Life in the Ruins",
        "description": "Massively overhauled with vanilla aesthetic and scarcity challenge. Lunar Fallout Overhaul, True Perks, Sim Settlements 2, survival options.",
        "author": "Community",
        "source": "Wabbajack",
        "source_url": "https://www.wabbajack.org/",
        "wiki_url": "",
        "mod_count": 450,
        "playstyle_tags": json.dumps(["hardcore", "survival", "overhaul", "scarcity"]),
        "performance_tier": "mid",
        "upvotes": 0,
        "downvotes": 0,
        "is_seed": 1,
        "seed_note": "Seeded from popular Wabbajack modlist - will be replaced by community submissions",
    },
    # FALLOUT NEW VEGAS
    {
        "game": "falloutnv",
        "name": "Viva New Vegas",
        "description": "Stable, smooth, enjoyable vanilla+ experience. Performance focused with modular extended section. Optional Vigor difficulty. Community standard for FNV.",
        "author": "Viva New Vegas Team",
        "source": "Community",
        "source_url": "https://www.vivanewvegas.io/",
        "wiki_url": "",
        "mod_count": 150,
        "playstyle_tags": json.dumps(
            ["vanilla_plus", "stable", "performance", "beginner_friendly"]
        ),
        "performance_tier": "low",
        "upvotes": 0,
        "downvotes": 0,
        "is_seed": 1,
        "seed_note": "Seeded from popular community modlist - will be replaced by community submissions",
    },
    {
        "game": "falloutnv",
        "name": "Uranium Fever",
        "description": "1300+ mods complete overhaul, survival-horror. STALKER/Resident Evil inspired with custom edits, optimized assets, visually stunning and brutally challenging.",
        "author": "Community",
        "source": "Wabbajack",
        "source_url": "https://www.wabbajack.org/",
        "wiki_url": "",
        "mod_count": 1300,
        "playstyle_tags": json.dumps(["hardcore", "survival_horror", "overhaul", "stalker"]),
        "performance_tier": "high",
        "upvotes": 0,
        "downvotes": 0,
        "is_seed": 1,
        "seed_note": "Seeded from popular Wabbajack modlist - will be replaced by community submissions",
    },
    # OBLIVION
    {
        "game": "oblivion",
        "name": "Oblivion Enhanced",
        "description": "Vanilla+ experience for Oblivion. Bug fixes, visual improvements, QoL enhancements while maintaining the classic Oblivion feel.",
        "author": "Community",
        "source": "Nexus Collections",
        "source_url": "https://www.nexusmods.com/oblivion",
        "wiki_url": "",
        "mod_count": 200,
        "playstyle_tags": json.dumps(
            ["vanilla_plus", "bug_fixes", "visual_enhancement", "classic"]
        ),
        "performance_tier": "low",
        "upvotes": 0,
        "downvotes": 0,
        "is_seed": 1,
        "seed_note": "Seeded from popular Nexus collections - will be replaced by community submissions",
    },
    # STARFIELD
    {
        "game": "starfield",
        "name": "Melius",
        "description": "Challenging immersive experience based on Serenity of Stars overhaul. Combat AI overhaul, StarUI, Real Fuel/O2, survival mechanics, New Atlantis overhaul.",
        "author": "Community",
        "source": "Wabbajack",
        "source_url": "https://www.wabbajack.org/",
        "wiki_url": "",
        "mod_count": 300,
        "playstyle_tags": json.dumps(["hardcore", "survival", "overhaul", "immersive"]),
        "performance_tier": "mid",
        "upvotes": 0,
        "downvotes": 0,
        "is_seed": 1,
        "seed_note": "Seeded from popular Wabbajack modlist - will be replaced by community submissions",
    },
    # SKYRIM VR
    {
        "game": "skyrimvr",
        "name": "FUS",
        "description": "Fundamental modular modlist for VR with 4 profiles (FUS/FUS RO/FUS RO DAH/Cangar). VRIK, Spellsiphon, HIGGS. Beginner-friendly VR entry point.",
        "author": "Community",
        "source": "Wabbajack",
        "source_url": "https://www.wabbajack.org/",
        "wiki_url": "",
        "mod_count": 400,
        "playstyle_tags": json.dumps(["vr", "modular", "beginner_friendly", "combat_overhaul"]),
        "performance_tier": "mid",
        "upvotes": 0,
        "downvotes": 0,
        "is_seed": 1,
        "seed_note": "Seeded from popular Wabbajack modlist - will be replaced by community submissions",
    },
]


def migrate():
    """Run the migration."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Create community_builds table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS community_builds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            author TEXT NOT NULL DEFAULT 'Community',
            source TEXT NOT NULL DEFAULT 'Community',
            source_url TEXT,
            wiki_url TEXT,
            mod_count INTEGER,
            playstyle_tags TEXT,
            performance_tier TEXT DEFAULT 'mid',
            upvotes INTEGER DEFAULT 0,
            downvotes INTEGER DEFAULT 0,
            is_seed INTEGER DEFAULT 0,
            seed_note TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    # Create index for game-based queries
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_community_builds_game
        ON community_builds(game)
    """
    )

    # Create index for playstyle tag queries
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_community_builds_tags
        ON community_builds(playstyle_tags)
    """
    )

    # Create votes table for tracking user votes
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS community_build_votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            build_id INTEGER NOT NULL,
            user_email TEXT NOT NULL,
            vote INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (build_id) REFERENCES community_builds(id),
            UNIQUE (build_id, user_email)
        )
    """
    )

    # Insert seed data
    for build in SEED_BUILDS:
        cursor.execute(
            """
            INSERT INTO community_builds (
                game, name, description, author, source, source_url, wiki_url,
                mod_count, playstyle_tags, performance_tier, upvotes, downvotes,
                is_seed, seed_note
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                build["game"],
                build["name"],
                build["description"],
                build["author"],
                build["source"],
                build.get("source_url"),
                build.get("wiki_url"),
                build.get("mod_count"),
                build["playstyle_tags"],
                build["performance_tier"],
                build["upvotes"],
                build["downvotes"],
                build["is_seed"],
                build.get("seed_note"),
            ),
        )

    conn.commit()
    conn.close()

    print(f"✓ Created community_builds table with {len(SEED_BUILDS)} seed builds")
    print("  Note: All seed builds are marked with is_seed=1 and will be replaced")
    print("  as community members submit their own builds.")


if __name__ == "__main__":
    migrate()
