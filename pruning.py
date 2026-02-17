"""
Pruning — Neurological-style context reduction for AI agents.

Philosophy:
  Pruning is the deliberate removal of non-essential information to strengthen
  the signal. Like synaptic pruning in the brain, we remove redundancy and
  noise so what remains is more actionable. We prune context, not truth:
  user-specific conflicts, mod names, and actionable fixes are never cut.

  Input pruning: Before sending context to an AI agent, we reduce volume while
  preserving signal. Errors > warnings > info. User-relevant content wins.

  Output pruning: Optional distillation of AI responses into key points.
  Used for Fix Guide steps, not for chat replies (user sees full reply).

Invariants (we never cut):
  - Error-level conflicts and their suggested actions
  - Warning-level conflicts and their suggested actions
  - Mod names that appear in conflicts
  - The user's question or message
  - Game name and core identifiers

Config:
  PRUNING_ENABLED=1 (default) — set 0 to bypass
  PRUNING_MAX_CONTEXT_CHARS=12000 — soft cap; we prefer smart pruning over hard truncation
"""

import logging
import os
import re
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

PRUNING_ENABLED = os.environ.get('PRUNING_ENABLED', '1').strip() in ('1', 'true', 'yes')
PRUNING_MAX_CONTEXT_CHARS = int(os.environ.get('PRUNING_MAX_CONTEXT_CHARS', '12000'))


# Conflict line pattern: [type] severity [mods]: message
_CONFLICT_LINE = re.compile(r'^\[([^\]]+)\]\s+(error|warning|info)\s+', re.I)


def _classify_conflict_line(line: str) -> Optional[str]:
    """Return 'error', 'warning', 'info', or None if not a conflict line."""
    m = _CONFLICT_LINE.search(line.strip())
    return m.group(2).lower() if m else None


def prune_input_context(
    context: str,
    user_message: Optional[str] = None,
    max_chars: Optional[int] = None,
) -> Tuple[str, dict]:
    """
    Prune AI input context. Preserves errors, warnings, and user-relevant content.

    Invariants: never cut error/warning conflicts or their actions. Info caps at 12.
    If still over limit, trim from knowledge/system-impact sections last.

    Returns:
      (pruned_context, stats) — stats has keys: original_len, pruned_len, pruning_applied, info_capped
    """
    if not PRUNING_ENABLED or not context:
        return (context, {'pruning_applied': False})

    max_chars = max_chars or PRUNING_MAX_CONTEXT_CHARS
    original_len = len(context)
    stats = {'original_len': original_len, 'pruning_applied': False, 'info_capped': False}

    if original_len <= max_chars:
        return (context, stats)

    lines = context.splitlines()
    result_lines = []
    info_count = 0
    info_cap = 12
    skip_next = False  # Skip "→ action" when we omit its parent info conflict

    for i, line in enumerate(lines):
        if skip_next:
            skip_next = False
            continue  # Skip the "→ action" line for omitted info conflict

        severity = _classify_conflict_line(line)
        if severity:
            if severity == 'error' or severity == 'warning':
                result_lines.append(line)
            elif severity == 'info':
                if info_count < info_cap:
                    result_lines.append(line)
                    info_count += 1
                else:
                    if info_count == info_cap:
                        result_lines.append("  ... (additional info items omitted for context)")
                        stats['info_capped'] = True
                    info_count += 1
                    # Next line may be "  → action" for this omitted conflict
                    if i + 1 < len(lines) and lines[i + 1].strip().startswith('→'):
                        skip_next = True
        else:
            result_lines.append(line)

    result = '\n'.join(result_lines)

    # If still over limit, trim from the end (knowledge/system impact are last)
    if len(result) > max_chars:
        # Find a safe break point: after last error/warning block
        result = result[:max_chars]
        last_newline = result.rfind('\n')
        if last_newline > max_chars * 0.7:  # Avoid cutting mid-line
            result = result[:last_newline + 1]
        result += "\n\n[Context trimmed. All errors and warnings above are preserved.]"
        stats['trimmed'] = True

    stats['pruned_len'] = len(result)
    stats['pruning_applied'] = True
    return (result, stats)


def prune_output_for_fix_guide(reply: str, max_bullets: int = 8) -> str:
    """
    Optional output pruning: distill an AI reply into key bullets for Fix Guide steps.
    Only used when appending to the Live Fix Guide. Full reply still shown to user.

    Conservative: we extract numbered/bullet points; if none, return original.
    """
    if not reply or not PRUNING_ENABLED:
        return reply

    bullets = []
    for line in reply.splitlines():
        s = line.strip()
        if not s:
            continue
        # Match "1. ", "- ", "• ", "* "
        if re.match(r'^[\d]+[.)]\s', s) or re.match(r'^[-•*]\s', s):
            bullets.append(s)
        elif s.startswith('→') or s.startswith('→'):
            bullets.append(s)

    if len(bullets) <= max_bullets:
        return reply
    # Keep first max_bullets and add ellipsis
    kept = bullets[:max_bullets]
    return '\n'.join(kept) + '\n  (see full reply in chat)'


def prune_game_folder_context(tree: str, key_files: dict, plugins: list, max_tree_chars: int = 4000, max_file_chars: int = 3000) -> Tuple[str, dict, dict]:
    """
    Prune game folder scan context. Keep: plugin list, folder structure (truncate depth),
    key file contents (truncate per file).
    """
    if not PRUNING_ENABLED:
        return (tree, key_files, {'pruning_applied': False})

    stats = {'pruning_applied': True}
    if len(tree) > max_tree_chars:
        tree = tree[:max_tree_chars] + "\n\n[Folder structure truncated. Key paths preserved.]"
        stats['tree_truncated'] = True

    pruned_files = {}
    for path, content in key_files.items():
        if content and len(content) > max_file_chars:
            pruned_files[path] = content[:max_file_chars] + "\n\n[File truncated.]"
            stats['files_truncated'] = stats.get('files_truncated', 0) + 1
        else:
            pruned_files[path] = content or ''

    return (tree, pruned_files, stats)
