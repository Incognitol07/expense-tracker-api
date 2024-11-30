# app/routers/category_budget.py

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from app.schemas import (
    CategoryBudgetCreate,
    CategoryBudgetUpdate,
    CategoryBudgetResponse,
    CategoryBudgetStatus,
    CategoryBudgetHistory,
    DetailResponse,
)
from app.models import CategoryBudget, Category, Notification, Expense
from app.database import get_db, SessionLocal
from app.routers.auth import get_current_user
from app.models import User
from app.websocket_manager import manager
from app.utils import logger

router = APIRouter()


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
                message = (
                    f"You've exceeded your budget for category {budget.category_id} "
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
                    notification = Notification(user_id=user_id, message=message)
                    db.add(notification)
                    db.commit()
                    db.refresh(notification)
                    logger.info(f"Notification created: {notification.message}")
                    manager.send_notification(user_id, message)
        logger.info(f"Category budget check completed for user ID: {user_id}")
    except Exception as e:
        logger.error(f"Error in category budget check: {e}")
    finally:
        db.close()



@router.post(
    "/", response_model=CategoryBudgetResponse, status_code=status.HTTP_201_CREATED
)
def create_category_budget(
    background_tasks: BackgroundTasks,
    budget_data: CategoryBudgetCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Create a new category budget for the authenticated user.

    Args: \n
        budget_data (CategoryBudgetCreate): Data for creating the budget.
        db (Session): Database session dependency.
        user (User): Authenticated user.

    Returns:
        CategoryBudgetResponse: The newly created budget details.
    """
    category = (
        db.query(Category)
        .filter(
            Category.user_id == user.id,
            Category.name == budget_data.name,
        )
        .first()
    )
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category name {budget_data.name} does not exist",
        )
    existing_budget = (
        db.query(CategoryBudget)
        .filter(
            CategoryBudget.user_id == user.id,
            CategoryBudget.category_id == category.id,
            CategoryBudget.status == "active",
            CategoryBudget.start_date <= budget_data.end_date,
            CategoryBudget.end_date >= budget_data.start_date,
        )
        .first()
    )
    if existing_budget:
        logger.warning(
            f"Duplicate category budget creation attempt by user '{user.username}'."
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An active budget for this category already exists in the given date range.",
        )

    new_budget = CategoryBudget(
        category_id=category.id, 
        amount_limit=budget_data.amount_limit, 
        start_date=budget_data.start_date, 
        end_date=budget_data.end_date,
        user_id=user.id)
    db.add(new_budget)
    db.commit()
    db.refresh(new_budget)
    background_tasks.add_task(check_category_budget, user.id)
    logger.info(
        f"Category budget created for user '{user.username}' (ID: {user.id})."
    )
    return new_budget


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
