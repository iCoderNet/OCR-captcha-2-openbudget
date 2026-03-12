import asyncio
import logging
import re
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.models import APIKey, RoutePrice, Transaction, TransactionType, UsageLog, User
from ..db.session import AsyncSessionLocal

log = logging.getLogger(__name__)

DEFAULT_COST = Decimal("0.001000")

# Cache of compiled route patterns: list of (method, regex, cost)
_price_cache: list[tuple[str, re.Pattern, Decimal]] | None = None


def _pattern_to_regex(pattern: str) -> re.Pattern:
    """Convert '/vote/{otp_key}/verify' to a compiled regex."""
    parts = re.split(r"\{[^}]+\}", pattern)
    escaped = [re.escape(p) for p in parts]
    return re.compile("^" + "[^/]+".join(escaped) + "$")


def _match_cost(
    prices: list[tuple[str, re.Pattern, Decimal]],
    method: str,
    path: str,
) -> Decimal:
    for price_method, regex, cost in prices:
        if price_method not in ("*", method):
            continue
        if regex.match(path):
            return cost
    return DEFAULT_COST


async def load_route_prices(db: AsyncSession) -> list[tuple[str, re.Pattern, Decimal]]:
    result = await db.execute(
        select(RoutePrice).where(RoutePrice.is_active == True)
    )
    prices = result.scalars().all()
    return [(_p.method, _pattern_to_regex(_p.route_pattern), _p.cost) for _p in prices]


async def get_route_cost(method: str, path: str) -> Decimal:
    global _price_cache
    if _price_cache is None:
        async with AsyncSessionLocal() as db:
            _price_cache = await load_route_prices(db)
    return _match_cost(_price_cache, method, path)


def invalidate_price_cache():
    global _price_cache
    _price_cache = None


async def deduct_and_log(
    user_id: str,
    api_key_id: str,
    route: str,
    method: str,
    status_code: int,
    cost: Decimal,
    response_time_ms: int,
    ip_address: str | None,
):
    """Deduct balance and write logs. Run after response is sent."""
    try:
        async with AsyncSessionLocal() as db:
            async with db.begin():
                # Lock user row to prevent race conditions
                result = await db.execute(
                    select(User).where(User.id == user_id).with_for_update()
                )
                user = result.scalar_one_or_none()
                if not user:
                    return

                user.balance -= cost

                await db.execute(
                    update(APIKey)
                    .where(APIKey.id == api_key_id)
                    .values(
                        total_requests=APIKey.total_requests + 1,
                        total_spent=APIKey.total_spent + cost,
                        last_used_at=datetime.now(timezone.utc),
                    )
                )

                db.add(
                    UsageLog(
                        user_id=user_id,
                        api_key_id=api_key_id,
                        route=route,
                        method=method,
                        status_code=status_code,
                        cost=cost,
                        response_time_ms=response_time_ms,
                        ip_address=ip_address,
                    )
                )
                db.add(
                    Transaction(
                        user_id=user_id,
                        amount=-cost,
                        type=TransactionType.USAGE,
                        description=f"{method} {route}",
                    )
                )
    except Exception:
        log.exception("Billing deduction failed for user %s, route %s %s", user_id, method, route)
