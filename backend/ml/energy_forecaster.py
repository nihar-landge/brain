"""
Energy Forecaster - Time series forecasting for energy levels.
Uses simple day-of-week averaging (Prophet is optional).
"""

from datetime import datetime, timedelta

import numpy as np
from sqlalchemy.orm import Session

from models.journal import JournalEntry


class EnergyForecaster:
    """Energy level forecaster."""

    def __init__(self, db: Session):
        self.db = db

    def forecast(self, user_id: int, days_ahead: int = 7) -> dict:
        """Forecast energy levels for the next N days."""
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

        if len(entries) < 7:
            avg = 5.0
            if entries:
                avg = sum(e.energy_level for e in entries) / len(entries)

            return {
                "forecast": [
                    {
                        "date": (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d"),
                        "energy": round(avg, 1),
                        "lower": round(avg - 1, 1),
                        "upper": round(avg + 1, 1),
                    }
                    for i in range(1, days_ahead + 1)
                ],
                "method": "simple_average",
            }

        # Day-of-week patterns
        dow_data = {}
        for entry in entries:
            dow = entry.entry_date.weekday()
            if dow not in dow_data:
                dow_data[dow] = []
            dow_data[dow].append(entry.energy_level)

        overall_avg = sum(e.energy_level for e in entries) / len(entries)
        overall_std = np.std([e.energy_level for e in entries])

        forecast = []
        for i in range(1, days_ahead + 1):
            future = datetime.now() + timedelta(days=i)
            dow = future.weekday()

            if dow in dow_data:
                avg = sum(dow_data[dow]) / len(dow_data[dow])
                std = np.std(dow_data[dow]) if len(dow_data[dow]) > 1 else overall_std
            else:
                avg = overall_avg
                std = overall_std

            forecast.append({
                "date": future.strftime("%Y-%m-%d"),
                "day": future.strftime("%A"),
                "energy": round(float(avg), 1),
                "lower": round(float(max(1, avg - std)), 1),
                "upper": round(float(min(10, avg + std)), 1),
            })

        return {
            "forecast": forecast,
            "method": "day_of_week_pattern",
            "data_points": len(entries),
        }
