# app/models/group_debt.py

from sqlalchemy import Column, Integer, ForeignKey, Float, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class GroupDebt(Base):
    """
    Represents a debt between users in a group.

    Attributes:
        id (Integer): Unique identifier for the debt record.
        group_id (Integer): Foreign key to the group where the debt exists.
        debtor_id (Integer): Foreign key to the user who owes the debt.
        creditor_id (Integer): Foreign key to the user who is requesting payment.
        amount (Float): The amount of the debt.
        description (String): Optional description of the debt.
        amount_paid (Float): The amount that has been repaid.
        status (String): Debt status, e.g., "active", "paid", or "partial".
        due_date (DateTime): Optional due date for repayment.
        created_at (DateTime): Date and time when the debt was created.
    """
    __tablename__ = "group_debts"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"))
    debtor_id = Column(Integer, ForeignKey("users.id"))
    creditor_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Float, nullable=False)
    description = Column(String, nullable=True)
    amount_paid = Column(Float, default=0)
    status = Column(String, default="active")  # "active", "paid", "partial"
    due_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    group = relationship("Group", back_populates="group_debts")
    debtor = relationship("User", foreign_keys=[debtor_id])
    creditor = relationship("User", foreign_keys=[creditor_id])
