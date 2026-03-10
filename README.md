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

## Project structure

```
.actor/
  INPUT_SCHEMA.json   # Actor input schema (start_url, max_items)
src/
  main.py             # Actor entrypoint: fetch, parse, paginate, push_data
  web.py              # FastAPI app: home page + Swagger at /docs
Dockerfile
pyproject.toml
poetry.lock
```

## License

This project is licensed under the MIT License — see [LICENSE](LICENSE).

## Code of conduct

We adhere to the Contributor Covenant; see [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
