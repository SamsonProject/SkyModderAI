"""
Game executable version database for SkyModderAI.
Maps game IDs to known executable versions with compatibility notes.
Used for version-aware conflict detection and user education.

CRITICAL: LE and SE versions are distinct and must never be mixed.
- Skyrim LE: 1.9.32 only (32-bit, SKSE, DirectX 9)
- Skyrim SE: 1.4.x to 1.6.x (64-bit, SKSE64, DirectX 11)
- Anniversary Edition = Special Edition 1.6+ (not a separate game)
"""

# Skyrim Legendary Edition (LE) - The OLD Skyrim (2011-2016)
# Only ONE version that matters: 1.9.32
# Uses old SKSE (not SKSE64), 32-bit engine, DirectX 9
SKYRIM_LE_VERSIONS = {
    "1.9.32.0.8": {
        "name": "Final Version (1.9.32)",
        "date": "March 2013",
        "skse": "SKSE 1.7.3",
        "notes": "Final version before Special Edition. Most LE mods target this.",
        "common": True,
    }
}

# Skyrim Special Edition (SE) - The REMASTER (2016+)
# 64-bit engine, SKSE64, DirectX 11
# Pre-AE: 1.5.97 | AE: 1.6.x (Anniversary Edition IS Special Edition)
SKYRIM_SE_VERSIONS = {
    "1.5.97": {
        "name": "Pre-Anniversary (1.5.97)",
        "date": "Nov 10, 2021",
        "skse": "SKSE64 2.0.20",
        "notes": "MOST MODS TARGET THIS. Last version before Anniversary broke everything. Many users stay here.",
        "common": True,
        "recommended": True,
    },
    "1.6.317": {
        "name": "Anniversary Launch (1.6.317)",
        "date": "Nov 11, 2021",
        "skse": "SKSE64 2.1.0+",
        "notes": "Anniversary Edition release. Broke most SKSE mods. Address Library v2 → v11.",
    },
    "1.6.353": {
        "name": "AE Patch 1 (1.6.353)",
        "date": "Nov 2021",
        "skse": "SKSE64 2.1.3+",
        "notes": "First AE hotfix. Still unstable.",
    },
    "1.6.640": {
        "name": "AE Stable (1.6.640)",
        "date": "Sept 2022",
        "skse": "SKSE64 2.1.5+",
        "notes": "Most common AE version. Many mods updated for this. Stable modding.",
        "common": True,
    },
    "1.6.1130": {
        "name": "Creations Update (1.6.1130)",
        "date": "Dec 5, 2023",
        "skse": "SKSE64 2.2.3+",
        "notes": "Added unified Creations menu. ESL range doubled to 4096. Broke mods again.",
    },
    "1.6.1170": {
        "name": "Latest (1.6.1170)",
        "date": "Jan 17, 2024",
        "skse": "SKSE64 2.2.6+",
        "notes": "Current version. Requires updated Address Library. Limited mod support.",
        "warning": "Many mods haven't updated for 1.6.1170 yet. Consider 1.6.640 for better compatibility.",
    },
}

# Skyrim VR - Frozen at SE version 1.4.15, uses SKSEVR
SKYRIM_VR_VERSIONS = {
    "1.4.15.0": {
        "name": "Latest (1.4.15)",
        "date": "2018",
        "skse": "SKSEVR 2.0.12",
        "notes": "Based on Skyrim SE 1.4.15. Never updated to AE. Uses SKSEVR.",
        "common": True,
    }
}

# Fallout 4
FALLOUT4_VERSIONS = {
    "1.10.163.0": {
        "name": "Pre-Next Gen (1.10.163)",
        "date": "Feb 2019",
        "f4se": "F4SE 0.6.21",
        "notes": "MOST MODS TARGET THIS. Last version before Next Gen. Most users stay here or downgrade to this.",
        "common": True,
        "recommended": True,
    },
    "1.10.980.0": {
        "name": "Next Gen Beta (1.10.980)",
        "date": "April 25, 2024",
        "f4se": "F4SE 0.7.0+",
        "notes": "Initial Next Gen update. Broke ALL F4SE mods. Community backlash.",
    },
    "1.10.984.0": {
        "name": "Next Gen Latest (1.10.984)",
        "date": "May 2024",
        "f4se": "F4SE 0.7.2+",
        "notes": "Current version. Many mods still broken. Downgrade patcher highly recommended.",
        "warning": "Next Gen Update broke most mods! Strongly recommend downgrading to 1.10.163.",
        "downgrade_link": "https://www.nexusmods.com/fallout4/mods/78896",
    },
}

