# app/models/group.py

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.database import Base

class Group(Base):
    __tablename__ = "groups"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True,nullable=False)
    
    group_members = relationship("GroupMember", back_populates="group", cascade="all, delete")
    group_expenses = relationship("GroupExpense", back_populates="group", cascade="all, delete")
