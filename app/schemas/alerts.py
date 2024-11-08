# app/schemas/alerts.py

from pydantic import BaseModel

# Base schema for alert-related data, defining the common fields
class AlertBase(BaseModel):
    """
    Base model for defining the common attributes of an alert.
    
    Attributes:
        threshold (float): The threshold for the alert, representing the limit
                            for triggering the alert (e.g., budget limit exceeded).
    """
    threshold: float

# Schema for creating a new alert
class AlertCreate(AlertBase):
    """
    Schema for creating a new alert.
    Inherits from AlertBase and does not add any additional fields.
    """
    pass

# Schema for updating an existing alert
class AlertUpdate(AlertBase):
    """
    Schema for updating an existing alert.
    Inherits from AlertBase and does not add any additional fields.
    """
    pass

# Schema for returning alert data in responses
class AlertResponse(AlertBase):
    """
    Schema for representing an alert in the response.
    
    Attributes:
        id (int): The unique identifier for the alert.
        user_id (int): The user associated with the alert.
    """
    id: int
    user_id: int

    class Config:
        """
        Configuration for the Pydantic model.
        Allows the model to use the attributes of the database models directly.
        """
        from_attributes = True
