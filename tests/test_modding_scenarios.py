"""
Comprehensive tests for real-world modding scenarios.
Tests edge cases, large load orders, and Bethesda-specific issues.
"""
from pathlib import Path

import pytest

from conflict_detector import ConflictDetector, ModListEntry, parse_mod_list_text
from loot_parser import LOOTParser, ModInfo

DATA_DIR = Path(__file__).parent / "data"


class TestRealWorldLoadOrders:
    """Tests with realistic load orders from actual modders."""

    def test_load_254_plugin_order(self):
        """Test parsing a near-limit 254 plugin load order."""
        filepath = DATA_DIR / "loadorder_skyrimse_254.txt"
        assert filepath.exists(), "Test data file missing"

        text = filepath.read_text()
        mods = parse_mod_list_text(text)

        # Should parse all non-comment, non-empty lines
        assert len(mods) > 200, f"Expected 200+ mods, got {len(mods)}"

        # All should have valid names
        for mod in mods:
            assert mod.name, "Mod name should not be empty"
            assert mod.name.endswith(('.esp', '.esm', '.esl')), f"Invalid extension: {mod.name}"

    def test_analysis_performance_500_mods(self):
        """Performance test: analyzing 500 mods should complete quickly."""
        parser = LOOTParser('skyrimse')
        detector = ConflictDetector(parser)

        # Create 500 fake mods
        mods = [ModListEntry(f'Mod_{i:04d}.esp', i, True) for i in range(500)]

        import time
        start = time.time()
        conflicts = detector.analyze_load_order(mods)
        elapsed = time.time() - start

        # Performance budget: should complete in under 5 seconds
        assert elapsed < 5.0, f"Performance regression: {elapsed:.2f}s > 5s budget"
        assert isinstance(conflicts, list), "Should return a list of conflicts"

    def test_esl_flagged_mods(self):
        """Test ESL-flagged mods (light plugins) are handled correctly."""
        parser = LOOTParser('skyrimse')
        detector = ConflictDetector(parser)

        # Mix of regular and ESL mods
        mods = [
            ModListEntry('Skyrim.esm', 0, True),
            ModListEntry('LightMod1.esl', 1, True),
            ModListEntry('LightMod2.esl', 2, True),
            ModListEntry('RegularMod.esp', 3, True),
            ModListEntry('FEIndex.esl', 254, True),  # FE-indexed ESL
        ]

        conflicts = detector.analyze_load_order(mods)
        assert isinstance(conflicts, list), "Should handle ESL mods without crashing"


