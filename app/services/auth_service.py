from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import timedelta
from app.database import User
from app.services.security_service import hash_password, verify_password, create_token
from app.config import settings
from app.services.email_service import send_reset_email
from jose import jwt

class AuthService:
    @staticmethod
    async def register_user(email: str, password: str, name: str, db: AsyncSession):
        query = await db.execute(select(User).where(User.email == email))
        if query.scalars().first():
            raise HTTPException(status_code=400, detail="Email already taken")

        user = User(email=email, hashed_password=hash_password(password), name=name)
        db.add(user)
        await db.commit()
        return user

    @staticmethod
    async def authenticate(email: str, password: str, db: AsyncSession):
        query = await db.execute(select(User).where(User.email == email))
        user = query.scalars().first()

        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        access_token = create_token({"sub": str(user.id)}, timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
        refresh_token = create_token({"sub": str(user.id)}, timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS))

        return access_token, refresh_token
    
    @staticmethod
    async def forgot_password(email: str, db: AsyncSession):
        query = await db.execute(select(User).where(User.email == email))
        user = query.scalars().first()

        if not user:
            return 

        reset_token = create_token({"sub": str(user.id)}, timedelta(hours=1))
        await send_reset_email(email, reset_token)

    @staticmethod
    async def reset_password(token: str, new_password: str, db: AsyncSession):
        try:
            payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
            user_id = int(payload.get("sub"))
        except:
            raise HTTPException(status_code=400, detail="Invalid or expired token")

        query = await db.execute(select(User).where(User.id == user_id))
        user = query.scalars().first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user.hashed_password = hash_password(new_password)
        await db.commit()
        return user
