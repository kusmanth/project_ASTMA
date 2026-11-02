from sqlalchemy import Column, Integer , String, Float , DateTime, func
from app.database import Base

class Address(Base):
    __tablename__= "address"

    id = Column(Integer, primary_key=True, index=True)
    street= Column(String(255), nullable=False)
    landmark= Column(String(255), nullable= True)
    city = Column(String(100),nullable=False)
    state = Column(String(100), nullable=False)
    pincode = Column(String(6), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)