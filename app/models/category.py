# app/models/category.py

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Category(Base):
    """
    Represents a category for organizing expenses under specific labels.

    Attributes:
        id (Integer): Unique identifier for each category.
        name (String): Name of the category, unique across the application.
        description (String): Optional description providing details about the category.
        user_id (Integer): Foreign key linking to the user who created the category.
    
    Relationships:
        expenses (Expense): List of expenses associated with this category, using a back-populated 'categories' attribute.
        owner (User): Reference to the User who owns the category, with a back-populated 'categories' attribute.
    """
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # Relationship with expenses
    expenses = relationship("Expense", back_populates="categories")

    owner = relationship("User", back_populates="categories")
