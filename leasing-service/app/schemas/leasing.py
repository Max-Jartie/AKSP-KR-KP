from pydantic import BaseModel
from typing import Optional, List
from datetime import date


class LeaseBase(BaseModel):
    unit_id: int
    start_date: date
    end_date: Optional[date] = None
    monthly_rent: float
    status: str


class LeaseCreate(LeaseBase):
    pass


class LeaseRead(LeaseBase):
    id: int

    class Config:
        orm_mode = True


class PaymentBase(BaseModel):
    lease_id: int
    payment_date: date
    amount: float
    status: str
    method: Optional[str] = None


class PaymentCreate(PaymentBase):
    pass


class PaymentRead(PaymentBase):
    id: int

    class Config:
        orm_mode = True


class LeaseWithPayments(LeaseRead):
    payments: List[PaymentRead] = []