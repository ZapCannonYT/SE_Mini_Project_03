
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.auth import require_role
from app.core.db import get_db
from app.models import Role, User
from app.schemas.user import UserCreate, UserOut, UserRoleUpdate
from app.services import user_service

router = APIRouter(prefix="/api/users", tags=["User Administration"])

admin_only = require_role(Role.ADMIN.value)


def to_out(user: User) -> UserOut:
    return UserOut(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role.value,
        is_active=user.is_active,
        created_at=user.created_at,
    )


@router.get("", response_model=list[UserOut])
def list_users(
    db: Session = Depends(get_db),
    _admin: User = Depends(admin_only),
):
    return [to_out(user) for user in user_service.list_users(db)]


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    data: UserCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(admin_only),
):
    return to_out(user_service.create_user(db, data))


@router.patch("/{user_id}/role", response_model=UserOut)
def update_user_role(
    user_id: int,
    data: UserRoleUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(admin_only),
):
    return to_out(user_service.update_user_role(db, user_id, data, admin))


@router.patch("/{user_id}/deactivate", response_model=UserOut)
def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(admin_only),
):
    return to_out(user_service.deactivate_user(db, user_id, admin))
