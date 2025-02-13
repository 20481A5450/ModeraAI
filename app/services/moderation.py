from transformers import pipeline
from app.core.cache import redis_client
import json

# Load Hugging Face's toxicity classification model
moderation_pipeline = pipeline("text-classification", model="unitary/toxic-bert")

def moderate_text(text: str):
    """
    Analyze text for toxicity using Hugging Face's `unitary/toxic-bert` model.
    Uses Redis for caching.
    """
    cache_key = f"moderation:{text}"
    cached_result = redis_client.get(cache_key)

    if cached_result:
        return json.loads(cached_result)  # Return cached result

    # Run text through the model
    result = moderation_pipeline(text)[0]
    
    # Convert Hugging Face model output to your database format
    flagged = result["score"] > 0.5  # Flagged if toxicity score > 0.5
    categories = {"toxicity_score": result["score"], "label": result["label"]}

    response = {
        "text": text,
        "flagged": flagged,
        "categories": categories
    }

    # Cache the result
    redis_client.setex(cache_key, 3600, json.dumps(response))  # Cache for 1 hour

    return response
