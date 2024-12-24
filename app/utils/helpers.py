from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models import (
    GroupDebt, 
    Notification,
    NotificationType, 
    User, 
    Group,
    Expense,
    Category
)
# Utility function to check if the user is part of the group
def check_group_membership(group_id: int, user_id: int, db: Session):
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    # Check if the user is a member of the group
    if not any(member.user_id == user_id for member in group.group_members):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not a member of this group")