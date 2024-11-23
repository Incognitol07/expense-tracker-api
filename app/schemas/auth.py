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

class GroupResponse(BaseModel):
    group_id: int
    group_role: str
    group_name: str

class LoginResponse(BaseModel):
    access_token:str
    token_type: str
    username:str
    user_id: int
    group_ids: List[GroupResponse]=None

class MessageResponse(BaseModel):
    message: str


class OAuth2PasswordRequestForm(BaseModel):
    """
    Schema for OAuth2 Password Request form.

    Used to validate user login credentials (username and password).
    """
    username: str = Field(..., title="Username", max_length=150, description="The username of the user.")
    password: str = Field(..., title="Password", description="The password of the user.")

    class Config:
        json_schema_extra = {
            "example": {
                "username": "user123",
                "password": "mypassword123"
            }
        }
