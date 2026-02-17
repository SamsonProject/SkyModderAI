"""
System Impact Analysis
Estimates performance impact of a mod list. Free for all tiers.

Engine flow:
  1. get_system_impact() — prediction: complexity, heavy_mods, estimated_vram_gb, recommendation
  2. format_system_impact_report() — human-readable plain text for copy/download reports
  3. format_system_impact_for_ai() — concise token-efficient block for AI agent context
"""

import re
from dataclasses import dataclass
from typing import Dict, List, Optional

# Mod name patterns that typically impact performance (case-insensitive)
_HEAVY_PATTERNS = [
    (r'\b(enb|enbseries)\b', 'ENB / post-processing', 'high'),
    (r'\b(4k|8k|2k)\b', 'High-res textures', 'medium'),
    (r'\b(high\s*poly|highpoly)\b', 'High-poly meshes', 'medium'),
    (r'\b(dyndolod|dyndolod)\b', 'DynDOLOD (LOD generation)', 'high'),
    (r"\bjk'?s?\b", 'City/town overhaul', 'medium'),
    (r'\b(flora\s*overhaul|sfo|skyrim\s*flora)\b', 'Flora overhaul', 'medium'),
    (r'\b(grass\s*mod|grass\s*overhaul)\b', 'Grass mod', 'medium'),
    (r'\b(smim|static\s*mesh)\b', 'SMIM / mesh improvement', 'low'),
    (r'\b(weather\s*mod|obsidian|cathedral)\b', 'Weather/lighting', 'medium'),
    (r'\b(immersive\s*citizens|ai\s*overhaul)\b', 'AI overhaul', 'medium'),
    (r'\b(open\s*cities)\b', 'Open Cities', 'high'),
    (r'\b(legacy\s*of\s*the\s*dragonborn)\b', 'Legacy of the Dragonborn', 'high'),
    (r'\b(beyond\s*skyrim|bruma)\b', 'Beyond Skyrim', 'high'),
    (r'\b(parallax)\b', 'Parallax textures', 'medium'),
    (r'\b(water\s*mod|realistic\s*water)\b', 'Water mod', 'low'),
    (r'\b(body\s*mod|cbbe|unp|hdt)\b', 'Body/skeleton mod', 'low'),
    (r'\b(animation\s*mod|nemesis|fnis)\b', 'Animation framework', 'medium'),
]


@dataclass
class HeavyMod:
    """A mod that may impact performance."""
    name: str
    category: str
    impact: str  # low, medium, high


# Game-specific VRAM multipliers (base multiplier for VRAM estimation)
_GAME_VRAM_MULTIPLIERS = {
    'skyrimse': 1.0,      # Base (Skyrim Special Edition)
    'skyrimle': 0.8,      # Slightly lower VRAM usage than SSE
    'skyrimvr': 1.5,      # VR requires more VRAM
    'fallout4': 1.2,      # More complex assets than Skyrim
    'fallout4vr': 1.7,    # VR + Fallout 4 = high VRAM needs
    'fallout3': 0.7,      # Older game, lower VRAM requirements
    'falloutnv': 0.7,     # Similar to Fallout 3
    'oblivion': 0.6,      # Much older game
    'starfield': 2.0,     # Newer game, much higher VRAM requirements
    'enderal': 1.1,       # Enderal (Skyrim total conversion)
    'enderal-se': 1.2,    # Enderal Special Edition
}

