"""Manual live retrieval diagnostic; it is safe to import during test discovery."""

from __future__ import annotations

import argparse

from backend.rag import search


def main() -> None:
    parser = argparse.ArgumentParser(description="Search the Liwin AI knowledge base.")
    parser.add_argument("query", nargs="?", default="Tell me about Smart Focus")
    parser.add_argument("--results", type=int, default=3)
    arguments = parser.parse_args()

    for index, document in enumerate(search(arguments.query, arguments.results), start=1):
        print(f"Result {index}\n{'-' * 40}\n{document}\n")


if __name__ == "__main__":
    main()
