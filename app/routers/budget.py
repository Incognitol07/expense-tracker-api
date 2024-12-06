# app/routers/budget.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi import BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.schemas import (
    GeneralBudgetCreate,
    GeneralBudgetUpdate,
    GeneralBudgetResponse,
    GeneralBudgetStatus,
    GeneralBudgetHistory,
    DetailResponse,
)
from app.models import GeneralBudget, Notification, CategoryBudget
from app.database import get_db
from app.routers.auth import get_current_user
from app.models import User
from app.background_tasks import check_budget, check_and_deactivate_expired_budgets
from app.utils import logger

# Create an instance of APIRouter to handle budget-related routes
router = APIRouter()


# Route to set a new budget for the user
@router.post(
    "/", response_model=GeneralBudgetResponse, status_code=status.HTTP_201_CREATED
)
def set_general_budget(
    background_tasks: BackgroundTasks,
    budget_data: GeneralBudgetCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Creates a new budget for the authenticated user.

    Args: \n
        budget_data (GeneralBudgetCreate): The budget data to create a new budget.
        db (Session): The database session for interacting with the database.
        user (User): The authenticated user requesting to set the budget.

    Raises:
        HTTPException: If a budget is already set for the user, suggesting to use the update route.

    Returns:
        GeneralBudgetResponse: The newly created budget.
    """
    # Check if the user already has a set budget
    existing_budget = (
        db.query(GeneralBudget)
        .filter(
            GeneralBudget.user_id == user.id,
            GeneralBudget.status == "active",
            GeneralBudget.start_date <= budget_data.end_date,
            GeneralBudget.end_date >= budget_data.start_date,
        )
        .first()
    )
    if existing_budget:
        logger.warning(
            f"User '{user.username}' (ID: {user.id}) attempted to create a budget, but an active budget already exists."
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An active budget already exists in the given date range. Use update instead.",
        )
    
    total_category_budget = (
        db.query(func.sum(CategoryBudget.amount_limit))
        .filter(CategoryBudget.user_id==user.id,
                CategoryBudget.status =="active"
                )
        .scalar() or 0.0
    )
    
    if budget_data.amount_limit<total_category_budget:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail=f"General budget cannot be less than total category budget of {total_category_budget}"
            )

    # Create and save the new budget
    new_budget = GeneralBudget(**budget_data.model_dump(), user_id=user.id)
    db.add(new_budget)
    db.commit()
    db.refresh(new_budget)
    background_tasks.add_task(check_budget, user.id)
    background_tasks.add_task(check_and_deactivate_expired_budgets)
    logger.info(
        f"New budget created for user '{user.username}' (ID: {user.id}) with amount {new_budget.amount_limit} from {new_budget.start_date} to {new_budget.end_date}."
    )

    return new_budget


# Route to get the current budget of the user
@router.get("/", response_model=GeneralBudgetResponse)
def get_general_budget(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """
    Retrieves the current budget set by the authenticated user.

    Args: \n
        db (Session): The database session for querying the budget.
        user (User): The authenticated user whose budget is to be fetched.

    Raises:
        HTTPException: If no budget is set for the user.

    Returns:
        GeneralBudgetResponse: The user's current budget.
    """
    budget = (
        db.query(GeneralBudget)
        .filter(GeneralBudget.user_id == user.id, GeneralBudget.status == "active")
        .first()
    )
    if not budget:
        logger.error(
            f"No active budget found for user '{user.username}' (ID: {user.id})."
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="GeneralBudget not set."
        )
    logger.info(
        f"Retrieved active budget for user '{user.username}' (ID: {user.id}) with amount {budget.amount_limit}."
    )
    return budget


# Route to update the user's existing budget
@router.put("/", response_model=GeneralBudgetResponse)
def update_general_budget(
    background_tasks: BackgroundTasks,
    budget_data: GeneralBudgetUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Updates the existing budget of the authenticated user and resets notifications if needed.
    """

    # Check if the user has an existing budget
    budget = (
        db.query(GeneralBudget)
        .filter(GeneralBudget.user_id == user.id, GeneralBudget.status == "active")
        .first()
    )
    if not budget:
        logger.error(
            f"No active budget found for user '{user.username}' (ID: {user.id}) to update."
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="GeneralBudget not set."
        )

    conflicting_budget = (
        db.query(GeneralBudget)
        .filter(
            GeneralBudget.user_id == user.id,
            GeneralBudget.status == "active",
            GeneralBudget.id != budget.id,  # Exclude the current budget being updated
            GeneralBudget.start_date <= budget_data.end_date,
            GeneralBudget.end_date >= budget_data.start_date,
        )
        .first()
    )
    if conflicting_budget:
        logger.warning(
            f"User '{user.username}' (ID: {user.id}) attempted to update budget with conflicting dates."
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The updated budget dates conflict with another active budget.",
        )

    # Reset notifications for this budget
    db.query(Notification).filter(
        Notification.user_id == user.id,
        Notification.message.ilike("%budget%"),
        Notification.is_read == False,
    ).update({"is_read": True})
    db.commit()
    logger.info(
        f"Notifications reset for user '{user.username}' (ID: {user.id}) due to budget update."
    )

    # Update the budget fields with the provided data
    for key, value in budget_data.model_dump(exclude_unset=True).items():
        setattr(budget, key, value)

    db.commit()
    db.refresh(budget)
    background_tasks.add_task(check_budget, user.id)
    background_tasks.add_task(check_and_deactivate_expired_budgets)
    logger.info(
        f"GeneralBudget updated for user '{user.username}' (ID: {user.id}) with new values."
    )
    return budget


# Route to get the current budget status for the user (remaining budget)
@router.get("/status", response_model=GeneralBudgetStatus)
def get_general_budget_status(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    """
    Retrieves the current status of the user's budget, including the remaining amount.

    Args: \n
        db (Session): The database session for querying the budget and expenses.
        user (User): The authenticated user whose budget status is to be fetched.

    Raises:
        HTTPException: If no budget is set for the user.

    Returns:
        GeneralBudgetStatus: The remaining budget, start date, and end date.
    """
    # Retrieve the user's current budget
    budget = (
        db.query(GeneralBudget)
        .filter(GeneralBudget.user_id == user.id, GeneralBudget.status == "active")
        .first()
    )
    if not budget:
        logger.error(
            f"No active budget found for user '{user.username}' (ID: {user.id})."
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="GeneralBudget not set."
        )

    # Calculate the remaining budget based on expenses within the specified date range
    expenses = [
        expense.amount
        for expense in budget.owner.expenses
        if budget.start_date <= expense.date <= budget.end_date
    ]
    remaining_amount = budget.amount_limit - sum(expenses)

    logger.info(
        f"GeneralBudget status successfully returned for user '{user.username}' (ID: {user.id})."
    )
    return GeneralBudgetStatus(
        remaining_amount=remaining_amount,
        start_date=budget.start_date,
        end_date=budget.end_date,
    )


# Route to get the history of all budgets for the user
@router.get("/history", response_model=list[GeneralBudgetHistory])
def get_general_budget_history(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    """
    Retrieves the history of all budgets set by the authenticated user.

    Args: \n
        db (Session): The database session for querying all budgets.
        user (User): The authenticated user whose budget history is to be fetched.

    Returns:
        list[GeneralBudgetHistory]: A list of all previous budgets for the user.
    """
    budgets = db.query(GeneralBudget).filter(GeneralBudget.user_id == user.id).all()
    logger.info(
        f"GeneralBudget history successfully returned for user '{user.username}' (ID: {user.id})."
    )
    return budgets


# Route to deactivate the user's current budget
@router.post("/deactivate", response_model=DetailResponse)
def deactivate_general_budget(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    """
    Deletes the currently set budget for the authenticated user.

    Args: \n
        db (Session): The database session for querying and deleting the budget.
        user (User): The authenticated user requesting to delete their budget.

    Raises:
        HTTPException: If no budget is set for the user.

    Returns:
        dict: A confirmation message indicating successful deletion.
    """
    # Check if the user has an existing budget to delete
    budget = (
        db.query(GeneralBudget)
        .filter(GeneralBudget.user_id == user.id, GeneralBudget.status == "active")
        .first()
    )
    if not budget:
        logger.error(
            f"No active budget found for user '{user.username}' (ID: {user.id}) to update."
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="GeneralBudget not set."
        )

    db.query(Notification).filter(
        Notification.user_id == user.id,
        Notification.message.ilike("%budget%"),
        Notification.is_read == False,
    ).update({"is_read": True})
    db.commit()
    logger.info(
        f"Notifications reset for user '{user.username}' (ID: {user.id}) due to budget deactivation."
    )

    # Deactivate the budget and commit the changes
    setattr(budget, "status", "deactivated")
    db.commit()
    db.refresh(budget)
    logger.info(
        f"Deactivated budget of amount {budget.amount_limit} for {budget.start_date} to {budget.end_date} successfully for user '{user.username}' (ID: {user.id})."
    )
    return {
        "detail": f"Deactivated budget of amount {budget.amount_limit} for {budget.start_date} to {budget.end_date} successfully"
    }


# Route to delete the user's current budget
@router.delete("/{budget_id}", response_model=DetailResponse)
def delete_general_budget(
    budget_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Deletes the currently set budget for the authenticated user.

    Args: \n
        db (Session): The database session for querying and deleting the budget.
        user (User): The authenticated user requesting to delete their budget.

    Raises:
        HTTPException: If no budget is set for the user.

    Returns:
        dict: A confirmation message indicating successful deletion.
    """
    # Check if the user has an existing budget to delete
    budget = (
        db.query(GeneralBudget)
        .filter(GeneralBudget.user_id == user.id, GeneralBudget.id == budget_id)
        .first()
    )
    if not budget:
        logger.error(
            f"GeneralBudget not found for user '{user.username}' (ID: {user.id})."
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="GeneralBudget not found."
        )
    if budget.status != "active":
        logger.warning(
            f"User '{user.username}' (ID: {user.id}) attempted to delete a non-active budget."
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only active budgets can be deleted. Please deactivate or update the budget.",
        )

    db.query(Notification).filter(
        Notification.user_id == user.id,
        Notification.message.ilike("%budget%"),
        Notification.is_read == False,
    ).update({"is_read": True})
    db.commit()
    logger.info(
        f"Notifications reset for user '{user.username}' (ID: {user.id}) due to budget deletion."
    )

    # Delete the budget and commit the changes
    db.delete(budget)
    db.commit()
    logger.info(
        f"Deleted budget of amount {budget.amount_limit} for user '{user.username}' (ID: {user.id}) successfully."
    )
    return {"detail": "Deleted successfully"}
