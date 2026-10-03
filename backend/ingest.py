"""Build the Chroma collection from the Markdown knowledge base.

Run explicitly after changing files under ``knowledge/``. The command fetches
all Gemini embeddings before replacing the existing collection, so a failed API
request cannot erase a working index.
"""

from __future__ import annotations

import hashlib
import logging
import uuid
from pathlib import Path

from backend.config import get_settings
from backend.rag import _chroma_client, create_embedding


logger = logging.getLogger("liwin-ai.ingest")
CHUNK_SIZE = 1800
CHUNK_OVERLAP = 250
EXCLUDED_SOURCES = {"assistant_behavior.md"}


def chunk_document(text: str, chunk_size: int = CHUNK_SIZE) -> list[str]:
    """Split Markdown into bounded, overlapping chunks at paragraph boundaries."""

    paragraphs = [paragraph.strip() for paragraph in text.split("\n\n") if paragraph.strip()]
    chunks: list[str] = []
    current = ""

    for paragraph in paragraphs:
        if len(paragraph) > chunk_size:
            words = paragraph.split()
            paragraph_parts: list[str] = []
            part = ""
            for word in words:
                candidate = f"{part} {word}".strip()
                if part and len(candidate) > chunk_size:
                    paragraph_parts.append(part)
                    part = word
                else:
                    part = candidate
            if part:
                paragraph_parts.append(part)
        else:
            paragraph_parts = [paragraph]

        for part in paragraph_parts:
            candidate = f"{current}\n\n{part}".strip()
            if current and len(candidate) > chunk_size:
                chunks.append(current)
                overlap = current[-CHUNK_OVERLAP:]
                current = f"{overlap}\n\n{part}".strip()
            else:
                current = candidate

    if current:
        chunks.append(current)
    return chunks


def load_documents(knowledge_path: Path) -> tuple[list[str], list[str], list[dict[str, object]]]:
    """Read non-empty Markdown files and return stable chunk IDs and metadata."""

    if not knowledge_path.is_dir():
        raise RuntimeError(f"Knowledge directory does not exist: {knowledge_path}")

    ids: list[str] = []
    documents: list[str] = []
    metadatas: list[dict[str, object]] = []
    for path in sorted(knowledge_path.glob("*.md")):
        if path.name in EXCLUDED_SOURCES:
            logger.info("Skipping non-reference knowledge file: %s", path.name)
            continue
        content = path.read_text(encoding="utf-8").strip()
        if not content:
            logger.info("Skipping empty knowledge file: %s", path.name)
            continue
        for index, chunk in enumerate(chunk_document(content)):
            digest = hashlib.sha256(chunk.encode("utf-8")).hexdigest()[:12]
            ids.append(f"{path.stem}-{index}-{digest}")
            documents.append(chunk)
            metadatas.append({"source": path.name, "chunk": index})

    if not documents:
        raise RuntimeError("No non-empty Markdown knowledge files were found.")
    return ids, documents, metadatas


def build_index() -> int:
    """Create and verify a replacement collection, retaining the old one on failure."""

    settings = get_settings()
    ids, documents, metadatas = load_documents(settings.knowledge_path)
    logger.info("Creating embeddings for %s chunks.", len(documents))
    embeddings = [create_embedding(document, "RETRIEVAL_DOCUMENT") for document in documents]

    temporary_name = f"{settings.collection_name}_staging_{uuid.uuid4().hex[:10]}"
    client = _chroma_client()
    staging = client.create_collection(
        name=temporary_name,
        metadata={
            "embedding_model": settings.embedding_model,
            "embedding_dimensions": settings.embedding_dimensions,
        },
    )
    previous_name: str | None = None
    try:
        staging.add(ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas)
        if staging.count() != len(documents):
            raise RuntimeError("Staging collection verification failed.")

        try:
            previous = client.get_collection(settings.collection_name)
            previous_name = f"{settings.collection_name}_backup_{uuid.uuid4().hex[:10]}"
            previous.modify(name=previous_name)
        except Exception:
            previous_name = None
        staging.modify(name=settings.collection_name)
        if previous_name:
            client.delete_collection(previous_name)
    except Exception:
        try:
            client.delete_collection(temporary_name)
        except Exception:
            logger.warning("Could not remove failed staging collection: %s", temporary_name)
        if previous_name:
            try:
                client.get_collection(previous_name).modify(name=settings.collection_name)
            except Exception:
                logger.exception("Could not restore the previous knowledge collection.")
        raise

    logger.info(
        "Indexed %s chunks from %s Markdown files with %s (%s dimensions).",
        len(documents),
        len({metadata["source"] for metadata in metadatas}),
        settings.embedding_model,
        settings.embedding_dimensions,
    )
    return len(documents)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    build_index()
