from pydantic import BaseModel, Field
from typing import Optional


class AnalyzeRequest(BaseModel):
    """
    Input schema for the resume analysis endpoint.
    resume_text: plain text extracted from the uploaded PDF/DOCX
    jd_text: optional job description to compare against

    FIX #11: Added max_length=15000 to resume_text.
    Previously there was only a min_length=50 with no upper bound.
    A malicious or accidental multi-MB string would pass validation
    and be forwarded to Groq across 11 LLM calls.
    15,000 chars comfortably fits a 10-page resume (~5,000 words).
    """
    resume_text: str = Field(
        ...,
        min_length=50,
        max_length=15000,
        description="Plain text of the resume"
    )
    jd_text: Optional[str] = Field(
        None,
        max_length=10000,
        description="Job description text for keyword matching"
    )


class CategoryScores(BaseModel):
    """
    Breakdown of ATS score by category.
    Each score is 0-100. Final score is a weighted average.
    """
    keyword_match: int = Field(..., ge=0, le=100, description="How well resume keywords match the JD (35% weight)")
    section_completeness: int = Field(..., ge=0, le=100, description="Presence of all key resume sections (20% weight)")
    action_verbs: int = Field(..., ge=0, le=100, description="Quality of action verbs used (15% weight)")
    quantification: int = Field(..., ge=0, le=100, description="Presence of measurable impact (15% weight)")
    formatting: int = Field(..., ge=0, le=100, description="ATS-friendly formatting (10% weight)")
    contact_info: int = Field(..., ge=0, le=100, description="Completeness of contact information (5% weight)")


class Improvement(BaseModel):
    """A single improvement suggestion with priority level."""
    priority: str = Field(..., description="high | medium | low")
    section: str = Field(..., description="Which section this applies to")
    message: str = Field(..., description="Specific actionable improvement")


class AnalyzeResponse(BaseModel):
    """
    Full ATS analysis result returned to careeros-api.
    overall_score: weighted average of all category scores (0-100)
    """
    overall_score: int = Field(..., ge=0, le=100)
    category_scores: CategoryScores
    keyword_gaps: list[str] = Field(default_factory=list, description="Keywords missing from resume but present in JD")
    extracted_skills: list[str] = Field(default_factory=list, description="Skills detected in the resume")
    improvements: list[Improvement] = Field(default_factory=list, description="Prioritized improvement suggestions")
    summary: str = Field(..., description="2-3 sentence overall assessment")
    status: str = Field(default="completed")