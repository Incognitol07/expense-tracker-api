# app/schemas/category_budget.py

from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional


# Base schema for CategoryBudget-related attributes
class CategoryBudgetBase(BaseModel):
    """
    Base schema for category budget-related attributes. This serves as the foundation for creating or updating category budgets.

    Attributes:
        amount_limit (float): The spending limit for the budget.
        start_date (date): The start date of the budget period.
        end_date (date): The end date of the budget period.
        category_id (int): The ID of the associated category.
    """

    amount_limit: float
    start_date: date
    end_date: date


# Schema for creating a new category budget (inherits from CategoryBudgetBase)
class CategoryBudgetCreate(CategoryBudgetBase):
    """
    Schema for creating a new category budget, extending the CategoryBudgetBase schema.
    Inherits all attributes from CategoryBudgetBase.
    """

    name: str


# Schema for updating an existing category budget (inherits from CategoryBudgetBase)
class CategoryBudgetUpdate(BaseModel):
    """
    Schema for updating an existing category budget.

    Attributes:
        amount_limit (Optional[float]): Updated spending limit for the budget.
        start_date (Optional[date]): Updated start date of the budget period.
        end_date (Optional[date]): Updated end date of the budget period.
    """

    amount_limit: Optional[float] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


# Schema for category budget response (includes the budget ID)
class CategoryBudgetResponse(CategoryBudgetBase):
    """
    Schema for returning a category budget's details in the response, including the budget ID.

    Attributes:
        id (int): The unique identifier for the category budget.
        user_id (int): The ID of the user who owns the category budget.
        status (str): The current status of the budget (e.g., "active", "deactivated").
        created_at (str): The timestamp when the category budget was created.
    """

    id: int
    user_id: int
    status: str
    created_at: datetime

    class Config:
        # This allows Pydantic to pull attributes from ORM models
        from_attributes = True

class AllCategoryBudgetResponse(CategoryBudgetBase):
    """
    Schema for returning a category budget's details in the response, including the budget ID.

    Attributes:
        id (int): The unique identifier for the category budget.
        user_id (int): The ID of the user who owns the category budget.
        status (str): The current status of the budget (e.g., "active", "deactivated").
        created_at (str): The timestamp when the category budget was created.
    """
    status: str
    created_at: datetime
    amount_used: float
    category_name: str

    class Config:
        # This allows Pydantic to pull attributes from ORM models
        from_attributes = True


# Schema for displaying the current status of a category budget
class CategoryBudgetStatus(BaseModel):
    """
    Schema for displaying the current status of a category budget.

    Attributes:
        remaining_amount (float): The amount left in the budget after expenses.
        category_id (int): The ID of the associated category.
    """

    status: str
    remaining_amount: float
    category_name: str


# Schema for category budget history (includes creation date and status)
class CategoryBudgetHistory(CategoryBudgetResponse):
    """
    Schema for category budget history, including the created_at timestamp.

    Attributes:
        created_at (str): The timestamp when the category budget was created.
        status (str): The status of the budget (e.g., "active", "deactivated").
    """

    created_at: datetime
    status: str
