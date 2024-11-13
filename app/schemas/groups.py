# app/schemas/groups.py

from pydantic import BaseModel, EmailStr
from typing import Optional

# 1. Group Schema
class GroupBase(BaseModel):
    name: str

class GroupCreate(GroupBase):
    pass

class Groups(GroupBase):
    id: int

    class Config:
        from_attributes = True

# 2. Group Member Schema
class GroupMemberBase(BaseModel):
    email: EmailStr
    group_id: int

class GroupMemberCreate(GroupMemberBase):
    pass

class GroupMemberStatus(BaseModel):
    status: str = "active"  # "active", "pending", "rejected"

class GroupMembers(GroupMemberBase):
    id: int
    role: str  # "admin", "member"
    status: str  # "active", "pending", "rejected"

    class Config:
        from_attributes = True

# 3. Group Expense Schema
class GroupExpenseBase(BaseModel):
    group_id: int
    amount: float
    description: Optional[str] = None

class GroupExpenseCreate(GroupExpenseBase):
    pass

class GroupExpenses(GroupExpenseBase):
    id: int
    payer_id: int

    class Config:
        from_attributes = True

# 4. Expense Split Schema
class ExpenseSplitBase(BaseModel):
    user_id: int
    amount: float

class ExpenseSplitCreate(ExpenseSplitBase):
    pass

class ExpenseSplits(ExpenseSplitBase):
    id: int
    expense_id: int

    class Config:
        from_attributes = True
