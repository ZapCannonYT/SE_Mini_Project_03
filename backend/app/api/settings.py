
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.auth import require_role
from app.core.db import get_db
from app.models import Role, User
from app.schemas.settings import SettingsOut, SettingsUpdate
from app.services import settings_service

router = APIRouter(prefix="/api/settings", tags=["Settings"])

admin_only = require_role(Role.ADMIN.value)


@router.get("", response_model=SettingsOut)
def get_settings(
    db: Session = Depends(get_db),
    _admin: User = Depends(admin_only),
):
    return settings_service.get_settings(db)


@router.patch("", response_model=SettingsOut)
def update_settings(
    data: SettingsUpdate,
    db: Session = Depends(get_db),
    _admin: User = Depends(admin_only),
):
    return settings_service.update_settings(db, data)
