from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.leasing import Lease
from app.schemas.leasing import LeaseCreate, LeaseRead, LeaseWithPayments
from app.core.security import get_current_user, CurrentUser

router = APIRouter()


@router.get("/", response_model=List[LeaseRead])
def list_leases(db: Session = Depends(get_db)):
    return db.query(Lease).all()


@router.post("/", response_model=LeaseRead, status_code=status.HTTP_201_CREATED)
def create_lease(
    lease_in: LeaseCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    if current_user.role != "OWNER":
        raise HTTPException(status_code=403, detail="Only owners can create leases")

    lease = Lease(
        unit_id=lease_in.unit_id,
        tenant_id=lease_in.tenant_id,
        start_date=lease_in.start_date,
        end_date=lease_in.end_date,
        monthly_rent=lease_in.monthly_rent,
        status=lease_in.status,
    )
    db.add(lease)
    db.commit()
    db.refresh(lease)
    return lease
