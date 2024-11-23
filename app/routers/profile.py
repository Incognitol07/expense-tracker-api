# app/routers/profile.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.models import User
from app.utils.security import hash_password, verify_password, create_access_token, verify_access_token
from app.routers.auth import get_current_user
from app.database import get_db
from app.utils.logging_config import logger