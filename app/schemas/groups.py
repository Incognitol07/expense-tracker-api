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
    group_id: int

class GroupMemberCreate(GroupMemberBase):
    email: EmailStr
    pass

class GroupMemberStatus(BaseModel):
    status: str = "active"  # "active", "pending", "rejected"

class GroupMemberResponse(BaseModel):
    user_id: int
    group_id: int
    role: str
    status: str
    # Add other fields here as needed

    class Config:
        from_attributes = True


class GroupMembers(GroupMemberBase):
    id: int
    role: str  # "admin", "member"
    status: str  # "active", "pending", "rejected"
    user_id:int

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
