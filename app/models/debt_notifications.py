# app/models/debt_notification.py

from sqlalchemy import Column, Integer, ForeignKey, Boolean, Float, String
from sqlalchemy.orm import relationship
from app.database import Base

class DebtNotification(Base):
    """
    Represents a notification of a debt sent by a payer to other group members.

    Attributes:
        id (Integer): Unique identifier for the debt notification.
        amount (Float): The amount of the debt.
        description (String): Optional description for the debt.
        debtor_id (Integer): Foreign key to the user who owes the debt.
        creditor_id (Integer): Foreign key to the user who is requesting payment.
        status (Boolean): Whether the debt was accepted (True) or rejected (False).
    """
    __tablename__ = "debt_notifications"

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float, nullable=False)
    description = Column(String, nullable=True)
    debtor_id = Column(Integer, ForeignKey("users.id"))
    creditor_id = Column(Integer, ForeignKey("users.id"))
    status = Column(Boolean, default=False)  # False for rejected, True for accepted

    # Relationships
    debtor = relationship("User", foreign_keys=[debtor_id])
    creditor = relationship("User", foreign_keys=[creditor_id])
