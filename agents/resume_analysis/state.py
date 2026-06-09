from typing import TypedDict, Optional


class ResumeAnalysisState(TypedDict):
    """
    LangGraph state object passed between all nodes in the ResumeAnalysisGraph.

    Each node reads from this state and writes back to it.
    The graph moves node-to-node, enriching the state at each step.

    FIX #8: Previous flow comment had wrong node order — it showed
    score_keywords before score_action_verbs, but graph.py wires
    score_action_verbs BEFORE score_keywords. Corrected below.

    Actual execution order (matches graph.py add_edge calls):
        extract_sections
            → extract_keywords
                → score_sections
                    → score_action_verbs      ← comes BEFORE score_keywords
                        → score_keywords
                            → score_quantification
                                → score_formatting
                                    → score_contact_info
                                        → generate_improvements
                                            → calculate_final_score
                                                → generate_summary
    """

    # ── Inputs ────────────────────────────────────────────────────────────────
    resume_text: str           # Raw plain text of the resume
    jd_text: Optional[str]    # Job description text (optional)

    # ── Extracted Data (populated by extraction nodes) ────────────────────────
    sections: dict             # { "experience": "...", "skills": "...", ... }
    extracted_skills: list     # ["Python", "Spring Boot", "React", ...]
    resume_keywords: list      # All meaningful keywords from resume
    jd_keywords: list          # All meaningful keywords from JD

    # ── Individual Scores (populated by scoring nodes) ────────────────────────
    keyword_match_score: int
    section_completeness_score: int
    action_verb_score: int
    quantification_score: int
    formatting_score: int
    contact_info_score: int

    # ── Analysis Results (populated by analysis nodes) ────────────────────────
    keyword_gaps: list         # Keywords in JD but missing from resume
    weak_action_verbs: list    # Weak verbs found: ["worked on", "helped", ...]
    improvements: list         # List of improvement suggestion dicts

    # ── Final Output (populated by final nodes) ────────────────────────────────
    overall_score: int
    summary: str