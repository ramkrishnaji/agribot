import { NextResponse } from 'next/server';
import { Redis } from '@upstash/redis';
import { auth } from '@clerk/nextjs/server';

const redis = new Redis({
  url: process.env.UPSTASH_REDIS_REST_URL!,
  token: process.env.UPSTASH_REDIS_REST_TOKEN!,
});

export async function GET() {
  try {
    const { userId } = auth();
    if (!userId) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

    const sessionsListKey = `user:${userId}:sessions`;
    
    // Get all session IDs for this user
    const sessions = await redis.smembers(sessionsListKey);
    
    // For each session, get the first message to use as a title
    const sessionData = await Promise.all(
      sessions.map(async (sessionId) => {
        const historyKey = `user:${userId}:session:${sessionId}`;
        const firstEntryRaw = await redis.lrange(historyKey, 0, 0);
        
        let title = "New Chat";
        if (firstEntryRaw && firstEntryRaw.length > 0) {
          const firstEntry = typeof firstEntryRaw[0] === 'string' ? JSON.parse(firstEntryRaw[0]) : firstEntryRaw[0];
          title = firstEntry.user.substring(0, 30) + (firstEntry.user.length > 30 ? "..." : "");
        }
        
        return {
          id: sessionId,
          title: title,
        };
      })
    );

    return NextResponse.json({ sessions: sessionData });

  } catch (error) {
    console.error('Sessions API error:', error);
    return NextResponse.json({ error: 'Failed to fetch sessions' }, { status: 500 });
  }
}
