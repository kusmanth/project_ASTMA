from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, func
from app.database import Base


class Junction(Base):
    __tablename__ = "junctions"

    id = Column(Integer, primary_key=True, index=True)
    junction_name = Column(String(255), nullable=False)
    junction_type = Column(Integer, nullable=False)
    address_id = Column(Integer, ForeignKey("address.id"), nullable=False)
    is_active = Column(Boolean, nullable=False, server_default="true")
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)