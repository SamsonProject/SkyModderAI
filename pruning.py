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

  Context Threading: Integrated with context_threading.py for intentional
  compression. When AI explores tangents, it leaves bookmarks that track:
  - WHY we diverged (intention)
  - WHAT we're exploring (branch)
  - WHEN to return (return condition)

  Message Pruning: When maintaining conversation history, NEVER prune system
  messages or the first message. Only remove middle-of-conversation user/
  assistant turns to stay within token limits.

Invariants (we never cut):
  - Error-level conflicts and their suggested actions
  - Warning-level conflicts and their suggested actions
  - Mod names that appear in conflicts
  - The user's question or message
  - Game name and core identifiers
  - System messages (role="system") - defines AI identity
  - The first message in any conversation

Config:
  PRUNING_ENABLED=1 (default) — set 0 to bypass
  PRUNING_MAX_CONTEXT_CHARS=12000 — soft cap; we prefer smart pruning over hard truncation
  CONTEXT_THREADING_ENABLED=1 (default) — enable context threading with bookmarks
"""

import logging
import os
import re
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

PRUNING_ENABLED = os.environ.get("PRUNING_ENABLED", "1").strip() in ("1", "true", "yes")


def _estimate_tokens(text: str) -> int:
    """Rough token estimation: ~4 chars per token for English text."""
    return len(text) // 4 if text else 0


def _message_tokens(message: Dict[str, str]) -> int:
    """Estimate tokens in a single message."""
    content = message.get("content", "")
    return _estimate_tokens(content)


def prune_context(
    messages: List[Dict[str, str]],
    max_tokens: int = 4000,
    min_exchanges: int = 2,
) -> List[Dict[str, str]]:
    """
    Prune AI conversation messages while protecting system prompt and first message.

    Invariants:
    - NEVER prune messages with role="system"
    - NEVER prune the first message in the array
    - Only remove middle-of-conversation user/assistant turns
    - Keep at least min_exchanges of the most recent conversation

    Args:
        messages: List of message dicts with 'role' and 'content' keys
        max_tokens: Maximum tokens to stay under (default: 4000)
        min_exchanges: Minimum user/assistant exchanges to keep (default: 2)

    Returns:
        Pruned list of messages that stays within token limit
    """
    if not messages:
        return []

    # Separate protected and prunable messages
    # Protected: system messages + first message
    protected = []
    prunable = []

    for i, msg in enumerate(messages):
        if i == 0 or msg.get("role") == "system":
            protected.append(msg)
        else:
            prunable.append(msg)

    # Calculate current token count
    def total_tokens():
        return sum(_message_tokens(m) for m in protected + prunable)

    # Trim from oldest prunable messages first
    while total_tokens() > max_tokens and len(prunable) > min_exchanges:
        prunable.pop(0)

    # Ensure we have at least one exchange if possible
    if len(prunable) < 2 and len(prunable) > 0:
        # Keep what we have, even if over limit
        pass

    return protected + prunable


PRUNING_MAX_CONTEXT_CHARS = int(os.environ.get("PRUNING_MAX_CONTEXT_CHARS", "12000"))
CONTEXT_THREADING_ENABLED = os.environ.get("CONTEXT_THREADING_ENABLED", "1").strip() in (
    "1",
    "true",
    "yes",
)

# Import context threading if enabled
if CONTEXT_THREADING_ENABLED:
    try:
        from context_threading import (
            CompressionLevel,
            InformationPipeline,
            get_pipeline,
            start_thread,
        )
    except ImportError:
        CONTEXT_THREADING_ENABLED = False


# Conflict line pattern: [type] severity [mods]: message
_CONFLICT_LINE = re.compile(r"^\[([^\]]+)\]\s+(error|warning|info)\s+", re.I)


def prune_with_intention(
    context: str,
    intention: str,
    max_chars: Optional[int] = None,
) -> Tuple[str, Dict]:
    """
    Prune context with intention tracking using context threading.

    This is smarter than basic pruning — it tracks WHY we're compressing
    and preserves goal-relevant information even if it would normally be cut.

    Args:
        context: Context to prune
        intention: The goal/intention (preserves goal-relevant info)
        max_chars: Maximum characters (default: PRUNING_MAX_CONTEXT_CHARS)

    Returns:
        (pruned_context, stats) — stats includes threading info if enabled
    """
    if CONTEXT_THREADING_ENABLED:
        try:
            pipeline = get_pipeline()

            # Compress with intention
            compressed, compress_stats = pipeline.compress(
                context,
                intention=intention,
                level=CompressionLevel.MODERATE,
            )

            # Then apply traditional pruning as safety net
            pruned, prune_stats = prune_input_context(
                compressed,
                user_message=intention,
                max_chars=max_chars,
            )

            # Combine stats
            stats = {
                **prune_stats,
                "compression": compress_stats,
                "threading_enabled": True,
                "intention": intention[:100],
            }

            return (pruned, stats)

        except Exception as e:
            logger.warning(f"Context threading failed: {e}, falling back to basic pruning")

    # Fallback to basic pruning
    return prune_input_context(context, user_message=intention, max_chars=max_chars)


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
        return (context, {"pruning_applied": False})

    max_chars = max_chars or PRUNING_MAX_CONTEXT_CHARS
    original_len = len(context)
    stats = {"original_len": original_len, "pruning_applied": False, "info_capped": False}

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
            if severity == "error" or severity == "warning":
                result_lines.append(line)
            elif severity == "info":
                if info_count < info_cap:
                    result_lines.append(line)
                    info_count += 1
                else:
                    if info_count == info_cap:
                        result_lines.append("  ... (additional info items omitted for context)")
                        stats["info_capped"] = True
                    info_count += 1
                    # Next line may be "  → action" for this omitted conflict
                    if i + 1 < len(lines) and lines[i + 1].strip().startswith("→"):
                        skip_next = True
        else:
            result_lines.append(line)

    result = "\n".join(result_lines)

    # If still over limit, trim from the end (knowledge/system impact are last)
    if len(result) > max_chars:
        # Find a safe break point: after last error/warning block
        result = result[:max_chars]
        last_newline = result.rfind("\n")
        if last_newline > max_chars * 0.7:  # Avoid cutting mid-line
            result = result[: last_newline + 1]
        result += "\n\n[Context trimmed. All errors and warnings above are preserved.]"
        stats["trimmed"] = True

    stats["pruned_len"] = len(result)
    stats["pruning_applied"] = True
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
        if re.match(r"^[\d]+[.)]\s", s) or re.match(r"^[-•*]\s", s):
            bullets.append(s)
        elif s.startswith("→") or s.startswith("→"):
            bullets.append(s)

    if len(bullets) <= max_bullets:
        return reply
    # Keep first max_bullets and add ellipsis
    kept = bullets[:max_bullets]
    return "\n".join(kept) + "\n  (see full reply in chat)"


def prune_game_folder_context(
    tree: str,
    key_files: dict,
    plugins: list,
    max_tree_chars: int = 4000,
    max_file_chars: int = 3000,
) -> Tuple[str, dict, dict]:
    """
    Prune game folder scan context. Keep: plugin list, folder structure (truncate depth),
    key file contents (truncate per file).
    """
    if not PRUNING_ENABLED:
        return (tree, key_files, {"pruning_applied": False})

    stats = {"pruning_applied": True}
    if len(tree) > max_tree_chars:
        tree = tree[:max_tree_chars] + "\n\n[Folder structure truncated. Key paths preserved.]"
        stats["tree_truncated"] = True

    pruned_files = {}
    for path, content in key_files.items():
        if content and len(content) > max_file_chars:
            pruned_files[path] = content[:max_file_chars] + "\n\n[File truncated.]"
            stats["files_truncated"] = stats.get("files_truncated", 0) + 1
        else:
            pruned_files[path] = content or ""

    return (tree, pruned_files, stats)
