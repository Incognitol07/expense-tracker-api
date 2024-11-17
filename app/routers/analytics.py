# app/routers/analytics.py

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, timedelta
from app.database import get_db
from app.models import Expense, Budget, User
from app.schemas import ExpenseSummary, MonthlyBreakdown, WeeklyBreakdown, TrendData, CategorySummary, MonthlyTrend,DailyExpensesResponse, DailyExpense, DailyCategoryBreakdown, DailyOverview, DateRangeExpenses
from app.routers.auth import get_current_user

router = APIRouter()

@router.get("/summary", response_model=ExpenseSummary)
def get_expense_summary(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    total_expenses = db.query(func.sum(Expense.amount)).filter(Expense.user_id == user.id).scalar() or 0.0
    expenses_by_category = [
        CategorySummary(category_id=category_id, total=total)
        for category_id, total in db.query(Expense.category_id, func.sum(Expense.amount).label("total"))
            .filter(Expense.user_id == user.id)
            .group_by(Expense.category_id)
            .all()
    ]
    budget = db.query(Budget).filter(Budget.user_id == user.id).first()
    budget_limit = budget.amount_limit if budget else 0
    adherence = (total_expenses / budget_limit) * 100 if budget_limit else None

    return ExpenseSummary(
        total_expenses=total_expenses,
        budget_limit=budget_limit,
        adherence=adherence,
        expenses_by_category=expenses_by_category
    )

@router.get("/monthly", response_model=MonthlyBreakdown)
def get_monthly_breakdown(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    current_month = date.today().month
    monthly_expenses = [
        CategorySummary(category_id=category_id, total=total)
        for category_id, total in db.query(Expense.category_id, func.sum(Expense.amount).label("total"))
            .filter(Expense.user_id == user.id, func.extract('month', Expense.date) == current_month)
            .group_by(Expense.category_id)
            .all()
    ]
    return MonthlyBreakdown(month=current_month, breakdown=monthly_expenses)

@router.get("/daily", response_model=DailyExpensesResponse)
def get_daily_expenses(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    current_month = date.today().month
    daily_expenses = db.query(
        func.date(Expense.date).label("expense_date"),
        func.sum(Expense.amount).label("total")
    ).filter(
        Expense.user_id == user.id,
        func.extract('month', Expense.date) == current_month
    ).group_by(
        func.date(Expense.date)
    ).order_by("expense_date").all()
    
    # Map query results to the response model
    expenses = [{"date": expense_date, "total": total} for expense_date, total in daily_expenses]
    
    return {"expenses": expenses}


@router.get("/weekly", response_model=WeeklyBreakdown)
def get_weekly_breakdown(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())
    weekly_expenses = [
        CategorySummary(category_id=category_id, total=total)
        for category_id, total in db.query(Expense.category_id, func.sum(Expense.amount).label("total"))
            .filter(Expense.user_id == user.id, Expense.date >= start_of_week)
            .group_by(Expense.category_id)
            .all()
    ]
    return WeeklyBreakdown(week_start=start_of_week, breakdown=weekly_expenses)

@router.get("/trends", response_model=TrendData)
def get_trend_data(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    past_year = date.today() - timedelta(days=365)
    monthly_trends = [
        MonthlyTrend(month=int(month), total=total)
        for month, total in db.query(func.extract('month', Expense.date).label("month"), func.sum(Expense.amount).label("total"))
            .filter(Expense.user_id == user.id, Expense.date >= past_year)
            .group_by(func.extract('month', Expense.date))
            .order_by("month")
            .all()
    ]
    return TrendData(trends=monthly_trends)

@router.get("/export")
def export_expenses(format: str = "csv", db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    expenses = db.query(Expense).filter(Expense.user_id == user.id).all()
    data = [
        {"id": expense.id, "amount": expense.amount, "description": expense.description, "date": str(expense.date), "category_id": expense.category_id}
        for expense in expenses
    ]
    
    if format == "csv":
        import csv
        from io import StringIO
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
        output.seek(0)
        return StreamingResponse(output, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=expenses.csv"})
    
    elif format == "json":
        return JSONResponse(content=data)
    
    raise HTTPException(status_code=400, detail="Unsupported export format.")

@router.get("/budget_adherence", response_model=dict)
def get_budget_adherence(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """
    Retrieve the user's budget adherence for monthly, quarterly, and yearly periods.

    This endpoint calculates total expenses for each period, compares them to the budget limit for that period,
    and returns an adherence percentage.
    """
    today = date.today()
    current_month = today.month
    current_year = today.year

    # --- Monthly Adherence ---
    monthly_expenses = db.query(func.sum(Expense.amount)).filter(
        Expense.user_id == user.id,
        func.extract('month', Expense.date) == current_month,
        func.extract('year', Expense.date) == current_year
    ).scalar() or 0.0
    monthly_budget = db.query(Budget).filter(
        Budget.user_id == user.id,
        func.extract('month', Budget.start_date) <= current_month,
        func.extract('month', Budget.end_date) >= current_month,
        func.extract('year', Budget.start_date) == current_year
    ).first()
    monthly_limit = monthly_budget.amount_limit if monthly_budget else 0
    monthly_adherence = (monthly_expenses / monthly_limit) * 100 if monthly_limit else None

    # --- Quarterly Adherence ---
    current_quarter = (current_month - 1) // 3 + 1
    quarter_start_month = (current_quarter - 1) * 3 + 1
    quarterly_expenses = db.query(func.sum(Expense.amount)).filter(
        Expense.user_id == user.id,
        func.extract('month', Expense.date).between(quarter_start_month, quarter_start_month + 2),
        func.extract('year', Expense.date) == current_year
    ).scalar() or 0.0
    quarterly_budget = db.query(func.sum(Budget.amount_limit)).filter(
        Budget.user_id == user.id,
        func.extract('month', Budget.start_date).between(quarter_start_month, quarter_start_month + 2),
        func.extract('year', Budget.start_date) == current_year
    ).scalar() or 0.0
    quarterly_adherence = (quarterly_expenses / quarterly_budget) * 100 if quarterly_budget else None

    # --- Yearly Adherence ---
    yearly_expenses = db.query(func.sum(Expense.amount)).filter(
        Expense.user_id == user.id,
        func.extract('year', Expense.date) == current_year
    ).scalar() or 0.0
    yearly_budget = db.query(func.sum(Budget.amount_limit)).filter(
        Budget.user_id == user.id,
        func.extract('year', Budget.start_date) == current_year
    ).scalar() or 0.0
    yearly_adherence = (yearly_expenses / yearly_budget) * 100 if yearly_budget else None

    # Return results as a dictionary
    return {
        "monthly_adherence": ExpenseSummary(
            total_expenses=monthly_expenses,
            budget_limit=monthly_limit,
            adherence=monthly_adherence,
            expenses_by_category=[]
        ),
        "quarterly_adherence": ExpenseSummary(
            total_expenses=quarterly_expenses,
            budget_limit=quarterly_budget,
            adherence=quarterly_adherence,
            expenses_by_category=[]
        ),
        "yearly_adherence": ExpenseSummary(
            total_expenses=yearly_expenses,
            budget_limit=yearly_budget,
            adherence=yearly_adherence,
            expenses_by_category=[]
        )
    }

@router.get("/date_range", response_model=ExpenseSummary)
def get_expense_summary_for_range(
    start_date: date, 
    end_date: date, 
    db: Session = Depends(get_db), 
    user: User = Depends(get_current_user)
):
    """
    Retrieve expense summary and budget adherence for a specific date range.
    The user provides start and end dates for the analysis period.
    """
    
    # Calculate total expenses for the date range
    total_expenses = db.query(func.sum(Expense.amount)).filter(
        Expense.user_id == user.id,
        Expense.date >= start_date,
        Expense.date <= end_date
    ).scalar() or 0.0
    
    # Expenses by category for the date range
    expenses_by_category = [
        CategorySummary(category_id=category_id, total=total)
        for category_id, total in db.query(Expense.category_id, func.sum(Expense.amount).label("total"))
            .filter(Expense.user_id == user.id, Expense.date >= start_date, Expense.date <= end_date)
            .group_by(Expense.category_id)
            .all()
    ]
    
    # Fetch user's budget for the date range
    budget = db.query(Budget).filter(
        Budget.user_id == user.id,
        Budget.start_date <= end_date,
        Budget.end_date >= start_date
    ).first()
    
    budget_limit = budget.amount_limit if budget else 0
    adherence = (total_expenses / budget_limit) * 100 if budget_limit else None
    
    return ExpenseSummary(
        total_expenses=total_expenses,
        budget_limit=budget_limit,
        adherence=adherence,
        expenses_by_category=expenses_by_category
    )

@router.get("/daily/categorized", response_model=list[DailyCategoryBreakdown])
def get_daily_expenses_by_category(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    current_month = date.today().month
    categorized_expenses = db.query(
        func.date(Expense.date).label("expense_date"),
        Expense.category_id,
        func.sum(Expense.amount).label("total")
    ).filter(
        Expense.user_id == user.id,
        func.extract('month', Expense.date) == current_month
    ).group_by(
        func.date(Expense.date),
        Expense.category_id
    ).order_by("expense_date").all()
    
    # Organize data into a list of DailyCategoryBreakdown objects
    daily_data = {}
    for expense_date, category_id, total in categorized_expenses:
        if expense_date not in daily_data:
            daily_data[expense_date] = []
        daily_data[expense_date].append(CategorySummary(category_id=category_id, total=total))
    
    response = [
        DailyCategoryBreakdown(date=expense_date, categories=categories)
        for expense_date, categories in daily_data.items()
    ]
    
    return response


@router.get("/daily/overview", response_model=DailyOverview)
def get_daily_expenses_overview(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    current_month = date.today().month
    current_year = date.today().year

    # Total monthly expenses
    total_monthly_expenses = db.query(
        func.sum(Expense.amount)
    ).filter(
        Expense.user_id == user.id,
        func.extract('month', Expense.date) == current_month,
        func.extract('year', Expense.date) == current_year
    ).scalar() or 0.0

    # Daily expenses grouped by date
    daily_expenses = db.query(
        func.date(Expense.date).label("expense_date"),
        func.sum(Expense.amount).label("total")
    ).filter(
        Expense.user_id == user.id,
        func.extract('month', Expense.date) == current_month
    ).group_by(
        func.date(Expense.date)
    ).order_by("expense_date").all()

    # Format response
    daily_data = {str(expense_date): total for expense_date, total in daily_expenses}
    average_daily_expense = total_monthly_expenses / len(daily_data) if daily_data else 0.0

    return {
        "total_monthly_expenses": total_monthly_expenses,
        "average_daily_expense": average_daily_expense,
        "daily_expenses": daily_data,
    }


@router.get("/daily/range", response_model=list[DateRangeExpenses])
def get_expenses_for_date_range(
    start_date: date, 
    end_date: date, 
    db: Session = Depends(get_db), 
    user: User = Depends(get_current_user)
):
    daily_expenses = db.query(
        func.date(Expense.date).label("expense_date"),
        func.sum(Expense.amount).label("total")
    ).filter(
        Expense.user_id == user.id,
        Expense.date >= start_date,
        Expense.date <= end_date
    ).group_by(
        func.date(Expense.date)
    ).order_by("expense_date").all()
    
    # Return as a list of DateRangeExpenses objects
    return [DateRangeExpenses(date=expense_date, total=total) for expense_date, total in daily_expenses]