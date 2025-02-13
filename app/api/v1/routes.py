# import openai
import os
import json
import redis
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from fastapi import APIRouter
from app.core.database import Base, engine, SessionLocal
from app.api.v1.schemas import TextModerationRequest, TextModerationResponse
from app.models.moderation import ModerationResult
from app.services.moderation import moderate_text
from app.core.cache import get_redis

# Load OpenAI API Key
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

router = APIRouter()

@router.get("/")
async def read_root():
    return {"message": "Welcome to ModeraAI"}

@router.get("/health")
async def health_check():
    if engine:
    # if engine:
    #     from sqlalchemy import text
    #     db = SessionLocal()
    #     result = db.execute(text("SELECT * FROM information_schema.tables WHERE table_schema='public'")).mappings().all()
    #     tables = [dict(row) for row in result]
    #     db.close()
        # return {"status": "Database connection successful", "tables": tables}
        return {"status":"ok", "message":"ModeraAI is running"}
    else:
        return {"status": "Database connection failed"}

# @router.post("/moderate/text", response_model=TextModerationResponse, tags=["Moderation"])
# async def moderate_text(request: TextModerationRequest, db: Session = Depends(get_db)):
#     """Moderates text content using OpenAI's Moderation API and stores the result."""

#     # Check Redis cache first
#     cache_key = f"moderation:{request.text}"
#     cached_result = redis_client.get(cache_key)
    
#     if cached_result:
#         return TextModerationResponse(**json.loads(cached_result))

#     # Call OpenAI Moderation API
#     try:
#         print(OPENAI_API_KEY)
#         response = openai.Moderation.create(input=request.text, api_key=OPENAI_API_KEY)
#         print(response)
#         moderation_result = response["results"][0]
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"OpenAI API error: {str(e)}")

#     # Store moderation result in PostgreSQL
#     moderation_entry = ModerationResult(
#         text=request.text,
#         flagged=moderation_result["flagged"],
#         categories=moderation_result["categories"]
#     )
#     db.add(moderation_entry)
#     db.commit()
#     db.refresh(moderation_entry)

#     # Cache the response in Redis
#     response_data = {
#         "id": moderation_entry.id,
#         "text": moderation_entry.text,
#         "flagged": moderation_entry.flagged,
#         "categories": moderation_entry.categories,
#     }
#     redis_client.setex(cache_key, 3600, json.dumps(response_data))  # Cache for 1 hour

#     return response_data

from fastapi import Request

@router.post("/moderate/text")
async def moderate_text_endpoint(request: Request):
    payload = await request.json()
    text = payload.get("text")
    if not text:
        raise HTTPException(status_code=400, detail="No text provided")

    # Moderate the text
    result = await moderate_text(text)

    # Save result to database
    db = SessionLocal()
    db_entry = ModerationResult(
        text=result["text"],
        flagged=result["flagged"],
        categories=result["categories"]
    )
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)
    db.close()

    return result   

@router.get("/moderation/{id}")
async def get_moderation_result(id: int, db: Session = Depends(get_db)):
    """
    Retrieve a moderation result by ID.
    Uses Redis caching for faster access.
    """
    redis_client = await get_redis()  # Await the async Redis connection
    cache_key = f"moderation:{id}"

    # Check if result exists in Redis cache
    cached_result = await redis_client.get(cache_key)
    if cached_result:
        print("Cache hit!")
        return json.loads(cached_result)

    # Fetch from database if not in cache
    result = db.query(ModerationResult).filter(ModerationResult.id == id).first()
    print("Cache miss! - Direct from DB")
    if not result:
        raise HTTPException(status_code=404, detail="Moderation result not found")

    # Serialize response
    response = {
        "id": result.id,
        "text": result.text,
        "flagged": result.flagged,
        "categories": result.categories,
    }

    # Store result in Redis for caching
    await redis_client.set(cache_key, json.dumps(response), ex=3600)

    return response

@router.get("/stats")
async def get_moderation_stats(db: Session = Depends(get_db)):
    """
    Get moderation statistics (total moderated, flagged vs non-flagged, category breakdown).
    Uses Redis caching for efficiency.
    """
    redis_client = await get_redis()  # Await the async Redis connection
    cache_key = "moderation_stats"

    # Check Redis cache first
    cached_stats = await redis_client.get(cache_key)
    if cached_stats:
        print("Cache hit!")
        return json.loads(cached_stats)

    # Fetch stats from the database
    total_count = db.query(ModerationResult).count()
    flagged_count = db.query(ModerationResult).filter(ModerationResult.flagged == True).count()
    non_flagged_count = total_count - flagged_count

    # Get category-wise breakdown
    category_counts = {}
    all_results = db.query(ModerationResult.categories).all()
    for result in all_results:
        if result.categories:  # Ensure categories exist
            for category, score in result.categories.items():
                if category not in category_counts:
                    category_counts[category] = 0
                category_counts[category] += 1

    print("Cache miss! - Direct from DB")

    # Prepare response
    stats = {
        "total_moderated": total_count,
        "flagged_count": flagged_count,
        "non_flagged_count": non_flagged_count,
        "category_breakdown": category_counts,
    }

    # Store in Redis (cache for 5 minutes)
    await redis_client.set(cache_key, json.dumps(stats), ex=300)

    return stats

