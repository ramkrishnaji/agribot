import os
import json
from groq import Groq
try:
    from together import Together
except ImportError:
    Together = None

BUDGET_TO_RECOMMENDATION = [
    {
        "max_budget_lakh": 2,
        "recommendations": [
            {
                "crop": "Dragon Fruit",
                "reason": "Low setup cost, drought tolerant, 25-year productive life",
                "area": "0.4–0.5 acre open field",
                "subsidy": "Check state NHM scheme"
            },
            {
                "crop": "Vegetables (open field)",
                "reason": "Quick returns in 60–90 days",
                "area": "0.5–1 acre",
                "subsidy": "PM-KISAN for input support"
            }
        ]
    },
    {
        "max_budget_lakh": 5,
        "recommendations": [
            {
                "crop": "Dragon Fruit",
                "reason": "Full 1-acre setup possible",
                "area": "1 acre",
                "subsidy": "State NHM scheme"
            },
            {
                "crop": "Shade Net Vegetables",
                "reason": "Better quality than open field, lower cost than polyhouse",
                "area": "500 sqm",
                "subsidy": "NHB Scheme 1 — 40–50% back-ended"
            }
        ]
    },
    {
        "max_budget_lakh": 15,
        "recommendations": [
            {
                "crop": "Capsicum (Coloured) in NV Polyhouse",
                "reason": "High value crop, ₹60–120/kg, NHB subsidy available",
                "area": "500–1000 sqm polyhouse",
                "subsidy": "NHB Scheme 1 — 40–50% of project cost"
            },
            {
                "crop": "Tomato / Cucumber in Polyhouse",
                "reason": "Steady demand, consistent price",
                "area": "500 sqm",
                "subsidy": "NHB Scheme 1"
            }
        ]
    },
    {
        "max_budget_lakh": 50,
        "recommendations": [
            {
                "crop": "Coloured Capsicum / Exotic Flowers in Fan & Pad Polyhouse",
                "reason": "Premium crop, controlled environment, highest returns",
                "area": "2000–4000 sqm polyhouse",
                "subsidy": "NHB Scheme 1 — up to ₹56–70L subsidy"
            }
        ]
    }
]

class QAEngine:
    def __init__(self):
        # Primary: Groq
        self.groq_key = os.environ.get("GROQ_API_KEY")
        self.groq_client = Groq(api_key=self.groq_key) if self.groq_key else None
        
        # Fallback: Together AI
        self.together_key = os.environ.get("TOGETHER_API_KEY")
        self.together_client = Together(api_key=self.together_key) if (self.together_key and Together) else None
        
        self.system_prompt = f"""You are AgriBot Beta, an Expert Agricultural Project Consultant for Indian Farmers.

### LANGUAGE & TONE RULE:
- **Language**: ALWAYS respond in English ONLY. 
- **Simplicity**: Use simple, clear English. Avoid complex jargon.
- **Enforcement**: If the user writes in Hindi or any other language, your ONLY response must be: "I currently support English only. Please rephrase your question in English."
- **Currency**: ALWAYS use Indian numbering for amounts (e.g., ₹2 lakh instead of ₹200,000, ₹1 crore instead of ₹10,000,000).
- **Tone**: Professional, encouraging, and emoji-friendly (🌾, 🚜, 💰).

### GREETING RULE:
If the user sends a greeting (hi, hello, etc.), respond with: "Hello! 🌾 I am your Modern Agriculture Consultant. I can help you with high-ROI crops (like Dragon Fruit), Polyhouse investments, live weather, and government subsidies (NHB/NHM). How can I assist you in English today?"

### SPECIAL BEHAVIOR — SUBSIDY AND SCHEME QUERIES:
When a farmer asks about any government scheme, subsidy, or wants to set up a polyhouse/greenhouse/cold storage, do NOT give a full answer immediately.
Instead, follow this ELIGIBILITY CHECKER flow (ask ONE question at a time in English):
1. Ask "Which state are you from?" (To determine 40% vs 50% subsidy)
2. Ask "How much land do you have — owned or 10-year registered lease?"
3. Ask "Do you have a bank account and are you interested in taking a loan?" (NHB is credit-linked)
4. Ask "What is your approximate budget?"

Only after getting these answers, use the provided context to calculate their setup cost, net investment after subsidy, and ROI.

### REVERSE CALCULATOR (If user mentions budget):
Use this logic to recommend options if the user is unsure:
{json.dumps(BUDGET_TO_RECOMMENDATION, indent=2)}

### RESPONSE STRUCTURE (FOR NON-GREETINGS):
1. **📍 Summary**: Direct 1-sentence answer in English.
2. **📋 Action Plan**: Clear numbered steps.
3. **💰 Financial Outlook**: Specifically mention costs and subsidy in LAKHS.
4. **⚠️ Critical Warning**: "Do not start any construction BEFORE receiving the IPA (In-Principle Approval) from the NHB scheme — otherwise, you will be automatically disqualified for the subsidy."

### FINANCIAL DATA RULE:
Whenever you provide any cost or subsidy figure, ALWAYS end with:
"📋 Source: [Name of Source from Context]
✅ Verify latest figures at: [Verify URL from Context]
⚠️ Costs and subsidy percentages may change annually. Always confirm with your nearest NHB/State Horticulture office."
"""

    def answer_question(self, context: str, question: str, history: list = None) -> dict:
        messages = [{"role": "system", "content": self.system_prompt}]
        for entry in (history or [])[-6:]:
            messages.append({"role": "user", "content": entry.get("user", "")})
            messages.append({"role": "assistant", "content": entry.get("bot", "")})
        
        user_msg = f"CONTEXT DATA (Verified PDFs):\n{context}\n\nUSER QUESTION: {question}"
        messages.append({"role": "user", "content": user_msg})

        # 1. Try Groq
        if self.groq_client:
            try:
                completion = self.groq_client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=messages,
                    temperature=0.3,
                )
                return {"answer": completion.choices[0].message.content, "score": 1.0}
            except Exception as e:
                print(f"Groq failed: {e}. Trying fallback...")

        # 2. Try Together AI Fallback
        if self.together_client:
            try:
                completion = self.together_client.chat.completions.create(
                    model="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
                    messages=messages,
                    temperature=0.3,
                )
                return {"answer": completion.choices[0].message.content, "score": 0.9}
            except Exception as e:
                print(f"Together AI failed: {e}")

        return {
            "answer": "I'm experiencing high traffic. Please try again in a moment.",
            "score": 0.0,
            "error": "All AI providers failed or not configured."
        }

# Singleton
qa_model = QAEngine()
