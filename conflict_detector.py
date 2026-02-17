"""
Mod Conflict Detection Engine
Analyzes user's mod list and detects conflicts, missing requirements, load order issues
"""

import re
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Dict, List, Optional, Set

from loot_parser import LOOTParser, ModConflict, ModInfo


@dataclass
class ModListEntry:
    """Represents a mod in the user's load order"""
    name: str
    position: int  # Position in load order (0 = first)
    enabled: bool = True

    def __hash__(self):
        return hash(self.name.lower())


# Game-specific xEdit tool links for dirty edits (Nexus mod ID or docs)
_XEDIT_LINKS = {
    'skyrimse': ('SSEEdit', 'https://www.nexusmods.com/skyrimspecialedition/mods/164'),
    'skyrimvr': ('SSEEdit', 'https://www.nexusmods.com/skyrimspecialedition/mods/164'),
    'skyrim': ('TES5Edit', 'https://www.nexusmods.com/skyrim/mods/25859'),
    'oblivion': ('TES4Edit', 'https://www.nexusmods.com/oblivion/mods/11536'),
    'fallout3': ('FO3Edit', 'https://www.nexusmods.com/fallout3/mods/637'),
    'falloutnv': ('FNVEdit', 'https://www.nexusmods.com/newvegas/mods/34703'),
    'fallout4': ('FO4Edit', 'https://www.nexusmods.com/fallout4/mods/27373'),
    'starfield': ('xEdit', 'https://tes5edit.github.io/docs/7-mod-cleaning-and-error-checking.html#ThreeEasyStepstocleanMods'),
}
_XEDIT_DOCS = 'https://tes5edit.github.io/docs/7-mod-cleaning-and-error-checking.html#ThreeEasyStepstocleanMods'

# Cross-game mod hints: (selected_game_id, pattern_in_mod_name) -> (wrong_game_name, suggestion)
# Used to warn when user likely pasted a mod from a different game (e.g. LE mod in SE list).
_CROSS_GAME_HINTS = [
    # Skyrim SE/VR selected but mod looks like LE
    ('skyrimse', 'legendary edition', 'Skyrim Legendary Edition', 'Use the Special Edition version (USSEP, SkyUI_SE, etc.) for Skyrim SE.'),
    ('skyrimse', 'usleep', 'Skyrim Legendary Edition', 'USLEEP is for Legendary Edition. Use USSEP (Unofficial Skyrim Special Edition Patch) for Skyrim SE.'),
    ('skyrimse', 'uskp', 'Skyrim Legendary Edition', 'USKP is for original Skyrim. Use USSEP for Skyrim SE.'),
    ('skyrimvr', 'legendary edition', 'Skyrim Legendary Edition', 'Use the Special Edition version for Skyrim VR.'),
    ('skyrimvr', 'usleep', 'Skyrim Legendary Edition', 'USLEEP is for Legendary Edition. Use USSEP for Skyrim VR.'),
    ('skyrimvr', 'uskp', 'Skyrim Legendary Edition', 'USKP is for original Skyrim. Use USSEP for Skyrim VR.'),
    # Skyrim LE selected but mod looks like SE
    ('skyrim', 'special edition', 'Skyrim Special Edition', 'Use the Legendary Edition version (USLEEP, SkyUI, etc.) for Skyrim LE.'),
    ('skyrim', 'ussep', 'Skyrim Special Edition', 'USSEP is for Special Edition. Use USLEEP (Unofficial Skyrim Legendary Edition Patch) for Skyrim LE.'),
    ('skyrim', '_se.', 'Skyrim Special Edition', 'This appears to be a Special Edition plugin. Use the LE version for Skyrim Legendary Edition.'),
    ('skyrim', 'skyui_se', 'Skyrim Special Edition', 'SkyUI_SE is for Special Edition. Use SkyUI for Skyrim LE.'),
    # Fallout 4 vs 3/NV (less common but possible)
    ('fallout4', 'fallout 3', 'Fallout 3', 'This mod may be for Fallout 3. Use Fallout 4 versions for FO4.'),
    ('fallout4', 'fallout new vegas', 'Fallout New Vegas', 'This mod may be for New Vegas. Use Fallout 4 versions for FO4.'),
    ('fallout3', 'fallout 4', 'Fallout 4', 'This mod may be for Fallout 4. Use Fallout 3 versions for FO3.'),
    ('falloutnv', 'fallout 4', 'Fallout 4', 'This mod may be for Fallout 4. Use New Vegas versions for FNV.'),
]


