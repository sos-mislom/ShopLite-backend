from typing import List

from app.schemas.order import OrderOut
from app.schemas.payment import PaymentOut


class OrderAdminOut(OrderOut):
    payments: List[PaymentOut] = []

