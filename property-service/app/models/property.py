from sqlalchemy import Column, Integer, String, Text, Numeric, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Property(Base):
    __tablename__ = "property"
    __table_args__ = {"schema": "property_mgmt"}

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, nullable=False)  # FK на auth.app_user.id
    name = Column(String(255), nullable=False)
    address = Column(Text, nullable=False)
    description = Column(Text)
    property_type = Column(String(50), nullable=False)  # APARTMENT, HOUSE, OFFICE и т.п.
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    units = relationship("Unit", back_populates="property")


class Unit(Base):
    __tablename__ = "unit"
    __table_args__ = {"schema": "property_mgmt"}

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("property_mgmt.property.id", ondelete="CASCADE"), nullable=False)
    unit_number = Column(String(50), nullable=False)
    area = Column(Numeric(10, 2))
    floor = Column(Integer)
    status = Column(String(20), nullable=False, default="AVAILABLE")
    monthly_rent = Column(Numeric(12, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    property = relationship("Property", back_populates="units")
