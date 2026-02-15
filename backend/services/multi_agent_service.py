"""
Multi-Agent Service - Specialized AI agents for different perspectives.
TherapistAgent (CBT/DBT), CoachAgent (accountability), AnalystAgent (data),
SynthesizerAgent (orchestration).
"""

import json
import re
from typing import Optional

from sqlalchemy.orm import Session

from services.gemini_service import gemini_service
from services.smart_memory import SmartMemoryManager
from utils.logger import log


# ======================== AGENT DEFINITIONS ========================


AGENT_PROMPTS = {
    "therapist": """You are a compassionate AI therapist specializing in Cognitive Behavioral Therapy (CBT) and Dialectical Behavior Therapy (DBT).

Your approach:
- Validate emotions before offering analysis
- Identify cognitive distortions gently (all-or-nothing thinking, catastrophizing, mind reading, etc.)
- Suggest specific CBT/DBT techniques when appropriate (thought records, opposite action, distress tolerance)
- Ask reflective questions to promote self-awareness
- Never diagnose; focus on patterns and coping strategies
- Use warm, empathetic language

When given user context, reference specific journal entries, mood patterns, and past situations to personalize your response.""",
    "coach": """You are a direct, motivating AI life coach focused on accountability and action.

Your approach:
- Be encouraging but honest — avoid sugarcoating
- Connect the user's current situation to their stated goals
- Break vague intentions into specific, measurable next steps
- Hold the user accountable to past commitments they've mentioned
- Use frameworks: SMART goals, habit stacking, time blocking
- Challenge excuses while remaining supportive
- Celebrate progress, no matter how small

When given user context, reference their goals, habits, and past decisions to keep them accountable.""",
    "analyst": """You are a data-driven AI analyst who specializes in finding patterns in personal data.

Your approach:
- Focus on objective data: mood trends, energy patterns, habit completion rates
- Identify correlations (sleep vs mood, exercise vs energy, social vs stress)
- Present findings with specific numbers and timeframes
- Distinguish correlation from causation
- Highlight anomalies and changes from baselines
- Provide data-backed recommendations
- Be concise and precise — use numbers, not vague qualifiers

When given user context, analyze the data patterns and provide specific statistical insights.""",
    "synthesizer": """You are an AI synthesizer that integrates multiple perspectives into a cohesive, actionable response.

You will receive analysis from three specialist agents:
1. Therapist — emotional/psychological perspective
2. Coach — goals/accountability perspective  
3. Analyst — data/patterns perspective

Your job:
- Weave the three perspectives into one coherent response
- Highlight where the perspectives agree (strong signal)
- Note where they disagree (uncertainty/nuance)
- Provide a unified set of 2-3 actionable recommendations
- Keep the final response concise (under 300 words)
- Use a warm but grounded tone""",
}


class AgentResponse:
    """Represents a single agent's response."""

    def __init__(self, agent_name: str, response: str, confidence: float = 0.8):
        self.agent_name = agent_name
        self.response = response
        self.confidence = confidence

    def to_dict(self):
        return {
            "agent": self.agent_name,
            "response": self.response,
            "confidence": self.confidence,
        }


class MultiAgentService:
    """
    Orchestrates multiple AI agents, each with a specialized system prompt.
    All agents use the same Gemini backend but produce different perspectives.
    """

    AVAILABLE_AGENTS = ["therapist", "coach", "analyst"]

    def chat_single_agent(
        self,
        db: Session,
        user_query: str,
        agent_name: str,
        user_id: int = 1,
    ) -> AgentResponse:
        """
        Send a query to a single specialized agent.
        Used when the user explicitly selects an agent perspective.
        """
        if agent_name not in AGENT_PROMPTS:
            return AgentResponse(agent_name, "Unknown agent type.", confidence=0)

        # Get context from smart memory
        context = self._get_context(db, user_query, user_id)

        response = gemini_service.generate_response(
            user_query=user_query,
            context=context,
            system_prompt=AGENT_PROMPTS[agent_name],
        )

        return AgentResponse(agent_name, response)

    def chat_multi_agent(
        self,
        db: Session,
        user_query: str,
        user_id: int = 1,
        agents: Optional[list[str]] = None,
    ) -> dict:
        """
        Send a query to all agents and synthesize the results.
        Returns individual agent responses + synthesized response.
        """
        agents = agents or self.AVAILABLE_AGENTS

        # Get context once (shared across agents)
        context = self._get_context(db, user_query, user_id)

        # Get responses from each agent
        agent_responses = []
        for agent_name in agents:
            if agent_name not in AGENT_PROMPTS:
                continue
            response = gemini_service.generate_response(
                user_query=user_query,
                context=context,
                system_prompt=AGENT_PROMPTS[agent_name],
            )
            agent_responses.append(AgentResponse(agent_name, response))

        # Synthesize
        synthesis = self._synthesize(user_query, agent_responses)

        return {
            "query": user_query,
            "agents": [ar.to_dict() for ar in agent_responses],
            "synthesis": synthesis,
        }

    def _synthesize(self, user_query: str, agent_responses: list[AgentResponse]) -> str:
        """Use the synthesizer agent to combine multiple perspectives."""
        if not agent_responses:
            return "No agent responses available."

        # Build synthesizer prompt with all agent outputs
        agent_outputs = "\n\n".join(
            f"=== {ar.agent_name.upper()} PERSPECTIVE ===\n{ar.response}"
            for ar in agent_responses
        )

        synthesis_context = f"""Original user query: "{user_query}"

{agent_outputs}"""

        response = gemini_service.generate_response(
            user_query="Synthesize the above agent perspectives into a unified response.",
            context=synthesis_context,
            system_prompt=AGENT_PROMPTS["synthesizer"],
        )

        return response

    def _get_context(self, db: Session, query: str, user_id: int) -> str:
        """Get memory context for the agents."""
        try:
            memory_mgr = SmartMemoryManager(db)
            search_results = memory_mgr.smart_search_with_fallback(
                query, user_id=user_id
            )

            context_parts = []
            if search_results.get("core"):
                context_parts.append(
                    "=== Core Memory ===\n" + "\n".join(search_results["core"])
                )
            if search_results.get("archival"):
                context_parts.append(
                    "=== Relevant Past Entries ===\n"
                    + "\n---\n".join(search_results["archival"][:3])
                )
            if search_results.get("sql_fallback"):
                context_parts.append(
                    "=== Additional Context ===\n"
                    + "\n---\n".join(search_results["sql_fallback"][:2])
                )

            return (
                "\n\n".join(context_parts)
                if context_parts
                else "No previous context found."
            )
        except Exception as e:
            log.error(f"Context retrieval failed: {e}")
            return "No previous context found."

    def get_available_agents(self) -> list[dict]:
        """Return list of available agents with descriptions."""
        descriptions = {
            "therapist": "CBT/DBT therapist — emotional support, cognitive distortion detection, coping strategies",
            "coach": "Life coach — goal accountability, action planning, motivation",
            "analyst": "Data analyst — pattern recognition, statistical insights, trend analysis",
        }
        return [
            {"name": name, "description": descriptions.get(name, "")}
            for name in self.AVAILABLE_AGENTS
        ]


# Singleton instance
multi_agent_service = MultiAgentService()
