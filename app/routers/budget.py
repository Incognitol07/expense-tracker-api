# app/routers/budget.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi import BackgroundTasks
from sqlalchemy.orm import Session
from app.schemas.budget import BudgetCreate, BudgetUpdate, BudgetResponse, BudgetStatus, BudgetHistory
from app.models import Budget, Notification
from app.database import get_db
from app.routers.auth import get_current_user
from app.models import User
from app.routers.alerts import check_budget

# Create an instance of APIRouter to handle budget-related routes
router = APIRouter()

# Route to set a new budget for the user
@router.post("/", response_model=BudgetResponse, status_code=status.HTTP_201_CREATED)
def set_budget(background_tasks: BackgroundTasks,budget_data: BudgetCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """
    Creates a new budget for the authenticated user.
    
    Args:
        budget_data (BudgetCreate): The budget data to create a new budget.
        db (Session): The database session for interacting with the database.
        user (User): The authenticated user requesting to set the budget.
        
    Raises:
        HTTPException: If a budget is already set for the user, suggesting to use the update route.
        
    Returns:
        BudgetResponse: The newly created budget.
    """
    # Check if the user already has a set budget
    existing_budget = db.query(Budget).filter(
    Budget.user_id == user.id,
    Budget.status == "active",
    Budget.start_date <= budget_data.end_date,
    Budget.end_date >= budget_data.start_date
    ).first()
    if existing_budget:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An active budget already exists in the given date range. Use update instead."
        )
    
    # Create and save the new budget
    new_budget = Budget(**budget_data.model_dump(), user_id=user.id)
    db.add(new_budget)
    db.commit()
    db.refresh(new_budget)
    background_tasks.add_task(check_budget, user.id)
    new_budget.created_at=new_budget.created_at.strftime("%Y-%m-%d %H:%M:%S %p")
    return new_budget

# Route to get the current budget of the user
@router.get("/", response_model=BudgetResponse)
def get_budget(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """
    Retrieves the current budget set by the authenticated user.
    
    Args:
        db (Session): The database session for querying the budget.
        user (User): The authenticated user whose budget is to be fetched.
        
    Raises:
        HTTPException: If no budget is set for the user.
        
    Returns:
        BudgetResponse: The user's current budget.
    """
    budget = db.query(Budget).filter(Budget.user_id == user.id, Budget.status == "active").first()
    if not budget:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not set.")
    budget.created_at=budget.created_at.strftime("%Y-%m-%d %H:%M:%S %p")
    return budget

# Route to update the user's existing budget
@router.put("/", response_model=BudgetResponse)
def update_budget(background_tasks: BackgroundTasks,budget_data: BudgetUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """
    Updates the existing budget of the authenticated user and resets notifications if needed.
    """
    conflicting_budget = db.query(Budget).filter(
    Budget.user_id == user.id,
    Budget.status == "active",
    Budget.id != budget.id,  # Exclude the current budget being updated
    Budget.start_date <= budget_data.end_date,
    Budget.end_date >= budget_data.start_date
    ).first()
    if conflicting_budget:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The updated budget dates conflict with another active budget."
        )

    # Check if the user has an existing budget
    budget = db.query(Budget).filter(Budget.user_id == user.id, Budget.status == "active").first()
    if not budget:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not set.")
    
    # Reset notifications for this budget
    db.query(Notification).filter(
    Notification.user_id == user.id,
    Notification.message.ilike("%budget%"),
    Notification.is_read == False
    ).update({"is_read": True})
    db.commit()
    
    # Update the budget fields with the provided data
    for key, value in budget_data.model_dump(exclude_unset=True).items():
        setattr(budget, key, value)
    
    db.commit()
    db.refresh(budget)
    background_tasks.add_task(check_budget, user.id)
    return budget

# Route to get the current budget status for the user (remaining budget)
@router.get("/status", response_model=BudgetStatus)
def get_budget_status(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """
    Retrieves the current status of the user's budget, including the remaining amount.
    
    Args:
        db (Session): The database session for querying the budget and expenses.
        user (User): The authenticated user whose budget status is to be fetched.
        
    Raises:
        HTTPException: If no budget is set for the user.
        
    Returns:
        BudgetStatus: The remaining budget, start date, and end date.
    """
    # Retrieve the user's current budget
    budget = db.query(Budget).filter(Budget.user_id == user.id, Budget.status=="active").first()
    if not budget:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not set.")
    
    # Calculate the remaining budget based on expenses within the specified date range
    expenses = [
        expense.amount
        for expense in budget.owner.expenses
        if budget.start_date <= expense.date <= budget.end_date
    ]
    remaining_amount = budget.amount_limit - sum(expenses)
    if remaining_amount<0:
        remaining_amount=0
    
    return BudgetStatus(
        remaining_amount=remaining_amount,
        start_date=budget.start_date,
        end_date=budget.end_date
    )

# Route to get the history of all budgets for the user
@router.get("/history", response_model=list[BudgetHistory])
def get_budget_history(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """
    Retrieves the history of all budgets set by the authenticated user.
    
    Args:
        db (Session): The database session for querying all budgets.
        user (User): The authenticated user whose budget history is to be fetched.
        
    Returns:
        list[BudgetHistory]: A list of all previous budgets for the user.
    """
    budgets = db.query(Budget).filter(Budget.user_id == user.id).all()
    for budget in budgets:
        budget.created_at=budget.created_at.strftime("%Y-%m-%d %H:%M:%S %p")
    return budgets

# Route to deactivate the user's current budget
@router.post("/deactivate")
def deactivate_budget(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """
    Deletes the currently set budget for the authenticated user.
    
    Args:
        db (Session): The database session for querying and deleting the budget.
        user (User): The authenticated user requesting to delete their budget.
        
    Raises:
        HTTPException: If no budget is set for the user.
        
    Returns:
        dict: A confirmation message indicating successful deletion.
    """
    # Check if the user has an existing budget to delete
    budget = db.query(Budget).filter(Budget.user_id == user.id, Budget.status == "active").first()
    if not budget:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not set.")
    
    db.query(Notification).filter(
    Notification.user_id == user.id,
    Notification.message.ilike("%budget%"),
    Notification.is_read == False
    ).update({"is_read": True})
    db.commit()

    # Deactivate the budget and commit the changes
    setattr(budget, "status", "deactivated")
    db.commit()
    db.refresh(budget)
    
    return { "message" : f"Deactivated budget of amount {budget.amount_limit} for {budget.start_date} to {budget.end_date} successfully" }

# Route to delete the user's current budget
@router.delete("/{budget_id}")
def delete_budget(budget_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """
    Deletes the currently set budget for the authenticated user.
    
    Args:
        db (Session): The database session for querying and deleting the budget.
        user (User): The authenticated user requesting to delete their budget.
        
    Raises:
        HTTPException: If no budget is set for the user.
        
    Returns:
        dict: A confirmation message indicating successful deletion.
    """
    # Check if the user has an existing budget to delete
    budget = db.query(Budget).filter(Budget.user_id == user.id, Budget.id == budget_id).first()
    if not budget:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found.")
    if budget.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only active budgets can be deleted. Please deactivate or update the budget."
        )

    db.query(Notification).filter(
    Notification.user_id == user.id,
    Notification.message.ilike("%budget%"),
    Notification.is_read == False
    ).update({"is_read": True})
    db.commit()

    # Delete the budget and commit the changes
    db.delete(budget)
    db.commit()
    
    return { "message" : "Deleted successfully" }
