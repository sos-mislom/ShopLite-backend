from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Order, OrderItem, Store, StoreVisit, User, get_db
from app.schemas.analytics import AnalyticsOut, SalesPoint, TopProduct, TopStore, VisitsPoint
from app.services.auth_service import AuthService

router = APIRouter(prefix="/analytics", tags=["Analytics"])

PAID_PAYMENT_STATUSES = ("succeeded", "paid")


async def _get_owned_store(db: AsyncSession, store_id: int, user_id: int) -> Store:
    row = await db.get(Store, store_id)
    if not row or row.user_id != user_id:
        raise HTTPException(404, "Store not found")
    return row


async def _build_analytics(db: AsyncSession, store_ids: list[int], period_days: int, store_id: int | None = None) -> AnalyticsOut:
    if not store_ids:
        return AnalyticsOut(
            period_days=period_days,
            orders_total=0,
            orders_paid=0,
            revenue_paid=0.0,
            visits_total=0,
            visits_by_day=[],
            sales_by_day=[],
            top_stores=[],
            top_products=[],
            store_id=store_id,
        )

    since = datetime.utcnow() - timedelta(days=period_days)

    orders_total_stmt = select(func.count(Order.id)).where(Order.store_id.in_(store_ids), Order.created_at >= since)
    orders_paid_stmt = select(func.count(Order.id)).where(
        Order.store_id.in_(store_ids),
        Order.created_at >= since,
        Order.payment_status.in_(PAID_PAYMENT_STATUSES),
    )
    revenue_paid_stmt = select(func.coalesce(func.sum(Order.total_amount), 0)).where(
        Order.store_id.in_(store_ids),
        Order.created_at >= since,
        Order.payment_status.in_(PAID_PAYMENT_STATUSES),
    )

    orders_total = int((await db.execute(orders_total_stmt)).scalar() or 0)
    orders_paid = int((await db.execute(orders_paid_stmt)).scalar() or 0)
    revenue_paid = float((await db.execute(revenue_paid_stmt)).scalar() or 0)

    visits_total_stmt = select(func.count(StoreVisit.id)).where(
        StoreVisit.store_id.in_(store_ids), StoreVisit.created_at >= since
    )
    visits_total = int((await db.execute(visits_total_stmt)).scalar() or 0)

    visit_day = func.date_trunc("day", StoreVisit.created_at).label("day")
    visits_stmt = (
        select(visit_day, func.count(StoreVisit.id).label("visits"))
        .where(StoreVisit.store_id.in_(store_ids), StoreVisit.created_at >= since)
        .group_by(visit_day)
        .order_by(visit_day.asc())
    )
    visit_rows = (await db.execute(visits_stmt)).all()
    visits_by_day = [VisitsPoint(day=row.day, visits=int(row.visits or 0)) for row in visit_rows]

    day = func.date_trunc("day", Order.created_at).label("day")
    sales_stmt = (
        select(
            day,
            func.count(Order.id).label("orders"),
            func.coalesce(func.sum(Order.total_amount), 0).label("revenue"),
        )
        .where(
            Order.store_id.in_(store_ids),
            Order.created_at >= since,
            Order.payment_status.in_(PAID_PAYMENT_STATUSES),
        )
        .group_by(day)
        .order_by(day.asc())
    )
    sales_rows = (await db.execute(sales_stmt)).all()
    sales_by_day = [
        SalesPoint(day=row.day, orders=int(row.orders or 0), revenue=float(row.revenue or 0)) for row in sales_rows
    ]

    top_stores: list[TopStore] = []
    if store_id is None:
        top_stores_stmt = (
            select(
                Store.id.label("store_id"),
                Store.name.label("store_name"),
                func.count(Order.id).label("orders"),
                func.coalesce(func.sum(Order.total_amount), 0).label("revenue"),
            )
            .join(Order, Order.store_id == Store.id)
            .where(
                Store.id.in_(store_ids),
                Order.created_at >= since,
                Order.payment_status.in_(PAID_PAYMENT_STATUSES),
            )
            .group_by(Store.id, Store.name)
            .order_by(func.coalesce(func.sum(Order.total_amount), 0).desc())
            .limit(5)
        )
        store_rows = (await db.execute(top_stores_stmt)).all()
        top_stores = [
            TopStore(
                store_id=int(r.store_id),
                store_name=r.store_name,
                orders=int(r.orders or 0),
                revenue=float(r.revenue or 0),
            )
            for r in store_rows
        ]

    top_products_stmt = (
        select(
            OrderItem.product_id.label("product_id"),
            OrderItem.product_name.label("product_name"),
            func.coalesce(func.sum(OrderItem.quantity), 0).label("qty"),
        )
        .join(Order, Order.id == OrderItem.order_id)
        .where(
            Order.store_id.in_(store_ids),
            Order.created_at >= since,
            Order.payment_status.in_(PAID_PAYMENT_STATUSES),
        )
        .group_by(OrderItem.product_id, OrderItem.product_name)
        .order_by(func.coalesce(func.sum(OrderItem.quantity), 0).desc())
        .limit(5)
    )
    product_rows = (await db.execute(top_products_stmt)).all()
    top_products = [
        TopProduct(product_id=int(r.product_id), product_name=r.product_name, quantity=int(r.qty or 0)) for r in product_rows
    ]

    return AnalyticsOut(
        period_days=period_days,
        orders_total=orders_total,
        orders_paid=orders_paid,
        revenue_paid=revenue_paid,
        visits_total=visits_total,
        visits_by_day=visits_by_day,
        sales_by_day=sales_by_day,
        top_stores=top_stores,
        top_products=top_products,
        store_id=store_id,
    )


@router.get("/overview", response_model=AnalyticsOut)
async def analytics_overview(
    period_days: int = 30,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user),
):
    store_rows = await db.execute(select(Store.id).where(Store.user_id == current_user.id))
    store_ids = [int(r[0]) for r in store_rows.all()]
    return await _build_analytics(db, store_ids, period_days)


@router.get("/stores/{store_id}", response_model=AnalyticsOut)
async def analytics_store(
    store_id: int,
    period_days: int = 30,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user),
):
    await _get_owned_store(db, store_id, current_user.id)
    return await _build_analytics(db, [store_id], period_days, store_id=store_id)
