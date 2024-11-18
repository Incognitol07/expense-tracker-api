# app/models/alert.py

from sqlalchemy import Column, Integer, Float, ForeignKey, String
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime

class Alert(Base):
    """
    Represents an alert notification related to user budget thresholds.

    Attributes:
        id (Integer): Unique identifier for each alert.
        threshold (Float): Defined limit to trigger alert notifications (e.g., budget limit).
        user_id (Integer): Foreign key linking to the user associated with this alert.
    
    Relationships:
        owner (User): Reference to the User who owns the alert, with a back-populated 'alerts' attribute.
    """
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    threshold = Column(Float, nullable=False)
    created_at = Column(String, default=datetime.now().strftime("%d-%m-%Y"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    owner = relationship("User", back_populates="alerts")
