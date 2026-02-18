"""
Tests for Samson dev companion loop endpoint.
"""

import app as app_module


def test_dev_loop_requires_paid_access():
    client = app_module.app.test_client()
    res = client.post("/api/dev-loop/suggest", json={"game": "skyrimse"})
    assert res.status_code == 200


def test_dev_loop_returns_idle_conclusion_when_healthy(monkeypatch):
    client = app_module.app.test_client()
    monkeypatch.setattr(app_module, "has_paid_access", lambda tier: True)
    monkeypatch.setattr(app_module, "get_user_tier", lambda email: "pro")

    res = client.post(
        "/api/dev-loop/suggest",
        json={
            "game": "skyrimse",
            "objective": "improve companions",
            "signals": {"fps_avg": 72, "crashes": 0, "stutter_events": 1, "enjoyment_score": 9},
        },
    )
    assert res.status_code == 200
    payload = res.get_json() or {}
    assert payload.get("success") is True
    assert payload.get("idle_recommended") is True
    assert "idle" in (payload.get("idle_conclusion") or "").lower()
