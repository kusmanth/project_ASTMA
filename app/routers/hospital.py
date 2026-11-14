from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
 
from app.database import get_db
from app.models import Address, Hospital, Junction
from app.schemas.hospital import HospitalCreate, HospitalResponse, HospitalUpdate
 
router = APIRouter(prefix="/hospitals", tags=["Hospitals"])
 
 
def get_hospital_or_404(hospital_id: int, db: Session) -> Hospital:
    hospital = db.get(Hospital, hospital_id)
    if hospital is None:
        raise HTTPException(status_code=404, detail="Hospital not found")
    return hospital
 
 
def check_links(changes: dict, db: Session) -> None:
    if "address_id" in changes and db.get(Address, changes["address_id"]) is None:
        raise HTTPException(status_code=400, detail=f"Address {changes['address_id']} does not exist")
    if "nearest_junction_id" in changes and db.get(Junction, changes["nearest_junction_id"]) is None:
        raise HTTPException(status_code=400, detail=f"Junction {changes['nearest_junction_id']} does not exist")
 
 
@router.post("", response_model=HospitalResponse, status_code=status.HTTP_201_CREATED)
def create_hospital(data: HospitalCreate, db: Session = Depends(get_db)):
    check_links(data.model_dump(), db)
    hospital = Hospital(**data.model_dump())
    db.add(hospital)
    db.commit()
    db.refresh(hospital)
    return hospital
 
 
@router.get("", response_model=list[HospitalResponse])
def get_all_hospitals(db: Session = Depends(get_db)):
    return db.scalars(select(Hospital)).all()
 
 
@router.get("/{hospital_id}", response_model=HospitalResponse)
def get_hospital(hospital_id: int, db: Session = Depends(get_db)):
    return get_hospital_or_404(hospital_id, db)
 
 
@router.put("/{hospital_id}", response_model=HospitalResponse)
def replace_hospital(hospital_id: int, data: HospitalCreate, db: Session = Depends(get_db)):
    hospital = get_hospital_or_404(hospital_id, db)
    changes = data.model_dump()
    check_links(changes, db)
    for key, value in changes.items():
        setattr(hospital, key, value)
    db.commit()
    db.refresh(hospital)
    return hospital
 
 
@router.patch("/{hospital_id}", response_model=HospitalResponse)
def update_hospital(hospital_id: int, data: HospitalUpdate, db: Session = Depends(get_db)):
    hospital = get_hospital_or_404(hospital_id, db)
    changes = data.model_dump(exclude_unset=True)
    check_links(changes, db)
    for key, value in changes.items():
        setattr(hospital, key, value)
    db.commit()
    db.refresh(hospital)
    return hospital
 
 
@router.delete("/{hospital_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_hospital(hospital_id: int, db: Session = Depends(get_db)):
    hospital = get_hospital_or_404(hospital_id, db)
    db.delete(hospital)
    db.commit()