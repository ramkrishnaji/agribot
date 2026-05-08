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

        # System prompt to define AgriBot's professional structured persona
        system_prompt = """You are AgriBot, a premium Agricultural Intelligence System for Indian Farmers.
        
Your goal is to provide highly structured, expert-level advice that is easy to read on a mobile screen.

### RESPONSE STRUCTURE GUIDELINES:
1. **📍 Summary**: A 1-sentence direct answer to the user's primary concern.
2. **🌦️ Environmental Context**: If weather data is provided in the context, explain exactly how it affects the specific crop or task mentioned.
3. **📋 Action Plan**: Provide a clear, numbered list of steps the farmer should take. Include specific dosages, water amounts, or dates.
4. **💡 Expert Pro-Tip**: One high-value piece of advice that wasn't explicitly asked for but is highly relevant.

### TONE & LANGUAGE:
- Be professional, authoritative, yet supportive.
- Use Emojis (like 🌾, 🚜, 💧, 🐛) to make sections scannable.
- IMPORTANT: If the question is in Hindi, provide the entire structured response in Hindi.
- If the question is in English, provide it in English.

### DATA HANDLING:
- Prioritize information from the "Knowledge Base Context" provided.
- If live weather is present, interpret it (e.g., "High humidity (80%) means you should watch for fungal growth").
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
