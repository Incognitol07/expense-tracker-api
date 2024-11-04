# app/schemas/budget.py

from pydantic import BaseModel
from datetime import date

class BudgetBase(BaseModel):
    amount: float
    category_id: int  # Category relation
    start_date: date
    end_date: date

class BudgetCreate(BudgetBase):
    pass

class BudgetResponse(BudgetBase):
    id: int

    class Config:
        orm_mode = True
