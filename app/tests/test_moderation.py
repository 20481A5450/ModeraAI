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

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

client = TestClient(app)

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

def test_system_status():
    """Test system status endpoint."""
    response = client.get("/api/v1/start")
    assert response.status_code == 200
    data = response.json()
    assert "database" in data
    assert "redis" in data

def test_valid_text_moderation():
    """Test text moderation with valid input."""
    request_data = {"text": "Hi I wan't to buy some stuff. Could you help me?"}
    response = client.post("/api/v1/moderate/text", json=request_data)
    assert response.status_code == 200
    data = response.json()
    assert "flagged" in data
    assert "categories" in data

# from httpx import AsyncClient

# @pytest.mark.asyncio
# async def test_valid_image_moderation():
#     async with AsyncClient(app=app, base_url="http://127.0.0.1:8000") as async_client:
#         with open("test_images/valid_image.jpg", "rb") as image:
#             response = await async_client.post("/api/v1/moderate/image", files={"file": image})
#         assert response.status_code == 200

# def test_invalid_file_format():
#     """Test rejection of an unsupported file format."""
#     with open("test_images/sample.txt", "rb") as file:
#         response = client.post("/api/v1/moderate/image", files={"file": file})
#     assert response.status_code == 400
#     assert response.json()["detail"] == "Unsupported file format. Use JPEG or PNG."

# def test_corrupt_image():
#     """Test handling of corrupt image files."""
#     with open("test_images/corrupt.jpg", "rb") as image:
#         response = client.post("/api/v1/moderate/image", files={"file": image})
#     assert response.status_code == 400
#     assert "Invalid image file" in response.json()["detail"]

# def test_moderation_caching():
#     """Test if caching mechanism works properly."""
#     request_data = {"text": "This is a harmless comment."}
#     client.post("/api/v1/moderate/text", json=request_data)  # First request to cache result
#     response = client.post("/api/v1/moderate/text", json=request_data)  # Second request should hit cache
#     assert response.status_code == 200
#     assert "flagged" in response.json()

# def test_api_failure_handling():
#     """Test handling of external API failures."""
#     with patch("requests.post") as mock_post:
#         mock_post.return_value.status_code = 500
#         mock_post.return_value.json.return_value = {"error": "Internal Server Error"}
#         request_data = {"text": "This is a test message."}
#         response = client.post("/api/v1/moderate/text", json=request_data)
#     assert response.status_code == 500
#     assert "Google API error" in response.json()["detail"]

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
