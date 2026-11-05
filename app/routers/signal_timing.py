
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.signal_timing import SignalTiming
from app.schemas.signal_timing import (
    SignalTimingCreate,
    SignalTimingUpdate,
    SignalTimingResponse,
)

router = APIRouter(
    prefix="/signal-timings",
    tags=["Signal Timings"]
)


@router.post("/", response_model=SignalTimingResponse, status_code=201)
def create_signal_timing(
    timing: SignalTimingCreate,
    db: Session = Depends(get_db)
):
    db_timing = SignalTiming(**timing.model_dump())
    db.add(db_timing)
    db.commit()
    db.refresh(db_timing)
    return db_timing


@router.get("/", response_model=list[SignalTimingResponse])
def get_signal_timings(db: Session = Depends(get_db)):
    return db.query(SignalTiming).all()


@router.get("/{timing_id}", response_model=SignalTimingResponse)
def get_signal_timing(
    timing_id: int,
    db: Session = Depends(get_db)
):
    timing = db.query(SignalTiming).filter(
        SignalTiming.id == timing_id
    ).first()

    if not timing:
        raise HTTPException(status_code=404, detail="Signal timing not found")

    return timing


@router.put("/{timing_id}", response_model=SignalTimingResponse)
def update_signal_timing(
    timing_id: int,
    timing_data: SignalTimingUpdate,
    db: Session = Depends(get_db)
):
    timing = db.query(SignalTiming).filter(
        SignalTiming.id == timing_id
    ).first()

    if not timing:
        raise HTTPException(status_code=404, detail="Signal timing not found")

    for key, value in timing_data.model_dump().items():
        setattr(timing, key, value)

    db.commit()
    db.refresh(timing)
    return timing


@router.delete("/{timing_id}", status_code=204)
def delete_signal_timing(
    timing_id: int,
    db: Session = Depends(get_db)
):
    timing = db.query(SignalTiming).filter(
        SignalTiming.id == timing_id
    ).first()

    if not timing:
        raise HTTPException(status_code=404, detail="Signal timing not found")

    db.delete(timing)
    db.commit()
