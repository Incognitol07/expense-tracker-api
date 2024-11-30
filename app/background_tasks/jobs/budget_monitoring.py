from datetime import datetime
from app.database import SessionLocal
from app.models import GeneralBudget, Notification
from app.utils import logger
from app.websocket_manager import manager

def check_and_deactivate_expired_budgets():
    """
    Checks if any active budget has passed its 'end_date' and deactivates it by setting status to 'deactivated'.
    Sends a notification to the user when the budget is deactivated.
    """
    db = SessionLocal()
    try:
        # Query all active budgets that haven't passed their 'end_date'
        budgets = db.query(GeneralBudget).filter(GeneralBudget.status == "active").all()

        for budget in budgets:
            if budget.end_date and budget.end_date < datetime.now().date():
                # If the budget's end date has passed, deactivate it
                budget.status = "deactivated"
                db.commit()  # Commit the changes to the database
                logger.info(
                    f"GeneralBudget (ID: {budget.id}) for user {budget.user_id} has been deactivated."
                )

                # Send a notification to the user informing them that their budget was deactivated
                message = f"Your budget (ID: {budget.id}) has been deactivated because its end date has passed."
                existing_notification = (
                    db.query(Notification)
                    .filter(
                        Notification.user_id == budget.user_id,
                        Notification.message == message,
                        Notification.is_read == False,
                    )
                    .first()
                )

                # Only create a new notification if there are no unread ones with the same message
                if not existing_notification:
                    logger.info(
                        f"Creating notification for user ID: {budget.user_id} with message: '{message}'"
                    )
                    notification = Notification(user_id=budget.user_id, message=message)
                    db.add(notification)
                    db.commit()  # Commit the session to persist the notification in the database

                    # Send the notification to the user's WebSocket
                    manager.send_notification(budget.user_id, message)
                else:
                    logger.info(
                        f"User ID: {budget.user_id} already has an unread notification with the same message."
                    )
                logger.info(
                    f"Deactivation notification sent for user ID: {budget.user_id}"
                )
    finally:
        db.close()
