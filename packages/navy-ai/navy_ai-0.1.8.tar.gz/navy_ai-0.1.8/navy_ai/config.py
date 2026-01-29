import os

def get_api_key(name: str) -> str | None:
    return os.environ.get(name)
