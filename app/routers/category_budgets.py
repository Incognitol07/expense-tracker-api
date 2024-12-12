# app/routers/category_budget.py

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.schemas import (
    CategoryBudgetCreate,
    CategoryBudgetUpdate,
    CategoryBudgetResponse,
    CategoryBudgetStatus,
    CategoryBudgetHistory,
    DetailResponse,
    AllCategoryBudgetResponse
)
from app.models import (
    CategoryBudget, 
    Category, 
    Notification, 
    GeneralBudget
)
from app.database import get_db, SessionLocal
from app.routers.auth import get_current_user
from app.models import User
from app.background_tasks import check_category_budget
from app.websocket_manager import manager
from app.utils import logger

router = APIRouter()


@router.get("/{category_name}", response_model=CategoryBudgetResponse)
def retrieve_category_budget(
    category_name: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Retrieve an active category budget for the specified category.

    Args: \n
        category_name (str): category_name of the category.
        db (Session): Database session dependency.
        user (User): Authenticated user.

    Returns:
        CategoryBudgetResponse: The details of the active budget.
    """
    category = (
        db.query(Category)
        .filter(
            Category.user_id == user.id,
            Category.name == category_name,
        )
        .first()
    )
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category name '{category_name}' does not exist",
        )
    budget = (
        db.query(CategoryBudget)
        .filter(
            CategoryBudget.user_id == user.id,
            CategoryBudget.category_id == category.id,
            CategoryBudget.status == "active",
        )
        .first()
    )
    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active budget for the specified category.",
        )
    return budget


@router.put("/{category_name}", response_model=CategoryBudgetResponse)
def modify_category_budget(
    category_name: str,
    budget_data: CategoryBudgetUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Update an existing active category budget.

    Args: \n\n
        category_name (str): category_name of the category.
        budget_data (CategoryBudgetUpdate): Data for updating the budget.
        background_tasks (BackgroundTasks): Background task manager for running asynchronous tasks.
        db (Session): Database session dependency.
        user (User): Authenticated user.

    Returns:
        CategoryBudgetResponse: The updated budget details.
    """
    category = (
        db.query(Category)
        .filter(
            Category.user_id == user.id,
            Category.name == category_name,
        )
        .first()
    )
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category name '{category_name}' does not exist",
        )
    budget = (
        db.query(CategoryBudget)
        .filter(
            CategoryBudget.user_id == user.id,
            CategoryBudget.category_id == category.id,
            CategoryBudget.status == "active",
        )
        .first()
    )
    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active budget found for the specified category.",
        )
    total_general_budget = (
        db.query(GeneralBudget)
        .filter(GeneralBudget.user_id == user.id, GeneralBudget.status == "active")
        .first()
    )
    total_category_budget = (
        db.query(func.sum(CategoryBudget.amount_limit))
        .filter(CategoryBudget.user_id==user.id,
                CategoryBudget.status =="active", 
                CategoryBudget.category_id!=category.id
                )
        .scalar() or 0.0
    )
    if total_general_budget:
        if total_general_budget.amount_limit<(total_category_budget + budget_data.amount_limit):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail=f"Category budget '{category_name}' cannot be greater than general budget {total_general_budget.amount_limit}"
                )

    db.query(Notification).filter(
        Notification.user_id == user.id,
        Notification.message.ilike("%category%"),
        Notification.is_read == False,
    ).update({"is_read": True})
    db.commit()
    for key, value in budget_data.model_dump(exclude_unset=True).items():
        setattr(budget, key, value)

    db.commit()
    db.refresh(budget)
    background_tasks.add_task(check_category_budget, user.id)
    logger.info(
        f"Category budget updated for user '{user.username}' (ID: {user.id})."
    )
    return budget


