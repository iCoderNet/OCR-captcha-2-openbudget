"""
Run once to create the first admin user and default route prices.
Usage: python -m scripts.seed  (from inside gateway/)
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from decimal import Decimal
from app.config import settings
from app.db.base import Base
from app.db.session import engine, AsyncSessionLocal
from app.db.models import RoutePrice, User, UserRole
from app.core.security import hash_password
from sqlalchemy import select

DEFAULT_PRICES = [
    ("GET",  "/boards",                              Decimal("0.0001"), "Board list"),
    ("GET",  "/budget-params",                       Decimal("0.0001"), "Budget params"),
    ("GET",  "/news",                                Decimal("0.0001"), "News list"),
    ("GET",  "/initiatives/{initiative_id}",         Decimal("0.0002"), "Single initiative"),
    ("GET",  "/my-school/boards/active",             Decimal("0.0001"), "School boards"),
    ("GET",  "/board/{board_id}/initiatives",        Decimal("0.0002"), "Board initiatives"),
    ("GET",  "/initiative/{initiative_id}/count",    Decimal("0.0001"), "Vote count"),
    ("GET",  "/statistics/boards",                   Decimal("0.0002"), "Board statistics"),
    ("GET",  "/statistics/board/{board_id}/budget",  Decimal("0.0002"), "Board budget stats"),
    ("GET",  "/votes/{initiative_token}",            Decimal("0.0002"), "Vote list"),
    ("GET",  "/captcha/solve",                       Decimal("0.0050"), "Captcha OCR solve"),
    ("POST", "/vote/start",                          Decimal("0.0100"), "Vote start (captcha+OTP)"),
    ("POST", "/vote/{otp_key}/verify",               Decimal("0.0050"), "Vote OTP verify"),
    ("POST", "/vote/initiative-token",               Decimal("0.0050"), "Initiative token"),
]


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        # Admin user
        existing = (await db.execute(select(User).where(User.role == UserRole.ADMIN))).scalar_one_or_none()
        if not existing:
            admin = User(
                email=settings.ADMIN_EMAIL,
                password_hash=hash_password(settings.ADMIN_PASSWORD),
                full_name=settings.ADMIN_FULL_NAME,
                role=UserRole.ADMIN,
            )
            db.add(admin)
            print(f"✓ Admin created: {settings.ADMIN_EMAIL}")
        else:
            print(f"  Admin already exists: {existing.email}")

        # Route prices
        for method, pattern, cost, desc in DEFAULT_PRICES:
            exists = (
                await db.execute(
                    select(RoutePrice).where(
                        RoutePrice.route_pattern == pattern,
                        RoutePrice.method == method,
                    )
                )
            ).scalar_one_or_none()
            if not exists:
                db.add(RoutePrice(route_pattern=pattern, method=method, cost=cost, description=desc))
                print(f"✓ Price: {method} {pattern} → ${cost}")

        await db.commit()
        print("Seed complete.")


if __name__ == "__main__":
    asyncio.run(seed())
