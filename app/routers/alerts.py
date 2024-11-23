# app/routers/alerts.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db, SessionLocal
from app.routers.auth import get_current_user
from app.models import User, Alert, Expense, Budget
from app.models.notification import Notification  # New import for notifications
from app.schemas.alerts import AlertCreate, AlertUpdate, AlertResponse
from fastapi import BackgroundTasks
from app.websocket_manager import manager
from app.utils import logger

router = APIRouter()


# Background task to check thresholds
async def check_thresholds(user_id: int):
    """
    Background task to check if the user's expenses exceed their set alert threshold.

    Args:
        user_id (int): The ID of the user whose alert thresholds are being checked.

    Checks if the total expenses exceed the threshold and creates a notification if they do.
    """
    db = SessionLocal()  # Assuming SessionLocal is the session factory from your database setup
    try:
        logger.info(f"Initiating threshold check for user ID: {user_id}")
        alert = db.query(Alert).filter(Alert.user_id == user_id).first()
        if not alert:
            logger.warning(f"No alert found for user ID: {user_id}")
        user_expenses = db.query(Expense).filter(Expense.user_id == user_id).all()
        logger.info(f"Fetched {len(user_expenses)} expenses for user ID: {user_id}")

        total_expenses = sum(expense.amount for expense in user_expenses)

        logger.info(f"Total expenses for user ID {user_id}: {total_expenses}")
        adherence = total_expenses - alert.threshold 

        # Condition to check if adherence exceeds the threshold
        if adherence>0:
            logger.info(f"Threshold exceeded for user ID {user_id}. Exceedance amount: {adherence:.2f}")
            message = f"Your alert threshold of {alert.threshold} has been exceeded by {adherence:.2f}"
            
            # Check for existing unread notifications with the same message
            existing_notification = db.query(Notification).filter(
                Notification.user_id == user_id,
                Notification.message == message,
                Notification.is_read == False
            ).first()

            # Only create a new notification if there are no unread ones with the same message
            if not existing_notification:
                logger.info(f"Creating notification for user ID: {user_id}")
                notification = Notification(
                    user_id=user_id,
                    message=message
                )
                db.add(notification)
                db.commit()  # Commit the session to persist the notification in the database
                await manager.send_notification(user_id, message)
            logger.info(f"Threshold check completed for user ID: {user_id}")
    finally:
        db.close()  # Close the session after use

# Background task to check thresholds
async def check_budget(user_id: int):
    """
    Background task to check if the user's expenses exceed their set alert threshold.

    Args:
        user_id (int): The ID of the user whose alert thresholds are being checked.

    Checks if the total expenses exceed the threshold and creates a notification if they do.
    """
    db = SessionLocal()
    try:
        logger.info(f"Initiating budget check for user ID: {user_id}")
        budget = db.query(Budget).filter(Budget.user_id == user_id, Budget.status == "active").first()
        if not budget:
            logger.warning(f"No active budget found for user ID: {user_id}")
            return
        user_expenses = db.query(Expense).filter(
            Expense.user_id == user_id,
            Expense.date >= budget.start_date,
            Expense.date <= budget.end_date
        ).all()
        logger.info(f"Fetched {len(user_expenses)} expenses for user ID: {user_id} within budget period")

        expenses = [
        expense.amount
        for expense in budget.owner.expenses
        if budget.start_date <= expense.date <= budget.end_date
        ]
        remaining_amount = budget.amount_limit - sum(expenses)

        logger.info(f"Remaining budget for user ID {user_id}: {remaining_amount}")
        # Only send a notification if expenses exceed the current budget
        if remaining_amount < 0:
            logger.info(f"Budget exceeded for user ID {user_id}. Exceedance amount: {abs(remaining_amount)}")
            message = f"You've exceeded your budget of {budget.amount_limit} by {abs(remaining_amount)}."
            existing_notification = db.query(Notification).filter(
                Notification.user_id == user_id,
                Notification.message == message, 
                Notification.is_read == False
            ).first()

            # Create a new notification if not already present
            if not existing_notification:
                logger.info(f"Creating notification for user ID: {user_id}")
                notification = Notification(user_id=user_id, message=message)
                db.add(notification)
                db.commit()
                await manager.send_notification(user_id, message)
            logger.info(f"Budget check completed for user ID: {user_id}")
    finally:
        db.close()

