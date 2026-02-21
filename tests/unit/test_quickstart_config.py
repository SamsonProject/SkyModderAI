"""
Tests for quickstart_config to keep noob onboarding stable.
"""

from quickstart_config import get_all_quickstart, get_quickstart_for_game


def test_quickstart_unknown_game_falls_back():
    data = get_quickstart_for_game("unknown_game")
    assert data["name"] == "Skyrim SE"
    assert "appdata_path" in data
    assert "os_plugin_paths" in data
    assert "linux" in data["os_plugin_paths"]
    assert "mac" in data["os_plugin_paths"]


def test_quickstart_payload_contains_internal_links_and_noob_journey():
    payload = get_all_quickstart()
    assert "internal_links" in payload
    assert "noob_journey" in payload
    assert len(payload["internal_links"]) > 0
    assert len(payload["noob_journey"]) > 0


def test_internal_links_use_site_paths():
    payload = get_all_quickstart()
    for link in payload["internal_links"]:
        assert link["url"].startswith("/")
