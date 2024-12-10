# app/schemas/auth.py

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List

# Base schema for user-related attributes
class UserBase(BaseModel):
    """
    Base schema for user-related attributes, typically used for creating or logging in users.
    
    Attributes:
        username (str): The username of the user.
    """
    email: EmailStr

# Schema for user creation (includes email and password)
class UserCreate(UserBase):
    """
    Schema for user creation, including required email and password.
    
    Attributes:
        email (EmailStr): The user's email address.
        password (str): The user's password.
    """
    username: str
    password: str

# Schema for user login (includes username and password)
class UserLogin(UserBase):
    """
    Schema for user login, requiring the username and password.
    
    Attributes:
        password (str): The user's password.
    """
    password: str

# Schema for user response (returns user info after successful creation or login)
class UserResponse(UserBase):
    """
    Schema for the user response, which includes the user ID and an optional message.
    
    Attributes:
        id (int): The unique identifier for the user.
        message (Optional[str]): An optional message (e.g., confirmation or error message).
    """
    id: int
    message: Optional[str]
    
    class Config:
        # This allows Pydantic to pull attributes from ORM models
        from_attributes = True

class RegisterResponse(BaseModel):
    username:str
    email: EmailStr
    message: str



class LoginResponse(BaseModel):
    access_token:str
    refresh_token: str
    token_type: str
    username:str
    user_id: int

class DetailResponse(BaseModel):
    detail: str

class RefreshResponse(BaseModel):
    access_token:str
    token_type: str

class RefreshToken(BaseModel):
    refresh_token: str
