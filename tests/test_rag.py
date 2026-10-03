import unittest
from unittest.mock import patch

from backend import rag


class FakeCollection:
    def count(self):
        return 3

    def query(self, **_kwargs):
        return {
            "documents": [["# Highlights\nSeven technical certifications are listed."]],
            "metadatas": [[{"source": "achievements.md"}]],
        }

    def get(self, **_kwargs):
        return {
            "documents": [
                "# Highlights\nSeven technical certifications are listed.",
                "# Certifications\n- Deep Learning Fundamentals",
            ],
            "metadatas": [
                {"source": "achievements.md"},
                {"source": "certifications.md"},
            ],
        }


class RagTests(unittest.TestCase):
    @patch.object(rag, "create_embedding", return_value=[0.1, 0.2])
    @patch.object(rag, "get_collection", return_value=FakeCollection())
    def test_search_boosts_an_exact_source_subject(self, _get_collection, _embedding):
        results = rag.search("What certifications does Liwin have?", k=1)

        self.assertEqual(results, ["# Certifications\n- Deep Learning Fundamentals"])


if __name__ == "__main__":
    unittest.main()
