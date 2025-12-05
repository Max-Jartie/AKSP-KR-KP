from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import or_

from app.db.session import get_db
from app.models.property import Property
from app.schemas.property import PropertyCreate, PropertyRead, PropertyWithUnits
from app.core.security import get_current_user, CurrentUser

router = APIRouter()


@router.get("/public", response_model=List[PropertyRead])
def list_properties_public(
    name: Optional[str] = Query(None, description="Фильтр по названию"),
    address: Optional[str] = Query(None, description="Фильтр по адресу"),
    db: Session = Depends(get_db),
):
    """Публичный список всех объектов с фильтрацией"""
    query = db.query(Property)
    
    if name:
        query = query.filter(Property.name.ilike(f"%{name}%"))
    if address:
        query = query.filter(Property.address.ilike(f"%{address}%"))
    
    return query.all()


@router.get("/", response_model=List[PropertyRead])
def list_properties(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Получить список объектов текущего пользователя"""
    properties = db.query(Property).filter(Property.user_id == current_user.id).all()
    return properties


@router.get("/{property_id}", response_model=PropertyRead)
def get_property(
    property_id: int,
    db: Session = Depends(get_db),
):
    """Получить информацию об объекте (публичный доступ)"""
    property_obj = db.query(Property).filter(Property.id == property_id).first()
    if not property_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found"
        )
    return property_obj


@router.post("/", response_model=PropertyRead, status_code=status.HTTP_201_CREATED)
def create_property(
    prop_in: PropertyCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    try:
        prop = Property(
            user_id=current_user.id,
            name=prop_in.name,
            address=prop_in.address,
            description=prop_in.description,
            property_type=prop_in.property_type,
        )
        db.add(prop)
        db.commit()
        db.refresh(prop)
        return prop
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating property: {str(e)}"
        )
