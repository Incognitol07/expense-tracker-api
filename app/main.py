# app/main.py

from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from fastapi import FastAPI
from app.database import get_db, SessionLocal
from app.routers.alerts import check_thresholds  # Import the function to be scheduled
from app.models import User
from app.routers import auth, expenses, categories, budget, analytics, alerts, admin, notifications  # Import routers
from app.database import engine, Base  # Database connection and metadata
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
    # Create a new database session
    db = SessionLocal()
    try:
        # Fetch all users from the database
        users = db.query(User).all()
        for user in users:
            # Schedule the check_thresholds function for each user
            scheduler.add_job(check_thresholds, IntervalTrigger(seconds=5), args=[user.id])
    finally:
        db.close()
    # Start the scheduler
    scheduler.start()


# Initialize database (create tables if they don't exist)
# This is typically handled by migrations, but useful for testing or initial setup
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
    allow_origins=settings.CORS_ORIGINS,   # Use origins from configuration
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    # You can initialize other resources here, like a cache or background tasks

@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()
    print("Shutting down the application...")
    # Cleanup logic can be placed here, such as closing database connections