from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.auth import require_role
from app.core.db import get_db
from app.models import Role, User
from app.schemas.audit import AuditLogOut
from app.services import audit_service

router = APIRouter(prefix="/api/audit", tags=["Audit Logs"])

admin_only = require_role(Role.ADMIN.value)


@router.get("", response_model=list[AuditLogOut])
def get_audit_logs(
    actor_id: int | None = Query(default=None, ge=1),
    action: str | None = Query(default=None, min_length=1),
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
    _admin: User = Depends(admin_only),
):
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start date cannot be after end date",
        )

    return audit_service.list_audit_logs(
        db,
        actor_id=actor_id,
        action=action,
        start_date=start_date,
        end_date=end_date,
    )
