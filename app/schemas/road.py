from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class RoadCreate(BaseModel):
    road_name: str = Field(min_length=4, max_length=255)
    from_junction_id: int
    to_junction_id: int
    distance_km: float = Field(gt=0)
    lanes: int = Field(ge=1, le=8)
    is_active: bool = True


class RoadUpdate(BaseModel):
    road_name: str | None = Field(default=None, min_length=4, max_length=255)
    from_junction_id: int | None = None
    to_junction_id: int | None = None
    distance_km: float | None = Field(default=None, gt=0)
    lanes: int | None = Field(default=None, ge=1, le=8)
    is_active: bool | None = None


class RoadResponse(RoadCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime