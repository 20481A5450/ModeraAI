import openai
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

# Load OpenAI API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize Redis cache
redis_client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

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

@router.post("/moderate/text", response_model=TextModerationResponse, tags=["Moderation"])
async def moderate_text(request: TextModerationRequest, db: Session = Depends(get_db)):
    """Moderates text content using OpenAI's Moderation API and stores the result."""

    # Check Redis cache first
    cache_key = f"moderation:{request.text}"
    cached_result = redis_client.get(cache_key)
    
    if cached_result:
        return TextModerationResponse(**json.loads(cached_result))

    # Call OpenAI Moderation API
    try:
        response = openai.Moderation.create(input=request.text, api_key=OPENAI_API_KEY)
        moderation_result = response["results"][0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI API error: {str(e)}")

    # Store moderation result in PostgreSQL
    moderation_entry = ModerationResult(
        text=request.text,
        flagged=moderation_result["flagged"],
        categories=moderation_result["categories"]
    )
    db.add(moderation_entry)
    db.commit()
    db.refresh(moderation_entry)

    # Cache the response in Redis
    response_data = {
        "id": moderation_entry.id,
        "text": moderation_entry.text,
        "flagged": moderation_entry.flagged,
        "categories": moderation_entry.categories,
    }
    redis_client.setex(cache_key, 3600, json.dumps(response_data))  # Cache for 1 hour

    return response_data