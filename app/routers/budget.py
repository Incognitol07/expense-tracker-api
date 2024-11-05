# app/routers/budget.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.schemas.budget import BudgetCreate, BudgetUpdate, BudgetResponse, BudgetStatus, BudgetHistory
from app.models.budget import Budget
from app.database import get_db
from app.routers.auth import get_current_user
from app.models.user import User

router = APIRouter()

@router.post("/budget", response_model=BudgetResponse, status_code=status.HTTP_201_CREATED)
def set_budget(budget_data: BudgetCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    existing_budget = db.query(Budget).filter(Budget.user_id == user.id).first()
    if existing_budget:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Budget already set. Use update instead.")
    
    new_budget = Budget(**budget_data.model_dump(), user_id=user.id)
    db.add(new_budget)
    db.commit()
    db.refresh(new_budget)
    return new_budget

@router.get("/budget", response_model=BudgetResponse)
def get_budget(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    budget = db.query(Budget).filter(Budget.user_id == user.id).first()
    if not budget:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not set.")
    return budget

@router.put("/budget", response_model=BudgetResponse)
def update_budget(budget_data: BudgetUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    budget = db.query(Budget).filter(Budget.user_id == user.id).first()
    if not budget:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not set.")
    
    for key, value in budget_data.model_dump(exclude_unset=True).items():
        setattr(budget, key, value)
    
    db.commit()
    db.refresh(budget)
    return budget

@router.get("/budget/status", response_model=BudgetStatus)
def get_budget_status(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    budget = db.query(Budget).filter(Budget.user_id == user.id).first()
    if not budget:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not set.")
    
    # Calculate remaining budget based on the specified date range
    expenses = [
        expense.amount
        for expense in budget.owner.expenses
        if budget.start_date <= expense.date <= budget.end_date
    ]
    remaining_amount = budget.amount_limit - sum(expenses)
    
    return BudgetStatus(
        remaining_amount=remaining_amount,
        start_date=budget.start_date,
        end_date=budget.end_date
    )

@router.get("/budget/history", response_model=list[BudgetHistory])
def get_budget_history(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    budgets = db.query(Budget).filter(Budget.user_id == user.id).all()
    return budgets

@router.delete("/budget")
def delete_budget(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    budget = db.query(Budget).filter(Budget.user_id == user.id).first()
    if not budget:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not set.")
    
    db.delete(budget)
    db.commit()
    return { "message" : "Deleted successfully" }
