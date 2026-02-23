import subprocess
import tempfile
import os

AVAILABLE_MODELS = [
    "gemini-3-flash-preview",
    "claude-haiku-4-5-20251001",
    "glm-4.7",
    "glm-5",
    "claude-sonnet-4-6",
    "claude-opus-4-6-fast",
    "gemini-3-pro-preview",
]

DEFAULT_MODEL = "gemini-3-flash-preview"

MAX_CONTEXT_CHARS = 60000


def call_droid(prompt: str, model: str = DEFAULT_MODEL, timeout: int = 180) -> str:
    fd, prompt_file = tempfile.mkstemp(suffix=".md", prefix="rfp_prompt_")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(prompt)

        result = subprocess.run(
            ["droid", "exec", "-f", prompt_file, "-m", model, "-o", "text", "--auto", "low"],
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
        )
        output = result.stdout.strip()
        if result.returncode != 0 and not output:
            return f"[Error] droid exec failed: {result.stderr.strip()}"
        return output
    except subprocess.TimeoutExpired:
        return "[Error] droid exec timed out. Try a faster model or shorter input."
    except FileNotFoundError:
        return "[Error] 'droid' CLI not found. Install from https://docs.factory.ai"
    finally:
        try:
            os.unlink(prompt_file)
        except OSError:
            pass


def summarize_text(text: str, max_chars: int, label: str, model: str = DEFAULT_MODEL) -> str:
    if len(text) <= max_chars:
        return text
    chunk = text[: max_chars * 2]
    prompt = (
        "You are a precise summarizer. Condense the following text keeping "
        "ALL key facts, requirements, numbers, names, and deadlines. "
        "Output only the summary, no preamble.\n\n"
        f"TEXT TO SUMMARIZE ({label}):\n{chunk}"
    )
    return call_droid(prompt, model, timeout=120)


class BaseAgent:
    name: str = ""
    description: str = ""
    system_prompt: str = ""

    def __init__(self, model: str = DEFAULT_MODEL):
        self.model_name = model

    def _truncate(self, text: str, max_chars: int) -> str:
        if len(text) <= max_chars:
            return text
        return text[:max_chars] + "\n\n[... truncated ...]"

    def run(self, user_input: str, context: str = "") -> str:
        parts = [f"INSTRUCTIONS:\n{self.system_prompt}"]

        if context:
            context = self._truncate(context, MAX_CONTEXT_CHARS)
            parts.append(f"CONTEXT:\n{context}")

        parts.append(f"USER REQUEST:\n{user_input}")

        full_prompt = "\n\n".join(parts)
        return call_droid(full_prompt, self.model_name)
