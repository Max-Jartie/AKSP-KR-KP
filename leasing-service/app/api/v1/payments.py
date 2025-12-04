from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.leasing import Payment
from app.schemas.leasing import PaymentCreate, PaymentRead
from app.core.security import get_current_user, CurrentUser

router = APIRouter()


@router.get("/", response_model=List[PaymentRead])
def list_payments(lease_id: int | None = None, db: Session = Depends(get_db)):
    query = db.query(Payment)
    if lease_id is not None:
        query = query.filter(Payment.lease_id == lease_id)
    return query.all()


@router.post("/", response_model=PaymentRead, status_code=status.HTTP_201_CREATED)
def create_payment(
    pay_in: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    if current_user.role not in ("OWNER", "TENANT"):
        raise HTTPException(status_code=403, detail="Not allowed")

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
