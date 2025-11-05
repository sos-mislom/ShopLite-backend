from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.user import UserCreate, UserLogin, Token
from app.database import get_db
from app.services.auth_service import AuthService
from app.schemas.user import EmailSchema, ResetPassword

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register", response_model=Token)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    new_user = await AuthService.register_user(user.email, user.password, user.name, db)
    access_token, refresh_token = await AuthService.authenticate(user.email, user.password, db)
    return Token(access_token=access_token, refresh_token=refresh_token)

@router.post("/login", response_model=Token)
async def login(user: UserLogin, db: AsyncSession = Depends(get_db)):
    access_token, refresh_token = await AuthService.authenticate(user.email, user.password, db)
    return Token(access_token=access_token, refresh_token=refresh_token)

@router.post("/forgot")
async def forgot(email: EmailSchema, db: AsyncSession = Depends(get_db)):
    await AuthService.forgot_password(email.email, db)
    return {"message": "If this email exists, reset link was sent"}

@router.post("/reset")
async def reset_password(data: ResetPassword, db: AsyncSession = Depends(get_db)):
    await AuthService.reset_password(data.token, data.new_password, db)
    return {"message": "Password successfully updated"}
