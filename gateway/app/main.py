from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .cache.redis_client import close_redis
from .db.base import Base
from .db.session import engine
from .middleware.auth_billing import APIKeyMiddleware
from .proxy.reverse_proxy import close_clients, init_clients
from .routers import auth, balance, keys, logs
from .routers.admin import logs as admin_logs
from .routers.admin import prices as admin_prices
from .routers.admin import users as admin_users
from .routers.proxy import router as proxy_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all tables (use Alembic in production for migrations)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await init_clients()
    yield
    await close_clients()
    await close_redis()


app = FastAPI(
    title="OpenBudget API Gateway",
    description="Pay-per-use gateway for OpenBudget.uz API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(APIKeyMiddleware)

# Client panel routes (JWT protected)
app.include_router(auth.router)
app.include_router(keys.router)
app.include_router(balance.router)
app.include_router(logs.router)

# Admin panel routes (JWT + admin role protected)
app.include_router(admin_users.router)
app.include_router(admin_prices.router)
app.include_router(admin_logs.router)

# Proxy routes (API key protected via middleware)
app.include_router(proxy_router)


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok"}
