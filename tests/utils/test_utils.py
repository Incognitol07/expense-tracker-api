from fastapi.testclient import TestClient
from app.models import User
from app.schemas.auth import UserCreate, UserLogin, LoginResponse
from sqlalchemy.orm import Session
from app.utils import hash_password


def create_test_user(db: Session, user_data: UserCreate):
    """
    Helper function to create a test user in the database using the UserCreate schema.
    
    Args:
        db (Session): Database session.
        user_data (UserCreate): User creation data including username, email, and password.
        
    Returns:
        User: The created User object.
    """
    hashed_password = hash_password(user_data.password)
    test_user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hashed_password,
    )
    db.add(test_user)
    db.commit()
    db.refresh(test_user)
    return test_user


def authenticate_test_user(client: TestClient, login_data: UserLogin) -> LoginResponse:
    """
    Helper function to authenticate a user and return an access token.

    Args:
        client (TestClient): FastAPI TestClient.
        login_data (UserLogin): Login data including email and password.

    Returns:
        LoginResponse: A parsed response containing the access token and user details.
    """
    response = client.post(
        "/auth/user/login",
        data={"email": login_data.email, "password": login_data.password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    return LoginResponse(**response.json())


def create_and_authenticate_user(
    client: TestClient, db: Session, user_data: UserCreate
) -> LoginResponse:
    """
    Combines user creation and authentication for convenience in tests.

    Args:
        client (TestClient): FastAPI TestClient.
        db (Session): Database session.
        user_data (UserCreate): User creation data including username, email, and password.

    Returns:
        LoginResponse: A parsed response containing the access token and user details.
    """
    create_test_user(db, user_data)
    login_data = UserLogin(email=user_data.email, password=user_data.password)
    return authenticate_test_user(client, login_data)
