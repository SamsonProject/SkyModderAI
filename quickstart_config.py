"""
Quick Start config — Central source for game-specific links and resources.
Used by /api/quickstart and avoids hard-coding in templates/docs.

NOTE: No hardcoded mod recommendations. All mod suggestions come from:
1. Community builds (user-submitted, voted)
2. LOOT data (search engine)
3. User's own analysis

Tool links (Nexus, LOOT, xEdit) are universal utilities, not mod recommendations.
"""

from typing import Any, Dict

# Global tool links (not game-specific) - These are universal utilities
TOOLS = {
    "nexus": {
        "name": "Nexus Mods",
        "url": "https://www.nexusmods.com/",
        "desc": "Mod downloads for all Bethesda games",
    },
    "loot": {
        "name": "LOOT",
        "url": "https://loot.github.io/",
        "desc": "Load order optimizer (desktop app)",
    },
    "xedit": {
        "name": "xEdit",
        "url": "https://tes5edit.github.io/",
        "desc": "SSEEdit, FO4Edit, FNVEdit, etc. For cleaning and conflict resolution",
    },
    "wabbajack": {
        "name": "Wabbajack",
        "url": "https://www.wabbajack.org/",
        "desc": "One-click mod list installer",
    },
}

# Mod managers — Vortex is site-wide; MO2 has primary Nexus page (Skyrim SE)
MOD_MANAGERS = {
    "mo2": {
        "name": "Mod Organizer 2 (MO2)",
        "url": "https://www.nexusmods.com/skyrimspecialedition/mods/6194",
        "desc": "Popular mod manager for Bethesda games",
    },
    "vortex": {
        "name": "Vortex",
        "url": "https://www.nexusmods.com/site/mods/1",
        "desc": "Nexus official mod manager",
    },
}

# Learning resources
LEARNING_RESOURCES = [
    {
        "name": "GamerPoets",
        "url": "https://www.youtube.com/@GamerPoets",
        "desc": "Step-by-step tutorials on MO2, xEdit, conflict resolution. Skyrim & Fallout.",
    },
    {
        "name": "Gopher",
        "url": "https://www.youtube.com/@GopherVids",
        "desc": "Classic Skyrim modding guides. MO2, LOOT, fundamentals.",
    },
    {
        "name": "xEdit documentation",
        "url": "https://tes5edit.github.io/docs/",
        "desc": "Official docs for SSEEdit, FO4Edit. Cleaning, conflict resolution.",
    },
]

INTERNAL_LINKS = [
    {"name": "Sign up", "url": "/signup-pro", "desc": "Create your account before checkout."},
    {
        "name": "Profile",
        "url": "/profile",
        "desc": "Manage sessions, API keys, and linked accounts.",
    },
    {
        "name": "Pricing section",
        "url": "/#pricing",
        "desc": "Compare Free, Pro, and OpenClaw Lab tiers.",
    },
]

NOOB_JOURNEY = [
    {"step": "Install a mod manager first (MO2 or Vortex)."},
    {"step": "Copy your plugin/load order list exactly as text."},
    {"step": "Paste into Analyze, fix red errors first, then warnings."},
    {"step": "Keep a backup before major mod changes."},
    {"step": "Use Build a List when starting fresh and send it to Analyze."},
]

# Per-game quickstart data: Links to game pages on Nexus, AppData path
# NOTE: No hardcoded mod recommendations (USSEP, SKSE, etc.)
# Users should browse community builds or use the search engine
GAME_QUICKSTART: Dict[str, Dict[str, Any]] = {
    "skyrimse": {
        "name": "Skyrim SE",
        "nexus_slug": "skyrimspecialedition",
        "nexus_mods_url": "https://www.nexusmods.com/skyrimspecialedition/mods",
        "appdata_path": "%LOCALAPPDATA%\\Skyrim Special Edition\\",
        "mo2_url": "https://www.nexusmods.com/skyrimspecialedition/mods/6194",
    },
    "skyrim": {
        "name": "Skyrim LE",
        "nexus_slug": "skyrim",
        "nexus_mods_url": "https://www.nexusmods.com/skyrim/mods",
        "appdata_path": "%LOCALAPPDATA%\\Skyrim\\",
        "mo2_url": "https://www.nexusmods.com/skyrim/mods/6194",
    },
    "skyrimvr": {
        "name": "Skyrim VR",
        "nexus_slug": "skyrimspecialedition",
        "nexus_mods_url": "https://www.nexusmods.com/skyrimspecialedition/mods",
        "appdata_path": "%LOCALAPPDATA%\\Skyrim VR\\",
        "mo2_url": "https://www.nexusmods.com/skyrimspecialedition/mods/6194",
    },
    "oblivion": {
        "name": "Oblivion",
        "nexus_slug": "oblivion",
        "nexus_mods_url": "https://www.nexusmods.com/oblivion/mods",
        "appdata_path": "%LOCALAPPDATA%\\Oblivion\\",
        "mo2_url": "https://www.nexusmods.com/oblivion/mods/1334",
    },
    "fallout3": {
        "name": "Fallout 3",
        "nexus_slug": "fallout3",
        "nexus_mods_url": "https://www.nexusmods.com/fallout3/mods",
        "appdata_path": "%LOCALAPPDATA%\\Fallout3\\",
        "mo2_url": "https://www.nexusmods.com/fallout3/mods/6194",
    },
    "falloutnv": {
        "name": "Fallout New Vegas",
        "nexus_slug": "newvegas",
        "nexus_mods_url": "https://www.nexusmods.com/newvegas/mods",
        "appdata_path": "%LOCALAPPDATA%\\FalloutNV\\",
        "mo2_url": "https://www.nexusmods.com/newvegas/mods/6194",
    },
    "fallout4": {
        "name": "Fallout 4",
        "nexus_slug": "fallout4",
        "nexus_mods_url": "https://www.nexusmods.com/fallout4/mods",
        "appdata_path": "%LOCALAPPDATA%\\Fallout4\\",
        "mo2_url": "https://www.nexusmods.com/fallout4/mods/6194",
    },
    "starfield": {
        "name": "Starfield",
        "nexus_slug": "starfield",
        "nexus_mods_url": "https://www.nexusmods.com/starfield/mods",
        "appdata_path": "%LOCALAPPDATA%\\Starfield\\",
        "mo2_url": "https://www.nexusmods.com/starfield/mods/6194",
    },
}

