"""
Tests for Wellness APIs — burnout risk, anomalies, schedule.
"""

import pytest
from unittest.mock import patch, MagicMock


class TestBurnoutApi:
    """Burnout endpoint tests."""

    @patch("api.burnout.burnout_predictor")
    def test_get_burnout_risk(self, mock_predictor, client, auth_headers):
        """Get burnout risk score."""
        mock_predictor.calculate_risk.return_value = {
            "risk_level": "moderate",
            "risk_score": 0.55,
            "metrics": {"workload": 0.7, "recovery": 0.4},
            "primary_insight": "Your workload has been high lately.",
        }
        resp = client.get("/api/burnout/risk", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "risk_level" in data

    @patch("api.burnout.burnout_predictor")
    def test_get_burnout_factors(self, mock_predictor, client, auth_headers):
        """Get burnout contributing factors."""
        mock_predictor.calculate_risk.return_value = {
            "risk_level": "low",
            "risk_score": 0.2,
            "metrics": {"workload": 0.3},
            "primary_insight": "Looking good.",
        }
        resp = client.get("/api/burnout/factors", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "metrics" in data
        assert "primary_insight" in data


class TestAnomaliesApi:
    """Anomaly endpoint tests."""

    @patch("api.anomalies.anomaly_detector")
    def test_get_active_anomalies(self, mock_detector, client, auth_headers):
        """Get active anomaly alerts."""
        mock_detector.detect_anomalies.return_value = None
        resp = client.get("/api/anomalies", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    @patch("api.anomalies.anomaly_detector")
    def test_get_anomaly_history(self, mock_detector, client, auth_headers):
        """Get anomaly history."""
        resp = client.get("/api/anomalies/history", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestScheduleApi:
    """Schedule endpoint tests."""

    @patch("api.schedule.schedule_optimizer")
    def test_get_optimal_schedule(self, mock_optimizer, client, auth_headers):
        """Get optimal schedule suggestions."""
        mock_optimizer.get_optimal_schedule.return_value = {
            "optimal_focus_hours": ["09:00-11:00", "14:00-16:00"],
            "status": "ok",
            "insight": "Morning is best",
            "peak_productivity_hour": 10,
        }
        resp = client.get("/api/schedule/optimal", headers=auth_headers)
        assert resp.status_code == 200

    @patch("api.schedule.schedule_optimizer")
    def test_get_schedule_recommendations(self, mock_optimizer, client, auth_headers):
        """Get schedule-based recommendations."""
        mock_optimizer.get_optimal_schedule.return_value = {
            "status": "ok",
            "insight": "Take a break",
            "peak_productivity_hour": 14,
        }
        resp = client.get("/api/schedule/recommendations", headers=auth_headers)
        assert resp.status_code == 200
