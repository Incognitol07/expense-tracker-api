from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models import (
    User,
    Expense
)
from .notifications import log_exception


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