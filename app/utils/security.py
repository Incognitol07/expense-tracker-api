# app/utils/security.py

import os
import jwt
from fastapi import Depends, HTTPException, status
from datetime import datetime, timedelta
from passlib.context import CryptContext
from pydantic import ValidationError

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Hash a password
def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt hashing algorithm.

    Args: \n
        password (str): The plain text password to be hashed.

    Returns:
        str: The hashed password.
    """
    return pwd_context.hash(password)


# Verify a password against its hashed version
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify if the provided password matches the hashed password.

    Args: \n
        plain_password (str): The plain text password.
        hashed_password (str): The hashed password to compare with.

    Returns:
        bool: True if the passwords match, otherwise False.
    """
    return pwd_context.verify(plain_password, hashed_password)


# JWT configuration
SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY"
)  # Ensure the JWT_SECRET_KEY is set in the environment
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15  # Expiry time in minutes for access token


# Create an access token with expiration time
def create_access_token(data: dict) -> str:
    """
    Create a JWT access token with an expiration time.

    Args: \n
        data (dict): The data to encode in the JWT token.

    Returns:
        str: The generated JWT access token.
    """
    to_encode = (
        data.copy()
    )  # Create a copy of the data dictionary to avoid modifying the original
    expire = datetime.now() + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )  # Use UTC time for consistency
    to_encode.update({"token_type": "access"})
    to_encode.update({"exp": expire})  # Add expiration time to the payload
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# Verify and decode the access token
def verify_access_token(token: str) -> dict:
    """
    Verify and decode the JWT access token.

    Args: \n
        token (str): The JWT token to verify and decode.

    Returns:
        dict: The decoded payload of the JWT token.

    Raises:
        HTTPException: If the token is expired, invalid, or malformed.
    """
    try:
        payload = jwt.decode(
            token, SECRET_KEY, algorithms=[ALGORITHM]
        )  # Decode the token using the secret key
        if payload["token_type"] != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type for access",
            )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except ValidationError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed token",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Refresh token expiration time (e.g., 7 days)
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Create a refresh token with a longer expiration time
def create_refresh_token(data: dict) -> str:
    """
    Create a JWT refresh token with a longer expiration time.

    Args:
        data (dict): The data to encode in the JWT token.

    Returns:
        str: The generated JWT refresh token.
    """
    to_encode = data.copy()
    expire = datetime.now() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"token_type": "refresh"})
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Verify and decode the refresh token
def verify_refresh_token(token: str) -> dict:
    """
    Verify and decode the JWT refresh token.

    Args:
        token (str): The JWT token to verify and decode.

    Returns:
        dict: The decoded payload of the JWT token.

    Raises:
        HTTPException: If the token is expired, invalid, or malformed.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload["token_type"] != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type for refresh",
            )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
