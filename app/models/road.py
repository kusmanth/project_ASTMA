from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, func
from app.database import Base


class Road(Base):
    __tablename__ = "roads"

    id = Column(Integer, primary_key=True, index=True)
    road_name = Column(String(255), nullable=False)
    from_junction_id = Column(Integer, ForeignKey("junctions.id"), nullable=False)
    to_junction_id = Column(Integer, ForeignKey("junctions.id"), nullable=False)
    distance_km = Column(Float, nullable=False)
    lanes = Column(Integer, nullable=False)
    is_active = Column(Boolean, nullable=False, server_default="true")
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)