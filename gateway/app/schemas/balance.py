from pydantic import BaseModel


class BalanceResponse(BaseModel):
    balance: float


class TransactionItem(BaseModel):
    id: str
    amount: float
    type: str
    description: str | None
    created_at: str

    class Config:
        from_attributes = True
