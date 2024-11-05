# app/schemas/expenses.py

from pydantic import BaseModel
from typing import Optional
from datetime import date

class ExpenseBase(BaseModel):
    amount: float
    description: str
    date: date

class ExpenseCreate(ExpenseBase):
    category_id: int  # Category relation

class ExpenseResponse(ExpenseBase):
    id: int
    user_id: int  # The user who created the expense

    class Config:
        from_attributes = True



class ExpenseUpdate(BaseModel):
    amount: Optional[float]
    description: Optional[str]
    date: Optional[date]
    category_id: Optional[int]

    class Config:
        from_attributes = True
