
from sqlalchemy import Column, Integer, Time, DateTime, ForeignKey, func
from app.database import Base


class SignalTiming(Base):
    __tablename__ = "signal_timings"

    id = Column(Integer, primary_key=True, index=True)

    signal_id = Column(
        Integer,
        ForeignKey("signals.id"),
        nullable=False
    )

    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)

    green_time = Column(Integer, nullable=False)
    yellow_time = Column(Integer, nullable=False)
    red_time = Column(Integer, nullable=False)

    created_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )

    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
