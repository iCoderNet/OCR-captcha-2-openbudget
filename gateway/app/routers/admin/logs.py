from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...db.models import APIKey, UsageLog, User
from ...db.session import get_db
from ...deps import get_admin_user
from ...schemas.common import PaginatedResponse
from ...schemas.logs import UsageLogItem

router = APIRouter(prefix="/admin/logs", tags=["Admin – Logs"])


@router.get("", response_model=PaginatedResponse[UsageLogItem])
async def all_logs(
    page: int = Query(0, ge=0),
    size: int = Query(20, ge=1, le=100),
    _: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    total = (await db.execute(select(func.count(UsageLog.id)))).scalar()

    result = await db.execute(
        select(UsageLog)
        .options(selectinload(UsageLog.user), selectinload(UsageLog.api_key))
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
                user_email=l.user.email if l.user else None,
                api_key_name=l.api_key.name if l.api_key else None,
            )
            for l in logs
        ],
        total=total,
        page=page,
        size=size,
        pages=-(-total // size),
    )
