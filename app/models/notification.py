from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
import enum

class NotificationType(enum.Enum):
    ALERT = "alert"
    GROUP_DEBT = "group_debt"
    SYSTEM = "system"

class Notification(Base):
    """
    Represents a notification for a user, typically used for alerts or updates.

    Attributes:
        id (Integer): Unique identifier for each notification.
        user_id (Integer): Foreign key linking to the user associated with this notification.
        type (Enum): Category of the notification (e.g., alert, group debt, system).
        message (String): Content of the notification message.
        is_read (Boolean): Flag indicating whether the notification has been read by the user (default is False).
        created_at (DateTime): Timestamp of when the notification was created, defaults to the current date and time.

    Relationships:
        owner (User): Reference to the User who received the notification, with a back-populated 'notifications' attribute.
    """
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    type = Column(Enum(NotificationType), nullable=False)
    message = Column(String, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now(), index=True)
    
    # Relationships
    owner = relationship("User", back_populates="notifications")
