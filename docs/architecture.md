# Architecture

## System boundary

This repository is a server-rendered FastAPI analytics application. It loads a versioned CSV data artifact, applies validated dashboard filters, computes analytical view models, and renders a Jinja2 dashboard. It does not own data collection, database persistence, authentication, or model training.

## Layers

```text
HTTP request
    -> app.main (composition root and route adapter)
    -> app.dashboard_service (query validation, filtering, KPI/view-model orchestration)
    -> app.analytics (data loading, normalization, aggregation primitives)
    -> data/Sales Data For Data Analyst Role (1).csv
    -> Jinja2 template + static assets
```

`app.config.Settings` owns environment-driven paths and runtime configuration. `app.dashboard_service.DashboardService` owns application use cases and is testable with an in-memory DataFrame. `app.analytics` contains reusable, side-effect-light analytical primitives. The template layer receives a prepared view model and should not perform data access.

## Design decisions

- The application uses dependency injection for settings and the data frame so tests do not require the production CSV.
- Data normalization and aggregation are separated from HTTP concerns.
- Invalid dates and years are rejected with a user-visible error instead of producing a server traceback.
- Unknown grouping fields are ignored at the request boundary rather than used as arbitrary DataFrame keys.
- The static directory is mounted without mutating the repository during import.
