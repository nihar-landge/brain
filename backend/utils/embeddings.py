"""
Embedding Generation Utilities.
Uses gemini-embedding-001 (Fix #1: replaces deprecated text-embedding-004).
"""

from config import generate_embedding as _generate_embedding


def embed_document(text: str) -> list:
    """
    Generate embedding for a document (for storage/indexing).
    Uses gemini-embedding-001 with retrieval_document task type.
    """
    return _generate_embedding(text, task_type="retrieval_document")


def embed_query(text: str) -> list:
    """
    Generate embedding for a search query.
    Uses gemini-embedding-001 with retrieval_query task type.
    """
    return _generate_embedding(text, task_type="retrieval_query")


def embed_for_similarity(text: str) -> list:
    """
    Generate embedding for semantic similarity comparison.
    Uses gemini-embedding-001 with semantic_similarity task type.
    """
    return _generate_embedding(text, task_type="semantic_similarity")


def embed_for_classification(text: str) -> list:
    """
    Generate embedding for classification.
    Uses gemini-embedding-001 with classification task type.
    """
    return _generate_embedding(text, task_type="classification")
