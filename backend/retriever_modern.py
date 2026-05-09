import os
import json
from retriever import retrieve

def search_modern_kb(query: str) -> list[dict]:
    """
    Simple keyword search on structured knowledge base.
    Returns full Expert Cards, not just text.
    """
    try:
        kb_path = os.path.join(os.path.dirname(__file__), "knowledge_modern.json")
        with open(kb_path, encoding='utf-8') as f:
            kb = json.load(f)
    except Exception as e:
        print(f"Error loading modern KB: {e}")
        return []
    
    query_lower = query.lower()
    
    # Keywords to card mapping
    keyword_map = {
        "polyhouse": ["infra_polyhouse_nv", "infra_polyhouse_fanpad"],
        "greenhouse": ["infra_polyhouse_nv", "infra_polyhouse_fanpad"],
        "dragon fruit": ["crop_dragon_fruit"],
        "pitaya": ["crop_dragon_fruit"],
        "kamalam": ["crop_dragon_fruit"],
        "capsicum": ["crop_capsicum_polyhouse"],
        "shimla mirch": ["crop_capsicum_polyhouse"],
        "nhb": ["subsidy_nhb_scheme1", "infra_polyhouse_nv", "infra_polyhouse_fanpad"],
        "subsidy": ["subsidy_nhb_scheme1", "infra_polyhouse_nv", "infra_polyhouse_fanpad", "crop_dragon_fruit"],
        "scheme": ["subsidy_nhb_scheme1"],
        "fan pad": ["infra_polyhouse_fanpad"],
        "cold storage": ["subsidy_nhb_scheme1"],
    }
    
    matched_ids = set()
    for keyword, ids in keyword_map.items():
        if keyword in query_lower:
            matched_ids.update(ids)
    
    return [card for card in kb if card["id"] in matched_ids]

def retrieve_with_source(query: str, top_k: int = 5) -> dict:
    """
    Returns results from both vector DB (scraped articles) 
    and structured modern knowledge base.
    """
    # Existing vector search
    vector_results = retrieve(query, top_k=top_k)
    
    # Structured knowledge base search
    modern_results = search_modern_kb(query)
    
    # Convert modern results to a readable string for the LLM
    structured_context = ""
    if modern_results:
        structured_context = "--- HIGH PRECISION DATA (FROM OFFICIAL PDFS) ---\n"
        structured_context += json.dumps(modern_results, indent=2)
        structured_context += "\n--- END HIGH PRECISION DATA ---\n"

    return {
        "context": structured_context + "\n" + "\n".join(vector_results),
        "has_financial_data": len(modern_results) > 0
    }
