from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models import (
    User,
    Category
)
from app.schemas import CategoryCreate
from .notifications import log_exception

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