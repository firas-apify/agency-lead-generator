"""
Shared scraping logic: fetch pages, parse .provider-row cards, paginate.
Used by both the Apify Actor (main.py) and the web API (web.py).
"""
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup


def _text(soup_element) -> str | None:
    if soup_element is None:
        return None
    t = soup_element.get_text(strip=True)
    return t or None


def _attr(soup_element, attr: str) -> str | None:
    if soup_element is None:
        return None
    return soup_element.get(attr)


def parse_provider_cards(soup: BeautifulSoup, page_url: str) -> list[dict]:
    """Find .provider-row cards and extract agency fields."""
    rows = soup.select(".provider-row")
    results = []

    for row in rows:
        name_el = (
            row.select_one("h2, h3")
            or row.select_one(".name, .agency-name, .provider-name, .company-name")
            or row.select_one("a[href]")
        )
        agency_name = _text(name_el)

        website_url = None
        for a in row.select('a[href^="http"]'):
            if "website" in (a.get("class") or []) or "website" in (a.get_text() or "").lower():
                website_url = _attr(a, "href")
                break
        if not website_url:
            first_link = row.select_one('a[href^="http"]')
            website_url = _attr(first_link, "href") if first_link else None

        minimum_project_size = _text(row.select_one(".min-project, .project-size, .budget, [data-min-project]"))
        if not minimum_project_size:
            for label in ("min project", "minimum project", "project size", "min. budget", "budget"):
                el = row.find(string=lambda t: t and label in (t or "").lower())
                if el and el.parent:
                    n = el.parent.find_next()
                    if n:
                        minimum_project_size = _text(n)
                    break

        rate_el = row.select_one(".rate, .hourly-rate, .hourly, [data-rate], .price")
        hourly_rate = _text(rate_el)

        location_el = row.select_one(".location, .location-name, .address, [data-location], .region")
        location = _text(location_el)

        results.append({
            "agency_name": agency_name,
            "website_url": website_url,
            "minimum_project_size": minimum_project_size,
            "hourly_rate": hourly_rate,
            "location": location,
        })

    return results


def get_next_page_url(soup: BeautifulSoup, current_url: str) -> str | None:
    """Return absolute URL for the Next pagination link, or None."""
    next_link = soup.select_one('a[rel="next"]')
    if not next_link:
        next_link = soup.find("a", string=lambda t: t and t.strip().lower() == "next")
    if not next_link:
        next_link = soup.select_one(".next a, .pagination .next, a.next")
    if not next_link:
        for a in soup.select("a"):
            if a.get_text(strip=True).lower() == "next":
                next_link = a
                break
    if next_link and next_link.get("href"):
        return urljoin(current_url, next_link["href"])
    return None


async def run_scraper(
    start_url: str,
    max_items: int = 50,
    proxy_url: str | None = None,
) -> list[dict]:
    """
    Scrape agency profile cards from start_url with pagination.
    Returns a list of dicts with keys: agency_name, website_url,
    minimum_project_size, hourly_rate, location.
    """
    items: list[dict] = []
    current_url = start_url

    async with httpx.AsyncClient(
        proxy=proxy_url,
        follow_redirects=True,
        timeout=30.0,
        headers={"User-Agent": "Mozilla/5.0 (compatible; Apify Agency Lead Generator)"},
    ) as client:
        while current_url and len(items) < max_items:
            try:
                response = await client.get(current_url)
                response.raise_for_status()
            except httpx.HTTPError:
                break

            soup = BeautifulSoup(response.text, "html.parser")
            cards = parse_provider_cards(soup, current_url)

            for item in cards:
                if len(items) >= max_items:
                    break
                items.append(item)

            if len(items) >= max_items:
                break

            next_url = get_next_page_url(soup, current_url)
            if not next_url or next_url == current_url:
                break
            current_url = next_url

    return items
