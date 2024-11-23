from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.models import User
from app.routers.auth import get_current_user
from app.database import get_db
from app.schemas.profile import UserProfile, ProfileResponse
from app.utils.logging_config import logger

router = APIRouter()

@router.get("/", response_model=ProfileResponse)
def get_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve the authenticated user's profile.
    """
    logger.info(f"Profile retrieval initiated for user ID {current_user.id}.")
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        logger.error(f"Profile retrieval failed: User with ID {current_user.id} not found in the database.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    logger.info(
        f"Profile successfully retrieved for user ID {current_user.id} with username '{current_user.username}'."
    )
    return user


@router.put("/", response_model=UserProfile)
def update_profile(
    profile: UserProfile,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update the user profile with new details.
    """
    logger.info(f"Profile update initiated for user ID {current_user.id}.")
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        logger.error(f"Profile update failed: User with ID {current_user.id} not found in the database.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )
    
    # Log the fields being updated
    updated_fields = []
    if profile.full_name:
        user.full_name = profile.full_name
        updated_fields.append("full_name")
    if profile.phone_number:
        user.phone_number = profile.phone_number
        updated_fields.append("phone_number")
    if profile.bio:
        user.bio = profile.bio
        updated_fields.append("bio")
    
    db.commit()
    db.refresh(user)

    logger.info(
        f"Profile successfully updated for user ID {current_user.id}. Updated fields: {', '.join(updated_fields) if updated_fields else 'None'}."
    )
    return user
