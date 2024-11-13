# app/models/expense_split.py

from sqlalchemy import Column, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class ExpenseSplit(Base):
    __tablename__ = "expense_splits"
    
    id = Column(Integer, primary_key=True, index=True)
    expense_id = Column(Integer, ForeignKey("group_expenses.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Float, nullable=False)
    
    group_expenses = relationship("GroupExpense", back_populates="expense_splits")
    user = relationship("User", back_populates="expense_splits")
