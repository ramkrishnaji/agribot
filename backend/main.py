import os
import hashlib
import json
import asyncio
from fastapi import FastAPI, HTTPException, Request, Form, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from upstash_redis import Redis
from twilio.twiml.messaging_response import MessagingResponse

# Internal imports
from model import qa_model
from retriever_modern import retrieve_with_source
from weather import get_weather

app = FastAPI(
    title="AgriBot Beta",
    description="Modern Agriculture Expert — High ROI Crops & Subsidy Consultant",
    version="3.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Redis Caching ───────────────────────────────────────────────────────────

redis_client = None
url = os.environ.get("UPSTASH_REDIS_REST_URL")
token = os.environ.get("UPSTASH_REDIS_REST_TOKEN")

if url and token:
    redis_client = Redis(url=url, token=token)

CACHE_TTL_SECONDS = 6 * 60 * 60  # 6 hours

def get_cache_key(query: str) -> str:
    normalized = query.lower().strip()
    return "agribot:cache:v3:" + hashlib.md5(normalized.encode()).hexdigest()

def get_cached_answer(query: str) -> str | None:
    if not redis_client:
        return None
    try:
        key = get_cache_key(query)
        cached = redis_client.get(key)
        if cached:
            return cached 
    except Exception as e:
        print(f"Cache Read Error: {e}")
    return None

def set_cached_answer(query: str, answer: str) -> None:
    if not redis_client:
        return
    try:
        key = get_cache_key(query)
        redis_client.setex(key, CACHE_TTL_SECONDS, answer)
    except Exception as e:
        print(f"Cache Write Error: {e}")

# ─── Schemas ─────────────────────────────────────────────────────────────────

class HistoryEntry(BaseModel):
    user: str
    bot: str

class QAQuery(BaseModel):
    question: str
    history: Optional[List[HistoryEntry]] = []

class QAResponse(BaseModel):
    answer: str
    score: float
    cached: bool = False

# ─── Endpoints ───────────────────────────────────────────────────────────────

@app.get("/")
def read_root():
    return {
        "message": "Welcome to AgriBot Beta API",
        "status": "online",
        "documentation": "/docs",
        "health": "/health"
    }

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "agribot-modern-backend", "engine": "Groq/Llama-3.1"}

@app.post("/ask", response_model=QAResponse)
async def ask_question(query: QAQuery):
    if not query.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    # 1. Check Redis Cache First
    cached = get_cached_answer(query.question)
    if cached:
        return QAResponse(answer=cached, score=1.0, cached=True)

    # 2. Retrieve Context (Dual Search: Vector + Structured)
    retrieval_data = retrieve_with_source(query.question)
    context = retrieval_data["context"]

    # 3. Inject Live Weather if applicable
    weather_keywords = ["weather", "mausam", "temperature", "tapman", "rain", "baarish"]
    if any(kw in query.question.lower() for kw in weather_keywords):
        # Extract city
        words = query.question.split()
        city = None
        
        # Look for "in [City]"
        for i, word in enumerate(words):
            if word.lower() in ["in", "at", "for"] and i + 1 < len(words):
                city = words[i+1].strip("?.,")
                break
        
        # If not found, look for word before "weather/mausam"
        if not city:
            for i, word in enumerate(words):
                if word.lower() in weather_keywords and i > 0:
                    city = words[i-1].strip("?.,")
                    break
        
        if not city:
            city = "Mumbai" # Absolute fallback
        
        weather_context = get_weather(city)
        context = f"--- LIVE WEATHER UPDATE ---\n{weather_context}\n--- END WEATHER ---\n\n" + context

    # 4. Generate Answer with LLM
    history_list = [{"user": h.user, "bot": h.bot} for h in (query.history or [])]
    result = qa_model.answer_question(context, query.question, history_list)

    if result.get("error") and not result.get("answer"):
        raise HTTPException(status_code=500, detail=result["error"])

    answer = result["answer"]

    # 4. Cache the result
    set_cached_answer(query.question, answer)

    return QAResponse(
        answer=answer,
        score=result.get("score", 1.0),
        cached=False
    )

# ─── WhatsApp Webhook ────────────────────────────────────────────────────────

def format_for_whatsapp(text: str) -> str:
    """Converts basic markdown to WhatsApp formatting."""
    # Convert bold **text** to *text*
    text = text.replace("**", "*")
    # Remove other complex markdown if necessary
    return text

@app.post("/whatsapp")
async def whatsapp_webhook(Body: str = Form(...), From: str = Form(...)):
    """
    Twilio WhatsApp Webhook
    Body: The incoming message text
    From: The sender's WhatsApp number (e.g., whatsapp:+919876543210)
    """
    query_text = Body.strip()
    user_id = From.replace("whatsapp:", "")
    history_key = f"agribot:wa:history:{user_id}"

    # 1. Fetch History from Redis
    history_list = []
    if redis_client:
        try:
            raw_history = redis_client.lrange(history_key, -6, -1)
            history_list = [json.loads(h) for h in raw_history]
        except Exception as e:
            print(f"WA History Read Error: {e}")

    # 2. Retrieve Context (Reuse logic from /ask)
    retrieval_data = retrieve_with_source(query_text)
    context = retrieval_data["context"]

    # 3. Weather Integration
    weather_keywords = ["weather", "mausam", "temperature", "tapman", "rain", "baarish"]
    if any(kw in query_text.lower() for kw in weather_keywords):
        words = query_text.split()
        city = None
        for i, word in enumerate(words):
            if word.lower() in ["in", "at", "for"] and i + 1 < len(words):
                city = words[i+1].strip("?.,")
                break
        if not city:
            city = "Mumbai"
        weather_context = get_weather(city)
        context = f"--- LIVE WEATHER UPDATE ---\n{weather_context}\n--- END WEATHER ---\n\n" + context

    # 4. Generate Answer
    result = qa_model.answer_question(context, query_text, history_list)
    answer = result["answer"]

    # 5. Save History to Redis (1 hour TTL)
    if redis_client:
        try:
            new_entry = {"user": query_text, "bot": answer}
            redis_client.rpush(history_key, json.dumps(new_entry))
            redis_client.expire(history_key, 3600) # 1 hour
        except Exception as e:
            print(f"WA History Write Error: {e}")

    # 6. Respond via TwiML
    resp = MessagingResponse()
    formatted_answer = format_for_whatsapp(answer)
    resp.message(formatted_answer)
    
    return Response(content=str(resp), media_type="application/xml")
