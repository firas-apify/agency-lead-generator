"""
Web server: home page and Swagger API docs.
Run with: uvicorn src.web:app --host 0.0.0.0 --port 8080
"""
import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel, Field

from src.scraper import run_scraper

app = FastAPI(
    title="Agency Lead Generator",
    description="Apify Actor for scraping agency profiles (name, website, rates, location).",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    openapi_schema["info"]["x-logo"] = {"url": "https://apify.com/favicon.ico"}
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


class ActorRunInput(BaseModel):
    """Input for the Agency Lead Generator Actor (same as Apify input schema)."""

    start_url: str = Field(..., description="The URL to start scraping from.")
    max_items: int = Field(50, ge=1, description="Maximum number of items to scrape.")


class AgencyItem(BaseModel):
    """A single scraped agency profile."""

    agency_name: str | None = None
    website_url: str | None = None
    minimum_project_size: str | None = None
    hourly_rate: str | None = None
    location: str | None = None


class ActorRunResponse(BaseModel):
    """Response from the run endpoint."""

    count: int = Field(..., description="Number of items scraped.")
    items: list[AgencyItem] = Field(..., description="Scraped agency profiles.")


HOME_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Agency Lead Generator</title>
    <link rel="icon" href="/favicon.ico" type="image/png">
    <style>
        * { box-sizing: border-box; }
        body { font-family: system-ui, -apple-system, sans-serif; margin: 0; padding: 2rem; background: #f5f5f5; }
        .card { max-width: 640px; margin: 0 auto; background: #fff; border-radius: 12px; padding: 2rem; box-shadow: 0 2px 8px rgba(0,0,0,.08); }
        h1 { margin: 0 0 0.5rem; color: #111; }
        p { color: #444; line-height: 1.6; margin: 0 0 1rem; }
        a { color: #e6522f; text-decoration: none; font-weight: 500; }
        a:hover { text-decoration: underline; }
        ul { margin: 0; padding-left: 1.25rem; }
        li { margin-bottom: 0.5rem; }
    </style>
</head>
<body>
    <div class="card">
        <h1>Agency Lead Generator</h1>
        <p>Apify Actor that scrapes agency profile cards from a start URL, with pagination and Apify Proxy support.</p>
        <p><strong>Links</strong></p>
        <ul>
            <li><a href="/docs">Swagger UI</a> — interactive API documentation</li>
            <li><a href="/redoc">ReDoc</a> — alternative API docs</li>
            <li><a href="/openapi.json">OpenAPI schema</a> — raw JSON</li>
            <li><a href="/health">Health check</a></li>
        </ul>
    </div>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse, tags=["General"])
async def home():
    """Home page with links to Swagger and API docs."""
    return HOME_HTML


@app.get("/health", tags=["General"])
async def health():
    """Health check for deployments and load balancers."""
    return {"status": "ok"}


_FAVICON_PATH = Path(__file__).resolve().parent.parent / "static" / "favicon.png"


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """Serve the site favicon."""
    if _FAVICON_PATH.exists():
        return FileResponse(_FAVICON_PATH, media_type="image/png")
    raise HTTPException(status_code=404, detail="Not found")


def _load_input_schema() -> dict:
    path = Path(__file__).resolve().parent.parent / ".actor" / "INPUT_SCHEMA.json"
    if path.exists():
        return json.loads(path.read_text())
    return {
        "title": "Agency Lead Generator input",
        "type": "object",
        "schemaVersion": 1,
        "properties": {
            "start_url": {"title": "Start URL", "type": "string", "description": "The URL to start scraping from."},
            "max_items": {"title": "Max items", "type": "integer", "default": 50, "minimum": 1, "description": "Maximum number of items to scrape."},
        },
        "required": ["start_url"],
    }


@app.get("/input-schema", tags=["Actor"])
async def get_input_schema():
    """
    Return the Apify Actor input schema (same as .actor/INPUT_SCHEMA.json).
    Use this to integrate with Apify Console or API clients.
    """
    return _load_input_schema()


@app.post("/run", response_model=ActorRunResponse, tags=["Actor"])
async def run_actor(body: ActorRunInput):
    """
    Run the Agency Lead Generator: scrape agency profiles from the given start URL
    with pagination until max_items is reached or no more pages exist.
    Returns the list of scraped items.
    """
    try:
        items = await run_scraper(
            start_url=body.start_url,
            max_items=body.max_items,
            proxy_url=None,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Scraper error: {e!s}") from e
    return ActorRunResponse(count=len(items), items=[AgencyItem(**i) for i in items])
