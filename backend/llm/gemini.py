"""Gemini text generation provider."""

from __future__ import annotations

import os

from google import genai
from google.genai import types

from backend.config import get_settings


def generate(prompt: str) -> str:
    """Generate a concise portfolio answer with the configured Gemini model."""

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set.")

    settings = get_settings()
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=settings.gemini_generation_model,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.3,
            max_output_tokens=700,
        ),
    )
    return (response.text or "").strip()
