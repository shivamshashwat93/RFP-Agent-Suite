from groq import Groq

AVAILABLE_MODELS = [
    "gemma2-9b-it",
    "gemma-7b-it",
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "mixtral-8x7b-32768",
]

DEFAULT_MODEL = "gemma2-9b-it"


class BaseAgent:
    name: str = ""
    description: str = ""
    system_prompt: str = ""

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL):
        self.client = Groq(api_key=api_key)
        self.model_name = model

    def run(self, user_input: str, context: str = "") -> str:
        prompt = (
            f"CONTEXT:\n{context}\n\nUSER REQUEST:\n{user_input}"
            if context
            else user_input
        )
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=4096,
        )
        return response.choices[0].message.content
