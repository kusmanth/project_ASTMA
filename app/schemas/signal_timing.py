
from datetime import time, datetime
from pydantic import BaseModel, ConfigDict


class SignalTimingBase(BaseModel):
    signal_id: int
    start_time: time
    end_time: time
    green_time: int
    yellow_time: int
    red_time: int


class SignalTimingCreate(SignalTimingBase):
    pass


class SignalTimingUpdate(SignalTimingBase):
    pass


class SignalTimingResponse(SignalTimingBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
