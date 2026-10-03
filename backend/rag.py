"""Gemini embedding and Chroma retrieval helpers."""

from __future__ import annotations

import os
import logging
import re
import time
from functools import lru_cache

import chromadb
from chromadb.config import Settings as ChromaSettings
from google import genai
from google.genai import types

from backend.config import get_settings


logger = logging.getLogger("liwin-ai.rag")
LATEST_RESUME_SOURCE = "resume_latest.md"
RESUME_SUBJECTS = {
    "certification", "contact", "education", "experience", "project", "role", "skill"
}


class KnowledgeBaseNotReadyError(RuntimeError):
    """Raised when the application has not been indexed yet."""


@lru_cache(maxsize=1)
def _gemini_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set.")
    return genai.Client(api_key=api_key)


@lru_cache(maxsize=1)
def _chroma_client() -> chromadb.PersistentClient:
    settings = get_settings()
    settings.chroma_path.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(
        path=str(settings.chroma_path),
        settings=ChromaSettings(anonymized_telemetry=False),
    )


def get_collection():
    """Get the existing collection without silently creating an empty one."""

    settings = get_settings()
    try:
        return _chroma_client().get_collection(name=settings.collection_name)
    except Exception as error:
        raise KnowledgeBaseNotReadyError(
            "The knowledge base has not been indexed. Run `python -m backend.ingest`."
        ) from error


def create_embedding(text: str, task_type: str = "RETRIEVAL_QUERY") -> list[float]:
    """Create a Gemini embedding using the configured stable dimensions."""

    settings = get_settings()
    for attempt in range(3):
        try:
            response = _gemini_client().models.embed_content(
                model=settings.embedding_model,
                contents=text,
                config=types.EmbedContentConfig(
                    task_type=task_type,
                    output_dimensionality=settings.embedding_dimensions,
                ),
            )
            if not response.embeddings:
                raise RuntimeError("Gemini returned no embedding.")
            return list(response.embeddings[0].values)
        except Exception as error:
            status_code = getattr(error, "status_code", None)
            retryable = not isinstance(error, RuntimeError) and (
                status_code is None or status_code == 429 or status_code >= 500
            )
            if not retryable or attempt == 2:
                raise
            delay = 2**attempt
            logger.warning(
                "Gemini embedding request failed; retrying in %s second(s).", delay
            )
            time.sleep(delay)

    raise RuntimeError("Gemini embedding retry loop ended unexpectedly.")


def _keywords(text: str) -> set[str]:
    """Return simple normalized terms for a small lexical reranking signal."""

    ignored = {
        "about", "and", "are", "does", "for", "from", "have", "how", "liwin",
        "my", "of", "the", "to", "what", "with", "your",
    }
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {
        word.rstrip("s")
        for word in words
        if len(word) > 2 and word not in ignored
    }


def search(query: str, k: int = 3) -> list[str]:
    """Return relevant chunks with semantic retrieval and a lightweight lexical boost."""

    if not query or not query.strip():
        return []

    collection = get_collection()
    count = collection.count()
    if count == 0:
        raise KnowledgeBaseNotReadyError(
            "The knowledge base is empty. Run `python -m backend.ingest`."
        )

    candidate_count = min(max(k * 4, 12), count)
    results = collection.query(
        query_embeddings=[create_embedding(query)],
        n_results=candidate_count,
        include=["documents", "metadatas"],
    )
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    query_terms = _keywords(query)
    scored: list[tuple[int, int, str]] = []

    def relevance_score(document: str, source: str) -> int:
        document_terms = _keywords(document)
        source_overlap = len(query_terms & _keywords(source))
        headings = " ".join(
            line.lstrip("# ") for line in document.splitlines() if line.startswith("#")
        )
        heading_overlap = len(query_terms & _keywords(headings))
        document_overlap = len(query_terms & document_terms)
        resume_boost = (
            10
            if source == LATEST_RESUME_SOURCE and query_terms & RESUME_SUBJECTS
            else 0
        )
        return source_overlap * 8 + heading_overlap * 6 + document_overlap * 2 + resume_boost

    seen_documents: set[str] = set()
    for rank, document in enumerate(documents):
        if not document:
            continue
        metadata = metadatas[rank] if rank < len(metadatas) else {}
        source = str(metadata.get("source", "")) if metadata else ""
        scored.append((relevance_score(document, source), -rank, document))
        seen_documents.add(document)

    # A personal knowledge base can safely scan its compact corpus for direct
    # subject matches. This prevents a short, precise resume section from
    # being excluded by semantic recall alone.
    all_results = collection.get(include=["documents", "metadatas"])
    for document, metadata in zip(
        all_results.get("documents", []), all_results.get("metadatas", [])
    ):
        if not document or document in seen_documents:
            continue
        source = str(metadata.get("source", "")) if metadata else ""
        scored.append(
            (relevance_score(document, source), -candidate_count, document)
        )

    scored.sort(reverse=True)
    return [document for _, _, document in scored[: min(max(k, 1), len(scored))]]
