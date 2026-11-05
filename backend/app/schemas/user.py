
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints

Name = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=100),
]

Password = Annotated[
    str,
    StringConstraints(min_length=8, max_length=128),
]


class UserCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Name
    email: EmailStr
    password: Password
    role: str = Field(pattern=r"^(admin|planner|viewer)$")


class UserRoleUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: str = Field(pattern=r"^(admin|planner|viewer)$")


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    role: str
    is_active: bool
    created_at: datetime
