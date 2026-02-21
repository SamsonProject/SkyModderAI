"""
Tests for game-aware list-builder preference options.
"""

from list_builder import _get_terms_for_pref, get_preference_options


def _keys(options):
    return [row["key"] for row in options]


def test_skyrim_has_character_preferences():
    keys = _keys(get_preference_options("skyrimse"))
    assert "hair" in keys
    assert "body" in keys


def test_fallout4_hides_character_preferences():
    keys = _keys(get_preference_options("fallout4"))
    assert "hair" not in keys
    assert "body" not in keys
    assert "graphics" in keys


def test_starfield_environment_is_scifi_focused():
    options = get_preference_options("starfield")
    env = next(row for row in options if row["key"] == "environment")
    values = {c["value"] for c in env["choices"]}
    assert "sci_fi" in values
    assert "dark_fantasy" not in values
    assert "any" in values


def test_oblivion_and_fallout3_options_exist():
    oblivion_keys = _keys(get_preference_options("oblivion"))
    fallout3_keys = _keys(get_preference_options("fallout3"))
    assert "graphics" in oblivion_keys
    assert "graphics" in fallout3_keys
    assert "hair" not in fallout3_keys


def test_no_skyrim_fallback_terms_for_other_games():
    # Fallout 4 should not inherit Skyrim-only body/hair preferences.
    assert _get_terms_for_pref("fallout4", "hair", "ks_hairdos") == []
