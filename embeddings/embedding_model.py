"""
AI-003 — Embedding model wrapper.

Wraps sentence-transformers (all-MiniLM-L6-v2) and provides
text chunking so long resumes/JDs are split into manageable
pieces before embedding.
"""

import logging
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

MODEL_NAME = "all-MiniLM-L6-v2"

# Chunking config — roughly 200 words per chunk with overlap
# to preserve context across chunk boundaries.
CHUNK_SIZE_WORDS = 200
CHUNK_OVERLAP_WORDS = 30

_model: SentenceTransformer | None = None


def get_model() -> SentenceTransformer:
    """
    Lazily load the sentence-transformers model.

    Loaded once and reused — loading the model is the expensive
    part (downloads + initializes weights on first call).
    """
    global _model
    if _model is None:
        logger.info("Loading sentence-transformers model: %s", MODEL_NAME)
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE_WORDS,
               overlap: int = CHUNK_OVERLAP_WORDS) -> list[str]:
    """
    Split text into overlapping word-based chunks.

    Returns a list of chunk strings. If the text is shorter than
    chunk_size, returns a single-element list with the whole text.
    """
    words = text.split()

    if len(words) <= chunk_size:
        return [text.strip()] if text.strip() else []

    chunks = []
    step = chunk_size - overlap
    for start in range(0, len(words), step):
        chunk_words = words[start:start + chunk_size]
        if not chunk_words:
            break
        chunks.append(" ".join(chunk_words))
        if start + chunk_size >= len(words):
            break

    return chunks


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Generate embeddings for a list of text chunks.

    Returns a list of 384-dimensional float vectors, one per input text.
    """
    if not texts:
        return []

    model = get_model()
    embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
    return embeddings.tolist()
