"""
Tests for information discovery and disclosure surfaces.
"""

from app import app


def test_information_map_has_core_sections():
    client = app.test_client()
    res = client.get("/api/information-map")
    assert res.status_code == 200
    payload = res.get_json() or {}
    assert payload.get("success") is True
    assert "inputs" in payload
    assert "processing" in payload
    assert "stores" in payload
    assert "actions" in payload


def test_ai_feed_links_discovery_surfaces():
    client = app.test_client()
    res = client.get("/ai-feed.json")
    assert res.status_code == 200
    payload = res.get_json() or {}
    assert payload.get("api_hub", "").endswith("/api")
    assert payload.get("information_map", "").endswith("/api/information-map")
    assert payload.get("safety_disclosure", "").endswith("/safety")


def test_robots_lists_sitemap():
    client = app.test_client()
    res = client.get("/robots.txt")
    assert res.status_code == 200
    body = res.get_data(as_text=True)
    assert "User-agent: *" in body
    assert "Sitemap:" in body
    assert "/sitemap.xml" in body


def test_sitemap_and_public_hubs_render():
    client = app.test_client()
    sitemap = client.get("/sitemap.xml")
    assert sitemap.status_code == 200
    assert "<urlset" in sitemap.get_data(as_text=True)

    api_page = client.get("/api")
    assert api_page.status_code == 200
    assert "API Hub" in api_page.get_data(as_text=True)

    safety_page = client.get("/safety")
    assert safety_page.status_code == 200
    assert "Safety & Model Constraints" in safety_page.get_data(as_text=True)
