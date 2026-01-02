from pydantic import BaseModel, EmailStr
from typing import Any, Optional, List

from app.schemas.order import OrderOut
from app.schemas.payment import PaymentOut


class CheckoutItemIn(BaseModel):
    product_id: int
    quantity: int
    variant_info: Optional[Any] = None


class CheckoutCreate(BaseModel):
    store_id: int
    customer_email: EmailStr
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    shipping_address: Optional[Any] = None
    billing_address: Optional[Any] = None
    items: List[CheckoutItemIn]
    return_url: Optional[str] = None


class CheckoutOut(BaseModel):
    order: OrderOut
    payment: PaymentOut
    confirmation_url: str

