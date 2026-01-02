from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Store, StoreDesign, get_db
from app.schemas.store import PublishedStoreOut
from app.config import settings

router = APIRouter(prefix="/public", tags=["Public"])


@router.get("/{slug}", response_model=PublishedStoreOut)
async def get_published_store(slug: str, db: AsyncSession = Depends(get_db)):
    normalized = slug.lower()
    store_stmt = select(Store).where(func.lower(Store.slug) == normalized)
    store_row = await db.execute(store_stmt)
    store = store_row.scalars().first()
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")

    design_stmt = select(StoreDesign).where(StoreDesign.store_id == store.id)
    design_row = await db.execute(design_stmt)
    design = design_row.scalars().first()
    if not design or not design.is_published:
        raise HTTPException(status_code=404, detail="Store is not published")

    return PublishedStoreOut(
        id=store.id,
        name=store.name,
        slug=store.slug,
        description=store.description,
        color=store.color,
        logo_url=store.logo_url,
        domain=store.domain,
        design_data=design.design_data,
        theme=design.theme,
        custom_css=design.custom_css,
        version=design.version,
        published=True,
        published_url=f"{settings.PUBLIC_BASE_URL.rstrip('/')}/s/{store.slug}",
    )
