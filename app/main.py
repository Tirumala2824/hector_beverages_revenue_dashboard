from __future__ import annotations

import json
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .config import Settings
from .dashboard_service import DashboardQuery, DashboardService

settings=Settings.from_environment()
service=DashboardService(settings)
app=FastAPI(title="Revenue Performance Dashboard", version="1.0.0")
templates=Jinja2Templates(directory=str(settings.template_dir))
app.mount("/static", StaticFiles(directory=str(settings.static_dir)), name="static")

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, start_date: str | None = None, end_date: str | None = None, years: str | None = None, time_grain: str = "monthly", group_by1: str | None = None, group_by2: str | None = None, compare_yoy: bool = False, auto_apply: bool = False, clear_filters: bool = False):
    query=DashboardQuery(start_date=start_date,end_date=end_date,years=years,time_grain=time_grain,group_by1=group_by1,group_by2=group_by2,compare_yoy=compare_yoy,auto_apply=auto_apply,clear_filters=clear_filters)
    try:
        context=service.build_context(query, request.query_params)
    except ValueError as exc:
        context=service._empty_context(query, str(exc))
    context["request"]=request
    if "trend_labels_json" in context and isinstance(context["trend_labels_json"], list):
        context["trend_labels_json"]=json.dumps(context["trend_labels_json"])
        context["trend_values_json"]=json.dumps(context["trend_values_json"])
        context["yoy_data_json"]=json.dumps(context["yoy_data_json"]) if context["yoy_data_json"] is not None else "null"
    return templates.TemplateResponse("dashboard.html", context)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=False)
