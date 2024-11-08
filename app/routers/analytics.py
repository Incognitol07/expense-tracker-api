# app/routers/analytics.py

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, timedelta
from app.database import get_db
from app.models.expense import Expense
from app.models.budget import Budget
from app.schemas.analytics import ExpenseSummary, MonthlyBreakdown, WeeklyBreakdown, TrendData
from app.routers.auth import get_current_user
from app.models.user import User

# Create an instance of APIRouter to handle analytics-related routes
router = APIRouter()

# Route to get a summary of the user's expenses
@router.get("/analytics/summary", response_model=ExpenseSummary)
def get_expense_summary(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """
    Retrieves a summary of the user's total expenses, including category-wise breakdown and budget adherence.
    
    Args:
        db (Session): The database session for querying expenses and budget data.
        user (User): The authenticated user whose expense summary is to be fetched.
        
    Returns:
        ExpenseSummary: A summary containing total expenses, budget limit, adherence percentage, and category breakdown.
    """
    # Retrieve total expenses for the user
    total_expenses = db.query(func.sum(Expense.amount)).filter(Expense.user_id == user.id).scalar()
    
    # Retrieve expenses grouped by category
    expenses_by_category = [
        {"category_id": category_id, "total": total}
        for category_id, total in db.query(Expense.category_id, func.sum(Expense.amount).label("total"))
            .filter(Expense.user_id == user.id)
            .group_by(Expense.category_id)
            .all()
    ]

    # Retrieve the user's budget and calculate adherence if it exists
    budget = db.query(Budget).filter(Budget.user_id == user.id).first()
    budget_limit = budget.amount_limit if budget else 0
    adherence = (total_expenses / budget_limit) * 100 if budget_limit else None

    return ExpenseSummary(
        total_expenses=total_expenses,
        budget_limit=budget_limit,
        adherence=adherence,
        expenses_by_category=expenses_by_category
    )


# Route to get a breakdown of expenses for the current month
@router.get("/analytics/monthly", response_model=MonthlyBreakdown)
def get_monthly_breakdown(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """
    Retrieves the breakdown of expenses for the current month, grouped by category.
    
    Args:
        db (Session): The database session for querying expenses data.
        user (User): The authenticated user whose monthly breakdown is to be fetched.
        
    Returns:
        MonthlyBreakdown: A breakdown of expenses for the current month.
    """
    current_month = date.today().month
    monthly_expenses = [
        {"category_id": category_id, "total": total}
        for category_id, total in db.query(Expense.category_id, func.sum(Expense.amount).label("total"))
            .filter(Expense.user_id == user.id, func.extract('month', Expense.date) == current_month)
            .group_by(Expense.category_id)
            .all()
    ]
    return MonthlyBreakdown(month=current_month, breakdown=monthly_expenses)


# Route to get a breakdown of expenses for the current week
@router.get("/analytics/weekly", response_model=WeeklyBreakdown)
def get_weekly_breakdown(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """
    Retrieves the breakdown of expenses for the current week, grouped by category.
    
    Args:
        db (Session): The database session for querying expenses data.
        user (User): The authenticated user whose weekly breakdown is to be fetched.
        
    Returns:
        WeeklyBreakdown: A breakdown of expenses for the current week.
    """
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())
    weekly_expenses = [
        {"category_id": category_id, "total": total}
        for category_id, total in db.query(Expense.category_id, func.sum(Expense.amount).label("total"))
            .filter(Expense.user_id == user.id, Expense.date >= start_of_week)
            .group_by(Expense.category_id)
            .all()
    ]
    return WeeklyBreakdown(week_start=start_of_week, breakdown=weekly_expenses)


# Route to get trend data for expenses over the past year (monthly)
@router.get("/analytics/trends", response_model=TrendData)
def get_trend_data(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """
    Retrieves the trend of expenses over the past year, grouped by month.
    
    Args:
        db (Session): The database session for querying expenses data.
        user (User): The authenticated user whose trend data is to be fetched.
        
    Returns:
        TrendData: The trend data for monthly expenses over the past year.
    """
    past_year = date.today() - timedelta(days=365)
    monthly_trends = [
        {"month": int(month), "total": total}
        for month, total in db.query(func.extract('month', Expense.date).label("month"), func.sum(Expense.amount).label("total"))
            .filter(Expense.user_id == user.id, Expense.date >= past_year)
            .group_by(func.extract('month', Expense.date))
            .order_by("month")
            .all()
    ]
    return TrendData(trends=monthly_trends)


# Route to export expense data to CSV or JSON format
@router.get("/analytics/export")
def export_expenses(format: str = "csv", db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """
    Exports the user's expense data to either CSV or JSON format.
    
    Args:
        format (str): The format to export the data in. Defaults to 'csv'.
        db (Session): The database session for querying expenses data.
        user (User): The authenticated user whose expense data is to be exported.
        
    Raises:
        HTTPException: If the specified export format is unsupported.
        
    Returns:
        StreamingResponse or JSONResponse: The exported data in the specified format.
    """
    expenses = db.query(Expense).filter(Expense.user_id == user.id).all()
    data = [
        {"id": expense.id, "amount": expense.amount, "description": expense.description, "date": str(expense.date), "category": expense.category_id}
        for expense in expenses
    ]
    
    # Handle CSV export
    if format == "csv":
        import csv
        from io import StringIO
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
        output.seek(0)
        return StreamingResponse(output, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=expenses.csv"})
    
    # Handle JSON export
    elif format == "json":
        return JSONResponse(content=data)
    
    # Raise error if format is unsupported
    raise HTTPException(status_code=400, detail="Unsupported export format.")
