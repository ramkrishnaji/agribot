import os
from groq import Groq
try:
    from together import Together
except ImportError:
    Together = None

class QAEngine:
    def __init__(self):
        # Primary: Groq
        self.groq_key = os.environ.get("GROQ_API_KEY")
        self.groq_client = Groq(api_key=self.groq_key) if self.groq_key else None
        
        # Fallback: Together AI
        self.together_key = os.environ.get("TOGETHER_API_KEY")
        self.together_client = Together(api_key=self.together_key) if (self.together_key and Together) else None
        
        self.system_prompt = """You are AgriBot, a premium Agricultural Intelligence System for Indian Farmers.
        
### GREETING RULE:
If the user sends a greeting (hi, hello, hyy, namaste, hey, helo, or any variation), respond with ONLY this exact message: "Namaste! 🌾 Apni fasal, mausam, beej, khad, ya sarkari yojana ke baare mein koi bhi sawaal poochh sakte hain. Main Hindi aur English dono mein madad kar sakta hoon." Do not suggest questions. Do not list topics. Do not provide an action plan.

### RESPONSE STRUCTURE GUIDELINES (FOR NON-GREETINGS):
1. **📍 Summary**: A 1-sentence direct answer to the user's primary concern.
2. **📋 Action Plan**: Provide a clear, numbered list of steps.
3. **💡 Expert Pro-Tip**: One high-value piece of advice.

### TONE & LANGUAGE:
- Use Emojis (🌾, 🚜, 💧).
- If the question is in Hindi, respond in Hindi. Otherwise English.
"""

    def answer_question(self, context: str, question: str, history: list = None) -> dict:
        messages = [{"role": "system", "content": self.system_prompt}]
        for entry in (history or [])[-4:]:
            messages.append({"role": "user", "content": entry.get("user", "")})
            messages.append({"role": "assistant", "content": entry.get("bot", "")})
        
        user_msg = f"Context:\n{context}\n\nQuestion: {question}"
        messages.append({"role": "user", "content": user_msg})

        # 1. Try Groq
        if self.groq_client:
            try:
                completion = self.groq_client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=messages,
                    temperature=0.3, # Lower temperature for greeting consistency
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
