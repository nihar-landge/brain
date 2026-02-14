"""Tests for Chat API endpoints."""

from unittest.mock import patch, MagicMock


class TestChatApi:
    """Test chat send, history, and clear."""

    @patch("api.chat.gemini_service")
    @patch("api.chat.SmartMemoryManager")
    def test_send_message(self, MockMemoryMgr, mock_gemini, client):
        # Mock instance returned by constructor
        mock_mem = MockMemoryMgr.return_value
        mock_mem.smart_search_with_fallback.return_value = {
            "combined_context": "No previous context",
            "core": [],
            "archival": [],
            "sql_fallback": [],
        }

        mock_gemini.generate_response.return_value = "Hello! How can I help?"

        resp = client.post("/api/chat", json={"message": "Hi there"})
        assert resp.status_code == 200
        data = resp.json()
        assert "response" in data

    def test_get_history_empty(self, client):
        resp = client.get("/api/chat/history")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_clear_chat(self, client):
        resp = client.delete("/api/chat/clear")
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"
