"""
Mod Warnings — Dynamic warnings for the recommendations area.
Plugin limit, system strain, with links to fix guides.
"""

import logging
from typing import Any, Dict, List, Optional

from constants import PLUGIN_LIMIT, PLUGIN_LIMIT_WARN_THRESHOLD

logger = logging.getLogger(__name__)

PLUGIN_LIMIT_WARN = PLUGIN_LIMIT_WARN_THRESHOLD

# Fix guides — cap and performance
_FIX_LINKS = {
    "plugin_limit": {
        "title": "How to fix",
        "url": "https://tes5edit.github.io/docs/5-mod-conversion-to-esl.html",
        "description": "ESLify plugins or merge mods to stay under 255",
    },
    "eslify_guide": {
        "title": "ESLify guide",
        "url": "https://www.nexusmods.com/skyrimspecialedition/mods/68570",
        "description": "SSE Engine Fixes / ESLify",
    },
    "merge_guide": {
        "title": "Merge plugins",
        "url": "https://tes5edit.github.io/docs/4-mod-merging.html",
        "description": "xEdit merge guide",
    },
    "performance": {
        "title": "Optimize performance",
        "url": "https://www.youtube.com/results?search_query=skyrim+mod+performance+optimization",
        "description": "Performance tuning guides",
    },
    "vram_optimization": {
        "title": "Reduce VRAM usage",
        "url": "https://www.nexusmods.com/skyrimspecialedition/articles/3684",
        "description": "Texture resolution, ENB presets",
    },
}


def get_mod_warnings(
    mod_list_text: Optional[str] = None,
    mod_list: Optional[List[str]] = None,
    game: str = "skyrimse",
    specs: Optional[Dict] = None,
) -> List[Dict[str, Any]]:
    """
    Build dynamic warnings from mod list, game, and specs.
    Returns list of {severity, message, link_title, link_url, link_extra?}.
    Uses mod_list_text when available (accurate enabled count); else mod_list (assume all enabled).
    """
    from conflict_detector import parse_mod_list_text
    from system_impact import get_system_impact

    warnings = []
    if mod_list_text and mod_list_text.strip():
        mods = parse_mod_list_text(mod_list_text)
        enabled_count = sum(1 for m in mods if m.enabled)
        mod_names = [m.name for m in mods if m.enabled]
    else:
        mod_list = mod_list or []
        enabled_count = len(mod_list)
        mod_names = list(mod_list)

    if enabled_count == 0:
        return warnings

    # Plugin limit (Skyrim, FO4, Starfield — Bethesda engine)
    if game in ("skyrimse", "skyrim", "skyrimvr", "fallout4", "starfield"):
        if enabled_count >= PLUGIN_LIMIT:
            warnings.append(
                {
                    "severity": "error",
                    "message": f"You have {enabled_count} enabled plugins. The engine cap is {PLUGIN_LIMIT} — the game may not load.",
                    "link_title": _FIX_LINKS["plugin_limit"]["title"],
                    "link_url": _FIX_LINKS["plugin_limit"]["url"],
                    "link_extra": _FIX_LINKS["eslify_guide"],
                }
            )
        elif enabled_count >= PLUGIN_LIMIT_WARN:
            warnings.append(
                {
                    "severity": "warning",
                    "message": f"Approaching the {PLUGIN_LIMIT} plugin limit ({enabled_count} enabled). ESLs don't count — consider ESLifying or merging.",
                    "link_title": _FIX_LINKS["plugin_limit"]["title"],
                    "link_url": _FIX_LINKS["plugin_limit"]["url"],
                    "link_extra": _FIX_LINKS["merge_guide"],
                }
            )

    # System strain — use system_impact
    si = get_system_impact(mod_names=mod_names, enabled_count=enabled_count, specs=specs)
    estimated_vram = si.get("estimated_vram_gb", 0)
    complexity = si.get("complexity", "low")
    has_specs = si.get("has_specs", False)

    if has_specs and si.get("recommendation"):
        rec = si["recommendation"]
        if "Consider reducing" in rec or "avoid stuttering" in rec:
            warnings.append(
                {
                    "severity": "warning",
                    "message": rec,
                    "link_title": _FIX_LINKS["vram_optimization"]["title"],
                    "link_url": _FIX_LINKS["vram_optimization"]["url"],
                }
            )
        elif "close to your" in rec or "Consider a performance" in rec:
            warnings.append(
                {
                    "severity": "info",
                    "message": rec,
                    "link_title": _FIX_LINKS["vram_optimization"]["title"],
                    "link_url": _FIX_LINKS["vram_optimization"]["url"],
                }
            )
    else:
        # No specs — generic strain warning based on count/complexity
        if enabled_count >= 150 or complexity == "high":
            warnings.append(
                {
                    "severity": "info",
                    "message": f"With {enabled_count} mods and {si.get('complexity_label', 'high')} complexity, you may strain mid-range systems. Add your specs for personalized warnings.",
                    "link_title": _FIX_LINKS["performance"]["title"],
                    "link_url": _FIX_LINKS["performance"]["url"],
                }
            )
        elif enabled_count >= 100 and complexity in ("medium", "high"):
            warnings.append(
                {
                    "severity": "info",
                    "message": f"~{estimated_vram:.0f}GB VRAM estimated. Add your GPU/VRAM in specs for tailored advice.",
                    "link_title": _FIX_LINKS["performance"]["title"],
                    "link_url": _FIX_LINKS["performance"]["url"],
                }
            )

    return warnings