@router.post("/", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
def create_alert(
    alert_data: AlertCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Creates a new alert for the user and schedules a background task to check their expense thresholds.

    Args:
        alert_data (AlertCreate): The alert data including the threshold.
        background_tasks (BackgroundTasks): Background task manager to run the threshold check.
        db (Session): The database session.
        current_user (User): The current authenticated user.

    Returns:
        AlertResponse: The created alert details.
    
    Raises:
        HTTPException: If an alert with the same threshold already exists.
    """
    logger.info(f"Attempting to create an alert for user '{current_user.username}' (ID: {current_user.id})")
    # Check if an alert with the same threshold already exists for the user
    existing_alert = db.query(Alert).filter(
        Alert.user_id == current_user.id,
        Alert.threshold == alert_data.threshold
    ).first()

    # Only proceed if there is no existing alert with the same threshold
    if existing_alert:
        logger.warning(f"Alert with threshold {alert_data.threshold} already exists for user '{current_user.username}' (ID: {current_user.id})")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An alert with the same threshold already exists. Please delete it first to create a new one."
        )

    active_budget = db.query(Budget).filter(Budget.user_id == current_user.id, Budget.status == "active").first()
    if not active_budget:
        logger.warning(f"No active budget found for user '{current_user.username}' (ID: {current_user.id}) while creating alert")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An active budget is required to create an alert."
        )

    # Create the new alert since no duplicate was found
    alert = Alert(**alert_data.model_dump(), user_id=current_user.id)
    db.add(alert)
    db.commit()
    db.refresh(alert)
    logger.info(f"Alert created successfully for user '{current_user.username}' (ID: {current_user.id}) with threshold: {alert_data.threshold}")

    # Add background task to check thresholds for this user, to be run immediately
    background_tasks.add_task(check_thresholds, current_user.id)
    logger.info(f"Background task scheduled to check thresholds for user '{current_user.username}' (ID: {current_user.id})")
    return alert

@router.get("/", response_model=list[AlertResponse])
def get_alerts(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves all alert settings for the user.

    Args:
        db (Session): Database session for querying the database.
        current_user (User): The current authenticated user.

    Returns:
        list[AlertResponse]: A list of all alerts for the user.
    """
    logger.info(f"Fetching all alerts for user '{current_user.username}' (ID: {current_user.id})")
    alerts = db.query(Alert).filter(Alert.user_id == current_user.id).all()
    logger.info(f"Retrieved {len(alerts)} alerts for user '{current_user.username}' (ID: {current_user.id})")
    active_budget = db.query(Budget).filter(Budget.user_id == current_user.id, Budget.status == "active").first()
    if active_budget:
        background_tasks.add_task(check_thresholds, current_user.id)
        logger.info(f"Background task scheduled to check thresholds for user '{current_user.username}' (ID: {current_user.id})")

    return alerts

@router.put("/", response_model=AlertResponse)
def update_alert(
    background_tasks: BackgroundTasks,
    alert_data: AlertUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Updates a specific alert for the user.

    Args:
        alert_id (int): The ID of the alert to be updated.
        alert_data (AlertUpdate): The updated alert data.
        db (Session): Database session for querying and modifying the database.
        current_user (User): The current authenticated user.

    Returns:
        AlertResponse: The updated alert details.
    
    Raises:
        HTTPException: If the alert does not exist.
    """
    logger.info(f"Attempting to update an alert for user '{current_user.username}' (ID: {current_user.id})")
    # Retrieve the alert to be updated
    alert = db.query(Alert).filter(Alert.user_id == current_user.id).first()
    if not alert:
        logger.warning(f"Alert not found for user '{current_user.username}' (ID: {current_user.id})")
        raise HTTPException(status_code=404, detail="Alert not found")
    
    active_budget = db.query(Budget).filter(Budget.user_id == current_user.id, Budget.status == "active").first()
    if not active_budget:
        logger.warning(f"No active budget found for user '{current_user.username}' (ID: {current_user.id}) while updating alert")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An active budget is required to update an alert."
        )

    
    db.query(Notification).filter(
    Notification.user_id == current_user.id,
    Notification.message.ilike("%alert%"),
    Notification.is_read == False
    ).update({"is_read": True})
    db.commit()
    logger.info(f"Marking all unread alert-related notifications as read for user '{current_user.username}' (ID: {current_user.id})")
    # Update alert details
    for key, value in alert_data.model_dump(exclude_unset=True).items():
        setattr(alert, key, value)
    db.commit()
    db.refresh(alert)
    logger.info(f"Alert updated successfully for user '{current_user.username}' (ID: {current_user.id})")
    background_tasks.add_task(check_thresholds, current_user.id)
    logger.info(f"Background task scheduled to check thresholds for user '{current_user.username}' (ID: {current_user.id})")
    return alert

@router.delete("/")
def delete_alert(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Deletes a specific alert for the user.

    Args:
        alert_id (int): The ID of the alert to be deleted.
        db (Session): Database session for querying and modifying the database.
        current_user (User): The current authenticated user.

    Returns:
        dict: Success message confirming the alert deletion.
    
    Raises:
        HTTPException: If the alert does not exist.
    """
    logger.info(f"Attempting to delete an alert for user '{current_user.username}' (ID: {current_user.id})")
    # Retrieve the alert to be deleted
    alert = db.query(Alert).filter(Alert.user_id == current_user.id).first()
    if not alert:
        logger.warning(f"Alert not found for user '{current_user.username}' (ID: {current_user.id})")
        raise HTTPException(status_code=404, detail="Alert not found")
    
    db.query(Notification).filter(
    Notification.user_id == current_user.id,
    Notification.message.ilike("%alert%"),
    Notification.is_read == False
    ).update({"is_read": True})
    db.commit()
    logger.info(f"Marking all unread alert-related notifications as read for user '{current_user.username}' (ID: {current_user.id})")
    
    db.delete(alert)
    db.commit()
    logger.info(f"Alert deleted successfully for user '{current_user.username}' (ID: {current_user.id})")
    return {"message": f"Alert of threshold {alert.threshold} deleted successfully"}
