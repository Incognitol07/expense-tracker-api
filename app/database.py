# app/database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

DATABASE_URL = settings.DATABASE_URL

# Create the database engine
engine = create_engine(DATABASE_URL)

# Create a session local for handling database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for declarative models
Base = declarative_base()

# Dependency to get the database session, which can be used in route functions
def get_db():
    db = SessionLocal()  # Create a new database session
    try:
        yield db  # Return the session to the calling function
    finally:
        db.close()  # Ensure the session is closed after usage
