from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, func

from app.database import Base
 
 
class PoliceStation(Base):

    __tablename__ = "police_stations"
 
    id = Column(Integer, primary_key=True, index=True)

    station_name = Column(String(255), nullable=False)

    address_id = Column(Integer, ForeignKey("address.id"), nullable=False)

    nearest_junction_id = Column(Integer, ForeignKey("junctions.id"), nullable=False)

    contact_number = Column(String(10), nullable=False)

    is_active = Column(Boolean, nullable=False, server_default="true")

    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
 