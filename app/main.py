# app/main.py

import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from app.websocket_manager import manager
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.database import get_db, SessionLocal
from app.routers.alerts import (
    check_budget,
)  # Import the function to be scheduled
from app.routers.category_budgets import check_category_budget
from app.models import User, GeneralBudget, Notification
from app.routers import (
    auth_router,
    expenses_router,
    categories_router,
    budget_router,
    analytics_router,
    alerts_router,
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
from app.utils import logger
from datetime import datetime, timedelta
from asgiref.sync import async_to_sync



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


# Initialize the scheduler
scheduler = BackgroundScheduler()


def delete_old_notifications():
    """
    Deletes notifications that are older than 30 days.
    """
    db = SessionLocal()
    try:
        # Calculate the threshold date
        threshold_date = datetime.now() - timedelta(days=30)

        # Query and delete notifications older than the threshold
        deleted_count = (
            db.query(Notification)
            .filter(Notification.created_at < threshold_date)
            .delete()
        )
        db.commit()

        # Log the cleanup process
        if deleted_count > 0:
            logger.info(f"Deleted {deleted_count} notifications older than 30 days.")
        else:
            logger.info("No notifications older than 30 days to delete.")
    except Exception as e:
        logger.error(f"Error occurred while deleting old notifications: {e}")
    finally:
        db.close()


def check_and_deactivate_expired_budgets():
    """
    Checks if any active budget has passed its 'end_date' and deactivates it by setting status to 'deactivated'.
    Sends a notification to the user when the budget is deactivated.
    """
    db = SessionLocal()
    try:
        # Query all active budgets that haven't passed their 'end_date'
        budgets = db.query(GeneralBudget).filter(GeneralBudget.status == "active").all()

        for budget in budgets:
            if budget.end_date and budget.end_date < datetime.now().date():
                # If the budget's end date has passed, deactivate it
                budget.status = "deactivated"
                db.commit()  # Commit the changes to the database
                logger.info(
                    f"GeneralBudget (ID: {budget.id}) for user {budget.user_id} has been deactivated."
                )

                # Send a notification to the user informing them that their budget was deactivated
                message = f"Your budget (ID: {budget.id}) has been deactivated because its end date has passed."
                existing_notification = (
                    db.query(Notification)
                    .filter(
                        Notification.user_id == budget.user_id,
                        Notification.message == message,
                        Notification.is_read == False,
                    )
                    .first()
                )

                # Only create a new notification if there are no unread ones with the same message
                if not existing_notification:
                    logger.info(
                        f"Creating notification for user ID: {budget.user_id} with message: '{message}'"
                    )
                    notification = Notification(user_id=budget.user_id, message=message)
                    db.add(notification)
                    db.commit()  # Commit the session to persist the notification in the database

                    # Send the notification to the user's WebSocket
                    manager.send_notification(budget.user_id, message)
                else:
                    logger.info(
                        f"User ID: {budget.user_id} already has an unread notification with the same message."
                    )
                logger.info(
                    f"Deactivation notification sent for user ID: {budget.user_id}"
                )
    finally:
        db.close()


def start_scheduler():
    """
    This function will start the scheduler and run the threshold check job for all users.
    """
    # Add the job to check expired budgets every 5 minutes
    scheduler.add_job(check_and_deactivate_expired_budgets, IntervalTrigger(minutes=5))
    scheduler.add_job(async_to_sync(check_all_thresholds), IntervalTrigger(seconds=5)) # Run every 5 minutes

    # Schedule the cleanup task for old notifications every day
    scheduler.add_job(delete_old_notifications, IntervalTrigger(days=1))

    scheduler.start()


async def check_all_thresholds():
    """
    Checks budget and alert thresholds for all users in a single job.
    """
    db = SessionLocal()
    try:
        users = db.query(User).all()
        for user in users: # Check thresholds for each user
            await check_budget(user.id)  # Check budget for each user
            await check_category_budget(user.id)
    finally:
        db.close()


# Initialize database (create tables if they don't exist)
Base.metadata.create_all(bind=engine)

# Include routers
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(expenses_router, prefix="/expenses", tags=["Expenses"])
app.include_router(categories_router, prefix="/categories", tags=["Categories"])
app.include_router(category_budgets_router, prefix="/category_budgets", tags=["Category Budget"])
app.include_router(budget_router, prefix="/budget", tags=["Budget"])
app.include_router(analytics_router, prefix="/analytics", tags=["Analytics"])
app.include_router(alerts_router, prefix="/alert", tags=["Alerts"])
app.include_router(admin_router, prefix="/admin", tags=["Admin"])
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
