"""
Social Graph Service - People extraction, relationship analysis, social battery.
Uses Gemini for NER (named entity recognition) from journal entries,
and NetworkX for graph analysis.
"""

import json
import re
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import func

from models.social import Person, SocialInteraction, SocialBatteryLog
from models.journal import JournalEntry, Event, Decision, MoodLog
from services.gemini_service import gemini_service
from utils.logger import log


class SocialGraphService:
    """
    Manages the social graph: extraction, analysis, toxic pattern detection,
    social battery tracking, and relationship insights.
    """

    def __init__(self):
        self._nx = None  # Lazy-load networkx

    def _ensure_networkx(self):
        if self._nx is None:
            try:
                import networkx as nx

                self._nx = nx
            except ImportError:
                log.warning("networkx not installed, graph analysis unavailable")
        return self._nx

    # ======================== EXTRACTION ========================

    def extract_people_from_entry(self, entry_content: str) -> list[dict]:
        """
        Use Gemini to extract people mentioned in a journal entry.
        Returns list of dicts: [{name, relationship_type, sentiment, context}]
        """
        prompt = f"""Extract all people mentioned in this journal entry.
For each person, provide:
- name: their name (first name or full name)
- relationship_type: one of [friend, family, colleague, mentor, partner, acquaintance, other]
- sentiment: one of [positive, negative, neutral, mixed]
- context: brief description of what they did or their role in the entry (max 20 words)

Journal entry:
\"\"\"{entry_content}\"\"\"

Return ONLY a JSON array. If no people are mentioned, return [].
Example: [{{"name": "Sarah", "relationship_type": "friend", "sentiment": "positive", "context": "had coffee together"}}]"""

        try:
            raw = gemini_service._generate_with_retry(prompt)
            # Extract JSON from response (handle markdown code blocks)
            json_match = re.search(r"\[.*\]", raw, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return []
        except Exception as e:
            log.error(f"People extraction failed: {e}")
            return []

    def process_journal_entry(self, db: Session, entry_id: int, user_id: int = 1):
        """
        Process a journal entry to extract and store people + interactions.
        Called after a new journal entry is created/updated.
        """
        entry = (
            db.query(JournalEntry)
            .filter(
                JournalEntry.id == entry_id,
                JournalEntry.user_id == user_id,
            )
            .first()
        )
        if not entry:
            return

        people_data = self.extract_people_from_entry(entry.content)

        for p in people_data:
            person = self._get_or_create_person(
                db, user_id, p["name"], p.get("relationship_type")
            )
            person.total_mentions = (person.total_mentions or 0) + 1

            # Create interaction record
            sentiment_to_mood = {"positive": 7, "negative": 3, "neutral": 5, "mixed": 5}
            sentiment_to_drain = {
                "positive": 3,
                "negative": -3,
                "neutral": 0,
                "mixed": -1,
            }

            interaction = SocialInteraction(
                user_id=user_id,
                journal_entry_id=entry.id,
                person_id=person.id,
                interaction_date=entry.entry_date,
                mood_after=entry.mood,
                energy_after=entry.energy_level,
                draining_vs_energizing=sentiment_to_drain.get(
                    p.get("sentiment", "neutral"), 0
                ),
                notes=p.get("context"),
            )
            db.add(interaction)

        db.commit()

    def _get_or_create_person(
        self,
        db: Session,
        user_id: int,
        name: str,
        relationship_type: Optional[str] = None,
    ) -> Person:
        """Find existing person by name (case-insensitive) or create new."""
        person = (
            db.query(Person)
            .filter(
                Person.user_id == user_id,
                func.lower(Person.name) == name.lower().strip(),
            )
            .first()
        )

        if not person:
            person = Person(
                user_id=user_id,
                name=name.strip(),
                relationship_type=relationship_type,
                first_mentioned_date=datetime.now().date(),
                total_mentions=0,
            )
            db.add(person)
            db.flush()  # Get ID without committing

        return person

    # ======================== ANALYSIS ========================

    def get_social_graph(self, db: Session, user_id: int = 1) -> dict:
        """
        Build and return the social graph with nodes (people) and edges (interactions).
        Suitable for frontend force-directed graph visualization.
        """
        people = (
            db.query(Person)
            .filter(
                Person.user_id == user_id,
                Person.is_active == True,
            )
            .all()
        )

        if not people:
            return {"nodes": [], "edges": [], "stats": {}}

        nodes = []
        for p in people:
            avg_impact = self._calculate_mood_impact(db, p.id, user_id)
            nodes.append(
                {
                    "id": p.id,
                    "name": p.name,
                    "relationship_type": p.relationship_type or "other",
                    "total_mentions": p.total_mentions or 0,
                    "avg_mood_impact": avg_impact,
                    "energy_impact": p.energy_impact,
                    "tags": p.tags or [],
                    "interaction_frequency": p.interaction_frequency,
                }
            )

        # Build edges: people who appear in same journal entries
        edges = self._build_co_occurrence_edges(db, user_id, people)

        # Graph stats
        stats = self._compute_graph_stats(db, user_id, people)

        return {"nodes": nodes, "edges": edges, "stats": stats}

    def _calculate_mood_impact(
        self, db: Session, person_id: int, user_id: int
    ) -> Optional[float]:
        """Calculate average mood impact of interactions with a person."""
        interactions = (
            db.query(SocialInteraction)
            .filter(
                SocialInteraction.person_id == person_id,
                SocialInteraction.user_id == user_id,
            )
            .all()
        )

        if not interactions:
            return None

        impacts = [
            i.draining_vs_energizing
            for i in interactions
            if i.draining_vs_energizing is not None
        ]
        return round(sum(impacts) / len(impacts), 2) if impacts else None

    def _build_co_occurrence_edges(
        self, db: Session, user_id: int, people: list
    ) -> list:
        """Find people who co-occur in the same journal entries."""
        edges = []
        interactions = (
            db.query(SocialInteraction)
            .filter(
                SocialInteraction.user_id == user_id,
                SocialInteraction.journal_entry_id.isnot(None),
            )
            .all()
        )

        # Group by journal_entry_id
        entry_people: dict[int, list[int]] = {}
        for inter in interactions:
            entry_id = inter.journal_entry_id
            if entry_id not in entry_people:
                entry_people[entry_id] = []
            if inter.person_id not in entry_people[entry_id]:
                entry_people[entry_id].append(inter.person_id)

        # Create edges for co-occurrences
        seen = set()
        for entry_id, person_ids in entry_people.items():
            for i in range(len(person_ids)):
                for j in range(i + 1, len(person_ids)):
                    pair = tuple(sorted([person_ids[i], person_ids[j]]))
                    if pair not in seen:
                        seen.add(pair)
                        edges.append(
                            {
                                "source": pair[0],
                                "target": pair[1],
                                "weight": 1,
                            }
                        )
                    else:
                        # Increment weight for existing edge
                        for e in edges:
                            if (e["source"], e["target"]) == pair:
                                e["weight"] += 1
                                break

        return edges

    def _compute_graph_stats(self, db: Session, user_id: int, people: list) -> dict:
        """Compute summary statistics for the social graph."""
        total_interactions = (
            db.query(SocialInteraction)
            .filter(
                SocialInteraction.user_id == user_id,
            )
            .count()
        )

        # Most mentioned person
        most_mentioned = (
            max(people, key=lambda p: p.total_mentions or 0) if people else None
        )

        return {
            "total_people": len(people),
            "total_interactions": total_interactions,
            "most_mentioned": most_mentioned.name if most_mentioned else None,
            "relationship_breakdown": self._relationship_breakdown(people),
        }

    def _relationship_breakdown(self, people: list) -> dict:
        """Count people by relationship type."""
        breakdown = {}
        for p in people:
            rtype = p.relationship_type or "other"
            breakdown[rtype] = breakdown.get(rtype, 0) + 1
        return breakdown

    # ======================== TOXIC PATTERN DETECTION ========================

    def detect_toxic_patterns(self, db: Session, user_id: int = 1) -> list[dict]:
        """
        Analyze interactions to detect potentially toxic or draining relationships.
        Returns list of warnings with person details and evidence.
        """
        warnings = []
        people = (
            db.query(Person)
            .filter(
                Person.user_id == user_id,
                Person.is_active == True,
            )
            .all()
        )

        for person in people:
            interactions = (
                db.query(SocialInteraction)
                .filter(
                    SocialInteraction.person_id == person.id,
                    SocialInteraction.user_id == user_id,
                )
                .order_by(SocialInteraction.interaction_date.desc())
                .limit(20)
                .all()
            )

            if len(interactions) < 3:
                continue

            # Check for consistently draining interactions
            drain_scores = [
                i.draining_vs_energizing
                for i in interactions
                if i.draining_vs_energizing is not None
            ]
            if drain_scores and len(drain_scores) >= 3:
                avg_drain = sum(drain_scores) / len(drain_scores)
                if avg_drain <= -2:
                    warnings.append(
                        {
                            "person_id": person.id,
                            "person_name": person.name,
                            "pattern": "consistently_draining",
                            "severity": "high" if avg_drain <= -3 else "medium",
                            "avg_drain_score": round(avg_drain, 2),
                            "interaction_count": len(drain_scores),
                            "suggestion": f"Interactions with {person.name} consistently lower your energy. Consider setting boundaries or reducing interaction frequency.",
                        }
                    )

            # Check for mood drops after interaction
            mood_drops = [
                (i.mood_before - i.mood_after)
                for i in interactions
                if i.mood_before is not None and i.mood_after is not None
            ]
            if mood_drops and len(mood_drops) >= 3:
                avg_drop = sum(mood_drops) / len(mood_drops)
                if avg_drop >= 2:
                    warnings.append(
                        {
                            "person_id": person.id,
                            "person_name": person.name,
                            "pattern": "mood_drop_after_interaction",
                            "severity": "high" if avg_drop >= 3 else "medium",
                            "avg_mood_drop": round(avg_drop, 2),
                            "interaction_count": len(mood_drops),
                            "suggestion": f"Your mood tends to drop after interacting with {person.name}. Reflect on what specifically triggers this.",
                        }
                    )

        return warnings

    # ======================== SOCIAL BATTERY ========================

    def log_social_battery(
        self,
        db: Session,
        user_id: int,
        battery_level: int,
        solo_minutes: int = 0,
        social_minutes: int = 0,
    ) -> SocialBatteryLog:
        """Log current social battery level."""
        today = datetime.now().date()

        # Upsert for today
        existing = (
            db.query(SocialBatteryLog)
            .filter(
                SocialBatteryLog.user_id == user_id,
                SocialBatteryLog.log_date == today,
            )
            .first()
        )

        if existing:
            existing.battery_level = battery_level
            existing.solo_time_minutes = solo_minutes
            existing.social_time_minutes = social_minutes
            log_entry = existing
        else:
            log_entry = SocialBatteryLog(
                user_id=user_id,
                log_date=today,
                battery_level=battery_level,
                solo_time_minutes=solo_minutes,
                social_time_minutes=social_minutes,
            )
            db.add(log_entry)

        db.commit()
        db.refresh(log_entry)
        return log_entry

    def get_social_battery_history(
        self, db: Session, user_id: int = 1, days: int = 30
    ) -> list[dict]:
        """Get social battery history for charting."""
        start_date = datetime.now().date() - timedelta(days=days)
        logs = (
            db.query(SocialBatteryLog)
            .filter(
                SocialBatteryLog.user_id == user_id,
                SocialBatteryLog.log_date >= start_date,
            )
            .order_by(SocialBatteryLog.log_date)
            .all()
        )

        return [
            {
                "date": str(l.log_date),
                "battery_level": l.battery_level,
                "solo_minutes": l.solo_time_minutes,
                "social_minutes": l.social_time_minutes,
                "optimal_solo_ratio": l.optimal_solo_ratio,
            }
            for l in logs
        ]

    # ======================== PERSON IMPACT REFRESH ========================

    def refresh_person_metrics(self, db: Session, person_id: int, user_id: int = 1):
        """Recalculate aggregated metrics for a person based on their interactions."""
        person = (
            db.query(Person)
            .filter(Person.id == person_id, Person.user_id == user_id)
            .first()
        )
        if not person:
            return

        interactions = (
            db.query(SocialInteraction)
            .filter(
                SocialInteraction.person_id == person_id,
                SocialInteraction.user_id == user_id,
            )
            .all()
        )

        if not interactions:
            return

        # Average mood impact
        mood_impacts = [
            i.draining_vs_energizing
            for i in interactions
            if i.draining_vs_energizing is not None
        ]
        if mood_impacts:
            person.avg_mood_impact = round(sum(mood_impacts) / len(mood_impacts), 2)

        # Energy impact
        energy_vals = [
            i.energy_after for i in interactions if i.energy_after is not None
        ]
        if energy_vals:
            person.energy_impact = round(sum(energy_vals) / len(energy_vals), 2)

        # Interaction frequency
        if len(interactions) >= 2:
            dates = sorted([i.interaction_date for i in interactions])
            span_days = (dates[-1] - dates[0]).days or 1
            avg_gap = span_days / len(interactions)
            if avg_gap <= 2:
                person.interaction_frequency = "daily"
            elif avg_gap <= 8:
                person.interaction_frequency = "weekly"
            elif avg_gap <= 35:
                person.interaction_frequency = "monthly"
            else:
                person.interaction_frequency = "rare"

        db.commit()

    # ======================== NETWORK ANALYSIS ========================

    def get_network_analysis(self, db: Session, user_id: int = 1) -> dict:
        """
        Use NetworkX to compute graph metrics: centrality, clusters, etc.
        Returns analysis results for the frontend.
        """
        nx = self._ensure_networkx()
        if not nx:
            return {"error": "networkx not available"}

        graph_data = self.get_social_graph(db, user_id)
        if not graph_data["nodes"]:
            return {"centrality": {}, "clusters": [], "density": 0}

        G = nx.Graph()
        for node in graph_data["nodes"]:
            G.add_node(node["id"], **node)
        for edge in graph_data["edges"]:
            G.add_edge(edge["source"], edge["target"], weight=edge.get("weight", 1))

        # Metrics
        result = {
            "density": round(nx.density(G), 3) if len(G.nodes) > 1 else 0,
            "num_components": nx.number_connected_components(G)
            if len(G.nodes) > 0
            else 0,
        }

        if len(G.nodes) > 1 and len(G.edges) > 0:
            centrality = nx.degree_centrality(G)
            result["centrality"] = {
                str(k): round(v, 3)
                for k, v in sorted(centrality.items(), key=lambda x: -x[1])
            }
            betweenness = nx.betweenness_centrality(G)
            result["betweenness"] = {
                str(k): round(v, 3)
                for k, v in sorted(betweenness.items(), key=lambda x: -x[1])
            }
        else:
            result["centrality"] = {}
            result["betweenness"] = {}

        return result


# Singleton instance
social_graph_service = SocialGraphService()
