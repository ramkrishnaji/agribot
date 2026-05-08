import { NextResponse } from 'next/server';
import { Redis } from '@upstash/redis';
import { v4 as uuidv4 } from 'uuid';
import axios from 'axios';

// Upstash Redis REST client — works in Vercel serverless (no TCP needed)
const redis = (process.env.UPSTASH_REDIS_REST_URL && !process.env.UPSTASH_REDIS_REST_URL.includes('your_'))
  ? new Redis({
      url: process.env.UPSTASH_REDIS_REST_URL!,
      token: process.env.UPSTASH_REDIS_REST_TOKEN!,
    })
  : null;

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:7860';

export async function POST(request: Request) {
  try {
    const body = await request.json();
    let { sessionId, message } = body;

    if (!message || !message.trim()) {
      return NextResponse.json({ error: 'Message is required' }, { status: 400 });
    }

    // Generate session ID for new conversations
    if (!sessionId) {
      sessionId = uuidv4();
    }

    // Retrieve last 6 entries (3 exchanges) from Redis for conversation memory
    let history: { user: string; bot: string; timestamp: string }[] = [];
    if (redis) {
      try {
        const raw = await redis.lrange(`session:${sessionId}`, -6, -1);
        history = raw.map((item) =>
          typeof item === 'string' ? JSON.parse(item) : item
        );
      } catch (redisError) {
        // Non-fatal — continue without history if Redis is unavailable
        console.warn('Redis unavailable, proceeding without history:', redisError);
      }
    }

    // Call the FastAPI backend (now on HF Spaces port 7860)
    const backendResponse = await axios.post(
      `${BACKEND_URL}/ask`,
      {
        question: message,
        history: history,  // Pass conversation history so Gemini can handle follow-ups
      },
      { timeout: 30000 }  // 30s timeout — Gemini can take a moment
    );

    const aiAnswer =
      backendResponse.data.answer ||
      "I'm sorry, I couldn't find an answer. Please try rephrasing.";

    // Store this exchange in Redis (24h expiry)
    const chatEntry = {
      user: message,
      bot: aiAnswer,
      timestamp: new Date().toISOString(),
    };

    if (redis) {
      try {
        await redis.rpush(`session:${sessionId}`, JSON.stringify(chatEntry));
        await redis.expire(`session:${sessionId}`, 86400);
      } catch (redisError) {
        console.warn('Could not store to Redis:', redisError);
      }
    }

    return NextResponse.json({
      sessionId,
      answer: aiAnswer,
      score: backendResponse.data.score,
    });

  } catch (error: unknown) {
    const err = error as { message?: string; response?: { data?: unknown } };
    console.error('Chat API error:', err.message);
    return NextResponse.json(
      {
        error: 'Failed to process request',
        details: err.response?.data || err.message,
      },
      { status: 500 }
    );
  }
}
