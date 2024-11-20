# app/routers/notifications.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.routers.auth import get_current_user
from app.models.user import User
from app.models.notification import Notification
from app.schemas.notifications import NotificationResponse
from app.utils import logger  # Import the logger

# Create an instance of APIRouter for notification-related routes
router = APIRouter()

# Route to fetch all unread notifications for the authenticated user
@router.get("/", response_model=list[NotificationResponse])
def get_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Fetches all unread notifications for the authenticated user.

    Args:
        db (Session): The database session to interact with the database.
        current_user (User): The currently authenticated user.

    Returns:
        list[NotificationResponse]: A list of unread notifications for the user.
    
    Raises:
        HTTPException: If no unread notifications are found.
    """
    notifications = db.query(Notification).filter(
        Notification.user_id == current_user.id, 
        Notification.is_read == False
    ).all()

    # Log the fetched unread notifications
    logger.info(f"Fetched {len(notifications)} unread notifications for user {current_user.id}.")
    
    # If no unread notifications are found, return an empty list
    if not notifications:
        logger.warning(f"No unread notifications found for user {current_user.id}.")
    return notifications

# Route to mark a specific notification as read
@router.put("/{notification_id}/mark-as-read", response_model=NotificationResponse)
def mark_notification_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Marks a specific notification as read for the authenticated user.

    Args:
        notification_id (int): The ID of the notification to mark as read.
        db (Session): The database session to interact with the database.
        current_user (User): The currently authenticated user.

    Returns:
        NotificationResponse: The updated notification after marking it as read.
    
    Raises:
        HTTPException: If the notification is not found or does not belong to the user.
    """
    notification = db.query(Notification).filter(
        Notification.id == notification_id, 
        Notification.user_id == current_user.id
    ).first()

    if not notification:
        logger.error(f"Notification {notification_id} not found for user {current_user.id}.")
        raise HTTPException(status_code=404, detail="Notification not found")
    
    notification.is_read = True  # Mark the notification as read
    db.commit()  # Commit the update to the database
    db.refresh(notification)  # Refresh the notification object to get the updated state
    
    # Log the action of marking the notification as read
    logger.info(f"Notification {notification_id} marked as read for user {current_user.id}.")
    
    return notification

# Route to mark all unread notifications as read
@router.put("/mark-all-as-read", response_model=list[NotificationResponse])
def mark_all_notifications_as_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Marks all unread notifications as read for the authenticated user.

    Args:
        db (Session): The database session to interact with the database.
        current_user (User): The currently authenticated user.

    Returns:
        list[NotificationResponse]: A list of notifications that were marked as read.
    
    Raises:
        HTTPException: If no unread notifications are found.
    """
    # Query all unread notifications for the user
    notifications = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).all()
    
    if not notifications:
        logger.warning(f"No unread notifications found for user {current_user.id}.")
        raise HTTPException(status_code=404, detail="No unread notifications found")

    # Mark all fetched notifications as read
    for notification in notifications:
        notification.is_read = True

    db.commit()  # Commit the updates to the database
    
    # Log the action of marking all notifications as read
    logger.info(f"Marked all unread notifications as read for user {current_user.id}. Total: {len(notifications)}.")
    
    # Return the list of updated notifications
    return notifications
