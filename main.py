from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

import json

import numpy as np
import pandas as pd
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = BASE_DIR /  "data" / "Sales Data For Data Analyst Role (1).csv"

app = FastAPI(title="Revenue Performance Dashboard (FastAPI)")

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@lru_cache()
def load_sales_data() -> pd.DataFrame:
    """
    Load the transactional sales data and derive standard time attributes.
    """
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Data file not found at {DATA_PATH}")

    df = pd.read_csv(DATA_PATH)

    required_cols = {"Posting Date", "Amount", "Quantity"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"CSV is missing required columns: {', '.join(sorted(missing))}")

    df["Posting Date"] = pd.to_datetime(df["Posting Date"], errors="coerce")
    df = df.dropna(subset=["Posting Date"])
    
    # Extract time dimensions for multi-year analysis
    df["Year"] = df["Posting Date"].dt.year
    df["Month"] = df["Posting Date"].dt.month
    df["Quarter"] = df["Posting Date"].dt.quarter
    df["YearMonth"] = df["Posting Date"].dt.to_period("M").astype(str)
    df["YearQuarter"] = df["Posting Date"].dt.to_period("Q").astype(str)
    df["Week"] = df["Posting Date"].dt.isocalendar().week

    return df


def identify_dimensions(df: pd.DataFrame) -> List[str]:
    """
    Identify candidate dimension / hierarchy fields automatically.
    """
    exclude_cols = {"Posting Date", "Year", "Month", "Quarter", "YearMonth", "YearQuarter", "Week"}
    measure_cols = {"Amount", "Quantity"}

    dims: List[str] = []
    for col in df.columns:
        if col in exclude_cols or col in measure_cols:
            continue
        if pd.api.types.is_numeric_dtype(df[col]):
            continue
        dims.append(col)
    return dims


def format_inr(value: float) -> str:
    """Format number as INR currency."""
    if pd.isna(value) or value is None:
        return "₹0"
    abs_val = abs(value)
    if abs_val >= 1_00_00_000:  # Crore
        return f"₹{value/1_00_00_000:.2f}Cr"
    elif abs_val >= 1_00_000:  # Lakh
        return f"₹{value/1_00_000:.2f}L"
    elif abs_val >= 1_000:  # Thousand
        return f"₹{value/1_000:.2f}K"
    else:
        return f"₹{value:,.0f}"


def format_pct(value: float) -> str:
    """Format percentage."""
    if pd.isna(value) or value is None:
        return "–"
    return f"{value:+.1f}%"


def get_time_grain_column(df: pd.DataFrame, time_grain: str) -> str:
    """Get the appropriate time column based on grain."""
    grain_map = {
        "daily": "Posting Date",
        "weekly": "Week",
        "monthly": "YearMonth",
        "quarterly": "YearQuarter",
        "yearly": "Year"
    }
    return grain_map.get(time_grain, "YearMonth")


def aggregate_data(df: pd.DataFrame, group_cols: List[str], time_grain: str = "monthly") -> pd.DataFrame:
    """
    Aggregate data based on time grain and grouping columns.
    """
    time_col = get_time_grain_column(df, time_grain)
    
    agg_cols = [time_col] + group_cols if group_cols else [time_col]
    
    agg_df = (
        df.groupby(agg_cols)
        .agg(
            Revenue=("Amount", "sum"),
            Quantity=("Quantity", "sum"),
            TxnCount=("Amount", "count"),
        )
        .reset_index()
    )
    
    agg_df["AvgOrderValue"] = agg_df["Revenue"] / agg_df["TxnCount"]
    agg_df["AvgPricePerCase"] = agg_df["Revenue"] / agg_df["Quantity"].replace(0, np.nan)
    
    # Sort by time
    agg_df = agg_df.sort_values(by=[time_col] + group_cols)
    
    # Calculate period-over-period growth for revenue and quantity
    if group_cols:
        agg_df["RevenuePrevPeriod"] = agg_df.groupby(group_cols)["Revenue"].shift(1)
        agg_df["QuantityPrevPeriod"] = agg_df.groupby(group_cols)["Quantity"].shift(1)
    else:
        agg_df["RevenuePrevPeriod"] = agg_df["Revenue"].shift(1)
        agg_df["QuantityPrevPeriod"] = agg_df["Quantity"].shift(1)
    
    agg_df["RevenueGrowthAbs"] = agg_df["Revenue"] - agg_df["RevenuePrevPeriod"]
    agg_df["RevenueGrowthPct"] = (agg_df["RevenueGrowthAbs"] / agg_df["RevenuePrevPeriod"].replace(0, np.nan)) * 100
    # Quantity growth for display in KPIs may be computed later as needed
    
    # Performance bucketing
    def bucket_performance(row):
        pct = row["RevenueGrowthPct"]
        abs_change = abs(row["RevenueGrowthAbs"])
        
        if pd.isna(pct):
            return "New/No Data"
        if pct >= 10 and abs_change >= 500000:
            return "Strong Growth"
        elif pct >= 3 and abs_change >= 100000:
            return "Moderate Growth"
        elif pct <= -3 and abs_change >= 100000:
            return "Significant Decline"
        else:
            return "Minor/Noise"
    
    agg_df["PerformanceBucket"] = agg_df.apply(bucket_performance, axis=1)
    
    return agg_df


