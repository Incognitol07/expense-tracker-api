# app/main.py

import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from app.websocket_manager import manager
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.database import get_db, SessionLocal
from app.background_tasks import (
    scheduler,
    start_scheduler
    )
from app.models import User, GeneralBudget, Notification
from app.routers import (
    auth_router,
    expenses_router,
    categories_router,
    budget_router,
    analytics_router,
    admin_router,
    notifications_router,
    groups_router,
    debt_router,
    profile_router,
    category_budgets_router
)
from app.database import engine, Base
from app.config import settings  # Configuration settings (e.g., environment variables)
from fastapi.middleware.cors import CORSMiddleware




# Create the FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="An API to manage personal finances with expense tracking, budgeting, and analytics features.",
    version="1.0.0",
    debug=settings.DEBUG,  # Enable debug mode if in development
)


# WebSocket endpoint for real-time notifications
@app.websocket("/ws/notifications/{user_id}")
async def websocket_notifications(websocket: WebSocket, user_id: int):
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            print(f"Received data from user {user_id}: {data}")
            await websocket.send_text(
                "ping"
            )  # Optionally ping to keep the connection alive
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
        print(f"User {user_id} disconnected")


# Initialize database (create tables if they don't exist)
Base.metadata.create_all(bind=engine)

# Include routers
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(expenses_router, prefix="/expenses", tags=["Expenses"])
app.include_router(categories_router, prefix="/categories", tags=["Categories"])
app.include_router(category_budgets_router, prefix="/category_budgets", tags=["Category Budget"])
app.include_router(budget_router, prefix="/budget", tags=["Budget"])
app.include_router(analytics_router, prefix="/analytics", tags=["Analytics"])
# app.include_router(admin_router, prefix="/admin", tags=["Admin"])
app.include_router(notifications_router, prefix="/notifications", tags=["Notifications"])
app.include_router(groups_router, prefix="/groups", tags=["Groups"])
app.include_router(debt_router, prefix="/debts", tags=["Debts"])
app.include_router(profile_router, prefix="/profile", tags=["Profile"])

# CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,  # Allow origins from config
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all HTTP headers
)


# Root endpoint for health check
@app.get("/")
def read_root():
    return {"message": f"{settings.APP_NAME} is running"}


# Optional startup and shutdown event handlers for database or other resources
@app.on_event("startup")
async def startup_event():
    start_scheduler()
    asyncio.create_task(manager.keep_alive())
    print("Starting up the application...")
    # Any other startup logic (e.g., cache initialization) can go here


@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()  # Shutdown the scheduler when the app shuts down
    print("Shutting down the application...")
    # Any cleanup logic (e.g., closing database connections) can go here
