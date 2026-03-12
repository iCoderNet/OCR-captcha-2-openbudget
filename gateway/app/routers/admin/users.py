from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...db.models import Transaction, TransactionType, User
from ...db.session import get_db
from ...deps import get_admin_user
from ...schemas.admin import GrantCreditsRequest, UserAdminItem, UserToggleRequest
from ...schemas.common import PaginatedResponse

router = APIRouter(prefix="/admin/users", tags=["Admin – Users"])


@router.get("", response_model=PaginatedResponse[UserAdminItem])
async def list_users(
    page: int = Query(0, ge=0),
    size: int = Query(20, ge=1, le=100),
    _: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    total = (await db.execute(select(func.count(User.id)))).scalar()
    result = await db.execute(
        select(User).order_by(User.created_at.desc()).offset(page * size).limit(size)
    )
    users = result.scalars().all()
    return PaginatedResponse(
        items=[
            UserAdminItem(
                id=str(u.id),
                email=u.email,
                full_name=u.full_name,
                role=u.role.value,
                is_active=u.is_active,
                balance=float(u.balance),
                created_at=u.created_at.isoformat(),
            )
            for u in users
        ],
        total=total,
        page=page,
        size=size,
        pages=-(-total // size),
    )


@router.post("/{user_id}/credits", status_code=200)
async def grant_credits(
    user_id: str,
    payload: GrantCreditsRequest,
    _: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    import uuid as _uuid
    user = await db.get(User, _uuid.UUID(user_id))
    if not user:
        raise HTTPException(404, "User not found")

    user.balance += payload.amount
    db.add(
        Transaction(
            user_id=user.id,
            amount=payload.amount,
            type=TransactionType.ADMIN_GRANT,
            description=payload.description or f"Admin grant: {payload.amount}",
        )
    )
    await db.commit()
    return {"ok": True, "new_balance": float(user.balance)}


@router.patch("/{user_id}/toggle", status_code=200)
async def toggle_user(
    user_id: str,
    payload: UserToggleRequest,
    _: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    import uuid as _uuid
    user = await db.get(User, _uuid.UUID(user_id))
    if not user:
        raise HTTPException(404, "User not found")

    user.is_active = payload.is_active
    await db.commit()
    return {"ok": True, "is_active": user.is_active}