@app.get("/", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    years: Optional[str] = "",  # Comma-separated years
    time_grain: str = "monthly",  # daily, weekly, monthly, quarterly, yearly
    group_by1: Optional[str] = None,
    group_by2: Optional[str] = None,
    compare_yoy: bool = False,  # Year-over-year comparison
    auto_apply: bool = False,
    clear_filters: bool = False,
):

    # Load data
    df = load_sales_data()
    
    # Get available years from data
    available_years = sorted(df["Year"].unique().tolist(), reverse=True)
    min_date = df["Posting Date"].min().date()
    max_date = df["Posting Date"].max().date()
    
    # Handle clear filters
    if clear_filters:
        start_date = min_date.isoformat()
        end_date = max_date.isoformat()
        years = None
        time_grain = "monthly"
        group_by1 = None
        group_by2 = None
        compare_yoy = False
        auto_apply = False
    
    # Set defaults
    if not start_date:
        start_date = min_date.isoformat()
    if not end_date:
        end_date = max_date.isoformat()
    
    # Parse years filter (comma-separated string of integers)
    selected_years: List[int] = []
    if years and years.strip():
        # allow either comma separated or single value
        for token in years.split(","):
            token = token.strip()
            if token.isdigit():
                selected_years.append(int(token))

    
    # Apply date filter
    start_dt = pd.Timestamp(start_date)
    end_dt = pd.Timestamp(end_date)
    base_df = df[(df["Posting Date"] >= start_dt) & (df["Posting Date"] <= end_dt)].copy()
    
    # Apply year filter if specified
    if selected_years:
        base_df = base_df[base_df["Year"].isin(selected_years)]
    
    if base_df.empty:
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "error_message": "No data available for the selected filters.",
            "dimension_cols": identify_dimensions(df),
            "dimensions_meta": [],
            "available_years": available_years,
            "selected_years": selected_years,
            "time_grain": time_grain,
            "compare_yoy": compare_yoy,
            "group_by1": group_by1 or "",
            "group_by2": group_by2 or "",
            "start_date": start_date,
            "end_date": end_date,
            "min_date": min_date.isoformat(),
            "max_date": max_date.isoformat(),
            "auto_apply": auto_apply,
            "kpis": None,
        })
    
    # Identify dimensions for filters
    dimension_cols = identify_dimensions(df)
    
    # Build dimension filter metadata
    dimensions_meta: List[Dict[str, Any]] = []
    # use QueryParams directly so we can call getlist; if clear_filters ignore existing params
    qp = {} if clear_filters else request.query_params
    import re
    for col in dimension_cols:
        unique_vals = sorted(base_df[col].dropna().unique().tolist())
        if len(unique_vals) <= 50:  # Only show dimensions with reasonable cardinality
            # sanitize column name for HTML/URL use
            safe = re.sub(r"\W+", "_", col)
            param_key = f"dim_{safe}"
            # getlist returns a list of values for repeated parameters
            selected = qp.getlist(param_key) if hasattr(qp, "getlist") else []
            if isinstance(selected, str):
                selected = [selected]
            elif not isinstance(selected, list):
                selected = []

            dimensions_meta.append({
                "col": col,
                "param_key": param_key,
                "dim_values": unique_vals,
                "selected_values": selected,
            })

            # Apply dimension filter
            if selected:
                base_df = base_df[base_df[col].isin(selected)]

    
    # Determine grouping columns
    group_cols = []
    if group_by1:
        group_cols.append(group_by1)
    if group_by2 and group_by2 != group_by1:
        group_cols.append(group_by2)
    
    # Aggregate data
    agg_df = aggregate_data(base_df, group_cols, time_grain)
    
    # Calculate KPIs
    time_col = get_time_grain_column(base_df, time_grain)
    latest_period = agg_df[time_col].max()
    latest_df = agg_df[agg_df[time_col] == latest_period]
    
    total_revenue = latest_df["Revenue"].sum()
    total_quantity = latest_df["Quantity"].sum()
    total_txns = latest_df["TxnCount"].sum()
    
    prev_revenue = latest_df["RevenuePrevPeriod"].sum()
    revenue_growth_pct = ((total_revenue - prev_revenue) / prev_revenue * 100) if prev_revenue else 0
    
    prev_quantity = latest_df.get("QuantityPrevPeriod", pd.Series(dtype="float64")).sum()
    quantity_growth_pct = ((total_quantity - prev_quantity) / prev_quantity * 100) if prev_quantity else 0
    
    avg_price = total_revenue / total_quantity if total_quantity else 0
    
    # Format KPIs
    kpis = {
        "revenue_latest": format_inr(total_revenue),
        "revenue_growth": format_pct(revenue_growth_pct),
        "quantity_latest": f"{total_quantity:,.0f}",
        "quantity_growth": format_pct(quantity_growth_pct),
        "avg_price": format_inr(avg_price),
        "latest_period_label": str(latest_period),
        "total_txns": f"{total_txns:,}",
    }
    
    # Prepare trend data
    trend_df = agg_df.groupby(time_col)["Revenue"].sum().reset_index()
    # ensure labels are strings for javascript
    trend_labels = trend_df[time_col].astype(str).tolist()
    trend_values = trend_df["Revenue"].tolist()
    
    # Year-over-year comparison data
    yoy_data = None
    if compare_yoy and time_grain in ["monthly", "quarterly"]:
        if time_grain == "monthly":
            base_df["ComparePeriod"] = base_df["Year"].astype(str) + "-" + base_df["Month"].astype(str).str.zfill(2)
        else:
            base_df["ComparePeriod"] = base_df["Year"].astype(str) + "-Q" + base_df["Quarter"].astype(str)

        yoy_agg = (
            base_df
            .groupby(["ComparePeriod", "Year"])
            .agg(Revenue=("Amount", "sum"))
            .reset_index()
        )
        yoy_pivot = yoy_agg.pivot(index="ComparePeriod", columns="Year", values="Revenue").fillna(0)
        yoy_data = {
            "periods": yoy_pivot.index.tolist(),
            "years": yoy_pivot.columns.tolist(),
            "values": yoy_pivot.to_dict(orient="list")
        }
    
    # Prepare breakdown data
    breakdown_headers = group_cols + [
        "Revenue (Curr)",
        "Revenue (Prev)",
        "Δ Revenue",
        "Revenue Growth %",
        "Quantity",
        "PerformanceBucket",
    ]
    
    def row_to_display(row: pd.Series) -> Dict[str, Any]:
        d: Dict[str, Any] = {}
        for col in group_cols:
            val = row[col]
            d[col] = "-" if pd.isna(val) else str(val)
        
        d["Revenue (Curr)"] = format_inr(row["Revenue"])
        d["Revenue (Prev)"] = format_inr(row["RevenuePrevPeriod"])
        d["Δ Revenue"] = format_inr(row["RevenueGrowthAbs"])
        d["Revenue Growth %"] = format_pct(row["RevenueGrowthPct"])
        d["Quantity"] = f"{row['Quantity']:,.0f}"
        d["PerformanceBucket"] = row["PerformanceBucket"]
        return d
    
    # Get latest period breakdown
    latest_rows_df = agg_df[agg_df[time_col] == latest_period].copy()
    breakdown_rows = [row_to_display(r) for _, r in latest_rows_df.iterrows()]
    
    # Strong growth segments
    strong_df = latest_rows_df[
        latest_rows_df["PerformanceBucket"].isin(["Strong Growth", "Moderate Growth"])
    ].sort_values("RevenueGrowthAbs", ascending=False).head(20)
    strong_rows = [row_to_display(r) for _, r in strong_df.iterrows()]
    
    # Significant declines
    decline_df = latest_rows_df[
        latest_rows_df["PerformanceBucket"] == "Significant Decline"
    ].sort_values("RevenueGrowthAbs", ascending=True).head(20)
    decline_rows = [row_to_display(r) for _, r in decline_df.iterrows()]
    
    context = {
        "request": request,
        "dimension_cols": dimension_cols,
        "dimensions_meta": dimensions_meta,
        "available_years": available_years,
        "selected_years": selected_years,
        "time_grain": time_grain,
        "compare_yoy": compare_yoy,
        "group_by1": group_by1 or "",
        "group_by2": group_by2 or "",
        "start_date": start_date,
        "end_date": end_date,
        "min_date": min_date.isoformat(),
        "max_date": max_date.isoformat(),
        "auto_apply": auto_apply,
        "kpis": kpis,
        "trend_labels_json": json.dumps(trend_labels),
        "trend_values_json": json.dumps(trend_values),
        "yoy_data_json": json.dumps(yoy_data) if yoy_data is not None else "null",
        "breakdown_headers": breakdown_headers,
        "breakdown_rows": breakdown_rows,
        "strong_rows": strong_rows,
        "decline_rows": decline_rows,
        "error_message": None,
    }
    
    return templates.TemplateResponse("dashboard.html", context)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
