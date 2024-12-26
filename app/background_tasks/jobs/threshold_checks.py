from app.database import SessionLocal
from app.models import Expense, GeneralBudget, CategoryBudget, Category
from app.models import Notification, NotificationType
from app.websocket_manager import manager
from app.utils import logger
from app.utils import send_notification


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
                send_notification(
                    db=db,
                    user_id=user_id,
                    type=NotificationType.ALERT,
                    message=message
                )
                await manager.send_notification(user_id, message)
            logger.info(f"Budget check completed for user ID: {user_id}")
    finally:
        db.close()

# Background task to check category-specific budgets
async def check_category_budget(user_id: int):
    db = SessionLocal()
    try:
        logger.info(f"Initiating category budget check for user ID: {user_id}")
        active_budgets = (
            db.query(CategoryBudget)
            .filter(CategoryBudget.user_id == user_id, CategoryBudget.status == "active")
            .all()
        )
        if not active_budgets:
            logger.warning(f"No active category budgets found for user ID: {user_id}")
            return

        categories = {budget.category_id: budget for budget in active_budgets}
        user_expenses = (
            db.query(Expense)
            .filter(
                Expense.user_id == user_id,
                Expense.category_id.in_(categories.keys()),
            )
            .all()
        )

        category_totals = {}
        for expense in user_expenses:
            category_totals[expense.category_id] = (
                category_totals.get(expense.category_id, 0) + expense.amount
            )

        for category_id, total_expense in category_totals.items():
            budget = categories[category_id]
            remaining_budget = budget.amount_limit - total_expense

            logger.info(
                f"Category {category_id}: Total expense = {total_expense}, Remaining budget = {remaining_budget}"
            )

            if remaining_budget < 0:
                exceed_amount = abs(remaining_budget)
                category = db.query(Category).filter(
                    Category.user_id == user_id,
                    Category.id == budget.category_id
                ).first()

                category_name = category.name if category else"Unknown Category"
                message = (
                    f"You've exceeded your budget for category '{category_name}' "
                    f"by {exceed_amount:.2f}. Your limit was {budget.amount_limit}."
                )

                existing_notification = (
                    db.query(Notification)
                    .filter(
                        Notification.user_id == user_id,
                        Notification.message == message,
                        Notification.is_read == False,
                    )
                    .first()
                )
                if not existing_notification:
                    send_notification(
                        db=db, 
                        user_id=user_id, 
                        type=NotificationType.ALERT, 
                        message=message
                    )
                    logger.info(f"Notification created: '{message}'")
                    await manager.send_notification(user_id, message)
        logger.info(f"Category budget check completed for user ID: {user_id}")
    except Exception as e:
        logger.error(f"Error in category budget check: {e}")
    finally:
        db.close()