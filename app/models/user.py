# app/models/user.py

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    """
    Represents a user in the system, who can have expenses, budgets, categories, alerts, and notifications.

    Attributes:
        id (Integer): Unique identifier for each user.
        username (String): The unique username chosen by the user.
        email (String): The unique email address of the user.
        hashed_password (String): The user's password, stored as a hash for security.

    Relationships:
        expenses (Expense): List of expenses associated with this user, using a back-populated 'owner' attribute.
        budgets (Budget): List of budgets set by the user, using a back-populated 'owner' attribute.
        categories (Category): List of categories created by the user, using a back-populated 'owner' attribute.
        alerts (Alert): List of alerts associated with this user, using a back-populated 'owner' attribute.
        notifications (Notification): List of notifications sent to this user, using a back-populated 'owner' attribute.
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    
    # Relationships
    expenses = relationship("Expense", back_populates="owner", cascade="all, delete-orphan")
    budgets = relationship("Budget", back_populates="owner", cascade="all, delete-orphan")
    categories = relationship("Category", back_populates="owner", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="owner", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="owner", cascade="all, delete-orphan")
