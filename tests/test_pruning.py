"""
Tests for pruning.py — ensure useful info is never cut.

Invariants we verify:
- Error and warning conflicts are never removed
- Info conflicts may be capped at 12 (with ellipsis)
- Mod names and suggested actions are preserved
"""

import os

# Ensure pruning is enabled for tests
os.environ["PRUNING_ENABLED"] = "1"

from pruning import (
    prune_game_folder_context,
    prune_input_context,
    prune_output_for_fix_guide,
)


class TestPruneInputContext:
    """Input pruning must never cut errors or warnings."""

    def test_errors_and_warnings_always_kept(self):
        context = """Game: Skyrim SE
Nexus: https://www.nexusmods.com/games/skyrimspecialedition/mods

[missing_requirement] error [ModA.esp ↔ SKSE]: Requires SKSE.
  → Install SKSE from silverlock.org
[incompatible] warning [ModB.esp ↔ ModC.esp]: These mods conflict.
  → Choose one or install a patch
[load_order_violation] warning [Patch.esp ↔ Parent.esp]: Load after parent.
  → Move Patch.esp after Parent.esp in load order
"""
        pruned, stats = prune_input_context(context, max_chars=5000)
        assert "[missing_requirement] error" in pruned
        assert "ModA.esp" in pruned
        assert "Install SKSE" in pruned
        assert "[incompatible] warning" in pruned
        assert "[load_order_violation] warning" in pruned
        assert "ModB.esp" in pruned
        assert "Patch.esp" in pruned

    def test_info_capped_at_12(self):
        lines = ["Game: Skyrim SE\n", "Nexus: https://nexusmods.com\n\n"]
        for i in range(20):
            lines.append(f"[unknown_mod] info [CustomMod{i}.esp]: Not in masterlist.\n")
        context = "".join(lines)
        # Use low max_chars so pruning is triggered (context is ~1200 chars)
        pruned, stats = prune_input_context(context, max_chars=800)
        assert stats.get("info_capped") is True
        assert "additional info items omitted" in pruned
        # First 12 should be present
        assert "CustomMod0.esp" in pruned
        assert "CustomMod11.esp" in pruned

    def test_short_context_unchanged(self):
        context = "Game: Skyrim SE\n[missing_requirement] error [X.esp]: Needs Y."
        pruned, stats = prune_input_context(context, max_chars=10000)
        assert pruned == context
        assert stats.get("pruning_applied") is False

    def test_preamble_preserved(self):
        context = """Game: Skyrim SE
User specs: GPU: RTX 3060, VRAM: 8GB

[missing_requirement] error [X.esp]: Needs SKSE.
  → Install SKSE
"""
        pruned, _ = prune_input_context(context, max_chars=5000)
        assert "Game: Skyrim SE" in pruned
        assert "User specs" in pruned
        assert "RTX 3060" in pruned


class TestPruneOutputForFixGuide:
    """Output pruning distills but does not lose key points."""

    def test_short_reply_unchanged(self):
        reply = "Install SKSE. Run LOOT. You're good."
        result = prune_output_for_fix_guide(reply, max_bullets=8)
        assert result == reply

    def test_long_bullet_list_trimmed(self):
        reply = "\n".join([f"{i + 1}. Step {i + 1} here." for i in range(12)])
        result = prune_output_for_fix_guide(reply, max_bullets=8)
        assert "Step 1" in result
        assert "Step 8" in result
        assert "see full reply" in result


class TestPruneGameFolderContext:
    """Game folder pruning preserves structure and key files."""

    def test_tree_truncated_when_long(self):
        tree = "Data/\n" + "  " * 50 + "deep/file.esp\n"
        tree = tree * 500  # Very long
        key_files = {"skyrim.ini": "content"}
        plugins = ["Skyrim.esm"]
        t, kf, stats = prune_game_folder_context(tree, key_files, plugins, max_tree_chars=1000)
        assert len(t) <= 1100  # 1000 + truncation message
        assert "Data/" in t
        assert "truncated" in t or stats.get("tree_truncated")

    def test_key_files_truncated_per_file(self):
        tree = "Data/"
        key_files = {"skyrim.ini": "x" * 5000}
        plugins = []
        t, kf, stats = prune_game_folder_context(tree, key_files, plugins, max_file_chars=500)
        assert len(kf["skyrim.ini"]) <= 550
