"""
Tests for /api/modlist/normalize endpoint.
"""

from app import app


def test_modlist_normalize_requires_input():
    client = app.test_client()
    res = client.post("/api/modlist/normalize", json={"game": "skyrimse"})
    assert res.status_code == 400
    payload = res.get_json() or {}
    assert payload.get("success") is False


def test_modlist_normalize_returns_summary_and_text():
    client = app.test_client()
    res = client.post(
        "/api/modlist/normalize",
        json={"game": "skyrimse", "mod_list": "*Skyrim.esm\nUpdate.esm"},
    )
    assert res.status_code == 200
    payload = res.get_json() or {}
    assert "normalized_text" in payload
    assert "entries" in payload
    assert "summary" in payload
    assert payload["summary"]["total"] == 2
