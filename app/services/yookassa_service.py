import uuid
from decimal import Decimal
from typing import Any

import httpx

from app.config import settings


class YooKassaService:
    @staticmethod
    def _ensure_configured() -> None:
        if not settings.YOOKASSA_SHOP_ID or not settings.YOOKASSA_SECRET_KEY:
            raise RuntimeError("YOOKASSA_SHOP_ID/YOOKASSA_SECRET_KEY are not configured")

    @staticmethod
    async def create_payment(
        amount: Decimal,
        currency: str,
        description: str,
        return_url: str,
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        YooKassaService._ensure_configured()

        payload: dict[str, Any] = {
            "amount": {"value": f"{amount:.2f}", "currency": currency},
            "capture": True,
            "confirmation": {"type": "redirect", "return_url": return_url},
            "description": description,
            "metadata": metadata,
        }

        headers = {"Idempotence-Key": str(uuid.uuid4())}
        async with httpx.AsyncClient(
            base_url=settings.YOOKASSA_API_BASE.rstrip("/"),
            auth=(settings.YOOKASSA_SHOP_ID, settings.YOOKASSA_SECRET_KEY),
            timeout=20.0,
        ) as client:
            resp = await client.post("/v3/payments", json=payload, headers=headers)
            resp.raise_for_status()
            return resp.json()

    @staticmethod
    async def get_payment(payment_id: str) -> dict[str, Any]:
        YooKassaService._ensure_configured()
        async with httpx.AsyncClient(
            base_url=settings.YOOKASSA_API_BASE.rstrip("/"),
            auth=(settings.YOOKASSA_SHOP_ID, settings.YOOKASSA_SECRET_KEY),
            timeout=20.0,
        ) as client:
            resp = await client.get(f"/v3/payments/{payment_id}")
            resp.raise_for_status()
            return resp.json()

