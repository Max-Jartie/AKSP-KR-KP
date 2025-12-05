from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.db.session import get_db
from app.models.leasing import Payment, Lease
from app.schemas.leasing import PaymentCreate, PaymentRead
from app.core.security import get_current_user, CurrentUser

router = APIRouter()


@router.get("/", response_model=List[PaymentRead])
def list_payments(
    lease_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Получить список платежей текущего пользователя"""
    # Фильтруем только платежи по договорам текущего пользователя
    query = db.query(Payment).join(Lease).filter(Lease.user_id == current_user.id)
    
    if lease_id is not None:
        # Дополнительно проверяем, что lease принадлежит пользователю
        lease = db.query(Lease).filter(
            Lease.id == lease_id,
            Lease.user_id == current_user.id
        ).first()
        if not lease:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lease not found or access denied"
            )
        query = query.filter(Payment.lease_id == lease_id)
    
    return query.all()


@router.post("/", response_model=PaymentRead, status_code=status.HTTP_201_CREATED)
def create_payment(
    pay_in: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Создать платеж (только для договоров текущего пользователя)"""
    # Проверяем, что lease принадлежит текущему пользователю
    lease = db.query(Lease).filter(
        Lease.id == pay_in.lease_id,
        Lease.user_id == current_user.id
    ).first()
    
    if not lease:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lease not found or access denied"
        )
    
    try:
        pay = Payment(
            lease_id=pay_in.lease_id,
            payment_date=pay_in.payment_date,
            amount=pay_in.amount,
            status=pay_in.status,
            method=pay_in.method,
        )
        db.add(pay)
        db.commit()
        db.refresh(pay)
        return pay
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
            detail=f"Error creating payment: {str(e)}"
        )
