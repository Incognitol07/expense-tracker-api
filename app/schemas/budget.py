from pydantic import BaseModel
from datetime import date
from typing import Literal

class BudgetBase(BaseModel):
    amount: float
    period: Literal["monthly", "weekly"]

class BudgetCreate(BudgetBase):
    pass

class BudgetUpdate(BudgetBase):
    pass

class BudgetResponse(BudgetBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True

class BudgetStatus(BaseModel):
    remaining_amount: float
    limit: float
    period: str

class BudgetHistory(BudgetResponse):
    date_created: date
