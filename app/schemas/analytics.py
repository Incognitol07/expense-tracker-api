# app/schemas/analytics.py

from pydantic import BaseModel
from datetime import date
from typing import List, Optional

# Schema for summarizing expenses by category
class CategorySummary(BaseModel):
    """
    Schema for representing the summary of expenses per category.
    
    Attributes:
        category_id (int): The ID of the category.
        total (float): The total amount spent in this category.
    """
    category_id: int
    total: float

# Schema for summarizing total expenses, adherence to budget, and expenses by category
class ExpenseSummary(BaseModel):
    """
    Schema for representing the overall summary of expenses, including budget adherence.
    
    Attributes:
        total_expenses (float): Total expenses across all categories.
        budget_limit (Optional[float]): The set budget limit for the user (if applicable).
        adherence (Optional[float]): The adherence percentage to the budget (if applicable).
        expenses_by_category (List[CategorySummary]): A list of category-wise expense summaries.
    """
    total_expenses: float
    budget_limit: Optional[float]
    adherence: Optional[float]
    expenses_by_category: List[CategorySummary]

class ExpensesResponse(BaseModel):
    id: int
    description: str
    date: date
    category_id: int


# Schema for breaking down expenses by month
class MonthlyBreakdown(BaseModel):
    """
    Schema for representing monthly breakdown of expenses by category.
    
    Attributes:
        month (int): The month number (1-12).
        breakdown (List[CategorySummary]): A list of category summaries for this month.
    """
    month: int
    breakdown: List[CategorySummary]

# Schema for breaking down expenses by week
class WeeklyBreakdown(BaseModel):
    """
    Schema for representing weekly breakdown of expenses by category.
    
    Attributes:
        week_start (date): The start date of the week.
        breakdown (List[CategorySummary]): A list of category summaries for this week.
    """
    week_start: date
    breakdown: List[CategorySummary]

# Schema for representing monthly trends in expenses
class MonthlyTrend(BaseModel):
    """
    Schema for representing monthly trends in total expenses.
    
    Attributes:
        month (int): The month number (1-12).
        total (float): The total expenses for this month.
    """
    month: int
    total: float

# Schema for representing a collection of monthly trends
class TrendData(BaseModel):
    """
    Schema for representing trends over multiple months.
    
    Attributes:
        trends (List[MonthlyTrend]): A list of monthly trends.
    """
    trends: List[MonthlyTrend]

# Schema for exporting expense data (used internally, not a direct response model)
class ExportData(BaseModel):
    """
    Schema for representing export data of expenses, used for internal purposes.
    
    Attributes:
        id (int): The unique identifier for the expense entry.
        amount (float): The amount of the expense.
        description (Optional[str]): An optional description for the expense.
        date (date): The date the expense occurred.
        category_id (int): The ID of the category the expense belongs to.
    """
    id: int
    amount: float
    description: Optional[str]
    date: date
    category_id: int
