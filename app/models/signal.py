from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, func
from app.database import Base
class Signal(Base):
    __tablename__ = "signals"
    id = Column(Integer, primary_key=True, index=True)
    junction_id = Column(Integer, ForeignKey("junctions.id"), nullable=False)
    road_id = Column(Integer, ForeignKey("roads.id"), nullable=False)
    current_state = Column(String(10), nullable=False, server_default="red")
    is_active = Column(Boolean, nullable=False, server_default="true")
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(),nullable=False)
