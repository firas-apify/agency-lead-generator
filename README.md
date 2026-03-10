# Agency Lead Generator

Apify Actor that scrapes agency profile cards from a start URL, with pagination and Apify Proxy support. Extracts agency name, website URL, minimum project size, hourly rate, and location.

## Requirements

- Python 3.11+
- [Poetry](https://python-poetry.org/)

## Setup

```bash
poetry install
```

## Running the Actor

Run the scraper locally (uses Apify input format; for full proxy support run on the Apify platform):

```bash
poetry run python src/main.py
```

Provide input via Apify (e.g. in Console or via API) or by setting `APIFY_INPUT_KEY` / default input. Input schema:

| Input       | Type    | Required | Default | Description                          |
|------------|---------|----------|---------|--------------------------------------|
| `start_url`| string  | Yes      | —       | The URL to start scraping from.      |
| `max_items`| integer | No       | 50      | Maximum number of items to scrape.   |

Results are pushed to the Actor dataset via `Actor.push_data()`.

## Web app (Home + Swagger)

Serve the home page and Swagger API docs locally:

```bash
poetry run uvicorn src.web:app --host 0.0.0.0 --port 8080
```

- **Home:** http://localhost:8080/
- **Swagger UI:** http://localhost:8080/docs
- **ReDoc:** http://localhost:8080/redoc
- **Health:** http://localhost:8080/health

## Docker

Build and run the Actor image:

```bash
docker build -t agency-lead-generator .
docker run -e APIFY_IS_AT_HOME=1 -e APIFY_INPUT_KEY=default agency-lead-generator
```

The Dockerfile uses Python 3.11, Poetry, and runs `src/main.py` by default.

## Run on Apify

To run this Actor on the [Apify platform](https://apify.com):

1. **From GitHub (recommended)**  
   - In [Apify Console](https://console.apify.com/) go to **Actors** → **Create new** → **Import from GitHub**.  
   - Connect your GitHub account, select the `firas-apify/agency-lead-generator` repo (or your fork).  
   - Apify will use the Dockerfile and `.actor/actor.json` to build and run the Actor.  
   - Trigger runs from the Console or via the [Apify API](https://docs.apify.com/api/v2).

2. **Using Apify CLI**  
   - Install the [Apify CLI](https://docs.apify.com/cli) and log in: `apify login`.  
   - From the project root run: `apify push` to build and deploy the Actor to your Apify account.

Input is the same as the schema: `start_url` (required) and `max_items` (optional, default 50). Results are stored in the run’s default dataset.

## Tests

```bash
poetry install
poetry run pytest tests/ -v
```

Tests cover the scraper (parsing, pagination, `run_scraper` with mocked HTTP) and the web API (home, health, input schema, `/run` with mocked scraper).

## Project structure

```
.actor/
  actor.json          # Apify Actor definition (name, version, dockerfile, input)
  INPUT_SCHEMA.json   # Actor input schema (start_url, max_items)
src/
  main.py             # Actor entrypoint: fetch, parse, paginate, push_data
  scraper.py          # Shared scraping logic (retries, backoff, delay)
  web.py              # FastAPI app: home page + Swagger at /docs
tests/
  test_scraper.py     # Scraper and parsing tests
  test_web.py         # Web API tests
Dockerfile
pyproject.toml
poetry.lock
```

## License

This project is licensed under the MIT License — see [LICENSE](LICENSE).

## Code of conduct

We adhere to the Contributor Covenant; see [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
