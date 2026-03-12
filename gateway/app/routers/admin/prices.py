from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.billing import invalidate_price_cache
from ...db.models import RoutePrice, User
from ...db.session import get_db
from ...deps import get_admin_user
from ...schemas.admin import RoutePriceItem, RoutePriceUpsert

router = APIRouter(prefix="/admin/prices", tags=["Admin – Pricing"])


@router.get("", response_model=list[RoutePriceItem])
async def list_prices(
    _: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(RoutePrice).order_by(RoutePrice.id))
    return [
        RoutePriceItem(
            id=p.id,
            route_pattern=p.route_pattern,
            method=p.method,
            cost=float(p.cost),
            description=p.description,
            is_active=p.is_active,
        )
        for p in result.scalars().all()
    ]


@router.post("", response_model=RoutePriceItem, status_code=201)
async def create_price(
    payload: RoutePriceUpsert,
    _: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    price = RoutePrice(**payload.model_dump())
    db.add(price)
    await db.commit()
    await db.refresh(price)
    invalidate_price_cache()
    return RoutePriceItem(
        id=price.id,
        route_pattern=price.route_pattern,
        method=price.method,
        cost=float(price.cost),
        description=price.description,
        is_active=price.is_active,
    )


@router.put("/{price_id}", response_model=RoutePriceItem)
async def update_price(
    price_id: int,
    payload: RoutePriceUpsert,
    _: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    price = await db.get(RoutePrice, price_id)
    if not price:
        raise HTTPException(404, "Price not found")

    for k, v in payload.model_dump().items():
        setattr(price, k, v)

    await db.commit()
    invalidate_price_cache()
    return RoutePriceItem(
        id=price.id,
        route_pattern=price.route_pattern,
        method=price.method,
        cost=float(price.cost),
        description=price.description,
        is_active=price.is_active,
    )


@router.delete("/{price_id}", status_code=204)
async def delete_price(
    price_id: int,
    _: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    price = await db.get(RoutePrice, price_id)
    if not price:
        raise HTTPException(404, "Price not found")
    await db.delete(price)
    await db.commit()
    invalidate_price_cache()
