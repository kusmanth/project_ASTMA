from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

VehicleType = Literal["ambulance", "fire_truck", "police", "vvip_convoy"]


class EmergencyVehicleCreate(BaseModel):
    vehicle_number: str = Field(min_length=4, max_length=20)
    vehicle_type: VehicleType
    priority_level: int = Field(ge=1, le=5)
    is_active: bool = True


class EmergencyVehicleUpdate(BaseModel):
    vehicle_number: str | None = Field(default=None, min_length=4, max_length=20)
    vehicle_type: VehicleType | None = None
    priority_level: int | None = Field(default=None, ge=1, le=5)
    is_active: bool | None = None


class EmergencyVehicleResponse(EmergencyVehicleCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
