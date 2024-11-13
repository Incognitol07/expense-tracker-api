# app/routers/groups.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.schemas import GroupMemberStatus, Groups, GroupCreate, GroupExpenses, GroupExpenseCreate, GroupMembers, GroupMemberCreate, ExpenseSplitCreate, DebtNotifications, GroupMemberResponse
from app.models import User, Group, GroupExpense, GroupMember, ExpenseSplit, Notification, DebtNotification, Expense, Category
from app.database import get_db
from app.routers.auth import get_current_user

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

    return new_group

# 2. Add a member to a group
@router.post("/{group_id}/members", response_model=GroupMemberResponse)
def add_member(group_id: int, member: GroupMemberCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")

    # Check if current user is admin of the group
    admin_check = db.query(GroupMember).filter(GroupMember.user_id == current_user.id, GroupMember.group_id == group_id, GroupMember.role == "admin").first()
    if not admin_check:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only group admins can add members")

    # Look up the user by email
    user = db.query(User).filter(User.email == member.email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User with this email not found")

    # Check if user is already a member
    existing_member = db.query(GroupMember).filter(GroupMember.user_id == user.id, GroupMember.group_id == group_id).first()
    if existing_member:
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

    return new_member



# 3. Approve or reject a group join request
@router.put("/members/{member_id}", response_model=GroupMembers)
def update_member_status(member_id: int, status_sent: GroupMemberStatus, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    member = db.query(GroupMember).filter(GroupMember.id == member_id).first()
    
    if not member or member.status != "pending":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pending invitation not found")

    # Check if the current user is the member being invited
    if member.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This invitation is not for you")

    # Update the status to "active" if the user accepts
    member.status = "active" if status_sent.status == "accepted" else "rejected"
    db.commit()
    db.refresh(member)

    return member



# 4. Create a group expense
@router.post("/{group_id}/expenses", response_model=GroupExpenses)
def create_and_split_group_expense(group_id: int, expense: GroupExpenseCreate, splits: list[ExpenseSplitCreate], db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Ensure user is a member of the group
    member = db.query(GroupMember).filter_by(user_id=current_user.id, group_id=group_id, status="active").first()
    if not member:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You must be a group member to add expenses")

    # Create the expense entry
    new_expense = GroupExpense(group_id=group_id, payer_id=current_user.id, amount=expense.amount, description=expense.description)
    db.add(new_expense)
    db.commit()
    db.refresh(new_expense)

    # Track total amount that is being split to ensure it matches the expense
    total_split_amount = sum(split.amount for split in splits)

    # Ensure that the total split amount equals the expense amount
    if total_split_amount != expense.amount:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The total split amount must equal the expense amount")

    # Process each split
    expense_splits = []
    for split in splits:
        # Ensure that the user is a member of the group
        group_member_check = db.query(GroupMember).filter(GroupMember.user_id == split.user_id, GroupMember.group_id == group_id).first()
        if not group_member_check:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"User {split.user_id} is not a member of the group")

        # Create expense split entries
        expense_split = ExpenseSplit(expense_id=new_expense.id, user_id=split.user_id, amount=split.amount)
        db.add(expense_split)
        expense_splits.append(expense_split)

        # Skip the payer when creating debt notifications
        if split.user_id != current_user.id:  # Payer is excluded
            # Create a debt notification for each member (this assumes you have a DebtNotification model)
            debt_notification = DebtNotification(
                amount=split.amount,
                description=f"You owe {split.amount} for '{new_expense.description}'",
                debtor_id=split.user_id,
                creditor_id=current_user.id
            )
            db.add(debt_notification)

            # Send a notification as well
            notification = Notification(user_id=split.user_id, message=f"You owe {split.amount} for '{new_expense.description}'")
            db.add(notification)

    db.commit()



# 6. Get all expenses for a group
@router.get("/{group_id}/expenses", response_model=list[GroupExpenses])
def get_group_expenses(group_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Check if the current user is a member of the group
    member = db.query(GroupMember).filter_by(user_id=current_user.id, group_id=group_id).first()
    if not member:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not a member of this group")

    # Optional: Check user role to limit access (e.g., only admins can view full expense details)
    if member.role != 'admin':  # Assuming only admins can access all expenses
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to view all expenses")

    expenses = db.query(GroupExpense).filter(GroupExpense.group_id == group_id).all()
    return expenses


# 7. Get all members of a group
@router.get("/{group_id}/members", response_model=list[GroupMembers])
def get_group_members(group_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    member = db.query(GroupMember).filter_by(user_id=current_user.id, group_id=group_id).first()
    if not member:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not a member of this group")

    members = db.query(GroupMember).filter(GroupMember.group_id == group_id).all()
    return members



# Responding to debt notification with dynamic category assignment
@router.put("/debt_notifications/{debt_notification_id}", response_model=DebtNotifications)
def respond_to_debt_notification(debt_notification_id: int, accept: bool, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    debt_notification = db.query(DebtNotification).filter(DebtNotification.id == debt_notification_id).first()
    
    if not debt_notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Debt notification not found")
    
    # Ensure the current user is the debtor in the notification
    if debt_notification.debtor_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This debt notification is not for you")
    
    # Retrieve the appropriate debt category for the current user
    debt_category = db.query(Category).filter(
        Category.name == "Debt", 
        Category.user_id == current_user.id  # Add the user_id filter
    ).first()

    if not debt_category:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Debt category not found")


    # Update the status based on the user's response
    debt_notification.status = accept

    if accept:
        # Create the expense for the debtor if they accept
        new_expense = Expense(
            amount=debt_notification.amount,
            description=debt_notification.description,
            user_id=current_user.id,
            category_id=debt_category.id  # Use the retrieved Debt category's ID
        )
        db.add(new_expense)

    db.commit()
    db.refresh(debt_notification)
    return debt_notification