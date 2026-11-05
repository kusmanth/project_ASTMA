from sqlalchemy import Boolean, Column, DateTime, Integer, String, func
from app.database import Base


class EmergencyVehicle(Base):
    __tablename__ = "emergency_vehicles"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_number = Column(String(20), nullable=False, unique=True)
    vehicle_type = Column(String(20), nullable=False)
    priority_level = Column(Integer, nullable=False)
    is_active = Column(Boolean, nullable=False, server_default="true")
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)