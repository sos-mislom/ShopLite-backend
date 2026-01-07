from decimal import Decimal

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import Order, Payment, Store, get_db
from app.services.email_service import send_order_tracking_email
from app.services.tracking_service import generate_tracking_number
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
    paid_statuses = {"succeeded", "paid"}
    was_paid = str(order.payment_status or "").lower() in paid_statuses

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
    if not order.tracking_number:
        order.tracking_number = await generate_tracking_number(db)

    await db.commit()
    if not was_paid and str(status).lower() in paid_statuses and order.customer_email and order.tracking_number:
        store = await db.get(Store, order.store_id)
        base = settings.PUBLIC_BASE_URL.rstrip("/")
        tracking_url = None
        if store and store.slug:
            tracking_url = f"{base}/s/{store.slug}?tracking={order.tracking_number}"
        elif base:
            tracking_url = f"{base}/?tracking={order.tracking_number}"
        paid_at = payment_data.get("captured_at") or payment_data.get("created_at")
        await send_order_tracking_email(
            email=order.customer_email,
            order_id=order.id,
            tracking_number=order.tracking_number,
            order_status=order.status or "",
            payment_status=str(status),
            amount=str(payment_row.amount),
            currency=str(payment_row.currency),
            payment_provider=payment_row.provider,
            payment_id=payment_row.provider_payment_id,
            paid_at=str(paid_at) if paid_at else None,
            tracking_url=tracking_url,
        )
    return {"status": "ok"}
