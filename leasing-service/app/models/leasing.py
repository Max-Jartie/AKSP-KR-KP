from sqlalchemy import Column, Integer, String, Date, DateTime, Numeric
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Lease(Base):
    __tablename__ = "lease"
    __table_args__ = {"schema": "leasing"}

    id = Column(Integer, primary_key=True, index=True)

    unit_id = Column(Integer, nullable=False)
    tenant_id = Column(Integer, nullable=False)

    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)

    monthly_rent = Column(Numeric(12, 2), nullable=False)
    status = Column(String(20), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Payment(Base):
    __tablename__ = "payment"
    __table_args__ = {"schema": "leasing"}

    id = Column(Integer, primary_key=True, index=True)

    lease_id = Column(Integer, nullable=False)
    payment_date = Column(Date, nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    status = Column(String(20), nullable=False)
    method = Column(String(20), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
