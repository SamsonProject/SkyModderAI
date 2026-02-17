"""
SkyModderAI Knowledge Index — Structured knowledge graph for AI assistant navigation.

Maps:
- Conflict types → resolution patterns, tools, links
- Mod relationships → requirements, patches, incompatibilities
- Game-specific resources → Nexus, xEdit, LOOT, Reddit, wikis
- Esoteric solutions → common fixes for CTD, ILS, dirty edits

Designed for AI to query: "Given conflict X, what are known resolutions?"
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------
# Conflict type → resolution patterns (what to suggest)
# -------------------------------------------------------------------
CONFLICT_RESOLUTIONS = {
    "missing_requirement": {
        "description": "Mod requires another mod that is not installed",
        "actions": [
            "Install the required mod from Nexus or the mod page",
            "Check mod description for exact version requirements (SKSE, DLC, etc.)",
            "Use LOOT to see masterlist recommendations",
        ],
        "tools": ["LOOT", "Nexus Mods", "Mod Organizer 2", "Vortex"],
        "links": [
            ("Nexus Mods", "https://www.nexusmods.com/"),
            ("LOOT", "https://loot.github.io/"),
        ],
        "common_causes": ["SKSE", "Address Library", "DLC", "USSEP", "RaceMenu", "Body mod"],
    },
    "incompatible": {
        "description": "Two mods conflict and should not be used together",
        "actions": [
            "Choose one mod or the other—do not run both",
            'Check if a compatibility patch exists (search "X Y patch" on Nexus)',
            "Some incompatibilities can be resolved with load order or patches",
        ],
        "tools": ["xEdit", "LOOT", "Nexus Mods"],
        "links": [
            (
                "xEdit conflict resolution",
                "https://tes5edit.github.io/docs/5-mod-conflict-resolution.html",
            ),
        ],
        "common_causes": [
            "Two overhauls of same system",
            "Duplicate functionality",
            "Script conflicts",
        ],
    },
    "load_order_violation": {
        "description": "Mod should load before or after another for correct behavior",
        "actions": [
            "Run LOOT to auto-sort load order",
            "Manually move the mod in Mod Organizer 2 or Vortex",
            "Create a custom LOOT rule if the masterlist is wrong",
        ],
        "tools": ["LOOT", "Mod Organizer 2", "Vortex"],
        "links": [
            ("LOOT", "https://loot.github.io/"),
            ("LOOT metadata", "https://github.com/loot"),
        ],
        "common_causes": [
            "Patches must load after both parent mods",
            "Framework before dependent mods",
        ],
    },
    "patch_available": {
        "description": "Compatibility patch exists for mods you have installed",
        "actions": [
            "Download and install the patch from Nexus",
            "Enable the patch and place it after both parent mods in load order",
            "Check patch requirements (may need all DLC or specific versions)",
        ],
        "tools": ["Nexus Mods", "LOOT"],
        "links": [],
        "common_causes": ["Popular mod combinations have community patches"],
    },
    "dirty_edits": {
        "description": "Mod has ITM/UDR records that can cause subtle bugs",
        "actions": [
            "Clean with xEdit (SSEEdit, FO4Edit, etc.)—see the cleaning guide",
            "Backup the mod before cleaning",
            "Do not clean mods that explicitly say not to (e.g. some bashed patches)",
        ],
        "tools": ["xEdit", "SSEEdit", "FO4Edit", "TES5Edit"],
        "links": [
            (
                "xEdit cleaning guide",
                "https://tes5edit.github.io/docs/7-mod-cleaning-and-error-checking.html#ThreeEasyStepstocleanMods",
            ),
        ],
        "common_causes": [
            "Mod was created in CK without proper cleaning",
            "Old mods from before cleaning was common",
        ],
    },
    "unknown_mod": {
        "description": "Mod not in LOOT masterlist—may be custom, renamed, or new",
        "actions": [
            "Check if the name is correct (typo? different version?)",
            "Search Nexus for the mod—it may have a different filename",
            "Custom/merged mods will not be in the database",
        ],
        "tools": ["Nexus Mods", "LOOT"],
        "links": [],
        "common_causes": ["Custom merge", "Renamed plugin", "Very new mod", "Non-Nexus mod"],
    },
    "cross_game": {
        "description": "Mod appears to be for a different game (e.g. LE mod in SE list)",
        "actions": [
            "Install the correct game version of the mod",
            "USSEP for SE, USLEEP for LE; SkyUI_SE for SE, SkyUI for LE",
        ],
        "tools": ["Nexus Mods"],
        "links": [],
        "common_causes": ["Wrong game filter on Nexus", "Pasted list from different game"],
    },
    "info": {
        "description": "Informational message from LOOT masterlist",
        "actions": [
            "Read the message—it may contain version checks or setup tips",
            "Not all info messages require action",
        ],
        "tools": [],
        "links": [],
        "common_causes": [
            "Version compatibility notes",
            "Optional requirements",
            "Setup instructions",
        ],
    },
}

# -------------------------------------------------------------------
# Esoteric / scattered solutions (CTD, ILS, common issues)
# -------------------------------------------------------------------
ESOTERIC_SOLUTIONS = [
    {
        "issue": "Crash to desktop (CTD) on startup",
        "causes": [
            "Missing master",
            "SKSE version mismatch",
            "Address Library outdated",
            "DLL conflict",
        ],
        "solutions": [
            "Run LOOT—missing masters show as errors",
            "Check SKSE version matches game (1.5.97 vs 1.6.640 have different mod support)",
            "Update Address Library for SKSE plugins",
            "Disable mods one by one to isolate the culprit",
        ],
        "keywords": ["ctd", "crash", "startup", "launch"],
    },
    {
        "issue": "Infinite loading screen (ILS)",
        "causes": ["Load order", "Missing navmesh", "Script overload", "Too many mods"],
        "solutions": [
            "Run LOOT and fix load order",
            "Disable mods that add many NPCs/scripts",
            "Increase Papyrus budget (ini tweaks)",
            "Check for mods that conflict on same area",
        ],
        "keywords": ["ils", "infinite loading", "loading screen", "stuck"],
    },
    {
        "issue": "Game runs but mods do not work",
        "causes": [
            "Mod not enabled",
            "Wrong load order",
            "Missing requirement",
            "SKSE not launching",
        ],
        "solutions": [
            "Launch via SKSE loader, not Steam",
            "Enable the mod in MO2/Vortex",
            "Check mod is in correct load order",
            "Verify all requirements are installed",
        ],
        "keywords": ["not working", "does not work", "not loading", "no effect"],
    },
    {
        "issue": "Purple/missing textures",
        "causes": ["Archives not registered", "Wrong install order", "Missing texture pack"],
        "solutions": [
            "Enable archive invalidation / bInvalidateOlderFiles=1",
            "Install texture mods after body/armor mods",
            "Check mod has loose files or BSA is loaded",
        ],
        "keywords": ["purple", "missing texture", "pink", "checkerboard"],
    },
    {
        "issue": "T-posing / broken animations",
        "causes": ["FNIS/Nemesis not run", "Wrong skeleton", "Animation conflict"],
        "solutions": [
            "Run FNIS or Nemesis after installing animation mods",
            "Install XPMSSE or compatible skeleton",
            "Do not mix FNIS and Nemesis for same animation types",
        ],
        "keywords": ["t-pose", "tpose", "animation", "fnis", "nemesis", "skeleton"],
    },
    {
        "issue": "Script errors / Papyrus spam",
        "causes": ["Incompatible mods", "Outdated mod", "Missing dependency"],
        "solutions": [
            "Check Papyrus log for which mod throws errors",
            "Update or remove the offending mod",
            "Some errors are harmless—focus on CTDs and broken features",
        ],
        "keywords": ["papyrus", "script", "error", "log"],
    },
]

# -------------------------------------------------------------------
# Game-specific resource links
# -------------------------------------------------------------------
GAME_RESOURCES = {
    "skyrimse": {
        "nexus_slug": "skyrimspecialedition",
        "xedit": "SSEEdit",
        "xedit_url": "https://www.nexusmods.com/skyrimspecialedition/mods/164",
        "skse_url": "https://skse.silverlock.org/",
        "loot_repo": "loot/skyrimse",
        "reddit": ["r/skyrimmods", "r/skyrimmods"],
        "wiki": "https://www.nexusmods.com/skyrimspecialedition/wiki/",
    },
    "skyrim": {
        "nexus_slug": "skyrim",
        "xedit": "TES5Edit",
        "xedit_url": "https://www.nexusmods.com/skyrim/mods/25859",
        "skse_url": "https://skse.silverlock.org/",
        "loot_repo": "loot/skyrim",
        "reddit": ["r/skyrimmods"],
        "wiki": "https://www.nexusmods.com/skyrim/wiki/",
    },
    "skyrimvr": {
        "nexus_slug": "skyrimspecialedition",
        "xedit": "SSEEdit",
        "xedit_url": "https://www.nexusmods.com/skyrimspecialedition/mods/164",
        "skse_url": "https://skse.silverlock.org/",
        "loot_repo": "loot/skyrimvr",
        "reddit": ["r/skyrimvr", "r/skyrimmods"],
        "wiki": "https://www.nexusmods.com/skyrimspecialedition/wiki/",
    },
    "fallout4": {
        "nexus_slug": "fallout4",
        "xedit": "FO4Edit",
        "xedit_url": "https://www.nexusmods.com/fallout4/mods/27373",
        "skse_url": "https://f4se.silverlock.org/",
        "loot_repo": "loot/fallout4",
        "reddit": ["r/fo4", "r/FalloutMods"],
        "wiki": "https://www.nexusmods.com/fallout4/wiki/",
    },
    "falloutnv": {
        "nexus_slug": "newvegas",
        "xedit": "FNVEdit",
        "xedit_url": "https://www.nexusmods.com/newvegas/mods/34703",
        "skse_url": None,
        "loot_repo": "loot/falloutnv",
        "reddit": ["r/fnv", "r/FalloutMods"],
        "wiki": "https://www.nexusmods.com/newvegas/wiki/",
    },
    "fallout3": {
        "nexus_slug": "fallout3",
        "xedit": "FO3Edit",
        "xedit_url": "https://www.nexusmods.com/fallout3/mods/637",
        "skse_url": None,
        "loot_repo": "loot/fallout3",
        "reddit": ["r/fo3", "r/FalloutMods"],
        "wiki": "https://www.nexusmods.com/fallout3/wiki/",
    },
    "oblivion": {
        "nexus_slug": "oblivion",
        "xedit": "TES4Edit",
        "xedit_url": "https://www.nexusmods.com/oblivion/mods/11536",
        "skse_url": None,
        "loot_repo": "loot/oblivion",
        "reddit": ["r/oblivion"],
        "wiki": "https://www.nexusmods.com/oblivion/wiki/",
    },
    "starfield": {
        "nexus_slug": "starfield",
        "xedit": "xEdit",
        "xedit_url": "https://tes5edit.github.io/",
        "skse_url": None,
        "loot_repo": "loot/starfield",
        "reddit": ["r/starfield", "r/starfieldmods"],
        "wiki": "https://www.nexusmods.com/starfield/wiki/",
    },
}


def get_resolution_for_conflict(conflict_type: str) -> Dict[str, Any]:
    """Get resolution pattern for a conflict type. For AI context."""
    return CONFLICT_RESOLUTIONS.get(conflict_type, CONFLICT_RESOLUTIONS.get("info", {}))


def get_esoteric_solutions(query: str) -> List[Dict[str, Any]]:
    """
    Find esoteric solutions matching user query (CTD, ILS, etc.).
    Returns list of {issue, causes, solutions, keywords}.
    """
    if not query or len(query.strip()) < 2:
        return []
    q = query.lower().strip()
    results = []
    for sol in ESOTERIC_SOLUTIONS:
        score = 0
        for kw in sol["keywords"]:
            if kw in q or q in kw:
                score += 1
        if score > 0:
            results.append({**sol, "relevance": score})
    results.sort(key=lambda x: (-x["relevance"], x["issue"]))
    return results[:5]


def get_game_resources(game_id: str) -> Dict[str, Any]:
    """Get game-specific resource links for AI context."""
    return GAME_RESOURCES.get(game_id.lower(), GAME_RESOURCES.get("skyrimse", {}))


def _conflict_type(c: Any) -> str:
    """Extract conflict type from object or dict."""
    if hasattr(c, "type"):
        return getattr(c, "type", "info")
    if isinstance(c, dict):
        return c.get("type", "info")
    return "info"


def format_knowledge_for_ai(ctx: Dict[str, Any]) -> str:
    """Format knowledge context as compact text for AI token budget."""
    if not ctx:
        return ""
    lines = ["", "---", "Resolution guide (conflict type → actions):"]
    for ct, res in (ctx.get("resolutions") or {}).items():
        actions = res.get("actions", [])[:3]
        if actions:
            lines.append(f"  [{ct}]: {'; '.join(actions)}")
    esoteric = ctx.get("esoteric_solutions") or []
    if esoteric:
        lines.append("")
        lines.append("Common issues & solutions:")
        for s in esoteric[:3]:
            lines.append(f"  {s.get('issue', '')}: {'; '.join((s.get('solutions') or [])[:2])}")
    resources = ctx.get("game_resources") or {}
    if resources:
        lines.append("")
        lines.append(
            f"Resources: xEdit={resources.get('xedit', '')}, Nexus={resources.get('nexus_slug', '')}"
        )
    return "\n".join(lines)


def build_ai_context(
    game_id: str,
    conflicts: List[Any],
    mod_list: List[str],
    specs: Optional[Dict] = None,
    user_query: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Build structured context for AI assistant.
    Includes: game resources, conflict resolutions, esoteric solutions, mod count.
    """
    conflict_types = list(set(_conflict_type(c) for c in conflicts))
    resolutions = {}
    for ct in conflict_types:
        resolutions[ct] = get_resolution_for_conflict(ct)

    esoteric = []
    if user_query:
        esoteric = get_esoteric_solutions(user_query)
    # Also add based on conflict types
    for c in conflicts:
        ct = getattr(c, "type", "")
        if ct in ("missing_requirement", "incompatible"):
            for sol in get_esoteric_solutions("ctd crash"):
                if sol not in esoteric:
                    esoteric.append(sol)
            break

    return {
        "game": game_id,
        "game_resources": get_game_resources(game_id),
        "mod_count": len(mod_list),
        "conflict_count": len(conflicts),
        "conflict_types": conflict_types,
        "resolutions": resolutions,
        "esoteric_solutions": esoteric[:5],
        "specs": specs or {},
    }
