# app/schemas/budget.py

from pydantic import BaseModel
from datetime import date


# Base schema for MonthlyBudget-related attributes
class MonthlyBudgetBase(BaseModel):
    """
    Base schema for budget-related attributes. This serves as the foundation for creating or updating budgets.

    Attributes:
        amount_limit (float): The spending limit for the budget.
        start_date (date): The start date of the budget period.
        end_date (date): The end date of the budget period.
    """

    amount_limit: float
    start_date: date
    end_date: date


# Schema for creating a new budget (inherits from MonthlyBudgetBase)
class MonthlyBudgetCreate(MonthlyBudgetBase):
    """
    Schema for creating a new budget, extending the MonthlyBudgetBase schema.
    Inherits all attributes from MonthlyBudgetBase.
    """

    pass


# Schema for updating an existing budget (inherits from MonthlyBudgetBase)
class MonthlyBudgetUpdate(MonthlyBudgetBase):
    """
    Schema for updating an existing budget, extending the MonthlyBudgetBase schema.
    Inherits all attributes from MonthlyBudgetBase.
    """

    pass


# Schema for budget response (includes the budget ID)
class MonthlyBudgetResponse(MonthlyBudgetBase):
    """
    Schema for returning a budget's details in the response, including the budget ID.

    Attributes:
        id (int): The unique identifier for the budget.
    """

    id: int
    created_at: str

    class Config:
        # This allows Pydantic to pull attributes from ORM models
        from_attributes = True


# Schema for displaying the current status of a budget (remaining amount and budget period)
class MonthlyBudgetStatus(BaseModel):
    """
    Schema for displaying the current status of a budget, including the remaining amount.

    Attributes:
        remaining_amount (float): The amount left in the budget after expenses.
        start_date (date): The start date of the budget period.
        end_date (date): The end date of the budget period.
    """

    remaining_amount: float
    start_date: date
    end_date: date


# Schema for budget history (includes creation date and extends MonthlyBudgetResponse)
class MonthlyBudgetHistory(MonthlyBudgetResponse):
    """
    Schema for budget history, including the created_at timestamp.

    Attributes:
        created_at (date): The date when the budget was created.
    """

    created_at: str
    status: str
