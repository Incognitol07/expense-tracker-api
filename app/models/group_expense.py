# app/models/group_expense.py
from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime

class GroupExpense(Base):
    __tablename__ = "group_expenses"
    
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"))
    payer_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Float, nullable=False)
    description = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now(), nullable=False)
    
    group = relationship("Group", back_populates="group_expenses")
    expense_splits = relationship("ExpenseSplit", back_populates="group_expenses", cascade="all, delete")
    user =  relationship("User", back_populates="group_expenses")
