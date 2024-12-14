# # app/routers/google_auth.py

from fastapi import HTTPException, APIRouter, Depends, status
from app.config import settings
from app.models import User
from app.database import get_db
from app.utils import logger, create_access_token, create_refresh_token
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import requests

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
        db_user = new_user
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
