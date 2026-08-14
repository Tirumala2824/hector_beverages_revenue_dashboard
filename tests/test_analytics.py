import pandas as pd

from app.analytics import aggregate_data, identify_dimensions

def frame():
    return pd.DataFrame({"Posting Date": pd.to_datetime(["2024-01-01","2024-02-01","2024-03-01"]),"Amount":[100,200,150],"Quantity":[10,20,15],"Region":["A","A","B"]})

def test_aggregate_adds_growth_and_uses_year_week():
    df=frame(); from app.analytics import load_sales_data
    normalized=df.copy(); normalized["Year"]=normalized["Posting Date"].dt.year; normalized["Month"]=normalized["Posting Date"].dt.month; normalized["Quarter"]=normalized["Posting Date"].dt.quarter; normalized["YearMonth"]=normalized["Posting Date"].dt.to_period("M").astype(str); normalized["YearQuarter"]=normalized["Posting Date"].dt.to_period("Q").astype(str); normalized["YearWeek"]=normalized["Posting Date"].dt.strftime("%G-W%V"); normalized["Week"]=normalized["Posting Date"].dt.isocalendar().week.astype(int)
    out=aggregate_data(normalized,["Region"],"monthly")
    assert {"RevenueGrowthPct","PerformanceBucket"}.issubset(out.columns)

def test_dimensions_exclude_measures_and_time_columns():
    df=frame(); df["Year"]=2024; df["YearMonth"]="2024-01"; assert identify_dimensions(df)==["Region"]
