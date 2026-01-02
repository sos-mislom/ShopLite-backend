from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import Order, Store, User, get_db
from app.schemas.order_admin import OrderAdminOut
from app.services.auth_service import AuthService

router = APIRouter(tags=["Orders"])


class OrderUpdate(BaseModel):
    status: str | None = None
    payment_status: str | None = None
    notes: str | None = None


async def _get_owned_store(db: AsyncSession, store_id: int, user_id: int) -> Store:
    store = await db.get(Store, store_id)
    if not store or store.user_id != user_id:
        raise HTTPException(404, "Store not found")
    return store


@router.get("/orders/my", response_model=list[OrderAdminOut])
async def list_my_orders(
    status: str | None = None,
    payment_status: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user),
):
    store_rows = await db.execute(select(Store.id).where(Store.user_id == current_user.id))
    store_ids = [int(r[0]) for r in store_rows.all()]
    if not store_ids:
        return []

    q = (
        select(Order)
        .where(Order.store_id.in_(store_ids))
        .options(selectinload(Order.items), selectinload(Order.payments))
        .order_by(Order.created_at.desc())
    )
    if status:
        q = q.where(Order.status == status)
    if payment_status:
        q = q.where(Order.payment_status == payment_status)

    rows = await db.execute(q)
    return rows.scalars().all()


@router.get("/stores/{store_id}/orders", response_model=list[OrderAdminOut])
async def list_store_orders(
    store_id: int,
    status: str | None = None,
    payment_status: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user),
):
    await _get_owned_store(db, store_id, current_user.id)

    q = (
        select(Order)
        .where(Order.store_id == store_id)
        .options(selectinload(Order.items), selectinload(Order.payments))
        .order_by(Order.created_at.desc())
    )
    if status:
        q = q.where(Order.status == status)
    if payment_status:
        q = q.where(Order.payment_status == payment_status)

    rows = await db.execute(q)
    return rows.scalars().all()


@router.get("/stores/{store_id}/orders/{order_id}", response_model=OrderAdminOut)
async def get_store_order(
    store_id: int,
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user),
):
    await _get_owned_store(db, store_id, current_user.id)
    q = (
        select(Order)
        .where(Order.id == order_id, Order.store_id == store_id)
        .options(selectinload(Order.items), selectinload(Order.payments))
    )
    row = await db.execute(q)
    order = row.scalars().first()
    if not order:
        raise HTTPException(404, "Order not found")
    return order


@router.patch("/stores/{store_id}/orders/{order_id}", response_model=OrderAdminOut)
async def update_store_order(
    store_id: int,
    order_id: int,
    payload: OrderUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user),
):
    await _get_owned_store(db, store_id, current_user.id)
    q = (
        select(Order)
        .where(Order.id == order_id, Order.store_id == store_id)
        .options(selectinload(Order.items), selectinload(Order.payments))
    )
    row = await db.execute(q)
    order = row.scalars().first()
    if not order:
        raise HTTPException(404, "Order not found")

    data = payload.dict(exclude_unset=True)
    for key, value in data.items():
        setattr(order, key, value)

    await db.commit()
    await db.refresh(order)
    return order

