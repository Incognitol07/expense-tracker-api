# app/main.py

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
from app.websocket_manager import manager
from app.background_tasks import scheduler, start_scheduler
from app.database import engine, Base
from app.config import settings  # Configuration settings (e.g., environment variables)
from app.routers import (
    auth_router,
    expenses_router,
    categories_router,
    budget_router,
    analytics_router,
    notifications_router,
    groups_router,
    debt_router,
    profile_router,
    category_budgets_router,
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
app.include_router(expenses_router, prefix="/expenses", tags=["Expenses"])
app.include_router(categories_router, prefix="/categories", tags=["Categories"])
app.include_router(category_budgets_router, prefix="/category_budgets", tags=["Category Budget"])
app.include_router(budget_router, prefix="/budget", tags=["Budget"])
app.include_router(analytics_router, prefix="/analytics", tags=["Analytics"])
app.include_router(notifications_router, prefix="/notifications", tags=["Notifications"])
app.include_router(groups_router, prefix="/groups", tags=["Groups"])
app.include_router(debt_router, prefix="/debts", tags=["Debts"])
app.include_router(profile_router, prefix="/profile", tags=["Profile"])

app.debug = settings.DEBUG
# CORS settings
if settings.ENVIRONMENT == "production":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    # Development-specific settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# Root endpoint for health check
@app.get("/")
def read_root():
    return {"message": f"{settings.APP_NAME} is running"}
