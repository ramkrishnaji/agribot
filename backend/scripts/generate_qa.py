import json
import time
import asyncio
from pathlib import Path
import groq
import os

client = groq.Groq(api_key=os.environ.get("GROQ_API_KEY"))

async def generate_qa_for_chunk(chunk: dict, index: int) -> list:
    prompt = f"""You are an Indian agriculture expert helping farmers.

Read this farming information and generate 3 realistic questions 
an Indian farmer might ask, with answers based ONLY on this text.
Keep answers practical and in simple English.
Include Hindi terms where they are commonly used (e.g. kharif, rabi, jeevamrit).

Text:
{chunk['text']}

Return ONLY a valid JSON array, no other text:
[
  {{
    "question": "question a farmer would ask",
    "answer": "practical answer from the text",
    "tags": {json.dumps(chunk['tags'])}
  }}
]"""

    try:
        # Wrap the blocking call in a thread or just run it as is if it's not a lot of concurrency
        # Groq client is synchronous, so we use to_thread for better performance in asyncio
        resp = await asyncio.to_thread(
            client.chat.completions.create,
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=600
        )
        raw = resp.choices[0].message.content.strip()
        
        # Clean up common JSON issues
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            if raw.endswith("```"):
                raw = raw[:-3]
        
        qa_list = json.loads(raw)
        print(f"  Chunk {index}: generated {len(qa_list)} Q&A pairs")
        return qa_list

    except Exception as e:
        print(f"  Chunk {index} failed: {e}")
        return []

async def main():
    # Load cleaned knowledge base
    kb_path = Path("backend/knowledge_cleaned.json")
    if not kb_path.exists():
        print(f"Error: {kb_path} not found.")
        return

    with open(kb_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    print(f"Generating Q&A for {len(chunks)} chunks...")
    print("Estimated time: ~{:.0f} minutes\n".format(len(chunks) * 2 / 60))

    all_qa = []
    
    # Process in batches to respect Groq rate limits
    # Free tier: ~30 requests/minute
    BATCH_SIZE = 10 # Smaller batch to be safer on free tier
    SLEEP_BETWEEN_BATCHES = 65  # seconds

    for batch_start in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[batch_start:batch_start + BATCH_SIZE]
        batch_num = batch_start // BATCH_SIZE + 1
        total_batches = (len(chunks) + BATCH_SIZE - 1) // BATCH_SIZE
        
        print(f"\nBatch {batch_num}/{total_batches} "
              f"(chunks {batch_start}–{batch_start + len(batch) - 1})")

        tasks = [
            generate_qa_for_chunk(chunk, batch_start + i)
            for i, chunk in enumerate(batch)
        ]
        results = await asyncio.gather(*tasks)
        
        for qa_list in results:
            all_qa.extend(qa_list)

        # Save progress after every batch (crash-safe)
        progress_path = Path("backend/qa_pairs_progress.json")
        with open(progress_path, "w", encoding="utf-8") as f:
            json.dump(all_qa, f, ensure_ascii=False, indent=2)

        print(f"  Progress saved to {progress_path}. Total Q&A so far: {len(all_qa)}")

        # Rate limit pause between batches
        if batch_start + BATCH_SIZE < len(chunks):
            print(f"  Waiting {SLEEP_BETWEEN_BATCHES}s for rate limit...")
            await asyncio.sleep(SLEEP_BETWEEN_BATCHES)

    # Save final output
    output_path = Path("backend/qa_pairs_final.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_qa, f, ensure_ascii=False, indent=2)

    print(f"\n✓ Done! Generated {len(all_qa)} Q&A pairs")
    print(f"Saved to {output_path}")

if __name__ == "__main__":
    asyncio.run(main())
