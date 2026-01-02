from pydantic import BaseModel
from typing import Any, Optional
from datetime import datetime
from decimal import Decimal


class PaymentOut(BaseModel):
    id: int
    order_id: int
    provider: str
    provider_payment_id: str
    status: str
    amount: Decimal
    currency: str
    confirmation_url: Optional[str] = None
    raw_response: Optional[Any] = None
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True

