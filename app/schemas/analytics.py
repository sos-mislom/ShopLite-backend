from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class VisitsPoint(BaseModel):
    day: datetime
    visits: int


class SalesPoint(BaseModel):
    day: datetime
    orders: int
    revenue: float


class TopStore(BaseModel):
    store_id: int
    store_name: str
    orders: int
    revenue: float


class TopProduct(BaseModel):
    product_id: int
    product_name: str
    quantity: int


class AnalyticsOut(BaseModel):
    period_days: int
    orders_total: int
    orders_paid: int
    revenue_paid: float
    visits_total: int
    visits_by_day: List[VisitsPoint] = []
    sales_by_day: List[SalesPoint] = []
    top_stores: List[TopStore] = []
    top_products: List[TopProduct] = []
    store_id: Optional[int] = None
