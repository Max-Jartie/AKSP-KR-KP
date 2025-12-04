from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.property import Unit
from app.schemas.property import UnitCreate, UnitRead

router = APIRouter()


@router.get("/", response_model=List[UnitRead])
def list_units(property_id: int | None = None, db: Session = Depends(get_db)):
    query = db.query(Unit)
    if property_id is not None:
        query = query.filter(Unit.property_id == property_id)
    return query.all()


@router.post("/", response_model=UnitRead, status_code=status.HTTP_201_CREATED)
def create_unit(unit_in: UnitCreate, db: Session = Depends(get_db)):
    unit = Unit(
        property_id=unit_in.property_id,
        unit_number=unit_in.unit_number,
        area=unit_in.area,
        floor=unit_in.floor,
        status=unit_in.status,
        monthly_rent=unit_in.monthly_rent,
    )
    db.add(unit)
    db.commit()
    db.refresh(unit)
    return unit


@router.get("/{unit_id}", response_model=UnitRead)
def get_unit(unit_id: int, db: Session = Depends(get_db)):
    unit = db.query(Unit).filter(Unit.id == unit_id).first()
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    return unit


@router.patch("/{unit_id}/status", response_model=UnitRead)
def update_unit_status(unit_id: int, status_value: str, db: Session = Depends(get_db)):
    unit = db.query(Unit).filter(Unit.id == unit_id).first()
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    unit.status = status_value
    db.commit()
    db.refresh(unit)
    return unit
