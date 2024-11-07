from pydantic import BaseModel

class AlertBase(BaseModel):
    threshold: float

class AlertCreate(AlertBase):
    pass

class AlertUpdate(AlertBase):
    pass

class AlertResponse(AlertBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True
