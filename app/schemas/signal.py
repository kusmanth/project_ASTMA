from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict

SignalState = Literal["green", "yellow", "red"]
class SignalCreate(BaseModel):
    junction_id: int
    road_id: int
    current_state: SignalState = "red"
    is_active: bool = True

class SignalUpdate(BaseModel):
    junction_id: int | None = None
    road_id: int | None = None
    current_state: SignalState | None = None
    is_active: bool | None = None

class SignalResponse(SignalCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime