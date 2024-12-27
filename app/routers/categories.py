# app/routers/categories.py

from datetime import date
from calendar import monthrange
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from app.schemas import CategoryCreate, CategoryResponse, CategoryUpdate, DetailResponse
from app.models import Category, CategoryBudget
from app.database import get_db
from app.routers.auth import get_current_user
from app.models.user import User
from app.background_tasks import check_category_budget
from app.utils import (
    logger, 
    existing_category_attribute,
    get_category_model_by_name,
    get_category_model_by_id,
    create_new_category
)

# Create an instance of APIRouter for category-related routes
router = APIRouter()

# Route to create a new category and automatically create a default category budget
@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    category: CategoryCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Creates a new category for the authenticated user and automatically creates a default category budget.
    """

    db_user = db.query(User).filter(User.email == user.email).first()

    # Check for existing category name and description   
    existing_category_attribute(db=db, user=user, category=category, attribute="name")
    existing_category_attribute(db=db, user=user, category=category, attribute="description")

    new_category = create_new_category(
        db=db,
        category=category,
        db_user=db_user
    )

    background_tasks.add_task(check_category_budget, user.id)

    logger.info(f"Category '{category.name}' created successfully for user '{user.username}' (ID: {user.id}).")

    # Optionally, you can return both category and budget details in the response
    return new_category



# Route to get all categories of the authenticated user
@router.get("/", response_model=list[CategoryResponse])
def get_categories(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    """
    Retrieves all categories for the authenticated user.

    Args: \n
        db (Session): The database session to interact with the database.
        user (User): The currently authenticated user.

    Returns:
        list[CategoryResponse]: List of categories belonging to the user.

    Raises:
        HTTPException: If no categories are found for the user.
    """
    categories = db.query(Category).filter(Category.user_id == user.id).all()

    # Log the number of categories retrieved
    logger.info(
        f"Fetched {len(categories)} categories for user '{user.username}' (ID: {user.id})."
    )

    if not categories:
        logger.warning(
            f"No categories found for user '{user.username}' (ID: {user.id})."
        )

    return categories


# Route to get a specific category by its ID
@router.get("/{category_id}", response_model=CategoryResponse)
def get_category_by_id(
    category_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Retrieves a specific category by its ID for the authenticated user.

    Args: \n
        category_id (int): The ID of the category to retrieve.
        db (Session): The database session to interact with the database.
        user (User): The currently authenticated user.

    Returns:
        CategoryResponse: The category with the specified ID.

    Raises:
        HTTPException: If the category is not found or does not belong to the user.
    """
    category = get_category_model_by_id(db=db, user=user, category_id=category_id)

    logger.info(
        f"Fetched category {category_id} for user '{user.username}' (ID: {user.id})."
    )
    return category


# Route to update an existing category by its ID
@router.put("/id/{category_id}", response_model=CategoryResponse)
def update_category_by_id(
    category_id: int,
    category_data: CategoryUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Updates a category by its ID for the authenticated user.

    Args: \n
        category_id (int): The ID of the category to update.
        category_data (CategoryUpdate): The updated data for the category.
        db (Session): The database session to interact with the database.
        user (User): The currently authenticated user.

    Returns:
        CategoryResponse: The updated category.

    Raises:
        HTTPException: If the category is not found or does not belong to the user.
    """
    category = get_category_model_by_id(db=db, user=user, category_id=category_id)

    # Update category attributes with new values
    for key, value in category_data.model_dump(exclude_unset=True).items():
        setattr(category, key, value)

    db.commit()  # Commit changes to the database
    db.refresh(category)  # Refresh to get the updated state

    logger.info(
        f"Category {category_id} updated for user '{user.username}' (ID: {user.id})."
    )
    return category


# Route to update an existing category by its name
@router.put("/name/{category_name}", response_model=CategoryResponse)
def update_category_by_name(
    category_name: str,
    category_data: CategoryUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Updates a category by its name for the authenticated user.

    Args: \n
        category_name (str): The name of the category to update.
        category_data (CategoryUpdate): The updated data for the category.
        db (Session): The database session to interact with the database.
        user (User): The currently authenticated user.

    Returns:
        CategoryResponse: The updated category.

    Raises:
        HTTPException: If the category is not found or does not belong to the user.
    """
    category = get_category_model_by_name(db=db, user=user, category_name=category_name)

    # Update category attributes with new values
    for key, value in category_data.model_dump(exclude_unset=True).items():
        setattr(category, key, value)

    db.commit()  # Commit changes to the database
    db.refresh(category)  # Refresh to get the updated state

    logger.info(
        f"Category {category_name} updated for user '{user.username}' (ID: {user.id})."
    )
    return category


# Route to delete a category by its ID
@router.delete("/id/{category_id}", response_model=DetailResponse)
def delete_category_by_id(
    category_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Deletes a category by its ID for the authenticated user.

    Args: \n
        category_id (int): The ID of the category to delete.
        db (Session): The database session to interact with the database.
        user (User): The currently authenticated user.

    Returns:
        dict: A message indicating successful deletion.

    Raises:
        HTTPException: If the category is not found or does not belong to the user.
    """
    category = get_category_model_by_id(db=db, user=user, category_id=category_id)

    if category.name == "Group Debts":
        logger.error(
            f"Attempt to delete restricted category 'Group Debts' by user '{user.username}' (ID: {user.id})."
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete this category",
        )

    db.delete(category)  # Delete the category from the session
    db.commit()  # Commit the deletion to the database

    logger.info(
        f"Category {category_id} deleted successfully for user '{user.username}' (ID: {user.id})."
    )
    return {"detail": f"Deleted category '{category.name}' successfully"}


# Route to delete a category by its name
@router.delete("/name/{category_name}", response_model=DetailResponse)
def delete_category_by_name(
    category_name: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Deletes a category by its name for the authenticated user.

    Args: \n
        category_name (str): The name of the category to delete.
        db (Session): The database session to interact with the database.
        user (User): The currently authenticated user.

    Returns:
        dict: A message indicating successful deletion.

    Raises:
        HTTPException: If the category is not found or does not belong to the user.
    """
    category = get_category_model_by_name(db=db, user=user, category_name=category_name)

    if category.name == "Group Debts":
        logger.error(
            f"Attempt to delete restricted category 'Group Debts' by user '{user.username}' (ID: {user.id})."
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete this category",
        )

    db.delete(category)  # Delete the category from the session
    db.commit()  # Commit the deletion to the database

    logger.info(
        f"Category {category_name} deleted successfully for user '{user.username}' (ID: {user.id})."
    )
    return {"detail": "Deleted successfully"}
