# app/routers/categories.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.schemas.categories import CategoryCreate, CategoryResponse, CategoryUpdate
from app.models.category import Category
from app.database import get_db
from app.routers.auth import get_current_user
from app.models.user import User

# Create an instance of APIRouter for category-related routes
router = APIRouter()

# Route to create a new category
@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(category: CategoryCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """
    Creates a new category for the authenticated user.

    Args:
        category (CategoryCreate): The category data provided by the user.
        db (Session): The database session to interact with the database.
        user (User): The currently authenticated user.

    Returns:
        CategoryResponse: The newly created category.
    
    Raises:
        HTTPException: If there is an issue with creating the category.
    """

    db_user = db.query(User).filter(User.email == user.email).first()
    db_category_name = db.query(Category).filter(Category.user_id == user.id, Category.name == category.name).first()
    db_category_description = db.query(Category).filter(Category.user_id == user.id, Category.description == category.description).first()

    if db_category_name:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category name already exists"
        )
    
    if db_category_description:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category description already exists"
        )

    # Create a new category with the generated category_id
    new_category = Category(
        name=category.name,
        description=category.description,
        user_id=db_user.id,
    )
    
    db.add(new_category)  # Add the new category to the session
    db.commit()  # Commit the changes to the database
    db.refresh(new_category)  # Refresh to get the latest state of the category
    return new_category

# Route to get all categories of the authenticated user
@router.get("/", response_model=list[CategoryResponse])
def get_categories(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """
    Retrieves all categories for the authenticated user.

    Args:
        db (Session): The database session to interact with the database.
        user (User): The currently authenticated user.

    Returns:
        list[CategoryResponse]: List of categories belonging to the user.
    
    Raises:
        HTTPException: If no categories are found for the user.
    """
    categories = db.query(Category).filter(Category.user_id == user.id).all()
    return categories

# Route to get a specific category by its ID
@router.get("/{category_id}", response_model=CategoryResponse)
def get_category_by_id(category_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """
    Retrieves a specific category by its ID for the authenticated user.

    Args:
        category_id (int): The ID of the category to retrieve.
        db (Session): The database session to interact with the database.
        user (User): The currently authenticated user.

    Returns:
        CategoryResponse: The category with the specified ID.
    
    Raises:
        HTTPException: If the category is not found or does not belong to the user.
    """
    category = db.query(Category).filter(Category.id == category_id, Category.user_id == user.id).first()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return category

# Route to update an existing category by its ID
@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(category_id: int, category_data: CategoryUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """
    Updates a category by its ID for the authenticated user.

    Args:
        category_id (int): The ID of the category to update.
        category_data (CategoryUpdate): The updated data for the category.
        db (Session): The database session to interact with the database.
        user (User): The currently authenticated user.

    Returns:
        CategoryResponse: The updated category.
    
    Raises:
        HTTPException: If the category is not found or does not belong to the user.
    """
    category = db.query(Category).filter(Category.id == category_id, Category.user_id == user.id).first()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    
    # Update category attributes with new values
    for key, value in category_data.model_dump(exclude_unset=True).items():
        setattr(category, key, value)
    
    db.commit()  # Commit changes to the database
    db.refresh(category)  # Refresh to get the updated state
    return category

# Route to delete a category by its ID
@router.delete("/{category_id}")
def delete_category(category_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """
    Deletes a category by its ID for the authenticated user.

    Args:
        category_id (int): The ID of the category to delete.
        db (Session): The database session to interact with the database.
        user (User): The currently authenticated user.

    Returns:
        dict: A message indicating successful deletion.
    
    Raises:
        HTTPException: If the category is not found or does not belong to the user.
    """
    category = db.query(Category).filter(Category.id == category_id, Category.user_id == user.id).first()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    
    db.delete(category)  # Delete the category from the session
    db.commit()  # Commit the deletion to the database
    return { "message" : "Deleted successfully" }
