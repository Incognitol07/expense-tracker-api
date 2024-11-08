# app/models/user.py

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    
    # Relationship with expenses and budget
    expenses = relationship("Expense", back_populates="owner")
    budgets = relationship("Budget", back_populates="owner")
    categories = relationship("Category", back_populates="owner")
    alerts = relationship("Alert", back_populates="owner")
    notifications = relationship("Notification", back_populates="owner")
