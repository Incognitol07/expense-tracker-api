from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models import (
    GroupMember,
    User, 
    Group,
    Expense,
    Category
)
from .notifications import log_exception

# Utility function to check if the user is part of the group
def check_group_membership(group_id: int, user: User, db: Session):
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Group not found"
            )
    # Check if the user is a member of the group
    if not any(member.user_id == user.id for member in group.group_members):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="You are not a member of this group"
            )

def get_group_by_id(db:Session, current_user:User, group_id:int):
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        log_exception(
            log_level="warning",
            log_message=f"Group ID: {group_id} not found for user '{current_user.username}' (ID: {current_user.id})",
            status_raised=status.HTTP_404_NOT_FOUND,
            exception_message=f"Group #{group_id} not found"
        )
    
    return group

def get_member_model(
        db: Session, 
        user: User, 
        group_id:int, 
        check_if_not_exists: bool = False, 
        active: bool = False,
        manager: bool = False
    ):
    query = (
        db.query(GroupMember)
        .filter(
            GroupMember.user_id == user.id, GroupMember.group_id == group_id
        )
    )
    if active:
        query.filter(GroupMember.status=="active")
    if manager:
        query.filter(GroupMember.role=="manager")

    member = query.first()
    if check_if_not_exists:
        if member:
            log_exception(
                log_level="warning",
                log_message=f"User is already a member of group ID: {group_id}",
                status_raised=status.HTTP_400_BAD_REQUEST,
                exception_message=f"User '{user.username}' is already a member of the group"
            )
    
    if not member:
        if manager:
            log_exception(
            log_level="warning",
            log_message=f"User '{user.username}' (ID: {user.id}) attempted to perform a sensitive action from group ID: {group_id} without manager privileges.",
            status_raised=status.HTTP_403_FORBIDDEN,
            exception_message="Only group managers can perform this action",
            )
        if active:
            log_exception(
                log_level="warning",
                log_message=f"User '{user.username}' (ID: {user.id}) is not an active member of group ID: {group_id}.",
                status_raised=status.HTTP_400_BAD_REQUEST,
                exception_message=f"User '{user.username}' is not an active member of group ID: {group_id}"
            )
        log_exception(
            log_level="warning",
            log_message=f"User with email '{user.email}' is not a member of group ID: {group_id}",
            status_raised=status.HTTP_400_BAD_REQUEST,
            exception_message=f"User '{user.username}' is not a member of the group"
        )
    
    return member