import math

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Category, Product, Store, get_db
from app.schemas.product import ProductCreate, ProductForm, ProductOut

router = APIRouter(tags=["Products"])

ALLOWED_PRODUCT_STATUSES = {"active", "draft", "archived"}


def _normalize_string(value: object, *, field: str, max_len: int | None = None) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        normalized = value.strip()
    else:
        normalized = str(value).strip()
    if not normalized:
        return None
    if max_len is not None and len(normalized) > max_len:
        raise HTTPException(400, f"{field} is too long")
    return normalized


def _require_string(value: object, *, field: str, max_len: int | None = None) -> str:
    normalized = _normalize_string(value, field=field, max_len=max_len)
    if not normalized:
        raise HTTPException(400, f"{field} is required")
    return normalized


def _parse_non_negative_int(value: object, *, field: str) -> int:
    if value is None:
        return 0
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        raise HTTPException(400, f"{field} must be an integer")
    if parsed < 0:
        raise HTTPException(400, f"{field} must be >= 0")
    return parsed


def _parse_non_negative_float(value: object, *, field: str) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        raise HTTPException(400, f"{field} must be a number")
    if not math.isfinite(parsed) or parsed < 0:
        raise HTTPException(400, f"{field} must be >= 0")
    return parsed


async def _get_store(db: AsyncSession, store_id: int) -> Store:
    if store_id <= 0:
        raise HTTPException(400, "store_id must be a positive integer")
    store = await db.get(Store, store_id)
    if not store:
        raise HTTPException(404, "Store not found")
    return store


async def _validate_product_data(db: AsyncSession, store_id: int, data: dict, product_id: int | None = None) -> dict:
    data["name"] = _require_string(data.get("name"), field="name", max_len=255)
    if "status" in data:
        status = _normalize_string(data.get("status"), field="status", max_len=20) or "active"
        if status not in ALLOWED_PRODUCT_STATUSES:
            raise HTTPException(400, f"status must be one of: {', '.join(sorted(ALLOWED_PRODUCT_STATUSES))}")
        data["status"] = status

    data["price"] = _parse_non_negative_float(data.get("price"), field="price")
    if data.get("compare_at_price") is not None:
        data["compare_at_price"] = _parse_non_negative_float(data.get("compare_at_price"), field="compare_at_price")

    if "stock" in data:
        data["stock"] = _parse_non_negative_int(data.get("stock"), field="quantity")

    if "sku" in data:
        sku = _normalize_string(data.get("sku"), field="sku", max_len=100)
        data["sku"] = sku
        if sku:
            stmt = select(Product.id).where(Product.sku == sku)
            if product_id is not None:
                stmt = stmt.where(Product.id != product_id)
            existing = (await db.execute(stmt)).scalar()
            if existing:
                raise HTTPException(400, "SKU already taken")

    if data.get("category_id") is not None:
        try:
            category_id = int(data["category_id"])
        except (TypeError, ValueError):
            raise HTTPException(400, "category_id must be an integer")
        if category_id <= 0:
            raise HTTPException(400, "category_id must be a positive integer")
        category = await db.get(Category, category_id)
        if not category or category.store_id != store_id:
            raise HTTPException(400, "Invalid category_id for this store")
        data["category_id"] = category_id

    return data


async def _get_product(db: AsyncSession, prod_id: int, store_id: int | None = None) -> Product:
    product = await db.get(Product, prod_id)
    if not product:
        raise HTTPException(404, "Product not found")
    if store_id is not None and product.store_id != store_id:
        raise HTTPException(404, "Product not found for this store")
    return product


def _prepare_product_data(store_id: int, payload: dict) -> dict:
    data = payload.copy()
    data["store_id"] = store_id

    if "quantity" in data:
        data["stock"] = data.pop("quantity") or 0

    variants = data.pop("variants", {}) or {}
    if data.get("size"):
        variants["size"] = data.pop("size")
    if data.get("color"):
        variants["color"] = data.pop("color")
    if "hasLimit" in data:
        variants["hasLimit"] = data.pop("hasLimit")
    if variants:
        data["variants"] = variants

    data.pop("id", None)
    return data


@router.get("/products/store/{store_id}", response_model=list[ProductOut])
@router.get("/stores/{store_id}/products", response_model=list[ProductOut])
async def get_products(store_id: int, status: str = "all", db: AsyncSession = Depends(get_db)):
    query = select(Product).where(Product.store_id == store_id)
    if status != "all":
        query = query.where(Product.status == status)
    rows = await db.execute(query)
    return rows.scalars().all()


@router.get("/products/{prod_id}", response_model=ProductOut)
async def get_product(prod_id: int, db: AsyncSession = Depends(get_db)):
    return await _get_product(db, prod_id)


@router.post("/products", response_model=ProductOut)
async def create_product(payload: ProductCreate, db: AsyncSession = Depends(get_db)):
    if not payload.store_id:
        raise HTTPException(400, "store_id is required")

    await _get_store(db, int(payload.store_id))
    data = _prepare_product_data(int(payload.store_id), payload.dict())
    await _validate_product_data(db, int(payload.store_id), data)
    prod = Product(**data)
    db.add(prod)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(400, "Invalid product data")
    await db.refresh(prod)
    return prod


@router.post("/stores/{store_id}/products", response_model=ProductOut)
async def create_store_product(store_id: int, payload: ProductForm, db: AsyncSession = Depends(get_db)):
    await _get_store(db, store_id)
    data = _prepare_product_data(store_id, payload.dict())
    await _validate_product_data(db, store_id, data)
    prod = Product(**data)
    db.add(prod)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(400, "Invalid product data")
    await db.refresh(prod)
    return prod


@router.put("/products/{prod_id}", response_model=ProductOut)
async def update_product(prod_id: int, payload: ProductCreate, db: AsyncSession = Depends(get_db)):
    row = await _get_product(db, prod_id)

    if payload.store_id and int(payload.store_id) != int(row.store_id):
        raise HTTPException(400, "store_id cannot be changed")

    data = _prepare_product_data(int(row.store_id), payload.dict(exclude_unset=True))
    await _validate_product_data(db, int(row.store_id), data, product_id=int(row.id))
    for k, v in data.items():
        setattr(row, k, v)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(400, "Invalid product data")
    await db.refresh(row)
    return row


@router.put("/stores/{store_id}/products/{prod_id}", response_model=ProductOut)
async def update_store_product(store_id: int, prod_id: int, payload: ProductForm, db: AsyncSession = Depends(get_db)):
    row = await _get_product(db, prod_id, store_id)
    data = _prepare_product_data(store_id, payload.dict(exclude_unset=True))
    await _validate_product_data(db, store_id, data, product_id=int(row.id))
    for k, v in data.items():
        setattr(row, k, v)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(400, "Invalid product data")
    await db.refresh(row)
    return row


@router.delete("/products/{prod_id}")
async def delete_product(prod_id: int, db: AsyncSession = Depends(get_db)):
    row = await _get_product(db, prod_id)
    await db.delete(row)
    await db.commit()
    return {"status": "ok"}


@router.delete("/stores/{store_id}/products/{prod_id}")
async def delete_store_product(store_id: int, prod_id: int, db: AsyncSession = Depends(get_db)):
    row = await _get_product(db, prod_id, store_id)
    await db.delete(row)
    await db.commit()
    return {"status": "ok"}
