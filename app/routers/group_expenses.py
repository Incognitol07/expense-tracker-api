# app/routers/group_expenses.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.schemas import (
    GroupExpenses,
    GroupExpenseCreate,
    ExpenseSplitCreate,
    GroupMemberExpenseShare
)
from app.models import (
    User,
    Group,
    GroupExpense,
    GroupMember,
    ExpenseSplit,
    Notification,
    GroupDebt
)
from app.database import get_db
from app.routers.auth import get_current_user
from app.utils import logger

router = APIRouter()

@router.get("/{group_id}/expenses", response_model=list[GroupExpenses])
def get_group_expenses(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Ensure the user is a member of the group
    member_check = db.query(GroupMember).filter(
        GroupMember.user_id == current_user.id, GroupMember.group_id == group_id, GroupMember.status == "active"
    ).first()
    if not member_check:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You must be an active member of the group to view expenses")

    expenses = db.query(GroupExpense).filter(GroupExpense.group_id == group_id).all()
    return [
        GroupExpenses(id=expense.id, payer_id=expense.payer_id, amount=expense.amount, description=expense.description, created_at=expense.created_at)
        for expense in expenses
    ]

@router.get("/{group_id}/expenses/{expense_id}/share", response_model=GroupMemberExpenseShare)
def get_member_expense_share(
    group_id: int,
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Ensure the user is a member of the group
    member_check = db.query(GroupMember).filter(
        GroupMember.user_id == current_user.id, GroupMember.group_id == group_id, GroupMember.status == "active"
    ).first()
    if not member_check:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You must be an active member of the group to view expenses")

    # Find the expense and its splits
    expense = db.query(GroupExpense).filter(GroupExpense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")

    splits = db.query(ExpenseSplit).filter(ExpenseSplit.expense_id == expense.id).all()
    total_amount = sum(split.amount for split in splits)
    user_share = next((split.amount for split in splits if split.user_id == current_user.id), 0)

    return GroupMemberExpenseShare(amount=user_share, total_amount=total_amount, description=expense.description)


@router.post("/{group_id}/expenses", response_model=GroupExpenses)
def create_and_split_group_expense(
    group_id: int,
    expense: GroupExpenseCreate,
    splits: list[ExpenseSplitCreate],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Ensure user is a member of the group
    member = db.query(GroupMember).filter_by(user_id=current_user.id, group_id=group_id, status="active").first()
    if not member:
        logger.warning(f"User '{current_user.username}' (ID: {current_user.id}) is not an active member of group ID: {group_id}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You must be an active group member to add expenses")

    # Create the expense entry
    new_expense = GroupExpense(
        group_id=group_id,
        payer_id=current_user.id,
        amount=expense.amount,
        description=expense.description,
    )
    db.add(new_expense)
    db.commit()
    db.refresh(new_expense)

    # Validate split total matches the expense amount
    total_split_amount = sum(split.amount for split in splits)
    if total_split_amount != expense.amount:
        logger.warning(f"Split total of {total_split_amount} does not match the expense amount {expense.amount}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The total split amount must equal the expense amount")

    # Process each split and track debts
    expense_splits = []
    for split in splits:
        # Ensure the user is a valid group member
        group_member_check = db.query(GroupMember).filter(
            GroupMember.user_id == split.user_id,
            GroupMember.group_id == group_id,
            GroupMember.status == "active"
        ).first()
        if not group_member_check:
            logger.warning(f"User '{split.user_id}' is not a member of group ID: {group_id}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"User {split.user_id} is not a member of the group")

        # Add split to the database
        expense_split = ExpenseSplit(expense_id=new_expense.id, user_id=split.user_id, amount=split.amount)
        db.add(expense_split)
        expense_splits.append(expense_split)

        # Create GroupDebt for other members who owe money
        if split.user_id != current_user.id:
            group_debt = GroupDebt(
                group_id=group_id,
                debtor_id=split.user_id,
                creditor_id=current_user.id,
                amount=split.amount,
                description=f"You owe {current_user.username} {split.amount} for '{new_expense.description}'",
            )
            db.add(group_debt)

            # Create notification for the debtor
            notification = Notification(
                user_id=split.user_id,
                message=f"You owe {current_user.username} {split.amount} for '{new_expense.description}'",
            )
            db.add(notification)

    db.commit()

    logger.info(f"Created and split group expense ID: {new_expense.id} successfully for user '{current_user.username}' (ID: {current_user.id}) in group ID: {group_id}")
    
    return {
        "id": new_expense.id,
        "group_id": new_expense.group_id,
        "payer_id": new_expense.payer_id,
        "amount": new_expense.amount,
        "description": new_expense.description,
        "splits": [
            {"id": split.id, "expense_id": new_expense.id, "user_id": split.user_id, "amount": split.amount}
            for split in expense_splits
        ],
    }

# New route to view the debts (People I'm Owing)
@router.get("/{group_id}/debts", response_model=dict)
def get_group_debts(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Ensure the user is a member of the group
    member_check = db.query(GroupMember).filter(
        GroupMember.user_id == current_user.id, GroupMember.group_id == group_id, GroupMember.status == "active"
    ).first()
    if not member_check:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You must be an active member of the group to view debts")

    # Get all debts where the user is the debtor in the group
    debts = db.query(GroupDebt).filter(
        GroupDebt.debtor_id == current_user.id,
        GroupDebt.group_id == group_id,
        GroupDebt.status == "active",
    ).all()

    debt_summary = {
        "total_owe": sum(debt.amount for debt in debts),
        "debts": [{"from_user": debt.debtor_id, "amount": debt.amount, "description": debt.description} for debt in debts],
    }

    return debt_summary

