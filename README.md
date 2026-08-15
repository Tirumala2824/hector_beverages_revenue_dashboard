# Revenue Performance Dashboard

A FastAPI and pandas dashboard for exploring beverage sales performance across time periods and business dimensions. The project turns a CSV sales artifact into a server-rendered analytical experience with revenue, quantity, transaction, growth, trend, year-over-year, and segment-performance views.

[![CI](https://github.com/Tirumala2824/hector_beverages_revenue_dashboard/actions/workflows/ci.yml/badge.svg)](https://github.com/Tirumala2824/hector_beverages_revenue_dashboard/actions/workflows/ci.yml)

## Why this project exists

This repository demonstrates a production-minded data application boundary: a validated analytical core, an application service that prepares a dashboard view model, a thin HTTP adapter, and a Jinja2 presentation layer. It is intentionally read-only and file-backed; it does not pretend to be a multi-user analytical platform.

## Features

- Revenue, quantity, transaction-count, average-order-value, and price-per-case metrics.
- Daily, ISO year-week, monthly, quarterly, and yearly aggregation.
- Date, year, dimension, and comparison filters.
- Year-over-year comparisons for monthly and quarterly views.
- Segment performance buckets for growth, moderate growth, decline, and new/no-data periods.
- Static dashboard assets and demo material under `static/`.

## Architecture

```text
HTTP request
    -> app.main                 FastAPI composition root and route adapter
    -> app.dashboard_service     Query validation and dashboard view-model orchestration
    -> app.analytics              CSV normalization and analytical primitives
    -> data/*.csv                 Versioned local data artifact
    -> templates/dashboard.html  Jinja2 presentation layer
```

Read [`docs/architecture.md`](docs/architecture.md) for boundaries and design decisions. The service layer is dependency-injected with settings and data frames so the behavior can be tested without launching the web server or relying on the production CSV.

## Technology

Python 3.11, FastAPI, Uvicorn, Jinja2, pandas, NumPy, pytest, and Ruff.

## Installation and local usage

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`. The compatibility command `python main.py` is also supported.

## Configuration

The application reads these variables from the environment:

| Variable | Default | Purpose |
|---|---|---|
| `DASHBOARD_DATA_PATH` | `data/Sales Data For Data Analyst Role (1).csv` | Relative or absolute path to the CSV artifact. |
| `DASHBOARD_HOST` | `127.0.0.1` | Bind host for the local runner. |
| `DASHBOARD_PORT` | `8000` | Bind port for the local runner. |

Do not commit private sales data, credentials, or local environment files. The dataset’s provenance and license must be verified before public redistribution.

## Data contract

The CSV must contain `Posting Date`, `Amount`, and `Quantity`. Dates are parsed with invalid records removed; measure columns are coerced to numeric values; and derived time dimensions are created for year, month, quarter, ISO year-week, year-month, and year-quarter.

## Testing and quality

```bash
ruff check .
python -m compileall -q app tests main.py
pytest
```

Tests cover the data artifact contract, analytics primitives, settings path resolution, dashboard query/service behavior, invalid dates, unsupported grouping boundaries, and application importability.

## Deployment

Read [`docs/deployment.md`](docs/deployment.md) before deploying. The current implementation is a read-only CSV-backed dashboard. A production expansion should add authentication, data versioning, refresh orchestration, observability, cache strategy, and a durable analytical store before claiming enterprise readiness.

## API contract

The dashboard is rendered by `GET /`. Query parameters and validation rules are documented in [`docs/api.md`](docs/api.md).

## Demo assets

The repository includes a storyboard PDF and demo video under `static/`. Keep these assets synchronized with the current UI and verify their licensing before publishing or redistributing them.

## Contributing and security

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for development and pull-request expectations. Report suspected vulnerabilities privately according to [`SECURITY.md`](SECURITY.md). Never submit secrets, personal data, or unlicensed datasets in an issue or pull request.

## License

MIT License. See [`LICENSE`](LICENSE).
