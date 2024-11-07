from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.schemas.auth import UserCreate, UserLogin
from app.models.user import User
from app.utils.security import hash_password, verify_password, create_access_token, verify_access_token
from app.database import get_db

router = APIRouter()

# OAuth2 scheme to retrieve token from Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Dependency to retrieve and verify the current user
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Verify the token and retrieve user information
    payload = verify_access_token(token)
    if payload is None:
        raise credentials_exception

    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception
    
    db_user = db.query(User).filter(User.username == username).first()
    if db_user is None:
        raise credentials_exception
    return db_user

# Register route
@router.post("/register")
async def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered")
    
    hashed_password = hash_password(user.password)
    new_user = User(username=user.username, email=user.email,hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# Login route
@router.post("/login")
async def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username and User.hashed_password == hash_password(user.password)).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": db_user.username})
    return {"access_token": access_token, "token_type": "bearer"}

# Protected route
@router.get("/protected-route")
async def protected_route(current_user: User = Depends(get_current_user)):
    return {"message": f"Hello, {current_user.username}! You have access to this protected route."}
