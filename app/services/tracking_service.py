import secrets

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Order

TRACKING_PREFIX = "SL"
TRACKING_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
TRACKING_LENGTH = 8


async def generate_tracking_number(db: AsyncSession) -> str:
    for _ in range(10):
        token = "".join(secrets.choice(TRACKING_ALPHABET) for _ in range(TRACKING_LENGTH))
        tracking_number = f"{TRACKING_PREFIX}-{token}"
        res = await db.execute(select(Order.id).where(Order.tracking_number == tracking_number))
        if res.scalar() is None:
            return tracking_number
    raise RuntimeError("Failed to generate tracking number")
