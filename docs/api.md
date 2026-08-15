# API and query contract

## `GET /`

Renders the dashboard. Supported query parameters are `start_date`, `end_date` (ISO date strings), `years` (comma-separated integer years), `time_grain` (`daily`, `weekly`, `monthly`, `quarterly`, or `yearly`), `group_by1`, `group_by2`, `compare_yoy`, `auto_apply`, and `clear_filters`.

The route validates dates and years, restricts grouping fields to discovered dimensions, and returns an explanatory empty-state message when filters match no records. The HTML response includes prepared KPI, trend, year-over-year, breakdown, growth, and decline view models for the template.

## Data contract

The CSV must include `Posting Date`, `Amount`, and `Quantity`. Invalid dates and non-numeric measures are removed during normalization. The repository’s tests cover missing artifacts, header presence, analytics aggregation, query validation, and application importability.
