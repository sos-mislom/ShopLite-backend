from pydantic import BaseModel
from typing import Optional


class VisitCreate(BaseModel):
    store_id: int
    path: Optional[str] = None
    referrer: Optional[str] = None

