import json
import os
import torch
from sentence_transformers import SentenceTransformer, util


class Retriever:
    def __init__(self, knowledge_path="knowledge.json"):
        print("Loading sentence transformer model...")
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

        # Load knowledge base
        try:
            with open(knowledge_path, "r", encoding="utf-8") as f:
                self.documents = json.load(f)
            print(f"Loaded {len(self.documents)} documents from knowledge base.")
        except Exception as e:
            print(f"Error loading knowledge base: {e}")
            self.documents = ["AgriBot is a conversational AI assistant for Indian agriculture."]

        # Load or compute embeddings
        embedding_cache_path = "embeddings.pt"
        if os.path.exists(embedding_cache_path):
            try:
                self.document_embeddings = torch.load(
                    embedding_cache_path, map_location=torch.device("cpu")
                )
                print(f"Loaded cached embeddings ({self.document_embeddings.shape[0]} vectors).")
            except Exception as e:
                print(f"Failed to load cached embeddings: {e}. Recomputing...")
                self._compute_and_save_embeddings(embedding_cache_path)
        else:
            print("No embedding cache found. Computing embeddings (this may take a few minutes)...")
            self._compute_and_save_embeddings(embedding_cache_path)

    def _compute_and_save_embeddings(self, path: str):
        self.document_embeddings = self.model.encode(
            self.documents, convert_to_tensor=True, show_progress_bar=True, batch_size=64
        )
        torch.save(self.document_embeddings, path)
        print(f"Embeddings computed and saved to {path}.")

    def get_context(self, query: str, top_k: int = 5) -> str:
        """
        Returns the top-k most semantically relevant paragraphs
        from the knowledge base, joined as a single context string.
        """
        query_embedding = self.model.encode(query, convert_to_tensor=True)
        cos_scores = util.cos_sim(query_embedding, self.document_embeddings)[0]

        # Get top-k results (previously only returned top-1)
        k = min(top_k, len(self.documents))
        top_results = torch.topk(cos_scores, k=k)

        docs = [self.documents[idx] for idx in top_results.indices]
        return "\n\n---\n\n".join(docs)


# Singleton instance
retriever = Retriever()
