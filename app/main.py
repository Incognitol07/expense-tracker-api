from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.database import get_db, SessionLocal
from app.routers.alerts import check_thresholds  # Import the function to be scheduled
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

# Initialize the scheduler
scheduler = BackgroundScheduler()

def start_scheduler():
    """
    This function will be used to start a scheduled job for checking thresholds.
    It will be executed when the app starts and will run the `check_thresholds`
    job for each user every 5 seconds.
    """
    db = SessionLocal()
    try:
        users = db.query(User).all()  # Get all users
        for user in users:
            # Schedule check_thresholds function for each user
            scheduler.add_job(check_thresholds, IntervalTrigger(seconds=30), args=[user.id])
    finally:
        db.close()
    scheduler.start()  # Start the background scheduler

# Initialize database (create tables if they don't exist)
Base.metadata.create_all(bind=engine)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(expenses.router, prefix="/expenses", tags=["Expenses"])
app.include_router(categories.router, prefix="/categories", tags=["Categories"])
app.include_router(budget.router, prefix="/budget", tags=["Budget"])
app.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
app.include_router(alerts.router, prefix="/alerts", tags=["Alerts"])
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
    print("Starting up the application...")
    # Any other startup logic (e.g., cache initialization) can go here

@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()  # Shutdown the scheduler when the app shuts down
    print("Shutting down the application...")
    # Any cleanup logic (e.g., closing database connections) can go here
