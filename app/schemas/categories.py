# app/schemas/categories.py

from pydantic import BaseModel
from typing import Optional

# Base schema for Category-related attributes
class CategoryBase(BaseModel):
    """
    Base schema for category-related attributes. This serves as the foundation for creating or updating categories.
    
    Attributes:
        name (str): The name of the category.
        description (Optional[str]): A brief description of the category (optional).
    """
    name: str
    description: Optional[str] = None

# Schema for creating a new category (inherits from CategoryBase)
class CategoryCreate(CategoryBase):
    """
    Schema for creating a new category, extending the CategoryBase schema.
    Inherits all attributes from CategoryBase.
    """
    pass

# Schema for returning category details in the response (includes the category ID)
class CategoryResponse(CategoryBase):
    """
    Schema for returning a category's details in the response, including the category ID.
    
    Attributes:
        id (int): The unique identifier for the category.
    """
    id: int

    class Config:
        # This allows Pydantic to pull attributes from ORM models
        from_attributes = True

# Schema for updating an existing category (inherits from CategoryBase)
class CategoryUpdate(CategoryBase):
    """
    Schema for updating an existing category, extending the CategoryBase schema.
    Inherits all attributes from CategoryBase.
    """
    pass
