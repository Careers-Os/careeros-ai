"""
AI-003 — Qdrant client setup.

Provides a singleton Qdrant client and ensures the
'resume_embeddings' collection exists with the correct
vector configuration (384 dims, cosine distance) for
the all-MiniLM-L6-v2 sentence-transformers model.
"""

import os
import logging
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

logger = logging.getLogger(__name__)

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "resume_embeddings")

# all-MiniLM-L6-v2 produces 384-dimensional embeddings
VECTOR_SIZE = 384

_client: QdrantClient | None = None


def get_qdrant_client() -> QdrantClient:
    """Return a singleton Qdrant client instance."""
    global _client
    if _client is None:
        _client = QdrantClient(url=QDRANT_URL)
    return _client


def ensure_collection() -> None:
    """
    Create the resume_embeddings collection if it doesn't exist.

    Called once on FastAPI startup. Safe to call multiple times —
    checks existence first.
    """
    client = get_qdrant_client()

    existing = [c.name for c in client.get_collections().collections]

    if COLLECTION_NAME in existing:
        logger.info("Qdrant collection '%s' already exists", COLLECTION_NAME)
        return

    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
    )
    logger.info("Created Qdrant collection '%s' (size=%d, cosine)", COLLECTION_NAME, VECTOR_SIZE)