def _neutralize_message(text: str) -> str:
    """
    Soften overly definitive LOOT language for clearer user-facing messages.
    Keeps statements neutral: 'this may conflict if...' instead of 'You seem to be...'
    """
    if not text or not isinstance(text, str):
        return text
    t = text
    # "You seem to be using X, but you have not enabled a compatibility patch..."
    t = re.sub(
        r'You seem to be using ([^,]+,) but you have not enabled a compatibility patch for this mod\.',
        r'This may conflict if you have \1 a compatibility patch may be needed.',
        t, flags=re.I
    )
    t = re.sub(r'\bYou seem to be using\b', 'This may apply if you have', t, flags=re.I)
    t = re.sub(r'\bIt appears you (do not|don\'t)\b', 'You may want to check if', t, flags=re.I)
    t = re.sub(r'\bYour installed version of\b', 'The installed version of', t, flags=re.I)
    t = re.sub(r'\bis not compatible\b', 'may not be compatible', t, flags=re.I)
    t = re.sub(r'\bSome of this plugin\'s requirements seem to be missing\b',
               'Some requirements may be missing for this plugin', t, flags=re.I)
    t = re.sub(r'\bA patch is required\b', 'A patch may be required', t, flags=re.I)
    t = re.sub(r'\bis required (?:for|to)\b', 'may be required for', t, flags=re.I)
    return t


def _check_cross_game(mod_name: str, game_id: str) -> Optional[tuple]:
    """If mod appears to be from a different game, return (wrong_game_name, suggestion)."""
    name_lower = mod_name.lower()
    for gid, pattern, wrong_game, suggestion in _CROSS_GAME_HINTS:
        if gid == game_id and pattern in name_lower:
            return (wrong_game, suggestion)
    return None


