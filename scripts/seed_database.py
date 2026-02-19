"""
SkyModderAI - Database Seeding Script

Seeds the database with:
- Curated knowledge sources
- High-credibility mod entries
- Conflict resolution rules
- Version compatibility data

Run with: python scripts/seed_database.py
"""

import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, List

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def seed_knowledge_sources():
    """Seed curated knowledge sources."""
    from db import get_db_session
    from models import KnowledgeSource, SourceCredibility
    
    session = get_db_session()
    
    # Curated knowledge entries
    knowledge_entries = [
        {
            "source_url": "https://www.nexusmods.com/skyrimspecialedition/mods/266",
            "title": "Unofficial Skyrim Special Edition Patch (USSEP)",
            "game": "skyrimse",
            "game_version": "all",
            "category": "utility",
            "subcategory": "bug_fixes",
            "summary": "Essential bug fixes for Skyrim SE. Should be loaded first in load order.",
            "tags": json.dumps(["essential", "bug_fixes", "patch", "ussep"]),
            "credibility_score": 0.98,
            "is_standard_approach": True,
            "requires": json.dumps([]),
            "conflicts_with": json.dumps([])
        },
        {
            "source_url": "https://www.nexusmods.com/skyrimspecialedition/mods/164",
            "title": "SSEEdit",
            "game": "skyrimse",
            "game_version": "all",
            "category": "utility",
            "subcategory": "tools",
            "summary": "Essential tool for cleaning mods, checking conflicts, and editing plugins.",
            "tags": json.dumps(["essential", "tool", "cleaning", "xedit"]),
            "credibility_score": 0.99,
            "is_standard_approach": True,
            "requires": json.dumps([]),
            "conflicts_with": json.dumps([])
        },
        {
            "source_url": "https://skse.silverlock.org/",
            "title": "Skyrim Script Extender (SKSE64)",
            "game": "skyrimse",
            "game_version": "1.6.1170",
            "category": "utility",
            "subcategory": "script_extender",
            "summary": "Required for many advanced mods. Must match game version exactly.",
            "tags": json.dumps(["essential", "skse", "script_extender"]),
            "credibility_score": 1.0,
            "is_standard_approach": True,
            "requires": json.dumps([]),
            "conflicts_with": json.dumps([])
        },
        {
            "source_url": "https://www.nexusmods.com/skyrimspecialedition/mods/12604",
            "title": "Ordinator - Perks of Skyrim",
            "game": "skyrimse",
            "game_version": "all",
            "category": "fun",
            "subcategory": "overhaul",
            "summary": "Complete perk overhaul with 400+ new perks. Requires new game.",
            "tags": json.dumps(["perks", "overhaul", "combat", "ordinator"]),
            "credibility_score": 0.95,
            "is_standard_approach": True,
            "requires": json.dumps(["Address Library for SKSE"]),
            "conflicts_with": json.dumps(["Vokrii", "APCO"])
        },
        {
            "source_url": "https://www.nexusmods.com/skyrimspecialedition/mods/30100",
            "title": "Address Library for SKSE Plugins",
            "game": "skyrimse",
            "game_version": "all",
            "category": "utility",
            "subcategory": "library",
            "summary": "Required library for many SKSE plugins. Essential for modern modding.",
            "tags": json.dumps(["essential", "library", "skse", "address_library"]),
            "credibility_score": 0.97,
            "is_standard_approach": True,
            "requires": json.dumps(["SKSE64"]),
            "conflicts_with": json.dumps([])
        },
        {
            "source_url": "https://www.nexusmods.com/skyrimspecialedition/mods/23401",
            "title": "SkyUI",
            "game": "skyrimse",
            "game_version": "all",
            "category": "utility",
            "subcategory": "interface",
            "summary": "Improved inventory and UI management. Requires SKSE64.",
            "tags": json.dumps(["ui", "inventory", "skyui", "essential"]),
            "credibility_score": 0.96,
            "is_standard_approach": True,
            "requires": json.dumps(["SKSE64"]),
            "conflicts_with": json.dumps([])
        },
        {
            "source_url": "https://www.nexusmods.com/skyrimspecialedition/mods/17230",
            "title": "Cathedral Weathers",
            "game": "skyrimse",
            "game_version": "all",
            "category": "design",
            "subcategory": "weather",
            "summary": "Beautiful weather overhaul with performance focus. No ENB required.",
            "tags": json.dumps(["weather", "visuals", "cathedral", "performance"]),
            "credibility_score": 0.92,
            "is_standard_approach": True,
            "requires": json.dumps([]),
            "conflicts_with": json.dumps(["Obsidian Weathers", "True Storms"])
        },
        {
            "source_url": "https://www.nexusmods.com/skyrimspecialedition/mods/20071",
            "title": "Engine Fixes",
            "game": "skyrimse",
            "game_version": "all",
            "category": "utility",
            "subcategory": "bug_fixes",
            "summary": "Engine bug fixes not covered by USSEP. Essential for stability.",
            "tags": json.dumps(["essential", "engine", "bug_fixes", "stability"]),
            "credibility_score": 0.97,
            "is_standard_approach": True,
            "requires": json.dumps(["SKSE64"]),
            "conflicts_with": json.dumps([])
        }
    ]
    
    added = 0
    for entry in knowledge_entries:
        # Check if exists
        existing = session.query(KnowledgeSource).filter(
            KnowledgeSource.source_url == entry["source_url"]
        ).first()
        
        if existing:
            continue
        
        # Create credibility record
        credibility = SourceCredibility(
            source_url=entry["source_url"],
            source_type="nexus_mods" if "nexusmods" in entry["source_url"] else "official",
            overall_score=entry["credibility_score"],
            source_credibility=entry["credibility_score"],
            content_freshness=0.9,
            community_validation=entry["credibility_score"],
            technical_accuracy=entry["credibility_score"],
            author_reputation=entry["credibility_score"],
            confidence=0.95,
            flags=json.dumps(["highly_reliable", "verified"])
        )
        session.add(credibility)
        session.flush()
        
        # Create knowledge source
        import hashlib
        content_hash = hashlib.sha256(
            f"{entry['title']}|{entry['summary']}|{entry['game']}".encode()
        ).hexdigest()
        
        source = KnowledgeSource(
            source_url=entry["source_url"],
            title=entry["title"],
            content_hash=content_hash,
            game=entry["game"],
            game_version=entry.get("game_version"),
            category=entry["category"],
            subcategory=entry.get("subcategory"),
            tags=entry.get("tags"),
            credibility_id=credibility.id,
            summary=entry["summary"],
            requires=entry.get("requires"),
            conflicts_with=entry.get("conflicts_with"),
            is_standard_approach=entry["is_standard_approach"],
            status="active"
        )
        session.add(source)
        added += 1
    
    session.commit()
    return added


