# app/routers/analytics.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, timedelta
from app.database import get_db
from app.models import Expense, Budget, User, Category
from app.schemas import ExpenseSummary, MonthlyBreakdown, WeeklyBreakdown, TrendData, CategorySummary, MonthlyTrend,DailyExpensesResponse, DailyCategoryBreakdown, DailyOverview, DateRangeExpenses, Adherence, BudgetAdherence
from app.routers.auth import get_current_user
from app.utils import logger

router = APIRouter()

@router.get("/summary", response_model=ExpenseSummary)
def get_expense_summary(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    logger.info(f"Fetching analytics summary for user '{user.username}' (ID: {user.id}).")
    total_expenses = db.query(func.sum(Expense.amount)).filter(Expense.user_id == user.id).scalar() or 0.0
    expenses_by_category = [
        CategorySummary(category_id=category_id, total=total, category_name="name")
        for category_id, total in db.query(Expense.category_id, func.sum(Expense.amount).label("total"))
            .filter(Expense.user_id == user.id)
            .group_by(Expense.category_id)
            .all()
    ]
    for expenses in expenses_by_category:
        expenses.category_name = db.query(Category.name).filter(Category.user_id == user.id, Category.id == expenses.category_id).first()[0]

    budget = db.query(Budget).filter(Budget.user_id == user.id, Budget.status == "active").first()
    budget_limit = budget.amount_limit if budget else 0
    adherence = (total_expenses / budget_limit) * 100 if budget_limit else None

    logger.info(f"Analytics summary retrieved successfully for user '{user.username}' (ID: {user.id}).")
    return ExpenseSummary(
        total_expenses=total_expenses,
        budget_limit=budget_limit,
        adherence=adherence,
        expenses_by_category=expenses_by_category
    )

@router.get("/monthly", response_model=MonthlyBreakdown)
def get_monthly_breakdown(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    logger.info(f"Fetching monthly expense breakdown for user '{user.username}' (ID: {user.id}).")
    current_month = date.today().month
    monthly_expenses = [
        CategorySummary(category_id=category_id, total=total, category_name="name")
        for category_id, total in db.query(Expense.category_id, func.sum(Expense.amount).label("total"))
            .filter(Expense.user_id == user.id, func.extract('month', Expense.date) == current_month)
            .group_by(Expense.category_id)
            .all()
    ]
    for expenses in monthly_expenses:
        expenses.category_name = db.query(Category.name).filter(Category.user_id == user.id, Category.id == expenses.category_id).first()[0]
    logger.info(f"Monthly expense breakdown successfully generated for user '{user.username}' (ID: {user.id}).")
    return MonthlyBreakdown(month=current_month, breakdown=monthly_expenses)

@router.get("/daily", response_model=DailyExpensesResponse)
def get_daily_expenses(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    logger.info(f"Fetching daily expenses for user '{user.username}' (ID: {user.id}) for the current month.")
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
    
    logger.info(f"Daily expenses successfully generated for user '{user.username}' (ID: {user.id}).")
    return {"expenses": expenses}


@router.get("/weekly", response_model=WeeklyBreakdown)
def get_weekly_breakdown(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    logger.info(f"Fetching weekly expense breakdown for user '{user.username}' (ID: {user.id}).")
    # Weekly calculation
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())
    weekly_expenses = [
        CategorySummary(category_id=category_id, total=total, category_name="name")
        for category_id, total in db.query(Expense.category_id, func.sum(Expense.amount).label("total"))
            .filter(Expense.user_id == user.id, Expense.date >= start_of_week)
            .group_by(Expense.category_id)
            .all()
    ]
    for expenses in weekly_expenses:
        expenses.category_name = db.query(Category.name).filter(Category.user_id == user.id, Category.id == expenses.category_id).first()[0]
    logger.info(f"Weekly expense breakdown successfully generated for user '{user.username}' (ID: {user.id}).")
    return WeeklyBreakdown(week_start=start_of_week, breakdown=weekly_expenses)

@router.get("/trends", response_model=TrendData)
def get_trend_data(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    logger.info(f"Fetching annual trend data for user '{user.username}' (ID: {user.id}).")
    # Trend data calculation
    past_year = date.today() - timedelta(days=365)
    monthly_trends = [
        MonthlyTrend(month=int(month), total=total)
        for month, total in db.query(func.extract('month', Expense.date).label("month"), func.sum(Expense.amount).label("total"))
            .filter(Expense.user_id == user.id, Expense.date >= past_year)
            .group_by(func.extract('month', Expense.date))
            .order_by("month")
            .all()
    ]
    logger.info(f"Annual trend data successfully retrieved for user '{user.username}' (ID: {user.id}).")
    return TrendData(trends=monthly_trends)

@router.get("/export")
def export_expenses(format: str = "csv", db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    logger.info(f"Starting expense export in '{format.upper()}' format for user '{user.username}' (ID: {user.id}).")
    expenses = db.query(Expense).filter(Expense.user_id == user.id).all()
    data = [
        {"id": expense.id, "amount": expense.amount, "description": expense.description, "date": str(expense.date), "category_name": db.query(Category.name).filter(Category.id == expense.category_id, Category.user_id == expense.user_id).first()[0],"category_id": expense.category_id}
        for expense in expenses
    ]
    if not data:
        logger.warning(f"No data to be exported for user '{user.username}' (ID: {user.id})")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No data to export.")

    # Format validation
    if format not in ["csv", "json"]:
        logger.warning(f"Invalid format requested: {format} for user '{user.username}' (ID: {user.id})")
        raise HTTPException(status_code=400, detail="Unsupported export format.")
    
    if format == "csv":
        import csv
        from io import StringIO
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
        output.seek(0)
        logger.info(f"Expenses successfully exported in '{format.upper()}' format for user '{user.username}' (ID: {user.id}).")
        return StreamingResponse(output, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=expenses.csv"})
    
    elif format == "json":
        logger.info(f"Expenses successfully exported in '{format.upper()}' format for user '{user.username}' (ID: {user.id}).")
        return JSONResponse(content=data)
    
    logger.warning(f"Failed to export expenses for user '{user.username}' (ID: {user.id})")

@router.get("/budget_adherence", response_model=BudgetAdherence)
def get_budget_adherence(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """
    Retrieve the user's budget adherence for monthly, quarterly, and yearly periods.

    This endpoint calculates total expenses for each period, compares them to the budget limit for that period,
    and returns an adherence percentage.
    """
    logger.info(f"Fetching budget adherence data for user '{user.username}' (ID: {user.id}).")
    today = date.today()
    current_month = today.month
    current_year = today.year
    
    # --- Monthly Adherence ---
    monthly_expenses = db.query(func.sum(Expense.amount)).filter(
        Expense.user_id == user.id,
        func.extract('month', Expense.date) == current_month,
        func.extract('year', Expense.date) == current_year
    ).scalar() or 0.0
    monthly_limit = db.query(func.sum(Budget.amount_limit)).filter(
        Budget.user_id == user.id,
        func.extract('month', Budget.start_date) <= current_month,
        func.extract('month', Budget.end_date) >= current_month,
        func.extract('year', Budget.start_date) == current_year,
        Budget.status=="active"
    ).scalar() or 0.0
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
        func.extract('year', Budget.start_date) == current_year,
        Budget.status=="active"
    ).scalar() or 0.0
    quarterly_adherence = (quarterly_expenses / quarterly_budget) * 100 if quarterly_budget else None

    # --- Yearly Adherence ---
    yearly_expenses = db.query(func.sum(Expense.amount)).filter(
        Expense.user_id == user.id,
        func.extract('year', Expense.date) == current_year
    ).scalar() or 0.0
    yearly_budget = db.query(func.sum(Budget.amount_limit)).filter(
        Budget.user_id == user.id,
        func.extract('year', Budget.start_date) == current_year,
        Budget.status=="active"
    ).scalar() or 0.0
    yearly_adherence = (yearly_expenses / yearly_budget) * 100 if yearly_budget else None

    logger.info(f"Budget adherence data successfully retrieved for user '{user.username}' (ID: {user.id}).")
    # Return results as a dictionary
    return {
        "monthly_adherence": Adherence(
            total_expenses=monthly_expenses,
            budget_limit=monthly_limit,
            adherence=monthly_adherence
        ),
        "quarterly_adherence": Adherence(
            total_expenses=quarterly_expenses,
            budget_limit=quarterly_budget,
            adherence=quarterly_adherence
        ),
        "yearly_adherence": Adherence(
            total_expenses=yearly_expenses,
            budget_limit=yearly_budget,
            adherence=yearly_adherence
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
    
    logger.info(f"Fetching expense summary for user '{user.username}' (ID: {user.id}) between {start_date} and {end_date}.")
    # Calculate total expenses for the date range
    total_expenses = db.query(func.sum(Expense.amount)).filter(
        Expense.user_id == user.id,
        Expense.date >= start_date,
        Expense.date <= end_date
    ).scalar() or 0.0
    
    # Expenses by category for the date range
    expenses_by_category = [
        CategorySummary(category_id=category_id, total=total, category_name="name")
        for category_id, total in db.query(Expense.category_id, func.sum(Expense.amount).label("total"))
            .filter(Expense.user_id == user.id, Expense.date >= start_date, Expense.date <= end_date)
            .group_by(Expense.category_id)
            .all()
    ]

    for expenses in expenses_by_category:
        expenses.category_name = db.query(Category.name).filter(Category.user_id == user.id, Category.id == expenses.category_id).first()[0]

    overlapping_budgets = db.query(Budget).filter(
    Budget.user_id == user.id,
    Budget.status == "active",
    Budget.end_date >= start_date,
    Budget.start_date <= end_date
    ).count()
    if overlapping_budgets > 1:
        raise HTTPException(status_code=400, detail="Overlapping active budgets are not allowed.")
    # Fetch user's budget for the date range
    budget = db.query(Budget).filter(
    Budget.user_id == user.id,
    Budget.start_date <= end_date,
    Budget.end_date >= start_date,
    Budget.status == "active"
    ).first()

    
    budget_limit = budget.amount_limit if budget else 0
    adherence = (total_expenses / budget_limit) * 100 if budget_limit else None
    if not budget_limit:
        logger.warning(f"Budget limit is zero or unavailable for user '{user.username}' (ID: {user.id}). Adherence cannot be calculated.")
        adherence = 0

    
    logger.info(f"Expense summary for the range {start_date} to {end_date} successfully retrieved for user '{user.username}' (ID: {user.id}).")
    return ExpenseSummary(
        total_expenses=total_expenses,
        budget_limit=budget_limit,
        adherence=adherence,
        expenses_by_category=expenses_by_category
    )

@router.get("/daily/categorized", response_model=list[DailyCategoryBreakdown])
def get_daily_expenses_by_category(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    logger.info(f"Fetching daily categorized expenses for user '{user.username}' (ID: {user.id}).")
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
        category_name = db.query(Category.name).filter(Category.user_id == user.id, Category.id == category_id).first()[0]
        daily_data[expense_date].append(CategorySummary(category_id=category_id, total=total, category_name=category_name))
    
    response = [
        DailyCategoryBreakdown(date=expense_date, categories=categories)
        for expense_date, categories in daily_data.items()
    ]
    
    logger.info(f"Daily categorized expenses successfully retrieved for user '{user.username}' (ID: {user.id}).")
    return response


@router.get("/daily/overview", response_model=DailyOverview)
def get_daily_expenses_overview(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    logger.info(f"Fetching daily expenses overview for user '{user.username}' (ID: {user.id}).")
    # Overview calculation
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
    average_daily_expense = (total_monthly_expenses / len(daily_data)).__round__(2) if daily_data else 0.0

    logger.info(f"Daily expenses overview successfully generated for user '{user.username}' (ID: {user.id}).")
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
    logger.info(f"Fetching daily expenses for user '{user.username}' (ID: {user.id}) between {start_date} and {end_date}.")
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
    logger.info(f"Daily expenses for the range {start_date} to {end_date} successfully retrieved for user '{user.username}' (ID: {user.id}).")
    return [DateRangeExpenses(date=expense_date, total=total) for expense_date, total in daily_expenses]