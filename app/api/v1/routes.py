import os
import json
import io
import requests
from PIL import Image
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Request, Response
from sqlalchemy.orm import Session
from celery.result import AsyncResult
from app.core.database import SessionLocal, get_db
from app.api.v1.schemas import TextModerationRequest, TextModerationResponse
from app.models.moderation import ModerationResult
from app.core.cache import get_redis
# from app.workers.tasks import test_celery
import base64
from fastapi.responses import PlainTextResponse
from prometheus_client import Counter

REQUEST_COUNT = Counter('request_count', 'Total request count', ['method', 'endpoint', 'http_status'])
REQUEST_LATENCY = Counter('request_latency', 'Total time taken for request', ['method', 'endpoint', 'http_status'])

load_dotenv()

GOOGLE_MODERATION_API_KEY = os.getenv("GOOGLE_MODERATION_API_KEY")
if not GOOGLE_MODERATION_API_KEY:
    raise ValueError("Google Moderation API key is missing. Set GOOGLE_MODERATION_API_KEY in .env file.")

PERSPECTIVE_API_URL = "https://commentanalyzer.googleapis.com/v1alpha1/comments:analyze"
GOOGLE_VISION_API_URL = "https://vision.googleapis.com/v1/images:annotate"

router = APIRouter()

@router.get("/")
async def root():
    return {"message": "Welcome to ModeraAI - go to /start to check system status"}

@router.get("/start")
async def start_system():
    """Endpoint to check system status"""

    # Check database
    try:
        db = SessionLocal()
        from sqlalchemy.sql import text
        if db.execute(text("SELECT 1")): # Simple query to check DB connection
            db_status = f"DB Status Check - Postgres is Up and Running"
        else:
            db_status = f"DB Status Check - Postgres Server is not Running: {str(e)}"  
        db.close()
        db_status = "DB Status Check - Postgres is Up and Running"
    except Exception as e:
        db_status = f"DB Status Check - Postgres Server is not Running: {str(e)}"

    # Check Redis
    redis_client = await get_redis()
    try:
        await redis_client.set("test", "OK", ex=5)  # Set test value
        redis_status = "Redis Status Check - Redis is Up and Running"
    except Exception as e:
        redis_status = f"Redis Status Check - Redis Server is not Running: {str(e)}"

    # Check Celery
    # try:
    #     task = test_celery.delay()
    #     result = AsyncResult(task.id)
    #     celery_status = result.state  # Expected to be 'PENDING'
    #     if celery_status != 'PENDING':
    #         celery_status = "Celery Status Check - Celery is Up and Running"
    #     else:
    #         celery_status = "Celery Status Check - Celery Task is Pending"
    # except Exception as e:
    #     celery_status = f"Celery Status Check - Celery Server is not Running: {str(e)}"

    return {
        "database": db_status,
        "redis": redis_status,
        # "celery": celery_status,
        "message": "System is up and running - all services are operational"
    }
    
@router.post("/moderate/text")
async def moderate_text_endpoint(request: TextModerationRequest, db: Session = Depends(get_db)):
    """Endpoint for text moderation using Google Perspective API."""
    REQUEST_COUNT.labels("POST", "/api/v1/moderate/text", 200).inc()
    REQUEST_LATENCY.labels("POST", "/api/v1/moderate/text", 200).inc()
    text = request.text
    if not text:
        raise HTTPException(status_code=400, detail="No text provided")

    redis_client = await get_redis()
    cache_key = f"moderation:text:{text}"
    cached_result = await redis_client.get(cache_key)
    if cached_result:
        return json.loads(cached_result)

    request_data = {
        "comment": {"text": text},
        "languages": ["en"],
        "requestedAttributes": {"TOXICITY": {}}
    }
    try:
        response = requests.post(
            f"{PERSPECTIVE_API_URL}?key={GOOGLE_MODERATION_API_KEY}",
            json=request_data,
            timeout=5  # Add timeout to prevent hanging
        )
        response.raise_for_status()  # Raises error for non-200 responses
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=502, detail=f"External API error: {str(e)}")
    
    # print(response.json())
    result = response.json()
    toxicity_score = result["attributeScores"]["TOXICITY"]["summaryScore"]["value"]
    flagged = toxicity_score > 0.5
    
    moderation_result = {
        "text": text,
        "flagged": flagged,
        "categories": {"toxicity_score": toxicity_score}
    }
    
    db_entry = ModerationResult(
        text=text, 
        flagged=flagged, 
        categories={"toxicity_score": toxicity_score}
    )
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)
    
    await redis_client.setex(cache_key, 3600, json.dumps(moderation_result))
    return moderation_result

