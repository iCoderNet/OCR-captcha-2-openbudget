from datetime import datetime
from pydantic import BaseModel


class ApiKeyCreate(BaseModel):
    name: str = "My Key"


class ApiKeyCreatedResponse(BaseModel):
    id: str
    name: str
    raw_key: str  # shown only once
    created_at: str


class ApiKeyItem(BaseModel):
    id: str
    name: str
    is_active: bool
    total_requests: int
    total_spent: float
    created_at: str
    last_used_at: str | None

    class Config:
        from_attributes = True


class ApiKeyToggleResponse(BaseModel):
    id: str
    is_active: bool
