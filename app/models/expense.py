# app/models/expense.py

from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Expense(Base):
    """
    Represents an expense record associated with a user and category.

    Attributes:
        id (Integer): Unique identifier for each expense.
        amount (Float): The amount spent in this expense.
        description (String): Optional description or details about the expense.
        date (Date): Date on which the expense was made.
        user_id (Integer): Foreign key linking to the user who made the expense.
        category_id (Integer): Foreign key linking to the category this expense belongs to.

    Relationships:
        owner (User): Reference to the User who made the expense, with a back-populated 'expenses' attribute.
        categories (Category): Reference to the Category of the expense, with a back-populated 'expenses' attribute.
    """
    __tablename__ = "expenses"
    
    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float, nullable=False)
    description = Column(String, nullable=True)
    date = Column(Date, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    category_id = Column(Integer, ForeignKey("categories.id"))  # Link to category

    # Relationship back to the user
    owner = relationship("User", back_populates="expenses")
    
    # Relationship back to the category
    categories = relationship("Category", back_populates="expenses")
