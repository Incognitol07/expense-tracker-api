# app/routers/groups.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.schemas import GroupMemberStatus, Groups, GroupCreate, GroupExpenses, GroupExpenseCreate, GroupMembers, GroupMemberCreate, ExpenseSplitCreate, DebtNotifications, GroupMemberResponse
from app.models import User, Group, GroupExpense, GroupMember, ExpenseSplit, Notification, DebtNotification, Expense, Category
from app.database import get_db
from app.routers.auth import get_current_user
from app.utils import logger

router = APIRouter()

# 1. Create a new group
@router.post("/", response_model=Groups)
def create_group(group: GroupCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    new_group = Group(name=group.name)
    db.add(new_group)
    db.commit()
    db.refresh(new_group)

    # Add current user as an admin of the group
    group_member = GroupMember(user_id=current_user.id, group_id=new_group.id, role="admin", status="active")
    db.add(group_member)
    db.commit()

    logger.info(f"Created group ID: {new_group.id} successfully for user '{current_user.username}' (ID: {current_user.id})")
    return new_group

# 2. Add a member to a group
@router.post("/{group_id}/members", response_model=GroupMemberResponse)
def add_member(group_id: int, member: GroupMemberCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        logger.warning(f"Group ID: {group_id} not found for user '{current_user.username}' (ID: {current_user.id})")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")

    # Check if current user is admin of the group
    admin_check = db.query(GroupMember).filter(GroupMember.user_id == current_user.id, GroupMember.group_id == group_id, GroupMember.role == "admin").first()
    if not admin_check:
        logger.warning(f"User '{current_user.username}' (ID: {current_user.id}) is not an admin in group ID: {group.id}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only group admins can add members")

    # Look up the user by email
    user = db.query(User).filter(User.email == member.email).first()
    if not user:
        logger.warning(f"User ID: {user.id} is already a member of group ID: {group.id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User with this email not found")

    # Check if user is already a member
    existing_member = db.query(GroupMember).filter(GroupMember.user_id == user.id, GroupMember.group_id == group_id).first()
    if existing_member:
        logger.warning(f"User with email '{member.email}' not found for group ID: {group.id}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is already a member of the group")

    # Create new member with the user's ID
    new_member = GroupMember(user_id=user.id, group_id=group_id, role="member", status="pending")
    db.add(new_member)
    db.commit()
    db.refresh(new_member)

    # Send notification to new member
    notification = Notification(user_id=user.id, message=f"You've been invited to join group '{group.name}'. Please accept or reject the invitation.")
    db.add(notification)
    db.commit()

    logger.info(f"Added member ID: {new_member.user_id} to group ID: {group.id} successfully for user '{current_user.username}' (ID: {current_user.id})")
    return new_member

# 3. Approve or reject a group join request
@router.put("/members/{member_id}", response_model=GroupMembers)
def update_member_status(member_id: int, status_sent: GroupMemberStatus, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    member = db.query(GroupMember).filter(GroupMember.id == member_id).first()
    
    if not member or member.status != "pending":
        logger.warning(f"Pending invitation not found or already processed for member ID: {member_id} for user '{current_user.username}' (ID: {current_user.id})")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pending invitation not found")

    # Check if the current user is the member being invited
    if member.user_id != current_user.id:
        logger.warning(f"User '{current_user.username}' (ID: {current_user.id}) is not the invited member in this request")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This invitation is not for you")

    # Update the status to "active" if the user accepts
    member.status = "active" if status_sent.status == "accepted" else "rejected"
    db.commit()
    db.refresh(member)

    logger.info(f"Updated member status for user '{current_user.username}' (ID: {current_user.id}) to '{member.status}' in group ID: {member.group_id}")
    return member

# 4. Create a group expense
@router.post("/{group_id}/expenses", response_model=GroupExpenses)
def create_and_split_group_expense(
    group_id: int,
    expense: GroupExpenseCreate,
    splits: list[ExpenseSplitCreate],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Ensure user is a member of the group
    member = db.query(GroupMember).filter_by(user_id=current_user.id, group_id=group_id, status="active").first()
    if not member:
        logger.warning(f"User '{current_user.username}' (ID: {current_user.id}) is not a member of group ID: {group_id}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You must be a group member to add expenses")

    # Create the expense entry
    new_expense = GroupExpense(group_id=group_id, payer_id=current_user.id, amount=expense.amount, description=expense.description)
    db.add(new_expense)
    db.commit()
    db.refresh(new_expense)

    # Validate split total
    total_split_amount = sum(split.amount for split in splits)
    if total_split_amount != expense.amount:
        logger.warning(f"Split total of {total_split_amount} does not match the expense amount {expense.amount} for user '{current_user.username}' (ID: {current_user.id})")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The total split amount must equal the expense amount")

    # Process each split
    expense_splits = []
    for split in splits:
        group_member_check = db.query(GroupMember).filter(GroupMember.user_id == split.user_id, GroupMember.group_id == group_id).first()
        if not group_member_check:
            logger.warning(f"User '{current_user.username}' (ID: {split.user_id}) is not a member of group ID: {group_id}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"User {split.user_id} is not a member of the group")

        expense_split = ExpenseSplit(expense_id=new_expense.id, user_id=split.user_id, amount=split.amount)
        db.add(expense_split)
        expense_splits.append(expense_split)

        if split.user_id != current_user.id:
            debt_notification = DebtNotification(
                amount=split.amount,
                description=f"You owe {split.amount} for '{new_expense.description}'",
                debtor_id=split.user_id,
                creditor_id=current_user.id
            )
            db.add(debt_notification)

            notification = Notification(user_id=split.user_id, message=f"You owe {split.amount} for '{new_expense.description}'")
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
        ]
    }

# 6. Get all expenses for a group
@router.get("/{group_id}/expenses", response_model=list[GroupExpenses])
def get_group_expenses(group_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Check if the current user is a member of the group
    member = db.query(GroupMember).filter_by(user_id=current_user.id, group_id=group_id).first()
    if not member:
        logger.warning(f"User '{current_user.username}' (ID: {current_user.id}) is not a member of group ID: {group_id}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not a member of this group")

    # Optional: Check user role to limit access (e.g., only admins can view full expense details)
    if member.role != 'admin':  # Assuming only admins can access all expenses
        logger.warning(f"User '{current_user.username}' (ID: {current_user.id}) is not an admin in group ID: {group_id}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to view all expenses")

    expenses = db.query(GroupExpense).filter(GroupExpense.group_id == group_id).all()

    logger.info(f"Fetched all expenses for group ID: {group_id} successfully for user '{current_user.username}' (ID: {current_user.id})")
    return expenses

# 7. Get all members of a group
@router.get("/{group_id}/members", response_model=list[GroupMembers])
def get_group_members(group_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    member = db.query(GroupMember).filter_by(user_id=current_user.id, group_id=group_id).first()
    if not member:
        logger.warning(f"User '{current_user.username}' (ID: {current_user.id}) is not a member of group ID: {group_id}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not a member of this group")

    members = db.query(GroupMember).filter(GroupMember.group_id == group_id).all()

    logger.info(f"Fetched all members for group ID: {group_id} successfully for user '{current_user.username}' (ID: {current_user.id})")
    return members

# Responding to debt notification with dynamic category assignment
@router.put("/debt_notifications/{debt_notification_id}", response_model=DebtNotifications)
def respond_to_debt_notification(debt_notification_id: int, accept: bool, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    debt_notification = db.query(DebtNotification).filter(DebtNotification.id == debt_notification_id).first()
    
    if not debt_notification:
        logger.warning(f"Failed to retrieve debt notifications for user '{current_user.username}' (ID: {current_user.id})")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Debt notification not found")
    
    # Ensure the current user is the debtor in the notification
    if debt_notification.debtor_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not the debtor in this notification")

    debt_notification.accepted = accept
    db.commit()
    db.refresh(debt_notification)

    logger.info(f"Responded to debt notification ID: {debt_notification.id} for user '{current_user.username}' (ID: {current_user.id}) with {'accept' if accept else 'reject'}")
    return debt_notification