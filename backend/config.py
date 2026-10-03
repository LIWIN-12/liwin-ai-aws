"""Central configuration for Liwin AI.

All paths are anchored to the project root so the application behaves the same
when it is launched from a process manager, Docker, or the repository root.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _positive_int(name: str, default: int) -> int:
    value = os.getenv(name, str(default))
    try:
        parsed = int(value)
    except ValueError as error:
        raise ValueError(f"{name} must be an integer.") from error
    if parsed < 1:
        raise ValueError(f"{name} must be greater than zero.")
    return parsed


def _csv(name: str, default: tuple[str, ...]) -> tuple[str, ...]:
    value = os.getenv(name)
    if value is None:
        return default
    return tuple(item.strip() for item in value.split(",") if item.strip())


@dataclass(frozen=True)
class Settings:
    chroma_path: Path
    collection_name: str
    knowledge_path: Path
    memory_path: Path
    embedding_model: str
    embedding_dimensions: int
    gemini_generation_model: str
    llm_providers: tuple[str, ...]
    allowed_origins: tuple[str, ...]
    memory_max_messages: int
    memory_retention_days: int
    request_limit: int
    request_window_seconds: int
    max_context_characters: int


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return validated, environment-backed application settings."""

    return Settings(
        chroma_path=Path(os.getenv("CHROMA_PATH", BASE_DIR / "chroma_db")),
        collection_name=os.getenv("CHROMA_COLLECTION", "liwin"),
        knowledge_path=Path(os.getenv("KNOWLEDGE_PATH", BASE_DIR / "knowledge")),
        memory_path=Path(os.getenv("MEMORY_DB_PATH", BASE_DIR / "liwin_memory.db")),
        embedding_model=os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001"),
        embedding_dimensions=_positive_int("GEMINI_EMBEDDING_DIMENSIONS", 768),
        gemini_generation_model=os.getenv("GEMINI_GENERATION_MODEL", "gemini-3.8-flash"),
        llm_providers=_csv("LLM_PROVIDERS", ("gemini", "openrouter", "groq")),
        allowed_origins=_csv(
            "ALLOWED_ORIGINS",
            ("http://127.0.0.1:5500", "http://localhost:5500"),
        ),
        memory_max_messages=_positive_int("MEMORY_MAX_MESSAGES", 10),
        memory_retention_days=_positive_int("MEMORY_RETENTION_DAYS", 30),
        request_limit=_positive_int("RATE_LIMIT_REQUESTS", 30),
        request_window_seconds=_positive_int("RATE_LIMIT_WINDOW_SECONDS", 60),
        max_context_characters=_positive_int("MAX_CONTEXT_CHARACTERS", 8000),
    )
