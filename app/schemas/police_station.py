from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
 
PHONE = r"^\d{10}$"
 
 
class PoliceStationCreate(BaseModel):
    station_name: str = Field(min_length=4, max_length=255)
    address_id: int
    nearest_junction_id: int
    contact_number: str = Field(pattern=PHONE)
    is_active: bool = True
 
 
class PoliceStationUpdate(BaseModel):
    station_name: str | None = Field(default=None, min_length=4, max_length=255)
    address_id: int | None = None
    nearest_junction_id: int | None = None
    contact_number: str | None = Field(default=None, pattern=PHONE)
    is_active: bool | None = None
 
 
class PoliceStationResponse(PoliceStationCreate):
    model_config = ConfigDict(from_attributes=True)
 
    id: int
    created_at: datetime
    updated_at: datetime