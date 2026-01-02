from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database import Order, OrderItem, Payment, Product, Store, get_db
from app.schemas.checkout import CheckoutCreate, CheckoutOut
from app.services.yookassa_service import YooKassaService

router = APIRouter(prefix="/checkout", tags=["Checkout"])


@router.post("/yookassa", response_model=CheckoutOut)
async def checkout_yookassa(payload: CheckoutCreate, db: AsyncSession = Depends(get_db)):
    store = await db.get(Store, payload.store_id)
    if not store:
        raise HTTPException(404, "Store not found")

    if not payload.items:
        raise HTTPException(400, "items are required")

    product_ids = [item.product_id for item in payload.items]
    prod_rows = await db.execute(
        select(Product).where(Product.store_id == payload.store_id, Product.id.in_(product_ids))
    )
    products = {p.id: p for p in prod_rows.scalars().all()}

    total = Decimal("0.00")
    prepared_items: list[OrderItem] = []
    for item in payload.items:
        if item.quantity <= 0:
            raise HTTPException(400, "quantity must be > 0")
        product = products.get(item.product_id)
        if not product:
            raise HTTPException(400, f"Product {item.product_id} not found")
        price = Decimal(str(product.price))
        total += price * item.quantity
        prepared_items.append(
            OrderItem(
                product_id=product.id,
                product_name=product.name,
                variant_info=item.variant_info,
                quantity=item.quantity,
                price=price,
            )
        )

    order = Order(
        store_id=payload.store_id,
        customer_email=str(payload.customer_email),
        customer_name=payload.customer_name,
        customer_phone=payload.customer_phone,
        shipping_address=payload.shipping_address,
        billing_address=payload.billing_address,
        total_amount=total,
        status="pending",
        payment_method="yookassa",
        payment_status="pending",
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)

    for oi in prepared_items:
        oi.order_id = order.id
        db.add(oi)
    await db.commit()

    return_url = payload.return_url
    if not return_url:
        base = settings.PUBLIC_BASE_URL.rstrip("/")
        if store.slug:
            return_url = f"{base}/s/{store.slug}?orderId={order.id}"
        else:
            return_url = f"{base}/?orderId={order.id}"

    try:
        payment_data = await YooKassaService.create_payment(
            amount=total,
            currency="RUB",
            description=f"Order #{order.id}",
            return_url=return_url,
            metadata={"order_id": str(order.id), "store_id": str(store.id)},
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"YooKassa error: {e}")

    confirmation_url = (
        (payment_data.get("confirmation") or {}).get("confirmation_url")
        or (payment_data.get("confirmation") or {}).get("confirmationUrl")
    )
    if not confirmation_url:
        raise HTTPException(502, "YooKassa did not return confirmation_url")

    provider_payment_id = payment_data.get("id")
    if not provider_payment_id:
        raise HTTPException(502, "YooKassa did not return payment id")

    payment = Payment(
        order_id=order.id,
        provider="yookassa",
        provider_payment_id=str(provider_payment_id),
        status=payment_data.get("status") or "pending",
        amount=total,
        currency=(payment_data.get("amount") or {}).get("currency") or "RUB",
        confirmation_url=confirmation_url,
        raw_response=payment_data,
    )
    db.add(payment)
    order.payment_status = payment.status
    await db.commit()

    order_q = select(Order).where(Order.id == order.id).options(selectinload(Order.items))
    order_res = await db.execute(order_q)
    order_full = order_res.scalars().first()
    await db.refresh(payment)

    return CheckoutOut(order=order_full, payment=payment, confirmation_url=confirmation_url)
