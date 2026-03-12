from pydantic import BaseModel


class UsageLogItem(BaseModel):
    id: str
    route: str
    method: str
    status_code: int | None
    cost: float
    response_time_ms: int | None
    ip_address: str | None
    created_at: str
    # For admin view
    user_email: str | None = None
    api_key_name: str | None = None

    class Config:
        from_attributes = True
