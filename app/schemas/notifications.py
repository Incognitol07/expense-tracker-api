# app/schemas/notifications.py

from pydantic import BaseModel
from datetime import datetime

class NotificationResponse(BaseModel):
    """
    Schema for representing a notification response.
    
    Attributes:
        id (int): The unique identifier for the notification.
        message (str): The content or message of the notification.
        is_read (bool): The status indicating whether the notification has been read.
        created_at (str): The timestamp when the notification was created, formatted as a string.
    """
    id: int
    message: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True
