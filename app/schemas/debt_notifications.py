# app/schemas/debt_notifications.py

from pydantic import BaseModel

# 1. Debt Notification Schema
class DebtNotificationBase(BaseModel):
    amount: float
    description: str
    debtor_id: int  # The user who owes the amount
    creditor_id: int  # The user who paid the expense

class DebtNotificationCreate(DebtNotificationBase):
    pass

class DebtNotificationStatus(str):
    ACCEPTED = True
    REJECTED = False
    PENDING = False

# 2. Debt Notification Schema with status (for responses)
class DebtNotifications(DebtNotificationBase):
    id: int
    status: str = DebtNotificationStatus.PENDING

    class Config:
        from_attributes = True

class DebtNotificationResponse(BaseModel):
    id: int
    amount: float
    description: str
    debtor_id: int  # The user who owes the amount
    creditor_id: int  # The user who paid the expense
    status: bool = DebtNotificationStatus.PENDING  # Status of the notification

    class Config:
        from_attributes = True
