from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.property import Property
from app.schemas.property import PropertyCreate, PropertyRead, PropertyWithUnits

router = APIRouter()


@router.get("/", response_model=List[PropertyRead])
def list_properties(db: Session = Depends(get_db)):
    properties = db.query(Property).all()
    return properties


@router.post("/", response_model=PropertyRead, status_code=status.HTTP_201_CREATED)
def create_property(prop_in: PropertyCreate, db: Session = Depends(get_db)):
    prop = Property(
        owner_id=prop_in.owner_id,
        name=prop_in.name,
        address=prop_in.address,
        description=prop_in.description,
        property_type=prop_in.property_type,
    )
    db.add(prop)
    db.commit()
    db.refresh(prop)
    return prop


@router.get("/{property_id}", response_model=PropertyWithUnits)
def get_property(property_id: int, db: Session = Depends(get_db)):
    prop = (
        db.query(Property)
        .filter(Property.id == property_id)
        .first()
    )
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    return prop


@router.delete("/{property_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_property(property_id: int, db: Session = Depends(get_db)):
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    db.delete(prop)
    db.commit()
    return
