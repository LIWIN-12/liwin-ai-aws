import tempfile
import unittest
from pathlib import Path

from backend.ingest import CHUNK_SIZE, chunk_document, load_documents


class IngestTests(unittest.TestCase):
    def test_chunk_document_keeps_content_within_the_configured_bound(self):
        text = "\n\n".join(["word " * 500, "another paragraph " * 300])

        chunks = chunk_document(text)

        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(len(chunk) <= CHUNK_SIZE + 300 for chunk in chunks))
        self.assertIn("word", chunks[0])
        self.assertIn("another", chunks[-1])

    def test_load_documents_skips_empty_files_and_adds_source_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            knowledge_path = Path(directory)
            (knowledge_path / "about.md").write_text("# About\n\nPortfolio information", encoding="utf-8")
            (knowledge_path / "empty.md").write_text("\n", encoding="utf-8")

            ids, documents, metadata = load_documents(knowledge_path)

        self.assertEqual(len(ids), 1)
        self.assertEqual(len(documents), 1)
        self.assertEqual(metadata, [{"source": "about.md", "chunk": 0}])
        self.assertTrue(ids[0].startswith("about-0-"))


if __name__ == "__main__":
    unittest.main()
