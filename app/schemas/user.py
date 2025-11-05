from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str


class UserOut(BaseModel):
    id: int
    email: EmailStr

    class Config:
        orm_mode = True


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

