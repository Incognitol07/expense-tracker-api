from fastapi import status
from sqlalchemy.orm import Session
from app.models import (
    GroupDebt,
    User
)
from .notifications import log_exception

def get_debt_model(db: Session, user: User,debt_id: int):
    debt = db.query(GroupDebt).filter(GroupDebt.id == debt_id).first()
    if not debt:
        log_exception(
            log_level="warning",
            log_message=f"Debt ID: {debt_id} not found for user '{user.username}' (ID: {user.id})",
            status_raised=status.HTTP_404_NOT_FOUND,
            exception_message=f"Debt ID: {debt_id} not found"
        )
    
    return debt