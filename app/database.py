from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Text,
    DateTime,
    ForeignKey,
    DECIMAL,
    JSON,
    Table,
)
from sqlalchemy.sql import func
from app.config import settings

# DATABASE CONNECTION
DATABASE_URL = settings.DATABASE_URL.replace(
    "postgresql+psycopg2://", "postgresql+asyncpg://"
)

engine = create_async_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

async def get_db():
    async with SessionLocal() as session:
        yield session


# ============================================
# USERS
# ============================================

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String)
    name = Column(String)
    phone = Column(String(50))
    
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    stores = relationship("Store", back_populates="user")


# ============================================
# STORES
# ============================================

class Store(Base):
    __tablename__ = "stores"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    color = Column(String(20), default="#2563EBCC")
    slug = Column(String(255), unique=True)
    logo_url = Column(Text)
    domain = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="stores")
    design = relationship(
        "StoreDesign",
        back_populates="store",
        uselist=False,
        cascade="all, delete-orphan",
    )

    products = relationship("Product", back_populates="store", cascade="all, delete-orphan")
    categories = relationship("Category", back_populates="store", cascade="all, delete-orphan")
    collections = relationship("Collection", back_populates="store", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="store", cascade="all, delete-orphan")


# ============================================
# STORE DESIGN (JSONB)
# ============================================

class StoreDesign(Base):
    __tablename__ = "store_designs"

    id = Column(Integer, primary_key=True)
    store_id = Column(Integer, ForeignKey("stores.id"), unique=True, nullable=False)
    design_data = Column(JSON, nullable=False)
    theme = Column(JSON)
    custom_css = Column(Text)
    is_published = Column(Boolean, default=False)
    version = Column(Integer, default=1)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    store = relationship("Store", back_populates="design")


# ============================================
# CATEGORIES
# ============================================

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    parent_id = Column(Integer, ForeignKey("categories.id"))
    image_url = Column(Text)
    order_index = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    store = relationship("Store", back_populates="categories")
    parent = relationship("Category", remote_side=[id])


# ============================================
# COLLECTIONS
# ============================================

class Collection(Base):
    __tablename__ = "collections"

    id = Column(Integer, primary_key=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    image_url = Column(Text)
    is_active = Column(Boolean, default=True)
    order_index = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    store = relationship("Store", back_populates="collections")

    products = relationship(
        "Product",
        secondary="collection_products",
        back_populates="collections",
    )


# ============================================
# PRODUCTS
# ============================================

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"))
    name = Column(String(255), nullable=False)
    description = Column(Text)
    price = Column(DECIMAL(10, 2), nullable=False)
    compare_at_price = Column(DECIMAL(10, 2))
    sku = Column(String(100), unique=True)
    barcode = Column(String(100))
    stock = Column(Integer, default=0)
    status = Column(String(20), default="active")
    images = Column(JSON)
    variants = Column(JSON)
    meta_title = Column(String(255))
    meta_description = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    store = relationship("Store", back_populates="products")
    category = relationship("Category")

    collections = relationship(
        "Collection",
        secondary="collection_products",
        back_populates="products",
    )


# ============================================
# COLLECTION-PRODUCT RELATION
# ============================================

class CollectionProduct(Base):
    __tablename__ = "collection_products"

    id = Column(Integer, primary_key=True)
    collection_id = Column(Integer, ForeignKey("collections.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    order_index = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())


# ============================================
# ORDERS
# ============================================

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False)
    customer_email = Column(String(255), nullable=False)
    customer_name = Column(String(255))
    customer_phone = Column(String(50))
    shipping_address = Column(JSON)
    billing_address = Column(JSON)
    total_amount = Column(DECIMAL(10, 2), nullable=False)
    status = Column(String(50), default="pending")
    payment_method = Column(String(50))
    payment_status = Column(String(50), default="unpaid")
    tracking_number = Column(String(32), unique=True, index=True)
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    store = relationship("Store", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="order", cascade="all, delete-orphan")


# ============================================
# ORDER ITEMS
# ============================================

class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    product_name = Column(String(255), nullable=False)
    variant_info = Column(JSON)
    quantity = Column(Integer, nullable=False)
    price = Column(DECIMAL(10, 2), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    order = relationship("Order", back_populates="items")


# ============================================
# PAYMENTS
# ============================================

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    provider = Column(String(50), nullable=False)
    provider_payment_id = Column(String(128), nullable=False, unique=True)
    status = Column(String(50), nullable=False)
    amount = Column(DECIMAL(10, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="RUB")
    confirmation_url = Column(Text)
    raw_response = Column(JSON)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    order = relationship("Order", back_populates="payments")


# ============================================
# STORE VISITS
# ============================================

class StoreVisit(Base):
    __tablename__ = "store_visits"

    id = Column(Integer, primary_key=True)
    store_id = Column(Integer, ForeignKey("stores.id", ondelete="CASCADE"), nullable=False)
    path = Column(Text)
    referrer = Column(Text)
    user_agent = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

    store = relationship("Store")
