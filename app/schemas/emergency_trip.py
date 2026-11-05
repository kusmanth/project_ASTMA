from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict

Urgency = Literal["critical", "normal", "none"]
TripStatus = Literal["active", "completed", "cancelled"]


class EmergencyTripCreate(BaseModel):
    vehicle_id: int
    created_by: int
    from_junction_id: int
    to_junction_id: int
    urgency_level: Urgency


class EmergencyTripUpdate(BaseModel):
    from_junction_id: int | None = None
    to_junction_id: int | None = None
    urgency_level: Urgency | None = None
    status: TripStatus | None = None


class EmergencyTripResponse(EmergencyTripCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    start_time: datetime
    end_time: datetime | None
    created_at: datetime
    updated_at: datetime