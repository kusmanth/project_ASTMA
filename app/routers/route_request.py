from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Junction, Road, RouteRequest, User
from app.schemas.route_request import (
    RouteRequestCreate,
    RouteRequestResponse,
    RouteRequestUpdate,
)

router = APIRouter(prefix="/route-requests", tags=["Route Requests"])

KEEP_FOR = timedelta(hours=2)


def get_request_or_404(request_id: int, db: Session) -> RouteRequest:
    request = db.get(RouteRequest, request_id)
    if request is None:
        raise HTTPException(status_code=404, detail="Route request not found")
    return request


def check_user(user_id: int, db: Session) -> None:
    if db.get(User, user_id) is None:
        raise HTTPException(status_code=400, detail=f"User {user_id} does not exist")


def check_route(from_id: int, to_id: int, road_ids: list[int], db: Session) -> None:
    """The roads must form one connected path from the start junction to the destination."""
    if from_id == to_id:
        raise HTTPException(status_code=400, detail="Start and destination junctions must be different")
    for junction_id in (from_id, to_id):
        if db.get(Junction, junction_id) is None:
            raise HTTPException(status_code=400, detail=f"Junction {junction_id} does not exist")
    current = from_id
    for road_id in road_ids:
        road = db.get(Road, road_id)
        if road is None:
            raise HTTPException(status_code=400, detail=f"Road {road_id} does not exist")
        if road.from_junction_id != current:
            raise HTTPException(status_code=400, detail=f"Road {road_id} does not start at junction {current}")
        current = road.to_junction_id
    if current != to_id:
        raise HTTPException(status_code=400, detail=f"Route ends at junction {current}, not {to_id}")


@router.post("", response_model=RouteRequestResponse, status_code=status.HTTP_201_CREATED)
def create_route_request(data: RouteRequestCreate, db: Session = Depends(get_db)):
    check_user(data.user_id, db)
    check_route(data.from_junction_id, data.to_junction_id, data.suggested_route, db)
    expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + KEEP_FOR
    request = RouteRequest(**data.model_dump(), expires_at=expires_at)
    db.add(request)
    db.commit()
    db.refresh(request)
    return request


@router.get("", response_model=list[RouteRequestResponse])
def get_all_route_requests(db: Session = Depends(get_db)):
    return db.scalars(select(RouteRequest)).all()


@router.get("/{request_id}", response_model=RouteRequestResponse)
def get_route_request(request_id: int, db: Session = Depends(get_db)):
    return get_request_or_404(request_id, db)


@router.put("/{request_id}", response_model=RouteRequestResponse)
def replace_route_request(request_id: int, data: RouteRequestCreate, db: Session = Depends(get_db)):
    request = get_request_or_404(request_id, db)
    check_user(data.user_id, db)
    check_route(data.from_junction_id, data.to_junction_id, data.suggested_route, db)
    for key, value in data.model_dump().items():
        setattr(request, key, value)
    db.commit()
    db.refresh(request)
    return request


@router.patch("/{request_id}", response_model=RouteRequestResponse)
def update_route_request(request_id: int, data: RouteRequestUpdate, db: Session = Depends(get_db)):
    request = get_request_or_404(request_id, db)
    changes = data.model_dump(exclude_unset=True)
    if "suggested_route" in changes:
        check_route(request.from_junction_id, request.to_junction_id, changes["suggested_route"], db)
    for key, value in changes.items():
        setattr(request, key, value)
    db.commit()
    db.refresh(request)
    return request


@router.delete("/{request_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_route_request(request_id: int, db: Session = Depends(get_db)):
    request = get_request_or_404(request_id, db)
    db.delete(request)
    db.commit()