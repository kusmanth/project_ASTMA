from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Junction, Road
from app.schemas.road import RoadCreate, RoadResponse, RoadUpdate

router = APIRouter(prefix="/roads", tags=["Roads"])


def get_road_or_404(road_id: int, db: Session) -> Road:
    road = db.get(Road, road_id)
    if road is None:
        raise HTTPException(status_code=404, detail="Road not found")
    return road


def check_junctions(from_id: int, to_id: int, db: Session) -> None:
    if from_id == to_id:
        raise HTTPException(status_code=400, detail="A road must connect two different junctions")
    for junction_id in (from_id, to_id):
        if db.get(Junction, junction_id) is None:
            raise HTTPException(status_code=400, detail=f"Junction {junction_id} does not exist")


@router.post("", response_model=RoadResponse, status_code=status.HTTP_201_CREATED)
def create_road(data: RoadCreate, db: Session = Depends(get_db)):
    check_junctions(data.from_junction_id, data.to_junction_id, db)
    road = Road(**data.model_dump())
    db.add(road)
    db.commit()
    db.refresh(road)
    return road


@router.get("", response_model=list[RoadResponse])
def get_all_roads(db: Session = Depends(get_db)):
    return db.scalars(select(Road)).all()


@router.get("/{road_id}", response_model=RoadResponse)
def get_road(road_id: int, db: Session = Depends(get_db)):
    return get_road_or_404(road_id, db)


@router.put("/{road_id}", response_model=RoadResponse)
def replace_road(road_id: int, data: RoadCreate, db: Session = Depends(get_db)):
    road = get_road_or_404(road_id, db)
    check_junctions(data.from_junction_id, data.to_junction_id, db)
    for key, value in data.model_dump().items():
        setattr(road, key, value)
    db.commit()
    db.refresh(road)
    return road


@router.patch("/{road_id}", response_model=RoadResponse)
def update_road(road_id: int, data: RoadUpdate, db: Session = Depends(get_db)):
    road = get_road_or_404(road_id, db)
    changes = data.model_dump(exclude_unset=True)
    if "from_junction_id" in changes or "to_junction_id" in changes:
        check_junctions(
            changes.get("from_junction_id", road.from_junction_id),
            changes.get("to_junction_id", road.to_junction_id),
            db,
        )
    for key, value in changes.items():
        setattr(road, key, value)
    db.commit()
    db.refresh(road)
    return road

@router.delete("/{road_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_road(road_id: int, db: Session = Depends(get_db)):
    road = get_road_or_404(road_id, db)
    try:
        db.delete(road)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Road is used by a signal or reading and cannot be deleted")