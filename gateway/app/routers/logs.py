from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.models import UsageLog, User
from ..db.session import get_db
from ..deps import get_current_user
from ..schemas.common import PaginatedResponse
from ..schemas.logs import UsageLogItem

router = APIRouter(prefix="/client/logs", tags=["Usage Logs"])


@router.get("", response_model=PaginatedResponse[UsageLogItem])
async def get_logs(
    page: int = Query(0, ge=0),
    size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    total_result = await db.execute(
        select(func.count()).where(UsageLog.user_id == user.id)
    )
    total = total_result.scalar()

    result = await db.execute(
        select(UsageLog)
        .where(UsageLog.user_id == user.id)
        .order_by(UsageLog.created_at.desc())
        .offset(page * size)
        .limit(size)
    )
    logs = result.scalars().all()

    return PaginatedResponse(
        items=[
            UsageLogItem(
                id=str(l.id),
                route=l.route,
                method=l.method,
                status_code=l.status_code,
                cost=float(l.cost),
                response_time_ms=l.response_time_ms,
                ip_address=l.ip_address,
                created_at=l.created_at.isoformat(),
            )
            for l in logs
        ],
        total=total,
        page=page,
        size=size,
        pages=-(-total // size),
    )
