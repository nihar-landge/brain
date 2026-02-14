"""
Data Manager Service - Single Source of Truth Pattern (Fix #3).

SQLite is the master data store. ChromaDB stores only vectors/IDs.
Letta stores only references. All writes go through this manager to
ensure consistency across all stores.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from models.journal import JournalEntry, MoodLog
from utils.embeddings import embed_document, embed_query
from config import get_chroma_client, get_or_create_collection


class DataManager:
    """
    Manages data consistency across SQLite, ChromaDB, and Letta.
    SQLite is the single source of truth (Fix #3).
    """

    def __init__(self, db: Session, letta_agent=None):
        self.db = db
        self.letta = letta_agent

        # Initialize ChromaDB
        self._chroma_client = get_chroma_client()
        self._collection = get_or_create_collection(self._chroma_client)

    def create_journal_entry(
        self,
        user_id: int,
        content: str,
        mood: Optional[int] = None,
        energy_level: Optional[int] = None,
        stress_level: Optional[int] = None,
        title: Optional[str] = None,
        tags: Optional[list] = None,
        category: Optional[str] = None,
    ) -> JournalEntry:
        """
        Create journal entry with full consistency across all stores.
        """
        try:
            # 1. MASTER: Save to SQLite (single source of truth)
            entry = JournalEntry(
                user_id=user_id,
                content=content,
                mood=mood,
                energy_level=energy_level,
                stress_level=stress_level,
                title=title,
                tags=tags,
                category=category,
                entry_date=datetime.now().date(),
                entry_time=datetime.now().time(),
            )
            self.db.add(entry)
            self.db.commit()
            self.db.refresh(entry)

            # 2. INDEX: Add to ChromaDB (vector search)
            try:
                embedding = embed_document(content)
                self._collection.add(
                    documents=[content],
                    embeddings=[embedding],
                    metadatas=[
                        {
                            "entry_id": entry.id,
                            "date": str(entry.entry_date),
                            "mood": mood or 0,
                            "user_id": user_id,
                        }
                    ],
                    ids=[f"entry_{entry.id}"],
                )
            except Exception as e:
                print(f"⚠️ ChromaDB indexing failed: {e}")

            # 3. MEMORY: Update Letta (references only)
            if self.letta:
                try:
                    short_ref = f"[Entry #{entry.id}] {content[:200]}..."
                    self.letta.archival_memory_insert(short_ref)

                    # If significant, update core memory
                    if self._is_significant(entry):
                        self._update_letta_core_memory(entry)
                except Exception as e:
                    print(f"⚠️ Letta memory update failed: {e}")

            # 4. Create mood log if mood provided
            if mood is not None:
                mood_log = MoodLog(
                    user_id=user_id,
                    journal_entry_id=entry.id,
                    log_date=datetime.now().date(),
                    log_time=datetime.now().time(),
                    mood_value=mood,
                    energy_level=energy_level,
                    stress_level=stress_level,
                )
                self.db.add(mood_log)
                self.db.commit()

            return entry

        except Exception as e:
            self.db.rollback()
            raise e

    def update_journal_entry(self, entry_id: int, **updates) -> Optional[JournalEntry]:
        """
        Update with consistency across all stores.
        """
        # 1. Update SQLite (master)
        entry = self.db.query(JournalEntry).get(entry_id)
        if not entry:
            return None

        for key, value in updates.items():
            if hasattr(entry, key):
                setattr(entry, key, value)
        entry.updated_at = datetime.utcnow()
        self.db.commit()

        # 2. Update ChromaDB index
        if "content" in updates:
            try:
                embedding = embed_document(updates["content"])
                self._collection.update(
                    ids=[f"entry_{entry_id}"],
                    documents=[updates["content"]],
                    embeddings=[embedding],
                    metadatas=[{"entry_id": entry_id, "updated": True}],
                )
            except Exception as e:
                print(f"⚠️ ChromaDB update failed: {e}")

        # 3. Letta memory update
        if self.letta:
            try:
                self.letta.archival_memory_insert(
                    f"[Updated Entry #{entry_id}] {entry.content[:200]}..."
                )
            except Exception:
                pass

        return entry

    def delete_journal_entry(self, entry_id: int) -> bool:
        """
        Delete with consistency (CASCADE across all stores).
        """
        entry = self.db.query(JournalEntry).get(entry_id)
        if not entry:
            return False

        # 1. Delete from SQLite (master)
        self.db.delete(entry)
        self.db.commit()

        # 2. Delete from ChromaDB
        try:
            self._collection.delete(ids=[f"entry_{entry_id}"])
        except Exception:
            pass

        # 3. Letta note
        if self.letta:
            try:
                self.letta.archival_memory_insert(
                    f"[DELETED] Entry #{entry_id} was removed on {datetime.now()}"
                )
            except Exception:
                pass

        return True

    def search_similar(self, query: str, n_results: int = 5, mood_min: Optional[int] = None):
        """
        Semantic search across journal entries using ChromaDB.
        Uses gemini-embedding-001 for query embedding.
        """
        try:
            query_embedding = embed_query(query)

            where_filter = None
            if mood_min is not None:
                where_filter = {"mood": {"$gte": mood_min}}

            results = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where_filter,
            )

            # Enrich with full SQLite data
            enriched = []
            if results["ids"] and results["ids"][0]:
                for i, doc_id in enumerate(results["ids"][0]):
                    entry_id = int(doc_id.replace("entry_", ""))
                    entry = self.db.query(JournalEntry).get(entry_id)
                    if entry:
                        enriched.append(
                            {
                                "entry": entry,
                                "distance": results["distances"][0][i] if results["distances"] else None,
                                "document": results["documents"][0][i] if results["documents"] else None,
                            }
                        )

            return enriched

        except Exception as e:
            print(f"⚠️ Search failed: {e}")
            return []

    def get_entry_with_context(self, entry_id: int):
        """Retrieve entry with full context from all sources."""
        entry = self.db.query(JournalEntry).get(entry_id)
        if not entry:
            return None

        # Get similar entries
        similar = self.search_similar(entry.content, n_results=5)

        return {
            "entry": entry,
            "similar_entries": [s for s in similar if s["entry"].id != entry_id],
        }

    def _is_significant(self, entry: JournalEntry) -> bool:
        """Determine if entry should update core memory."""
        if entry.content and "goal" in entry.content.lower():
            return True
        if entry.mood is not None and (entry.mood >= 9 or entry.mood <= 3):
            return True
        return False

    def _update_letta_core_memory(self, entry: JournalEntry):
        """Update Letta's core memory for significant entries."""
        if self.letta and "goal" in (entry.content or "").lower():
            try:
                current_goals = self.letta.core_memory_get("goals")
                self.letta.core_memory_replace(
                    "goals",
                    f"{current_goals}\n- New goal from Entry #{entry.id}",
                )
            except Exception:
                pass
