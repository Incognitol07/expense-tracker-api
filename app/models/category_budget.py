# app/models/budget.py

from sqlalchemy import Column, Integer, Float, ForeignKey, Date, DateTime, String, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class CategoryBudget(Base):
    """
    Represents a budget for a specific category, set by a user, with a limit and date range.

    Attributes:
        id (Integer): Unique identifier for each category budget record.
        name (String): The category name linked to the budget.
        amount_limit (Float): Budget amount limit for the specific category.
        start_date (Date): Start date for the budget period.
        end_date (Date): End date for the budget period.
        user_id (Integer): Foreign key linking to the user associated with this budget.
        created_at (DateTime): Timestamp of budget creation, defaults to the current datetime.
        status (String): Status of the budget, defaulting to 'active'.

    Constraints:
        UniqueConstraint: Ensures unique budgets for the same category, user, and date range.

    Relationships:
        category (Category): Reference to the associated category.
        owner (User): Reference to the User who owns this category budget.
    """

    __tablename__ = "category_budgets"

    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)  # ForeignKey to categories table
    amount_limit = Column(Float, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    status = Column(String, default="active", nullable=False)

    # Relationships
    categories = relationship("Category", back_populates="category_budgets")
    owner = relationship("User", back_populates="category_budgets")