"""
RAG Service - ChromaDB vector search.
Uses PersistentClient (Fix #2) and gemini-embedding-001 (Fix #1).
"""

from typing import Optional

from config import get_chroma_client, get_or_create_collection
from utils.embeddings import embed_document, embed_query


class RAGService:
    """
    Retrieval-Augmented Generation service using ChromaDB.
    Fix #2: Uses PersistentClient instead of deprecated duckdb+parquet config.
    """

    def __init__(self):
        self._client = get_chroma_client()
        self._collection = get_or_create_collection(self._client)

    def add_document(
        self,
        doc_id: str,
        content: str,
        metadata: Optional[dict] = None,
    ):
        """
        Add a document to the vector store.
        Embedding generated using gemini-embedding-001.
        """
        embedding = embed_document(content)
        self._collection.add(
            documents=[content],
            embeddings=[embedding],
            metadatas=[metadata or {}],
            ids=[doc_id],
        )

    def update_document(
        self,
        doc_id: str,
        content: str,
        metadata: Optional[dict] = None,
    ):
        """Update an existing document."""
        embedding = embed_document(content)
        self._collection.update(
            ids=[doc_id],
            documents=[content],
            embeddings=[embedding],
            metadatas=[metadata or {}],
        )

    def delete_document(self, doc_id: str):
        """Delete a document from the vector store."""
        try:
            self._collection.delete(ids=[doc_id])
        except Exception:
            pass

    def search(
        self,
        query: str,
        n_results: int = 5,
        where_filter: Optional[dict] = None,
    ) -> dict:
        """
        Semantic search using gemini-embedding-001 query embeddings.
        """
        query_embedding = embed_query(query)

        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_filter,
        )

        return {
            "documents": results.get("documents", [[]])[0],
            "metadatas": results.get("metadatas", [[]])[0],
            "distances": results.get("distances", [[]])[0],
            "ids": results.get("ids", [[]])[0],
        }

    def find_similar(self, doc_id: str, n_results: int = 5) -> dict:
        """Find documents similar to an existing document."""
        try:
            existing = self._collection.get(ids=[doc_id])
            if existing and existing["documents"]:
                return self.search(existing["documents"][0], n_results + 1)
        except Exception:
            pass
        return {"documents": [], "metadatas": [], "distances": [], "ids": []}

    def get_collection_count(self) -> int:
        """Get the number of documents in the collection."""
        return self._collection.count()


# Singleton instance
rag_service = RAGService()
