from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..cache.redis_client import get_redis
from ..core.security import generate_api_key, hash_api_key
from ..db.models import APIKey, User
from ..db.session import get_db
from ..deps import get_current_user
from ..schemas.keys import ApiKeyCreate, ApiKeyCreatedResponse, ApiKeyItem, ApiKeyToggleResponse

router = APIRouter(prefix="/client/keys", tags=["API Keys"])


@router.get("", response_model=list[ApiKeyItem])
async def list_keys(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(APIKey).where(APIKey.user_id == user.id).order_by(APIKey.created_at.desc())
    )
    keys = result.scalars().all()
    return [
        ApiKeyItem(
            id=str(k.id),
            name=k.name,
            is_active=k.is_active,
            total_requests=k.total_requests,
            total_spent=float(k.total_spent),
            created_at=k.created_at.isoformat(),
            last_used_at=k.last_used_at.isoformat() if k.last_used_at else None,
        )
        for k in keys
    ]


@router.post("", response_model=ApiKeyCreatedResponse, status_code=201)
async def create_key(
    payload: ApiKeyCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    raw_key = generate_api_key()
    key = APIKey(
        user_id=user.id,
        key_hash=hash_api_key(raw_key),
        name=payload.name,
    )
    db.add(key)
    await db.commit()
    await db.refresh(key)

    return ApiKeyCreatedResponse(
        id=str(key.id),
        name=key.name,
        raw_key=raw_key,  # shown only once
        created_at=key.created_at.isoformat(),
    )


@router.patch("/{key_id}/toggle", response_model=ApiKeyToggleResponse)
async def toggle_key(
    key_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    result = await db.execute(
        select(APIKey).where(APIKey.id == key_id, APIKey.user_id == user.id)
    )
    key = result.scalar_one_or_none()
    if not key:
        raise HTTPException(404, "Key not found")

    key.is_active = not key.is_active
    await db.commit()

    # Invalidate Redis cache so change takes effect immediately
    # (we don't store the raw key, so we can't invalidate by hash here)
    # The cache TTL (60s) will handle eventual consistency
    return ApiKeyToggleResponse(id=str(key.id), is_active=key.is_active)


@router.delete("/{key_id}", status_code=204)
async def delete_key(
    key_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(APIKey).where(APIKey.id == key_id, APIKey.user_id == user.id)
    )
    key = result.scalar_one_or_none()
    if not key:
        raise HTTPException(404, "Key not found")

    await db.delete(key)
    await db.commit()