@router.post("/moderate/image")
async def moderate_image_endpoint(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Endpoint for image moderation using Google Vision API's SafeSearch Detection.
    Supports JPG, JPEG and PNG formats.
    """
    REQUEST_COUNT.labels("POST", "/api/v1/moderate/image", 200).inc()
    REQUEST_LATENCY.labels("POST", "/api/v1/moderate/image", 200).inc()
    if file.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
        raise HTTPException(status_code=400, detail="Unsupported file format. Use JPEG or PNG.")

    try:
        # Read image bytes and validate the image
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes))
        image.verify()
    except UnidentifiedImageError as e:
        raise HTTPException(status_code=400, detail=f"Invalid image file: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading image: {str(e)}")

    # Convert image to Base64
    image_base64 = base64.b64encode(image_bytes).decode('utf-8')

    # Construct API request payload
    vision_request = {
        "requests": [{
            "image": {"content": image_base64},
            "features": [{"type": "SAFE_SEARCH_DETECTION"}]
        }]
    }

    redis_client = await get_redis()
    cache_key = f"moderation:image:{file.filename}"
    cached_result = await redis_client.get(cache_key)
    if cached_result:
        return json.loads(cached_result)

    # Call Google Vision API
    response = requests.post(
        f"{GOOGLE_VISION_API_URL}?key={GOOGLE_MODERATION_API_KEY}",
        json=vision_request
    )
    response_data = response.json()

    try:
        response_data = response.json()
        safe_search = response_data["responses"][0].get("safeSearchAnnotation", {})
    except (KeyError, IndexError) as e:
        raise HTTPException(status_code=500, detail=f"Unexpected response: {str(e)}")

    annotations = response_data["responses"][0]["safeSearchAnnotation"]
    flagged = annotations["adult"] in ["LIKELY", "VERY_LIKELY"] or annotations["violence"] in ["LIKELY", "VERY_LIKELY"]

    # Prepare moderation result
    moderation_result = {
        "filename": file.filename,
        "flagged": flagged,
        "categories": annotations
    }

    # Store result in database
    db_entry = ModerationResult(
        text=file.filename, flagged=flagged, categories=annotations
    )
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)

    # Cache the result for future requests
    await redis_client.setex(cache_key, 3600, json.dumps(moderation_result))
    return moderation_result

@router.get("/moderation/{id}")
async def get_moderation_result(id: int, db: Session = Depends(get_db)):
    REQUEST_COUNT.labels("GET", "/api/v1/moderation/{id}", 200).inc()
    REQUEST_LATENCY.labels("GET", "/api/v1/moderation/{id}", 200).inc()
    try:
        redis_client = await get_redis()
        cache_key = f"moderation:{id}"
        cached_result = await redis_client.get(cache_key)
        if cached_result:
            return json.loads(cached_result)
        
        result = db.query(ModerationResult).filter(ModerationResult.id == id).first()
        if not result:
            raise HTTPException(status_code=404, detail="Moderation result not found")
        
        response = {
            "id": result.id,
            "text": result.text,
            "flagged": result.flagged,
            "categories": result.categories,
        }
        
        await redis_client.set(cache_key, json.dumps(response), ex=3600)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
@router.get("/stats")
async def get_moderation_stats(db: Session = Depends(get_db)):
    REQUEST_COUNT.labels("GET", "/api/v1/stats", 200).inc
    REQUEST_LATENCY.labels("GET", "/api/v1/stats", 200).inc()
    try:
        redis_client = await get_redis()
        cache_key = "moderation_stats"
        cached_stats = await redis_client.get(cache_key)
        if cached_stats:
            return json.loads(cached_stats)
        
        total_count = db.query(ModerationResult).count()
        flagged_count = db.query(ModerationResult).filter(ModerationResult.flagged == True).count()
        non_flagged_count = total_count - flagged_count
        
        stats = {
            "total_moderated": total_count,
            "flagged_count": flagged_count,
            "non_flagged_count": non_flagged_count,
        }
        
        await redis_client.set(cache_key, json.dumps(stats), ex=300)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
