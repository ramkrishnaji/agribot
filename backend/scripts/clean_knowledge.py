import json
import re
from pathlib import Path

# Load existing knowledge base
# Adjusted path to match root-relative path if run from root or script location
kb_path = Path("backend/knowledge.json")
if not kb_path.exists():
    kb_path = Path("knowledge.json")

with open(kb_path, "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"Total entries before cleaning: {len(data)}")

# Step 1: Remove noise — content irrelevant to Indian farmer queries
NOISE_KEYWORDS = [
    # Global news unrelated to Indian farmers
    "gaza", "brazil fmd", "mexico", "screwworm", "woah", "paris",
    # International orgs/events not useful for farmers
    "fao food price index", "microsoft farmbeats", "national ffa",
    # Spiritual/motivational content
    "art of living", "gurudev", "sri sri ravi shankar", "sudarshan kriya",
    "satsang", "meditation", "pranayama",
    # Pure product advertising
    "tractorkarvan", "escorts kubota", "digitrac", "powertrac",
    "farmtrac", "kubota mu4201",
    # Workplace/HR content
    "posh act", "sexual harassment", "internal committee", "she-box",
    # Foreign country farming
    "zovawk pig", "mizoram pig", "bolivia",
]

def is_noise(text: str) -> bool:
    text_lower = text.lower()
    return any(kw in text_lower for kw in NOISE_KEYWORDS)

def is_too_short(text: str) -> bool:
    return len(text.strip().split()) < 8

def is_fragment(text: str) -> bool:
    # Sentences that are clearly incomplete fragments
    fragment_patterns = [
        r"^read on to",
        r"^click here",
        r"^also read",
        r"^source\s*[-–]",
        r"^\(",
        r"^note:",
        r"^join gfbn",
    ]
    text_lower = text.strip().lower()
    return any(re.match(p, text_lower) for p in fragment_patterns)

# Filter
cleaned = []
removed = []

for entry in data:
    text = entry if isinstance(entry, str) else str(entry)
    
    if is_noise(text):
        removed.append(("noise", text[:80]))
    elif is_too_short(text):
        removed.append(("too_short", text[:80]))
    elif is_fragment(text):
        removed.append(("fragment", text[:80]))
    else:
        cleaned.append(text)

print(f"Removed: {len(removed)}")
print(f"Remaining: {len(cleaned)}")

# Step 2: Group sentences into chunks of 4-5 sentences
# Group consecutive sentences that likely belong together
def chunk_sentences(sentences: list, chunk_size: int = 4) -> list:
    chunks = []
    for i in range(0, len(sentences), chunk_size):
        group = sentences[i:i + chunk_size]
        combined = " ".join(group).strip()
        if len(combined.split()) >= 30:  # skip tiny chunks
            chunks.append(combined)
    return chunks

chunks = chunk_sentences(cleaned, chunk_size=4)
print(f"Total chunks after grouping: {len(chunks)}")

# Step 3: Tag each chunk
def tag_chunk(text: str) -> list:
    text_lower = text.lower()
    tags = []

    crop_keywords = [
        "wheat", "rice", "paddy", "cotton", "maize", "sugarcane",
        "potato", "tomato", "chili", "mango", "banana", "pulse",
        "soybean", "mustard", "groundnut", "barley", "jowar", "bajra",
        "arhar", "moong", "urad", "chickpea", "lentil", "tea", "coffee",
        "rubber", "coconut", "spice", "turmeric", "ginger", "onion"
    ]
    disease_keywords = [
        "disease", "pest", "blight", "wilt", "rot", "aphid", "fungus",
        "bacterial", "virus", "insect", "hopper", "armyworm", "mite",
        "nematode", "spray", "fungicide", "pesticide", "ipm", "treatment"
    ]
    scheme_keywords = [
        "pm-kisan", "pmfby", "pkvy", "rkvy", "nmsa", "pmksy", "kcc",
        "kisan credit", "subsidy", "scheme", "yojana", "insurance",
        "government", "benefit", "eligibility", "application"
    ]
    irrigation_keywords = [
        "irrigation", "drip", "water", "rainfall", "monsoon", "aquifer",
        "groundwater", "canal", "tube well", "moisture", "drought"
    ]
    market_keywords = [
        "price", "msp", "mandi", "market", "export", "trade", "income",
        "profit", "cost", "revenue", "sell", "buyer", "enam", "agmarknet"
    ]
    soil_keywords = [
        "soil", "fertilizer", "nutrient", "nitrogen", "phosphorus",
        "potassium", "organic", "compost", "manure", "ph", "alluvial",
        "black soil", "red soil", "laterite"
    ]
    regional_keywords = [
        "punjab", "haryana", "maharashtra", "gujarat", "karnataka",
        "andhra pradesh", "telangana", "uttar pradesh", "madhya pradesh",
        "rajasthan", "bihar", "west bengal", "tamil nadu", "kerala",
        "odisha", "assam", "himachal", "uttarakhand", "jharkhand"
    ]

    if any(w in text_lower for w in crop_keywords):
        tags.append("crop")
    if any(w in text_lower for w in disease_keywords):
        tags.append("disease_pest")
    if any(w in text_lower for w in scheme_keywords):
        tags.append("scheme")
    if any(w in text_lower for w in irrigation_keywords):
        tags.append("irrigation")
    if any(w in text_lower for w in market_keywords):
        tags.append("market")
    if any(w in text_lower for w in soil_keywords):
        tags.append("soil")
    if any(w in text_lower for w in regional_keywords):
        tags.append("regional")

    return tags if tags else ["general"]

# Build final structured dataset
structured = []
for chunk in chunks:
    structured.append({
        "text": chunk,
        "tags": tag_chunk(chunk),
        "source": "icar_gov"
    })

# Save cleaned knowledge base
output_path = Path("backend/knowledge_cleaned.json")
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(structured, f, ensure_ascii=False, indent=2)

print(f"\nDone. Saved {len(structured)} chunks to {output_path}")
print("\nTag distribution:")
from collections import Counter
all_tags = [tag for entry in structured for tag in entry["tags"]]
for tag, count in Counter(all_tags).most_common():
    print(f"  {tag}: {count}")
