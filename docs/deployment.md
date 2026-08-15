# Deployment

## Local

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## Configuration

`DASHBOARD_DATA_PATH` points to the CSV data artifact. `DASHBOARD_HOST` and `DASHBOARD_PORT` control the local/server bind. In production, place the data artifact in managed storage or mount it read-only; do not upload sensitive sales data to public repositories.

## Validation

Run `ruff check .`, `python -m compileall -q app tests main.py`, and `pytest`. Before deployment, verify the health of the data artifact, date range, expected columns, static assets, and rendered dashboard.

## Production caveats

The current application is a read-only analytics dashboard backed by a CSV file. It is not yet a multi-user or high-concurrency service. A production expansion should add authentication, data versioning, refresh orchestration, observability, cache strategy, and a durable analytical store before claiming enterprise readiness.
