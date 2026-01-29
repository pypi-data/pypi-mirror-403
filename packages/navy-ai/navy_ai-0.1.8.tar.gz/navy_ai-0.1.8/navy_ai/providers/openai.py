import httpx
from navy_ai.providers.base import AIProvider
from navy_ai.config import get_api_key

class OpenAIProvider(AIProvider):
    def __init__(self, model: str = "gpt-3.5-turbo"):
        self.api_key = get_api_key("OPENAI_API_KEY")
        if not self.api_key:
            raise RuntimeError(
                "❌ OPENAI_API_KEY not set.\n"
                "Set it or use the free Ollama provider."
            )

        self.model = model
        self.url = "https://api.openai.com/v1/chat/completions"

    def chat(self, prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
        }

        try:
            r = httpx.post(self.url, headers=headers, json=payload, timeout=30)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                raise RuntimeError(
                    "❌ OpenAI rate-limited or billing not enabled.\n"
                    "Enable billing or use Ollama."
                )
            raise RuntimeError(f"❌ OpenAI error: HTTP {e.response.status_code}")
