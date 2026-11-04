
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class TrafficReadingCreate(BaseModel):
    road_id: int = Field(gt=0)

    two_wheeler_count: int = Field(ge=0)
    three_wheeler_count: int = Field(ge=0)
    four_wheeler_count: int = Field(ge=0)
    heavy_vehicle_count: int = Field(ge=0)

    average_speed: float = Field(ge=0)

    congestion_level: str = Field(pattern="^(low|medium|high)$")


class TrafficReadingResponse(TrafficReadingCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    reading_time: datetime
