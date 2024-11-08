from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    message = Column(String, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(String, default=datetime.now().strftime("%d-%m-%Y %H:%M:%S %p"))
    
    # Relationships
    owner = relationship("User", back_populates="notifications")