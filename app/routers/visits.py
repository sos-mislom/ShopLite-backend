from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Store, StoreVisit, get_db
from app.schemas.visit import VisitCreate

router = APIRouter(prefix="/visits", tags=["Visits"])


@router.post("")
async def create_visit(payload: VisitCreate, request: Request, db: AsyncSession = Depends(get_db)):
    store = await db.get(Store, payload.store_id)
    if not store:
        return {"status": "ignored"}

    user_agent = request.headers.get("user-agent")
    referrer = payload.referrer or request.headers.get("referer")

    row = StoreVisit(
        store_id=payload.store_id,
        path=payload.path,
        referrer=referrer,
        user_agent=user_agent,
    )
    db.add(row)
    await db.commit()
    return {"status": "ok"}

