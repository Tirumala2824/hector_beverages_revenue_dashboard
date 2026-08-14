# Dynamic Revenue Performance Dashboard (Python + FastAPI)

> **Quick start & file setup**
>
> 1. Clone or download this repository and open a terminal at the project root.
> 2. Create & activate a Python virtual environment (3.9+):
>    ```powershell
>    python -m venv .venv          # first time only
>    .\.venv\Scripts\Activate.ps1   # activate on Windows
>    ```
> 3. Install required packages:
>    ```powershell
>    pip install -r requirements.txt
>    ```
> 4. Make sure your sales CSV is located at `data/Sales Data For Data Analyst Role (1).csv`.
> 5. Launch the FastAPI server:
>    ```powershell
>    uvicorn fastapi_dashboard.main:app --reload
>    ```
> 6. Open a browser and navigate to <http://127.0.0.1:8000/> to view the dashboard.
>
> The sections below describe file layout, data requirements, and user guidance.

This project implements an **interactive, dynamic revenue performance dashboard** using **Python, FastAPI, and Jinja2 templates**, designed to look and behave like a Power BI–style dashboard.

It is built for **commercial and leadership stakeholders** to:

- Track revenue and quantity trends over time
- Analyze **period-over-period revenue growth %** at multiple hierarchy levels
- Drill into **where growth or decline is coming from**
- Distinguish **statistically significant** changes from noise
- Support 3–5 actionable insights for monthly business reviews

---

## 1. Project Structure

```text
.
├─ data/
│  └─ Sales Data For Data Analyst Role (1).csv        # Provided transactional dataset
├─ fastapi_dashboard/
│  ├─ main.py                                        # FastAPI backend + metrics logic
│  ├─ templates/
│  │  └─ dashboard.html                              # Jinja2 template (Power BI–style UI)
│  └─ static/                                        # Static assets (currently empty)
├─ revenue_dashboard/
│  └─ app.py                                         # OPTIONAL: Streamlit version of the dashboard
├─ requirements.txt                                  # Python dependencies
├─ README.md                                         # This documentation
└─ INSIGHTS_TEMPLATE.md                              # 1‑pager insight summary template
```

The **FastAPI + Jinja2** stack is the main implementation; the Streamlit app is kept as an optional alternative.

---

## 2. How to Run the FastAPI Dashboard

### 2.1. Install dependencies

From the project root (`c:/Users/10139565/OneDrive - NTT DATA Business Solutions AG/PraticeFolder/New folder`):

```bash
pip install -r requirements.txt
```

This installs:

- `fastapi`, `uvicorn` – web framework and ASGI server
- `jinja2` – templating engine
- `pandas`, `numpy` – data manipulation
- `streamlit` – only if you want to try the alternative app

### 2.2. Start the FastAPI app

From the same directory:

```bash
uvicorn fastapi_dashboard.main:app --reload
```

Then open in your browser:

```text
http://127.0.0.1:8000/
```

You’ll see a **web dashboard** with:

- Left sidebar for filters and grouping
- Main area with KPI cards, a revenue trend chart, and growth breakdown tables

---

## 3. Data Expectations

The app expects the CSV file:

```text
data/Sales Data For Data Analyst Role (1).csv
```

At minimum, the file must contain:

- `Posting Date` – transaction posting date, parseable as a date
- `Amount` – numeric, transaction value in INR
- `Quantity` – numeric, cases/units sold

Any **additional non-numeric columns** are treated as potential **hierarchy/dimension fields**, for example:

- Geography: `Region`, `Zone`, `Territory`
- Product: `Product Category`, `Brand`, `SKU`
- Channel: `Channel`, `Subchannel`
- Customer: `Customer Segment`, `Customer ID`, etc.

These are **detected automatically** in `fastapi_dashboard/main.py` and exposed in the UI as:

- Grouping options (`Group by` level 1 / 2)
- Dimension filters (multiselect boxes)

### 3.1. Basic cleaning rules

In `fastapi_dashboard/main.py` (`load_sales_data()`):

- `Posting Date` is converted to datetime; rows with invalid/missing posting date are dropped.
- `Amount` and `Quantity` are assumed to be numeric. If they contain nulls, they propagate into derived metrics, but sums remain valid where data is present.
- No hard-coded hierarchy names; any string column (except date/measures) can be used as a level in the hierarchy.

---

## 4. Dashboard User Guide (FastAPI UI)

Open `http://127.0.0.1:8000/` after starting the server.

### 4.1. Sidebar Controls

1. **Time filter (Start date / End date)**  
   - Default: full range of dates present in the dataset.  
   - Use to restrict the analysis window (e.g. last 12–24 months).  
   - Implemented via `start_date` and `end_date` query parameters.

