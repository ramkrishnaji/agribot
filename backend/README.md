# AgriBot Modern Backend 🧠

The engine powering AgriBot's intelligence. It combines RAG over static government documents with real-time API integrations.

## 🚀 Core Modules

- **`main.py`**: FastAPI application with endpoints for Web (`/ask`) and WhatsApp (`/whatsapp`).
- **`model.py`**: Consultative LLM engine using Llama 3.1 on Groq.
- **`retriever_modern.py`**: Dual-retrieval system (Upstash Vector + Structured Data).
- **`weather.py`**: Real-time weather integration (Open-Meteo).
- **`mandi_service.py`**: Real-time market price integration (Agmarknet).

## 🔌 API Endpoints

- `GET /`: Root health check.
- `POST /ask`: Web interface query.
- `POST /whatsapp`: Twilio webhook for WhatsApp interaction.

## 🛠️ Environment Variables
Required secrets to be set in your environment:
- `GROQ_API_KEY`
- `UPSTASH_VECTOR_REST_URL`
- `UPSTASH_VECTOR_REST_TOKEN`
- `UPSTASH_REDIS_REST_URL`
- `UPSTASH_REDIS_REST_TOKEN`
- `AGMARKNET_API_KEY`
- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
