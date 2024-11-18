# app/config.py

from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # Application settings
    APP_NAME: str = "Expense Tracker API"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")  # Default to 'development'
    DEBUG: bool = ENVIRONMENT == "development"

    # Database configuration
    DB_HOST: str = os.getenv("DB_HOST", "localhost")  # Default to localhost
    DB_NAME: str = os.getenv("DB_NAME", "expense_tracker")  # Default to expense_tracker
    DB_USER: str = os.getenv("DB_USER", "postgres")  # Default to postgres
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "password")  # Default password

    # Uncomment this to use a PostgreSQL database
    # DATABASE_URL: str = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}'

    # Comment this to use a PostgreSQL database
    DATABASE_URL: str = 'sqlite:///expense.db'

    # Admin Master Key
    MASTER_KEY: str = os.getenv("MASTER_KEY", "master_key")

    # JWT and authentication settings
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "myjwtsecretkey")  # Default secret

    # Other security settings
    ALLOWED_HOSTS: list = ["*"]
    CORS_ORIGINS: list = ["http://localhost", "http://localhost:3000", "http://localhost:5173"]  # Add frontend URL if applicable

    class Config:
        env_file = ".env"  # Load environment variables from a .env file if available

# Instantiate settings
settings = Settings()