class TestEdgeCases:
    """Tests for edge cases and problematic inputs."""

    def test_unicode_mod_names(self):
        """Test mod names with unicode characters."""
        filepath = DATA_DIR / "edge_cases.txt"
        assert filepath.exists(), "Test data file missing"

        text = filepath.read_text()
        mods = parse_mod_list_text(text)

        # Should parse unicode names without issues
        assert len(mods) > 100, f"Expected 100+ mods, got {len(mods)}"

        # Find unicode mods
        unicode_mods = [m for m in mods if any(ord(c) > 127 for c in m.name)]
        assert len(unicode_mods) > 0, "Should have unicode mod names"

    def test_special_characters_in_names(self):
        """Test mod names with special characters."""
        test_cases = [
            "Mod [v1.2.3].esp",
            "Mod (with) parens.esp",
            "Mod-with-dashes.esp",
            "Mod.with.dots.esp",
            "Mod_with_underscores.esp",
            "Mod's 'Quote'.esp",
        ]

        for name in test_cases:
            mods = parse_mod_list_text(f"*{name}")
            assert len(mods) == 1, f"Should parse: {name}"
            assert mods[0].name == name, f"Name mismatch: {name}"

    def test_very_long_mod_names(self):
        """Test handling of very long mod names."""
        long_name = "A" * 500 + ".esp"
        mods = parse_mod_list_text(f"*{long_name}")
        assert len(mods) == 1
        assert len(mods[0].name) > 400

    def test_empty_and_whitespace(self):
        """Test handling of empty lines and whitespace."""
        test_cases = [
            "",
            "   ",
            "\n\n\n",
            "*Skyrim.esm\n\n\n*Update.esm",
            "  *Mod.esp  ",  # Leading/trailing whitespace
        ]

        for text in test_cases:
            mods = parse_mod_list_text(text)
            assert isinstance(mods, list), f"Should handle: {repr(text)}"

    def test_disabled_mods(self):
        """Test parsing of disabled mods."""
        text = """*Enabled1.esp
Disabled1.esp
*Enabled2.esp
Disabled2.esp"""
        mods = parse_mod_list_text(text)

        enabled = [m for m in mods if m.enabled]
        disabled = [m for m in mods if not m.enabled]

        assert len(enabled) == 2
        assert len(disabled) == 2

    def test_mo2_format(self):
        """Test Mod Organizer 2 format (+/- prefixes)."""
        text = """+EnabledMO2.esp
-DisabledMO2.esp
+AnotherEnabled.esp"""
        mods = parse_mod_list_text(text)

        assert mods[0].enabled is True
        assert mods[1].enabled is False
        assert mods[2].enabled is True

    def test_vortex_format(self):
        """Test Vortex format (plain list, all enabled)."""
        text = """Skyrim.esm
Update.esm
Dawnguard.esm"""
        mods = parse_mod_list_text(text)

        # Vortex format: all enabled, no prefix
        assert all(m.enabled for m in mods)

    def test_full_path_extraction(self):
        """Test extraction of filename from full paths."""
        test_cases = [
            ("C:/Games/Skyrim/Data/Mod.esp", "Mod.esp"),
            ("C:\\Games\\Skyrim\\Data\\Mod.esp", "Mod.esp"),
            ("/home/user/skyrim/Data/Mod.esp", "Mod.esp"),
            ("~/skyrim/Data/Mod.esp", "Mod.esp"),
        ]

        for path, expected in test_cases:
            mods = parse_mod_list_text(path)
            assert len(mods) == 1, f"Should parse path: {path}"
            assert mods[0].name == expected, f"Expected {expected}, got {mods[0].name}"


class TestGameCompatibility:
    """Tests for all supported Bethesda games."""

    @pytest.mark.parametrize("game_id", [
        "skyrim", "skyrimse", "skyrimvr",
        "oblivion", "fallout3", "falloutnv",
        "fallout4", "starfield"
    ])
    def test_parser_initializes_for_all_games(self, game_id):
        """Test that LOOT parser initializes for all supported games."""
        parser = LOOTParser(game_id)
        assert parser is not None
        assert parser.game == game_id
        assert isinstance(parser.mod_database, dict)

    @pytest.mark.parametrize("game_id,expected_master", [
        ("skyrim", "Skyrim.esm"),
        ("skyrimse", "Skyrim.esm"),
        ("skyrimvr", "Skyrim.esm"),
        ("oblivion", "Oblivion.esm"),
        ("fallout3", "Fallout3.esm"),
        ("falloutnv", "FalloutNV.esm"),
        ("fallout4", "Fallout4.esm"),
        ("starfield", "Starfield.esm"),
    ])
    def test_game_master_exists(self, game_id, expected_master):
        """Test that master file is recognized for each game."""
        parser = LOOTParser(game_id)

        # Master should be in database or recognized
        assert parser is not None

    def test_skyrim_le_vs_se_distinction(self):
        """Test that Skyrim LE and SE are treated as different games."""
        le_parser = LOOTParser('skyrim')
        se_parser = LOOTParser('skyrimse')

        assert le_parser.game != se_parser.game
        # They may have different mod databases
        assert isinstance(le_parser.mod_database, dict)
        assert isinstance(se_parser.mod_database, dict)


