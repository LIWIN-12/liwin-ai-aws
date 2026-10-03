"""Manual live Gemini generation diagnostic; it is safe to import."""

from __future__ import annotations

from backend.config import get_settings
from backend.llm.gemini import generate


def main() -> None:
    settings = get_settings()
    answer = generate("Reply with exactly: Gemini generation check passed.")
    print(f"Model: {settings.gemini_generation_model}")
    print(answer)


if __name__ == "__main__":
    main()
