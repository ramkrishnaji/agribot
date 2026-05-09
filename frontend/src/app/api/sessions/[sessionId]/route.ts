import { NextResponse } from 'next/server';
import { Redis } from '@upstash/redis';
import { auth } from '@clerk/nextjs/server';

const redis = new Redis({
  url: process.env.UPSTASH_REDIS_REST_URL!,
  token: process.env.UPSTASH_REDIS_REST_TOKEN!,
});

export async function GET(
  request: Request,
  { params }: { params: Promise<{ sessionId: string }> }
) {
  try {
    const { userId } = auth();
    if (!userId) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

    const { sessionId } = await params;
    const historyKey = `user:${userId}:session:${sessionId}`;
    
    const raw = await redis.lrange(historyKey, 0, -1);
    const messages = raw.map((item) =>
      typeof item === 'string' ? JSON.parse(item) : item
    );

    // Format for the frontend
    const formatted = messages.flatMap((m: any) => [
      { role: "user", content: m.user },
      { role: "bot", content: m.bot }
    ]);

    return NextResponse.json({ messages: formatted });

  } catch (error) {
    console.error('Session Details API error:', error);
    return NextResponse.json({ error: 'Failed to fetch session messages' }, { status: 500 });
  }
}
