from pydantic import BaseModel
from datetime import date, datetime

class BudgetBase(BaseModel):
    amount_limit: float
    start_date: date
    end_date: date

class BudgetCreate(BudgetBase):
    pass

class BudgetUpdate(BudgetBase):
    pass

class BudgetResponse(BudgetBase):
    id: int

    class Config:
        from_attributes = True

class BudgetStatus(BaseModel):
    remaining_amount: float
    start_date: date
    end_date: date

class BudgetHistory(BudgetResponse):
    # Optional: Include only if `created_at` is part of the database model.
    created_at: date
