from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.auth import require_role
from app.core.db import get_db
from app.models import Role, User
from app.schemas.dashboard import DashboardOut
from app.services import dashboard_service

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])
any_user = require_role(Role.ADMIN.value, Role.PLANNER.value, Role.VIEWER.value)


@router.get("", response_model=DashboardOut)
def get_dashboard(db: Session = Depends(get_db), _user: User = Depends(any_user)):
    """Dashboard summary, product planning and 30-day/7-day trend (DFIP-F-017/F-018)."""
    return dashboard_service.build_dashboard(db)
