from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database import Order, OrderItem, get_db
from app.schemas.order import OrderCreate, OrderOut

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.get("/store/{store_id}", response_model=list[OrderOut])
async def get_orders(store_id: int, db: AsyncSession = Depends(get_db)):
    rows = await db.execute(
        select(Order)
        .where(Order.store_id == store_id)
        .options(selectinload(Order.items))
        .order_by(Order.created_at.desc())
    )
    return rows.scalars().all()


@router.get("/{order_id}", response_model=OrderOut)
async def get_order(order_id: int, db: AsyncSession = Depends(get_db)):
    q = select(Order).where(Order.id == order_id).options(selectinload(Order.items))
    res = await db.execute(q)
    row = res.scalars().first()
    if not row:
        raise HTTPException(404, "Order not found")
    return row


@router.post("/", response_model=OrderOut)
async def create_order(payload: OrderCreate, db: AsyncSession = Depends(get_db)):
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

    for item in payload.items:
        db.add(OrderItem(
            order_id=order.id,
            product_id=item.product_id,
            product_name=item.product_name,
            variant_info=item.variant_info,
            quantity=item.quantity,
            price=item.price
        ))

    await db.commit()
    q = select(Order).where(Order.id == order.id).options(selectinload(Order.items))
    res = await db.execute(q)
    return res.scalars().first()
