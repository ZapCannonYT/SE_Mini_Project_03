
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.security import hash_password
from app.models import Role, User
from app.schemas.user import UserCreate, UserRoleUpdate


def list_users(db: Session) -> list[User]:
    stmt = select(User).order_by(User.id)
    return list(db.scalars(stmt))


def create_user(db: Session, data: UserCreate) -> User:
    duplicate = db.scalar(
        select(User.id).where(func.lower(User.email) == data.email.lower())
    )

    if duplicate is not None:
        raise AppError(409, "email_exists", "A user with this email already exists.")

    user = User(
        name=data.name,
        email=data.email,
        password_hash=hash_password(data.password),
        role=Role(data.role),
        is_active=True,
    )

    db.add(user)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise AppError(
            409,
            "email_exists",
            "A user with this email already exists.",
        ) from None

    db.refresh(user)
    return user


def update_user_role(
    db: Session,
    user_id: int,
    data: UserRoleUpdate,
    actor: User,
) -> User:
    user = db.get(User, user_id)

    if user is None:
        raise AppError(404, "user_not_found", f"User {user_id} does not exist.")

    if user.id == actor.id and user.role.value != data.role:
        raise AppError(400, "self_role_change", "You cannot change your own role.")

    user.role = Role(data.role)
    db.commit()
    db.refresh(user)
    return user


def deactivate_user(db: Session, user_id: int, actor: User) -> User:
    user = db.get(User, user_id)

    if user is None:
        raise AppError(404, "user_not_found", f"User {user_id} does not exist.")

    if user.id == actor.id:
        raise AppError(400, "self_deactivation", "You cannot deactivate your own account.")

    if user.is_active:
        user.is_active = False
        db.commit()
        db.refresh(user)

    return user
