from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

RouteStatus = Literal["active", "completed"]


class RouteRequestCreate(BaseModel):
    user_id: int
    from_junction_id: int
    to_junction_id: int
    suggested_route: list[int] = Field(min_length=1)


class RouteRequestUpdate(BaseModel):
    suggested_route: list[int] | None = Field(default=None, min_length=1)
    status: RouteStatus | None = None


class RouteRequestResponse(RouteRequestCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    requested_at: datetime
    expires_at: datetime