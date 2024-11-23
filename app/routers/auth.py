# app/routers/auth.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.schemas import UserCreate, UserLogin, RegisterResponse, LoginResponse, MessageResponse
from app.models import User, Category, GroupMember, Group
from app.utils.security import hash_password, verify_password, create_access_token, verify_access_token
from app.database import get_db
from app.utils.logging_config import logger

# Create an instance of APIRouter to handle authentication routes
router = APIRouter()

# OAuth2 scheme to retrieve token from Authorization header
# The `tokenUrl` specifies the endpoint for obtaining a token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# Dependency to retrieve and verify the current user
# This will be used to secure routes that require user authentication
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Retrieves the current authenticated user by verifying the provided token.
    
    Args:
        token (str): The authentication token passed in the Authorization header.
        db (Session): The database session to query user information.
        
    Raises:
        HTTPException: If token validation fails or the user cannot be found.
        
    Returns:
        User: The authenticated user object from the database.
    """
    try:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        # Verify the token and retrieve user information
        payload = verify_access_token(token)
        if payload is None:
            logger.warning("Token validation failed for a request.")
            raise credentials_exception

        username: str = payload.get("sub")
        if username is None:
            logger.error("Invalid token payload: Missing 'sub' field.")
            raise credentials_exception
        
        # Query the user by username from the database
        db_user = db.query(User).filter(User.username == username).first()
        if db_user is None:
            logger.warning(f"Unauthorized access attempt by unknown user '{username}'.")
            raise credentials_exception
        
        logger.info(f"User '{username}' authenticated successfully.")
        return db_user
    except Exception as e:
        logger.error(f"Error during admin authentication: {e}")
        raise

# Register route to create a new user account
@router.post("/register", response_model=RegisterResponse)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    """
    Registers a new user account.
    
    Args:
        user (UserCreate): The user data containing the username, email, and password.
        db (Session): The database session to check for existing users and add new ones.
        
    Raises:
        HTTPException: If the username is already registered.
        
    Returns:
        User: The newly created user object.
    """
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        logger.warning(f"Attempt to register with an existing username: {user.username}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered")
    
    db_email = db.query(User).filter(User.email == user.email).first()
    if db_email:
        logger.warning(f"Attempt to register with an existing email: {user.email}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    
    # Hash the password before storing
    hashed_password = hash_password(user.password)
    new_user = User(username=user.username, email=user.email, hashed_password=hashed_password)
    
    # Add the new user to the database
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    db_user = db.query(User).filter(User.username == user.username, User.hashed_password==hashed_password).first()
    new_category = Category(
        name="Debt",
        description="For all debts",
        user_id=db_user.id
    )
    
    db.add(new_category)  # Add the new category to the session
    db.commit()  # Commit the changes to the database
    db.refresh(new_category)  # Refresh to get the latest state of the category

    logger.info(f"New user registered successfully: {new_user.username} ({new_user.email}).")
    return {"username":user.username, "email":user.email, "message":"Registered successfully", "created_at":new_user.created_at}

# Login route for user authentication and token generation
@router.post("/user/login")
async def user_login(user: UserLogin, db: Session = Depends(get_db)):
    """
    Logs in a user by verifying the username and password, and returning a JWT access token.
    
    Args:
        user (UserLogin): The user data containing the email and password.
        db (Session): The database session to validate user credentials.
        
    Raises:
        HTTPException: If the credentials are invalid.
        
    Returns:
        dict: A dictionary containing the access token and token type.
    """
    # Query the database for the user and verify password
    db_user = db.query(User).filter(User.email == user.email and User.hashed_password == hash_password(user.password)).first()
    
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        logger.warning(f"Failed login attempt for email: {user.email}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid credentials")

    # Create and return the JWT access token
    access_token = create_access_token(data={"sub": db_user.username})
    logger.info(f"User '{db_user.username}' logged in successfully.")
    return {"access_token": access_token, "token_type": "bearer", "username":db_user.username, "user_id": db_user.id}

# Protected route example requiring authentication
@router.get("/protected-route")
async def protected_route(current_user: User = Depends(get_current_user)):
    """
    A protected route that can only be accessed by authenticated users.
    
    Args:
        current_user (User): The currently authenticated user, provided by the `get_current_user` dependency.
        
    Returns:
        dict: A greeting message with the username of the authenticated user.
    """
    return {"message": f"Hello, {current_user.username}! You have access to this protected route."}

@router.delete("/account", response_model=MessageResponse)
def delete_account(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
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
    group_members= db.query(GroupMember).filter(GroupMember.user_id==user.id, GroupMember.role=="admin").all()
    if group_members:
        for group_member in group_members:
            groups= db.query(Group).filter(Group.id==group_member.id).all()
            for group in groups:
                db.delete(group)
                db.commit()
    user_id = db.query(User.id).filter(User.username == user.username, User.email==user.email).first()[0]
    target_user = db.query(User).filter(User.id == user_id).first()

    if not target_user:
        logger.warning(f"Attempted deletion of account with ID: {user_id} by user '{user.username}'.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")


    db.delete(target_user)
    db.commit()
    logger.info(f"User '{user.username}' deleted account (ID: {user_id}).")
    return {"message": f"Deleted account of '{target_user.username}' successfully"}

# Login route for user authentication and token generation
@router.post("/login")
async def login_for_oauth_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    db_user = db.query(User).filter(User.email == form_data.username).first()

    if not db_user or not verify_password(form_data.password, db_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid credentials")

    # Create and return the JWT access token
    access_token = create_access_token(data={"sub": db_user.username})
    return {"access_token": access_token, "token_type": "bearer", "username": db_user.username}