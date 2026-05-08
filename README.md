# AgriBot — Indian Agriculture AI Assistant

AgriBot is a conversational AI powered by **Groq (Llama 3)** and **RAG (Retrieval-Augmented Generation)**. It provides detailed, verified information on Indian agriculture, government schemes, weather, and pest management.

## 🚀 Deployment Guide

Follow these steps to get the project running on Hugging Face (Backend) and Vercel (Frontend).

### 1. GitHub Secrets (CI/CD)
Add these to your GitHub Repository -> Settings -> Secrets and variables -> Actions:
- `HF_TOKEN`: Your Hugging Face token with **Write** permission.
- `VERCEL_TOKEN`: Your Vercel account token.
- `VERCEL_ORG_ID`: Your Vercel Organization ID.
- `VERCEL_PROJECT_ID`: Your Vercel Project ID.

### 2. Backend (Hugging Face Spaces)
Once the GitHub Action deploys the code, go to your HF Space -> Settings -> **Variables and secrets**:
- Add `GROQ_API_KEY`: Your API key from [Groq Console](https://console.groq.com/).

### 3. Frontend (Vercel)
In your Vercel Project Settings -> **Environment Variables**:
- `BACKEND_URL`: `https://rk787-agribot.hf.space`
- `UPSTASH_REDIS_REST_URL`: (Optional) From Upstash for chat memory.
- `UPSTASH_REDIS_REST_TOKEN`: (Optional) From Upstash for chat memory.

## 🛠️ Project Structure
- `/backend`: FastAPI server + RAG logic + Groq integration.
- `/frontend`: Next.js 16 + Tailwind CSS 4 chat interface.
- `.github/workflows/ci.yml`: Automated deployment pipeline.

## 🧪 Local Development
1. **Backend**: `cd backend && pip install -r requirements.txt && uvicorn main:app --reload`
2. **Frontend**: `cd frontend && npm install && npm run dev`
