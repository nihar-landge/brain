"""
Causal Inference Service - Move beyond correlation to causation.
Uses statistical methods for causal modeling, counterfactual generation,
and A/B test suggestions.

Note: DoWhy is optional — falls back to simpler statistical methods if unavailable.
"""

import json
from datetime import datetime, timedelta
from typing import Optional

import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import func

from models.journal import JournalEntry, MoodLog, Event
from models.habits import Habit, HabitLog
from models.context import ContextLog
from models.social import SocialInteraction
from utils.logger import log


class CausalInferenceService:
    """
    Causal analysis engine: identifies potential causal relationships,
    generates counterfactuals, and suggests self-experiments.
    """

    def __init__(self):
        self._dowhy = None
        self._dowhy_available = None

    def _check_dowhy(self) -> bool:
        """Check if DoWhy is available."""
        if self._dowhy_available is None:
            try:
                import dowhy

                self._dowhy = dowhy
                self._dowhy_available = True
            except ImportError:
                self._dowhy_available = False
                log.info("DoWhy not available, using fallback statistical methods")
        return self._dowhy_available

    # ======================== DATA COLLECTION ========================

    def _build_daily_dataset(
        self, db: Session, user_id: int, days: int = 90
    ) -> list[dict]:
        """
        Build a daily dataset merging mood, habits, context, and social data.
        Each row = one day with all available features.
        """
        start_date = datetime.now().date() - timedelta(days=days)
        dataset = []

        for day_offset in range(days):
            date = start_date + timedelta(days=day_offset)
            row = {"date": str(date)}

            # Mood (average for the day)
            moods = (
                db.query(MoodLog)
                .filter(
                    MoodLog.user_id == user_id,
                    MoodLog.log_date == date,
                )
                .all()
            )
            if moods:
                row["mood"] = round(sum(m.mood_value for m in moods) / len(moods), 1)
                energies = [m.energy_level for m in moods if m.energy_level]
                row["energy"] = (
                    round(sum(energies) / len(energies), 1) if energies else None
                )
                stresses = [m.stress_level for m in moods if m.stress_level]
                row["stress"] = (
                    round(sum(stresses) / len(stresses), 1) if stresses else None
                )
            else:
                # Try journal entry
                entry = (
                    db.query(JournalEntry)
                    .filter(
                        JournalEntry.user_id == user_id,
                        JournalEntry.entry_date == date,
                        JournalEntry.deleted_at.is_(None),
                    )
                    .first()
                )
                if entry:
                    row["mood"] = entry.mood
                    row["energy"] = entry.energy_level
                    row["stress"] = entry.stress_level
                    row["sleep_hours"] = entry.sleep_hours

            # Sleep from journal
            if "sleep_hours" not in row:
                entry = (
                    db.query(JournalEntry)
                    .filter(
                        JournalEntry.user_id == user_id,
                        JournalEntry.entry_date == date,
                        JournalEntry.deleted_at.is_(None),
                    )
                    .first()
                )
                if entry and entry.sleep_hours:
                    row["sleep_hours"] = entry.sleep_hours

            # Habit completions count
            habit_logs = (
                db.query(HabitLog)
                .filter(
                    HabitLog.user_id == user_id,
                    HabitLog.log_date == date,
                )
                .all()
            )
            row["habits_completed"] = sum(1 for h in habit_logs if h.completed)
            row["habits_total"] = len(habit_logs)

            # Context switching count
            contexts = (
                db.query(ContextLog)
                .filter(
                    ContextLog.user_id == user_id,
                    func.date(ContextLog.started_at) == date,
                )
                .all()
            )
            row["context_switches"] = len(contexts)
            row["deep_work_minutes"] = sum(
                c.duration_minutes or 0
                for c in contexts
                if c.context_type in ("deep_work", "coding", "writing")
            )
            row["interruptions"] = sum(1 for c in contexts if c.is_interruption)

            # Social interactions
            interactions = (
                db.query(SocialInteraction)
                .filter(
                    SocialInteraction.user_id == user_id,
                    SocialInteraction.interaction_date == date,
                )
                .all()
            )
            row["social_interactions"] = len(interactions)
            drains = [
                i.draining_vs_energizing
                for i in interactions
                if i.draining_vs_energizing is not None
            ]
            row["avg_social_impact"] = (
                round(sum(drains) / len(drains), 1) if drains else None
            )

            # Only include days with at least mood data
            if "mood" in row and row["mood"] is not None:
                dataset.append(row)

        return dataset

    # ======================== CORRELATION ANALYSIS ========================

    def get_correlations(self, db: Session, user_id: int = 1, days: int = 90) -> dict:
        """
        Calculate correlations between all tracked variables and mood.
        Returns sorted correlations with significance indicators.
        """
        dataset = self._build_daily_dataset(db, user_id, days)
        if len(dataset) < 10:
            return {
                "correlations": [],
                "sample_size": len(dataset),
                "message": "Need at least 10 days of data for correlation analysis.",
            }

        mood_values = [d["mood"] for d in dataset]
        features = [
            "energy",
            "stress",
            "sleep_hours",
            "habits_completed",
            "context_switches",
            "deep_work_minutes",
            "interruptions",
            "social_interactions",
            "avg_social_impact",
        ]

        correlations = []
        for feature in features:
            values = [d.get(feature) for d in dataset]
            # Filter to pairs where both values exist
            pairs = [(m, v) for m, v in zip(mood_values, values) if v is not None]
            if len(pairs) < 5:
                continue

            m_arr = np.array([p[0] for p in pairs])
            v_arr = np.array([p[1] for p in pairs])

            # Pearson correlation
            if np.std(m_arr) == 0 or np.std(v_arr) == 0:
                continue

            corr = float(np.corrcoef(m_arr, v_arr)[0, 1])
            if np.isnan(corr):
                continue

            # Significance (rough p-value using t-test approximation)
            n = len(pairs)
            t_stat = (
                corr * np.sqrt((n - 2) / (1 - corr**2))
                if abs(corr) < 1
                else float("inf")
            )
            significant = abs(t_stat) > 2.0  # ~p < 0.05 for reasonable n

            correlations.append(
                {
                    "feature": feature,
                    "correlation": round(corr, 3),
                    "strength": self._correlation_strength(corr),
                    "direction": "positive" if corr > 0 else "negative",
                    "significant": significant,
                    "sample_size": n,
                }
            )

        # Sort by absolute correlation
        correlations.sort(key=lambda x: abs(x["correlation"]), reverse=True)

        return {
            "correlations": correlations,
            "sample_size": len(dataset),
            "period_days": days,
        }

    def _correlation_strength(self, r: float) -> str:
        """Classify correlation strength."""
        r_abs = abs(r)
        if r_abs >= 0.7:
            return "strong"
        elif r_abs >= 0.4:
            return "moderate"
        elif r_abs >= 0.2:
            return "weak"
        return "negligible"

    # ======================== CAUSAL ANALYSIS ========================

    def get_causal_analysis(
        self,
        db: Session,
        user_id: int = 1,
        treatment: str = "sleep_hours",
        outcome: str = "mood",
    ) -> dict:
        """
        Attempt causal inference for a specific treatment -> outcome relationship.
        Uses DoWhy if available, otherwise falls back to stratified analysis.
        """
        dataset = self._build_daily_dataset(db, user_id, days=90)
        if len(dataset) < 15:
            return {
                "error": "Insufficient data",
                "message": "Need at least 15 days of data for causal analysis.",
                "sample_size": len(dataset),
            }

        # Filter to rows with both treatment and outcome
        valid = [
            d
            for d in dataset
            if d.get(treatment) is not None and d.get(outcome) is not None
        ]
        if len(valid) < 10:
            return {
                "error": "Insufficient valid data",
                "message": f"Only {len(valid)} days have both '{treatment}' and '{outcome}' data.",
            }

        if self._check_dowhy():
            return self._dowhy_analysis(valid, treatment, outcome)
        else:
            return self._stratified_analysis(valid, treatment, outcome)

    def _stratified_analysis(
        self, dataset: list[dict], treatment: str, outcome: str
    ) -> dict:
        """
        Fallback causal analysis using stratification.
        Split treatment into high/low groups and compare outcomes.
        """
        treatment_vals = [d[treatment] for d in dataset]
        median = float(np.median(treatment_vals))

        high_group = [d[outcome] for d in dataset if d[treatment] >= median]
        low_group = [d[outcome] for d in dataset if d[treatment] < median]

        if not high_group or not low_group:
            return {"error": "Cannot stratify data — all values on one side of median."}

        high_mean = float(np.mean(high_group))
        low_mean = float(np.mean(low_group))
        effect = high_mean - low_mean

        # Effect size (Cohen's d)
        pooled_std = float(
            np.sqrt((np.std(high_group) ** 2 + np.std(low_group) ** 2) / 2)
        )
        cohens_d = effect / pooled_std if pooled_std > 0 else 0

        return {
            "method": "stratified_analysis",
            "treatment": treatment,
            "outcome": outcome,
            "median_split": round(median, 2),
            "high_group_mean": round(high_mean, 2),
            "low_group_mean": round(low_mean, 2),
            "estimated_effect": round(effect, 2),
            "effect_size_cohens_d": round(cohens_d, 2),
            "effect_magnitude": self._effect_magnitude(cohens_d),
            "high_group_n": len(high_group),
            "low_group_n": len(low_group),
            "interpretation": self._interpret_effect(
                treatment, outcome, effect, cohens_d
            ),
            "caution": "This is an observational analysis, not a controlled experiment. Confounding variables may exist.",
        }

    def _dowhy_analysis(
        self, dataset: list[dict], treatment: str, outcome: str
    ) -> dict:
        """Use DoWhy for proper causal inference."""
        try:
            import pandas as pd
            import dowhy

            df = pd.DataFrame(dataset)

            # Identify potential confounders (other available numeric columns)
            confounders = [
                col
                for col in df.columns
                if col not in [treatment, outcome, "date"]
                and df[col].dtype in ["float64", "int64"]
                and df[col].notna().sum() > len(df) * 0.5
            ]

            model = dowhy.CausalModel(
                data=df,
                treatment=treatment,
                outcome=outcome,
                common_causes=confounders if confounders else None,
            )

            identified = model.identify_effect()
            estimate = model.estimate_effect(
                identified,
                method_name="backdoor.linear_regression",
            )

            return {
                "method": "dowhy_causal_inference",
                "treatment": treatment,
                "outcome": outcome,
                "estimated_effect": round(float(estimate.value), 3),
                "confounders_controlled": confounders,
                "interpretation": self._interpret_effect(
                    treatment, outcome, float(estimate.value), float(estimate.value)
                ),
                "caution": "Causal estimate assumes no unmeasured confounders.",
            }
        except Exception as e:
            log.error(f"DoWhy analysis failed: {e}, falling back to stratified")
            return self._stratified_analysis(dataset, treatment, outcome)

    def _effect_magnitude(self, d: float) -> str:
        """Classify effect size (Cohen's d)."""
        d_abs = abs(d)
        if d_abs >= 0.8:
            return "large"
        elif d_abs >= 0.5:
            return "medium"
        elif d_abs >= 0.2:
            return "small"
        return "negligible"

    def _interpret_effect(
        self, treatment: str, outcome: str, effect: float, effect_size: float
    ) -> str:
        """Generate a human-readable interpretation."""
        direction = "higher" if effect > 0 else "lower"
        magnitude = self._effect_magnitude(effect_size)
        treatment_label = treatment.replace("_", " ")
        outcome_label = outcome.replace("_", " ")

        return (
            f"Higher {treatment_label} is associated with {direction} {outcome_label} "
            f"({magnitude} effect). "
            f"When {treatment_label} is above median, {outcome_label} is on average "
            f"{abs(effect):.1f} points {'higher' if effect > 0 else 'lower'}."
        )

    # ======================== COUNTERFACTUALS ========================

    def generate_counterfactuals(self, db: Session, user_id: int = 1) -> list[dict]:
        """
        Generate "what if" counterfactual scenarios based on user data.
        E.g., "If you had slept 8 hours instead of 6, your mood would likely be 7.2 instead of 5.8"
        """
        dataset = self._build_daily_dataset(db, user_id, days=60)
        if len(dataset) < 10:
            return []

        counterfactuals = []

        # Sleep counterfactual
        sleep_cf = self._sleep_counterfactual(dataset)
        if sleep_cf:
            counterfactuals.append(sleep_cf)

        # Exercise/habits counterfactual
        habits_cf = self._habits_counterfactual(dataset)
        if habits_cf:
            counterfactuals.append(habits_cf)

        # Deep work counterfactual
        deepwork_cf = self._deep_work_counterfactual(dataset)
        if deepwork_cf:
            counterfactuals.append(deepwork_cf)

        return counterfactuals

    def _sleep_counterfactual(self, dataset: list[dict]) -> Optional[dict]:
        """What if you slept more?"""
        pairs = [
            (d["sleep_hours"], d["mood"])
            for d in dataset
            if d.get("sleep_hours") and d.get("mood")
        ]
        if len(pairs) < 5:
            return None

        sleep_arr = np.array([p[0] for p in pairs])
        mood_arr = np.array([p[1] for p in pairs])

        # Simple linear model
        if np.std(sleep_arr) == 0:
            return None
        slope = float(
            np.corrcoef(sleep_arr, mood_arr)[0, 1]
            * np.std(mood_arr)
            / np.std(sleep_arr)
        )

        avg_sleep = float(np.mean(sleep_arr))
        avg_mood = float(np.mean(mood_arr))
        target_sleep = 8.0
        predicted_mood = avg_mood + slope * (target_sleep - avg_sleep)
        predicted_mood = max(1, min(10, predicted_mood))

        if abs(slope) < 0.05:
            return None

        return {
            "type": "sleep",
            "scenario": f"If you consistently slept {target_sleep:.0f} hours instead of your average {avg_sleep:.1f} hours",
            "current_avg": round(avg_mood, 1),
            "predicted_avg": round(predicted_mood, 1),
            "change": round(predicted_mood - avg_mood, 1),
            "confidence": "moderate" if len(pairs) >= 20 else "low",
        }

    def _habits_counterfactual(self, dataset: list[dict]) -> Optional[dict]:
        """What if you completed more habits?"""
        pairs = [
            (d["habits_completed"], d["mood"])
            for d in dataset
            if d.get("habits_completed") is not None and d.get("mood")
        ]
        if len(pairs) < 5:
            return None

        h_arr = np.array([p[0] for p in pairs])
        m_arr = np.array([p[1] for p in pairs])

        if np.std(h_arr) == 0:
            return None
        slope = float(np.corrcoef(h_arr, m_arr)[0, 1] * np.std(m_arr) / np.std(h_arr))

        avg_habits = float(np.mean(h_arr))
        avg_mood = float(np.mean(m_arr))
        max_habits = float(np.max(h_arr))
        if max_habits <= avg_habits:
            return None

        predicted = avg_mood + slope * (max_habits - avg_habits)
        predicted = max(1, min(10, predicted))

        if abs(slope) < 0.05:
            return None

        return {
            "type": "habits",
            "scenario": f"If you completed {max_habits:.0f} habits daily instead of your average {avg_habits:.1f}",
            "current_avg": round(avg_mood, 1),
            "predicted_avg": round(predicted, 1),
            "change": round(predicted - avg_mood, 1),
            "confidence": "moderate" if len(pairs) >= 20 else "low",
        }

    def _deep_work_counterfactual(self, dataset: list[dict]) -> Optional[dict]:
        """What if you did more deep work?"""
        pairs = [
            (d["deep_work_minutes"], d["mood"])
            for d in dataset
            if d.get("deep_work_minutes") and d.get("mood")
        ]
        if len(pairs) < 5:
            return None

        dw_arr = np.array([p[0] for p in pairs])
        m_arr = np.array([p[1] for p in pairs])

        if np.std(dw_arr) == 0:
            return None
        slope = float(np.corrcoef(dw_arr, m_arr)[0, 1] * np.std(m_arr) / np.std(dw_arr))

        avg_dw = float(np.mean(dw_arr))
        avg_mood = float(np.mean(m_arr))
        target_dw = 120.0  # 2 hours
        predicted = avg_mood + slope * (target_dw - avg_dw)
        predicted = max(1, min(10, predicted))

        if abs(slope) < 0.01:
            return None

        return {
            "type": "deep_work",
            "scenario": f"If you did {target_dw:.0f} min of deep work daily instead of {avg_dw:.0f} min",
            "current_avg": round(avg_mood, 1),
            "predicted_avg": round(predicted, 1),
            "change": round(predicted - avg_mood, 1),
            "confidence": "moderate" if len(pairs) >= 20 else "low",
        }

    # ======================== A/B TEST SUGGESTIONS ========================

    def suggest_experiments(self, db: Session, user_id: int = 1) -> list[dict]:
        """
        Based on correlation/causal analysis, suggest self-experiments
        the user can try to establish causation.
        """
        corr_data = self.get_correlations(db, user_id, days=60)
        suggestions = []

        for c in corr_data.get("correlations", []):
            if not c["significant"] or c["strength"] == "negligible":
                continue

            feature = c["feature"]
            direction = c["direction"]

            experiment = {
                "variable": feature,
                "correlation_with_mood": c["correlation"],
                "hypothesis": self._generate_hypothesis(feature, direction),
                "protocol": self._generate_protocol(feature, direction),
                "duration_days": 14,
                "measurement": "Track daily mood (1-10) throughout the experiment.",
            }
            suggestions.append(experiment)

            if len(suggestions) >= 3:
                break

        return suggestions

    def _generate_hypothesis(self, feature: str, direction: str) -> str:
        """Generate a testable hypothesis."""
        feature_label = feature.replace("_", " ")
        if direction == "positive":
            return f"Increasing {feature_label} will improve mood."
        else:
            return f"Decreasing {feature_label} will improve mood."

    def _generate_protocol(self, feature: str, direction: str) -> str:
        """Generate a simple experimental protocol."""
        protocols = {
            "sleep_hours": "Week 1: Sleep your normal amount (baseline). Week 2: Aim for 8+ hours every night. Compare average mood between weeks.",
            "habits_completed": "Week 1: Normal routine (baseline). Week 2: Focus on completing all tracked habits daily. Compare average mood.",
            "deep_work_minutes": "Week 1: Normal work routine (baseline). Week 2: Schedule 2 hours of uninterrupted deep work daily. Compare mood and productivity.",
            "social_interactions": "Week 1: Normal social activity (baseline). Week 2: Intentionally schedule one more social interaction per day. Compare mood.",
            "interruptions": "Week 1: Normal work (baseline). Week 2: Block all notifications during work hours. Compare mood and focus.",
            "context_switches": "Week 1: Normal work (baseline). Week 2: Batch similar tasks together, limit switches to max 4/day. Compare mood.",
            "energy": "Track energy levels — this is more of an outcome than a treatment. Consider what causes energy changes.",
            "stress": "Week 1: Normal routine (baseline). Week 2: Add 15 min daily stress-reduction activity (meditation, walk). Compare mood.",
            "avg_social_impact": "Week 1: Normal social activity. Week 2: Prioritize interactions with people who are energizing (positive impact). Compare mood.",
        }
        return protocols.get(
            feature,
            f"Week 1: Baseline. Week 2: Modify {feature.replace('_', ' ')}. Compare mood.",
        )


# Singleton instance
causal_inference_service = CausalInferenceService()
