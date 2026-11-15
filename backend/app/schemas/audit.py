from datetime import datetime

from pydantic import BaseModel


class AuditLogOut(BaseModel):
    id: int
    actor_id: int | None = None
    action: str
    entity: str | None = None
    entity_id: str | None = None
    result: str
    details: str | None = None
    timestamp: datetime

    model_config = {"from_attributes": True}
