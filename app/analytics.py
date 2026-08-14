from functools import lru_cache
from pathlib import Path
from typing import List, Union

import numpy as np
import pandas as pd

REQUIRED_COLUMNS = {"Posting Date", "Amount", "Quantity"}
TIME_COLUMNS = {"Posting Date", "Year", "Month", "Quarter", "YearMonth", "YearQuarter", "YearWeek", "Week"}

@lru_cache(maxsize=1)
def load_sales_data(data_path: Union[str, Path]) -> pd.DataFrame:
    path = Path(data_path)
    if not path.exists():
        raise FileNotFoundError(f"Data file not found at {path}")
    df = pd.read_csv(path)
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"CSV is missing required columns: {', '.join(sorted(missing))}")
    df = df.copy()
    df["Posting Date"] = pd.to_datetime(df["Posting Date"], errors="coerce")
    df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce")
    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce")
    df = df.dropna(subset=["Posting Date", "Amount", "Quantity"])
    df["Year"] = df["Posting Date"].dt.year
    df["Month"] = df["Posting Date"].dt.month
    df["Quarter"] = df["Posting Date"].dt.quarter
    df["YearMonth"] = df["Posting Date"].dt.to_period("M").astype(str)
    df["YearQuarter"] = df["Posting Date"].dt.to_period("Q").astype(str)
    df["YearWeek"] = df["Posting Date"].dt.strftime("%G-W%V")
    df["Week"] = df["Posting Date"].dt.isocalendar().week.astype(int)
    return df

def identify_dimensions(df: pd.DataFrame) -> List[str]:
    return [c for c in df.columns if c not in TIME_COLUMNS | {"Amount", "Quantity"} and not pd.api.types.is_numeric_dtype(df[c])]

def format_inr(value: float) -> str:
    if pd.isna(value) or value is None: return "₹0"
    absolute = abs(value)
    if absolute >= 1_00_00_000: return f"₹{value/1_00_00_000:.2f}Cr"
    if absolute >= 1_00_000: return f"₹{value/1_00_000:.2f}L"
    if absolute >= 1_000: return f"₹{value/1_000:.2f}K"
    return f"₹{value:,.0f}"

def format_pct(value: float) -> str:
    return "–" if pd.isna(value) or value is None else f"{value:+.1f}%"

def get_time_grain_column(df: pd.DataFrame, time_grain: str) -> str:
    mapping={"daily":"Posting Date","weekly":"YearWeek","monthly":"YearMonth","quarterly":"YearQuarter","yearly":"Year"}
    column=mapping.get(time_grain)
    if column is None or column not in df.columns: raise ValueError(f"Unsupported time grain: {time_grain}")
    return column

def aggregate_data(df: pd.DataFrame, group_cols: List[str], time_grain: str = "monthly") -> pd.DataFrame:
    time_col=get_time_grain_column(df,time_grain)
    invalid=[c for c in group_cols if c not in df.columns or c in TIME_COLUMNS]
    if invalid: raise ValueError(f"Invalid grouping columns: {invalid}")
    group=[time_col]+group_cols
    result=(df.groupby(group, dropna=False).agg(Revenue=("Amount","sum"),Quantity=("Quantity","sum"),TxnCount=("Amount","count")).reset_index())
    result["AvgOrderValue"]=result["Revenue"].div(result["TxnCount"].replace(0,np.nan))
    result["AvgPricePerCase"]=result["Revenue"].div(result["Quantity"].replace(0,np.nan))
    result=result.sort_values(group).reset_index(drop=True)
    previous=result.groupby(group_cols)["Revenue"].shift(1) if group_cols else result["Revenue"].shift(1)
    quantity_previous=result.groupby(group_cols)["Quantity"].shift(1) if group_cols else result["Quantity"].shift(1)
    result["RevenuePrevPeriod"]=previous; result["QuantityPrevPeriod"]=quantity_previous
    result["RevenueGrowthAbs"]=result["Revenue"]-result["RevenuePrevPeriod"]
    result["RevenueGrowthPct"]=result["RevenueGrowthAbs"].div(result["RevenuePrevPeriod"].replace(0,np.nan))*100
    def bucket(row):
        pct=row["RevenueGrowthPct"]; change=abs(row["RevenueGrowthAbs"])
        if pd.isna(pct): return "New/No Data"
        if pct>=10 and change>=500000: return "Strong Growth"
        if pct>=3 and change>=100000: return "Moderate Growth"
        if pct<=-3 and change>=100000: return "Significant Decline"
        return "Minor/Noise"
    result["PerformanceBucket"]=result.apply(bucket,axis=1)
    return result
