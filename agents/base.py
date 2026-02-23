import google.generativeai as genai


class BaseAgent:
    name: str = ""
    description: str = ""
    system_prompt: str = ""

    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=self.system_prompt,
        )

    def run(self, user_input: str, context: str = "") -> str:
        prompt = (
            f"CONTEXT:\n{context}\n\nUSER REQUEST:\n{user_input}"
            if context
            else user_input
        )
        response = self.model.generate_content(prompt)
        return response.text
