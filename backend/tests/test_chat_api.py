"""Tests for Chat API endpoints."""

from unittest.mock import patch, MagicMock


class TestChatApi:
    """Test chat send, history, and clear."""

    @patch("api.chat.gemini_service")
    @patch("api.chat.SmartMemoryManager")
    def test_send_message(self, MockMemoryMgr, mock_gemini, client, auth_headers):
        # Mock instance returned by constructor
        mock_mem = MockMemoryMgr.return_value
        mock_mem.smart_search_with_fallback.return_value = {
            "combined_context": "No previous context",
            "core": [],
            "archival": [],
            "sql_fallback": [],
        }

        mock_gemini.generate_stream.return_value = ["Hello! How can I help?"]

        resp = client.post("/api/chat", headers=auth_headers, json={"message": "Hi there"})
        assert resp.status_code == 200
        assert "Hello! How can I help?" in resp.text

    def test_get_history_empty(self, client, auth_headers):
        resp = client.get("/api/chat/history", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_clear_chat(self, client, auth_headers):
        resp = client.delete("/api/chat/clear", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"
