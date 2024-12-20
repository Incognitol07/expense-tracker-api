# app/schemas/expenses.py

from pydantic import BaseModel
from typing import Optional
from datetime import date


# Base schema for common expense attributes
class ExpenseBase(BaseModel):
    """
    Base schema for common expense attributes shared across creation, update, and response schemas.

    Attributes:
        amount (float): The amount spent for the expense.
        name (str): A name or name of the expense.
        date (date): The date when the expense occurred.
    """

    amount: float
    name: str
    date: date


# Schema for creating a new expense, including the category ID
class ExpenseCreate(ExpenseBase):
    """
    Schema for creating a new expense. Inherits from ExpenseBase and adds the category relation.

    Attributes:
        category_id (int): The ID of the category the expense belongs to.
    """

    category_name: str  # Category relation


# Schema for returning expense details in the response, including the expense ID and user ID
class ExpenseResponse(ExpenseBase):
    """
    Schema for returning expense details, including the unique ID and user ID associated with the expense.

    Attributes:
        id (int): The unique identifier for the expense.
        user_id (int): The ID of the user who created the expense.
    """

    id: int
    category_id: int

    class Config:
        from_attributes = True


class CategoryExpenseResponse(ExpenseBase):
    """
    Schema for returning expense details, including the unique ID and user ID associated with the expense.

    Attributes:
        id (int): The unique identifier for the expense.
        user_id (int): The ID of the user who created the expense.
    """

    id: int
    category_id: int
    category_name: str

    class Config:
        from_attributes = True

class GetExpenseResponse(BaseModel):
    total_count: int
    total_pages: int
    current_page: int
    per_page: int
    next_page: str | None
    prev_page: str | None
    expenses: list[CategoryExpenseResponse]


# Schema for updating an existing expense (optional fields)
class ExpenseUpdate(BaseModel):
    """
    Schema for updating an existing expense, where all fields are optional.

    Attributes:
        amount (Optional[float]): The updated amount for the expense.
        name (Optional[str]): The updated name of the expense.
        date (Optional[date]): The updated date for the expense.
        category_id (Optional[int]): The updated category ID for the expense.
    """

    amount: Optional[float] = None
    name: Optional[str] = None
    date: Optional[date]
    category_id: Optional[int] = None

    class Config:
        from_attributes = True
