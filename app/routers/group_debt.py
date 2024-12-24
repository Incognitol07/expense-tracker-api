# app/routers/group_debt.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.models import (
    GroupDebt, 
    Notification,
    NotificationType, 
    User,
    Expense,
    Category
)
from app.database import get_db
from app.routers.auth import get_current_user
from app.utils import check_group_membership

router = APIRouter()

# Route to create a new debt record
@router.post("/{group_id}/debts")
def create_group_debt(
    group_id: int,
    debtor_id: int,
    creditor_id: int,
    amount: float,
    description: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Check group membership
    check_group_membership(group_id, current_user.id, db)
    
    # Create new debt record
    new_debt = GroupDebt(
        group_id=group_id,
        debtor_id=debtor_id,
        creditor_id=creditor_id,
        amount=amount,
        description=description
    )
    db.add(new_debt)
    db.commit()
    db.refresh(new_debt)

    # Create and send a debt notification
    notification = Notification(
        user_id=creditor_id,
        type=NotificationType.GROUP_DEBT,
        message=f"You are owed {amount} by {debtor_id} for {description}"
    )
    db.add(notification)
    db.commit()

    return {"message": "Debt created successfully", "debt": new_debt}

# Route to accept a debt
@router.put("/{debt_id}/accept")
def accept_debt(
    debt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    debt = db.query(GroupDebt).filter(GroupDebt.id == debt_id).first()
    if not debt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Debt not found")

    if debt.debtor_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You cannot accept a debt that is not yours")

    debt.status = "active"  # Mark debt as active for payment
    db.commit()
    db.refresh(debt)

    return {"message": "Debt accepted", "debt": debt}

# Route to dispute a debt
@router.put("/{debt_id}/dispute")
def dispute_debt(
    debt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    debt = db.query(GroupDebt).filter(GroupDebt.id == debt_id).first()
    if not debt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Debt not found")

    if debt.debtor_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You cannot dispute a debt that is not yours")

    debt.status = "disputed"
    db.commit()
    db.refresh(debt)

    return {"message": "Debt disputed", "debt": debt}

# Route to pay a debt (partial or full)
@router.put("/{debt_id}/pay")
def pay_debt(
    debt_id: int,
    amount_paid: float,
    payment_type: str,  # 'partial' or 'full'
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payment_type not in ["partial", "full"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Invalid payment type"
        )

    debt = db.query(GroupDebt).filter(GroupDebt.id == debt_id).first()
    if not debt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Debt not found"
        )

    if debt.debtor_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="You cannot pay a debt that is not yours"
        )

    # Update the amount paid
    if payment_type == "full":
        amount_paid = debt.amount - debt.amount_paid  # Pay the remaining balance
    elif amount_paid > (debt.amount - debt.amount_paid):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Amount paid exceeds the remaining debt"
        )
    debt.amount_paid += amount_paid

    # Update debt status based on payment
    if debt.amount_paid >= debt.amount:
        debt.status = "paid"
    else:
        debt.status = "partial"

    # Associate debt payment with the 'Debt' category as an expense
    debt_category = db.query(Category).filter(
        Category.name == "Group Debts", 
        Category.user_id == current_user.id
    ).first()

    if not debt_category:
        # Create the Debt category for the user if it doesn't exist
        debt_category = Category(
            name="Group Debts",
            user_id=current_user.id
        )
        db.add(debt_category)
        db.commit()
        db.refresh(debt_category)

    # Add a new expense for this debt payment
    new_expense = Expense(
        amount=amount_paid,
        name=f"Payment for Debt #{debt.description}",
        user_id=current_user.id,
        category_id=debt_category.id,
    )
    db.add(new_expense)

    # Notify the creditor about the payment
    notification = Notification(
        user_id=debt.creditor_id,
        type=NotificationType.GROUP_DEBT,
        message=f"{current_user.username} has paid {amount_paid} towards your debt"
    )
    db.add(notification)

    db.commit()
    db.refresh(debt)
    db.refresh(new_expense)

    return {
        "message": f"Debt payment ({payment_type}) successful", 
        "debt": debt,
        "expense": new_expense
    }

# Route for creditor to confirm the payment
@router.put("/{debt_id}/confirm-payment")
def confirm_payment(
    debt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    debt = db.query(GroupDebt).filter(GroupDebt.id == debt_id).first()
    if not debt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Debt not found")

    if debt.creditor_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to confirm payment")

    if debt.status != "partial":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No partial payment to confirm")

    debt.status = "paid"
    db.commit()
    db.refresh(debt)

    return {"message": "Payment confirmed", "debt": debt}

# Route to get all debts for the debtor
@router.get("/debts/owed")
def get_debts_owed(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    debts = db.query(GroupDebt).filter(GroupDebt.debtor_id == current_user.id).all()
    if not debts:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No debts found")

    return {
        "total_owed":sum(debt.amount for debt in debts),
        "debts": debts
        }

# Route to get all debts for the creditor
@router.get("/debts/owed-to")
def get_debts_owed_to(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    debts = db.query(GroupDebt).filter(GroupDebt.creditor_id == current_user.id).all()
    if not debts:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No debts found")

    return {
        "total_owed_to": sum(debt.amount for debt in debts),
        "debts": debts
        }
