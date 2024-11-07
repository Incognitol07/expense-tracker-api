# app/routers/alerts.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.routers.auth import get_current_user
from app.models.user import User
from app.models.alert import Alert  # Assuming you have an Alert model
from app.schemas.alerts import AlertCreate, AlertUpdate, AlertResponse
from app.utils.notifications import send_email_notification

router = APIRouter()

# POST /alerts: Set up alerts for when a budget threshold is near or exceeded
@router.post("/alerts", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
def create_alert(
    alert_data: AlertCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Create a new alert for the user
    alert = Alert(**alert_data.model_dump(), user_id=current_user.id)
    db.add(alert)
    db.commit()
    db.refresh(alert)

    # Optionally, send a notification email on alert setup
    send_email_notification(
        to_email=current_user.email,
        subject="New Budget Alert Created",
        body=f"Your alert has been set up for a budget threshold of {alert_data.threshold}."
    )
    
    return alert

# GET /alerts: Retrieve all alert settings for the user
@router.get("/alerts", response_model=list[AlertResponse])
def get_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Fetch all alerts for the current user
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
@router.delete("/alerts/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
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
