from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
 
 
class HospitalCreate(BaseModel):
    hospital_name: str = Field(min_length=4, max_length=255)
    address_id: int
    nearest_junction_id: int
    emergency_available: bool = True
    is_active: bool = True
 
 
class HospitalUpdate(BaseModel):
    hospital_name: str | None = Field(default=None, min_length=4, max_length=255)
    address_id: int | None = None
    nearest_junction_id: int | None = None
    emergency_available: bool | None = None
    is_active: bool | None = None

class HospitalResponse(HospitalCreate):
    model_config = ConfigDict(from_attributes=True)
 
    id: int
    created_at: datetime
    updated_at: datetime