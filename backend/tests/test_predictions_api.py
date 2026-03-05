"""
Tests for Predictions API — ML predictions, status, performance.
"""

import pytest
from unittest.mock import patch, MagicMock


class TestPredictionsApi:
    """Prediction endpoint tests."""

    @patch("api.predictions.MLService")
    def test_predict_mood(self, MockMLService, client, auth_headers):
        """Predict mood for a date."""
        mock_instance = MockMLService.return_value
        mock_instance.predict_mood.return_value = {
            "predicted_mood": 7.2,
            "confidence": 0.85,
            "method": "adaptive_ml",
        }

        resp = client.post("/api/predict/mood", headers=auth_headers, json={
            "date": "2024-01-20",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "predicted_mood" in data

    @patch("api.predictions.MLService")
    def test_predict_habit(self, MockMLService, client, auth_headers):
        """Predict habit success probability."""
        mock_instance = MockMLService.return_value
        mock_instance.predict_habit_success.return_value = {
            "probability": 0.78,
            "confidence": 0.6,
            "factors": ["consistency", "time_of_day"],
        }

        resp = client.post("/api/predict/habit", headers=auth_headers, json={
            "habit": "meditation",
            "date": "2024-01-20",
        })
        assert resp.status_code == 200
        assert "probability" in resp.json()

    @patch("api.predictions.MLService")
    def test_get_energy_forecast(self, MockMLService, client, auth_headers):
        """Get energy forecast for next N days."""
        mock_instance = MockMLService.return_value
        mock_instance.get_energy_forecast.return_value = {
            "forecast": [6, 7, 5, 8, 6, 7, 7],
        }

        resp = client.get("/api/predict/energy?days_ahead=7", headers=auth_headers)
        assert resp.status_code == 200

    @patch("api.predictions.MLService")
    def test_get_prediction_status(self, MockMLService, client, auth_headers):
        """Get ML data status."""
        with patch("api.predictions.AdaptiveMLPredictor", create=True) as MockPredictor:
            mock_pred = MockPredictor.return_value
            mock_pred.get_data_status.return_value = {
                "journal_entries": 50,
                "mood_logs": 30,
                "ready": True,
            }
            resp = client.get("/api/predict/status", headers=auth_headers)
            assert resp.status_code == 200

    @patch("api.predictions.MLService")
    def test_retrain_models(self, MockMLService, client, auth_headers):
        """Trigger model retraining."""
        mock_instance = MockMLService.return_value
        mock_instance.retrain_models.return_value = {
            "status": "success",
            "models_retrained": ["mood", "habit"],
        }

        resp = client.post("/api/predict/retrain", headers=auth_headers)
        assert resp.status_code == 200

    @patch("api.predictions.MLService")
    def test_get_model_performance(self, MockMLService, client, auth_headers):
        """Get model performance metrics."""
        mock_instance = MockMLService.return_value
        mock_instance.get_model_performance.return_value = {
            "mood_model": {"accuracy": 0.82, "mae": 0.5},
        }

        resp = client.get("/api/predict/performance", headers=auth_headers)
        assert resp.status_code == 200
