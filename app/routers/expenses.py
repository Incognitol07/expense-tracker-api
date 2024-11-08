# app/routers/expenses.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.schemas.expenses import ExpenseCreate, ExpenseResponse, ExpenseUpdate
from app.models.expense import Expense
from app.routers.auth import get_current_user
from app.database import get_db
from app.models.user import User

# Create an instance of APIRouter for expense-related routes
router = APIRouter()

# Route to create a new expense
@router.post("/expenses", response_model=ExpenseResponse)
def create_expense(
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
    new_expense = Expense(**expense.model_dump(), user_id=current_user.id)
    db.add(new_expense)  # Add the new expense to the session
    db.commit()  # Commit the transaction to the database
    db.refresh(new_expense)  # Refresh to get the latest state of the expense
    return new_expense

# Route to get all expenses of the authenticated user
@router.get("/expenses", response_model=list[ExpenseResponse])
def get_expenses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves all expenses for the authenticated user.

    Args:
        db (Session): The database session to interact with the database.
        current_user (User): The currently authenticated user.

    Returns:
        list[ExpenseResponse]: List of expenses belonging to the user.
    
    Raises:
        HTTPException: If no expenses are found for the user.
    """
    expenses = db.query(Expense).filter(Expense.user_id == current_user.id).all()
    return expenses

# Route to get a specific expense by its ID
@router.get("/expenses/{expense_id}", response_model=ExpenseResponse)
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
    expense = db.query(Expense).filter(Expense.id == expense_id, Expense.user_id == current_user.id).first()
    if not expense:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")
    return expense

# Route to update an existing expense by its ID
@router.put("/expenses/{expense_id}", response_model=ExpenseResponse)
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
    expense = db.query(Expense).filter(Expense.id == expense_id, Expense.user_id == current_user.id).first()
    if not expense:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")
    
    # Update expense attributes with new values
    for key, value in expense_update.dict(exclude_unset=True).items():
        setattr(expense, key, value)
    
    db.commit()  # Commit changes to the database
    db.refresh(expense)  # Refresh to get the updated state
    return expense

# Route to delete an expense by its ID
@router.delete("/expenses/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
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
    expense = db.query(Expense).filter(Expense.id == expense_id, Expense.user_id == current_user.id).first()
    if not expense:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")
    
    db.delete(expense)  # Delete the expense from the session
    db.commit()  # Commit the deletion to the database
    return None
