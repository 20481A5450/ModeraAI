# ModeraAI - Content Moderation System

## Overview
ModeraAI is a scalable content moderation system designed to process text and image content using AI services. It follows a microservices architecture, implements caching, and supports high throughput.

## Features
- **Text Moderation API**: Accepts text for moderation with rate limiting and efficient request handling.
<<<<<<< HEAD
- **Image Moderation API**: Processes images for moderation (if implemented).
- **AI Service Integration**: Connects with OpenAI’s moderation API and includes a fallback mechanism to Google Perspective API if OpenAI is unavailable.
- **Queue Management**: Uses Celery with Redis for asynchronous task processing (skipped due to Pool issues on Windows).
=======
- **Image Moderation API**: Processes images for moderation.
- **AI Service Integration**: Connects with OpenAI’s moderation API and includes but not implemented due to free tier limit error.
  Implemented with Google Perspective API  - https://developers.perspectiveapi.com/s/docs-get-started?language=en_US
- **Queue Management**: Uses Celery with Redis for asynchronous task processing.
>>>>>>> 51d6371b406c56a9796265be22e18d2d21332480
- **Data Management**: Stores moderation results in PostgreSQL with optimized indexing and migrations.
- **Monitoring & Logging**: Structured logging and Prometheus metrics collection.
- **Dockerized Deployment**: Includes `docker-compose` for easy setup.
- **Health Checks**: Provides API health endpoints.

## Technologies Used
- **FastAPI** for API development
- **PostgreSQL** for data storage
- **Redis** for caching and queue management
<<<<<<< HEAD
- **Celery** for asynchronous task processing (skipped on Windows)
=======
- **Celery** for asynchronous task processing (Problem with Windows environment)
>>>>>>> 51d6371b406c56a9796265be22e18d2d21332480
- **Docker & docker-compose** for containerization
- **Prometheus** for monitoring
- **Pydantic** for data validation
- **pytest** for testing

## Setup Instructions

### Prerequisites
Ensure you have the following installed:
- Docker 
- Python 3.12.0
- Redis & PostgreSQL (if running without Docker)
- Prometheus (If running without Docker)

### Installation
1. Clone the repository:
   ```sh
   git clone https://github.com/20481A5450/moderaai.git
   cd moderaai
   ```

2. Set up environment variables by copying `.env.example`:
   ```sh
   cp .env.example .env
   ```
   Configure the `.env` file with the required database and API keys. If OpenAI API is unavailable, configure Google Perspective API as a fallback.

3. Start the services using Docker Compose:
   ```sh
   docker-compose up --build
   ```

4. If running manually, install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
   Then start the API server:
   ```sh
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

## API Endpoints

### Text Moderation
- **POST** `/api/v1/moderate/text`
  - **Request Body:**
    ```json
    {
      "text": "Your content here"
    }
    ```
  - **Response:**
    ```json
    {
      "id": "12345",
      "moderation_result": "safe",
      "flags": []
    }
    ```

### Image Moderation (If Implemented)
- **POST** `/api/v1/moderate/image`
  - **Request Body:** Image file upload
  - **Response:** Similar structure to text moderation

### Get Moderation Result
- **GET** `/api/v1/moderation/{id}`
  - **Response:**
    ```json
    {
      "id": "12345",
      "moderation_result": "safe",
      "flags": []
    }
    ```

### System Metrics
- **GET** `/metrics` (Prometheus metrics)
- **GET** `/health` (Health check endpoint)

## System Design
### Architecture
ModeraAI follows a **microservices-based** design with the following components:
1. **FastAPI Service**: Handles API requests and moderation logic.
2. **PostgreSQL Database**: Stores moderation results efficiently.
3. **Redis Cache**: Speeds up response times by caching results.
4. **Celery Workers**: Asynchronously process moderation tasks (skipped on Windows due to Pool issues).
5. **Prometheus**: Exposes monitoring metrics.

### Performance Considerations
- **Asynchronous Processing**: FastAPI ensures high concurrency.
- **Caching**: Redis caches results to minimize API calls.
- **Rate Limiting**: Protects against excessive requests.
- **Database Indexing**: Optimized PostgreSQL queries.
- **API Fallback**: If OpenAI API is unavailable, Google Perspective API is used.

## Load Testing
(Results to be added after testing)

## Testing
To run unit tests:
```sh
$env:PYTHONPATH = "$(Get-Location)"  # Add current directory to Python path
pytest 
```
