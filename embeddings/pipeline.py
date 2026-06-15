"""
AI-003 — Embedding pipeline service.

Implements the three core operations required by the issue:
- embed_resume(resume_id, text) — chunk + embed + upsert to Qdrant
- embed_jd(jd_id, text) — same, for job descriptions
- semantic_similarity(resume_id, jd_id) — cosine similarity 0-1

Both resumes and JDs are stored in the same 'resume_embeddings'
collection, distinguished by a 'doc_type' field in the payload
('resume' | 'jd'). Each chunk becomes its own point in Qdrant,
linked back to its parent document via 'doc_id'.
"""

# import hashlib
import logging
import uuid

import numpy as np
from qdrant_client.http.models import (
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)

from embeddings.qdrant_client import get_qdrant_client, COLLECTION_NAME
from embeddings.embedding_model import chunk_text, embed_texts

logger = logging.getLogger(__name__)


def _point_id(doc_id: str, doc_type: str, chunk_index: int) -> str:
    """
    Deterministic point ID so re-embedding the same document
    overwrites old chunks instead of creating duplicates.

    Uses a UUID5 hash of (doc_type, doc_id, chunk_index) so it's
    a valid Qdrant point ID (Qdrant requires UUID or unsigned int).
    """
    raw = f"{doc_type}:{doc_id}:{chunk_index}"
    return str(uuid.uuid5(uuid.NAMESPACE_OID, raw))


def _delete_existing_chunks(doc_id: str, doc_type: str) -> None:
    """Remove any previously stored chunks for this document before re-embedding."""
    client = get_qdrant_client()
    client.delete(
        collection_name=COLLECTION_NAME,
        points_selector=Filter(
            must=[
                FieldCondition(key="doc_id", match=MatchValue(value=doc_id)),
                FieldCondition(key="doc_type", match=MatchValue(value=doc_type)),
            ]
        ),
    )


def _embed_document(doc_id: str, doc_type: str, text: str) -> int:
    """
    Shared implementation for embed_resume / embed_jd.

    Chunks the text, generates embeddings, and upserts each chunk
    as a separate point in Qdrant. Returns the number of chunks stored.
    """
    if not text or not text.strip():
        raise ValueError(f"Cannot embed empty text for {doc_type} '{doc_id}'")

    chunks = chunk_text(text)
    if not chunks:
        raise ValueError(f"Text produced no chunks for {doc_type} '{doc_id}'")

    vectors = embed_texts(chunks)

    # Remove old chunks first so stale data doesn't linger if the
    # document was previously embedded with a different chunk count.
    _delete_existing_chunks(doc_id, doc_type)

    points = [
        PointStruct(
            id=_point_id(doc_id, doc_type, i),
            vector=vector,
            payload={
                "doc_id": doc_id,
                "doc_type": doc_type,
                "chunk_index": i,
                "text": chunk,
            },
        )
        for i, (chunk, vector) in enumerate(zip(chunks, vectors))
    ]

    client = get_qdrant_client()
    client.upsert(collection_name=COLLECTION_NAME, points=points)

    logger.info("Embedded %s '%s' — %d chunk(s) stored", doc_type, doc_id, len(points))
    return len(points)


def embed_resume(resume_id: str, text: str) -> int:
    """
    Chunk and embed a resume's text, upserting vectors into Qdrant.

    Returns the number of chunks stored.
    """
    return _embed_document(resume_id, "resume", text)


def embed_jd(jd_id: str, text: str) -> int:
    """
    Chunk and embed a job description's text, upserting vectors into Qdrant.

    Returns the number of chunks stored.
    """
    return _embed_document(jd_id, "jd", text)


def _fetch_chunk_vectors(doc_id: str, doc_type: str) -> list[list[float]]:
    """Retrieve all stored chunk vectors for a given document."""
    client = get_qdrant_client()

    points, _ = client.scroll(
        collection_name=COLLECTION_NAME,
        scroll_filter=Filter(
            must=[
                FieldCondition(key="doc_id", match=MatchValue(value=doc_id)),
                FieldCondition(key="doc_type", match=MatchValue(value=doc_type)),
            ]
        ),
        with_vectors=True,
        limit=1000,
    )

    return [p.vector for p in points if p.vector is not None]


def _mean_vector(vectors: list[list[float]]) -> np.ndarray:
    """Average a list of vectors into a single representative vector."""
    arr = np.array(vectors)
    return arr.mean(axis=0)


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity between two vectors, clamped to [0, 1]."""
    denom = (np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return 0.0
    sim = float(np.dot(a, b) / denom)
    # Cosine similarity is in [-1, 1]; clamp/rescale to [0, 1]
    # for an intuitive 0-1 "match score".
    return max(0.0, min(1.0, (sim + 1.0) / 2.0))


def semantic_similarity(resume_id: str, jd_id: str) -> float:
    """
    Compute a 0-1 semantic similarity score between a resume and a JD.

    Both documents must have been embedded first via embed_resume()
    and embed_jd(). Each document's chunks are averaged into a single
    representative vector, then compared via cosine similarity.

    Raises ValueError if either document has no stored embeddings.
    """
    resume_vectors = _fetch_chunk_vectors(resume_id, "resume")
    jd_vectors = _fetch_chunk_vectors(jd_id, "jd")

    if not resume_vectors:
        raise ValueError(f"No embeddings found for resume '{resume_id}'. Call embed_resume first.")
    if not jd_vectors:
        raise ValueError(f"No embeddings found for jd '{jd_id}'. Call embed_jd first.")

    resume_vec = _mean_vector(resume_vectors)
    jd_vec = _mean_vector(jd_vectors)

    return round(_cosine_similarity(resume_vec, jd_vec), 4)
