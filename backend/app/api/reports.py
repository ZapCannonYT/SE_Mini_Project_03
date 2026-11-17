from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.auth import require_role
from app.core.db import get_db
from app.models import Role, User
from app.schemas.report import PlanningReportRow
from app.services import report_service

router = APIRouter(prefix="/api/reports", tags=["Reports"])
any_user = require_role(Role.ADMIN.value, Role.PLANNER.value, Role.VIEWER.value)


@router.get("/planning", response_model=list[PlanningReportRow])
def planning_report(
    product_id: int | None = Query(None, gt=0, description="Only this product."),
    start_date: date | None = Query(None, description="Created on or after this date (YYYY-MM-DD)."),
    end_date: date | None = Query(None, description="Created on or before this date (YYYY-MM-DD)."),
    risk: Literal["none", "stockout", "overstock"] | None = Query(None, description="Only this risk level."),
    db: Session = Depends(get_db),
    _user: User = Depends(any_user),
):
    """Planning recommendations with their inputs, filtered by product and date (DFIP-F-019)."""
    return report_service.planning_report(db, product_id, start_date, end_date, risk)


@router.get("/planning/export")
def export_planning_report(
    product_id: int | None = Query(None, gt=0),
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    risk: Literal["none", "stockout", "overstock"] | None = Query(None),
    db: Session = Depends(get_db),
    _user: User = Depends(any_user),
):
    """The same filtered report as a CSV download (DFIP-F-020)."""
    rows = report_service.planning_report(db, product_id, start_date, end_date, risk)
    return Response(
        content=report_service.planning_report_csv(rows),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="planning_report.csv"'},
    )
