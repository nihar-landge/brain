"""
Letta (MemGPT) Service - Long-term memory management.
Uses gemini-embedding-001 for embeddings (Fix #1).
"""

from typing import Optional

from config import get_letta_config, GEMINI_API_KEY


class LettaService:
    """
    Manages the Letta (MemGPT) agent for long-term memory.
    """

    def __init__(self):
        self.client = None
        self.agent = None
        self._initialized = False

    def initialize(self):
        """Initialize Letta client and agent."""
        if self._initialized:
            return

        try:
            from letta import create_client

            self.client = create_client()
            llm_config, embedding_config = get_letta_config()

            if llm_config is None:
                print("⚠️ Letta config unavailable. Memory features disabled.")
                return

            # Check for existing agent
            agents = self.client.list_agents()
            for agent in agents:
                if agent.name == "PersonalMemoryAgent":
                    self.agent = agent
                    self._initialized = True
                    print("✅ Letta agent loaded: PersonalMemoryAgent")
                    return

            # Create new agent
            self.agent = self.client.create_agent(
                name="PersonalMemoryAgent",
                llm_config=llm_config,
                embedding_config=embedding_config,
                memory={
                    "human": "User profile and preferences - initially empty",
                    "persona": (
                        "You are a personal AI assistant that remembers everything "
                        "about the user. You provide personalized insights and advice "
                        "based on their journal entries, mood patterns, habits, and goals."
                    ),
                },
                system=(
                    "You have access to the user's complete history through your memory. "
                    "Use archival memory to search past entries. Use core memory for "
                    "current context and goals. Always be supportive and insightful."
                ),
            )
            self._initialized = True
            print("✅ Letta agent created: PersonalMemoryAgent")

        except ImportError:
            print("⚠️ Letta not installed. Running without long-term memory.")
        except Exception as e:
            print(f"⚠️ Letta initialization failed: {e}")

    def send_message(self, message: str) -> Optional[str]:
        """Send message to Letta agent and get response."""
        if not self._initialized or not self.agent:
            return None

        try:
            response = self.agent.user_message(message)
            return response
        except Exception as e:
            print(f"⚠️ Letta message failed: {e}")
            return None

    def insert_memory(self, text: str):
        """Insert text into archival memory."""
        if not self._initialized or not self.agent:
            return

        try:
            self.agent.archival_memory_insert(text)
        except Exception as e:
            print(f"⚠️ Archival memory insert failed: {e}")

    def search_memory(self, query: str, n_results: int = 5) -> list:
        """Search archival memory."""
        if not self._initialized or not self.agent:
            return []

        try:
            results = self.agent.archival_memory_search(query)
            return results[:n_results]
        except Exception as e:
            print(f"⚠️ Archival memory search failed: {e}")
            return []

    def get_core_memory(self, key: str = "human") -> Optional[str]:
        """Get core memory block."""
        if not self._initialized or not self.agent:
            return None

        try:
            return self.agent.core_memory_get(key)
        except Exception:
            return None

    def update_core_memory(self, key: str, content: str):
        """Update core memory block."""
        if not self._initialized or not self.agent:
            return

        try:
            self.agent.core_memory_replace(key, content)
        except Exception as e:
            print(f"⚠️ Core memory update failed: {e}")


# Singleton instance
letta_service = LettaService()
