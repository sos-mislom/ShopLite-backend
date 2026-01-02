from decimal import Decimal

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Order, Payment, get_db
from app.services.yookassa_service import YooKassaService

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/yookassa/webhook")
async def yookassa_webhook(payload: dict = Body(...), db: AsyncSession = Depends(get_db)):
    obj = payload.get("object") or {}
    payment_id = obj.get("id")
    if not payment_id:
        raise HTTPException(400, "Missing payment id")

    try:
        payment_data = await YooKassaService.get_payment(str(payment_id))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"YooKassa error: {e}")

    metadata = payment_data.get("metadata") or {}
    order_id = metadata.get("order_id") or metadata.get("orderId")
    if not order_id:
        return {"status": "ignored"}

    try:
        order_id_int = int(order_id)
    except ValueError:
        raise HTTPException(400, "Invalid order_id in metadata")

    order = await db.get(Order, order_id_int)
    if not order:
        return {"status": "ignored"}

    q = select(Payment).where(Payment.provider == "yookassa", Payment.provider_payment_id == str(payment_id))
    res = await db.execute(q)
    payment_row = res.scalars().first()

    amount_value = Decimal(str((payment_data.get("amount") or {}).get("value") or order.total_amount))
    currency = (payment_data.get("amount") or {}).get("currency") or "RUB"
    status = payment_data.get("status") or "unknown"
    confirmation_url = (payment_data.get("confirmation") or {}).get("confirmation_url")

    if payment_row:
        payment_row.status = status
        payment_row.amount = amount_value
        payment_row.currency = currency
        payment_row.raw_response = payment_data
        if confirmation_url:
            payment_row.confirmation_url = confirmation_url
    else:
        payment_row = Payment(
            order_id=order.id,
            provider="yookassa",
            provider_payment_id=str(payment_id),
            status=status,
            amount=amount_value,
            currency=currency,
            confirmation_url=confirmation_url,
            raw_response=payment_data,
        )
        db.add(payment_row)

    order.payment_method = "yookassa"
    order.payment_status = status

    await db.commit()
    return {"status": "ok"}

