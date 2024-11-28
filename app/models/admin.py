# app/models/admin.py

from sqlalchemy import Column, Integer, String, DateTime
from app.database import Base
from datetime import datetime

class Admin(Base):
    """
    Represents an admin user in the system.

    Attributes:
        id (Integer): Unique identifier for each admin.
        username (String): Admin's unique username.
        email (String): Admin's unique email address.
        hashed_password (String): Admin's hashed password for secure authentication.
    """
    __tablename__ = "admins"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now())
