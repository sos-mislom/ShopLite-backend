from decimal import Decimal, ROUND_HALF_UP

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database import Order, OrderItem, Product, Store, get_db
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
    if payload.store_id <= 0:
        raise HTTPException(400, "store_id must be a positive integer")

    store = await db.get(Store, payload.store_id)
    if not store:
        raise HTTPException(404, "Store not found")

    if not payload.items:
        raise HTTPException(400, "items are required")

    if len(payload.items) > 200:
        raise HTTPException(400, "Too many items")

    customer_name = payload.customer_name.strip() if payload.customer_name else None
    if customer_name and len(customer_name) > 255:
        raise HTTPException(400, "customer_name is too long")

    customer_phone = payload.customer_phone.strip() if payload.customer_phone else None
    if customer_phone and len(customer_phone) > 50:
        raise HTTPException(400, "customer_phone is too long")

    product_ids = [item.product_id for item in payload.items]
    if any(pid <= 0 for pid in product_ids):
        raise HTTPException(400, "product_id must be a positive integer")

    prod_rows = await db.execute(
        select(Product).where(Product.store_id == payload.store_id, Product.id.in_(set(product_ids)))
    )
    products = {int(p.id): p for p in prod_rows.scalars().all()}

    total = Decimal("0.00")
    prepared_items: list[OrderItem] = []
    for item in payload.items:
        if item.quantity <= 0:
            raise HTTPException(400, "quantity must be > 0")
        product = products.get(int(item.product_id))
        if not product:
            raise HTTPException(400, f"Product {item.product_id} not found")

        price = Decimal(str(product.price)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        total += price * int(item.quantity)
        prepared_items.append(
            OrderItem(
                product_id=int(product.id),
                product_name=product.name,
                variant_info=item.variant_info,
                quantity=int(item.quantity),
                price=price,
            )
        )

    total = total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    order = Order(
        store_id=payload.store_id,
        customer_email=str(payload.customer_email),
        customer_name=customer_name,
        customer_phone=customer_phone,
        shipping_address=payload.shipping_address,
        billing_address=payload.billing_address,
        total_amount=total,
        status="pending",
        payment_method="offline",
        payment_status="unpaid",
    )
    order.items = prepared_items
    db.add(order)
    await db.commit()
    await db.refresh(order)
    q = select(Order).where(Order.id == order.id).options(selectinload(Order.items))
    res = await db.execute(q)
    return res.scalars().first()
