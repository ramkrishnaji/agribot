import { NextResponse } from 'next/server';
import { Redis } from '@upstash/redis';
import { v4 as uuidv4 } from 'uuid';
import { auth } from '@clerk/nextjs/server';
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
    const { userId } = auth();
    
    if (!userId) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const body = await request.json();
    let { sessionId, message } = body;

    if (!message || !message.trim()) {
      return NextResponse.json({ error: 'Message is required' }, { status: 400 });
    }

    // Generate session ID for new conversations
    if (!sessionId) {
      sessionId = uuidv4();
    }

    // Individual context key
    const historyKey = `user:${userId}:session:${sessionId}`;
    const sessionsListKey = `user:${userId}:sessions`;

    // Retrieve last 6 entries (3 exchanges) from Redis for conversation memory
    let history: { user: string; bot: string; timestamp: string }[] = [];
    if (redis) {
      try {
        const raw = await redis.lrange(historyKey, -6, -1);
        history = raw.map((item) =>
          typeof item === 'string' ? JSON.parse(item) : item
        );
      } catch (redisError) {
        console.warn('Redis unavailable, proceeding without history:', redisError);
      }
    }

    // Call the FastAPI backend
    const backendResponse = await axios.post(
      `${BACKEND_URL}/ask`,
      {
        question: message,
        history: history,
      },
      { timeout: 30000 }
    );

    const aiAnswer =
      backendResponse.data.answer ||
      "I'm sorry, I couldn't find an answer. Please try rephrasing.";

    // Store this exchange in Redis (30 day expiry for individual context)
    const chatEntry = {
      user: message,
      bot: aiAnswer,
      timestamp: new Date().toISOString(),
    };

    if (redis) {
      try {
        // Save the exchange
        await redis.rpush(historyKey, JSON.stringify(chatEntry));
        await redis.expire(historyKey, 2592000); // 30 days
        
        // Add session to user's session list if it's new
        await redis.sadd(sessionsListKey, sessionId);
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
