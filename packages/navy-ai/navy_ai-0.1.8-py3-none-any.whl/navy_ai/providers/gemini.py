import httpx
from navy_ai.providers.base import AIProvider
from navy_ai.config import get_api_key

class GeminiProvider(AIProvider):
    def __init__(self, model: str | None = None):
        self.api_key = get_api_key("GEMINI_API_KEY")
        if not self.api_key:
            raise RuntimeError(
                "❌ GEMINI_API_KEY not set.\n"
                "Create one at https://aistudio.google.com/app/apikey"
            )

        self.model = model or "gemini-2.5-flash"
        self.url = (
            f"https://generativelanguage.googleapis.com/v1/"
            f"models/{self.model}:generateContent"
        )

    def chat(self, prompt: str) -> str:
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key,
        }

        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}]
        }

        try:
            r = httpx.post(self.url, headers=headers, json=payload, timeout=30)
            r.raise_for_status()
            return r.json()["candidates"][0]["content"]["parts"][0]["text"]
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"❌ Gemini error: HTTP {e.response.status_code}")
