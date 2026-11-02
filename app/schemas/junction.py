from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field , ConfigDict

class JunctionCreate(BaseModel):
    junction_name: str = Field(min_length=4,max_length=255)
    junction_type: Literal[2,3,4,5]
    address_id: int
    is_active: bool=True

class JunctionResponse(JunctionCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime

class JunctionUpdate(BaseModel):
    junction_name: str | None = Field(default=None,min_length=4, max_length=255)
    junction_type:Literal[2,3,4,5] |None = None
    address_id: int | None = None
    is_active: bool | None= None

class JunctionStatusUpdate(BaseModel):
    is_active: bool