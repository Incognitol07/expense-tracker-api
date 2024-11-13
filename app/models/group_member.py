# app/models/group_member.py

from sqlalchemy import Column, Integer, ForeignKey, String
from sqlalchemy.orm import relationship
from app.database import Base

class GroupMember(Base):
    __tablename__ = "group_members"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    group_id = Column(Integer, ForeignKey("groups.id"))
    role = Column(String, default="member")  # e.g., 'admin'
    status = Column(String, default="active")  # 'active' or 'pending'

    group = relationship("Group", back_populates="group_members")
    user = relationship("User", back_populates="group_members")