_OS_PLUGIN_PATHS: Dict[str, Dict[str, str]] = {
    "skyrimse": {
        "windows": r"%LOCALAPPDATA%\Skyrim Special Edition\plugins.txt",
        "linux": "~/.local/share/Steam/steamapps/compatdata/<app_id>/pfx/drive_c/users/steamuser/AppData/Local/Skyrim Special Edition/plugins.txt",
        "mac": "No native macOS runtime. Use Windows VM or CrossOver path to AppData and copy plugins.txt.",
    },
    "skyrim": {
        "windows": r"%LOCALAPPDATA%\Skyrim\plugins.txt",
        "linux": "~/.local/share/Steam/steamapps/compatdata/<app_id>/pfx/drive_c/users/steamuser/AppData/Local/Skyrim/plugins.txt",
        "mac": "No native macOS runtime. Use Windows VM or CrossOver path to AppData and copy plugins.txt.",
    },
    "skyrimvr": {
        "windows": r"%LOCALAPPDATA%\Skyrim VR\plugins.txt",
        "linux": "~/.local/share/Steam/steamapps/compatdata/<app_id>/pfx/drive_c/users/steamuser/AppData/Local/Skyrim VR/plugins.txt",
        "mac": "No native macOS runtime. Use Windows VM or CrossOver path to AppData and copy plugins.txt.",
    },
    "oblivion": {
        "windows": r"%LOCALAPPDATA%\Oblivion\plugins.txt",
        "linux": "~/.local/share/Steam/steamapps/compatdata/<app_id>/pfx/drive_c/users/steamuser/AppData/Local/Oblivion/plugins.txt",
        "mac": "No native macOS runtime. Use Windows VM or CrossOver path to AppData and copy plugins.txt.",
    },
    "fallout3": {
        "windows": r"%LOCALAPPDATA%\Fallout3\plugins.txt",
        "linux": "~/.local/share/Steam/steamapps/compatdata/<app_id>/pfx/drive_c/users/steamuser/AppData/Local/Fallout3/plugins.txt",
        "mac": "No native macOS runtime. Use Windows VM or CrossOver path to AppData and copy plugins.txt.",
    },
    "falloutnv": {
        "windows": r"%LOCALAPPDATA%\FalloutNV\plugins.txt",
        "linux": "~/.local/share/Steam/steamapps/compatdata/<app_id>/pfx/drive_c/users/steamuser/AppData/Local/FalloutNV/plugins.txt",
        "mac": "No native macOS runtime. Use Windows VM or CrossOver path to AppData and copy plugins.txt.",
    },
    "fallout4": {
        "windows": r"%LOCALAPPDATA%\Fallout4\plugins.txt",
        "linux": "~/.local/share/Steam/steamapps/compatdata/<app_id>/pfx/drive_c/users/steamuser/AppData/Local/Fallout4/plugins.txt",
        "mac": "No native macOS runtime. Use Windows VM or CrossOver path to AppData and copy plugins.txt.",
    },
    "starfield": {
        "windows": r"%LOCALAPPDATA%\Starfield\plugins.txt",
        "linux": "~/.local/share/Steam/steamapps/compatdata/<app_id>/pfx/drive_c/users/steamuser/AppData/Local/Starfield/plugins.txt",
        "mac": "No native macOS runtime. Use cloud/remote Windows path and paste plugin text.",
    },
}


def get_quickstart_for_game(game_id: str) -> Dict[str, Any]:
    """Get quickstart data for a game. Falls back to skyrimse if unknown."""
    gid = game_id.lower()
    out = GAME_QUICKSTART.get(gid, GAME_QUICKSTART["skyrimse"]).copy()
    out["os_plugin_paths"] = _OS_PLUGIN_PATHS.get(gid, _OS_PLUGIN_PATHS["skyrimse"])
    return out


def get_all_quickstart() -> Dict[str, Any]:
    """Return full quickstart config for API."""
    return {
        "tools": TOOLS,
        "mod_managers": MOD_MANAGERS,
        "learning_resources": LEARNING_RESOURCES,
        "internal_links": INTERNAL_LINKS,
        "noob_journey": NOOB_JOURNEY,
        "games": {gid: get_quickstart_for_game(gid) for gid in GAME_QUICKSTART},
    }
