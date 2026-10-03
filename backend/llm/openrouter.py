import os
import requests

from backend.config import get_settings


OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

DEFAULT_MODEL = "openai/gpt-oss-20b:free"


def generate(prompt: str) -> str:
    get_settings()
    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not set.")

    response = requests.post(
        OPENROUTER_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": os.getenv("OPENROUTER_MODEL", DEFAULT_MODEL),
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            "temperature": 0.3,
            "max_tokens": 700,
        },
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    if "choices" not in data or not data["choices"]:
        raise RuntimeError(
            f"Invalid OpenRouter response: {data}"
        )

    message = data["choices"][0].get("message", {})

    answer = message.get("content")

    if not answer:
        raise RuntimeError(
            f"OpenRouter returned empty content: {data}"
        )

    return answer.strip()
