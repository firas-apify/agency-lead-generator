"""Tests for the scraper module."""

import pytest
from bs4 import BeautifulSoup

from src.scraper import get_next_page_url, parse_provider_cards, run_scraper


# --- parse_provider_cards ---

SAMPLE_HTML_ROWS = """
<div class="provider-row">
    <h3 class="name">Acme Agency</h3>
    <a class="website" href="https://acme.example.com">Website</a>
    <span class="min-project">$10,000</span>
    <span class="hourly-rate">$150/hr</span>
    <span class="location">New York, NY</span>
</div>
<div class="provider-row">
    <h3>Beta Co</h3>
    <a href="https://beta.example.com">Visit</a>
    <span class="budget">$5,000 - $25,000</span>
    <span class="rate">$100/hr</span>
    <span class="address">San Francisco, CA</span>
</div>
<div class="provider-row">
    <h2>Gamma Inc</h2>
    <a href="https://gamma.example.com">Site</a>
    <span class="project-size">$50,000+</span>
    <span class="price">$200/hr</span>
    <span class="region">Remote</span>
</div>
"""


def test_parse_provider_cards_extracts_all_fields():
    soup = BeautifulSoup(SAMPLE_HTML_ROWS, "html.parser")
    results = parse_provider_cards(soup, "https://example.com/page")
    assert len(results) == 3
    assert results[0]["agency_name"] == "Acme Agency"
    assert results[0]["website_url"] == "https://acme.example.com"
    assert results[0]["minimum_project_size"] == "$10,000"
    assert results[0]["hourly_rate"] == "$150/hr"
    assert results[0]["location"] == "New York, NY"
    assert results[1]["agency_name"] == "Beta Co"
    assert results[1]["website_url"] == "https://beta.example.com"
    assert results[1]["minimum_project_size"] == "$5,000 - $25,000"
    assert results[1]["hourly_rate"] == "$100/hr"
    assert results[1]["location"] == "San Francisco, CA"
    assert results[2]["agency_name"] == "Gamma Inc"
    assert results[2]["website_url"] == "https://gamma.example.com"
    assert results[2]["minimum_project_size"] == "$50,000+"
    assert results[2]["hourly_rate"] == "$200/hr"
    assert results[2]["location"] == "Remote"


def test_parse_provider_cards_empty_when_no_rows():
    soup = BeautifulSoup("<div>No provider rows</div>", "html.parser")
    results = parse_provider_cards(soup, "https://example.com")
    assert results == []


# --- get_next_page_url ---

PAGINATION_HTML_REL_NEXT = """
<div class="pagination">
    <a href="/page1">Prev</a>
    <a rel="next" href="/page3">Next</a>
</div>
"""

PAGINATION_HTML_TEXT_NEXT = """
<div class="pagination">
    <a href="/page2">Next</a>
</div>
"""

PAGINATION_HTML_CLASS_NEXT = """
<div class="next">
    <a href="/page4">Next page</a>
</div>
"""

PAGINATION_HTML_NONE = """
<div class="pagination">
    <a href="/page1">Previous</a>
</div>
"""


def test_get_next_page_url_rel_next():
    soup = BeautifulSoup(PAGINATION_HTML_REL_NEXT, "html.parser")
    url = get_next_page_url(soup, "https://example.com/page2")
    assert url == "https://example.com/page3"


def test_get_next_page_url_text_next():
    soup = BeautifulSoup(PAGINATION_HTML_TEXT_NEXT, "html.parser")
    url = get_next_page_url(soup, "https://example.com/page1")
    assert url == "https://example.com/page2"


def test_get_next_page_url_class_next():
    soup = BeautifulSoup(PAGINATION_HTML_CLASS_NEXT, "html.parser")
    url = get_next_page_url(soup, "https://example.com/page3")
    assert url == "https://example.com/page4"


def test_get_next_page_url_returns_none_when_no_next():
    soup = BeautifulSoup(PAGINATION_HTML_NONE, "html.parser")
    url = get_next_page_url(soup, "https://example.com/page1")
    assert url is None


# --- run_scraper (with mocked HTTP) ---


@pytest.mark.asyncio
async def test_run_scraper_respects_max_items():
    from unittest.mock import AsyncMock, MagicMock, patch

    async def fake_get(url):
        resp = MagicMock()
        resp.raise_for_status = lambda: None
        resp.text = """
        <div class="provider-row"><h3>A1</h3><a href="https://a1.com">X</a></div>
        <div class="provider-row"><h3>A2</h3><a href="https://a2.com">X</a></div>
        <div class="provider-row"><h3>A3</h3><a href="https://a3.com">X</a></div>
        """
        return resp

    mock_client = MagicMock()
    mock_client.get = fake_get
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("src.scraper.httpx.AsyncClient", return_value=mock_client):
        items = await run_scraper(
            start_url="https://example.com/agencies",
            max_items=2,
            request_delay=(0, 0),
        )
    assert len(items) == 2
    assert items[0]["agency_name"] == "A1"
    assert items[1]["agency_name"] == "A2"


@pytest.mark.asyncio
async def test_run_scraper_stops_when_no_next():
    from unittest.mock import AsyncMock, MagicMock, patch

    async def fake_get(url):
        resp = MagicMock()
        resp.raise_for_status = lambda: None
        resp.text = '<div class="provider-row"><h3>Only</h3></div>'
        return resp

    mock_client = MagicMock()
    mock_client.get = fake_get
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("src.scraper.httpx.AsyncClient", return_value=mock_client):
        items = await run_scraper(
            start_url="https://example.com/p1",
            max_items=10,
            request_delay=(0, 0),
        )
    assert len(items) == 1
    assert items[0]["agency_name"] == "Only"