2. **Grouping (dynamic hierarchy)**  
   - `Group by (level 1)` and `Group by (level 2)` are populated from all **dimension columns** detected in the data.
   - You can select:
     - 0 levels → entire portfolio
     - 1 level → e.g., `Region`
     - 2 levels → e.g., `Region` + `Product Category`, or `Channel` + `Customer Segment`
   - Grouping directly determines:
     - Aggregation keys in monthly summaries
     - How Growth % is computed (per group)
     - What appears in the breakdown and “strong growth / decline” tables

   This mimics Power BI’s flexibility of switching between Region, Zone, Territory, Product, Channel, etc.

3. **Dimension filters**  
   - For each dimension with **≤ 50 unique values**:
     - A multi-select dropdown is shown with all distinct values.
     - Use Ctrl/Cmd + click to select multiple.
     - Clear the selection to reset to “All”.
   - This allows flexible cross-filtering:
     - E.g., only `Region = North`, `Channel = Modern Trade`, `Product Category = Beverages`.

The sidebar is rendered from `dimensions_meta` in the template (`fastapi_dashboard/templates/dashboard.html`).

---

### 4.2. Main View

If valid data is available after filters, the main page shows:

1. **KPI Cards (latest month)**

   Calculated in `dashboard()` in `main.py`:

   - **Revenue – Latest Period**
     - Value: `Revenue (INR)` for the most recent `YearMonth` in the filtered data.
     - Delta: `MoM Revenue Growth %` vs the immediately preceding month.

   - **Quantity – Latest Period**
     - Value: `Quantity` for the latest month.
     - Delta: `MoM Quantity Growth %`.

   - **Avg Price per Case**
     - Value: `Revenue / Quantity` for the latest month.

   KPI values are formatted using `format_inr()` and `format_pct()` for clean display.

2. **Revenue Trend Over Time**

   - A **line chart** implemented with Chart.js in `dashboard.html`.
   - X-axis: monthly periods (`YearMonth`).
   - Y-axis: total monthly Revenue.
   - Under the hood, values come from:

     ```python
     ts = (
         monthly.groupby("YearMonth")["Revenue"]
         .sum()
         .reset_index()
         .sort_values("YearMonth")
     )
     ```

   - Labels and values are passed to the template as JSON:
     - `trend_labels_json`
     - `trend_values_json`

3. **Growth Breakdown – Latest Period**

   A table at the selected grouping level(s), with one row per group (e.g., per Region or per Region + Category):

   Columns (see `breakdown_headers`):

   - Grouping columns (0–2: e.g., `Region`, `Product Category`)
   - `Revenue (Curr)` – Revenue in latest month
   - `Revenue (Prev)` – Revenue in previous month for the same group
   - `Δ Revenue` – absolute MoM change (`RevenueGrowthAbs`)
   - `Revenue Growth %` – MoM percentage growth (`RevenueGrowthPct`)
   - `Quantity` – Quantity in latest month
   - `PerformanceBucket` – qualitative label (see below)

4. **Strong Growth & Significant Decline Tables**

   Two compact tables:

   - **Strong growth segments**
     - Groups where `PerformanceBucket` is `"Strong Growth"` or `"Moderate Growth"`
     - Sorted by `Δ Revenue` (descending)
     - Top 20 rows

   - **Significant declines**
     - Groups where `PerformanceBucket` is `"Significant Decline"`
     - Sorted by `Δ Revenue` (ascending)
     - Top 20 rows

These are fed from `strong_rows` and `decline_rows` prepared in `dashboard()`.

5. **Error / empty states**

   - If filters result in no data:
     - Message: “No data for the selected date range and filters.”
   - If aggregation yields no rows:
     - Message: “No aggregated data available for the current selection.”

---

## 5. Metric Definitions & Growth Logic

All core business logic is implemented in `fastapi_dashboard/main.py`, primarily in:

- `aggregate_monthly()`
- The KPI section inside `dashboard()`

### 5.1. Monthly aggregation

```python
work = df.copy()
work["YearMonth"] = work["Posting Date"].dt.to_period("M")

agg_keys = ["YearMonth"] + group_cols
grouped = (
    work.groupby(agg_keys, dropna=False)
    .agg(
        Revenue=("Amount", "sum"),
        Quantity=("Quantity", "sum"),
        TxnCount=("Amount", "size"),
    )
    .reset_index()
)
```

- **YearMonth**: monthly period derived from `Posting Date`.
- **group_cols**: selected group dimensions (`group_by1`, `group_by2`) from the UI.

### 5.2. Base KPIs per group

For each `(YearMonth, group_cols…)` combination:

- **Revenue (INR)**  
  `Revenue = SUM(Amount)`

- **Quantity (cases/units)**  
  `Quantity = SUM(Quantity)`

- **TxnCount (transactions)**  
  `TxnCount = count of rows in the underlying data for that group and month`

