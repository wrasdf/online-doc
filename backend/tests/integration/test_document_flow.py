import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from src.main import app
from src.db.session import Base, get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


def test_create_and_edit_document():
    # This is a placeholder test. It will fail because the endpoints are not implemented yet.
    # Create user
    response = client.post("/api/v1/users/", json={"email": "test@test.com", "password": "test"})
    assert response.status_code == 200
    user = response.json()

    # Create document
    response = client.post("/api/v1/documents/", json={"title": "test document", "owner_id": user["id"]})
    assert response.status_code == 200
    document = response.json()

    # Edit document
    response = client.put(f"/api/v1/documents/{document['id']}", json={"title": "new title"})
    assert response.status_code == 200
    assert response.json()["title"] == "new title"
