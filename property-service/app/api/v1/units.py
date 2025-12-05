from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.property import Unit, Property
from app.schemas.property import UnitCreate, UnitRead
from app.core.security import get_current_user, CurrentUser
from sqlalchemy.exc import IntegrityError

router = APIRouter()


@router.get("/public", response_model=List[UnitRead])
def list_units_public(
    property_id: int = Query(..., description="ID объекта"),
    db: Session = Depends(get_db),
):
    """Публичный список помещений объекта"""
    # Проверяем, что объект существует
    property_obj = db.query(Property).filter(Property.id == property_id).first()
    if not property_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found"
        )
    
    # Возвращаем только доступные помещения
    units = db.query(Unit).filter(
        Unit.property_id == property_id,
        Unit.status == "AVAILABLE"
    ).all()
    return units


@router.get("/", response_model=List[UnitRead])
def list_units(
    property_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Получить список помещений текущего пользователя"""
    # Фильтруем только помещения, принадлежащие объектам текущего пользователя
    query = db.query(Unit).join(Property).filter(Property.user_id == current_user.id)
    
    if property_id is not None:
        # Дополнительно проверяем, что property принадлежит пользователю
        property_obj = db.query(Property).filter(
            Property.id == property_id,
            Property.user_id == current_user.id
        ).first()
        if not property_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property not found or access denied"
            )
        query = query.filter(Unit.property_id == property_id)
    
    return query.all()


@router.post("/", response_model=UnitRead, status_code=status.HTTP_201_CREATED)
def create_unit(
    unit_in: UnitCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    # Проверяем, что property принадлежит текущему пользователю
    property_obj = db.query(Property).filter(
        Property.id == unit_in.property_id,
        Property.user_id == current_user.id
    ).first()
    
    if not property_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found or access denied"
        )
    
    unit = Unit(
        property_id=unit_in.property_id,
        unit_number=unit_in.unit_number,
        area=unit_in.area,
        floor=unit_in.floor,
        status=unit_in.status,
        monthly_rent=unit_in.monthly_rent,
    )
    db.add(unit)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Unit with this number already exists in this property",
        )
    db.refresh(unit)
    return unit


@router.get("/public/{unit_id}", response_model=UnitRead)
def get_unit_public(
    unit_id: int,
    db: Session = Depends(get_db),
):
    """Получить информацию о помещении (публичный доступ)"""
    unit = db.query(Unit).filter(Unit.id == unit_id).first()
    
    if not unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unit not found"
        )
    return unit


@router.get("/{unit_id}", response_model=UnitRead)
def get_unit(
    unit_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Получить помещение (только если оно принадлежит объекту текущего пользователя)"""
    unit = db.query(Unit).join(Property).filter(
        Unit.id == unit_id,
        Property.user_id == current_user.id
    ).first()
    
    if not unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unit not found or access denied"
        )
    return unit


@router.patch("/{unit_id}/status", response_model=UnitRead)
def update_unit_status(
    unit_id: int,
    status_value: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Обновить статус помещения (только если оно принадлежит объекту текущего пользователя)"""
    unit = db.query(Unit).join(Property).filter(
        Unit.id == unit_id,
        Property.user_id == current_user.id
    ).first()
    
    if not unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unit not found or access denied"
        )
    
    unit.status = status_value
    db.commit()
    db.refresh(unit)
    return unit