- **AvgOrderValue (AOV)**

  ```python
  grouped["AvgOrderValue"] = grouped["Revenue"] / grouped["TxnCount"].replace(0, np.nan)
  ```

- **AvgPricePerCase**

  ```python
  grouped["AvgPricePerCase"] = grouped["Revenue"] / grouped["Quantity"].replace(0, np.nan)
  ```

### 5.3. Period-over-period Revenue Growth (mandatory metric)

For each group:

```python
if group_cols:
    grouped["RevenuePrevPeriod"] = grouped.groupby(group_cols)["Revenue"].shift(1)
else:
    grouped["RevenuePrevPeriod"] = grouped["Revenue"].shift(1)

grouped["RevenueGrowthAbs"] = grouped["Revenue"] - grouped["RevenuePrevPeriod"]
grouped["RevenueGrowthPct"] = grouped["RevenueGrowthAbs"] / grouped["RevenuePrevPeriod"]
```

This exactly reflects:

\[
\text{Growth %} =
\frac{\text{Current Period Revenue} - \text{Previous Period Revenue}}{\text{Previous Period Revenue}}
\]

**Important:**

- Because this is done in a grouped time series per `(YearMonth, group_cols…)`, the same formula works **for any hierarchy level** (Region → Zone → Territory, Category → Brand → SKU, Channel, Segment, etc.).
- This satisfies the **multi-level Growth % indicator requirement**.

### 5.4. KPI cards aggregation

In `dashboard()`:

- Latest month (`latest_period`) is identified as the maximum `YearMonth` present under current filters.
- Previous month is the largest `YearMonth` less than `latest_period`.
- `rev_curr`, `rev_prev`, `rev_delta`, `rev_growth_pct` are computed across **all groups combined** (i.e., grand totals).
- The same is done for quantity to show `Quantity Growth %`.

These feed the KPI cards.

### 5.5. Significance / Performance Buckets

To separate signal from noise:

```python
abs_growth_pct = grouped["RevenueGrowthPct"].abs()
abs_delta = grouped["RevenueGrowthAbs"].abs()

conditions = [
    (grouped["RevenueGrowthPct"] >= 0.10) & (abs_delta >= 5e5),
    (grouped["RevenueGrowthPct"] >= 0.03) & (abs_delta >= 1e5),
    (grouped["RevenueGrowthPct"] <= -0.03) & (abs_delta >= 1e5),
]
choices = ["Strong Growth", "Moderate Growth", "Significant Decline"]

grouped["PerformanceBucket"] = np.select(
    conditions,
    choices,
    default="Minor / Noise",
)
```

Interpretation (tunable thresholds):

- **Strong Growth**  
  - Growth % ≥ 10%  
  - AND |Δ Revenue| ≥ ₹500,000

- **Moderate Growth**  
  - Growth % ≥ 3%  
  - AND |Δ Revenue| ≥ ₹100,000

- **Significant Decline**  
  - Growth % ≤ −3%  
  - AND |Δ Revenue| ≥ ₹100,000

- **Minor / Noise**  
  - Everything else.

Use these to focus leadership on **material** movers.

---

## 6. Assumptions & Edge Cases

- **Time granularity**
  - All analysis is at **monthly** grain, using `YearMonth` derived from `Posting Date`.
  - Daily/weekly views are not implemented to keep the design aligned with monthly business reviews.

- **Incomplete periods**
  - The latest month in the dataset may be **partial**.
  - The dashboard:
    - Always shows which period (`latest_period_label`) is used.
    - Shows the **max data date** at the top (“Data up to YYYY-MM-DD”).
  - You can extend logic to explicitly tag and exclude incomplete months if needed.

- **Null / zero previous period**
  - If a group has no revenue in the previous month (e.g., new product or new territory), `RevenuePrevPeriod` is NaN / 0:
    - `RevenueGrowthPct` becomes NaN and is displayed as `"–"` in the breakdown.
    - Such rows may still appear in the tables but without a meaningful %.

- **High-cardinality dimensions**
  - Only dimensions with ≤ 50 unique values get sidebar filters to avoid overwhelming the UI.
  - You can still group by high-cardinality fields (e.g., SKU) using the Group by selectors.

---



The template is structured to guide you to 3–5 actionable observations and next steps.

---



However, the **FastAPI + Jinja2** implementation is the primary answer to the requirement:

> “in python only look like powerbi dashboard id need use the fastapi and template”

and should be used as the main deliverable.

## Project governance

- Contributions: [`CONTRIBUTING.md`](CONTRIBUTING.md)
- Security reports: [`SECURITY.md`](SECURITY.md)
- License: [`LICENSE`](LICENSE)
- Change history: [`CHANGELOG.md`](CHANGELOG.md)
