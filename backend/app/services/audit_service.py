from datetime import date, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit import AuditLog


def log_action(
    db: Session,
    action: str,
    result: str,
    actor_id: int | None = None,
    entity: str | None = None,
    entity_id: str | None = None,
    details: str | None = None,
) -> AuditLog:
    """Record an action without storing passwords or authentication tokens."""

    audit_log = AuditLog(
        actor_id=actor_id,
        action=action,
        entity=entity,
        entity_id=entity_id,
        result=result,
        details=details,
    )

    db.add(audit_log)
    db.flush()

    return audit_log


def list_audit_logs(
    db: Session,
    actor_id: int | None = None,
    action: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[AuditLog]:
    query = select(AuditLog)

    if actor_id is not None:
        query = query.where(AuditLog.actor_id == actor_id)

    if action is not None:
        query = query.where(AuditLog.action == action)

    if start_date is not None:
        start = datetime.combine(start_date, time.min)
        query = query.where(AuditLog.timestamp >= start)

    if end_date is not None:
        end = datetime.combine(end_date + timedelta(days=1), time.min)
        query = query.where(AuditLog.timestamp < end)

    query = query.order_by(AuditLog.timestamp.desc())

    return list(db.scalars(query).all())