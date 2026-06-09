from fastapi import APIRouter, HTTPException
from schemas.resume import AnalyzeRequest, AnalyzeResponse, CategoryScores, Improvement
from agents.resume_analysis.graph import resume_analysis_graph

router = APIRouter()


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_resume(request: AnalyzeRequest):
    """
    POST /analyze

    Runs the full ResumeAnalysisGraph on the provided resume text.
    Called by careeros-api (Analysis Service) after text extraction.

    Input:  { resume_text: "...", jd_text: "..." }
    Output: Full ATS analysis with scores, gaps, and improvements
    """
    try:
        # Initial state — all other fields will be populated by graph nodes
        initial_state = {
            "resume_text": request.resume_text,
            "jd_text": request.jd_text,
            "sections": {},
            "extracted_skills": [],
            "resume_keywords": [],
            "jd_keywords": [],
            "keyword_match_score": 0,
            "section_completeness_score": 0,
            "action_verb_score": 0,
            "quantification_score": 0,
            "formatting_score": 0,
            "contact_info_score": 0,
            "keyword_gaps": [],
            "weak_action_verbs": [],
            "improvements": [],
            "overall_score": 0,
            "summary": "",
        }

        # Run the graph — this executes all 11 nodes sequentially
        result = await resume_analysis_graph.ainvoke(initial_state)

        # Build and return the response
        return AnalyzeResponse(
            overall_score=result["overall_score"],
            category_scores=CategoryScores(
                keyword_match=result["keyword_match_score"],
                section_completeness=result["section_completeness_score"],
                action_verbs=result["action_verb_score"],
                quantification=result["quantification_score"],
                formatting=result["formatting_score"],
                contact_info=result["contact_info_score"],
            ),
            keyword_gaps=result["keyword_gaps"],
            extracted_skills=result["extracted_skills"],
            improvements=[
                Improvement(**imp) for imp in result["improvements"]
                if isinstance(imp, dict)
            ],
            summary=result["summary"],
            status="completed",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/health")
async def health():
    """Health check endpoint — used by careeros-api to verify AI service is up."""
    return {"status": "ok", "service": "careeros-ai"}