@router.post("/{category_name}/deactivate", response_model=DetailResponse)
def deactivate_category_budget(
    category_name: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Deactivate an active category budget.

    Args: \n
        category_name (str): category_name of the category.
        db (Session): Database session dependency.
        user (User): Authenticated user.

    Returns:
        DetailResponse: A success message.
    """
    category = (
        db.query(Category)
        .filter(
            Category.user_id == user.id,
            Category.name == category_name,
        )
        .first()
    )
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category name '{category_name}' does not exist",
        )
    budget = (
        db.query(CategoryBudget)
        .filter(
            CategoryBudget.user_id == user.id,
            CategoryBudget.category_id == category.id,
            CategoryBudget.status == "active",
        )
        .first()
    )
    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active budget found for the specified category.",
        )

    db.query(Notification).filter(
        Notification.user_id == user.id,
        Notification.message.ilike("%category%"),
        Notification.is_read == False,
    ).update({"is_read": True})
    db.commit()
    budget.status = "deactivated"
    db.commit()
    logger.info(
        f"Category budget deactivated for user '{user.username}' (ID: {user.id})."
    )
    return {"detail": "Category budget deactivated successfully."}


@router.get("/{category_name}/status", response_model=CategoryBudgetStatus)
def retrieve_category_budget_status(
    category_name: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Retrieve the current status of a category budget.

    Args: \n
        category_name (str): category_name of the category.
        db (Session): Database session dependency.
        user (User): Authenticated user.

    Returns:
        CategoryBudgetStatus: The status of the active budget.
    """
    category = (
        db.query(Category)
        .filter(
            Category.user_id == user.id,
            Category.name == category_name,
        )
        .first()
    )
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category name '{category_name}' does not exist",
        )
    budget = (
        db.query(CategoryBudget)
        .filter(
            CategoryBudget.user_id == user.id,
            CategoryBudget.category_id == category.id,
            CategoryBudget.status == "active",
        )
        .first()
    )
    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active budget for the specified category.",
        )

    expenses = [
        expense.amount
        for expense in budget.owner.expenses
        if budget.start_date <= expense.date <= budget.end_date
    ]
    remaining_amount = budget.amount_limit - sum(expenses)
    status_sent = (
        "within limits"
        if remaining_amount >= budget.amount_limit * 0.2
        else "nearing threshold" if remaining_amount > 0 else "exceeded"
    )
    return {
        "status": status_sent,
        "remaining_amount": remaining_amount,
        "category_name": category_name,
    }


@router.get("/{category_name}/history", response_model=list[CategoryBudgetHistory])
def retrieve_category_budget_history(
    category_name: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Retrieve the history of all budgets for the specified category.

    Args: \n
        category_name (str): ID of the category.
        db (Session): Database session dependency.
        user (User): Authenticated user.

    Returns:
        List[CategoryBudgetHistory]: A list of budget history records.
    """
    category = (
        db.query(Category)
        .filter(
            Category.user_id == user.id,
            Category.name == category_name,
        )
        .first()
    )
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category name does not exist",
        )
    budgets = (
        db.query(CategoryBudget)
        .filter(
            CategoryBudget.user_id == user.id,
            CategoryBudget.category_id == category.id,
        )
        .order_by(CategoryBudget.start_date.desc())
        .all()
    )
    if not budgets:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No budget history found for the specified category.",
        )
    return budgets

@router.get("/", response_model=list[AllCategoryBudgetResponse])
def retrieve_user_category_budgets(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Retrieve all category budgets for a specific user with details like start date, end date, name, amount limit,
    amount used, created_at, and status.

    Args: \n
        user_id (int): ID of the user to retrieve category budgets for.
        db (Session): Database session dependency.
        user (User): Authenticated user (check if the requested user is the same).

    Returns:
        List[CategoryBudgetResponse]: List of category budgets for the specified user.
    """
    category_budgets = (
        db.query(CategoryBudget)
        .join(Category)
        .filter(CategoryBudget.user_id == user.id)
        .all()
    )
    if not category_budgets:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No category budgets found for this user.",
        )

    # Add additional calculations for amount_used if needed (e.g., based on related expenses)
    for budget in category_budgets:
        amount_used = sum(
            expense.amount
            for expense in budget.owner.expenses
            if budget.start_date <= expense.date <= budget.end_date
        )
        budget.amount_used = amount_used

    # Include category name in response
    result = [
        {
            "category_name": budget.categories.name,
            "start_date": budget.start_date,
            "end_date": budget.end_date,
            "amount_limit": budget.amount_limit,
            "amount_used": budget.amount_used,
            "created_at": budget.created_at,
            "status": budget.status,
        }
        for budget in category_budgets
    ]

    return result