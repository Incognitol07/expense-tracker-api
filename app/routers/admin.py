# app/routers/admin.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.admin import Admin
from fastapi.security import OAuth2PasswordBearer
from app.models import User, Expense, Budget, Alert, Category
from app.schemas.auth import UserLogin, UserResponse, AdminCreate
from app.utils.security import create_access_token, hash_password, verify_access_token, verify_password
from app.config import settings

router = APIRouter()

# Dependency to retrieve and verify the current admin user
async def get_admin_user(token: str = Depends(OAuth2PasswordBearer(tokenUrl="admin/login")), db: Session = Depends(get_db)):
    """
    Retrieves and verifies the current admin user based on the access token.

    Args:
        token (str): The access token passed in the request header.
        db (Session): Database session for querying the database.

    Raises:
        HTTPException: If token validation fails or admin user is not found.
    
    Returns:
        Admin: The admin user object if valid.
    """
    payload = verify_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    username = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    db_admin = db.query(Admin).filter(Admin.username == username).first()
    if db_admin is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this resource"
        )

    return db_admin

@router.post("/login")
async def login(user: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticates an admin user and generates an access token.

    Args:
        user (UserLogin): Admin login credentials (username and password).
        db (Session): Database session for querying the database.

    Raises:
        HTTPException: If credentials are invalid.
    
    Returns:
        dict: Access token and token type for authentication.
    """
    db_admin = db.query(Admin).filter(Admin.username == user.username).first()
    if not db_admin or not verify_password(user.password, db_admin.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": db_admin.username})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", response_model=UserResponse)
async def register(user: AdminCreate, db: Session = Depends(get_db)):
    """
    Registers a new admin user.

    Args:
        user (AdminCreate): Admin registration data (username, email, password, master key).
        db (Session): Database session for querying the database.

    Raises:
        HTTPException: If master key is incorrect or username is already registered.
    
    Returns:
        dict: Success message with admin user details.
    """
    if user.master_key != settings.MASTER_KEY:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect master key")
    
    if db.query(Admin).filter(Admin.username == user.username).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered")
    
    hashed_password = hash_password(user.password)
    new_admin = Admin(username=user.username, email=user.email, hashed_password=hashed_password)
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)
    return {"id": new_admin.id, "username": new_admin.username, "message": "Registered successfully!"}

@router.get("/users")
def get_all_users(db: Session = Depends(get_db), admin: Admin = Depends(get_admin_user)):
    """
    Retrieves a list of all users.

    Args:
        db (Session): Database session for querying the database.
        admin (Admin): The current admin user.

    Returns:
        list: List of all users in the database.
    """
    users = db.query(User).all()
    return users

@router.get("/expenses")
def get_all_expenses(db: Session = Depends(get_db), admin: Admin = Depends(get_admin_user)):
    """
    Retrieves a list of all expenses.

    Args:
        db (Session): Database session for querying the database.
        admin (Admin): The current admin user.

    Returns:
        list: List of all expenses in the database.
    """
    expenses = db.query(Expense).all()
    return expenses

@router.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), admin: Admin = Depends(get_admin_user)):
    """
    Deletes a user along with their related expenses, budgets, alerts, and categories.

    Args:
        user_id (int): The ID of the user to be deleted.
        db (Session): Database session for querying and modifying the database.
        admin (Admin): The current admin user.

    Raises:
        HTTPException: If the user does not exist.

    Returns:
        dict: Success message confirming the user deletion.
    """
    target_user = db.query(User).filter(User.id == user_id).first()
    target_expenses = db.query(Expense).filter(Expense.user_id == user_id).all()
    target_budgets = db.query(Budget).filter(Budget.user_id == user_id).all()
    target_alerts = db.query(Alert).filter(Alert.user_id == user_id).all()
    target_categories = db.query(Category).filter(Category.user_id == user_id).all()

    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if target_expenses:
        for expense in target_expenses:
            db.delete(expense)
    if target_budgets:
        for budget in target_budgets:
            db.delete(budget)
    if target_alerts:
        for alert in target_alerts:
            db.delete(alert)
    if target_categories:
        for category in target_categories:
            db.delete(category)
    db.delete(target_user)

    db.commit()
    return {"message": f"Deleted user '{target_user.username}' successfully"}
