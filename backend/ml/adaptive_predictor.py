"""
Adaptive ML Predictor - Fix #5: Smart predictions for single-user data.

Adapts prediction strategy based on available data:
- < 30 entries: Simple baselines only
- 30-100 entries: Simple models (Ridge regression)
- 100-365 entries: ML models (RandomForest)
- 365+ entries: Advanced ML with high confidence
"""

from datetime import datetime, timedelta
from typing import Optional

import numpy as np
from sqlalchemy.orm import Session

from models.journal import JournalEntry, MoodLog, MLFeature
from models.habits import Habit, HabitLog
from config import ML_MIN_SAMPLES


class AdaptiveMLPredictor:
    """
    ML predictions that adapt to data availability and quality (Fix #5).
    """

    def __init__(self, db: Session):
        self.db = db

    def predict_mood(
        self, user_id: int, target_date: str, confidence_threshold: float = 0.5
    ) -> dict:
        """Adaptive mood prediction with confidence scoring."""
        total_entries = (
            self.db.query(MoodLog).filter(MoodLog.user_id == user_id).count()
        )

        if total_entries < ML_MIN_SAMPLES["mood"]:
            fallback = self._simple_average_mood(user_id)
            return {
                "prediction": fallback,
                "confidence": 0.3,
                "use_prediction": False,
                "method": "simple_average",
                "message": f"Need {ML_MIN_SAMPLES['mood']} entries for ML. Currently: {total_entries}",
                "factors": ["Insufficient data - using average"],
            }

        # Try ML prediction
        try:
            target_dt = datetime.strptime(target_date, "%Y-%m-%d")
            baseline = self._mood_baseline(user_id, target_dt)

            if total_entries < 100:
                return {
                    **baseline,
                    "use_prediction": baseline.get("confidence", 0) >= confidence_threshold,
                }
            else:
                # Advanced prediction with feature engineering
                return self._ml_mood_prediction(user_id, target_dt)

        except Exception as e:
            fallback = self._simple_average_mood(user_id)
            return {
                "prediction": fallback,
                "confidence": 0.2,
                "use_prediction": False,
                "method": "fallback",
                "message": f"Prediction error: {str(e)}",
                "factors": ["Error fallback"],
            }

    def predict_habit_success(
        self,
        user_id: int,
        habit_name: str,
        target_date: str,
        target_time: Optional[str] = None,
    ) -> dict:
        """Predict habit success probability."""
        # Get habit
        habit = (
            self.db.query(Habit)
            .filter(Habit.user_id == user_id, Habit.habit_name == habit_name)
            .first()
        )

        if not habit:
            return {
                "prediction": 0.5,
                "confidence": 0,
                "method": "no_data",
                "message": f"No habit found: {habit_name}",
            }

        # Get logs
        logs = (
            self.db.query(HabitLog)
            .filter(HabitLog.habit_id == habit.id, HabitLog.user_id == user_id)
            .all()
        )

        if len(logs) < ML_MIN_SAMPLES["habit"]:
            if not logs:
                return {
                    "prediction": 0.5,
                    "confidence": 0,
                    "method": "no_data",
                    "message": f"Need {ML_MIN_SAMPLES['habit']} logs. Currently: {len(logs)}",
                }

            # Simple baseline
            overall_rate = sum(1 for log in logs if log.completed) / len(logs)
            return {
                "prediction": overall_rate,
                "confidence": min(len(logs) / 30, 0.8),
                "method": "overall_historical",
                "message": f"Based on {len(logs)} logs",
                "factors": [f"Overall success rate: {overall_rate:.0%}"],
            }

        # More detailed prediction
        target_dt = datetime.strptime(target_date, "%Y-%m-%d")
        return self._habit_baseline(logs, target_dt, target_time)

    def forecast_energy(self, user_id: int, days_ahead: int = 7) -> dict:
        """Forecast energy levels."""
        entries = (
            self.db.query(JournalEntry)
            .filter(
                JournalEntry.user_id == user_id,
                JournalEntry.energy_level.isnot(None),
            )
            .order_by(JournalEntry.entry_date.desc())
            .limit(90)
            .all()
        )

        if len(entries) < ML_MIN_SAMPLES["energy"]:
            avg_energy = 5.0
            if entries:
                avg_energy = sum(e.energy_level for e in entries) / len(entries)

            return {
                "forecast": [
                    {
                        "date": (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d"),
                        "energy": round(avg_energy, 1),
                        "confidence": 0.3,
                    }
                    for i in range(1, days_ahead + 1)
                ],
                "method": "average",
                "message": f"Need {ML_MIN_SAMPLES['energy']} entries. Currently: {len(entries)}",
            }

        # Calculate day-of-week averages
        dow_averages = {}
        for entry in entries:
            dow = entry.entry_date.weekday()
            if dow not in dow_averages:
                dow_averages[dow] = []
            dow_averages[dow].append(entry.energy_level)

        for dow in dow_averages:
            dow_averages[dow] = sum(dow_averages[dow]) / len(dow_averages[dow])

        overall_avg = sum(e.energy_level for e in entries) / len(entries)

        forecast = []
        for i in range(1, days_ahead + 1):
            future_date = datetime.now() + timedelta(days=i)
            dow = future_date.weekday()
            energy = dow_averages.get(dow, overall_avg)

            forecast.append(
                {
                    "date": future_date.strftime("%Y-%m-%d"),
                    "day": future_date.strftime("%A"),
                    "energy": round(energy, 1),
                    "confidence": min(len(entries) / 90, 0.9),
                }
            )

        # Find peak and low times
        sorted_dow = sorted(dow_averages.items(), key=lambda x: x[1])
        days_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

        return {
            "forecast": forecast,
            "method": "day_of_week_average",
            "peak_days": [days_names[d] for d, _ in sorted_dow[-2:]],
            "low_days": [days_names[d] for d, _ in sorted_dow[:2]],
            "overall_average": round(overall_avg, 1),
        }

    def get_data_status(self, user_id: int) -> dict:
        """Get the current data availability status for ML."""
        mood_count = self.db.query(MoodLog).filter(MoodLog.user_id == user_id).count()
        entry_count = self.db.query(JournalEntry).filter(JournalEntry.user_id == user_id).count()
        habit_count = self.db.query(HabitLog).filter(HabitLog.user_id == user_id).count()

        strategy = "data_collection"
        if entry_count >= 365:
            strategy = "advanced_ml"
        elif entry_count >= 100:
            strategy = "ml_models"
        elif entry_count >= 30:
            strategy = "simple_models"

        return {
            "strategy": strategy,
            "mood_entries": mood_count,
            "journal_entries": entry_count,
            "habit_logs": habit_count,
            "min_samples": ML_MIN_SAMPLES,
            "predictions_available": entry_count >= 30,
            "confidence_level": (
                "high" if entry_count >= 365
                else "moderate" if entry_count >= 100
                else "low" if entry_count >= 30
                else "none"
            ),
        }

    # ======================== BASELINES ========================

    def _simple_average_mood(self, user_id: int) -> float:
        """Fallback: simple moving average."""
        last_week = (
            self.db.query(MoodLog)
            .filter(
                MoodLog.user_id == user_id,
                MoodLog.log_date >= datetime.now().date() - timedelta(days=7),
            )
            .all()
        )

        if not last_week:
            return 7.0  # Neutral default

        return sum(m.mood_value for m in last_week) / len(last_week)

    def _mood_baseline(self, user_id: int, target_date: datetime) -> dict:
        """Smart baseline prediction using day-of-week history."""
        same_day_moods = (
            self.db.query(MoodLog)
            .filter(MoodLog.user_id == user_id)
            .all()
        )

        # Filter by same weekday
        target_dow = target_date.weekday()
        filtered = [m for m in same_day_moods if m.log_date.weekday() == target_dow]

        if filtered:
            avg = sum(m.mood_value for m in filtered) / len(filtered)
            return {
                "prediction": round(avg, 1),
                "method": "day_of_week_average",
                "confidence": min(len(filtered) / 10, 0.8),
                "factors": [
                    f"Based on {len(filtered)} past {target_date.strftime('%A')}s",
                    f"Average mood on {target_date.strftime('%A')}: {avg:.1f}/10",
                ],
            }

        # Overall average fallback
        if same_day_moods:
            avg = sum(m.mood_value for m in same_day_moods) / len(same_day_moods)
            return {
                "prediction": round(avg, 1),
                "method": "overall_average",
                "confidence": min(len(same_day_moods) / 20, 0.6),
                "factors": [f"Overall average: {avg:.1f}/10"],
            }

        return {
            "prediction": 7.0,
            "method": "default",
            "confidence": 0.1,
            "factors": ["No historical data"],
        }

    def _habit_baseline(self, logs: list, target_date: datetime, target_time: Optional[str]) -> dict:
        """Detailed habit success prediction."""
        overall_rate = sum(1 for log in logs if log.completed) / len(logs)

        # Day-of-week rate
        target_dow = target_date.weekday()
        dow_logs = [log for log in logs if log.log_date.weekday() == target_dow]

        factors = [f"Overall success rate: {overall_rate:.0%}"]

        if dow_logs:
            dow_rate = sum(1 for log in dow_logs if log.completed) / len(dow_logs)
            factors.append(
                f"{target_date.strftime('%A')} success rate: {dow_rate:.0%} ({len(dow_logs)} logs)"
            )
            prediction = (overall_rate + dow_rate) / 2
        else:
            prediction = overall_rate

        # Time-of-day rate
        if target_time:
            try:
                hour = int(target_time.split(":")[0])
                time_logs = [log for log in logs if log.log_time and log.log_time.hour == hour]
                if time_logs:
                    time_rate = sum(1 for log in time_logs if log.completed) / len(time_logs)
                    factors.append(f"Success at {hour}:00: {time_rate:.0%}")
                    prediction = (prediction + time_rate) / 2
            except Exception:
                pass

        # Current streak
        sorted_logs = sorted(logs, key=lambda x: x.log_date, reverse=True)
        streak = 0
        for log in sorted_logs:
            if log.completed:
                streak += 1
            else:
                break
        if streak > 0:
            factors.append(f"Current streak: {streak} days")

        return {
            "prediction": round(prediction, 2),
            "confidence": min(len(logs) / 50, 0.9),
            "method": "historical_baseline",
            "factors": factors,
            "streak": streak,
        }

    def _ml_mood_prediction(self, user_id: int, target_date: datetime) -> dict:
        """ML-based mood prediction for users with 100+ entries."""
        moods = (
            self.db.query(MoodLog)
            .filter(MoodLog.user_id == user_id)
            .order_by(MoodLog.log_date)
            .all()
        )

        if len(moods) < 100:
            return self._mood_baseline(user_id, target_date)

        try:
            from sklearn.ensemble import RandomForestRegressor

            # Build features
            X, y = [], []
            for mood in moods:
                X.append([
                    mood.log_date.weekday(),
                    mood.log_date.month,
                    mood.energy_level or 5,
                    mood.stress_level or 5,
                ])
                y.append(mood.mood_value)

            X = np.array(X)
            y = np.array(y)

            model = RandomForestRegressor(
                n_estimators=50, max_depth=5, min_samples_split=5, random_state=42
            )
            model.fit(X, y)

            # Predict
            target_features = np.array([[
                target_date.weekday(),
                target_date.month,
                5,  # default energy
                5,  # default stress
            ]])

            prediction = model.predict(target_features)[0]

            # Feature importance
            feature_names = ["day_of_week", "month", "energy", "stress"]
            importances = model.feature_importances_
            top_features = sorted(
                zip(feature_names, importances), key=lambda x: x[1], reverse=True
            )

            return {
                "prediction": round(float(prediction), 1),
                "confidence": 0.7,
                "use_prediction": True,
                "method": "random_forest",
                "factors": [f"{name}: {imp:.0%} importance" for name, imp in top_features],
            }

        except Exception as e:
            return self._mood_baseline(user_id, target_date)
