import unittest
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

import backend.app as app_module


class AppTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app_module.app)
        app_module.rate_limiter._requests.clear()

    def test_home_serves_the_web_app_with_security_headers(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Liwin AI", response.text)
        self.assertEqual(response.headers["x-content-type-options"], "nosniff")
        self.assertIn("default-src 'self'", response.headers["content-security-policy"])

    def test_health_reports_index_state(self):
        with patch.object(app_module, "get_collection") as get_collection:
            get_collection.return_value.count.return_value = 4
            response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["knowledge_base"], "ready")
        self.assertEqual(response.json()["document_count"], 4)

    def test_greeting_skips_external_services_and_is_saved(self):
        memory = Mock()
        with patch.object(app_module, "memory", memory), patch.object(app_module, "search") as search:
            response = self.client.post("/chat", json={"question": "Hello", "session_id": "session_1"})

        self.assertEqual(response.status_code, 200)
        self.assertIn("Hello", response.json()["answer"])
        search.assert_not_called()
        self.assertEqual(memory.add_message.call_count, 2)

    def test_chat_uses_retrieval_and_generation(self):
        memory = Mock()
        memory.format_history.return_value = "USER: Tell me about a project"
        with (
            patch.object(app_module, "memory", memory),
            patch.object(app_module, "search", return_value=["Smart Focus reference data"]),
            patch.object(app_module, "generate_answer", return_value=("I built Smart Focus.", "gemini")),
        ):
            response = self.client.post(
                "/chat",
                json={"question": "Tell me about Smart Focus", "session_id": "session_2"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"answer": "I built Smart Focus."})
        self.assertEqual(memory.add_message.call_count, 2)

    def test_invalid_question_is_rejected(self):
        response = self.client.post("/chat", json={"question": "   ", "session_id": "session_3"})

        self.assertEqual(response.status_code, 422)

    def test_delete_chat_validates_and_clears_a_session(self):
        memory = Mock()
        with patch.object(app_module, "memory", memory):
            response = self.client.delete("/chat/session_4")

        self.assertEqual(response.status_code, 204)
        memory.clear.assert_called_once_with("session_4")


if __name__ == "__main__":
    unittest.main()
