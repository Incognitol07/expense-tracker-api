# app/schemas/analytics.py

from pydantic import BaseModel
from datetime import date
from typing import List, Optional

# Schema for Expense Summary
class CategorySummary(BaseModel):
    category_id: int
    total: float

class ExpenseSummary(BaseModel):
    total_expenses: float
    budget_limit: Optional[float]
    adherence: Optional[float]
    expenses_by_category: List[CategorySummary]


# Schema for Monthly Breakdown
class MonthlyBreakdown(BaseModel):
    month: int
    breakdown: List[CategorySummary]


# Schema for Weekly Breakdown
class WeeklyBreakdown(BaseModel):
    week_start: date
    breakdown: List[CategorySummary]


# Schema for Trend Data
class MonthlyTrend(BaseModel):
    month: int
    total: float

class TrendData(BaseModel):
    trends: List[MonthlyTrend]


# Schema for Export Data (used internally, no direct response model)
class ExportData(BaseModel):
    id: int
    amount: float
    description: Optional[str]
    date: date
    category_id: int
