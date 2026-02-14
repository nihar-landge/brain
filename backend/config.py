"""
Personal AI Memory & Prediction System - Configuration
All critical fixes applied:
- Fix #1: Using gemini-embedding-001 (not deprecated text-embedding-004)
- Fix #2: Using ChromaDB PersistentClient (not deprecated duckdb+parquet)
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ======================== ENVIRONMENT ========================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/database.db")
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./data/chromadb")
API_SECRET_KEY = os.getenv("API_SECRET_KEY", "")  # Empty = auth disabled (dev mode)

# ======================== GEMINI CONFIGURATION ========================

# Embedding model: gemini-embedding-001 (user-specified, replaces text-embedding-004)
EMBEDDING_MODEL = "models/gemini-embedding-001"
EMBEDDING_DIM = 768
EMBEDDING_CHUNK_SIZE = 2000

# LLM model for conversations & insights
LLM_MODEL = "gemini-2.0-flash"
LLM_CONTEXT_WINDOW = 32000

# ======================== LETTA CONFIGURATION ========================


def get_letta_config():
    """
    Get production-ready Letta configuration.
    Fix #1: Uses gemini-embedding-001 instead of deprecated text-embedding-004.
    """
    try:
        from letta import LLMConfig, EmbeddingConfig

        llm_config = LLMConfig(
            model=LLM_MODEL,
            model_endpoint_type="google_ai",
            context_window=LLM_CONTEXT_WINDOW,
        )

        embedding_config = EmbeddingConfig(
            embedding_model="gemini-embedding-001",  # Fix #1
            embedding_endpoint_type="google_ai",
            embedding_dim=EMBEDDING_DIM,
            embedding_chunk_size=EMBEDDING_CHUNK_SIZE,
        )

        return llm_config, embedding_config

    except ImportError:
        print("⚠️  Letta not installed. Memory features will be limited.")
        return None, None


# ======================== CHROMADB CONFIGURATION ========================


def get_chroma_client():
    """
    Get production-ready ChromaDB client.
    Fix #2: Uses PersistentClient instead of deprecated duckdb+parquet config.
    """
    import chromadb
    from chromadb.config import Settings as ChromaSettings

    os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)

    client = chromadb.PersistentClient(
        path=CHROMA_PERSIST_DIR,
        settings=ChromaSettings(
            anonymized_telemetry=False,
            allow_reset=False,  # Safety: prevent accidental deletion
        ),
    )

    return client


def get_or_create_collection(client, name="journal_entries"):
    """Get or create a ChromaDB collection."""
    try:
        collection = client.get_collection(name=name)
    except Exception:
        collection = client.create_collection(
            name=name,
            metadata={
                "description": "User journal entries",
                "embedding_model": "gemini-embedding-001",
                "embedding_dimension": str(EMBEDDING_DIM),
            },
            embedding_function=None,  # Use custom embeddings
        )
    return collection


# ======================== EMBEDDING GENERATION ========================


def generate_embedding(text: str, task_type: str = "retrieval_document") -> list:
    """
    Generate embedding using gemini-embedding-001 model.
    Fix #1: Uses gemini-embedding-001 instead of deprecated text-embedding-004.

    Args:
        text: Text to embed
        task_type: One of: retrieval_document, retrieval_query,
                   semantic_similarity, classification, clustering
    Returns:
        List of floats (768-dim vector)
    """
    import google.generativeai as genai

    genai.configure(api_key=GEMINI_API_KEY)

    result = genai.embed_content(
        model=EMBEDDING_MODEL,  # models/gemini-embedding-001
        content=text,
        task_type=task_type,
    )
    return result["embedding"]


# ======================== APPLICATION SETTINGS ========================

APP_TITLE = "Personal AI Memory & Prediction System"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = (
    "A personal AI assistant with long-term memory, predictions, and insights"
)

# CORS
CORS_ORIGINS = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]

# Add production origin from environment (e.g. "http://your-ec2-ip" or "https://yourdomain.com")
_extra_origin = os.getenv("CORS_ORIGIN", "")
if _extra_origin:
    CORS_ORIGINS.append(_extra_origin)

# ML Settings
ML_MIN_SAMPLES = {
    "mood": 30,
    "habit": 20,
    "energy": 40,
    "decision": 10,
}

ML_MODELS_DIR = "./ml/models"
