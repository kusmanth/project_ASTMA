from datetime import datetime
from fastapi import APIRouter, status, HTTPException
from app.schemas.junction import JunctionCreate, JunctionResponse, JunctionUpdate, JunctionStatusUpdate

router = APIRouter(prefix="/junctions", tags=["junctions"])

junctions_db=[]
next_id = 1

@router.post("/", response_model=JunctionResponse,status_code=status.HTTP_201_CREATED)
def create_junction(junction: JunctionCreate):
    global next_id
    now = datetime.now()
    new_junction ={
        "id": next_id,
        **junction.model_dump(),
        "created_at": now,
        "updated_at": now,
    }
    junctions_db.append(new_junction)
    next_id += 1
    return new_junction

@router.get("/",response_model=list[JunctionResponse])
def get_all_junctions():
    return junctions_db

@router.get("/{junction_id}",response_model=JunctionResponse)
def get_junction(junction_id: int):
    for junction in junctions_db:
        if junction["id"]== junction_id:
            return junction
    raise HTTPException(status_code=404,detail="Junction not found")

@router.put("/{junction_id}",response_model=JunctionResponse)
def replace_junction(junction_id: int,junction:JunctionCreate):
    for stored in junctions_db:
        if stored["id"] == junction_id:
            stored.update(junction.model_dump())
            stored["updated_at"]= datetime.now()
            return stored
    raise HTTPException(status_code=404,detail="Junction not found")

@router.patch("/{junction_id}",response_model=JunctionResponse)
def update_junction(junction_id: int,junction:JunctionUpdate):
    for stored in junctions_db:
        if stored["id"]== junction_id:
            stored.update(junction.model_dump(exclude_unset=True))
            stored["updated_at"]= datetime.now()
            return stored
    raise HTTPException(status_code=404,detail="Junction not found")

@router.patch("/{junction_id}/status", response_model=JunctionResponse)
def update_junction_status(junction_id: int, body: JunctionStatusUpdate):
    for stored in junctions_db:
        if stored["id"] == junction_id:
            stored["is_active"]= body.is_active
            stored["updated_at"]= datetime.now()
            return stored
    raise HTTPException(status_code=404, detail="Junction not Found")

@router.delete("/{junction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_junction(juncti_id: int):
    for index, junction in enumerate(junctions_db):
        if junction["id"] == junction_id:
            junctions_db.pop(index)
            return
    raise HTTPException(status_code=404,detail="junction not found")