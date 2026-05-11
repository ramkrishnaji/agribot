---
title: AgriBot
emoji: 🌾
colorFrom: green
colorTo: emerald
sdk: docker
app_port: 7860
pinned: false
---

# AgriBot: Modern Agriculture Consultant 🌾🚜

**AgriBot** is a high-precision Conversational AI consultant designed to help Indian farmers transition from traditional agriculture to high-value, modern farming. It bridges the information gap between complex government subsidies and practical, on-ground implementation.

---

## 🌟 Key Features

### 1. High-ROI Crop Analysis
- Specialized knowledge in crops like **Dragon Fruit (Kamalam)**, **Coloured Capsicum**, and **Exotic Flowers**.
- Automated ROI calculations based on your specific budget (from ₹2 lakh to ₹50 lakh+).

### 2. Live Intelligence Engines
- **Real-Time Weather**: Live temperature, humidity, and rain forecasts via Open-Meteo integration.
- **Mandi Prices**: Daily wholesale prices fetched directly from the **Agmarknet API** (data.gov.in) for 4,300+ markets in India.

### 3. Government Subsidy Consultant (NHB/NHM)
- Guided eligibility checker for National Horticulture Board (NHB) and NHM schemes.
- Explains 40-50% back-ended subsidies in plain English.
- **Critical Safety Check**: Warns farmers about construction rules to prevent subsidy disqualification.

### 4. Multi-Channel Accessibility
- **Premium Web Dashboard**: A modern, glassmorphic interface built for desktop and mobile.
- **WhatsApp Integration**: Interact with AgriBot directly via WhatsApp (powered by Twilio) — no app installation required.

---

## 🛠️ Technical Architecture

- **LLM**: Llama 3.1 (8B/70B) running on **Groq** for ultra-fast (LPU) inference.
- **RAG Engine**: Dual-search architecture using **Upstash Vector** for semantic search over official government PDFs.
- **Memory & Cache**: **Upstash Redis** for conversation history and query caching.
- **Backend**: **FastAPI** (Python) with Twilio Webhooks.
- **Frontend**: **Next.js 16** + **Tailwind CSS** + **Clerk Auth**.

---

## 🇮🇳 Optimized for Indian Agriculture
- **Simple English**: Clear, jargon-free communication.
- **Indian Numbering**: Always uses Lakhs and Crores (₹2 lakh instead of ₹200,000).
- **Consultative Tone**: Acts as a professional advisor, not just a chatbot.

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- API Keys: `GROQ_API_KEY`, `UPSTASH_VECTOR_REST_URL`, `UPSTASH_REDIS_REST_URL`, `AGMARKNET_API_KEY`, `TWILIO_ACCOUNT_SID`.

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
python main.py
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

---

## 🏗️ Future Roadmap
- [ ] **Voice-First Interaction**: Support for voice notes in regional languages.
- [ ] **Soil Test Analysis**: Uploading soil reports for customized crop recommendations.
- [ ] **Market Prediction**: AI-based price trend forecasting.

---

**Disclaimer**: AgriBot provides advice based on official data. Always verify specific subsidy amounts with your local Horticulture officer.
