# app/routers/alerts.py

from app.database import SessionLocal
from app.models import Expense, GeneralBudget
from app.models import Notification
from app.websocket_manager import manager
from app.utils import logger


# Background task to check thresholds
async def check_budget(user_id: int):
    """
    Background task to check if the user's expenses exceed their set alert threshold.

    Args: \n
        user_id (int): The ID of the user whose alert thresholds are being checked.

    Checks if the total expenses exceed the threshold and creates a notification if they do.
    """
    db = SessionLocal()
    try:
        logger.info(f"Initiating budget check for user ID: {user_id}")
        budget = (
            db.query(GeneralBudget)
            .filter(GeneralBudget.user_id == user_id, GeneralBudget.status == "active")
            .first()
        )
        if not budget:
            logger.warning(f"No active budget found for user ID: {user_id}")
            return
        user_expenses = (
            db.query(Expense)
            .filter(
                Expense.user_id == user_id,
                Expense.date >= budget.start_date,
                Expense.date <= budget.end_date,
            )
            .all()
        )
        logger.info(
            f"Fetched {len(user_expenses)} expenses for user ID: {user_id} within budget period"
        )

        expenses = [
            expense.amount
            for expense in budget.owner.expenses
            if budget.start_date <= expense.date <= budget.end_date
        ]
        remaining_amount = budget.amount_limit - sum(expenses)

        logger.info(f"Remaining budget for user ID {user_id}: {remaining_amount}")
        # Only send a notification if expenses exceed the current budget
        if remaining_amount < 0:
            logger.info(
                f"GeneralBudget exceeded for user ID {user_id}. Exceedance amount: {abs(remaining_amount)}"
            )
            message = f"You've exceeded your budget of {budget.amount_limit} by {abs(remaining_amount)}."
            existing_notification = (
                db.query(Notification)
                .filter(
                    Notification.user_id == user_id,
                    Notification.message == message,
                    Notification.is_read == False,
                )
                .first()
            )

            # Create a new notification if not already present
            if not existing_notification:
                logger.info(f"Creating notification for user ID: {user_id}")
                notification = Notification(user_id=user_id, message=message)
                db.add(notification)
                db.commit()
                await manager.send_notification(user_id, message)
            logger.info(f"GeneralBudget check completed for user ID: {user_id}")
    finally:
        db.close()