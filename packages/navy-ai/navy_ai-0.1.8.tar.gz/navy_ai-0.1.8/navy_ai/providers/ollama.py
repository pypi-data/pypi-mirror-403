import httpx


class OllamaProvider:
    def __init__(self, model: str | None = None):
        self.model = model or "mistral"
        self.url = "http://localhost:11434/api/chat"

    def chat(self, prompt: str) -> str:
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        }

        try:
            r = httpx.post(self.url, json=payload, timeout=10)
            r.raise_for_status()
            return r.json()["message"]["content"]

        except httpx.ConnectError:
            raise RuntimeError(
                "Ollama is not running.\n"
                "Start it with: ollama serve\n"
                "Or install a model with: ollama pull mistral"
            )

        except httpx.ReadTimeout:
            raise RuntimeError(
                "Ollama request timed out.\n"
                "The model may still be loading.\n"
                "Try again in a few seconds."
            )

        except httpx.HTTPStatusError as e:
            raise RuntimeError(
                f"Ollama returned an error ({e.response.status_code})."
            )

        except Exception:
            raise RuntimeError(
                "Unexpected error while talking to Ollama."
            )
