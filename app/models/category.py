from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base

class Category(Base):
    """
    Represents a category for organizing expenses under specific labels.

    Attributes:
        id (Integer): Unique identifier for each category entry in the database.
        category_id (Integer): Unique identifier for each category per user.
        name (String): Name of the category, unique per user.
        description (String): Optional description providing details about the category.
        user_id (Integer): Foreign key linking to the user who created the category.
    
    Relationships:
        expenses (Expense): List of expenses associated with this category, using a back-populated 'categories' attribute.
        owner (User): Reference to the User who owns the category, with a back-populated 'categories' attribute.
    """
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, index=True, nullable=False)
    description = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))

    # Unique Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'name','description', name='uq_user_category_name_description'),
    )

    # Relationships
    expenses = relationship("Expense", back_populates="categories", cascade="all, delete-orphan")
    category_budgets = relationship("CategoryBudget", back_populates="categories", cascade="all, delete-orphan")
    owner = relationship("User", back_populates="categories")
