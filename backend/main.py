import os
import hashlib
import json
import asyncio
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from upstash_redis import Redis

# Internal imports
from model import qa_model
from retriever_modern import retrieve_with_source

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

    # 3. Generate Answer with LLM
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
