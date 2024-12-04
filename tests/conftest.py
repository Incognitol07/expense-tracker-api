import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db

# Configure test database (SQLite in-memory database)
SQLALCHEMY_DATABASE_URL = "sqlite:///./expense.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency override for test database
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module")
def test_client():
    """
    Fixture to set up and tear down the FastAPI test client.
    """
    # Create all tables in the test database
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as client:
        yield client
    # Drop all tables after tests
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def test_db():
    """
    Fixture to provide a clean database session for each test.
    """
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
