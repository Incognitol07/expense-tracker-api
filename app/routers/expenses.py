# app/routers/expenses.py

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session
from datetime import date
from app.schemas import (
    ExpenseCreate,
    ExpenseResponse,
    ExpenseUpdate,
    CategoryExpenseResponse,
    DetailResponse,
    GetExpenseResponse
)
from app.models import Expense, Category
from app.routers.auth import get_current_user
from app.database import get_db
from app.models import User
from app.background_tasks import check_budget, check_category_budget
from app.utils import logger
from math import ceil

# Create an instance of APIRouter for expense-related routes
router = APIRouter()


@router.post("/", response_model=ExpenseResponse)
def create_expense(
    background_tasks: BackgroundTasks,
    expense: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Creates a new expense for the authenticated user.

    Args: \n
        expense (ExpenseCreate): The expense data provided by the user.
        db (Session): The database session to interact with the database.
        current_user (User): The currently authenticated user.

    Returns:
        ExpenseResponse: The newly created expense.

    Raises:
        HTTPException: If there is an issue with creating the expense.
    """
    logger.info(
        f"Creating expense for user '{current_user.username}' (ID: {current_user.id}) "
    )
    # Check if the category_id exists in the category table
    category = db.query(Category).filter(Category.name == expense.category_name).first()
    if not category:
        logger.warning(
            f"Failed to create expense: Category '{expense.category_name}' not found for user '{current_user.username}' (ID: {current_user.id}) "
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Please create the provided category first",
        )
    # Proceed with creating the expense if category_id is valid
    new_expense = Expense(
        amount=expense.amount,
        name=expense.name,
        date=expense.date,
        user_id=current_user.id,
        category_id=category.id,
    )
    db.add(new_expense)  # Add the new expense to the session
    db.commit()  # Commit the transaction to the database
    db.refresh(new_expense)  # Refresh to get the latest state of the expense
    logger.info(
        f"Created expense ID: {new_expense.id} successfully for user '{current_user.username}' (ID: {current_user.id}) "
    )
    background_tasks.add_task(check_budget, current_user.id)
    background_tasks.add_task(check_category_budget, current_user.id)
    return new_expense


# Route to get all expenses of the authenticated user
@router.get("/", response_model=GetExpenseResponse)
def get_expenses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = Query(
        10, ge=1, le=100, description="Maximum number of expenses to return."
    ),
    offset: int = Query(0, ge=0, description="Number of expenses to skip."),
    start_date: date = Query(None, description="Start date for filtering expenses."),
    end_date: date = Query(None, description="End date for filtering expenses."),
    name: str = Query(None, name="Filter by expense name."),
    category_name: str = Query(None, name="Filter by category name."),
    keyword: str = Query(None, name="Keyword to search in expenses."),
):
    """
    Retrieves, filters, and searches expenses for the authenticated user.

    Args: \n
        db (Session): The database session.
        current_user (User): The authenticated user.
        limit (int): Maximum number of expenses to return.
        offset (int): Number of expenses to skip.
        start_date (date): Start date for filtering.
        end_date (date): End date for filtering.
        name (str): Filter by name.
        category_name (str): Filter by category name.
        keyword (str): Keyword to search in expenses.

    Returns:
        dict: Dictionary containing the list of expenses and pagination metadata.
    """
    logger.info(
        f"Fetching expenses for user '{current_user.username}' (ID: {current_user.id}) with query parameters."
    )

    # Base query with joins and user-specific filtering
    query = (
        db.query(
            Expense.id,
            Expense.amount,
            Expense.name,
            Expense.date,
            Expense.category_id,
            Category.name.label("category_name"),
        )
        .join(Category, Expense.category_id == Category.id)
        .filter(Expense.user_id == current_user.id)
    )

    # Apply filters if provided
    if start_date:
        query = query.filter(Expense.date >= start_date)
    if end_date:
        query = query.filter(Expense.date <= end_date)
    if name:
        query = query.filter(Expense.name.ilike(f"%{name}%"))
    if category_name:
        query = query.filter(Category.name.ilike(f"%{category_name}%"))
    if keyword:
        query = query.filter(
            Expense.name.ilike(f"%{keyword}%") | Category.name.ilike(f"%{keyword}%")
        )

    # Get the total count before applying pagination
    total_count = query.count()

    # Apply ordering, pagination, and execute query
    expenses = (
        query.order_by(desc(Expense.date), desc(Expense.id))
        .offset(offset)
        .limit(limit)
        .all()
    )

    if not expenses:
        logger.warning(
            f"No expenses found for user '{current_user.username}' (ID: {current_user.id}) with applied filters or search."
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No expenses found."
        )

    # Calculate pagination metadata
    total_pages = ceil(total_count / limit)
    current_page = (offset // limit) + 1
    prev_page = f"/expenses?limit={limit}&offset={max(0, offset - limit)}" if offset > 0 else None
    next_page = f"/expenses?limit={limit}&offset={offset + limit}" if offset + limit < total_count else None

    result = {
        "total_count": total_count,
        "total_pages": total_pages,
        "current_page": current_page,
        "per_page": limit,
        "next_page": next_page,
        "prev_page": prev_page,
        "expenses": [
            {
                "id": expense.id,
                "amount": expense.amount,
                "name": expense.name,
                "date": expense.date,
                "category_id": expense.category_id,
                "category_name": expense.category_name,
            }
            for expense in expenses
        ],
    }
    return result



# Route to get a specific expense by its ID
@router.get("/id/{expense_id}", response_model=ExpenseResponse)
def get_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieves a specific expense by its ID for the authenticated user.

    Args: \n
        expense_id (int): The ID of the expense to retrieve.
        db (Session): The database session to interact with the database.
        current_user (User): The currently authenticated user.

    Returns:
        ExpenseResponse: The expense with the specified ID.

    Raises:
        HTTPException: If the expense is not found or does not belong to the user.
    """
    logger.info(
        f"Retrieving expense ID: {expense_id} for user '{current_user.username}' (ID: {current_user.id}) "
    )
    expense = (
        db.query(Expense)
        .filter(Expense.id == expense_id, Expense.user_id == current_user.id)
        .first()
    )
    if not expense:
        logger.warning(
            f"Failed to retrieve expense ID: {expense_id} for user '{current_user.username}' (ID: {current_user.id}) "
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Expenses not found"
        )
    logger.info(
        f"Retrieved expense ID: {expense.id} successfully for user '{current_user.username}' (ID: {current_user.id}) "
    )
    return expense


# Route to update an existing expense by its ID
@router.put("/{expense_id}", response_model=ExpenseResponse)
def update_expense(
    expense_id: int,
    expense_update: ExpenseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Updates a specific expense by its ID for the authenticated user.

    Args: \n
        expense_id (int): The ID of the expense to update.
        expense_update (ExpenseUpdate): The updated data for the expense.
        db (Session): The database session to interact with the database.
        current_user (User): The currently authenticated user.

    Returns:
        ExpenseResponse: The updated expense.

    Raises:
        HTTPException: If the expense is not found or does not belong to the user.
    """
    logger.info(
        f"Updating expense ID: {expense_id} for user '{current_user.username}' (ID: {current_user.id}) "
    )
    expense = (
        db.query(Expense)
        .filter(Expense.id == expense_id, Expense.user_id == current_user.id)
        .first()
    )
    if not expense:
        logger.warning(
            f"Failed to update expense ID: {expense_id} for user '{current_user.username}' (ID: {current_user.id}) "
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found"
        )

    # Update expense attributes with new values
    for key, value in expense_update.model_dump(exclude_unset=True).items():
        setattr(expense, key, value)

    db.commit()  # Commit changes to the database
    db.refresh(expense)  # Refresh to get the updated state
    logger.info(
        f"Updated expense ID: {expense.id} successfully for user '{current_user.username}' (ID: {current_user.id}) "
    )
    return expense


# Route to delete an expense by its ID
@router.delete("/{expense_id}", response_model=DetailResponse)
def delete_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Deletes a specific expense by its ID for the authenticated user.

    Args: \n
        expense_id (int): The ID of the expense to delete.
        db (Session): The database session to interact with the database.
        current_user (User): The currently authenticated user.

    Returns:
        None: Indicates that the expense has been successfully deleted.

    Raises:
        HTTPException: If the expense is not found or does not belong to the user.
    """
    logger.info(
        f"Deleting expense ID: {expense_id} for user '{current_user.username}' (ID: {current_user.id}) "
    )
    expense = (
        db.query(Expense)
        .filter(Expense.id == expense_id, Expense.user_id == current_user.id)
        .first()
    )
    if not expense:
        logger.warning(
            f"Failed to delete expense ID: {expense_id} for user '{current_user.username}' (ID: {current_user.id}) "
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found"
        )

    logger.info(
        f"Deleted expense ID: {expense.id} successfully for user '{current_user.username}' (ID: {current_user.id}) "
    )
    db.delete(expense)  # Delete the expense from the session
    db.commit()  # Commit the deletion to the database
    return {
        "detail": f"Expense '{expense.name}' of amount {expense.amount} deleted successfully"
    }
