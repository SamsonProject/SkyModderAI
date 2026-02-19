"""
LOOT-Based Mod Suggestions — Only LOOT-sourced missing requirements and companion mods.
No affiliate recommendations, no "popular" mods, no marketing suggestions.
No hardcoded curation — all suggestions come from actual LOOT data and community builds.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# NOTE: No hardcoded mod recommendations here.
# All mod suggestions now come from:
# 1. LOOT data (requirements, load_after rules)
# 2. Community builds (user-submitted, voted)
# 3. User's own mod list analysis
#
# See community_builds.py for the community-driven build database.
# See /api/community-builds for browsing and submitting builds.


def get_loot_based_suggestions(
    parser,
    mod_names: List[str],
    limit: int = 8,
) -> List[Dict[str, Any]]:
    """
    Get LOOT-sourced suggestions based on user's current mod list.
    
    Only returns:
    - Missing mods that LOOT data says are REQUIRED by mods already installed
    - Common companion mods that LOOT explicitly marks as recommended (load_after)
    
    No affiliate recommendations, no "popular" mods, no marketing suggestions.
    
    Returns list of {name, reason, nexus_url, image_url}.
    """
    if not mod_names:
        return []
    
    mod_names_clean = {_norm(n) for n in mod_names if n}
    if not mod_names_clean:
        return []
    
    seen = set(mod_names_clean)
    out: List[tuple] = []  # (name, reason, score) for sorting
    
    # First pass: collect requirements (highest priority - these are MISSING)
    for clean in mod_names_clean:
        info = parser.mod_database.get(clean)
        if not info:
            continue
        
        # Requirements: mods that are REQUIRED by user's installed mods
        for req in info.requirements or []:
            req_clean = _norm(req)
            if req_clean not in seen:
                req_info = parser.mod_database.get(req_clean)
                name = req_info.name if req_info else req
                out.append((name, "Required by your mods", 10, req_info))
                seen.add(req_clean)
    
    # Second pass: collect load_after recommendations (companion mods)
    for clean in mod_names_clean:
        info = parser.mod_database.get(clean)
        if not info:
            continue
        
        # Load after: mods that LOOT explicitly recommends loading together
        for after in info.load_after or []:
            after_clean = _norm(after)
            if after_clean not in seen:
                after_info = parser.mod_database.get(after_clean)
                name = after_info.name if after_info else after
                out.append((name, "Recommended companion mod", 5, after_info))
                seen.add(after_clean)
    
    # Dedupe by name, keep highest score
    by_name: Dict[str, tuple] = {}
    for name, reason, score, info in out:
        key = _norm(name)
        if key not in by_name or by_name[key][2] < score:
            by_name[key] = (name, reason, score, info)
    
    # Sort: requirements first (higher score), then alphabetically
    sorted_out = sorted(by_name.values(), key=lambda x: (-x[2], x[0].lower()))[:limit]
    
    # Build result
    result = []
    for name, reason, _, info in sorted_out:
        if not _is_plugin(name):
            continue
        tags = getattr(info, "tags", None) if info else None
        picture_url = getattr(info, "picture_url", None) if info else None
        nexus_slug = _get_nexus_slug(parser)
        entry = {
            "name": name,
            "reason": reason,
            "nexus_url": f"https://www.nexusmods.com/games/{nexus_slug}/mods?keyword={_url_enc(name)}",
            "image_url": picture_url or "/static/icons/mod-placeholder.svg",
        }
        result.append(entry)
    
    return result


def _norm(s: str) -> str:
    """Normalize mod name for comparison."""
    return (
        (s or "")
        .lower()
        .strip()
        .replace(".esp", "")
        .replace(".esm", "")
        .replace(".esl", "")
        .strip()
    )


def _is_plugin(name: str) -> bool:
    """Only suggest actual plugins (.esp/.esm/.esl), not DLLs or other files."""
    n = (name or "").lower()
    return n.endswith((".esp", ".esm", ".esl"))


def _url_enc(s: str) -> str:
    """URL encode a string for Nexus Mods search."""
    from urllib.parse import quote
    return quote(s)


def _get_nexus_slug(parser) -> str:
    """Get the Nexus Mods game slug from the parser."""
    game = getattr(parser, "game", "skyrimse")
    game_to_slug = {
        "skyrimse": "skyrimse",
        "skyrim": "skyrim",
        "skyrimvr": "skyrimse",
        "oblivion": "oblivion",
        "fallout3": "fallout3",
        "falloutnv": "falloutnv",
        "fallout4": "fallout4",
        "starfield": "starfield",
    }
    return game_to_slug.get(game, "skyrimse")
