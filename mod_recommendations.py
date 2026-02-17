"""
Mod Recommendations — Suggest mods based on user's current list.
Used for: live strip as you type, AI chat previews.
Pro AI: categorized top picks (Utility, Design, Fun, Environmental).
"""

import logging
import re
from collections import defaultdict
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Placeholder for mods without images (simple 16:9 mod icon)
MOD_PLACEHOLDER = "/static/icons/mod-placeholder.svg"

# Category taxonomy for top picks — (pattern, category)
_CATEGORY_PATTERNS = [
    # Utility: patches, fixes, stability, QoL, UI, tools
    (r"\b(patch|fix|unofficial|bug\s*fix|stability)\b", "utility"),
    (r"\b(skyui|mcm|mod\s*config|configuration)\b", "utility"),
    (r"\b(skse|address\s*library|engine\s*fix)\b", "utility"),
    (r"\b(loot|load\s*order|xedit|sseedit)\b", "utility"),
    (r"\b(cutting\s*room|crf|ussep|usleep|ufo4p|yup)\b", "utility"),
    # Design: visual — textures, meshes, body, lighting, appearance
    (r"\b(texture|parallax|4k|8k|2k|hd|high\s*res)\b", "design"),
    (r"\b(smim|static\s*mesh|mesh\s*improvement)\b", "design"),
    (r"\b(cbbe|unp|body|bodyslide|skeleton|xpmse)\b", "design"),
    (r"\b(enb|lighting|weather|obsidian|cathedral|rustic)\b", "design"),
    (r"\b(face|appearance|bijin|pandorable)\b", "design"),
    (r"\b(animation|nemesis|fnis|dar|oar)\b", "design"),
    # Fun: gameplay — perks, combat, spells, mechanics, new content
    (r"\b(ordinator|perks|skill|combat)\b", "fun"),
    (r"\b(spell|magic|enchant)\b", "fun"),
    (r"\b(quest|new\s*content|adventure)\b", "fun"),
    (r"\b(requiem|survival|difficulty)\b", "fun"),
    (r"\b(immersive\s*creatures|enemy)\b", "fun"),
    # Environmental: world, immersion — weather, flora, cities, NPCs, AI
    (r"\b(weather|flora|grass|landscape|terrain)\b", "environmental"),
    (r"\b(dyndolod|lod|distant)\b", "environmental"),
    (r"\b(immersive\s*citizens|ai\s*overhaul|npc)\b", "environmental"),
    (r"\b(open\s*cities|jk|city|town)\b", "environmental"),
    (r"\b(legacy\s*of\s*the\s*dragonborn|lotd)\b", "environmental"),
    (r"\b(beyond\s*skyrim|bruma)\b", "environmental"),
    (r"\b(water|rwt|realistic\s*water)\b", "environmental"),
]

# Curated top picks per game — (game_id, category) -> search terms for fallback
_CURATED_TOP_PICKS = {
    "skyrimse": {
        "utility": ["unofficial patch", "skyui", "cutting room floor", "engine fixes"],
        "design": ["smim", "noble skyrim", "cbbe", "cathedral weathers"],
        "fun": ["ordinator", "alternate start", "relationship dialogue", "immersive creatures"],
        "environmental": ["dyndolod", "obsidian weathers", "immersive citizens", "open cities"],
    },
    "skyrim": {
        "utility": ["unofficial patch", "skyui", "cutting room floor"],
        "design": ["smim", "noble skyrim", "cbbe"],
        "fun": ["ordinator", "alternate start", "immersive creatures"],
        "environmental": ["dyndolod", "immersive citizens"],
    },
    "skyrimvr": {
        "utility": ["unofficial patch", "skyui", "vrik", "spell wheel"],
        "design": ["smim", "vrik", "cbbe"],
        "fun": ["vrik", "spell wheel", "alternate start"],
        "environmental": ["dyndolod", "obsidian weathers"],
    },
    "fallout4": {
        "utility": ["unofficial patch", "armor keywords", "sim settlements"],
        "design": ["cvc", "enhanced lights", "body"],
        "fun": ["sim settlements", "start me up", "weapon"],
        "environmental": ["true storms", "vivid weathers", "better settlers"],
    },
    "falloutnv": {
        "utility": ["yup", "nvac", "mod configuration"],
        "design": ["nvr", "character"],
        "fun": ["jsawyer", "weapon mods", "project nevada"],
        "environmental": ["nvr", "weather", "settlements"],
    },
    "starfield": {
        "utility": ["community patch", "starfield script"],
        "design": ["texture", "character"],
        "fun": ["grav jump", "ship"],
        "environmental": ["weather", "planet"],
    },
}


