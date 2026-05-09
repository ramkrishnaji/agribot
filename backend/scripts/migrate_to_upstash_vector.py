import json
import os
import uuid
from sentence_transformers import SentenceTransformer
from upstash_vector import Index

# Load environment variables
# Note: The user mentioned UPSTASH_VECTOR_URL and UPSTASH_VECTOR_TOKEN in Task 3
# but UPSTASH_VECTOR_REST_URL and UPSTASH_VECTOR_REST_TOKEN in my previous turns.
# I will check for both or use the user's specified ones.
UPSTASH_VECTOR_URL = os.environ.get("UPSTASH_VECTOR_URL") or os.environ.get("UPSTASH_VECTOR_REST_URL")
UPSTASH_VECTOR_TOKEN = os.environ.get("UPSTASH_VECTOR_TOKEN") or os.environ.get("UPSTASH_VECTOR_REST_TOKEN")

if not UPSTASH_VECTOR_URL or not UPSTASH_VECTOR_TOKEN:
    print("Error: UPSTASH_VECTOR_URL and UPSTASH_VECTOR_TOKEN must be set.")
    exit(1)

# Initialize
index = Index(url=UPSTASH_VECTOR_URL, token=UPSTASH_VECTOR_TOKEN)
print("Loading embedding model...")
model = SentenceTransformer("all-MiniLM-L6-v2")

# Load Q&A pairs (final or progress)
qa_path = "backend/qa_pairs_final.json"
if not os.path.exists(qa_path):
    qa_path = "backend/qa_pairs_progress.json"

if not os.path.exists(qa_path):
    print(f"Error: No Q&A data found. Wait for generate_qa.py to start.")
    exit(1)

with open(qa_path, "r", encoding="utf-8") as f:
    qa_pairs = json.load(f)

print(f"Migrating {len(qa_pairs)} Q&A pairs to Upstash Vector...")

# Upsert in batches of 100 (Upstash limit)
BATCH_SIZE = 100

for batch_start in range(0, len(qa_pairs), BATCH_SIZE):
    batch = qa_pairs[batch_start:batch_start + BATCH_SIZE]

    # Embed the questions (what farmers will search for)
    texts = [item["question"] for item in batch]
    embeddings = model.encode(texts, show_progress_bar=False)

    # Build vectors
    vectors = []
    for i, (item, embedding) in enumerate(zip(batch, embeddings)):
        vectors.append({
            "id": str(uuid.uuid4()),
            "vector": embedding.tolist(),
            "metadata": {
                "question": item["question"],
                "answer": item["answer"],
                "tags": item.get("tags", ["general"]),
                "source": item.get("source", "icar_gov")
            }
        })

    index.upsert(vectors=vectors)
    print(f"  Uploaded batch {batch_start // BATCH_SIZE + 1} "
          f"({batch_start + len(batch)}/{len(qa_pairs)})")

print("\nMigration complete!")
try:
    print(f"Total vectors in index: {index.info().vector_count}")
except:
    print("Could not retrieve index info (maybe using an older library version).")