class ConflictDetector:
    """Detects conflicts in user's mod list"""

    def __init__(self, parser: LOOTParser, nexus_slug: Optional[str] = None):
        self.parser = parser
        self.nexus_slug = nexus_slug or 'skyrimspecialedition'
        self.conflicts: List[ModConflict] = []
        self.mod_info_cache: Dict[str, Optional[ModInfo]] = {}

    def _get_mod_info_cached(self, mod_name: str) -> Optional[ModInfo]:
        """Get mod info with caching to avoid repeated lookups."""
        key = mod_name.lower()
        if key not in self.mod_info_cache:
            self.mod_info_cache[key] = self.parser.get_mod_info(mod_name)
        return self.mod_info_cache[key]

    def analyze_load_order(self, mod_list: List[ModListEntry]) -> List[ModConflict]:
        """
        Analyze a mod list and return all detected conflicts

        Args:
            mod_list: List of mods in user's current load order

        Returns:
            List of conflicts found
        """
        self.conflicts = []
        self.mod_info_cache.clear()  # Clear cache for new analysis

        # Build lookup maps
        mod_positions = {mod.name.lower(): mod.position for mod in mod_list}
        enabled_mods = {mod.name.lower() for mod in mod_list if mod.enabled}
        mod_names_lower_to_original = {mod.name.lower(): mod.name for mod in mod_list}

        game_id = getattr(self.parser, 'game', 'skyrimse')
        for mod in mod_list:
            if not mod.enabled:
                continue

            # Check 0: Cross-game mod (e.g. LE mod in SE list)
            cross = _check_cross_game(mod.name, game_id)
            if cross:
                wrong_game, suggestion = cross
                self.conflicts.append(ModConflict(
                    type='cross_game',
                    severity='warning',
                    message=f'**{mod.name}** looks like a **{wrong_game}** mod, but you selected a different game. {suggestion}',
                    affected_mod=mod.name,
                    suggested_action=suggestion
                ))

            # Get mod info from LOOT database (cached)
            mod_info = self._get_mod_info_cached(mod.name)

            if not mod_info:
                # Mod not in LOOT database - friendly note; suggest fuzzy match if any
                msg = f'We don\'t have **{mod.name}** in our database yet—it might be a custom or renamed mod.'
                suggestion = self.parser.get_fuzzy_suggestion(mod.name)
                if suggestion:
                    msg += f' Did you mean **{suggestion}**?'
                self.conflicts.append(ModConflict(
                    type='unknown_mod',
                    severity='info',
                    message=msg,
                    affected_mod=mod.name
                ))
                continue

            # Check 1: Missing requirements
            self._check_requirements(mod.name, mod_info, enabled_mods, mod_names_lower_to_original)

            # Check 2: Incompatibilities
            self._check_incompatibilities(mod.name, mod_info, enabled_mods, mod_names_lower_to_original)

            # Check 3: Load order violations
            self._check_load_order(mod.name, mod_info, mod_positions, mod_names_lower_to_original)

            # Check 4: Patch available (user has both mods but not the patch)
            for patch_entry in mod_info.patches:
                if isinstance(patch_entry, dict):
                    for other_mod, patch_name in patch_entry.items():
                        other_clean = self.parser._normalize_name(other_mod)
                        patch_clean = self.parser._normalize_name(patch_name)
                        if other_clean in enabled_mods and patch_clean not in enabled_mods:
                            orig_patch = mod_names_lower_to_original.get(patch_clean, patch_name)
                            self.conflicts.append(ModConflict(
                                type='patch_available',
                                severity='warning',
                                message=f'**{mod.name}** and **{other_mod}** have a compatibility patch: **{orig_patch}**. Install and enable it for best results.',
                                affected_mod=mod.name,
                                suggested_action=f'Install and enable {orig_patch}',
                                related_mod=other_mod
                            ))

            # Check 5: Dirty edits (with game-specific xEdit links)
            if mod_info.dirty_edits:
                game_id = getattr(self.parser, 'game', 'skyrimse')
                editor_name, editor_url = _XEDIT_LINKS.get(game_id, ('xEdit', _XEDIT_DOCS))
                self.conflicts.append(ModConflict(
                    type='dirty_edits',
                    severity='warning',
                    message=(
                        f'**{mod.name}** has dirty edits. Cleaning it with '
                        f'[{editor_name}]({editor_url}) or '
                        f'[xEdit docs]({_XEDIT_DOCS}) '
                        'can prevent subtle bugs—see the links for a short guide.'
                    ),
                    affected_mod=mod.name,
                    suggested_action=(
                        f'Clean with [{editor_name}]({editor_url}) '
                        f'or [xEdit](https://tes5edit.github.io/) — see the [cleaning guide]({_XEDIT_DOCS}).'
                    )
                ))

            # Check 6: LOOT messages (all from masterlist; softened for user-friendly tone)
            for message in mod_info.messages:
                neutral = _neutralize_message(message)
                self.conflicts.append(ModConflict(
                    type='info',
                    severity='info',
                    message=f'**{mod.name}**: {neutral}',
                    affected_mod=mod.name
                ))

        return self.conflicts

    def _check_requirements(self, mod_name: str, mod_info: ModInfo, enabled_mods: Set[str],
                           mod_names_lower_to_original: Dict[str, str]) -> None:
        """Check if all required mods are present."""
        for req in mod_info.requirements:
            req_clean = self.parser._normalize_name(req)
            if req_clean not in enabled_mods:
                orig_req = mod_names_lower_to_original.get(req_clean, req)
                self.conflicts.append(ModConflict(
                    type='missing_requirement',
                    severity='error',
                    message=f'**{mod_name}** needs **{orig_req}** to work properly. Install and enable it to avoid missing content or crashes.',
                    affected_mod=mod_name,
                    suggested_action=f'Install and enable {orig_req}',
                    related_mod=orig_req
                ))

    def _check_incompatibilities(self, mod_name: str, mod_info: ModInfo, enabled_mods: Set[str],
                                mod_names_lower_to_original: Dict[str, str]) -> None:
        """Check for incompatible mods."""
        for inc in mod_info.incompatibilities:
            inc_clean = self.parser._normalize_name(inc)
            if inc_clean in enabled_mods:
                orig_inc = mod_names_lower_to_original.get(inc_clean, inc)
                self.conflicts.append(ModConflict(
                    type='incompatible',
                    severity='error',
                    message=f'**{mod_name}** and **{orig_inc}** don\'t work well together—using both can cause crashes or odd behavior. Pick one or disable the other.',
                    affected_mod=mod_name,
                    suggested_action=f'Disable either {mod_name} or {orig_inc}',
                    related_mod=orig_inc
                ))

    def _check_load_order(self, mod_name: str, mod_info: ModInfo, mod_positions: Dict[str, int],
                         mod_names_lower_to_original: Dict[str, str]) -> None:
        """Check if load order follows LOOT rules."""
        current_pos = mod_positions.get(mod_name.lower())
        if current_pos is None:
            return  # Should not happen because mod is in mod_list

        # Check "load after" rules
        for after_mod in mod_info.load_after:
            after_clean = self.parser._normalize_name(after_mod)
            after_pos = mod_positions.get(after_clean)
            if after_pos is not None:
                if current_pos <= after_pos:
                    orig_after = mod_names_lower_to_original.get(after_clean, after_mod)
                    self.conflicts.append(ModConflict(
                        type='load_order_violation',
                        severity='warning',
                        message=f'For best results, **{mod_name}** should load after **{orig_after}**.',
                        affected_mod=mod_name,
                        suggested_action=f'Move {mod_name} below {orig_after} in your load order',
                        related_mod=orig_after
                    ))

        # Check "load before" rules (inverse of load after)
        for before_mod in mod_info.load_before:
            before_clean = self.parser._normalize_name(before_mod)
            before_pos = mod_positions.get(before_clean)
            if before_pos is not None:
                if current_pos >= before_pos:
                    orig_before = mod_names_lower_to_original.get(before_clean, before_mod)
                    self.conflicts.append(ModConflict(
                        type='load_order_violation',
                        severity='warning',
                        message=f'For best results, **{mod_name}** should load before **{orig_before}**.',
                        affected_mod=mod_name,
                        suggested_action=f'Move {mod_name} above {orig_before} in your load order',
                        related_mod=orig_before
                    ))

    def get_conflicts_by_severity(self) -> Dict[str, List[ModConflict]]:
        """Group conflicts by severity. Always returns all three keys for consistent API response."""
        grouped = defaultdict(list)
        for conflict in self.conflicts:
            grouped[conflict.severity].append(conflict)
        # Ensure error, warning, info keys always exist so API consumers don't get KeyError
        result = dict(grouped)
        for key in ('error', 'warning', 'info'):
            result.setdefault(key, [])
        return result

    def get_suggested_load_order(self, mod_list: List[ModListEntry]) -> List[str]:
        """
        Generate suggested load order using LOOT load_after/load_before rules.
        Uses topological sort; mods with no rules keep relative order.
        """
        if not mod_list:
            return []

        name_to_mod = {m.name.lower(): m for m in mod_list}
        # Build edges: (a, b) means a must load before b  =>  b loads after a
        # So for "X load after Y" we have edge (Y, X): Y before X.
        in_degree: Dict[str, int] = {}
        for m in mod_list:
            key = m.name.lower()
            in_degree[key] = in_degree.get(key, 0)

        edges: Dict[str, List[str]] = defaultdict(list)  # from -> [tos]

        for mod in mod_list:
            if not mod.enabled:
                continue
            mod_key = mod.name.lower()
            mod_info = self._get_mod_info_cached(mod.name)
            if not mod_info:
                continue
            for after_name in mod_info.load_after:
                after_clean = self.parser._normalize_name(after_name)
                if after_clean in name_to_mod and name_to_mod[after_clean].enabled:
                    # mod must load after after_clean  =>  after_clean before mod
                    edges[after_clean].append(mod_key)
                    in_degree[mod_key] = in_degree.get(mod_key, 0) + 1
            for before_name in mod_info.load_before:
                before_clean = self.parser._normalize_name(before_name)
                if before_clean in name_to_mod and name_to_mod[before_clean].enabled:
                    # mod must load before before_clean  =>  mod before before_clean
                    edges[mod_key].append(before_clean)
                    in_degree[before_clean] = in_degree.get(before_clean, 0) + 1

        # Topological sort (Kahn)
        order: List[str] = []
        q = deque(k for k, d in in_degree.items() if d == 0)
        while q:
            # Keep stable order by processing in original position order when degree is 0
            current = q.popleft()
            order.append(current)
            for next_key in edges[current]:
                in_degree[next_key] -= 1
                if in_degree[next_key] == 0:
                    q.append(next_key)

        # Map back to original names (first occurrence in mod_list)
        orig_order = []
        seen = set()
        for key in order:
            if key in seen:
                continue
            seen.add(key)
            orig = next(m.name for m in mod_list if m.name.lower() == key)
            orig_order.append(orig)

        # Append any enabled mods not in the graph (no rules)
        for mod in mod_list:
            if mod.enabled and mod.name.lower() not in seen:
                orig_order.append(mod.name)
                seen.add(mod.name.lower())

        # Return only enabled mods in suggested order (for plugins.txt export)
        return orig_order

    def _plain(self, text: str) -> str:
        """Strip markdown bold for plain-text report."""
        if not text:
            return text
        return text.replace('**', '')

    def format_report(self) -> str:
        """Format conflicts into a human-readable report (plain text)."""
        if not self.conflicts:
            return "No issues found! Your load order looks good."

        grouped = self.get_conflicts_by_severity()
        report_lines = []

        # Errors
        if grouped.get('error'):
            report_lines.append(f"Errors ({len(grouped['error'])})")
            report_lines.append("=" * 60)
            for conflict in grouped['error']:
                report_lines.append(f"• {self._plain(conflict.message)}")
                if conflict.suggested_action:
                    report_lines.append(f"  → {self._plain(conflict.suggested_action)}")
            report_lines.append("")

        # Warnings
        if grouped.get('warning'):
            report_lines.append(f"Warnings ({len(grouped['warning'])})")
            report_lines.append("=" * 60)
            for conflict in grouped['warning']:
                report_lines.append(f"• {self._plain(conflict.message)}")
                if conflict.suggested_action:
                    report_lines.append(f"  → {self._plain(conflict.suggested_action)}")
            report_lines.append("")

        # Info (with disclaimer)
        if grouped.get('info'):
            report_lines.append(f"Info ({len(grouped['info'])})")
            report_lines.append("=" * 60)
            report_lines.append("(LOOT suggestions—check if they apply to your setup.)")
            for i, conflict in enumerate(grouped['info']):
                if i >= 10:
                    report_lines.append(f" ... and {len(grouped['info']) - 10} more")
                    break
                report_lines.append(f"• {self._plain(conflict.message)}")

        return "\n".join(report_lines)

    def format_report_for_ai(self, game_name: str = '', nexus_slug: str = 'skyrimspecialedition', specs: dict = None) -> str:
        """Structured report for AI agent: game context, specs, conflict types, mods, and actionable links."""
        lines = []
        lines.append(f"Game: {game_name or 'Unknown'}")
        lines.append(f"Nexus: https://www.nexusmods.com/games/{nexus_slug}/mods")
        if specs and any(v for v in specs.values() if v):
            spec_parts = [f"{k}: {v}" for k, v in specs.items() if v]
            if spec_parts:
                lines.append(f"User specs: {', '.join(spec_parts)}")
        lines.append("")
        if not self.conflicts:
            return "\n".join(lines) + "No issues found."
        for c in self.conflicts:
            mod_part = f" [{c.affected_mod or '?'}"
            if getattr(c, 'related_mod', None):
                mod_part += f" ↔ {c.related_mod}"
            mod_part += "]"
            lines.append(f"[{c.type}] {c.severity}{mod_part}: {self._plain(c.message)}")
            if c.suggested_action:
                lines.append(f"  → {self._plain(c.suggested_action)}")
        return "\n".join(lines)