def _classify_category(name: str, tags: Optional[List[str]] = None) -> Optional[str]:
    """Classify mod into utility, design, fun, or environmental. Returns first match."""
    text = (name or "").lower()
    if tags:
        text += " " + " ".join((t or "").lower() for t in tags)
    for pattern, cat in _CATEGORY_PATTERNS:
        if re.search(pattern, text):
            return cat
    return None


def get_recommendations(
    parser,
    mod_names: List[str],
    game: str,
    nexus_slug: str,
    limit: int = 8,
    exclude: Optional[set] = None,
    include_category: bool = False,
) -> List[Dict[str, Any]]:
    """
    Get mod recommendations based on current list.
    Sources: patches, load_after, requirements, popular (authority).
    Returns list of {name, reason, nexus_url, image_url, category?}.
    """
    exclude = exclude or set()
    mod_names_clean = {_norm(n) for n in mod_names if n and _norm(n) not in exclude}
    if not mod_names_clean:
        return _fallback_popular(parser, game, nexus_slug, limit)

    seen = set(mod_names_clean)
    out: List[tuple] = []  # (name, reason, score) for sorting

    for clean in mod_names_clean:
        info = parser.mod_database.get(clean)
        if not info:
            continue
        # Patches: user has A and B, suggest patch
        for p in info.patches or []:
            if isinstance(p, dict):
                for other, patch_name in p.items():
                    patch_clean = _norm(patch_name)
                    if patch_clean not in seen:
                        patch_info = parser.mod_database.get(patch_clean)
                        disp = patch_info.name if patch_info else patch_name
                        out.append((disp, "Compatibility patch", 3))
                        seen.add(patch_clean)
        # Requirements: user might need these
        for req in (info.requirements or [])[:2]:
            req_clean = _norm(req)
            if req_clean not in seen:
                req_info = parser.mod_database.get(req_clean)
                name = req_info.name if req_info else req
                out.append((name, "Required by your mods", 4))
                seen.add(req_clean)
        # Load after: mods that pair well
        for after in (info.load_after or [])[:2]:
            after_clean = _norm(after)
            if after_clean not in seen:
                after_info = parser.mod_database.get(after_clean)
                name = after_info.name if after_info else after
                out.append((name, "Pairs well with your load order", 2))
                seen.add(after_clean)

    # Dedupe by name, keep highest score
    by_name: Dict[str, tuple] = {}
    for name, reason, score in out:
        key = _norm(name)
        if key not in by_name or by_name[key][2] < score:
            by_name[key] = (name, reason, score)

    sorted_out = sorted(by_name.values(), key=lambda x: (-x[2], x[0].lower()))[:limit]
    if len(sorted_out) < limit:
        extra = _fallback_popular(parser, game, nexus_slug, limit - len(sorted_out))
        for r in extra:
            rn = _norm(r["name"])
            if rn not in seen:
                seen.add(rn)
                sorted_out.append((r["name"], r.get("reason", "Popular"), 1))

    nexus_base = f"https://www.nexusmods.com/games/{nexus_slug}/mods?keyword="
    result = []
    for name, reason, _ in sorted_out[:limit]:
        if not _is_plugin(name):
            continue
        info = parser.mod_database.get(_norm(name)) if hasattr(parser, "mod_database") else None
        tags = getattr(info, "tags", None) if info else None
        picture_url = getattr(info, "picture_url", None) if info else None
        entry = {
            "name": name,
            "reason": reason,
            "nexus_url": nexus_base + _url_enc(name),
            "image_url": picture_url or MOD_PLACEHOLDER,
        }
        if include_category:
            entry["category"] = _classify_category(name, tags)
        result.append(entry)
    return result


