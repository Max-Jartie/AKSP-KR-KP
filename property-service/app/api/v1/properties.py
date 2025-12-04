from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.property import Property
from app.schemas.property import PropertyCreate, PropertyRead, PropertyWithUnits
from app.core.security import get_current_user, CurrentUser

router = APIRouter()


@router.get("/", response_model=List[PropertyRead])
def list_properties(db: Session = Depends(get_db)):
    properties = db.query(Property).all()
    return properties


@router.post("/", response_model=PropertyRead, status_code=status.HTTP_201_CREATED)
def create_property(
    prop_in: PropertyCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    if current_user.role != "OWNER":
        raise HTTPException(status_code=403, detail="Only owners can create properties")

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
