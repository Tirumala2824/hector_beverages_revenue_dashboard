import pandas as pd
import pytest

from app.config import Settings
from app.dashboard_service import DashboardQuery, DashboardService


def sample_frame():
    frame = pd.DataFrame(
        {
            "Posting Date": pd.to_datetime(
                ["2024-01-01", "2024-02-01", "2024-03-01", "2024-03-15"]
            ),
            "Amount": [100.0, 200.0, 150.0, 50.0],
            "Quantity": [10, 20, 15, 5],
            "Region": ["North", "North", "South", "South"],
        }
    )
    frame["Year"] = frame["Posting Date"].dt.year
    frame["Month"] = frame["Posting Date"].dt.month
    frame["Quarter"] = frame["Posting Date"].dt.quarter
    frame["YearMonth"] = frame["Posting Date"].dt.to_period("M").astype(str)
    frame["YearQuarter"] = frame["Posting Date"].dt.to_period("Q").astype(str)
    frame["YearWeek"] = frame["Posting Date"].dt.strftime("%G-W%V")
    frame["Week"] = frame["Posting Date"].dt.isocalendar().week.astype(int)
    return frame


def service():
    settings = Settings.from_environment()
    return DashboardService(settings, data_frame=sample_frame())


def test_build_context_returns_kpis_and_breakdown():
    result = service().build_context(DashboardQuery(group_by1="Region"), {})
    assert result["kpis"]["total_txns"] == "2"
    assert result["breakdown_rows"]
    assert result["error_message"] is None


def test_invalid_date_is_rejected():
    with pytest.raises(ValueError, match="Invalid date"):
        service().build_context(DashboardQuery(start_date="not-a-date"), {})


def test_unsupported_group_is_ignored_at_application_boundary():
    result = service().build_context(DashboardQuery(group_by1="NotAColumn"), {})
    assert result["breakdown_headers"][:1] != ["NotAColumn"]
