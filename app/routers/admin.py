# app/routers/admin.py

import os
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.admin import Admin
from fastapi.security import OAuth2PasswordBearer
from app.models import User, Expense, Budget, Alert, Category
from app.schemas.auth import UserLogin, UserResponse, AdminCreate
from app.utils.security import create_access_token, hash_password, verify_access_token, verify_password
from app.config import settings
from app.utils.logging_config import logger  # Import the logger

router = APIRouter()

# Dependency to retrieve and verify the current admin user
async def get_admin_user(token: str = Depends(OAuth2PasswordBearer(tokenUrl="admin/login")), db: Session = Depends(get_db)):
    try:
        payload = verify_access_token(token)
        if payload is None:
            logger.warning("Token validation failed for a request.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        username = payload.get("sub")
        if username is None:
            logger.error("Invalid token payload: Missing 'sub' field.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )

        db_admin = db.query(Admin).filter(Admin.username == username).first()
        if db_admin is None:
            logger.warning(f"Unauthorized access attempt by unknown admin '{username}'.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this resource"
            )

        logger.info(f"Admin '{username}' authenticated successfully.")
        return db_admin
    except Exception as e:
        logger.error(f"Error during admin authentication: {e}")
        raise

@router.post("/login")
async def login(user: UserLogin, db: Session = Depends(get_db)):
    db_admin = db.query(Admin).filter(Admin.email == user.email).first()

    if not db_admin or not verify_password(user.password, db_admin.hashed_password):
        logger.warning(f"Failed login attempt for email: {user.email}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid credentials")

    access_token = create_access_token(data={"sub": db_admin.username})
    logger.info(f"Admin '{db_admin.username}' logged in successfully.")
    return {"access_token": access_token, "token_type": "bearer", "username": db_admin.username, "user_id": db_admin.id}

@router.post("/register")
async def register(user: AdminCreate, db: Session = Depends(get_db)):
    if user.master_key != settings.MASTER_KEY:
        logger.warning(f"Invalid master key used during admin registration for username: '{user.username}' and email: {user.email}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect master key")

    if db.query(Admin).filter(Admin.username == user.username).first():
        logger.warning(f"Attempt to register with an existing username: '{user.username}'")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered")
    
    if db.query(Admin).filter(Admin.email == user.email).first():
        logger.warning(f"Attempt to register with an existing email: {user.email}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    hashed_password = hash_password(user.password)
    new_admin = Admin(username=user.username, email=user.email, hashed_password=hashed_password)
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)
    logger.info(f"New admin registered successfully: '{new_admin.username}' ({new_admin.email}).")
    return {"username": new_admin.username, "email": user.email, "message": "Admin registered successfully!"}

@router.get("/users")
def get_all_users(db: Session = Depends(get_db), admin: Admin = Depends(get_admin_user)):
    users = db.query(User).all()
    logger.info(f"Admin '{admin.username}' retrieved all users.")
    for user in users:
        user.hashed_password = "Encrypted"
    return users

@router.get("/expenses")
def get_all_expenses(db: Session = Depends(get_db), admin: Admin = Depends(get_admin_user)):
    expenses = db.query(Expense).all()
    logger.info(f"Admin '{admin.username}' retrieved all expenses.")
    return expenses

@router.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), admin: Admin = Depends(get_admin_user)):
    target_user = db.query(User).filter(User.id == user_id).first()

    if not target_user:
        logger.warning(f"Attempted deletion of non-existent user with ID: {user_id} by admin '{admin.username}'.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    db.delete(target_user)
    db.commit()
    logger.info(f"Admin '{admin.username}' deleted user '{target_user.username}' (ID: {user_id}).")
    return {"message": f"Deleted user '{target_user.username}' successfully"}

@router.get("/logs")
def get_logs(admin: Admin = Depends(get_admin_user), skip: int = 0, limit: int = 100):
    """
    Securely retrieves application logs.
    - Only accessible to authenticated admins.
    - Logs are paginated to prevent overwhelming responses.
    """
    log_file = "audit_logs.log"
    if not os.path.exists(log_file):
        logger.error(f"Log file not found when requested by admin '{admin.username}'.")
        raise HTTPException(status_code=404, detail="Log file not found")

    with open(log_file, "r") as file:
        logs = file.readlines()

    # Sanitize sensitive data
    sanitized_logs = [line.replace("password", "****") for line in logs]

    # Paginate logs
    paginated_logs = sanitized_logs[skip: skip + limit]

    logger.info(f"Admin '{admin.username}' retrieved application logs (skip: {skip}, limit: {limit}).")
    return {"logs": paginated_logs}
