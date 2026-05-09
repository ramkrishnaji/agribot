import json
import os
import httpx
import asyncio
from sentence_transformers import SentenceTransformer

# Load credentials
URL = os.environ.get("UPSTASH_VECTOR_REST_URL")
TOKEN = os.environ.get("UPSTASH_VECTOR_REST_TOKEN")

async def migrate():
    if not URL or not TOKEN:
        print("Error: UPSTASH_VECTOR_REST_URL and UPSTASH_VECTOR_REST_TOKEN must be set.")
        return

    # Load local knowledge
    try:
        with open("knowledge.json", "r", encoding="utf-8") as f:
            docs = json.load(f)
        print(f"Loaded {len(docs)} documents.")
    except Exception as e:
        print(f"Error loading knowledge.json: {e}")
        return

    # Load model for one-time local embedding
    print("Loading embedding model...")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    
    # Prepare data in batches
    batch_size = 50
    async with httpx.AsyncClient(timeout=60.0) as client:
        for i in range(0, len(docs), batch_size):
            batch_docs = docs[i:i + batch_size]
            print(f"Processing batch {i//batch_size + 1} ({len(batch_docs)} docs)...")
            
            embeddings = model.encode(batch_docs).tolist()
            
            payload = []
            for j, text in enumerate(batch_docs):
                payload.append({
                    "id": f"doc_{i + j}",
                    "vector": embeddings[j],
                    "metadata": {"text": text}
                })
            
            # Push to Upstash
            resp = await client.post(
                f"{URL}/upsert",
                headers={"Authorization": f"Bearer {TOKEN}"},
                json=payload
            )
            resp.raise_for_status()
            print(f"Batch {i//batch_size + 1} upserted successfully.")

    print("Migration complete!")

if __name__ == "__main__":
    asyncio.run(migrate())
