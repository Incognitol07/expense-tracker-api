# app/main.py

import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from app.websocket_manager import manager
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.database import get_db, SessionLocal
from app.routers.alerts import check_thresholds, check_budget  # Import the function to be scheduled
from app.models import User
from app.routers import auth, expenses, categories, budget, analytics, alerts, admin, notifications
from app.database import engine, Base
from app.config import settings  # Configuration settings (e.g., environment variables)
from fastapi.middleware.cors import CORSMiddleware

# Create the FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="An API to manage personal finances with expense tracking, budgeting, and analytics features.",
    version="1.0.0",
    debug=settings.DEBUG  # Enable debug mode if in development
)

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



# Initialize the scheduler
scheduler = BackgroundScheduler()


def start_scheduler():
    """
    This function will start the scheduler and run the threshold check job for all users.
    """
    scheduler.add_job(check_all_thresholds, IntervalTrigger(minutes=5))  # Run every 5 minutes
    scheduler.start()

def check_all_thresholds():
    """
    Checks budget and alert thresholds for all users in a single job.
    """
    db = SessionLocal()
    try:
        users = db.query(User).all()
        for user in users:
            check_thresholds(user.id)  # Check thresholds for each user
            check_budget(user.id)      # Check budget for each user
    finally:
        db.close()


# Initialize database (create tables if they don't exist)
Base.metadata.create_all(bind=engine)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(expenses.router, prefix="/expenses", tags=["Expenses"])
app.include_router(categories.router, prefix="/categories", tags=["Categories"])
app.include_router(budget.router, prefix="/budget", tags=["Budget"])
app.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
app.include_router(alerts.router, prefix="/alert", tags=["Alerts"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])
app.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])

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
