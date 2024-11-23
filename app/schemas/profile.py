# app/schemas/profile.py

from pydantic import BaseModel, EmailStr
from typing import Optional


class UserProfile(BaseModel):
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    bio: Optional[str] = None

    class Config:
        from_attributes = True

class ProfileResponse(BaseModel):
    id: int
    username:str
    email: EmailStr
    full_name: str
    phone_number: str
    bio: str
    created_at: str