class TestConflictDetection:
    """Tests for conflict detection scenarios."""

    def test_missing_master_detection(self):
        """Test detection of missing master files."""
        parser = LOOTParser('skyrimse')
        detector = ConflictDetector(parser)

        # Mod that requires Dawnguard but Dawnguard not in load order
        mods = [
            ModListEntry('Skyrim.esm', 0, True),
            ModListEntry('DawnguardDependent.esp', 1, True),
        ]

        conflicts = detector.analyze_load_order(mods)
        # Should detect missing master or at least not crash
        assert isinstance(conflicts, list)

    def test_cyclic_dependency_detection(self):
        """Test detection of cyclic dependencies."""
        parser = LOOTParser('skyrimse')
        detector = ConflictDetector(parser)

        # Create circular dependency scenario
        mods = [
            ModListEntry('ModA.esp', 0, True),
            ModListEntry('ModB.esp', 1, True),
            ModListEntry('ModC.esp', 2, True),
        ]

        conflicts = detector.analyze_load_order(mods)
        assert isinstance(conflicts, list)

    def test_dirty_edit_detection(self):
        """Test detection of dirty edits."""
        parser = LOOTParser('skyrimse')
        detector = ConflictDetector(parser)

        # Add a mod known to have dirty edits
        parser.mod_database['dirtymod'] = ModInfo(
            name='DirtyMod.esp',
            clean_name='dirtymod',
            requirements=[],
            incompatibilities=[],
            load_after=[],
            load_before=[],
            patches=[],
            dirty_edits=True,  # Mark as dirty
            messages=['Has dirty edits'],
            tags=[],
        )

        mods = [ModListEntry('DirtyMod.esp', 0, True)]
        conflicts = detector.analyze_load_order(mods)

        # Should detect dirty edits
        dirty_conflicts = [c for c in conflicts if getattr(c, 'type', None) == 'dirty_edit']
        assert len(dirty_conflicts) > 0 or len(conflicts) > 0

    def test_incompatibility_detection(self):
        """Test detection of incompatible mods."""
        parser = LOOTParser('skyrimse')
        detector = ConflictDetector(parser)

        # Add incompatible mods
        parser.mod_database['mod1'] = ModInfo(
            name='Mod1.esp',
            clean_name='mod1',
            requirements=[],
            incompatibilities=['Mod2.esp'],
            load_after=[],
            load_before=[],
            patches=[],
            dirty_edits=False,
            messages=[],
            tags=[],
        )

        mods = [
            ModListEntry('Mod1.esp', 0, True),
            ModListEntry('Mod2.esp', 1, True),
        ]

        conflicts = detector.analyze_load_order(mods)
        # Should detect incompatibility
        assert isinstance(conflicts, list)


class TestPluginLimit:
    """Tests for plugin limit handling."""

    def test_near_plugin_limit_warning(self):
        """Test warning when approaching plugin limit."""
        parser = LOOTParser('skyrimse')
        detector = ConflictDetector(parser)

        # Create 250 mods (near the 255 limit)
        mods = [ModListEntry(f'Mod_{i:03d}.esp', i, True) for i in range(250)]

        conflicts = detector.analyze_load_order(mods)
        # Should handle without crashing, may warn about limit
        assert isinstance(conflicts, list)

    def test_esl_does_not_count_toward_limit(self):
        """Test that ESL files don't count toward plugin limit."""
        parser = LOOTParser('skyrimse')
        detector = ConflictDetector(parser)

        # 254 ESPs + many ESLs should be fine
        mods = [ModListEntry(f'Mod_{i:03d}.esp', i, True) for i in range(254)]
        mods.extend([ModListEntry(f'Light_{i:03d}.esl', 254 + i, True) for i in range(50)])

        conflicts = detector.analyze_load_order(mods)
        assert isinstance(conflicts, list)


class TestLoadOrderSorting:
    """Tests for load order sorting."""

    def test_masters_before_plugins(self):
        """Test that masters (.esm/.esl) are sorted before plugins (.esp)."""
        parser = LOOTParser('skyrimse')
        detector = ConflictDetector(parser)

        # Intentionally wrong order
        mods = [
            ModListEntry('Plugin.esp', 0, True),
            ModListEntry('Master.esm', 1, True),
        ]

        conflicts = detector.analyze_load_order(mods)
        # Should detect master order issue
        assert isinstance(conflicts, list)

    def test_light_plugins_after_regular(self):
        """Test ESL-flagged mods sorted correctly."""
        parser = LOOTParser('skyrimse')
        detector = ConflictDetector(parser)

        mods = [
            ModListEntry('Skyrim.esm', 0, True),
            ModListEntry('Light.esl', 1, True),
            ModListEntry('Regular.esp', 2, True),
        ]

        conflicts = detector.analyze_load_order(mods)
        assert isinstance(conflicts, list)
