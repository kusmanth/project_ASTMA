from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class AddressCreate(BaseModel):
    street: str = Field(min_length=2, max_length=255)
    landmark: str | None = Field(default=None, max_length=255)
    city: str = Field(min_length=2, max_length=100)
    state: str = Field(min_length=2, max_length=100)
    pincode: str = Field(pattern=r"^\d{6}$")
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class AddressUpdate(BaseModel):
    street: str | None = Field(default=None, min_length=2, max_length=255)
    landmark: str | None = Field(default=None, max_length=255)
    city: str | None = Field(default=None, min_length=2, max_length=100)
    state: str | None = Field(default=None, min_length=2, max_length=100)
    pincode: str | None = Field(default=None, pattern=r"^\d{6}$")
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)


class AddressResponse(AddressCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime