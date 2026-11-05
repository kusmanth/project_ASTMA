from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import EmergencyTrip, EmergencyVehicle, Junction, User
from app.schemas.emergency_trip import (
    EmergencyTripCreate,
    EmergencyTripResponse,
    EmergencyTripUpdate,
    TripStatus,
)

router = APIRouter(prefix="/emergency-trips", tags=["Emergency Trips"])

ALLOWED_CREATORS = {"emergency_driver", "police", "admin"}


def get_trip_or_404(trip_id: int, db: Session) -> EmergencyTrip:
    trip = db.get(EmergencyTrip, trip_id)
    if trip is None:
        raise HTTPException(status_code=404, detail="Emergency trip not found")
    return trip


def check_vehicle_and_user(vehicle_id: int, user_id: int, db: Session) -> None:
    vehicle = db.get(EmergencyVehicle, vehicle_id)
    if vehicle is None:
        raise HTTPException(status_code=400, detail=f"Emergency vehicle {vehicle_id} does not exist")
    if not vehicle.is_active:
        raise HTTPException(status_code=400, detail=f"Emergency vehicle {vehicle_id} is blocked")
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=400, detail=f"User {user_id} does not exist")
    if user.user_type not in ALLOWED_CREATORS:
        raise HTTPException(status_code=403, detail="Only emergency drivers, police or admin can start a trip")


def check_junctions(from_id: int, to_id: int, db: Session) -> None:
    if from_id == to_id:
        raise HTTPException(status_code=400, detail="Start and destination junctions must be different")
    for junction_id in (from_id, to_id):
        if db.get(Junction, junction_id) is None:
            raise HTTPException(status_code=400, detail=f"Junction {junction_id} does not exist")


@router.post("", response_model=EmergencyTripResponse, status_code=status.HTTP_201_CREATED)
def create_trip(data: EmergencyTripCreate, db: Session = Depends(get_db)):
    check_vehicle_and_user(data.vehicle_id, data.created_by, db)
    check_junctions(data.from_junction_id, data.to_junction_id, db)
    trip = EmergencyTrip(**data.model_dump())
    db.add(trip)
    db.commit()
    db.refresh(trip)
    return trip


@router.get("", response_model=list[EmergencyTripResponse])
def get_all_trips(
    trip_status: TripStatus | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
):
    query = select(EmergencyTrip)
    if trip_status is not None:
        query = query.where(EmergencyTrip.status == trip_status)
    return db.scalars(query).all()


@router.get("/{trip_id}", response_model=EmergencyTripResponse)
def get_trip(trip_id: int, db: Session = Depends(get_db)):
    return get_trip_or_404(trip_id, db)


@router.put("/{trip_id}", response_model=EmergencyTripResponse)
def replace_trip(trip_id: int, data: EmergencyTripCreate, db: Session = Depends(get_db)):
    trip = get_trip_or_404(trip_id, db)
    check_vehicle_and_user(data.vehicle_id, data.created_by, db)
    check_junctions(data.from_junction_id, data.to_junction_id, db)
    for key, value in data.model_dump().items():
        setattr(trip, key, value)
    db.commit()
    db.refresh(trip)
    return trip


@router.patch("/{trip_id}", response_model=EmergencyTripResponse)
def update_trip(trip_id: int, data: EmergencyTripUpdate, db: Session = Depends(get_db)):
    trip = get_trip_or_404(trip_id, db)
    changes = data.model_dump(exclude_unset=True)
    if "from_junction_id" in changes or "to_junction_id" in changes:
        check_junctions(
            changes.get("from_junction_id", trip.from_junction_id),
            changes.get("to_junction_id", trip.to_junction_id),
            db,
        )
    if changes.get("status") in ("completed", "cancelled") and trip.end_time is None:
        trip.end_time = datetime.now(timezone.utc).replace(tzinfo=None)
    for key, value in changes.items():
        setattr(trip, key, value)
    db.commit()
    db.refresh(trip)
    return trip


@router.delete("/{trip_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_trip(trip_id: int, db: Session = Depends(get_db)):
    trip = get_trip_or_404(trip_id, db)
    db.delete(trip)
    db.commit()