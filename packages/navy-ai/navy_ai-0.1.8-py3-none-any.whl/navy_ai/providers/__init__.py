from navy_ai.providers.ollama import OllamaProvider
from navy_ai.providers.gemini import GeminiProvider
from navy_ai.providers.openai import OpenAIProvider

def load_provider(name: str, model: str | None = None):
    name = name.lower()

    if name == "ollama":
        return OllamaProvider(model)
    if name == "gemini":
        return GeminiProvider(model)
    if name == "openai":
        return OpenAIProvider(model)

    raise RuntimeError(f"❌ Unknown provider: {name}")
