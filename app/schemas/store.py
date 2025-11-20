from pydantic import BaseModel
from datetime import datetime

class StoreCreate(BaseModel):
    name: str
    description: str | None = None
    color: str | None = None
    slug: str | None = None
    logo_url: str | None = None

class StoreOut(StoreCreate):
    id: int
    name: str
    slug: str | None = None
    created_at: datetime

    class Config:
        orm_mode = True
