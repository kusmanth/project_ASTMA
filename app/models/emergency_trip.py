from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from app.database import Base


class EmergencyTrip(Base):
    __tablename__ = "emergency_trips"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("emergency_vehicles.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    from_junction_id = Column(Integer, ForeignKey("junctions.id"), nullable=False)
    to_junction_id = Column(Integer, ForeignKey("junctions.id"), nullable=False)
    urgency_level = Column(String(10), nullable=False)
    status = Column(String(10), nullable=False, server_default="active")
    start_time = Column(DateTime, server_default=func.now(), nullable=False)
    end_time = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)