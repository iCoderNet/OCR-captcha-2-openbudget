from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.models import Transaction, User
from ..db.session import get_db
from ..deps import get_current_user
from ..schemas.balance import BalanceResponse, TransactionItem
from ..schemas.common import PaginatedResponse

router = APIRouter(prefix="/client/balance", tags=["Balance"])


@router.get("", response_model=BalanceResponse)
async def get_balance(user: User = Depends(get_current_user)):
    return BalanceResponse(balance=float(user.balance))


@router.get("/transactions", response_model=PaginatedResponse[TransactionItem])
async def get_transactions(
    page: int = Query(0, ge=0),
    size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    total_result = await db.execute(
        select(func.count()).where(Transaction.user_id == user.id)
    )
    total = total_result.scalar()

    result = await db.execute(
        select(Transaction)
        .where(Transaction.user_id == user.id)
        .order_by(Transaction.created_at.desc())
        .offset(page * size)
        .limit(size)
    )
    txns = result.scalars().all()

    return PaginatedResponse(
        items=[
            TransactionItem(
                id=str(t.id),
                amount=float(t.amount),
                type=t.type.value,
                description=t.description,
                created_at=t.created_at.isoformat(),
            )
            for t in txns
        ],
        total=total,
        page=page,
        size=size,
        pages=-(-total // size),
    )
