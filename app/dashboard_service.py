from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import pandas as pd

from .analytics import aggregate_data, get_time_grain_column, identify_dimensions, load_sales_data
from .config import Settings


@dataclass(frozen=True)
class DashboardQuery:
    start_date: str | None = None
    end_date: str | None = None
    years: str | None = None
    time_grain: str = "monthly"
    group_by1: str | None = None
    group_by2: str | None = None
    compare_yoy: bool = False
    auto_apply: bool = False
    clear_filters: bool = False


class DashboardService:
    """Application service that turns a validated dashboard query into a view model."""

    def __init__(self, settings: Settings, data_frame: pd.DataFrame | None = None):
        self.settings = settings
        self._data_frame = data_frame

    @property
    def data_frame(self) -> pd.DataFrame:
        if self._data_frame is None:
            self._data_frame = load_sales_data(str(self.settings.data_path))
        return self._data_frame

    def available_metadata(self) -> dict[str, Any]:
        df = self.data_frame
        return {
            "dimension_cols": identify_dimensions(df),
            "available_years": sorted(df["Year"].unique().tolist(), reverse=True),
            "min_date": df["Posting Date"].min().date().isoformat(),
            "max_date": df["Posting Date"].max().date().isoformat(),
        }

    @staticmethod
    def _parse_years(value: str | None) -> list[int]:
        if not value or not value.strip():
            return []
        tokens = [token.strip() for token in value.split(",") if token.strip()]
        if not all(token.isdigit() for token in tokens):
            raise ValueError("Years must be a comma-separated list of integers.")
        return sorted({int(token) for token in tokens})

    @staticmethod
    def _parse_date(value: str | None, fallback: str) -> pd.Timestamp:
        candidate = value or fallback
        timestamp = pd.to_datetime(candidate, errors="coerce")
        if pd.isna(timestamp):
            raise ValueError(f"Invalid date: {candidate}")
        return pd.Timestamp(timestamp)

    @staticmethod
    def _selected_dimensions(
        params: Mapping[str, Any], dimension_cols: list[str]
    ) -> dict[str, list[str]]:
        selected: dict[str, list[str]] = {}
        for column in dimension_cols:
            safe_name = re.sub(r"\W+", "_", column)
            values = params.getlist(f"dim_{safe_name}") if hasattr(params, "getlist") else []
            if isinstance(values, str):
                values = [values]
            if values:
                selected[column] = list(values)
        return selected

    @staticmethod
    def _dimension_metadata(
        df: pd.DataFrame, dimension_cols: list[str], selected: dict[str, list[str]]
    ) -> list[dict[str, Any]]:
        metadata = []
        for column in dimension_cols:
            unique_values = sorted(df[column].dropna().unique().tolist())
            if len(unique_values) <= 50:
                safe_name = re.sub(r"\W+", "_", column)
                metadata.append(
                    {
                        "col": column,
                        "param_key": f"dim_{safe_name}",
                        "dim_values": unique_values,
                        "selected_values": selected.get(column, []),
                    }
                )
        return metadata

    def _empty_context(
        self, query: DashboardQuery, error_message: str | None = None
    ) -> dict[str, Any]:
        metadata = self.available_metadata()
        return {
            **metadata,
            "selected_years": [],
            "time_grain": query.time_grain,
            "compare_yoy": query.compare_yoy,
            "group_by1": query.group_by1 or "",
            "group_by2": query.group_by2 or "",
            "start_date": query.start_date or metadata["min_date"],
            "end_date": query.end_date or metadata["max_date"],
            "auto_apply": query.auto_apply,
            "dimensions_meta": [],
            "kpis": None,
            "error_message": error_message or "No data available for the selected filters.",
        }

    def build_context(self, query: DashboardQuery, params: Mapping[str, Any]) -> dict[str, Any]:
        metadata = self.available_metadata()
        if query.clear_filters:
            query = DashboardQuery(time_grain="monthly")
        selected_years = self._parse_years(query.years)
        start_date = self._parse_date(query.start_date, metadata["min_date"])
        end_date = self._parse_date(query.end_date, metadata["max_date"])
        if start_date > end_date:
            raise ValueError("Start date must be on or before end date.")

        df = self.data_frame
        filtered = df[(df["Posting Date"] >= start_date) & (df["Posting Date"] <= end_date)].copy()
        if selected_years:
            filtered = filtered[filtered["Year"].isin(selected_years)]
        dimension_cols = metadata["dimension_cols"]
        selected_dimensions = (
            self._selected_dimensions(params, dimension_cols) if not query.clear_filters else {}
        )
        for column, values in selected_dimensions.items():
            filtered = filtered[filtered[column].isin(values)]
        dimensions_meta = self._dimension_metadata(filtered, dimension_cols, selected_dimensions)
        if filtered.empty:
            return {
                **self._empty_context(query),
                "selected_years": selected_years,
                "start_date": start_date.date().isoformat(),
                "end_date": end_date.date().isoformat(),
                "dimensions_meta": dimensions_meta,
            }

        group_cols = [
            column
            for column in (query.group_by1, query.group_by2)
            if column and column in dimension_cols
        ]
        group_cols = list(dict.fromkeys(group_cols))
        aggregate = aggregate_data(filtered, group_cols, query.time_grain)
        time_col = get_time_grain_column(filtered, query.time_grain)
        latest_period = aggregate[time_col].max()
        latest = aggregate[aggregate[time_col] == latest_period]
        total_revenue = float(latest["Revenue"].sum())
        total_quantity = float(latest["Quantity"].sum())
        total_transactions = int(latest["TxnCount"].sum())
        previous_revenue = (
            float(latest["RevenuePrevPeriod"].sum())
            if latest["RevenuePrevPeriod"].notna().any()
            else 0.0
        )
        previous_quantity = (
            float(latest["QuantityPrevPeriod"].sum())
            if latest["QuantityPrevPeriod"].notna().any()
            else 0.0
        )

        def pct(current: float, previous: float) -> float:
            return ((current - previous) / previous * 100) if previous else 0.0

        kpis = {
            "revenue_latest": self._format_inr(total_revenue),
            "revenue_growth": self._format_pct(pct(total_revenue, previous_revenue)),
            "quantity_latest": f"{total_quantity:,.0f}",
            "quantity_growth": self._format_pct(pct(total_quantity, previous_quantity)),
            "avg_price": self._format_inr(total_revenue / total_quantity if total_quantity else 0),
            "latest_period_label": str(latest_period),
            "total_txns": f"{total_transactions:,}",
        }
        trend = aggregate.groupby(time_col)["Revenue"].sum().reset_index()
        yoy_data = self._build_yoy(filtered, query.time_grain) if query.compare_yoy else None
        display_rows = [self._display_row(row, group_cols) for _, row in latest.iterrows()]
        strong = (
            latest[latest["PerformanceBucket"].isin(["Strong Growth", "Moderate Growth"])]
            .sort_values("RevenueGrowthAbs", ascending=False)
            .head(20)
        )
        decline = (
            latest[latest["PerformanceBucket"] == "Significant Decline"]
            .sort_values("RevenueGrowthAbs")
            .head(20)
        )
        return {
            **metadata,
            "selected_years": selected_years,
            "time_grain": query.time_grain,
            "compare_yoy": query.compare_yoy,
            "group_by1": query.group_by1 or "",
            "group_by2": query.group_by2 or "",
            "start_date": start_date.date().isoformat(),
            "end_date": end_date.date().isoformat(),
            "auto_apply": query.auto_apply,
            "dimensions_meta": dimensions_meta,
            "kpis": kpis,
            "trend_labels_json": trend[time_col].astype(str).tolist(),
            "trend_values_json": trend["Revenue"].tolist(),
            "yoy_data_json": yoy_data,
            "breakdown_headers": group_cols
            + [
                "Revenue (Curr)",
                "Revenue (Prev)",
                "Δ Revenue",
                "Revenue Growth %",
                "Quantity",
                "PerformanceBucket",
            ],
            "breakdown_rows": display_rows,
            "strong_rows": [self._display_row(row, group_cols) for _, row in strong.iterrows()],
            "decline_rows": [self._display_row(row, group_cols) for _, row in decline.iterrows()],
            "error_message": None,
        }

    @staticmethod
    def _build_yoy(df: pd.DataFrame, time_grain: str) -> dict[str, Any] | None:
        if time_grain not in {"monthly", "quarterly"}:
            return None
        period_column = "YearMonth" if time_grain == "monthly" else "YearQuarter"
        yoy = (
            df.groupby([period_column, "Year"], dropna=False)
            .agg(Revenue=("Amount", "sum"))
            .reset_index()
        )
        pivot = yoy.pivot(index=period_column, columns="Year", values="Revenue").fillna(0)
        return {
            "periods": pivot.index.astype(str).tolist(),
            "years": [int(year) for year in pivot.columns],
            "values": pivot.to_dict(orient="list"),
        }

    @staticmethod
    def _display_row(row: pd.Series, group_cols: list[str]) -> dict[str, Any]:
        result = {
            column: ("-" if pd.isna(row[column]) else str(row[column])) for column in group_cols
        }
        result.update(
            {
                "Revenue (Curr)": DashboardService._format_inr(row["Revenue"]),
                "Revenue (Prev)": DashboardService._format_inr(row["RevenuePrevPeriod"]),
                "Δ Revenue": DashboardService._format_inr(row["RevenueGrowthAbs"]),
                "Revenue Growth %": DashboardService._format_pct(row["RevenueGrowthPct"]),
                "Quantity": f"{row['Quantity']:,.0f}",
                "PerformanceBucket": row["PerformanceBucket"],
            }
        )
        return result

    @staticmethod
    def _format_inr(value: float) -> str:
        if pd.isna(value) or value is None:
            return "₹0"
        absolute = abs(value)
        if absolute >= 1_00_00_000:
            return f"₹{value / 1_00_00_000:.2f}Cr"
        if absolute >= 1_00_000:
            return f"₹{value / 1_00_000:.2f}L"
        if absolute >= 1_000:
            return f"₹{value / 1_000:.2f}K"
        return f"₹{value:,.0f}"

    @staticmethod
    def _format_pct(value: float) -> str:
        return "–" if pd.isna(value) or value is None else f"{value:+.1f}%"
