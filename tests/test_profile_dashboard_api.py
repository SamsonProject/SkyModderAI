"""
Tests for profile dashboard API.
"""

from app import SESSION_COOKIE_NAME, app, session_create


def test_profile_dashboard_requires_auth():
    client = app.test_client()
    res = client.get("/api/profile/dashboard")
    assert res.status_code == 401


def test_profile_dashboard_returns_payload_when_logged_in():
    client = app.test_client()
    with app.app_context():
        token, _ = session_create("profile_test@example.com", remember_me=False, user_agent="pytest")
    assert token
    client.set_cookie(SESSION_COOKIE_NAME, token)
    res = client.get("/api/profile/dashboard")
    assert res.status_code == 200
    payload = res.get_json() or {}
    assert payload.get("success") is True
    assert "stats" in payload
    assert "recent_activity" in payload
    assert "suggestions" in payload