def seed_conflict_rules():
    """Seed common conflict resolution rules."""
    from db import get_db_session
    from models import KnowledgeSource
    
    session = get_db_session()
    
    # Common conflict rules
    conflict_rules = [
        {
            "mod_a": "Ordinator - Perks of Skyrim.esp",
            "mod_b": "Vokrii - Minimalistic Perks of Skyrim.esp",
            "conflict_type": "incompatible",
            "resolution": "Choose one perk overhaul. Ordinator for complexity, Vokrii for simplicity.",
            "priority": "high"
        },
        {
            "mod_a": "Cathedral Weathers.esp",
            "mod_b": "Obsidian Weathers.esp",
            "conflict_type": "incompatible",
            "resolution": "Choose one weather overhaul. Use Cathedral Weathers + Cathedral Snow for best performance.",
            "priority": "high"
        },
        {
            "mod_a": "SkyUI.esp",
            "mod_b": "Classic Skyrim Interface.esp",
            "conflict_type": "load_order",
            "resolution": "Load SkyUI after Classic Skyrim Interface if using both.",
            "priority": "medium"
        },
        {
            "mod_a": "USSEP.esm",
            "mod_b": "any",
            "conflict_type": "load_order",
            "resolution": "USSEP should always be loaded first (after game master files).",
            "priority": "high"
        }
    ]
    
    added = 0
    for rule in conflict_rules:
        # Check if exists
        existing = session.query(KnowledgeSource).filter(
            KnowledgeSource.title == f"Conflict: {rule['mod_a']} vs {rule['mod_b']}"
        ).first()
        
        if existing:
            continue
        
        source = KnowledgeSource(
            source_url=f"internal:conflict:{rule['mod_a']}:{rule['mod_b']}",
            title=f"Conflict: {rule['mod_a']} vs {rule['mod_b']}",
            content_hash=f"conflict:{rule['mod_a']}:{rule['mod_b']}",
            game="skyrimse",
            category="conflict_resolution",
            summary=rule["resolution"],
            conflicts_with=json.dumps([rule["mod_b"] if rule["mod_b"] != "any" else "*"]),
            is_standard_approach=True,
            status="active"
        )
        session.add(source)
        added += 1
    
    session.commit()
    return added


def seed_version_data():
    """Seed game version compatibility data."""
    from db import get_db_session
    
    session = get_db_session()
    
    # This would typically update existing mod entries with version info
    # For now, just log that this step completed
    
    print("  Version data seeding: SKIPPED (requires existing mod database)")
    return 0


def run_seeding():
    """Run all seeding operations."""
    print("=" * 70)
    print("SkyModderAI Database Seeding")
    print("=" * 70)
    print()
    
    print("Seeding knowledge sources...")
    knowledge_added = seed_knowledge_sources()
    print(f"  Added {knowledge_added} knowledge sources")
    
    print("\nSeeding conflict rules...")
    conflicts_added = seed_conflict_rules()
    print(f"  Added {conflicts_added} conflict rules")
    
    print("\nSeeding version data...")
    version_added = seed_version_data()
    
    print("\n" + "=" * 70)
    print(f"Seeding complete!")
    print(f"  Knowledge sources: {knowledge_added}")
    print(f"  Conflict rules: {conflicts_added}")
    print(f"  Version data: {version_added}")
    print("=" * 70)
    
    return {
        "knowledge_sources": knowledge_added,
        "conflict_rules": conflicts_added,
        "version_data": version_added
    }


if __name__ == "__main__":
    results = run_seeding()
    
    # Save results
    results_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "seeding_report.json"
    )
    
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\nReport saved to: {results_path}")
