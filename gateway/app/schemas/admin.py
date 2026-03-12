from pydantic import BaseModel, EmailStr
from decimal import Decimal


class UserAdminItem(BaseModel):
    id: str
    email: str
    full_name: str | None
    role: str
    is_active: bool
    balance: float
    created_at: str

    class Config:
        from_attributes = True


class GrantCreditsRequest(BaseModel):
    amount: Decimal
    description: str | None = None


class UserToggleRequest(BaseModel):
    is_active: bool


class RoutePriceItem(BaseModel):
    id: int
    route_pattern: str
    method: str
    cost: float
    description: str | None
    is_active: bool

    class Config:
        from_attributes = True


class RoutePriceUpsert(BaseModel):
    route_pattern: str
    method: str = "*"
    cost: Decimal
    description: str | None = None
    is_active: bool = True
