
import enum

from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, Enum, func
from app.database import Base


class CongestionLevel(enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"


class TrafficReading(Base):
    __tablename__ = "traffic_readings"

    id = Column(Integer, primary_key=True, index=True)

    road_id = Column(Integer, ForeignKey("roads.id"), nullable=False)

    two_wheeler_count = Column(Integer, nullable=False)
    three_wheeler_count = Column(Integer, nullable=False)
    four_wheeler_count = Column(Integer, nullable=False)
    heavy_vehicle_count = Column(Integer, nullable=False)

    average_speed = Column(Float, nullable=False)

    congestion_level = Column(Enum(CongestionLevel), nullable=False)

    reading_time = Column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )
