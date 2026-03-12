import asyncio
import time
from decimal import Decimal

from fastapi import Request
from fastapi.responses import JSONResponse, Response
from sqlalchemy import select
from starlette.middleware.base import BaseHTTPMiddleware

from ..cache.redis_client import get_redis
from ..core.billing import deduct_and_log, get_route_cost
from ..core.security import hash_api_key
from ..db.models import APIKey, User
from ..db.session import AsyncSessionLocal

# Paths that bypass API key auth entirely
_SKIP_PREFIXES = ("/auth/", "/client/", "/admin/", "/docs", "/openapi.json", "/redoc")
_SKIP_EXACT = {"/", "/health"}


def _should_skip(path: str) -> bool:
    if path in _SKIP_EXACT:
        return True
    return any(path.startswith(p) for p in _SKIP_PREFIXES)


class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        if _should_skip(path):
            return await call_next(request)

        # ── 1. Extract API key ──────────────────────────────────────────────
        raw_key = request.headers.get("X-API-Key", "").strip()
        if not raw_key:
            return JSONResponse(
                status_code=401,
                content={"ok": False, "error": "API key required. Set X-API-Key header."},
            )

        key_hash = hash_api_key(raw_key)
        redis = await get_redis()
        cache_key = f"apikey:{key_hash}"

        # ── 2. Validate key (Redis cache → DB fallback) ─────────────────────
        cached = await redis.hgetall(cache_key)

        if cached:
            user_id = cached["user_id"]
            api_key_id = cached["api_key_id"]
            is_active = cached["is_active"] == "1"
        else:
            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    select(APIKey, User)
                    .join(User, APIKey.user_id == User.id)
                    .where(APIKey.key_hash == key_hash)
                )
                row = result.first()

            if not row:
                return JSONResponse(
                    status_code=401,
                    content={"ok": False, "error": "Invalid API key"},
                )

            api_key, user = row
            is_active = api_key.is_active and user.is_active
            user_id = str(user.id)
            api_key_id = str(api_key.id)

            await redis.hset(
                cache_key,
                mapping={
                    "user_id": user_id,
                    "api_key_id": api_key_id,
                    "is_active": "1" if is_active else "0",
                },
            )
            await redis.expire(cache_key, 60)

        if not is_active:
            return JSONResponse(
                status_code=403,
                content={"ok": False, "error": "API key or account is inactive"},
            )

        # ── 3. Balance check ────────────────────────────────────────────────
        cost = await get_route_cost(request.method, path)

        async with AsyncSessionLocal() as db:
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()

        if not user or user.balance < cost:
            return JSONResponse(
                status_code=402,
                content={
                    "ok": False,
                    "error": "Insufficient balance",
                    "balance": float(user.balance) if user else 0,
                    "required": float(cost),
                },
            )

        # ── 4. Process request ──────────────────────────────────────────────
        start = time.monotonic()
        response = await call_next(request)
        response_time_ms = int((time.monotonic() - start) * 1000)

        # Read body to reconstruct response (needed to access status code)
        body = b""
        async for chunk in response.body_iterator:
            body += chunk

        # ── 5. Deduct balance asynchronously ───────────────────────────────
        task = asyncio.create_task(
            deduct_and_log(
                user_id=user_id,
                api_key_id=api_key_id,
                route=path,
                method=request.method,
                status_code=response.status_code,
                cost=cost,
                response_time_ms=response_time_ms,
                ip_address=request.client.host if request.client else None,
            )
        )

        def _on_done(t: asyncio.Task):
            if t.exception():
                import logging
                logging.getLogger(__name__).error(
                    "Billing failed: %s", t.exception()
                )

        task.add_done_callback(_on_done)

        # Invalidate cached balance (force fresh read next request)
        await redis.delete(cache_key)

        return Response(
            content=body,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type,
        )
