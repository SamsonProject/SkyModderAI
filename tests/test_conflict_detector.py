"""
Tests for conflict_detector: parse_mod_list_text, ModListEntry, ConflictDetector.
"""
from conflict_detector import ConflictDetector, ModListEntry, parse_mod_list_text
from loot_parser import LOOTParser, ModInfo


class TestParseModListText:
    """Tests for parse_mod_list_text."""

    def test_plugins_txt_enabled(self):
        text = "*Skyrim.esm\n*Update.esm\n*Dawnguard.esm"
        mods = parse_mod_list_text(text)
        assert len(mods) == 3
        assert all(m.enabled for m in mods)
        assert mods[0].name == "Skyrim.esm"
        assert mods[1].name == "Update.esm"

    def test_plugins_txt_disabled(self):
        text = "*Skyrim.esm\nUpdate.esm\n*Dawnguard.esm"
        mods = parse_mod_list_text(text)
        assert len(mods) == 3
        assert mods[0].enabled is True
        assert mods[1].enabled is False
        assert mods[2].enabled is True

    def test_mo2_format(self):
        text = "+Unofficial Skyrim Special Edition Patch.esp\n-DisabledMod.esp"
        mods = parse_mod_list_text(text)
        assert len(mods) == 2
        assert mods[0].enabled is True
        assert mods[0].name == "Unofficial Skyrim Special Edition Patch.esp"
        assert mods[1].enabled is False

    def test_comments_skipped(self):
        text = "# comment\n*Skyrim.esm\n# another\n*Update.esm"
        mods = parse_mod_list_text(text)
        assert len(mods) == 2

    def test_empty_lines_skipped(self):
        text = "*Skyrim.esm\n\n\n*Update.esm"
        mods = parse_mod_list_text(text)
        assert len(mods) == 2

    def test_path_extraction(self):
        text = "C:/Games/Skyrim/Data/Skyrim.esm"
        mods = parse_mod_list_text(text)
        assert len(mods) == 1
        assert mods[0].name == "Skyrim.esm"

    def test_vortex_plain_all_enabled(self):
        text = "Skyrim.esm\nUpdate.esm"
        mods = parse_mod_list_text(text)
        assert len(mods) == 2
        # Without * prefix and no plugins.txt format, all enabled
        assert mods[0].enabled is True
        assert mods[1].enabled is True


class TestConflictDetector:
    """Tests for ConflictDetector with mock parser."""

    def test_unknown_mod_info(self):
        """Mod not in database gets info-level conflict."""
        parser = LOOTParser("skyrimse")
        parser.mod_database = {}  # empty
        detector = ConflictDetector(parser)
        mods = [ModListEntry("UnknownMod.esp", 0, True)]
        conflicts = detector.analyze_load_order(mods)
        assert len(conflicts) == 1
        assert conflicts[0].type == "unknown_mod"
        assert conflicts[0].severity == "info"

    def test_missing_requirement(self):
        """Mod with missing requirement gets error."""
        parser = LOOTParser("skyrimse")
        # Key must match _normalize_name("NeedsSKSE.esp") -> "needsskse"
        parser.mod_database = {
            "needsskse": ModInfo(
                name="NeedsSKSE.esp",
                clean_name="needsskse",
                requirements=["SKSE"],
                incompatibilities=[],
                load_after=[],
                load_before=[],
                patches=[],
                dirty_edits=False,
                messages=[],
                tags=[],
            )
        }
        detector = ConflictDetector(parser)
        mods = [ModListEntry("NeedsSKSE.esp", 0, True)]
        conflicts = detector.analyze_load_order(mods)
        assert any(c.type == "missing_requirement" for c in conflicts)
