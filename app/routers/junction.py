from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Address, Junction
from app.schemas.junction import (
    JunctionCreate,
    JunctionResponse,
    JunctionStatusUpdate,
    JunctionUpdate,
)

router = APIRouter(prefix="/junctions", tags=["Junctions"])


def get_junction_or_404(junction_id: int, db: Session) -> Junction:
    junction = db.get(Junction, junction_id)
    if junction is None:
        raise HTTPException(status_code=404, detail="Junction not found")
    return junction


def check_address_exists(address_id: int, db: Session) -> None:
    if db.get(Address, address_id) is None:
        raise HTTPException(status_code=400, detail=f"Address {address_id} does not exist")


@router.post("/", response_model=JunctionResponse, status_code=status.HTTP_201_CREATED)
def create_junction(data: JunctionCreate, db: Session = Depends(get_db)):
    check_address_exists(data.address_id, db)
    junction = Junction(**data.model_dump())
    db.add(junction)
    db.commit()
    db.refresh(junction)
    return junction


@router.get("/", response_model=list[JunctionResponse])
def get_all_junctions(db: Session = Depends(get_db)):
    return db.scalars(select(Junction)).all()


@router.get("/{junction_id}", response_model=JunctionResponse)
def get_junction(junction_id: int, db: Session = Depends(get_db)):
    return get_junction_or_404(junction_id, db)


@router.put("/{junction_id}", response_model=JunctionResponse)
def replace_junction(junction_id: int, data: JunctionCreate, db: Session = Depends(get_db)):
    junction = get_junction_or_404(junction_id, db)
    check_address_exists(data.address_id, db)
    for key, value in data.model_dump().items():
        setattr(junction, key, value)
    db.commit()
    db.refresh(junction)
    return junction


@router.patch("/{junction_id}", response_model=JunctionResponse)
def update_junction(junction_id: int, data: JunctionUpdate, db: Session = Depends(get_db)):
    junction = get_junction_or_404(junction_id, db)
    changes = data.model_dump(exclude_unset=True)
    if "address_id" in changes:
        check_address_exists(changes["address_id"], db)
    for key, value in changes.items():
        setattr(junction, key, value)
    db.commit()
    db.refresh(junction)
    return junction


@router.patch("/{junction_id}/status", response_model=JunctionResponse)
def update_junction_status(junction_id: int, data: JunctionStatusUpdate, db: Session = Depends(get_db)):
    junction = get_junction_or_404(junction_id, db)
    junction.is_active = data.is_active
    db.commit()
    db.refresh(junction)
    return junction


@router.delete("/{junction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_junction(junction_id: int, db: Session = Depends(get_db)):
    junction = get_junction_or_404(junction_id, db)
    try:
        db.delete(junction)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Junction is used by a road and cannot be deleted")