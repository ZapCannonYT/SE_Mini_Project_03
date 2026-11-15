
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models import Setting, User
from app.schemas.settings import SettingsUpdate
from app.services.audit_service import log_action


SETTING_KEYS = {
    "default_safety_stock",
    "default_overstock_factor",
    "minimum_history_periods",
}

DEFAULT_SETTINGS = {
    "minimum_history_periods": "8",
}


def get_settings(db: Session) -> dict[str, str]:
    saved_settings = db.scalars(select(Setting)).all()
    result = DEFAULT_SETTINGS.copy()

    for setting in saved_settings:
        if setting.key in SETTING_KEYS:
            result[setting.key] = setting.value

    return result


def update_settings(
    db: Session,
    data: SettingsUpdate,
    actor: User,
) -> dict[str, str]:
    values = data.model_dump(exclude_unset=True)

    if not values:
        raise AppError(
            400,
            "empty_settings",
            "At least one setting must be provided.",
        )

    changed_keys = []

    for key, value in values.items():
        if value is None:
            raise AppError(
                400,
                "invalid_setting",
                f"{key} cannot be null.",
            )

        setting = db.get(Setting, key)
        old_value = setting.value if setting else DEFAULT_SETTINGS.get(key)

        if old_value != str(value):
            changed_keys.append(key)

        if setting is None:
            setting = Setting(key=key, value=str(value))
            db.add(setting)
        else:
            setting.value = str(value)

    if changed_keys:
        log_action(
            db,
            action="settings_update",
            result="success",
            actor_id=actor.id,
            entity="settings",
            details=f"Updated settings: {', '.join(changed_keys)}",
        )

    db.commit()

    return get_settings(db)
