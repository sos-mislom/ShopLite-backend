from pydantic_settings import BaseSettings
from pydantic import Field
from functools import cached_property
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    POSTGRES_USER: str = Field("authuser", env="POSTGRES_USER")
    POSTGRES_PASSWORD: str = Field("authpass", env="POSTGRES_PASSWORD")
    POSTGRES_DB: str = Field("shoplite_db", env="POSTGRES_DB")
    POSTGRES_HOST: str = Field("db", env="POSTGRES_HOST")
    POSTGRES_PORT: int = Field(5432, env="POSTGRES_PORT")
    DATABASE_URL: str = Field("postgresql+psycopg2://authuser:authpass@db:5432/shoplite_db", env="DATABASE_URL")

    JWT_SECRET: str = Field("very_secret_key_change_me", env="JWT_SECRET")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(7, env="REFRESH_TOKEN_EXPIRE_DAYS")

    SMTP_USER: str = Field("", env="SMTP_USER")
    SMTP_PASSWORD: str = Field("", env="SMTP_PASSWORD")

    MEDIA_ROOT: str = Field("uploads", env="MEDIA_ROOT")
    MEDIA_URL: str = Field("/uploads", env="MEDIA_URL")
    PUBLIC_BASE_URL: str = Field("http://localhost:8000", env="PUBLIC_BASE_URL")

    YOOKASSA_SHOP_ID: str = Field("", env="YOOKASSA_SHOP_ID")
    YOOKASSA_SECRET_KEY: str = Field("", env="YOOKASSA_SECRET_KEY")
    YOOKASSA_API_BASE: str = Field("https://api.yookassa.ru", env="YOOKASSA_API_BASE")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
