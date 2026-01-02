from pydantic import BaseModel, EmailStr
from typing import Optional, List, Any
from datetime import datetime


class OrderItemIn(BaseModel):
    product_id: int
    product_name: str
    variant_info: Optional[Any] = None
    quantity: int
    price: float


class OrderBase(BaseModel):
    store_id: int
    customer_email: str
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    shipping_address: Optional[Any] = None
    billing_address: Optional[Any] = None
    total_amount: float


class OrderCreate(OrderBase):
    customer_email: EmailStr
    items: List[OrderItemIn]


class OrderItemOut(OrderItemIn):
    id: int
    order_id: int

    class Config:
        orm_mode = True


class OrderOut(OrderBase):
    id: int
    status: str
    payment_method: Optional[str] = None
    payment_status: str
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    items: List[OrderItemOut] = []

    class Config:
        orm_mode = True
