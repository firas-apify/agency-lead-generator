"""Tests for the web API."""

import pytest
from fastapi.testclient import TestClient

from src.web import app


client = TestClient(app)


def test_home_returns_html():
    r = client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "Agency Lead Generator" in r.text
    assert "/docs" in r.text


def test_health_returns_ok():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_input_schema_returns_schema():
    r = client.get("/input-schema")
    assert r.status_code == 200
    data = r.json()
    assert data.get("schemaVersion") == 1
    assert "start_url" in data.get("properties", {})
    assert "max_items" in data.get("properties", {})
    assert "start_url" in data.get("required", [])


def test_favicon_returns_200_or_404():
    r = client.get("/favicon.ico")
    assert r.status_code in (200, 404)


def test_run_requires_start_url():
    r = client.post("/run", json={})
    assert r.status_code == 422


def test_run_returns_items_when_scraper_mocked():
    from unittest.mock import AsyncMock, patch

    mock_items = [
        {"agency_name": "Agency A", "website_url": "https://a.com", "minimum_project_size": None, "hourly_rate": "$100", "location": "NYC"},
    ]
    with patch("src.web.run_scraper", new_callable=AsyncMock, return_value=mock_items):
        r = client.post(
            "/run",
            json={"start_url": "https://example.com/agencies", "max_items": 10},
        )
    assert r.status_code == 200
    data = r.json()
    assert data["count"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["agency_name"] == "Agency A"
    assert data["items"][0]["website_url"] == "https://a.com"
