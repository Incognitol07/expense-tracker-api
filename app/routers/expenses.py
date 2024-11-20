# app/routers/expenses.py

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from sqlalchemy.orm import Session
from app.schemas.expenses import ExpenseCreate, ExpenseResponse, ExpenseUpdate
from app.models import Expense, Category
from app.routers.auth import get_current_user
from app.database import get_db
from app.models.user import User
from app.routers.alerts import check_thresholds, check_budget
from app.utils import logger

# Create an instance of APIRouter for expense-related routes
router = APIRouter()


@router.post("/", response_model=ExpenseResponse)
def create_expense(
    background_tasks: BackgroundTasks,
    expense: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Creates a new expense for the authenticated user.

    Args:
        expense (ExpenseCreate): The expense data provided by the user.
        db (Session): The database session to interact with the database.
        current_user (User): The currently authenticated user.

    Returns:
        ExpenseResponse: The newly created expense.
    
    Raises:
        HTTPException: If there is an issue with creating the expense.
    """
    logger.info(f"Creating expense for user '{current_user.username}' (ID: {current_user.id}) ")
    # Check if the category_id exists in the category table
    category = db.query(Category).filter(Category.name == expense.category_name).first()
    if not category:
        logger.warning(f"Failed to create expense: Category '{expense.category_name}' not found for user '{current_user.username}' (ID: {current_user.id}) ")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Please create the provided category first"
        )
    category_id = db.query(Category.id).filter(Category.name == expense.category_name).first()[0]
    # Proceed with creating the expense if category_id is valid
    new_expense = Expense(amount=expense.amount, description=expense.description,date=expense.date, user_id=current_user.id, category_id=category_id)
    db.add(new_expense)  # Add the new expense to the session
    db.commit()  # Commit the transaction to the database
    db.refresh(new_expense)  # Refresh to get the latest state of the expense
    logger.info(f"Created expense ID: {new_expense.id} successfully for user '{current_user.username}' (ID: {current_user.id}) ")
    background_tasks.add_task(check_budget, current_user.id)
    background_tasks.add_task(check_thresholds, current_user.id)
    return new_expense


# Route to get all expenses of the authenticated user
@router.get("/", response_model=list[ExpenseResponse])
def get_expenses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    Retrieves all expenses for the authenticated user with pagination.

    Args:
        db (Session): The database session to interact with the database.
        current_user (User): The currently authenticated user.
        limit (int): Maximum number of expenses to return.
        offset (int): Number of expenses to skip.

    Returns:
        list[ExpenseResponse]: List of expenses belonging to the user.
    
    Raises:
        HTTPException: If no expenses are found for the user.
    """
    logger.info(f"Retrieving expenses for user '{current_user.username}' (ID: {current_user.id}) with limit={limit} and offset={offset} ")
    expenses = db.query(Expense).filter(Expense.user_id == current_user.id).offset(offset).limit(limit).all()
    if not expenses:
        logger.warning(f"Failed to retrieve expenses for user '{current_user.username}' (ID: {current_user.id}) ")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No expenses found")
    return expenses

# Route to get a specific expense by its ID
@router.get("/{expense_id}", response_model=ExpenseResponse)
def get_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves a specific expense by its ID for the authenticated user.

    Args:
        expense_id (int): The ID of the expense to retrieve.
        db (Session): The database session to interact with the database.
        current_user (User): The currently authenticated user.

    Returns:
        ExpenseResponse: The expense with the specified ID.
    
    Raises:
        HTTPException: If the expense is not found or does not belong to the user.
    """
    logger.info(f"Retrieving expense ID: {expense_id} for user '{current_user.username}' (ID: {current_user.id}) ")
    expense = db.query(Expense).filter(Expense.id == expense_id, Expense.user_id == current_user.id).first()
    if not expense:
        logger.warning(f"Failed to retrieve expense ID: {expense_id} for user '{current_user.username}' (ID: {current_user.id}) ")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expenses not found")
    logger.info(f"Retrieved expense ID: {expense.id} successfully for user '{current_user.username}' (ID: {current_user.id}) ")
    return expense

# Route to get a expenses by category
@router.get("/category/{category_name}", response_model=list[ExpenseResponse])
def get_expenses_by_category(
    category_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves a specific expense by its ID for the authenticated user.

    Args:
        category_id (int): The ID of the expense to retrieve.
        db (Session): The database session to interact with the database.
        current_user (User): The currently authenticated user.

    Returns:
        ExpenseResponse: The expense with the specified ID.
    
    Raises:
        HTTPException: If the expense is not found or does not belong to the user.
    """
    logger.info(f"Retrieving expenses in category '{category_name}' for user '{current_user.username}' (ID: {current_user.id}) ")
    category = db.query(Category).filter(Category.user_id == current_user.id, Category.name == category_name).first()
    if not category:
        logger.warning(f"Failed to retrieve expenses: Category '{category_name}' not found for user '{current_user.username}' (ID: {current_user.id}) ")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    
    category_id = db.query(Category.id).filter(Category.name == category_name).first()[0]
    
    expenses = db.query(Expense).filter(Expense.category_id == category_id, Expense.user_id == current_user.id).all()
    if not expenses:
        logger.warning(f"Failed to retrieve expenses in category '{category_name}' for user '{current_user.username}' (ID: {current_user.id}) ")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expenses not found")
    logger.info(f"Retrieved {len(expenses)} expenses in category '{category_name}' for user '{current_user.username}' (ID: {current_user.id}) ")
    return expenses

# Route to update an existing expense by its ID
@router.put("/{expense_id}", response_model=ExpenseResponse)
def update_expense(
    expense_id: int,
    expense_update: ExpenseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Updates a specific expense by its ID for the authenticated user.

    Args:
        expense_id (int): The ID of the expense to update.
        expense_update (ExpenseUpdate): The updated data for the expense.
        db (Session): The database session to interact with the database.
        current_user (User): The currently authenticated user.

    Returns:
        ExpenseResponse: The updated expense.
    
    Raises:
        HTTPException: If the expense is not found or does not belong to the user.
    """
    logger.info(f"Updating expense ID: {expense_id} for user '{current_user.username}' (ID: {current_user.id}) ")
    expense = db.query(Expense).filter(Expense.id == expense_id, Expense.user_id == current_user.id).first()
    if not expense:
        logger.warning(f"Failed to update expense ID: {expense_id} for user '{current_user.username}' (ID: {current_user.id}) ")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")
    
    # Update expense attributes with new values
    for key, value in expense_update.model_dump(exclude_unset=True).items():
        setattr(expense, key, value)
    
    db.commit()  # Commit changes to the database
    db.refresh(expense)  # Refresh to get the updated state
    logger.info(f"Updated expense ID: {expense.id} successfully for user '{current_user.username}' (ID: {current_user.id}) ")
    return expense

# Route to delete an expense by its ID
@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Deletes a specific expense by its ID for the authenticated user.

    Args:
        expense_id (int): The ID of the expense to delete.
        db (Session): The database session to interact with the database.
        current_user (User): The currently authenticated user.

    Returns:
        None: Indicates that the expense has been successfully deleted.
    
    Raises:
        HTTPException: If the expense is not found or does not belong to the user.
    """
    logger.info(f"Deleting expense ID: {expense_id} for user '{current_user.username}' (ID: {current_user.id}) ")
    expense = db.query(Expense).filter(Expense.id == expense_id, Expense.user_id == current_user.id).first()
    if not expense:
        logger.warning(f"Failed to delete expense ID: {expense_id} for user '{current_user.username}' (ID: {current_user.id}) ")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")
    
    logger.info(f"Deleted expense ID: {expense.id} successfully for user '{current_user.username}' (ID: {current_user.id}) ")
    db.delete(expense)  # Delete the expense from the session
    db.commit()  # Commit the deletion to the database
    return None
