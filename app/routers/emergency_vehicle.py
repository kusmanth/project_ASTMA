from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import EmergencyVehicle
from app.schemas.emergency_vehicle import (
    EmergencyVehicleCreate,
    EmergencyVehicleResponse,
    EmergencyVehicleUpdate,
)

router = APIRouter(prefix="/emergency-vehicles", tags=["Emergency Vehicles"])


def get_vehicle_or_404(vehicle_id: int, db: Session) -> EmergencyVehicle:
    vehicle = db.get(EmergencyVehicle, vehicle_id)
    if vehicle is None:
        raise HTTPException(status_code=404, detail="Emergency vehicle not found")
    return vehicle


def save(vehicle: EmergencyVehicle, db: Session) -> EmergencyVehicle:
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="This vehicle number is already registered")
    db.refresh(vehicle)
    return vehicle


@router.post("", response_model=EmergencyVehicleResponse, status_code=status.HTTP_201_CREATED)
def create_vehicle(data: EmergencyVehicleCreate, db: Session = Depends(get_db)):
    vehicle = EmergencyVehicle(**data.model_dump())
    db.add(vehicle)
    return save(vehicle, db)


@router.get("", response_model=list[EmergencyVehicleResponse])
def get_all_vehicles(db: Session = Depends(get_db)):
    return db.scalars(select(EmergencyVehicle)).all()


@router.get("/{vehicle_id}", response_model=EmergencyVehicleResponse)
def get_vehicle(vehicle_id: int, db: Session = Depends(get_db)):
    return get_vehicle_or_404(vehicle_id, db)


@router.put("/{vehicle_id}", response_model=EmergencyVehicleResponse)
def replace_vehicle(vehicle_id: int, data: EmergencyVehicleCreate, db: Session = Depends(get_db)):
    vehicle = get_vehicle_or_404(vehicle_id, db)
    for key, value in data.model_dump().items():
        setattr(vehicle, key, value)
    return save(vehicle, db)


@router.patch("/{vehicle_id}", response_model=EmergencyVehicleResponse)
def update_vehicle(vehicle_id: int, data: EmergencyVehicleUpdate, db: Session = Depends(get_db)):
    vehicle = get_vehicle_or_404(vehicle_id, db)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(vehicle, key, value)
    return save(vehicle, db)


@router.delete("/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vehicle(vehicle_id: int, db: Session = Depends(get_db)):
    vehicle = get_vehicle_or_404(vehicle_id, db)
    try:
        db.delete(vehicle)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Vehicle has emergency trips and cannot be deleted")
