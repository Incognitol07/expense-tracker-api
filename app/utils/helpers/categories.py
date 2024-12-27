from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models import (
    User,
    Category,
    CategoryBudget
)
from app.schemas import CategoryCreate
from .notifications import log_exception
from calendar import monthrange
from datetime import date
from app.utils import logger

def existing_category_attribute(db:Session, user: User, category:CategoryCreate, attribute:str):
    # Check for existing category attribute
    if attribute == "name":
        db_category_attribute = db.query(Category).filter(Category.user_id == user.id, Category.name == category.name).first()
    if attribute == "description":
        db_category_attribute = db.query(Category).filter(Category.user_id == user.id, Category.description == category.description).first()

    if db_category_attribute:
        log_exception(
            log_level="warning",
            log_message=f"Category {attribute} already exists for user '{user.username}' (ID: {user.id}).",
            status_raised=status.HTTP_404_NOT_FOUND,
            exception_message=f"Category {attribute} already exists"
        )

def get_category_model_by_id(db:Session, user:User, category_id:int):
    category = (
        db.query(Category)
        .filter(Category.id == category_id, Category.user_id == user.id)
        .first()
    )

    if not category:
        log_exception(
            log_level="error",
            log_message=f"Category {category_id} not found for user '{user.username}' (ID: {user.id}).",
            status_raised=status.HTTP_404_NOT_FOUND,
            exception_message=f"Category {category_id} not found"
        )
    
    return category

def get_category_model_by_name(db:Session, user:User, category_name:str):
    category = (
        db.query(Category)
        .filter(Category.name == category_name, Category.user_id == user.id)
        .first()
    )

    if not category:
        log_exception(
            log_level="error",
            log_message=f"Category {category_name} not found for user '{user.username}' (ID: {user.id}).",
            status_raised=status.HTTP_404_NOT_FOUND,
            exception_message=f"Category {category_name} not found"
        )
    
    return category


def create_new_category_budget(db: Session, new_category: Category, db_user: User):
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
        logger.warning(f"An active budget already exists for category '{new_category.name}' (ID: {new_category.id}).")
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
        logger.info(f"Default budget created for category '{new_category.name}' with ID {new_budget.id}.")


def create_new_category(db:Session, category:CategoryCreate, db_user: User):
    # Create the new category
    new_category = Category(
        name=category.name,
        description=category.description,
        user_id=db_user.id,
    )
    db.add(new_category)
    db.commit()
    db.refresh(new_category)

    create_new_category_budget(
        db=db,
        new_category=new_category,
        db_user=db_user
    )
    
    return new_category