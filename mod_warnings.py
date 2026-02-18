"""
Mod Warnings — Dynamic warnings for the recommendations area.
Plugin limit, system strain, with links to fix guides.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, TypedDict

from constants import ESL_LIMIT, PLUGIN_LIMIT, PLUGIN_LIMIT_WARN_THRESHOLD

logger = logging.getLogger(__name__)

PLUGIN_LIMIT_WARN = PLUGIN_LIMIT_WARN_THRESHOLD


# =============================================================================
# Type Definitions
# =============================================================================


class WarningLink(TypedDict, total=False):
    """Link structure for warnings."""

    title: str
    url: str
    description: str


class ModWarning(TypedDict):
    """Warning structure returned by get_mod_warnings."""

    severity: str  # error, warning, info
    message: str
    link_title: str
    link_url: str
    link_extra: Optional[WarningLink]


# =============================================================================
# Fix Guide Links
# =============================================================================

_FIX_LINKS: Dict[str, WarningLink] = {
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
    "script_heavy": {
        "title": "Script optimization",
        "url": "https://www.nexusmods.com/skyrimspecialedition/articles/1302",
        "description": "Reduce script-heavy mods",
    },
}


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class WarningConfig:
    """Configuration for warning thresholds."""

    plugin_limit: int = PLUGIN_LIMIT
    plugin_warn_threshold: int = PLUGIN_LIMIT_WARN_THRESHOLD
    esl_limit: int = ESL_LIMIT
    high_mod_count: int = 150
    moderate_mod_count: int = 100


# =============================================================================
# Main Warning Generation
# =============================================================================


def get_mod_warnings(
    mod_list_text: Optional[str] = None,
    mod_list: Optional[List[str]] = None,
    game: str = "skyrimse",
    specs: Optional[Dict[str, Any]] = None,
    config: Optional[WarningConfig] = None,
) -> List[ModWarning]:
    """
    Build dynamic warnings from mod list, game, and specs.

    Args:
        mod_list_text: Raw mod list text (preferred - preserves enabled/disabled state)
        mod_list: List of mod names (fallback if text not provided)
        game: Game identifier (e.g., 'skyrimse')
        specs: User's system specifications
        config: Optional warning configuration

    Returns:
        List of warning dictionaries with severity, message, and links
    """
    from conflict_detector import parse_mod_list_text
    from system_impact import get_system_impact

    config = config or WarningConfig()
    warnings: List[ModWarning] = []

    # Parse mod list
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

    # Game-specific warnings
    if game in ("skyrimse", "skyrim", "skyrimvr", "fallout4", "starfield"):
        warnings.extend(
            _check_plugin_limit(enabled_count, config)
        )

    # System strain warnings
    warnings.extend(
        _check_system_strain(mod_names, enabled_count, specs, game, config)
    )

    # Script-heavy mod warnings
    warnings.extend(
        _check_script_heavy_mods(mod_names)
    )

    return warnings


# =============================================================================
# Warning Checkers
# =============================================================================


def _check_plugin_limit(
    enabled_count: int,
    config: WarningConfig,
) -> List[ModWarning]:
    """Check for plugin limit violations."""
    warnings: List[ModWarning] = []

    if enabled_count >= config.plugin_limit:
        warnings.append(
            ModWarning(
                severity="error",
                message=f"You have {enabled_count} enabled plugins. The engine cap is {config.plugin_limit} — the game may not load.",
                link_title=_FIX_LINKS["plugin_limit"]["title"],
                link_url=_FIX_LINKS["plugin_limit"]["url"],
                link_extra=_FIX_LINKS["eslify_guide"],
            )
        )
    elif enabled_count >= config.plugin_warn_threshold:
        warnings.append(
            ModWarning(
                severity="warning",
                message=f"Approaching the {config.plugin_limit} plugin limit ({enabled_count} enabled). ESLs don't count — consider ESLifying or merging.",
                link_title=_FIX_LINKS["plugin_limit"]["title"],
                link_url=_FIX_LINKS["plugin_limit"]["url"],
                link_extra=_FIX_LINKS["merge_guide"],
            )
        )

    return warnings


def _check_system_strain(
    mod_names: List[str],
    enabled_count: int,
    specs: Optional[Dict[str, Any]],
    game: str,
    config: WarningConfig,
) -> List[ModWarning]:
    """Check for system strain based on mods and specs."""
    warnings: List[ModWarning] = []
    from system_impact import get_system_impact

    si = get_system_impact(mod_names=mod_names, enabled_count=enabled_count, specs=specs)
    estimated_vram = si.get("estimated_vram_gb", 0)
    complexity = si.get("complexity", "low")
    has_specs = si.get("has_specs", False)
    recommendation = si.get("recommendation", "")

    if has_specs and recommendation:
        if "Consider reducing" in recommendation or "avoid stuttering" in recommendation:
            warnings.append(
                ModWarning(
                    severity="warning",
                    message=recommendation,
                    link_title=_FIX_LINKS["vram_optimization"]["title"],
                    link_url=_FIX_LINKS["vram_optimization"]["url"],
                )
            )
        elif "close to your" in recommendation or "Consider a performance" in recommendation:
            warnings.append(
                ModWarning(
                    severity="info",
                    message=recommendation,
                    link_title=_FIX_LINKS["vram_optimization"]["title"],
                    link_url=_FIX_LINKS["vram_optimization"]["url"],
                )
            )
    else:
        # No specs — generic strain warning
        if enabled_count >= config.high_mod_count or complexity == "high":
            warnings.append(
                ModWarning(
                    severity="info",
                    message=f"With {enabled_count} mods and {si.get('complexity_label', 'high')} complexity, you may strain mid-range systems. Add your specs for personalized warnings.",
                    link_title=_FIX_LINKS["performance"]["title"],
                    link_url=_FIX_LINKS["performance"]["url"],
                )
            )
        elif enabled_count >= config.moderate_mod_count and complexity in ("medium", "high"):
            warnings.append(
                ModWarning(
                    severity="info",
                    message=f"~{estimated_vram:.0f}GB VRAM estimated. Add your GPU/VRAM in specs for tailored advice.",
                    link_title=_FIX_LINKS["performance"]["title"],
                    link_url=_FIX_LINKS["performance"]["url"],
                )
            )

    return warnings


def _check_script_heavy_mods(mod_names: List[str]) -> List[ModWarning]:
    """Check for script-heavy mods that may cause issues."""
    warnings: List[ModWarning] = []

    # Known script-heavy mods
    script_heavy_patterns = [
        "ordinator",
        "skyrim unlimited",
        "spells",
        "combat",
        "ai overhaul",
        "settlement",
        "sim settlements",
    ]

    heavy_count = sum(
        1 for mod in mod_names
        if any(pattern in mod.lower() for pattern in script_heavy_patterns)
    )

    if heavy_count >= 5:
        warnings.append(
            ModWarning(
                severity="info",
                message=f"You have {heavy_count} script-heavy mods. This may cause script lag or save bloat over time.",
                link_title=_FIX_LINKS["script_heavy"]["title"],
                link_url=_FIX_LINKS["script_heavy"]["url"],
            )
        )

    return warnings


# =============================================================================
# Utility Functions
# =============================================================================


def get_warning_summary(warnings: List[ModWarning]) -> Dict[str, int]:
    """
    Get a summary count of warnings by severity.

    Args:
        warnings: List of warnings

    Returns:
        Dictionary with counts per severity level
    """
    summary = {"error": 0, "warning": 0, "info": 0}
    for w in warnings:
        severity = w.get("severity", "info")
        if severity in summary:
            summary[severity] += 1
    return summary


def has_critical_warnings(warnings: List[ModWarning]) -> bool:
    """
    Check if there are any critical (error-level) warnings.

    Args:
        warnings: List of warnings

    Returns:
        True if any error-level warnings exist
    """
    return any(w.get("severity") == "error" for w in warnings)
