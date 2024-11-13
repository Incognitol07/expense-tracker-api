# app/routers/debt_notifications.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import DebtNotification, User, Expense
from app.routers.auth import get_current_user
from app.schemas import DebtNotificationStatus

router = APIRouter()

@router.post("/send_debt_notification/")
def send_debt_notification(
    amount: float,
    description: str,
    debtor_ids: list[int],  # List of user IDs who owe the debt
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Sends a debt notification to the specified group members.

    Args:
        amount (float): The amount of the debt.
        description (str): The description for the debt.
        debtor_ids (list): List of user IDs who owe the debt.
    
    Returns:
        str: A success message.
    
    Raises:
        HTTPException: If no debtors are provided.
    """
    if not debtor_ids:
        raise HTTPException(status_code=400, detail="No debtors provided")

    for debtor_id in debtor_ids:
        if debtor_id != current_user.id:  # Ensure the payer doesn't get a debt notification
            debtor = db.query(User).filter(User.id == debtor_id).first()
            if not debtor:
                raise HTTPException(status_code=404, detail=f"Debtor with ID {debtor_id} not found")
            debt_notification = DebtNotification(
                amount=amount,
                description=description,
                debtor_id=debtor_id,
                creditor_id=current_user.id
            )
            db.add(debt_notification)


    db.commit()
    return {"message": "Debt notifications sent successfully"}

# app/routers/debt_notifications.py (continued)

@router.post("/respond_debt_notification/{debt_notification_id}")
def respond_debt_notification(
    debt_notification_id: int,
    accept: bool,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Allows a debtor to accept or reject a debt notification.

    Args:
        debt_notification_id (int): The ID of the debt notification.
        accept (bool): Whether the debt is accepted or rejected.
    
    Returns:
        str: A success message.
    
    Raises:
        HTTPException: If the debt notification doesn't exist or is not for the current user.
    """
    debt_notification = db.query(DebtNotification).filter(DebtNotification.id == debt_notification_id).first()

    if not debt_notification:
        raise HTTPException(status_code=404, detail="Debt notification not found")

    if debt_notification.debtor_id != current_user.id:
        raise HTTPException(status_code=403, detail="This debt notification is not for you")

    # Update the status based on the user's response
    debt_notification.status = accept


    if accept:
        # Create the expense for the debtor if they accept
        new_expense = Expense(
            amount=debt_notification.amount,
            description=debt_notification.description,
            user_id=current_user.id,
            category_id=1  # You can adjust the category as needed
        )
        db.add(new_expense)

    db.commit()
    return {"message": "Debt notification responded successfully"}

