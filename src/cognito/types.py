from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class UnverifiedUserTypeDef(BaseModel):
    username: str = Field(..., alias="Username")
    user_create_date: datetime = Field(..., alias="UserCreateDate")


class CleanUpUnverifiedUserResult(BaseModel):
    deleted: bool
    username: str


class ListUnverifiedUsersResult(BaseModel):
    users: list[UnverifiedUserTypeDef]
    next_token: Optional[str] = None
