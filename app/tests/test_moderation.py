import pytest
import json
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal, get_db
from app.models.moderation import ModerationResult
from unittest.mock import patch
from sqlalchemy.orm import Session
import pytest
import asyncio
import os



@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def client():
    return TestClient(app)

# client = TestClient(app)

@pytest.fixture(scope="function")
def test_db_session():
    """Create a test database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()

@pytest.fixture(autouse=True)
def setup_and_teardown_db(test_db_session: Session):
    """Setup and teardown for database tests."""
    test_db_session.query(ModerationResult).delete()
    test_db_session.commit()

def test_system_status(client):
    """Test system status endpoint."""
    response = client.get("/api/v1/start")
    assert response.status_code == 200
    data = response.json()
    assert "database" in data
    assert "redis" in data

def test_valid_text_moderation(client):
    """Test text moderation with valid input."""
    request_data = {"text": "Hi I wan't to buy some stuff. Could you help me?"}
    response = client.post("/api/v1/moderate/text", json=request_data)
    assert response.status_code == 200
    data = response.json()
    assert "flagged" in data
    assert "categories" in data

def test_valid_image_moderation(client):
    """Test image moderation with valid input."""
    try:
        with open("test_images/valid_image.jpg", "rb") as image:
            response = client.post("/api/v1/moderate/image", files={"file": image})
        assert response.status_code == 200
        data = response.json()
        assert "flagged" in data
        assert "categories" in data
    except Exception as e:
        print(e)

def test_invalid_file_format(client):
    """Test rejection of an unsupported file format."""
    try:
        with open("test_images/sample.txt", "rb") as file:
            response = client.post("/api/v1/moderate/image", files={"file": file})
        assert response.status_code == 400
        assert response.json()["detail"] == "Unsupported file format. Use JPEG or PNG."
    except Exception as e:
        print(e)

def test_corrupt_image(client):
    """Test handling of corrupt image files."""
    try:
        with open("test_images/corrupt.jpg", "rb") as image:
            response = client.post("/api/v1/moderate/image", files={"file": image})
        assert response.status_code == 400
        assert "Invalid image file" in response.json()["detail"]
    except Exception as e:
        print(e)

def test_moderation_caching(client):
    """Test if caching mechanism works properly."""
    try:
        request_data = {"text": "This is a harmless comment."}
        client.post("/api/v1/moderate/text", json=request_data)  # First request to cache result
        response = client.post("/api/v1/moderate/text", json=request_data)  # Second request should hit cache
        assert response.status_code == 200
        assert "flagged" in response.json()
        assert "categories" in response.json()
    except Exception as e:
        print(e)

def test_api_failure_handling(client):
    """Test handling of external API failures."""
    try:
        with patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 500
            mock_post.return_value.json.return_value = {"error": "Internal Server Error"}
            request_data = {"text": "This is a test message."}
            response = client.post("/api/v1/moderate/text", json=request_data)
        assert response.status_code == 500
        assert "Google API error" in response.json()["detail"]
    except Exception as e:
        print(e)
# def test_prometheus_metrics():
#     """Test if Prometheus metrics endpoint is accessible."""
#     response = client.get("/api/v1/metrics")
#     assert response.status_code == 200
#     assert "moderation_requests_total" in response.text

# def test_health_check():
#     """Test if health check endpoint is working."""
#     response = client.get("/api/v1/health")
#     assert response.status_code == 200
#     assert response.json() == {"status": "ok", "message": "ModeraAI is running"}
