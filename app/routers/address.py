from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Address
from app.schemas.address import AddressCreate, AddressResponse, AddressUpdate

router = APIRouter(prefix="/address", tags=["Address"])


def get_address_or_404(address_id: int, db: Session) -> Address:
    address = db.get(Address, address_id)
    if address is None:
        raise HTTPException(status_code=404, detail="Address not found")
    return address


@router.post("/", response_model=AddressResponse, status_code=status.HTTP_201_CREATED)
def create_address(data: AddressCreate, db: Session = Depends(get_db)):
    address = Address(**data.model_dump())
    db.add(address)
    db.commit()
    db.refresh(address)
    return address


@router.get("/", response_model=list[AddressResponse])
def get_all_addresses(db: Session = Depends(get_db)):
    return db.scalars(select(Address)).all()


@router.get("/{address_id}", response_model=AddressResponse)
def get_address(address_id: int, db: Session = Depends(get_db)):
    return get_address_or_404(address_id, db)


@router.put("/{address_id}", response_model=AddressResponse)
def replace_address(address_id: int, data: AddressCreate, db: Session = Depends(get_db)):
    address = get_address_or_404(address_id, db)
    for key, value in data.model_dump().items():
        setattr(address, key, value)
    db.commit()
    db.refresh(address)
    return address


@router.patch("/{address_id}", response_model=AddressResponse)
def update_address(address_id: int, data: AddressUpdate, db: Session = Depends(get_db)):
    address = get_address_or_404(address_id, db)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(address, key, value)
    db.commit()
    db.refresh(address)
    return address


@router.delete("/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_address(address_id: int, db: Session = Depends(get_db)):
    address = get_address_or_404(address_id, db)
    try:
        db.delete(address)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Address is used by a junction and cannot be deleted")