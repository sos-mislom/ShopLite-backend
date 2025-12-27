from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import Order, OrderItem, get_db
from app.schemas.order import OrderCreate, OrderOut
from app.services.yookassa_payment_service import create_payment

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.get("/store/{store_id}", response_model=list[OrderOut])
async def get_orders(store_id: int, db: AsyncSession = Depends(get_db)):
    rows = await db.execute(select(Order).where(Order.store_id == store_id))
    return rows.scalars().all()


@router.get("/{order_id}", response_model=OrderOut)
async def get_order(order_id: int, db: AsyncSession = Depends(get_db)):
    row = await db.get(Order, order_id)
    if not row:
        raise HTTPException(404, "Order not found")
    return row


@router.post("/", response_model=OrderOut)
async def create_order(payload: OrderCreate, db: AsyncSession = Depends(get_db)):
    # TODO проверку на возможность оплаты (продавец указал shop_id и secret_key магазина Юкассы)
    # как минимум на фронт проверку точно надо

    order = Order(
        store_id=payload.store_id,
        customer_email=payload.customer_email,
        customer_name=payload.customer_name,
        customer_phone=payload.customer_phone,
        shipping_address=payload.shipping_address,
        billing_address=payload.billing_address,
        total_amount=payload.total_amount,
        status="pending",
        payment_status="unpaid",
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)

    total_price = 0.0

    for item in payload.items:
        db.add(OrderItem(
            order_id=order.id,
            product_id=item.product_id,
            product_name=item.product_name,
            variant_info=item.variant_info,
            quantity=item.quantity,
            price=item.price
        ))
        total_price += item.quantity * item.price

    await db.commit()

    payment_id = await _create_yookassa_payment(order.id, total_price)
    # TODO сохранить payment_id в Order

    return order

async def _create_yookassa_payment(order_id: int, total_price: float):
    shop_id = 'shop_id' # TODO вытаскиваем эту инфу из данных магазина
    secret_key = 'secret_key' # TODO вытаскиваем эту инфу из данных магазина
    payment_data = {
        "amount": {
            "value": f"{round(total_price, 2)}",
            "currency": "RUB" # TODO хорошо бы учитывать, в какой валюте будет платить клиент, но на данном этапе не важно
        },
        "capture": True,
        "confirmation": {
            "type": "redirect",
            "return_url": "https://example.com/thank-you-page" # TODO url редиректа после оплаты
        },
        "description": f"Заказ №{order_id}", # TODO нормальное описание заказа
        "metadata": {
            "order_id": order_id
        }
    }
    return await create_payment(shop_id, secret_key, payment_data)