def get_system_impact(
    mod_names: List[str],
    enabled_count: int,
    specs: Optional[Dict] = None,
    game: Optional[str] = None,
) -> Dict:
    """
    Analyze mod list for system/performance impact.

    Args:
        mod_names: List of mod names to analyze
        enabled_count: Number of enabled mods/plugins
        specs: Optional dict with system specs (vram_gb, cpu, gpu, etc.)
        game: Game ID (e.g., 'skyrimse', 'fallout4') for game-specific adjustments

    Returns:
        Dict with complexity, heavy_mods, estimated_vram_gb, recommendation
    """
    specs = specs or {}
    game = (game or '').lower()
    heavy_mods: List[Dict] = []

    for name in mod_names:
        name_lower = name.lower()
        for pattern, category, impact in _HEAVY_PATTERNS:
            if re.search(pattern, name_lower):
                heavy_mods.append({
                    'name': name,
                    'category': category,
                    'impact': impact,
                })
                break

    # Sort by impact (high > medium > low) for ranking display
    impact_order = {'high': 3, 'medium': 2, 'low': 1}
    heavy_mods.sort(key=lambda m: (-impact_order.get(m['impact'], 0), m['name'].lower()))

    # Base VRAM estimate: game + mods
    base_vram = 2.0
    per_mod = 0.02
    heavy_bonus = sum(0.5 if m['impact'] == 'high' else 0.2 if m['impact'] == 'medium' else 0.05 for m in heavy_mods)

    # Apply game-specific multiplier
    game_multiplier = _GAME_VRAM_MULTIPLIERS.get(game, 1.0)
    estimated_vram = (base_vram + (enabled_count * per_mod) + heavy_bonus) * game_multiplier

    # Cap at 24GB (realistic max for consumer GPUs)
    estimated_vram = min(24.0, round(estimated_vram, 1))

    # Complexity: low / medium / high
    heavy_count = len(heavy_mods)
    high_impact = sum(1 for m in heavy_mods if m['impact'] == 'high')
    if enabled_count >= 200 or high_impact >= 3:
        complexity = 'high'
        complexity_label = 'High'
    elif enabled_count >= 100 or heavy_count >= 5 or high_impact >= 1:
        complexity = 'medium'
        complexity_label = 'Medium'
    else:
        complexity = 'low'
        complexity_label = 'Low'

    # Recommendation based on specs
    recommendation = None
    vram_spec = None
    if specs:
        v = specs.get('vram_gb') or specs.get('vram')
        if v:
            try:
                vram_spec = int(str(v).replace('gb', '').strip())
            except (ValueError, TypeError):
                pass

    if vram_spec is not None:
        if estimated_vram > vram_spec + 1:
            recommendation = (
                f"Your GPU has {vram_spec}GB VRAM. This load order may use ~{estimated_vram:.0f}GB. "
                "Consider reducing texture resolution or disabling heavy mods to avoid stuttering or CTDs."
            )
        elif estimated_vram <= vram_spec - 1:
            recommendation = (
                f"Your {vram_spec}GB VRAM should handle this load order (~{estimated_vram:.0f}GB estimated). "
                "Monitor performance in dense areas."
            )
        else:
            recommendation = (
                f"VRAM usage (~{estimated_vram:.0f}GB) is close to your {vram_spec}GB. "
                "Consider a performance ENB preset or 2K textures if you see stuttering."
            )

    return {
        'complexity': complexity,
        'complexity_label': complexity_label,
        'enabled_count': enabled_count,
        'heavy_mod_count': len(heavy_mods),
        'heavy_mods': heavy_mods[:20],
        'impact_ranking': heavy_mods,  # Full list, heaviest first (scrollable in UI)
        'estimated_vram_gb': estimated_vram,
        'recommendation': recommendation,
        'has_specs': bool(specs and any(specs.values())),
    }


def format_system_impact_for_ai(si: Dict) -> str:
    """
    Compact system impact summary for AI agent context.
    Token-efficient, structured for reasoning about performance and recommendations.
    """
    if not si:
        return ''
    lines = [
        '---',
        'System Impact (performance prediction):',
        f"Complexity: {si.get('complexity_label', 'Low')} | ~{si.get('estimated_vram_gb', 0):.0f}GB VRAM | {si.get('heavy_mod_count', 0)} heavy mods",
    ]
    if si.get('recommendation'):
        lines.append(f"Recommendation: {si['recommendation']}")
    heavy = si.get('heavy_mods') or []
    if heavy:
        parts = [f"{m.get('name', '')}({m.get('impact', '?')})" for m in heavy[:12]]
        lines.append(f"Heavy mods: {', '.join(parts)}")
    return '\n'.join(lines)


def format_system_impact_report(si: Dict) -> str:
    """Format system impact as plain text for inclusion in reports."""
    if not si:
        return ''
    lines = [
        '',
        'System Impact',
        '=' * 60,
        f"Complexity: {si.get('complexity_label', 'Low')}",
        f"Estimated VRAM: ~{si.get('estimated_vram_gb', 0):.0f} GB",
        f"Heavy mods detected: {si.get('heavy_mod_count', 0)}",
    ]
    if si.get('recommendation'):
        lines.append('')
        lines.append(si['recommendation'])
    heavy = si.get('heavy_mods') or []
    if heavy:
        lines.append('')
        lines.append('Mods that may impact performance:')
        for m in heavy[:15]:
            lines.append(f"  • [{m.get('impact', 'medium').upper()}] {m.get('name', '')} ({m.get('category', '')})")
    return '\n'.join(lines)
