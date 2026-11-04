from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Junction, Road, Signal
from app.schemas.signal import SignalCreate, SignalResponse, SignalUpdate

router = APIRouter(prefix="/signals", tags=["Signals"])

def get_signal_or_404(signal_id: int, db: Session) -> Signal:
    signal = db.get(Signal, signal_id)
    if signal is None:
        raise HTTPException(status_code=404, detail="Signal not found")
    return signal

def check_junction_and_road(junction_id: int, road_id: int, db: Session) -> None:
    if db.get(Junction, junction_id) is None:
        raise HTTPException(status_code=400, detail=f"Junction {junction_id} does not exist")
    road = db.get(Road, road_id)
    if road is None:
        raise HTTPException(status_code=400, detail=f"Road {road_id} does not exist")
    if road.to_junction_id != junction_id:
        raise HTTPException(status_code=400, detail=f"Road {road_id} does not come into junction {junction_id}")
        
@router.post("/", response_model=SignalResponse, status_code=status.HTTP_201_CREATED)
def create_signal(data: SignalCreate, db: Session = Depends(get_db)):
    check_junction_and_road(data.junction_id, data.road_id, db)
    signal = Signal(**data.model_dump())
    db.add(signal)
    db.commit()
    db.refresh(signal)
    return signal

@router.get("/", response_model=list[SignalResponse])
def get_all_signals(db: Session = Depends(get_db)):
    return db.scalars(select(Signal)).all()

@router.get("/{signal_id}", response_model=SignalResponse)
def get_signal(signal_id: int, db: Session = Depends(get_db)):
    return get_signal_or_404(signal_id, db)

@router.put("/{signal_id}", response_model=SignalResponse)
def replace_signal(signal_id: int, data: SignalCreate, db: Session = Depends(get_db)):
    signal = get_signal_or_404(signal_id, db)
    check_junction_and_road(data.junction_id, data.road_id, db)
    for key, value in data.model_dump().items():
        setattr(signal, key, value)
        db.commit()
        db.refresh(signal)
        return signal

@router.patch("/{signal_id}", response_model=SignalResponse)
def update_signal(signal_id: int, data: SignalUpdate, db: Session = Depends(get_db)):
    signal = get_signal_or_404(signal_id, db)
    changes = data.model_dump(exclude_unset=True)
    if "junction_id" in changes or "road_id" in changes:
        check_junction_and_road(changes.get("junction_id", signal.junction_id),
        changes.get("road_id", signal.road_id),
        db,
        )
    for key, value in changes.items():
        setattr(signal, key, value)
    db.commit()
    db.refresh(signal) 
    return signal

@router.delete("/{signal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_signal(signal_id: int, db: Session = Depends(get_db)):
    signal = get_signal_or_404(signal_id, db)
    try:
        db.delete(signal)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Signal has timings and cannot be deleted")