# Fallout 3
FALLOUT3_VERSIONS = {
    "1.7.0.3": {
        "name": "GOTY Final (1.7.0.3)",
        "date": "2009",
        "fose": "FOSE 1.3",
        "notes": "Final version. Game of the Year Edition.",
        "common": True,
    }
}

# Fallout New Vegas
FALLOUT_NV_VERSIONS = {
    "1.4.0.525": {
        "name": "Ultimate Edition (1.4.0.525)",
        "date": "2012",
        "nvse": "NVSE 6.3.6",
        "notes": "Final version. Ultimate Edition with all DLC.",
        "common": True,
    }
}

# Oblivion
OBLIVION_VERSIONS = {
    "1.2.0.416": {
        "name": "GOTY Final (1.2.0.416)",
        "date": "2007",
        "obse": "OBSE 0021",
        "notes": "Final official version. Game of the Year Edition.",
        "common": True,
    }
}

# Starfield
STARFIELD_VERSIONS = {
    "1.7.29.0": {
        "name": "Launch (1.7.29)",
        "date": "Sept 2023",
        "sfse": "SFSE 0.1.x",
        "notes": "Launch version. Most initial mods target this.",
    },
    "1.8.86.0": {
        "name": "November Update (1.8.86)",
        "date": "Nov 2023",
        "sfse": "SFSE 0.2.x",
        "notes": "First major update.",
    },
    "1.10.30.0": {
        "name": "Current (1.10.30)",
        "date": "2024",
        "sfse": "SFSE 0.3.x+",
        "notes": "Most mods updated for this version.",
        "common": True,
    },
}

# Map game IDs (used by app) to their version sets
# skyrim = LE, skyrimse = SE, skyrimvr = VR
GAME_VERSIONS = {
    "skyrim": SKYRIM_LE_VERSIONS,
    "skyrimse": SKYRIM_SE_VERSIONS,
    "skyrimvr": SKYRIM_VR_VERSIONS,
    "oblivion": OBLIVION_VERSIONS,
    "fallout3": FALLOUT3_VERSIONS,
    "falloutnv": FALLOUT_NV_VERSIONS,
    "fallout4": FALLOUT4_VERSIONS,
    "starfield": STARFIELD_VERSIONS,
}


def get_versions_for_game(game_id: str) -> dict:
    """Return version dict for a game, or empty dict if unknown."""
    return GAME_VERSIONS.get((game_id or "").lower(), {})


def get_version_info(game_id: str, version: str) -> dict | None:
    """Return info for a specific game+version, or None.
    Supports fuzzy matching: e.g. user selects 1.5.97, stored as 1.5.97."""
    versions = get_versions_for_game(game_id)
    if not versions:
        return None
    # Exact match first
    if version in versions:
        return versions[version]
    # Fuzzy: strip trailing .0 for display variants (1.10.163 vs 1.10.163.0)
    for k, v in versions.items():
        if k.rstrip(".0") == version.rstrip(".0") or k == version:
            return v
    return None


def get_default_version(game_id: str) -> str:
    """Return the recommended or most common version for a game, or empty string."""
    versions = get_versions_for_game(game_id)
    if not versions:
        return ""
    # Prefer recommended
    for v, info in versions.items():
        if info.get("recommended"):
            return v
    # Fallback: common
    for v, info in versions.items():
        if info.get("common"):
            return v
    # Fallback: first version
    return next(iter(versions), "")


def get_version_warning(game_id: str, version: str) -> dict | None:
    """Return warning dict for a game+version if one exists. { severity, message, link }."""
    info = get_version_info(game_id, version)
    if not info or not info.get("warning"):
        return None
    return {
        "severity": "warning",
        "message": info["warning"],
        "link": info.get("downgrade_link", ""),
    }
