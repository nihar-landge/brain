"""
Context Switching Service - Time tracking, deep work detection, cognitive load analysis.
Manages context logs, identifies deep work blocks, and provides productivity insights.
"""

from datetime import datetime, timedelta, time as dt_time
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import func

from models.context import ContextLog, DeepWorkBlock
from utils.logger import log


class ContextSwitchingService:
    """
    Tracks context switches, detects deep work blocks,
    estimates cognitive load, and identifies optimal work times.
    """

    # ======================== CONTEXT TRACKING ========================

    def start_context(
        self,
        db: Session,
        user_id: int,
        context_name: str,
        context_type: str = "deep_work",
        task_complexity: Optional[int] = None,
    ) -> ContextLog:
        """
        Start a new context/task timer.
        Automatically ends the previous active context if any.
        """
        # End any currently active context
        active = self._get_active_context(db, user_id)
        if active:
            self.end_context(db, user_id, context_id=active.id)

        new_ctx = ContextLog(
            user_id=user_id,
            context_name=context_name,
            context_type=context_type,
            started_at=datetime.utcnow(),
            task_complexity=task_complexity,
            previous_context_id=active.id if active else None,
        )
        db.add(new_ctx)
        db.commit()
        db.refresh(new_ctx)
        return new_ctx

    def end_context(
        self,
        db: Session,
        user_id: int,
        context_id: Optional[int] = None,
        mood_after: Optional[int] = None,
        energy_after: Optional[int] = None,
        productivity_rating: Optional[int] = None,
    ) -> Optional[ContextLog]:
        """End the current or specified context, calculating duration."""
        if context_id:
            ctx = (
                db.query(ContextLog)
                .filter(
                    ContextLog.id == context_id,
                    ContextLog.user_id == user_id,
                )
                .first()
            )
        else:
            ctx = self._get_active_context(db, user_id)

        if not ctx:
            return None

        now = datetime.utcnow()
        ctx.ended_at = now
        ctx.duration_minutes = int((now - ctx.started_at).total_seconds() / 60)

        if mood_after is not None:
            ctx.mood_after = mood_after
        if energy_after is not None:
            ctx.energy_after = energy_after
        if productivity_rating is not None:
            ctx.productivity_rating = productivity_rating

        # Estimate switch cost from previous context
        if ctx.previous_context_id:
            prev = db.query(ContextLog).get(ctx.previous_context_id)
            if prev and prev.ended_at:
                gap = (ctx.started_at - prev.ended_at).total_seconds() / 60
                ctx.switch_cost_minutes = max(0, int(gap))

        # Estimate cognitive load based on complexity + duration
        ctx.estimated_cognitive_load = self._estimate_cognitive_load(
            ctx.task_complexity, ctx.duration_minutes, ctx.is_interruption
        )

        db.commit()
        db.refresh(ctx)

        # Check if this qualifies as a deep work block
        self._check_deep_work(db, ctx)

        return ctx

    def log_interruption(
        self,
        db: Session,
        user_id: int,
        interrupted_by: str = "unknown",
    ) -> Optional[ContextLog]:
        """Mark the current active context as interrupted."""
        active = self._get_active_context(db, user_id)
        if not active:
            return None

        active.is_interruption = True
        active.interrupted_by = interrupted_by
        db.commit()
        db.refresh(active)
        return active

    def _get_active_context(self, db: Session, user_id: int) -> Optional[ContextLog]:
        """Get the currently active (non-ended) context."""
        return (
            db.query(ContextLog)
            .filter(
                ContextLog.user_id == user_id,
                ContextLog.ended_at.is_(None),
            )
            .order_by(ContextLog.started_at.desc())
            .first()
        )

    def get_active_context(self, db: Session, user_id: int) -> Optional[dict]:
        """Get the current active context for the frontend timer."""
        active = self._get_active_context(db, user_id)
        if not active:
            return None

        elapsed = int((datetime.utcnow() - active.started_at).total_seconds() / 60)
        return {
            "id": active.id,
            "context_name": active.context_name,
            "context_type": active.context_type,
            "started_at": str(active.started_at),
            "elapsed_minutes": elapsed,
            "task_complexity": active.task_complexity,
            "is_interruption": active.is_interruption,
        }

    # ======================== DEEP WORK DETECTION ========================

    def _check_deep_work(self, db: Session, ctx: ContextLog):
        """
        Check if a completed context qualifies as deep work.
        Criteria: 90+ minutes uninterrupted, deep_work type.
        """
        if not ctx.duration_minutes or ctx.duration_minutes < 45:
            return
        if ctx.is_interruption:
            return
        if ctx.context_type not in ("deep_work", "coding", "writing", "studying"):
            return

        # It's a deep work block
        block = DeepWorkBlock(
            user_id=ctx.user_id,
            context_log_id=ctx.id,
            block_date=ctx.started_at.date(),
            start_time=ctx.started_at.time(),
            end_time=ctx.ended_at.time() if ctx.ended_at else datetime.utcnow().time(),
            duration_minutes=ctx.duration_minutes,
            interruptions_count=0,
            flow_state_achieved=ctx.duration_minutes >= 90,
            output_quality=ctx.productivity_rating,
        )
        db.add(block)
        db.commit()

    def get_deep_work_blocks(
        self, db: Session, user_id: int = 1, days: int = 30
    ) -> list[dict]:
        """Get deep work blocks for charting."""
        start_date = datetime.now().date() - timedelta(days=days)
        blocks = (
            db.query(DeepWorkBlock)
            .filter(
                DeepWorkBlock.user_id == user_id,
                DeepWorkBlock.block_date >= start_date,
            )
            .order_by(DeepWorkBlock.block_date)
            .all()
        )

        return [
            {
                "id": b.id,
                "date": str(b.block_date),
                "start_time": str(b.start_time),
                "end_time": str(b.end_time),
                "duration_minutes": b.duration_minutes,
                "flow_state": b.flow_state_achieved,
                "output_quality": b.output_quality,
                "success_factors": b.success_factors or [],
            }
            for b in blocks
        ]

    # ======================== COGNITIVE LOAD ========================

    def _estimate_cognitive_load(
        self, complexity: Optional[int], duration: Optional[int], interrupted: bool
    ) -> int:
        """
        Estimate cognitive load (1-10) based on task complexity,
        duration, and interruption status.
        """
        base = complexity if complexity else 5
        # Duration factor: longer sessions = more cognitive fatigue
        duration_factor = 0
        if duration:
            if duration > 120:
                duration_factor = 3
            elif duration > 60:
                duration_factor = 2
            elif duration > 30:
                duration_factor = 1

        interruption_penalty = 2 if interrupted else 0

        load = min(10, max(1, base + duration_factor + interruption_penalty))
        return load

    # ======================== ANALYTICS ========================

    def get_daily_summary(
        self, db: Session, user_id: int = 1, date: Optional[str] = None
    ) -> dict:
        """Get context switching summary for a specific day."""
        target_date = (
            datetime.strptime(date, "%Y-%m-%d").date()
            if date
            else datetime.now().date()
        )
        start = datetime.combine(target_date, dt_time.min)
        end = datetime.combine(target_date, dt_time.max)

        contexts = (
            db.query(ContextLog)
            .filter(
                ContextLog.user_id == user_id,
                ContextLog.started_at >= start,
                ContextLog.started_at <= end,
            )
            .order_by(ContextLog.started_at)
            .all()
        )

        if not contexts:
            return {
                "date": str(target_date),
                "total_contexts": 0,
                "total_minutes": 0,
                "type_breakdown": {},
                "deep_work_minutes": 0,
                "interruptions": 0,
                "avg_cognitive_load": None,
                "contexts": [],
            }

        total_minutes = sum(c.duration_minutes or 0 for c in contexts)
        interruptions = sum(1 for c in contexts if c.is_interruption)
        cog_loads = [
            c.estimated_cognitive_load for c in contexts if c.estimated_cognitive_load
        ]

        # Type breakdown
        type_breakdown = {}
        for c in contexts:
            ctype = c.context_type or "other"
            type_breakdown[ctype] = type_breakdown.get(ctype, 0) + (
                c.duration_minutes or 0
            )

        deep_work_minutes = (
            type_breakdown.get("deep_work", 0)
            + type_breakdown.get("coding", 0)
            + type_breakdown.get("writing", 0)
        )

        return {
            "date": str(target_date),
            "total_contexts": len(contexts),
            "total_minutes": total_minutes,
            "type_breakdown": type_breakdown,
            "deep_work_minutes": deep_work_minutes,
            "interruptions": interruptions,
            "avg_cognitive_load": round(sum(cog_loads) / len(cog_loads), 1)
            if cog_loads
            else None,
            "contexts": [
                {
                    "id": c.id,
                    "name": c.context_name,
                    "type": c.context_type,
                    "started_at": str(c.started_at),
                    "ended_at": str(c.ended_at) if c.ended_at else None,
                    "duration_minutes": c.duration_minutes,
                    "is_interruption": c.is_interruption,
                    "cognitive_load": c.estimated_cognitive_load,
                    "productivity": c.productivity_rating,
                }
                for c in contexts
            ],
        }

    def get_optimal_work_times(
        self, db: Session, user_id: int = 1, days: int = 30
    ) -> dict:
        """
        Analyze context history to find optimal work times.
        Returns hour-by-hour productivity scores based on historical data.
        """
        start_date = datetime.now() - timedelta(days=days)

        contexts = (
            db.query(ContextLog)
            .filter(
                ContextLog.user_id == user_id,
                ContextLog.started_at >= start_date,
                ContextLog.ended_at.isnot(None),
                ContextLog.productivity_rating.isnot(None),
            )
            .all()
        )

        if not contexts:
            return {"hours": {}, "best_time": None, "worst_time": None}

        # Group productivity by hour of day
        hour_scores: dict[int, list] = {h: [] for h in range(24)}
        for c in contexts:
            hour = c.started_at.hour
            hour_scores[hour].append(c.productivity_rating)

        hour_avgs = {}
        for h, scores in hour_scores.items():
            if scores:
                hour_avgs[h] = round(sum(scores) / len(scores), 1)

        best_hour = max(hour_avgs, key=hour_avgs.get) if hour_avgs else None
        worst_hour = min(hour_avgs, key=hour_avgs.get) if hour_avgs else None

        return {
            "hours": hour_avgs,
            "best_time": f"{best_hour}:00" if best_hour is not None else None,
            "worst_time": f"{worst_hour}:00" if worst_hour is not None else None,
            "total_sessions_analyzed": len(contexts),
        }

    def get_attention_residue_analysis(
        self, db: Session, user_id: int = 1, days: int = 30
    ) -> dict:
        """
        Analyze attention residue: how much switching between different context
        types impacts productivity.
        """
        start_date = datetime.now() - timedelta(days=days)

        contexts = (
            db.query(ContextLog)
            .filter(
                ContextLog.user_id == user_id,
                ContextLog.started_at >= start_date,
                ContextLog.ended_at.isnot(None),
            )
            .order_by(ContextLog.started_at)
            .all()
        )

        if len(contexts) < 2:
            return {
                "switch_penalties": {},
                "avg_switch_cost_minutes": 0,
                "recommendation": None,
            }

        # Analyze transitions
        transitions = {}
        switch_costs = []
        for i in range(1, len(contexts)):
            prev_type = contexts[i - 1].context_type or "other"
            curr_type = contexts[i].context_type or "other"
            key = f"{prev_type} -> {curr_type}"

            if key not in transitions:
                transitions[key] = {"count": 0, "avg_switch_cost": 0, "total_cost": 0}

            transitions[key]["count"] += 1
            cost = contexts[i].switch_cost_minutes or 0
            transitions[key]["total_cost"] += cost
            switch_costs.append(cost)

        for key in transitions:
            t = transitions[key]
            t["avg_switch_cost"] = (
                round(t["total_cost"] / t["count"], 1) if t["count"] > 0 else 0
            )

        avg_cost = (
            round(sum(switch_costs) / len(switch_costs), 1) if switch_costs else 0
        )

        # Find most costly transitions
        sorted_transitions = sorted(
            transitions.items(), key=lambda x: -x[1]["avg_switch_cost"]
        )
        worst = sorted_transitions[0] if sorted_transitions else None

        recommendation = None
        if worst and worst[1]["avg_switch_cost"] > 10:
            recommendation = f"Your most costly context switch is '{worst[0]}' (avg {worst[1]['avg_switch_cost']} min). Consider batching similar tasks together."

        return {
            "switch_penalties": transitions,
            "avg_switch_cost_minutes": avg_cost,
            "total_switches": len(contexts) - 1,
            "recommendation": recommendation,
        }


# Singleton instance
context_switching_service = ContextSwitchingService()
