from fastapi import FastAPI
from app.routers import auth, expenses, categories, budget, analytics  # Import routers
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

# Initialize database (create tables if they don't exist)
# This is typically handled by migrations, but useful for testing or initial setup
Base.metadata.create_all(bind=engine)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(expenses.router, prefix="/expenses", tags=["Expenses"])
app.include_router(categories.router, prefix="/categories", tags=["Categories"])
app.include_router(budget.router, prefix="/budget", tags=["Budget"])
app.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])

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
    print("Starting up the application...")
    # You can initialize other resources here, like a cache or background tasks

@app.on_event("shutdown")
async def shutdown_event():
    print("Shutting down the application...")
    # Cleanup logic can be placed here, such as closing database connections
