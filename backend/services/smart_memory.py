"""
Smart Memory Manager - Tiered Memory Strategy (Fix #4).

Manages memory across 4 tiers:
- Tier 1: Core Memory (~4000 chars, always active)
- Tier 2: Recent Memory (last 30 days)
- Tier 3: Archival Memory (all history, semantic search)
- Tier 4: Compressed Summaries (weekly/monthly/yearly)
"""

from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from models.journal import JournalEntry, MoodLog
from models.user import LettaMemory
from utils.embeddings import embed_query
from config import get_chroma_client, get_or_create_collection, GEMINI_API_KEY


class SmartMemoryManager:
    """
    Intelligent memory management with tiered approach (Fix #4).
    """

    def __init__(self, db: Session, letta_agent=None):
        self.db = db
        self.letta = letta_agent
        self._chroma_client = get_chroma_client()
        self._collection = get_or_create_collection(self._chroma_client)

    def update_core_memory_intelligently(self, user_id: int):
        """
        Automatically maintain core memory within limits.
        Only keep most important/recent info.
        """
        current_goals = self._get_active_goals(user_id)
        key_preferences = self._get_key_preferences(user_id)
        recent_context = self._get_recent_context(user_id)

        # Build optimized core memory (within 4000 char limit)
        human_block = self._build_human_block(
            goals=current_goals[:3],
            preferences=key_preferences[:10],
            context=recent_context,
        )

        if self.letta:
            try:
                self.letta.core_memory_replace("human", human_block)
            except Exception as e:
                print(f"⚠️ Core memory update failed: {e}")

        # Store locally as fallback
        self._save_memory_locally(user_id, "core", "human", human_block)

    def _build_human_block(self, goals, preferences, context) -> str:
        """Build concise human block (under 2000 chars)."""
        goals_str = "\n".join(f"- {g}" for g in goals) if goals else "- No active goals"
        prefs_str = "\n".join(f"- {p}" for p in preferences[:5]) if preferences else "- No preferences set"

        block = f"""Active Goals:
{goals_str}

Key Preferences:
{prefs_str}

Current Context (This Week):
- Mood avg: {context.get('avg_mood', 'N/A')}/10
- Energy: {context.get('energy_trend', 'N/A')}
- Focus: {context.get('current_focus', 'General')}
"""
        if len(block) > 1900:
            block = block[:1900] + "..."
        return block

    def smart_search_with_fallback(self, query: str, user_id: int, n_results: int = 5):
        """
        Multi-tiered search:
        1. Check core memory
        2. Search recent memory (recall)
        3. Semantic search archival (ChromaDB)
        4. Fall back to SQL if needed
        """
        results = {
            "core": [],
            "recent": [],
            "archival": [],
            "sql_fallback": [],
            "total_found": 0,
        }

        # Tier 1: Core memory (instant)
        core_results = self.db.query(LettaMemory).filter(
            LettaMemory.user_id == user_id,
            LettaMemory.memory_type == "core",
        ).all()
        for mem in core_results:
            if query.lower() in mem.memory_content.lower():
                results["core"].append(mem.memory_content)

        # Tier 2: Recent memory
        if self.letta:
            try:
                recent = self.letta.recall_memory_search(query, n=5)
                results["recent"] = recent
            except Exception:
                pass

        # Tier 3: Archival semantic search
        try:
            query_embedding = embed_query(query)
            archival = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
            )
            results["archival"] = archival.get("documents", [[]])[0]
        except Exception as e:
            print(f"⚠️ Archival search failed: {e}")

        # Tier 4: SQL fallback
        if len(results["archival"]) < 3:
            sql_results = (
                self.db.query(JournalEntry)
                .filter(
                    JournalEntry.user_id == user_id,
                    JournalEntry.content.contains(query),
                )
                .limit(5)
                .all()
            )
            results["sql_fallback"] = [e.content for e in sql_results]

        results["total_found"] = (
            len(results["core"])
            + len(results["recent"])
            + len(results["archival"])
            + len(results["sql_fallback"])
        )

        return results

    def create_periodic_summaries(self, user_id: int):
        """
        Create compressed summaries to preserve old knowledge.
        """
        week_entries = self._get_last_n_days_entries(user_id, 7)
        if not week_entries:
            return None

        weekly_summary = self._generate_summary(week_entries, summary_type="weekly")

        # Store summary in Letta memory table
        summary_mem = LettaMemory(
            user_id=user_id,
            memory_type="archival",
            memory_key=f"weekly_summary_{datetime.now().strftime('%Y_%W')}",
            memory_content=f"[WEEKLY SUMMARY] {weekly_summary}",
        )
        self.db.add(summary_mem)
        self.db.commit()

        # Add to Letta archival
        if self.letta:
            try:
                self.letta.archival_memory_insert(f"[WEEKLY SUMMARY] {weekly_summary}")
            except Exception:
                pass

        return weekly_summary

    def _generate_summary(self, entries, summary_type="weekly") -> str:
        """Use Gemini to generate compressed summary."""
        try:
            import google.generativeai as genai

            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel("gemini-2.0-flash")

            entries_text = "\n".join(e.content[:200] for e in entries[:10])
            prompt = f"""Summarize these {len(entries)} journal entries into a concise {summary_type} summary.
Focus on:
- Overall mood trends
- Key events
- Important decisions
- Pattern observations

Entries:
{entries_text}

Provide a 200-word maximum summary."""

            response = model.generate_content(prompt)
            return response.text

        except Exception as e:
            # Fallback: simple concatenation
            return f"Week of {datetime.now().strftime('%Y-%m-%d')}: {len(entries)} entries logged."

    def _get_active_goals(self, user_id: int) -> list:
        """Get active goal titles."""
        from models.goals import Goal

        goals = (
            self.db.query(Goal)
            .filter(Goal.user_id == user_id, Goal.status == "active")
            .limit(5)
            .all()
        )
        return [g.goal_title for g in goals]

    def _get_key_preferences(self, user_id: int) -> list:
        """Get user preferences."""
        from models.user import User

        user = self.db.query(User).get(user_id)
        if user and user.preferences:
            return list(user.preferences.values()) if isinstance(user.preferences, dict) else []
        return []

    def _get_recent_context(self, user_id: int) -> dict:
        """Get recent week context."""
        week_ago = datetime.now().date() - timedelta(days=7)
        recent_moods = (
            self.db.query(MoodLog)
            .filter(MoodLog.user_id == user_id, MoodLog.log_date >= week_ago)
            .all()
        )

        avg_mood = "N/A"
        if recent_moods:
            avg_mood = f"{sum(m.mood_value for m in recent_moods) / len(recent_moods):.1f}"

        return {
            "avg_mood": avg_mood,
            "energy_trend": "stable",
            "current_focus": "General",
        }

    def _get_last_n_days_entries(self, user_id: int, days: int):
        """Get entries from the last N days."""
        start_date = datetime.now().date() - timedelta(days=days)
        return (
            self.db.query(JournalEntry)
            .filter(
                JournalEntry.user_id == user_id,
                JournalEntry.entry_date >= start_date,
            )
            .all()
        )

    def _save_memory_locally(self, user_id: int, mem_type: str, key: str, content: str):
        """Save memory to local database for persistence."""
        existing = (
            self.db.query(LettaMemory)
            .filter(
                LettaMemory.user_id == user_id,
                LettaMemory.memory_type == mem_type,
                LettaMemory.memory_key == key,
            )
            .first()
        )

        if existing:
            existing.memory_content = content
            existing.updated_at = datetime.utcnow()
        else:
            mem = LettaMemory(
                user_id=user_id,
                memory_type=mem_type,
                memory_key=key,
                memory_content=content,
            )
            self.db.add(mem)

        self.db.commit()
