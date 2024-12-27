# app/main.py

from fastapi import (
    FastAPI, 
    WebSocket, 
    WebSocketDisconnect, 
    Request
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import asyncio
from app.websocket_manager import manager
from app.background_tasks import scheduler, start_scheduler
from app.database import engine, Base, SessionLocal
from app.config import settings
from app.models import User, Group, GroupMember, GroupDebt
from app.routers import (
    auth_router,
    google_router,
    expenses_router,
    categories_router,
    budget_router,
    analytics_router,
    notifications_router,
    groups_router,
    group_expenses_router,
    group_debt_router,
    profile_router,
    category_budgets_router,
)
from app.utils import logger
import sentry_sdk

sentry_sdk.init(
    dsn="https://04a0ab15c2e952017cfae042d9b03bd4@o4508454826082304.ingest.us.sentry.io/4508454867435520",
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for tracing.
    traces_sample_rate=1.0,
    _experiments={
        # Set continuous_profiling_auto_start to True
        # to automatically start the profiler on when
        # possible.
        "continuous_profiling_auto_start": True,
    },
)

# Create the FastAPI application
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    print("Starting up the application...")
    start_scheduler()
    asyncio.create_task(manager.keep_alive())
    try:
        yield
    finally:
        print("Shutting down the application...")
        scheduler.shutdown()

app = FastAPI(
    title=settings.APP_NAME,
    description="An API to manage personal finances with expense tracking, budgeting, and analytics features.",
    version="1.0.0",
    debug=settings.DEBUG,  # Enable debug mode if in development
    lifespan=lifespan,
)

# CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
db = SessionLocal()
users = db.query(User).all()
for user in users:
    user_id = (
        db.query(User.id)
        .filter(User.username == user.username, User.email == user.email)
        .first()[0]
    )
    target_user = db.query(User).filter(User.id == user_id).first()

    if not target_user:
        logger.warning(
            f"Attempted deletion of account with ID: {user_id} by user '{user.username}'."
        )

    db.delete(target_user)
    db.commit()
    logger.info(f"User '{user.username}' deleted account (ID: {user_id}).")



favicon_path = 'expense_tracker.png'

@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    return FileResponse(favicon_path)

# Initialize database (create tables if they don't exist)
Base.metadata.create_all(bind=engine)

# WebSocket endpoint for real-time notifications
@app.websocket("/ws/notifications/{user_id}")
async def websocket_notifications(websocket: WebSocket, user_id: int):
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            print(f"Received data from user {user_id}: {data}")
            await websocket.send_text("ping")  # Optionally ping to keep the connection alive
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
        print(f"User {user_id} disconnected")

# Include routers
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(google_router, prefix="/auth", tags=["Authentication"])
app.include_router(expenses_router, prefix="/expenses", tags=["Expenses"])
app.include_router(categories_router, prefix="/categories", tags=["Categories"])
app.include_router(category_budgets_router, prefix="/category_budgets", tags=["Category Budget"])
app.include_router(budget_router, prefix="/budget", tags=["Budget"])
app.include_router(analytics_router, prefix="/analytics", tags=["Analytics"])
app.include_router(notifications_router, prefix="/notifications", tags=["Notifications"])
app.include_router(groups_router, prefix="/groups", tags=["Groups"])
app.include_router(group_expenses_router, prefix="/group-expenses", tags=["Group Expenses"])
app.include_router(group_debt_router, prefix="/group-debts", tags=["Group Debts"])
app.include_router(profile_router, prefix="/profile", tags=["Profile"])

# Middleware to log route endpoints
@app.middleware("http")
async def log_requests(request: Request, call_next):
    endpoint = request.url.path
    method = request.method
    client_ip = request.client.host

    logger.info(f"Request: {method} {endpoint} from {client_ip}")
    
    response = await call_next(request)
    
    logger.info(f"Response: {method} {endpoint} returned {response.status_code}")
    return response



# Root endpoint for health check
@app.get("/")
def read_root():
    return {"message": f"{settings.APP_NAME} is running"}
