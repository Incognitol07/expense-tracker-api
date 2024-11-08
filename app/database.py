# app/database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os

# Load environment variables from a .env file
load_dotenv()

# Fetch database connection details from environment variables
DB_HOST: str = os.getenv("DB_HOST", "localhost")  # Default to localhost if not set
DB_NAME: str = os.getenv("DB_NAME", "expense_tracker")  # Default database name
DB_USER: str = os.getenv("DB_USER", "postgres")  # Default user is postgres
DB_PASSWORD: str = os.getenv("DB_PASSWORD")  # Database password (should be set in .env)

# Create the database URL using the environment variables
DATABASE_URL = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}'

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
