from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models import (
    Notification,
    NotificationType
)
from app.utils import logger

def send_notification(db: Session, user_id: int, type: NotificationType, message: str):
    notification = Notification(
        user_id=user_id,
        type=type,
        message=message
    )
    db.add(notification)
    db.commit()

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