def get_recommendations_for_ai(
    parser,
    mod_names: List[str],
    game: str,
    nexus_slug: str,
    limit: int = 12,
    top_picks_per_category: int = 2,
) -> Dict[str, Any]:
    """
    Pro AI: Full recommendation payload with categorized top picks.
    Returns { recommendations, top_picks: { utility, design, fun, environmental } }.
    """
    recs = get_recommendations(
        parser, mod_names, game, nexus_slug, limit=limit, include_category=True
    )
    # Bucket by category
    by_cat: Dict[str, List[Dict]] = defaultdict(list)
    for r in recs:
        cat = r.get("category") or "utility"  # default uncategorized to utility
        by_cat[cat].append(r)
    # Build top_picks: best 1–2 per category
    top_picks = {}
    for cat in ("utility", "design", "fun", "environmental"):
        picks = by_cat.get(cat, [])[:top_picks_per_category]
        if not picks:
            picks = _curated_fallback(parser, game, nexus_slug, cat, top_picks_per_category)
        top_picks[cat] = picks
    return {
        "recommendations": recs,
        "top_picks": top_picks,
    }


def _curated_fallback(
    parser, game: str, nexus_slug: str, category: str, limit: int
) -> List[Dict[str, Any]]:
    """Fill top_picks with curated search results when we have no matches in that category."""
    from search_engine import get_search_engine

    terms = _CURATED_TOP_PICKS.get(game, _CURATED_TOP_PICKS.get("skyrimse", {})).get(
        category, ["patch"]
    )
    engine = get_search_engine(parser)
    seen = set()
    out = []
    nexus_base = f"https://www.nexusmods.com/games/{nexus_slug}/mods?keyword="
    for term in terms:
        for r in engine.search(term, limit=2):
            name = r.mod_name
            if not _is_plugin(name):
                continue
            key = _norm(name)
            if key in seen:
                continue
            seen.add(key)
            out.append(
                {
                    "name": name,
                    "reason": f"Top {category} pick",
                    "nexus_url": nexus_base + _url_enc(name),
                    "image_url": r.picture_url or MOD_PLACEHOLDER,
                    "category": category,
                }
            )
            if len(out) >= limit:
                return out
    return out


def _norm(s: str) -> str:
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
    """Only recommend actual plugins (.esp/.esm/.esl), not DLLs or other files."""
    n = (name or "").lower()
    return n.endswith((".esp", ".esm", ".esl"))


def _url_enc(s: str) -> str:
    from urllib.parse import quote

    return quote(s)


def _fallback_popular(parser, game: str, nexus_slug: str, limit: int) -> List[Dict[str, Any]]:
    """Fallback: high-authority mods (referenced by many others)."""
    from search_engine import get_search_engine

    engine = get_search_engine(parser)
    # Get mods with high authority - we don't have direct access, so use search for common terms
    game_hints = {
        "skyrimse": ["skyui", "ussep", "alternate start", "ordinator", "cutting room"],
        "skyrim": ["skyui", "usleep", "alternate start"],
        "fallout4": ["sim settlements", "armor keywords", "unofficial patch"],
        "starfield": ["community patch", "dramatic grav"],
    }
    terms = game_hints.get(game, ["skyui", "patch"])
    seen = set()
    out = []
    for term in terms:
        results = engine.search(term, limit=3)
        for r in results:
            name = r.mod_name
            key = _norm(name)
            if key not in seen and _is_plugin(name):
                seen.add(key)
                nexus_base = f"https://www.nexusmods.com/games/{nexus_slug}/mods?keyword="
                out.append(
                    {
                        "name": name,
                        "reason": "Popular for this game",
                        "nexus_url": nexus_base + _url_enc(name),
                        "image_url": r.picture_url or MOD_PLACEHOLDER,
                    }
                )
                if len(out) >= limit:
                    return out
    return out
