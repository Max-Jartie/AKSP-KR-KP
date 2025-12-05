from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.db.session import get_db
from app.models.leasing import Lease
from app.schemas.leasing import LeaseCreate, LeaseRead, LeaseWithPayments
from app.core.security import get_current_user, CurrentUser

router = APIRouter()


@router.get("/", response_model=List[LeaseRead])
def list_leases(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Получить список договоров аренды текущего пользователя"""
    leases = db.query(Lease).filter(Lease.user_id == current_user.id).all()
    return leases


@router.post("/", response_model=LeaseRead, status_code=status.HTTP_201_CREATED)
def create_lease(
    lease_in: LeaseCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    try:
        lease = Lease(
            unit_id=lease_in.unit_id,
            user_id=current_user.id,
            start_date=lease_in.start_date,
            end_date=lease_in.end_date,
            monthly_rent=lease_in.monthly_rent,
            status=lease_in.status,
        )
        db.add(lease)
        db.commit()
        db.refresh(lease)
        return lease
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
            detail=f"Error creating lease: {str(e)}"
        )
