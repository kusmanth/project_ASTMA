from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.road import Road
from app.models.traffic_reading import TrafficReading
from app.schemas.traffic_reading import (
    TrafficReadingCreate,
    TrafficReadingResponse,
)

router = APIRouter(
    prefix="/traffic-readings",
    tags=["Traffic Readings"]
)


def get_reading_or_404(reading_id: int, db: Session) -> TrafficReading:
    reading = db.get(TrafficReading, reading_id)
    if reading is None:
        raise HTTPException(status_code=404, detail="Traffic reading not found")
    return reading


@router.post("", response_model=TrafficReadingResponse,
             status_code=status.HTTP_201_CREATED)
def create_traffic_reading(data: TrafficReadingCreate, db: Session = Depends(get_db)):
    if db.get(Road, data.road_id) is None:
        raise HTTPException(status_code=400, detail=f"Road {data.road_id} does not exist")

    reading = TrafficReading(**data.model_dump())
    db.add(reading)
    db.commit()
    db.refresh(reading)
    return reading


@router.get("", response_model=list[TrafficReadingResponse])
def get_all_traffic_readings(db: Session = Depends(get_db)):
    return db.scalars(select(TrafficReading)).all()


@router.get("/{reading_id}", response_model=TrafficReadingResponse)
def get_traffic_reading(reading_id: int, db: Session = Depends(get_db)):
    return get_reading_or_404(reading_id, db)