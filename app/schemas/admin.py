from pydantic import BaseModel, EmailStr
from datetime import date
from app.schemas import UserCreate

class AdminCreate(UserCreate):
    """
    Schema for creating an admin user, which extends the user creation schema and includes a master key.
    
    Attributes:
        master_key (str): The master key required to create an admin.
    """
    master_key: str

class AdminExpenses(BaseModel):
    id: int 
    date:date
    category_id:int
    category_name: str 
    name:str
    amount : float
    user_id: int
    username: str

class AdminUsers(BaseModel):
    id: int 
    username: str
    email : EmailStr
    created_at : str

    class Config:
        from_attributes=True

class LogResponse(BaseModel):
    logs: list[str]