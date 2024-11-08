from pydantic import BaseModel
from datetime import datetime

class NotificationResponse(BaseModel):
    id: int
    message: str
    is_read: bool
    created_at: str

    class Config:
        from_attributes = True
