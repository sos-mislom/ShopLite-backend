from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str


class UserOut(BaseModel):
    id: int
    email: EmailStr
    name: str | None = None
    phone: str | None = None

    class Config:
        orm_mode = True


class UserUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class EmailSchema(BaseModel):
    email: EmailStr
    
class ResetPassword(BaseModel):
    token: str
    new_password: str


class RefreshToken(BaseModel):
    refresh_token: str
