"""
AI-003 — Pydantic request/response schemas for the embedding API.
"""

from pydantic import BaseModel, Field


class EmbedResumeRequest(BaseModel):
    resume_id: str = Field(..., description="Unique ID of the resume (e.g. UUID from careeros-api)")
    text: str = Field(..., min_length=1, description="Plain text content of the resume")


class EmbedJdRequest(BaseModel):
    jd_id: str = Field(..., description="Unique ID of the job description")
    text: str = Field(..., min_length=1, description="Plain text content of the job description")


class EmbedResponse(BaseModel):
    status: str
    doc_id: str
    chunks_stored: int


class SimilarityRequest(BaseModel):
    resume_id: str = Field(..., description="Resume ID previously embedded via /embed/resume")
    jd_id: str = Field(..., description="JD ID previously embedded via /embed/jd")


class SimilarityResponse(BaseModel):
    resume_id: str
    jd_id: str
    similarity: float = Field(..., ge=0.0, le=1.0, description="Cosine similarity score, 0-1")
