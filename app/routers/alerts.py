from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db, SessionLocal
from app.routers.auth import get_current_user
from app.models import User, Alert, Expense
from app.models.notification import Notification  # New import for notifications
from app.schemas.alerts import AlertCreate, AlertUpdate, AlertResponse
from fastapi import BackgroundTasks

router = APIRouter()

# Background task to check thresholds
def check_thresholds(user_id: int):
    # Get a new session for background task execution
    db = SessionLocal()  # Assuming SessionLocal is the session factory from your database setup
    try:
        alert = db.query(Alert).filter(Alert.user_id == user_id).first()
        user_expenses = db.query(Expense).filter(Expense.user_id == user_id).all()
        total_expenses = sum(expense.amount for expense in user_expenses)

        adherence = total_expenses / alert.threshold

        # Condition to check if adherence exceeds the threshold
        if adherence > 1:
            message = f"Your alert threshold of {alert.threshold} has been exceeded by {adherence * 100 - 100:.2f}."
            
            # Check for existing unread notifications with the same message
            existing_notification = db.query(Notification).filter(
                Notification.user_id == user_id,
                Notification.message == message,
                Notification.is_read == False
            ).first()

            # Only create a new notification if there are no unread ones with the same message
            if not existing_notification:
                notification = Notification(
                    user_id=user_id,
                    message=message
                )
                db.add(notification)
                db.commit()  # Commit the session to persist the notification in the database
    finally:
        db.close()  # Close the session after use



@router.post("/alerts", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
def create_alert(
    alert_data: AlertCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Check if an alert with the same threshold already exists for the user
    existing_alert = db.query(Alert).filter(
        Alert.user_id == current_user.id,
        Alert.threshold == alert_data.threshold
    ).first()

    # Only proceed if there is no existing alert with the same threshold
    if existing_alert:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An alert with the same threshold already exists. Please delete it first to create a new one."
        )

    # Create the new alert since no duplicate was found
    alert = Alert(**alert_data.model_dump(), user_id=current_user.id)
    db.add(alert)
    db.commit()
    db.refresh(alert)

    # Add background task to check thresholds for this user, to be run immediately
    background_tasks.add_task(check_thresholds, current_user.id)

    return alert

# GET /alerts: Retrieve all alert settings for the user
@router.get("/alerts", response_model=list[AlertResponse])
def get_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    alerts = db.query(Alert).filter(Alert.user_id == current_user.id).all()
    return alerts

# PUT /alerts/{alert_id}: Update a specific alert
@router.put("/alerts/{alert_id}", response_model=AlertResponse)
def update_alert(
    alert_id: int,
    alert_data: AlertUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Retrieve the alert to be updated
    alert = db.query(Alert).filter(Alert.id == alert_id, Alert.user_id == current_user.id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    # Update alert details
    for key, value in alert_data.model_dump(exclude_unset=True).items():
        setattr(alert, key, value)
    db.commit()
    db.refresh(alert)
    
    return alert

# DELETE /alerts/{alert_id}: Delete a specific alert
@router.delete("/alerts/{alert_id}")
def delete_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Retrieve the alert to be deleted
    alert = db.query(Alert).filter(Alert.id == alert_id, Alert.user_id == current_user.id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    db.delete(alert)
    db.commit()
    
    return {"detail": "Alert deleted successfully"}
