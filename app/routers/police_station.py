from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
 
from app.database import get_db
from app.models import Address, Junction, PoliceStation
from app.schemas.police_station import (
    PoliceStationCreate,
    PoliceStationResponse,
    PoliceStationUpdate,
)
 
router = APIRouter(prefix="/police-stations", tags=["Police Stations"])
 
 
def get_station_or_404(station_id: int, db: Session) -> PoliceStation:
    station = db.get(PoliceStation, station_id)
    if station is None:
        raise HTTPException(status_code=404, detail="Police station not found")
    return station
 
 
def check_links(changes: dict, db: Session) -> None:
    if "address_id" in changes and db.get(Address, changes["address_id"]) is None:
        raise HTTPException(status_code=400, detail=f"Address {changes['address_id']} does not exist")
    if "nearest_junction_id" in changes and db.get(Junction, changes["nearest_junction_id"]) is None:
        raise HTTPException(status_code=400, detail=f"Junction {changes['nearest_junction_id']} does not exist")
 
 
@router.post("", response_model=PoliceStationResponse, status_code=status.HTTP_201_CREATED)
def create_station(data: PoliceStationCreate, db: Session = Depends(get_db)):
    check_links(data.model_dump(), db)
    station = PoliceStation(**data.model_dump())
    db.add(station)
    db.commit()
    db.refresh(station)
    return station
 
 
@router.get("", response_model=list[PoliceStationResponse])
def get_all_stations(db: Session = Depends(get_db)):
    return db.scalars(select(PoliceStation)).all()
 
 
@router.get("/{station_id}", response_model=PoliceStationResponse)
def get_station(station_id: int, db: Session = Depends(get_db)):
    return get_station_or_404(station_id, db)
 
 
@router.put("/{station_id}", response_model=PoliceStationResponse)
def replace_station(station_id: int, data: PoliceStationCreate, db: Session = Depends(get_db)):
    station = get_station_or_404(station_id, db)
    changes = data.model_dump()
    check_links(changes, db)
    for key, value in changes.items():
        setattr(station, key, value)
    db.commit()
    db.refresh(station)
    return station
 
 
@router.patch("/{station_id}", response_model=PoliceStationResponse)
def update_station(station_id: int, data: PoliceStationUpdate, db: Session = Depends(get_db)):
    station = get_station_or_404(station_id, db)
    changes = data.model_dump(exclude_unset=True)
    check_links(changes, db)
    for key, value in changes.items():
        setattr(station, key, value)
    db.commit()
    db.refresh(station)
    return station
 
 
@router.delete("/{station_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_station(station_id: int, db: Session = Depends(get_db)):
    station = get_station_or_404(station_id, db)
    db.delete(station)
    db.commit()