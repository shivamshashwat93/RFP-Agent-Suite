from groq import Groq

AVAILABLE_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "mixtral-8x7b-32768",
    "gemma2-9b-it",
]

DEFAULT_MODEL = "llama-3.3-70b-versatile"

MAX_CHAR_PER_TOKEN = 4

CONTEXT_BUDGETS = {
    "minimal": {"label": "Minimal (~2K tokens)", "ctx_chars": 8000, "prev_chars": 4000, "max_output": 2048},
    "low": {"label": "Low (~4K tokens)", "ctx_chars": 16000, "prev_chars": 8000, "max_output": 3072},
    "medium": {"label": "Medium (~8K tokens)", "ctx_chars": 32000, "prev_chars": 12000, "max_output": 4096},
    "high": {"label": "High (~16K+ tokens)", "ctx_chars": 64000, "prev_chars": 24000, "max_output": 4096},
}

DEFAULT_BUDGET = "low"


def summarize_text(client, model: str, text: str, max_chars: int, label: str = "document") -> str:
    if len(text) <= max_chars:
        return text
    chunk = text[:max_chars * 2]
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a precise summarizer. Condense the text keeping ALL key facts, requirements, numbers, and names. No fluff."},
            {"role": "user", "content": f"Summarize this {label} in under {max_chars // MAX_CHAR_PER_TOKEN} tokens. Keep every specific requirement, number, and deadline:\n\n{chunk}"},
        ],
        temperature=0.1,
        max_tokens=max_chars // MAX_CHAR_PER_TOKEN,
    )
    return resp.choices[0].message.content


class BaseAgent:
    name: str = ""
    description: str = ""
    system_prompt: str = ""

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL, budget: str = DEFAULT_BUDGET):
        self.client = Groq(api_key=api_key)
        self.model_name = model
        self.budget_cfg = CONTEXT_BUDGETS.get(budget, CONTEXT_BUDGETS[DEFAULT_BUDGET])

    def _truncate(self, text: str, max_chars: int) -> str:
        if len(text) <= max_chars:
            return text
        return text[:max_chars] + "\n\n[... truncated ...]"

    def run(self, user_input: str, context: str = "") -> str:
        max_ctx = self.budget_cfg["ctx_chars"]
        max_output = self.budget_cfg["max_output"]

        if context:
            context = self._truncate(context, max_ctx)
            user_input = self._truncate(user_input, max_ctx // 4)
            prompt = f"CONTEXT:\n{context}\n\nUSER REQUEST:\n{user_input}"
        else:
            prompt = self._truncate(user_input, max_ctx)

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=max_output,
        )
        return response.choices[0].message.content
