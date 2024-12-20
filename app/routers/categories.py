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
from app.utils import logger

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
    db_category_name = db.query(Category).filter(Category.user_id == user.id, Category.name == category.name).first()
    db_category_description = db.query(Category).filter(Category.user_id == user.id, Category.description == category.description).first()

    if db_category_name:
        logger.warning(f"Category name '{category.name}' already exists for user '{user.username}' (ID: {user.id}).")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category name already exists")

    if db_category_description:
        logger.warning(f"Category description '{category.description}' already exists for user '{user.username}' (ID: {user.id}).")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category description already exists")

    # Create the new category
    new_category = Category(
        name=category.name,
        description=category.description,
        user_id=db_user.id,
    )
    db.add(new_category)
    db.commit()
    db.refresh(new_category)

    # Generate default category budget for the current month
    today = date.today()
    start_date = today.replace(day=1)  # Start of current month
    end_date = today.replace(day=monthrange(today.year, today.month)[1])  # End of current month

    # Check if a default budget exists for the category
    existing_budget = db.query(CategoryBudget).filter(
        CategoryBudget.category_id == new_category.id,
        CategoryBudget.user_id == db_user.id,
        CategoryBudget.status == "active",
        CategoryBudget.start_date <= end_date,
        CategoryBudget.end_date >= start_date,
    ).first()

    if existing_budget:
        logger.warning(f"An active budget already exists for category '{category.name}' (ID: {new_category.id}).")
    else:
        # Create a new default budget
        new_budget = CategoryBudget(
            category_id=new_category.id,
            amount_limit=0,
            start_date=start_date,
            end_date=end_date,
            user_id=db_user.id
        )
        db.add(new_budget)
        db.commit()
        db.refresh(new_budget)
        logger.info(f"Default budget created for category '{category.name}' with ID {new_budget.id}.")

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
    category = (
        db.query(Category)
        .filter(Category.id == category_id, Category.user_id == user.id)
        .first()
    )

    if not category:
        logger.error(
            f"Category {category_id} not found for user '{user.username}' (ID: {user.id})."
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category not found"
        )

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
    category = (
        db.query(Category)
        .filter(Category.id == category_id, Category.user_id == user.id)
        .first()
    )

    if not category:
        logger.error(
            f"Category {category_id} not found for user '{user.username}' (ID: {user.id})."
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category not found"
        )

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
    category = (
        db.query(Category)
        .filter(Category.name == category_name, Category.user_id == user.id)
        .first()
    )

    if not category:
        logger.error(
            f"Category {category_name} not found for user '{user.username}' (ID: {user.id})."
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category not found"
        )

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
    category = (
        db.query(Category)
        .filter(Category.id == category_id, Category.user_id == user.id)
        .first()
    )

    if not category:
        logger.error(
            f"Category {category_id} not found for user '{user.username}' (ID: {user.id})."
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category not found"
        )

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
    category = (
        db.query(Category)
        .filter(Category.name == category_name, Category.user_id == user.id)
        .first()
    )

    if not category:
        logger.error(
            f"Category {category_name} not found for user '{user.username}' (ID: {user.id})."
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category not found"
        )

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
