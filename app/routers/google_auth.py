# # app/routers/google_auth.py

from fastapi import HTTPException, APIRouter, Depends, status
from app.config import settings
from app.models import (
    User,
    Category,
    CategoryBudget,
)
from app.database import get_db
from app.utils import logger, create_access_token, create_refresh_token
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import requests
from datetime import date
from calendar import monthrange

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
router = APIRouter()
GOOGLE_CLIENT_ID = settings.GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET = settings.GOOGLE_CLIENT_SECRET
GOOGLE_REDIRECT_URI = settings.GOOGLE_REDIRECT_URI

@router.get("/login/google")
async def login_google():
    return {
        "url": f"https://accounts.google.com/o/oauth2/auth?response_type=code&client_id={GOOGLE_CLIENT_ID}&redirect_uri={GOOGLE_REDIRECT_URI}&scope=openid%20profile%20email&access_type=offline"
    }



@router.get("/callback/google")
async def auth_google(code: str, db: Session = Depends(get_db)):
    token_url = "https://accounts.google.com/o/oauth2/token"
    data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }
    response = requests.post(token_url, data=data)
    access_token = response.json().get("access_token")

    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to retrieve access token from Google",
        )

    user_info = requests.get(
        "https://www.googleapis.com/oauth2/v1/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    google_data = user_info.json()
    google_id = google_data.get("id")
    email = google_data.get("email")
    name = google_data.get("name")
    picture = google_data.get("picture")

    if not email or not google_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Google OAuth data",
        )

    # Check if user exists
    db_user = db.query(User).filter(User.email == email).first()

    # Register a new user if not exists
    if not db_user:
        logger.info(f"Registering new user from Google OAuth: {email}")
        username = email.split("@")[0]
        new_user = User(
            username=username,
            email=email,
            hashed_password=None,  # No password needed for Google OAuth
            profile_picture=picture,  # Assuming your User model has this field
            google_id=google_id,  # Optional, if you want to store the Google ID
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        db_user = (
            db.query(User)
            .filter(User.username == new_user.username, User.hashed_password == None, User.email==email, User.google_id==google_id)
            .first()
        )
        new_category = Category(
            name="Debt", description="For all debts", user_id=db_user.id
        )

        db.add(new_category)  # Add the new category to the session
        db.commit()  # Commit the changes to the database
        db.refresh(new_category)  # Refresh to get the latest state of the category

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

        logger.info(
            f"New user registered successfully: {new_user.username} ({new_user.email})."
        )
    if not db_user.full_name:
        db_user.full_name = name
    if not db_user.google_id:
        db_user.google_id = google_id
    if not db_user.profile_picture:
        db_user.profile_picture = picture
    db.commit()
    # Generate tokens
    access_token = create_access_token(data={"sub": db_user.username})
    refresh_token = create_refresh_token(data={"sub": db_user.username})

    logger.info(f"User '{db_user.username}' authenticated via Google OAuth.")
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "username": db_user.username,
        "user_id": db_user.id,
    }
