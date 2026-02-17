"""
Tests for OpenClaw safety policy helpers and public safety endpoints.
"""

from app import _openclaw_guard_validate, app


def test_guard_rejects_system_path_segment():
    allowed, reasons = _openclaw_guard_validate("write", "Windows/System32/config.txt", 128)
    assert allowed is False
    assert any("Path segment not allowed" in r for r in reasons)


def test_guard_rejects_shell_like_tokens():
    allowed, reasons = _openclaw_guard_validate("write", "safe/ok;rm -rf.txt", 128)
    assert allowed is False
    assert any("shell-like" in r.lower() for r in reasons)


def test_openclaw_safety_status_endpoint_shape():
    client = app.test_client()
    res = client.get("/api/openclaw/safety-status")
    assert res.status_code == 200
    payload = res.get_json() or {}
    assert payload.get("success") is True
    assert "hardening" in payload
    assert "policy" in payload


def test_openclaw_capabilities_blocks_bios():
    client = app.test_client()
    res = client.get("/api/openclaw/capabilities")
    assert res.status_code == 200
    payload = res.get_json() or {}
    blocked = payload.get("capabilities", {}).get("blocked_hard", [])
    assert any("BIOS" in item or "UEFI" in item for item in blocked)


def test_openclaw_install_manifest_has_permission_contract():
    client = app.test_client()
    res = client.get("/api/openclaw/install-manifest")
    assert res.status_code == 200
    payload = res.get_json() or {}
    required = payload.get("companion", {}).get("required_permissions", [])
    assert any(p.get("scope") == "launch_game" for p in required)

