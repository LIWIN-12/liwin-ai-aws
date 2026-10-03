"""Initialize an empty persistent knowledge base before starting one web worker."""

from __future__ import annotations

import logging

from backend.ingest import build_index
from backend.rag import KnowledgeBaseNotReadyError, get_collection


def ensure_index() -> None:
    try:
        if get_collection().count() > 0:
            return
    except KnowledgeBaseNotReadyError:
        pass
    logging.getLogger("liwin-ai.bootstrap").info("No knowledge index found; creating one.")
    build_index()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    ensure_index()
