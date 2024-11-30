# app/models/budget.py

from sqlalchemy import Column, Integer, Float, ForeignKey, Date, DateTime, String
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class MonthlyBudget(Base):
    """
    Represents a budget set by a user, with a specific limit and date range.

    Attributes:
        id (Integer): Unique identifier for each budget record.
        amount_limit (Float): MonthlyBudget amount limit set by the user.
        start_date (Date): Start date for the budget period.
        end_date (Date): End date for the budget period.
        user_id (Integer): Foreign key linking to the user associated with this budget.
        created_at (DateTime): Timestamp of budget creation, defaults to the current date.

    Relationships:
        owner (User): Reference to the User who owns the budget, with a back-populated 'budgets' attribute.
    """

    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, index=True)
    amount_limit = Column(Float, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.now(), nullable=False)
    status = Column(String, default="active")

    # Relationship back to the user
    owner = relationship("User", back_populates="budgets")
