# app/schemas/__init__.py

from .auth import (
    UserCreate,
    UserLogin,
    UserResponse,
    RegisterResponse,
    LoginResponse,
    DetailResponse,
    RefreshResponse,
    RefreshToken
)  # Auth-related schemas
from .admin import AdminCreate, AdminExpenses, AdminUsers, LogResponse
from .expenses import (
    ExpenseCreate,
    ExpenseResponse,
    CategoryExpenseResponse,
    ExpenseUpdate,
)  # Expense-related schemas
from .categories import (
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
)  # Category-related schemas
from .budget import (
    GeneralBudgetCreate,
    GeneralBudgetResponse,
    GeneralBudgetHistory,
    GeneralBudgetStatus,
    GeneralBudgetUpdate,
)
from .category_budget import (
    CategoryBudgetCreate,
    CategoryBudgetHistory,
    CategoryBudgetResponse,
    CategoryBudgetStatus,
    CategoryBudgetUpdate,
    AllCategoryBudgetResponse
)
from .groups import (
    Groups,
    GroupCreate,
    GroupExpenses,
    GroupExpenseCreate,
    GroupMembers,
    GroupMemberCreate,
    GroupMemberStatus,
    ExpenseSplits,
    ExpenseSplitCreate,
    GroupMemberResponse,
    GroupResponse,
    GroupDetailResponse,
)
from .notifications import NotificationResponse
from .debt_notifications import (
    DebtNotifications,
    DebtNotificationCreate,
    DebtNotificationStatus,
    DebtNotificationResponse,
)
from .analytics import (
    ExpenseSummary,
    ExportData,
    CategorySummary,
    MonthlyBreakdown,
    MonthlyTrend,
    WeeklyBreakdown,
    TrendData,
    ExpensesResponse,
    DailyCategoryBreakdown,
    DailyOverview,
    DailyExpense,
    DailyExpensesResponse,
    DateRangeExpenses,
    Adherence,
    GeneralBudgetAdherence,
    ExpenseDetail,
    GeneralBudgetExpenseMapping,
    CategoryBudgetExpenses
)
from .profile import UserProfile, ProfileResponse
