from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings
from sqlalchemy import Column, Integer, String, Boolean

DATABASE_URL = settings.DATABASE_URL.replace("postgresql+psycopg2://", "postgresql+asyncpg://")

engine = create_async_engine(DATABASE_URL, echo=False)

SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()

async def get_db():
    async with SessionLocal() as session:
        yield session


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    name = Column(String)
