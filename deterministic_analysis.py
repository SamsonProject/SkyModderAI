"""
Deterministic Analysis Service
Replaces AI calls with deterministic logic for load order analysis, game folder scans, etc.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any, Optional

from conflict_detector import ConflictDetector
from knowledge_index import get_resolution_for_conflict
from loot_parser import LOOTParser

logger = logging.getLogger(__name__)


def analyze_load_order_deterministic(mod_list: list[str], game: str) -> dict[str, Any]:
    """
    Deterministic load order analysis.
    Replaces AI-based analysis with ConflictDetector + LOOT rules.

    Returns: {
        "conflicts": [...],
        "missing_requirements": [...],
        "load_order_issues": [...],
        "recommendations": [...],
        "dirty_edits": [...]
    }
    """
    detector = ConflictDetector(game)
    parser = LOOTParser(game)

    # Parse mod list
    mods = [ModListEntry(name=name, position=i) for i, name in enumerate(mod_list)]

    # Run deterministic analysis
    conflicts = detector.detect_conflicts(mods)
    missing = detector.check_missing_requirements(mods)
    load_order = detector.check_load_order(mods)
    dirty = detector.check_dirty_edits(mods)

    # Generate recommendations from knowledge index
    recommendations = []
    for conflict in conflicts:
        resolution = get_resolution_for_conflict(conflict["type"], game)
        if resolution:
            recommendations.append(
                {"type": "conflict_resolution", "content": resolution, "priority": "high"}
            )

    return {
        "conflicts": conflicts,
        "missing_requirements": missing,
        "load_order_issues": load_order,
        "recommendations": recommendations,
        "dirty_edits": dirty,
    }


def scan_game_folder_deterministic(
    game_path: str,
    game: str,
    tree: str = "",
    key_files: dict[str, str] = None,
    plugins: list[str] = None,
) -> dict[str, Any]:
    """
    Deterministic game folder scan.
    Replaces AI-based scan with file system checks + pattern matching.

    Returns: {
        "findings": [...],
        "warnings": [...],
        "plugins_found": [...],
        "issues": [...]
    }
    """
    findings = []
    warnings = []
    issues = []

    plugins = plugins or []
    key_files = key_files or {}

    # Check for expected files based on game
    expected_files = _get_expected_files(game)
    for expected in expected_files:
        found = any(expected in path for path in key_files.keys())
        if not found:
            warnings.append(f"Expected file not found: {expected}")

    # Check for direct overwrites in Data/
    if tree:
        overwrite_patterns = [
            r"Data/.*\.esp",
            r"Data/.*\.esm",
            r"Data/.*\.esl",
            r"Data/Meshes/.*",
            r"Data/Textures/.*",
        ]
        for pattern in overwrite_patterns:
            matches = re.findall(pattern, tree)
            if matches:
                findings.append(
                    {
                        "type": "direct_overwrite",
                        "content": f"Direct Data/ files found: {len(matches)} files",
                        "severity": "medium",
                    }
                )
                break

    # Check plugins.txt vs actual Data/ content
    if plugins:
        # Check for orphaned plugins
        plugin_files = [f for f in key_files.keys() if f.endswith((".esp", ".esm", ".esl"))]
        orphaned = set(plugins) - set(Path(f).name for f in plugin_files)
        if orphaned:
            issues.append(
                {
                    "type": "orphaned_plugins",
                    "content": f"{len(orphaned)} plugins in plugins.txt not found in Data/",
                    "orphaned": list(orphaned)[:10],
                }
            )

    # Check for SKSE/requirements
    skse_files = {
        "skyrimse": "SKSE64.dll",
        "skyrimvr": "SKSE64.dll",
        "skyrim": "SKSE.dll",
        "fallout4": "skse_steam_loader.dll",
    }
    skse_expected = skse_files.get(game)
    if skse_expected:
        has_skse = any(skse_expected in path for path in key_files.keys())
        if not has_skse:
            findings.append(
                {
                    "type": "missing_skse",
                    "content": f"{game.upper()} Script Extender not detected",
                    "severity": "low",
                }
            )

    return {
        "findings": findings,
        "warnings": warnings,
        "issues": issues,
        "plugins_found": plugins[:255],
    }


def generate_bespoke_setups_deterministic(
    game: str, preferences: dict[str, str], specs: Optional[dict[str, Any]] = None, limit: int = 3
) -> list[dict[str, Any]]:
    """
    Deterministic mod list setup generation.
    Replaces AI-based setup generation with preference mapping.

    Returns: [
        {
            "name": "Balanced Playthrough",
            "mods": [...],
            "rationale": "..."
        },
        ...
    ]
    """
    # Preference to mod mapping
    PREFERENCE_MAP = {
        "combat": {
            "vanilla": ["Unofficial Patch", "Bug Fixes"],
            "souls_like": ["Ordinator", "Wildcat", "SPID"],
            "action": ["Valhalla Combat", "Wildcat", "SPID"],
            "immersive": ["Immersive Encounters", "AI Overhaul"],
        },
        "graphics": {
            "performance": ["Ruvaak Dahmaan", "Skyland AIO"],
            "balanced": ["Skyland AIO", "Noble Skyrim"],
            "ultra": ["Skyland AIO", "Parallax Meshes"],
            "enb": ["ENB Helper", "Rudy ENB"],
        },
        "environment": {
            "dark_fantasy": ["Obsidian Weathers", "Supreme Storms"],
            "vanilla_plus": ["Cathedral Weathers", "Skyland AIO"],
            "high_fantasy": ["Apocalypse Spells", "Ordinator"],
            "survival": ["Frostfall", "iNeed", "Survival Mode"],
        },
        "stability": {
            "max": ["Engine Fixes", "Bug Fixes", "SSE Display Tweaks"],
            "balanced": ["Engine Fixes", "Bug Fixes"],
            "experimental": [],
        },
    }

    # Generate setups based on preferences
    setups = []

    # Setup 1: Preference-focused
    setup1_mods = set()
    setup1_name = "Custom Build"
    for pref_key, pref_value in preferences.items():
        if pref_value and pref_value != "any":
            mods = PREFERENCE_MAP.get(pref_key, {}).get(pref_value, [])
            setup1_mods.update(mods)

    if setup1_mods:
        setups.append(
            {
                "name": setup1_name,
                "mods": [
                    {
                        "name": m,
                        "nexus_url": f"https://nexusmods.com/search?q={m.replace(' ', '%20')}",
                    }
                    for m in list(setup1_mods)[:15]
                ],
                "rationale": f"Built from your preferences: {', '.join(f'{k}={v}' for k, v in preferences.items() if v and v != 'any')}",
            }
        )

    # Setup 2: Performance-focused (if specs indicate low VRAM)
    if specs:
        vram = specs.get("vram_gb", 0)
        if vram and vram < 4:
            perf_mods = (
                PREFERENCE_MAP["graphics"]["performance"] + PREFERENCE_MAP["stability"]["max"]
            )
            setups.append(
                {
                    "name": "Performance Build",
                    "mods": [
                        {
                            "name": m,
                            "nexus_url": f"https://nexusmods.com/search?q={m.replace(' ', '%20')}",
                        }
                        for m in perf_mods[:12]
                    ],
                    "rationale": f"Optimized for your system ({vram}GB VRAM) - prioritizes performance and stability",
                }
            )

    # Setup 3: Stability-focused
    stability_mods = PREFERENCE_MAP["stability"]["max"] + ["Unofficial Patch", "Bug Fixes"]
    setups.append(
        {
            "name": "Stability First",
            "mods": [
                {"name": m, "nexus_url": f"https://nexusmods.com/search?q={m.replace(' ', '%20')}"}
                for m in stability_mods[:10]
            ],
            "rationale": "Maximum stability - essential patches and fixes only",
        }
    )

    return setups[:limit]


def _get_expected_files(game: str) -> list[str]:
    """Get list of expected files for a game."""
    expected = {
        "skyrimse": ["SkyrimSE.exe", "SkyrimPrefs.ini", "Skyrim.ini"],
        "skyrimvr": ["SkyrimVR.exe", "SkyrimPrefs.ini", "Skyrim.ini"],
        "skyrim": ["SkyrimLauncher.exe", "SkyrimPrefs.ini", "Skyrim.ini"],
        "fallout4": ["Fallout4.exe", "Fallout4Prefs.ini", "Fallout4.ini"],
    }
    return expected.get(game, [])


# Import needed for ModListEntry
from dataclasses import dataclass


@dataclass
class ModListEntry:
    name: str
    position: int
    enabled: bool = True

    def __hash__(self):
        return hash(self.name.lower())
