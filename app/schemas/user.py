from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

UserType = Literal["driver", "emergency_driver", "police", "admin"]
MOBILE = r"^\d{10}$"
EMAIL = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class UserCreate(BaseModel):
    name: str = Field(min_length=4, max_length=255)
    mobile: str = Field(pattern=MOBILE)
    email: str | None = Field(default=None, max_length=255, pattern=EMAIL)
    user_type: UserType
    password: str = Field(min_length=8, max_length=72)
    is_active: bool = True


class UserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=4, max_length=255)
    mobile: str | None = Field(default=None, pattern=MOBILE)
    email: str | None = Field(default=None, max_length=255, pattern=EMAIL)
    user_type: UserType | None = None
    password: str | None = Field(default=None, min_length=8, max_length=72)
    is_active: bool | None = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    mobile: str
    email: str | None
    user_type: str
    is_active: bool
    created_at: datetime
    updated_at: datetime