"""
AI-003 — FastAPI router for the embedding pipeline.

Endpoints:
- POST /embed/resume        -> embed_resume()
- POST /embed/jd            -> embed_jd()
- POST /embed/similarity    -> semantic_similarity()
"""

import logging

from fastapi import APIRouter, HTTPException

from api.schemas import (
    EmbedResumeRequest,
    EmbedJdRequest,
    EmbedResponse,
    SimilarityRequest,
    SimilarityResponse,
)
from embeddings.pipeline import embed_resume, embed_jd, semantic_similarity

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/embed", tags=["Embeddings"])


@router.post("/resume", response_model=EmbedResponse)
def embed_resume_endpoint(request: EmbedResumeRequest):
    """Chunk, embed, and store a resume's text in Qdrant."""
    try:
        chunks_stored = embed_resume(request.resume_id, request.text)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Failed to embed resume %s", request.resume_id)
        raise HTTPException(status_code=500, detail=f"Embedding failed: {e}")

    return EmbedResponse(status="ok", doc_id=request.resume_id, chunks_stored=chunks_stored)


@router.post("/jd", response_model=EmbedResponse)
def embed_jd_endpoint(request: EmbedJdRequest):
    """Chunk, embed, and store a job description's text in Qdrant."""
    try:
        chunks_stored = embed_jd(request.jd_id, request.text)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Failed to embed jd %s", request.jd_id)
        raise HTTPException(status_code=500, detail=f"Embedding failed: {e}")

    return EmbedResponse(status="ok", doc_id=request.jd_id, chunks_stored=chunks_stored)


@router.post("/similarity", response_model=SimilarityResponse)
def similarity_endpoint(request: SimilarityRequest):
    """
    Compute semantic similarity (0-1) between an already-embedded
    resume and job description.
    """
    try:
        score = semantic_similarity(request.resume_id, request.jd_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(
            "Failed to compute similarity for resume=%s jd=%s",
            request.resume_id, request.jd_id,
        )
        raise HTTPException(status_code=500, detail=f"Similarity computation failed: {e}")

    return SimilarityResponse(
        resume_id=request.resume_id,
        jd_id=request.jd_id,
        similarity=score,
    )
