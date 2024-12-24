from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models import (
    GroupMember,
    GroupDebt, 
    Notification,
    NotificationType, 
    User, 
    Group,
    Expense,
    Category
)
from app.schemas import CategoryCreate
from app.utils import logger

def log_exception(log_level:str = None, log_message: str = None, status_raised:int = None, exception_message: str = None):
    if log_level == "warning":
        logger.warning(log_message)
    if log_level == "info":
        logger.info(log_message)
    if log_level == "error":
        logger.error(log_message)
    if log_level == "critical":
        logger.critical(log_message)
    if exception_message and status_raised:
        raise HTTPException(
            status_code=status_raised, detail=exception_message
        )

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


def get_expense_model(db:Session, expense_id:int, current_user: User, action:str):
    expense = (
        db.query(Expense)
        .filter(Expense.id == expense_id, Expense.user_id == current_user.id)
        .first()
    )
    if not expense:
        log_exception(
            log_level="warning", 
            log_message=f"Failed to {action} expense ID: {expense_id} for user '{current_user.username}' (ID: {current_user.id})",
            status_raised=status.HTTP_404_NOT_FOUND,
            exception_message=f"Expense ID: {expense_id} not found"
            )
    
    return expense

def existing_category_attribute(db:Session, user: User, category:CategoryCreate, attribute:str):
    # Check for existing category attribute
    db_category_attribute = db.query(Category).filter(Category.user_id == user.id, Category.name == category.attribute).first()

    if db_category_attribute:
        log_exception(
            log_level="warning",
            log_message=f"Category {attribute} '{category.attribute}' already exists for user '{user.username}' (ID: {user.id}).",
            status_raised=status.HTTP_404_NOT_FOUND,
            exception_message=f"Category {attribute} {category.attribute} already exists"
        )

def get_category_model_by_id(db:Session, user:User, category_id:int):
    category = (
        db.query(Category)
        .filter(Category.id == category_id, Category.user_id == user.id)
        .first()
    )

    if not category:
        log_exception(
            log_level="error",
            log_message=f"Category {category_id} not found for user '{user.username}' (ID: {user.id}).",
            status_raised=status.HTTP_404_NOT_FOUND,
            exception_message=f"Category {category_id} not found"
        )
    
    return category

def get_category_model_by_name(db:Session, user:User, category_name:str):
    category = (
        db.query(Category)
        .filter(Category.name == category_name, Category.user_id == user.id)
        .first()
    )

    if not category:
        log_exception(
            log_level="error",
            log_message=f"Category {category_name} not found for user '{user.username}' (ID: {user.id}).",
            status_raised=status.HTTP_404_NOT_FOUND,
            exception_message=f"Category {category_name} not found"
        )
    
    return category

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

def send_notification(db: Session, user_id: int, type, message: str):
    notification = Notification(
        user_id=user_id,
        type=type,
        message=message
    )
    db.add(notification)
    db.commit()