from pydantic import BaseModel
from typing import Optional, List


class PropertyBase(BaseModel):
    name: str
    address: str
    description: Optional[str] = None
    property_type: str


class PropertyCreate(PropertyBase):
    owner_id: int


class PropertyRead(PropertyBase):
    id: int

    class Config:
        orm_mode = True


class UnitBase(BaseModel):
    property_id: int
    unit_number: str
    area: Optional[float] = None
    floor: Optional[int] = None
    status: str = "AVAILABLE"
    monthly_rent: float


class UnitCreate(UnitBase):
    pass


class UnitRead(UnitBase):
    id: int

    class Config:
        orm_mode = True


class PropertyWithUnits(PropertyRead):
    units: List[UnitRead] = []
