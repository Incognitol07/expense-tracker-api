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
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    PENDING = "pending"

# 2. Debt Notification Schema with status (for responses)
class DebtNotifications(DebtNotificationBase):
    id: int
    status: str = DebtNotificationStatus.PENDING

    class Config:
        from_attributes = True