def parse_mod_list_text(text: str) -> List[ModListEntry]:
    """
    Parse various mod list formats into ModListEntry objects. Intentionally forgiving.

    Supports:
    - Mod Organizer 2: +ModName (enabled), -ModName (disabled)
    - plugins.txt: *ModName.esp (enabled), ModName.esp (disabled)
    - Vortex / plain: one plugin per line (all enabled)
    - Comments (#) and paths (last path segment used as name)
    - Lines with only whitespace are skipped; leading/trailing space is trimmed.
    """
    mods = []
    # Normalize line endings and strip BOM
    text = text.strip().replace('\r\n', '\n').replace('\r', '\n')
    lines = text.split('\n')

    # Detect plugins.txt format: at least one line starts with *
    looks_like_plugins_txt = any(
        ln.strip().startswith('*') for ln in lines if ln.strip() and not ln.strip().startswith('#')
    )

    position = 0
    for i, line in enumerate(lines):
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        enabled = True
        mod_name = line

        # MO2 format: +ModName or -ModName
        if line.startswith('+'):
            mod_name = line[1:].strip()
            enabled = True
        elif line.startswith('-'):
            mod_name = line[1:].strip()
            enabled = False
        # plugins.txt: * = enabled, no * = disabled
        elif line.startswith('*'):
            mod_name = line[1:].strip()
            enabled = True
        elif looks_like_plugins_txt:
            # Same file uses plugins.txt convention: unmarked = disabled
            enabled = False

        if not mod_name:
            continue

        # Strip common suffixes like " (disabled)" or " (disabled by user)"
        for suffix in (' (disabled)', ' (disabled by user)', ' (optional)'):
            if mod_name.lower().endswith(suffix.lower()):
                mod_name = mod_name[: -len(suffix)].strip()
                break

        # Extract filename from path if present
        if '/' in mod_name or '\\' in mod_name:
            mod_name = mod_name.replace('\\', '/').split('/')[-1]

        mods.append(ModListEntry(
            name=mod_name,
            position=position,
            enabled=enabled
        ))
        position += 1

    return mods
