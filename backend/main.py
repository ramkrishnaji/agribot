from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from model import qa_model
from retriever import retriever
from typing import Optional, List
import httpx
import os

app = FastAPI(
    title="AgriBot API",
    description="Indian Agriculture AI Assistant — powered by Gemini + RAG",
    version="2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Schemas ─────────────────────────────────────────────────────────────────

class HistoryEntry(BaseModel):
    user: str
    bot: str
    timestamp: Optional[str] = None


class QAQuery(BaseModel):
    question: str
    context: Optional[str] = None
    history: Optional[List[HistoryEntry]] = []


class QAResponse(BaseModel):
    answer: Optional[str]
    score: float
    error: Optional[str] = None


# ─── Weather (Open-Meteo — 100% free, no API key) ────────────────────────────

WEATHER_KEYWORDS = [
    "weather", "rain", "rainfall", "temperature", "forecast", "climate",
    "humidity", "wind", "monsoon", "mausam", "barish", "garmi", "sardi",
    "baarish", "tapman", "aaj ka mausam",
]

# Common Indian city coordinates for fast lookup (no geocoding API call needed)
CITY_COORDS = {
    "delhi": (28.6139, 77.2090, "Delhi"),
    "mumbai": (19.0760, 72.8777, "Mumbai"),
    "lucknow": (26.8467, 80.9462, "Lucknow"),
    "patna": (25.5941, 85.1376, "Patna"),
    "jaipur": (26.9124, 75.7873, "Jaipur"),
    "chandigarh": (30.7333, 76.7794, "Chandigarh"),
    "bhopal": (23.2599, 77.4126, "Bhopal"),
    "hyderabad": (17.3850, 78.4867, "Hyderabad"),
    "bangalore": (12.9716, 77.5946, "Bangalore"),
    "bengaluru": (12.9716, 77.5946, "Bengaluru"),
    "chennai": (13.0827, 80.2707, "Chennai"),
    "kolkata": (22.5726, 88.3639, "Kolkata"),
    "ahmedabad": (23.0225, 72.5714, "Ahmedabad"),
    "pune": (18.5204, 73.8567, "Pune"),
    "nagpur": (21.1458, 79.0882, "Nagpur"),
    "amritsar": (31.6340, 74.8723, "Amritsar"),
    "ludhiana": (30.9010, 75.8573, "Ludhiana"),
    "agra": (27.1767, 78.0081, "Agra"),
    "varanasi": (25.3176, 82.9739, "Varanasi"),
    "indore": (22.7196, 75.8577, "Indore"),
    "bhubaneswar": (20.2961, 85.8245, "Bhubaneswar"),
    "ranchi": (23.3441, 85.3096, "Ranchi"),
    "dehradun": (30.3165, 78.0322, "Dehradun"),
    "shimla": (31.1048, 77.1734, "Shimla"),
    "guwahati": (26.1445, 91.7362, "Guwahati"),
    "coimbatore": (11.0168, 76.9558, "Coimbatore"),
    "surat": (21.1702, 72.8311, "Surat"),
    "kanpur": (26.4499, 80.3319, "Kanpur"),
    "nashik": (19.9975, 73.7898, "Nashik"),
    "vijayawada": (16.5062, 80.6480, "Vijayawada"),
}

WEATHER_CODE_MAP = {
    0: "Clear sky ☀️", 1: "Mainly clear 🌤️", 2: "Partly cloudy ⛅", 3: "Overcast ☁️",
    45: "Foggy 🌫️", 48: "Freezing fog 🌫️",
    51: "Light drizzle 🌦️", 53: "Drizzle 🌦️", 55: "Heavy drizzle 🌧️",
    61: "Light rain 🌧️", 63: "Moderate rain 🌧️", 65: "Heavy rain 🌧️",
    71: "Light snow ❄️", 73: "Moderate snow ❄️", 75: "Heavy snow ❄️",
    80: "Rain showers 🌦️", 81: "Moderate showers 🌧️", 82: "Violent showers ⛈️",
    95: "Thunderstorm ⛈️", 96: "Thunderstorm with hail ⛈️",
}


def detect_weather_intent(question: str) -> bool:
    q = question.lower()
    return any(kw in q for kw in WEATHER_KEYWORDS)


def extract_location_from_query(question: str) -> tuple:
    """Returns (lat, lon, city_name) — defaults to Delhi if not found."""
    q = question.lower()
    for city_key, coords in CITY_COORDS.items():
        if city_key in q:
            return coords
    return (28.6139, 77.2090, "Delhi")


async def fetch_weather(lat: float, lon: float, city_name: str) -> str:
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}"
        f"&current=temperature_2m,relative_humidity_2m,precipitation,"
        f"weather_code,wind_speed_10m"
        f"&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,weather_code"
        f"&timezone=Asia%2FKolkata&forecast_days=5"
    )
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(url)
            data = resp.json()

        curr = data.get("current", {})
        daily = data.get("daily", {})
        condition = WEATHER_CODE_MAP.get(curr.get("weather_code", 0), "Unknown")

        lines = [f"**🌤️ Live Weather — {city_name}**"]
        lines.append(f"- Condition: {condition}")
        lines.append(f"- Temperature: {curr.get('temperature_2m', 'N/A')}°C")
        lines.append(f"- Humidity: {curr.get('relative_humidity_2m', 'N/A')}%")
        lines.append(f"- Rainfall now: {curr.get('precipitation', 0)} mm")
        lines.append(f"- Wind: {curr.get('wind_speed_10m', 'N/A')} km/h")
        lines.append("\n**📅 5-Day Forecast:**")

        dates = daily.get("time", [])
        for i in range(min(5, len(dates))):
            mx = daily.get("temperature_2m_max", [None] * 5)[i]
            mn = daily.get("temperature_2m_min", [None] * 5)[i]
            rain = daily.get("precipitation_sum", [0] * 5)[i]
            code = daily.get("weather_code", [0] * 5)[i]
            cond = WEATHER_CODE_MAP.get(code, "")
            lines.append(f"- {dates[i]}: {mn}°C – {mx}°C, Rain: {rain} mm  {cond}")

        return "\n".join(lines)

    except Exception as e:
        return f"(Weather data temporarily unavailable: {e})"


# ─── Endpoints ───────────────────────────────────────────────────────────────

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "model": "gemini-1.5-flash",
        "knowledge_base_size": len(retriever.documents),
        "version": "2.0",
    }


@app.post("/ask", response_model=QAResponse)
async def ask_question(query: QAQuery):
    if not query.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    # 1. Retrieve top-5 relevant documents from knowledge base
    active_context = (
        query.context.strip()
        if query.context and query.context.strip()
        else retriever.get_context(query.question)
    )

    # 2. Check if user is asking about weather — inject live data
    live_data = ""
    if detect_weather_intent(query.question):
        lat, lon, city_name = extract_location_from_query(query.question)
        weather_info = await fetch_weather(lat, lon, city_name)
        live_data = f"\n\n[LIVE DATA INJECTED]\n{weather_info}"

    full_context = active_context + live_data

    # 3. Build history list for Gemini
    history_list = [
        {"user": h.user, "bot": h.bot}
        for h in (query.history or [])
    ]

    # 4. Generate answer with Gemini
    result = qa_model.answer_question(full_context, query.question, history_list)

    if result.get("error") and not result.get("answer"):
        print(f"ERROR in /ask: {result['error']}")
        raise HTTPException(status_code=500, detail=f"AI model error: {result['error']}")

    return QAResponse(
        answer=result["answer"],
        score=result["score"],
        error=result.get("error"),
    )
