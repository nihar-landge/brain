"""
Tests for Sleep API — log, correlations, history.
"""

import pytest
from unittest.mock import patch, MagicMock


class TestSleepApi:
    """Sleep endpoint tests."""

    @patch("api.sleep.sleep_mood_engine")
    def test_log_sleep(self, mock_engine, client, auth_headers):
        """Log a sleep entry."""
        mock_engine.generate_quality_score.return_value = 85.0

        resp = client.post("/api/sleep/log", headers=auth_headers, json={
            "bed_time": "2024-01-15T23:00:00+00:00",
            "wake_time": "2024-01-16T07:00:00+00:00",
            "deep_sleep_minutes": 90,
            "rem_sleep_minutes": 60,
            "subjective_rating": 4,
            "source": "manual",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["quality_score"] == 85.0
        assert data["duration"] == 8.0

    def test_log_sleep_invalid_times(self, client, auth_headers):
        """Invalid sleep times should return 400."""
        resp = client.post("/api/sleep/log", headers=auth_headers, json={
            "bed_time": "2024-01-16T07:00:00+00:00",
            "wake_time": "2024-01-15T23:00:00+00:00",  # wake before bed
        })
        assert resp.status_code == 400

    @patch("api.sleep.sleep_mood_engine")
    def test_get_sleep_correlations(self, mock_engine, client, auth_headers):
        """Get sleep-mood correlations."""
        mock_engine.calculate_correlations.return_value = {
            "sleep_mood_correlation": 0.72,
            "data_points": 14,
        }
        resp = client.get("/api/sleep/correlations", headers=auth_headers)
        assert resp.status_code == 200

    @patch("api.sleep.sleep_mood_engine")
    def test_get_sleep_history(self, mock_engine, client, auth_headers):
        """Get sleep history (empty initially)."""
        mock_engine.generate_quality_score.return_value = 80.0

        # Log one entry first
        client.post("/api/sleep/log", headers=auth_headers, json={
            "bed_time": "2024-01-15T23:00:00+00:00",
            "wake_time": "2024-01-16T07:00:00+00:00",
        })

        resp = client.get("/api/sleep/history", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
