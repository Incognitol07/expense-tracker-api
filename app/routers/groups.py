# app/routers/groups.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.schemas import (
    GroupMemberStatus,
    Groups,
    GroupCreate,
    GroupMembers,
    GroupMemberCreate,
    GroupMemberResponse,
    DetailResponse,
    GroupResponse,
    GroupDetailResponse,
    GroupMemberExpenseShare,
)
from app.models import User, Group, GroupMember, Notification, NotificationType
from app.database import get_db
from app.routers.auth import get_current_user
from app.utils import (
    logger, 
    get_group_by_id, 
    log_exception,
    check_group_membership,
    get_member_model,
    send_notification
)

router = APIRouter()


# 1. Create a new group
@router.post("/", response_model=Groups)
def create_group(
    group: GroupCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing_group = db.query(Group).filter(Group.name == group.name).first()
    if existing_group:
        log_exception(
            log_level="warning",
            log_message=f"Attempt to create group with existing name '{group.name}' by '{current_user.username}'",
            status_raised=status.HTTP_400_BAD_REQUEST,
            exception_message="Group name already exists",
        )
    new_group = Group(name=group.name)
    db.add(new_group)
    db.commit()
    db.refresh(new_group)

    # Add current user as a manager of the group
    group_member = GroupMember(
        user_id=current_user.id, group_id=new_group.id, role="manager", status="active"
    )
    db.add(group_member)
    db.commit()

    logger.info(f"Created group ID: {new_group.id} successfully for user '{current_user.username}' (ID: {current_user.id})")
    return new_group


# 2. Add a member to a group
@router.post("/{group_id}/members", response_model=GroupMemberResponse)
def add_member(
    group_id: int,
    member: GroupMemberCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_group_membership(group_id=group_id, user=current_user, db=db)
    group = get_group_by_id(db=db, current_user=current_user, group_id=group_id)

    # Check if current user is manager of the group
    get_member_model(db=db, current_user=current_user, group_id=group_id, manager=True)

    # Look up the user by email
    user = db.query(User).filter(User.email == member.email).first()
    if not user:
        log_exception(
            log_level="warning",
            log_message=f"User with email '{member.email}' not found for group ID: {group.id}",
            status_raised=status.HTTP_404_NOT_FOUND,
            exception_message="User with this email not found",
        )

    # Check if user is already a member
    get_member_model(db=db, user=user, group_id=group_id, check_if_not_exists=True)

    # Create new member with the user's ID
    new_member = GroupMember(
        user_id=user.id, group_id=group_id, role="member", status="pending"
    )
    db.add(new_member)
    db.commit()
    db.refresh(new_member)

    # Send notification to new member
    send_notification(
        db=db, 
        user_id=user.id, 
        type=NotificationType.ALERT,
        message=f"You've been invited to join group '{group.name}' by '{current_user.username}'. Please accept or reject the invitation."
    )

    # Send notification to manager
    send_notification(
        db=db, 
        user_id=current_user.id, 
        type=NotificationType.ALERT,
        message=f"You've invited '{user.username}' to join group '{group.name}'."
    )

    logger.info(f"Added member ID: {new_member.user_id} to group ID: {group.id} successfully for user '{current_user.username}' (ID: {current_user.id})")
    return new_member


# 2. Remove a member from a group
@router.delete("/member/{group_id}", response_model=DetailResponse)
def remove_member(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_group_membership(group_id=group_id, user=current_user, db=db)
    group = get_group_by_id(db=db, current_user=current_user, group_id=group_id)

    # Check if user is already a member
    existing_member = get_member_model(
        db=db, 
        user=current_user, 
        group_id=group_id, 
        active=True
    )

    db.delete(existing_member)
    db.commit()

    if existing_member.role == "manager":
        db.delete(group)
        db.commit()

    logger.info(
        f"Removed member ID: {current_user.id} from group ID: {group.id} successfully for user '{current_user.username}'"
    )
    return {"detail": f"Deleted from group '{group.name}' successfully"}


@router.delete("/{group_id}", response_model=DetailResponse)
def remove_group(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_group_membership(group_id=group_id, user=current_user, db=db)
    group = get_group_by_id(db=db, current_user=current_user, group_id=group_id)

    get_member_model(
        db=db, 
        user=current_user, 
        group_id=group_id,
        manager=True
    )
    db.delete(group)
    db.commit()
    return {"detail": f"Deleted group '{group.name}' successfully"}


# 3. Approve or reject a group join request
@router.put("/members", response_model=GroupMembers)
def update_member_status(
    status_sent: GroupMemberStatus,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_group_membership(group_id=status_sent.group_id, user=current_user, db=db)
    member = get_member_model(db=db, user=current_user, group_id=status_sent.group_id)

    if member.status != "pending":
        logger.warning(
            f"Pending invitation not found or already processed for group ID: {status_sent.group_id} for user '{current_user.username}' (ID: {current_user.id})"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Pending invitation not found"
        )

    # Check if the current user is the member being invited
    if member.user_id != current_user.id:
        logger.warning(
            f"User '{current_user.username}' (ID: {current_user.id}) is not the invited member in this request"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This invitation is not for you",
        )

    # Update the status to "active" if the user accepts
    member.status = "active" if status_sent.status == "accepted" else "rejected"
    db.commit()
    db.refresh(member)

    rejected_member = (
        db.query(GroupMember)
        .filter(
            GroupMember.user_id == current_user.id,
            GroupMember.group_id == status_sent.group_id,
            GroupMember.status == "rejected",
        )
        .first()
    )
    if rejected_member:
        db.delete(rejected_member)
        db.commit()
        logger.info(
            f"Removed member {rejected_member.id} from group_id {status_sent.group_id} "
        )

    logger.info(
        f"Updated member status for user '{current_user.username}' (ID: {current_user.id}) to '{member.status}' in group ID: {member.group_id}"
    )
    return member


@router.delete("/{group_id}/members/{member_id}", response_model=DetailResponse)
def remove_member_as_manager(
    group_id: int,
    member_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Manager removes a member from the group.
    """
    check_group_membership(group_id=group_id, user=current_user, db=db)
    group = get_group_by_id(db=db, current_user=current_user, group_id=group_id)

    # Verify the current user is a manager in the group
    manager_check = get_member_model(db=db, user=current_user, group_id=group_id, active=True, manager=True)

    # Verify the member to be removed exists and is part of the group
    member_to_remove = (
        db.query(GroupMember)
        .filter(
            GroupMember.id == member_id,
            GroupMember.group_id == group_id,
            GroupMember.status == "active",
        )
        .first()
    )
    if not member_to_remove:
        logger.warning(
            f"Member ID: {member_id} not found in group ID: {group_id} by manager '{current_user.username}' (ID: {current_user.id})."
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found in the group",
        )

    # Prevent removing another manager
    if member_to_remove.role == "manager":
        logger.warning(
            f"Manager '{current_user.username}' (ID: {current_user.id}) attempted to remove another manager (ID: {member_id}) from group ID: {group_id}."
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot remove another manager from the group",
        )

    # Remove the member from the group
    db.delete(member_to_remove)
    db.commit()

    # Log the successful removal
    logger.info(
        f"Manager '{current_user.username}' (ID: {current_user.id}) successfully removed member ID: {member_id} from group ID: {group_id}."
    )

    # Return a success response
    return {
        "detail": f"Member ID {member_id} was removed from group '{group.name}' by manager '{current_user.username}'."
    }


@router.get("/", response_model=list[GroupResponse] | None)
def get_all_groups_details_for_user(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    member_ids = (
        db.query(GroupMember.id).
        filter(GroupMember.user_id == current_user.id)
        .all()
    )
    group_ids = (
        db.query(GroupMember.group_id)
        .filter(GroupMember.user_id == current_user.id)
        .all()
    )
    group_roles = (
        db.query(GroupMember.role)
        .filter(GroupMember.user_id == current_user.id)
        .all()
    )
    group_statuses = (
        db.query(GroupMember.status)
        .filter(GroupMember.user_id == current_user.id)
        .all()
    )
    if group_ids:
        group_list = []
        for group_id in group_ids:
            for group_role in group_roles:
                for group_status in group_statuses:
                    for member_id in member_ids:
                        group_name = (
                            db.query(Group.name).filter(Group.id == group_id[0]).first()
                        )
                        group_list.append(
                            {
                                "group_id": group_id[0],
                                "group_role": group_role[0],
                                "group_name": group_name[0],
                                "member_status": group_status[0],
                                "member_id": member_id[0],
                            }
                        )
        logger.info(f"User '{current_user.username}' logged in successfully.")
        return group_list


# 8. Get group details
@router.get("/{group_id}/details", response_model=GroupDetailResponse)
def get_group_details(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get details of a specific group, including members and group name.
    """
    group = get_group_by_id(db=db, current_user=current_user, group_id=group_id)

    # Check if the current user is a member of the group
    member = get_member_model(db=db, user=current_user, group_id=group_id, active=True)

    # Fetch all group members
    members = db.query(GroupMember).filter(GroupMember.group_id == group_id).all()
    member_list = []
    for member in members:
        username = db.query(User.username).filter(User.id == member.user_id).first()[0]
        member_list.append(
            {
                "member_id": member.id,
                "user_id": member.user_id,
                "username": username,
                "role": member.role,
                "status": member.status,
            }
        )

    # Build the response
    group_details = {"id": group.id, "name": group.name, "members": member_list}

    logger.info(
        f"Fetched details for group ID: {group_id} successfully for user '{current_user.username}' (ID: {current_user.id})."
    )
    return group_details
