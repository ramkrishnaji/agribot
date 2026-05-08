from groq import Groq
import os


class GroqModel:
    def __init__(self):
        # We look for GROQ_API_KEY now
        api_key = os.environ.get("GROQ_API_KEY", "")
        if api_key:
            self.client = Groq(api_key=api_key)
            self.model_name = "llama-3.1-8b-instant"
            self.ready = True
            print(f"Groq Model ({self.model_name}) loaded successfully.")
        else:
            print("WARNING: GROQ_API_KEY not set. Model will not respond.")
            self.ready = False

    def answer_question(self, context: str, question: str, history: list = None) -> dict:
        if not self.ready:
            return {
                "answer": "The Groq AI model is not configured. Please set GROQ_API_KEY.",
                "score": 0.0,
                "error": "No API key",
            }

        if history is None:
            history = []

        # System prompt to define AgriBot persona
        system_prompt = """You are AgriBot, an expert agricultural assistant for Indian farmers.
        
Your expertise covers:
- Indian government schemes: PM-KISAN, PMFBY, KCC, e-NAM, Soil Health Card, etc.
- Crop cultivation for Kharif, Rabi, and Zaid seasons.
- Soil health, irrigation (drip, sprinkler), and pest/disease management.
- Market prices (MSP) and mandi strategies.

Response guidelines:
- Give DETAILED, actionable answers with clear structure (bullet points).
- Include specific dosages, dates, and amounts.
- Cite the provided knowledge base if relevant.
- Be warm, encouraging, and supportive.
- Respond in Hindi if the question is in Hindi.
"""

        # Format conversation history for Groq
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add past context (last 4 turns)
        for entry in history[-4:]:
            messages.append({"role": "user", "content": entry.get("user", "")})
            messages.append({"role": "assistant", "content": entry.get("bot", "")})
            
        # Current RAG context + Question
        user_message = f"Knowledge Base Context:\n{context}\n\nQuestion: {question}"
        messages.append({"role": "user", "content": user_message})

        try:
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.7,
                max_tokens=2048,
                top_p=1,
                stream=False,
            )
            
            return {
                "answer": completion.choices[0].message.content,
                "score": 1.0,
                "error": None,
            }
        except Exception as e:
            return {
                "answer": "I'm having a technical issue with Groq. Please try again.",
                "score": 0.0,
                "error": str(e),
            }


# Singleton
qa_model = GroqModel()
