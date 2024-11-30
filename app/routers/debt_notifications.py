# app/routers/debt_notifications.py

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import DebtNotification, User, Expense, Category, Notification
from app.routers.auth import get_current_user
from app.schemas import DebtNotificationResponse, DebtNotificationStatus, DetailResponse
from app.utils import logger
from app.background_tasks import check_budget

router = APIRouter()


@router.post("/send_debt_notification/", response_model=DetailResponse)
def send_debt_notification(
    amount: float,
    description: str,
    debtor_ids: list[int],  # List of user IDs who owe the debt
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Sends a debt notification to the specified group members.

    Args: \n
        amount (float): The amount of the debt.
        description (str): The description for the debt.
        debtor_ids (list): List of user IDs who owe the debt.

    Returns:
        str: A success message.

    Raises:
        HTTPException: If no debtors are provided.
    """
    if not debtor_ids:
        logger.warning(
            f"No debtors provided by user '{current_user.username}' (ID: {current_user.id})"
        )
        raise HTTPException(status_code=400, detail="No debtors provided")

    logger.info(
        f"Sending debt notification from user '{current_user.username}' (ID: {current_user.id}) to debtors: {debtor_ids} with amount {amount}"
    )
    for debtor_id in debtor_ids:
        if (
            debtor_id != current_user.id
        ):  # Ensure the payer doesn't get a debt notification
            debtor = db.query(User).filter(User.id == debtor_id).first()
            if not debtor:
                logger.error(
                    f"Debtor with ID {debtor_id} not found by user '{current_user.username}' (ID: {current_user.id})"
                )
                raise HTTPException(
                    status_code=404, detail=f"Debtor with ID {debtor_id} not found"
                )
            debt_notification = DebtNotification(
                amount=amount,
                description=description,
                debtor_id=debtor_id,
                creditor_id=current_user.id,
            )
            db.add(debt_notification)
            logger.info(
                f"Debt notification created for debtor {debtor_id} by user '{current_user.username}' (ID: {current_user.id})"
            )
        else:
            logger.warning(
                f"User '{current_user.username}' (ID: {current_user.id}) tried to send debt notification to the payer"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payer can't get a debt notification",
            )

    db.commit()
    logger.info(
        f"Debt notifications sent successfully to user '{current_user.username}' (ID: {current_user.id})"
    )
    return {"detail": "Debt notifications sent successfully"}


@router.post(
    "/respond_debt_notification/{debt_notification_id}", response_model=DetailResponse
)
def respond_debt_notification(
    background_tasks: BackgroundTasks,
    debt_notification_id: int,
    accept: bool,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Allows a debtor to accept or reject a debt notification.

    Args: \n
        debt_notification_id (int): The ID of the debt notification.
        accept (bool): Whether the debt is accepted or rejected.

    Returns:
        str: A success message.

    Raises:
        HTTPException: If the debt notification doesn't exist or is not for the current user.
    """
    logger.info(
        f"Responding to debt notification {debt_notification_id} with {'accept' if accept else 'reject'} by user '{current_user.username}' (ID: {current_user.id})"
    )
    debt_notification = (
        db.query(DebtNotification)
        .filter(
            DebtNotification.id == debt_notification_id,
            DebtNotification.status == False,
        )
        .first()
    )

    if not debt_notification:
        logger.error(
            f"Debt notification {debt_notification_id} not found for user '{current_user.username}' (ID: {current_user.id})"
        )
        raise HTTPException(status_code=404, detail="Debt notification not found")

    if debt_notification.debtor_id != current_user.id:
        logger.warning(
            f"User '{current_user.username}' (ID: {current_user.id}) is not the intended debtor for notification {debt_notification_id}"
        )
        raise HTTPException(
            status_code=403, detail="This debt notification is not for you"
        )

    # Update the status based on the user's response
    debt_notification.status = (
        DebtNotificationStatus.ACCEPTED if accept else DebtNotificationStatus.REJECTED
    )
    logger.info(
        f"Debt notification {debt_notification_id} status updated to {'ACCEPTED' if accept else 'REJECTED'} for user '{current_user.username}' (ID: {current_user.id})"
    )

    debt_category = (
        db.query(Category)
        .filter(
            Category.name == "Debt",
            Category.user_id == current_user.id,  # Add the user_id filter
        )
        .first()
    )

    if not debt_category:
        logger.error(
            f"Debt category not found for user '{current_user.username}' (ID: {current_user.id})"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Debt category not found"
        )

    if accept:
        # Create the expense for the debtor if they accept
        new_expense = Expense(
            amount=debt_notification.amount,
            description=debt_notification.description,
            user_id=current_user.id,
            category_id=debt_category.id,
        )
        db.add(new_expense)
        logger.info(
            f"Expense created for debtor '{current_user.username}' (ID: {current_user.id}) with amount {debt_notification.amount}"
        )

    db.commit()
    background_tasks.add_task(check_budget, current_user.id)
    new_notification = Notification(
        message=f"Debt notification for {debt_notification.amount} responded successfully",
        user_id=current_user.id,
    )
    db.add(new_notification)
    db.commit()
    logger.info(
        f"Expense created for debtor '{current_user.username}' (ID: {current_user.id}) with amount {debt_notification.amount}"
    )
    logger.info(
        f"Debt notification {debt_notification_id} responded successfully for user '{current_user.username}' (ID: {current_user.id})"
    )
    return {"detail": "Debt notification responded successfully"}


@router.get("/debt-notifications/", response_model=list[DebtNotificationResponse])
def get_debt_notifications(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """
    Retrieves all debt notifications for the current user.

    Args: \n
        None.

    Returns:
        List of DebtNotificationResponse: A list of debt notifications.

    Raises:
        HTTPException: If there are no notifications for the user.
    """
    logger.info(
        f"Retrieving debt notifications for user '{current_user.username}' (ID: {current_user.id})"
    )
    debt_notifications = (
        db.query(DebtNotification)
        .filter(
            DebtNotification.debtor_id == current_user.id,
            DebtNotification.status == False,
        )
        .all()
    )

    if not debt_notifications:
        logger.warning(
            f"No debt notifications found for user '{current_user.username}' (ID: {current_user.id})"
        )
        raise HTTPException(status_code=404, detail="No debt notifications found")

    logger.info(
        f"Found {len(debt_notifications)} debt notifications for user '{current_user.username}' (ID: {current_user.id})"
    )
    return debt_notifications
