# app/schemas/auth.py

from pydantic import BaseModel, EmailStr
from typing import Optional

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    email: EmailStr
    password: str

class UserLogin(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    message: Optional[str]
    class Config:
        from_attributes = True

class AdminCreate(UserCreate):
    master_key: str