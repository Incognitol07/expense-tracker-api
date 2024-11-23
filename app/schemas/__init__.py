# app/schemas/__init__.py

from .auth import UserCreate, UserLogin, UserResponse, RegisterResponse, LoginResponse, MessageResponse  # Auth-related schemas
from .admin import AdminCreate, AdminExpenses, AdminUsers, LogResponse
from .expenses import ExpenseCreate, ExpenseResponse, CategoryExpenseResponse, ExpenseUpdate  # Expense-related schemas
from .categories import CategoryCreate, CategoryResponse, CategoryUpdate  # Category-related schemas
from .budget import BudgetCreate, BudgetResponse, BudgetHistory, BudgetStatus, BudgetUpdate
from .alerts import AlertResponse, AlertUpdate, AlertCreate
from .groups import Groups, GroupCreate, GroupExpenses, GroupExpenseCreate, GroupMembers, GroupMemberCreate, GroupMemberStatus, ExpenseSplits, ExpenseSplitCreate, GroupMemberResponse
from .notifications import NotificationResponse
from .debt_notifications import DebtNotifications, DebtNotificationCreate, DebtNotificationStatus, DebtNotificationResponse
from .analytics import ExpenseSummary, ExportData, CategorySummary, MonthlyBreakdown, MonthlyTrend, WeeklyBreakdown, TrendData, ExpensesResponse, DailyCategoryBreakdown, DailyOverview,DailyExpense, DailyExpensesResponse, DateRangeExpenses, Adherence, BudgetAdherence
from .profile import UserProfile, ProfileResponse