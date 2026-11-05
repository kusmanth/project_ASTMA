from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, func
from app.database import Base


class RouteRequest(Base):
    __tablename__ = "route_requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    from_junction_id = Column(Integer, ForeignKey("junctions.id"), nullable=False)
    to_junction_id = Column(Integer, ForeignKey("junctions.id"), nullable=False)
    suggested_route = Column(JSON, nullable=False)
    status = Column(String(10), nullable=False, server_default="active")
    requested_at = Column(DateTime, server_default=func.now(), nullable=False)
    expires_at = Column(DateTime, nullable=False)