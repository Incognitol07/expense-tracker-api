from .auth import router as auth_router
from .expenses import router as expenses_router
from .categories import router as categories_router
from .category_budgets import router as category_budgets_router
from .budget import router as budget_router
from .analytics import router as analytics_router
from .alerts import check_budget
from .admin import router as admin_router
from .groups import router as groups_router
from .debt_notifications import router as debt_router
from .notifications import router as notifications_router
from .profile import router as profile_router