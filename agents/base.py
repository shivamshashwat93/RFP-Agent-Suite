from groq import Groq

AVAILABLE_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "mixtral-8x7b-32768",
    "gemma2-9b-it",
]

DEFAULT_MODEL = "llama-3.3-70b-versatile"

MODEL_CTX_LIMITS = {
    "llama-3.3-70b-versatile": 120000,
    "llama-3.1-8b-instant": 120000,
    "mixtral-8x7b-32768": 28000,
    "gemma2-9b-it": 6000,
}

MAX_CHAR_PER_TOKEN = 4


class BaseAgent:
    name: str = ""
    description: str = ""
    system_prompt: str = ""

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL):
        self.client = Groq(api_key=api_key)
        self.model_name = model

    def _truncate(self, text: str, max_tokens: int) -> str:
        max_chars = max_tokens * MAX_CHAR_PER_TOKEN
        if len(text) <= max_chars:
            return text
        return text[:max_chars] + "\n\n[... document truncated to fit model context window ...]"

    def run(self, user_input: str, context: str = "") -> str:
        ctx_limit = MODEL_CTX_LIMITS.get(self.model_name, 6000)
        system_tokens = len(self.system_prompt) // MAX_CHAR_PER_TOKEN
        available = ctx_limit - system_tokens - 4096

        if context:
            context = self._truncate(context, int(available * 0.8))
            user_input = self._truncate(user_input, int(available * 0.2))
            prompt = f"CONTEXT:\n{context}\n\nUSER REQUEST:\n{user_input}"
        else:
            prompt = self._truncate(user_input, available)

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
