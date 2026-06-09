from typing import TypedDict, Optional


class ResumeAnalysisState(TypedDict):
    """
    LangGraph state object passed between all nodes in the ResumeAnalysisGraph.

    Each node reads from this state and writes back to it.
    The graph moves node-to-node, enriching the state at each step.

    FIX #8: Previous flow comment had wrong node order â€” it showed
    score_keywords before score_action_verbs, but graph.py wires
    score_action_verbs BEFORE score_keywords. Corrected below.

    Actual execution order (matches graph.py add_edge calls):
        extract_sections
            â†’ extract_keywords
                â†’ score_sections
                    â†’ score_action_verbs      â† comes BEFORE score_keywords
                        â†’ score_keywords
                            â†’ score_quantification
                                â†’ score_formatting
                                    â†’ score_contact_info
                                        â†’ generate_improvements
                                            â†’ calculate_final_score
                                                â†’ generate_summary
    """

    # â”€â”€ Inputs â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    resume_text: str           # Raw plain text of the resume
    jd_text: Optional[str]    # Job description text (optional)

    # â”€â”€ Extracted Data (populated by extraction nodes) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    sections: dict             # { "experience": "...", "skills": "...", ... }
    extracted_skills: list     # ["Python", "Spring Boot", "React", ...]
    resume_keywords: list      # All meaningful keywords from resume
    jd_keywords: list          # All meaningful keywords from JD

    # â”€â”€ Individual Scores (populated by scoring nodes) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    keyword_match_score: int
    section_completeness_score: int
    action_verb_score: int
    quantification_score: int
    formatting_score: int
    contact_info_score: int

    # â”€â”€ Analysis Results (populated by analysis nodes) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    keyword_gaps: list         # Keywords in JD but missing from resume
    weak_action_verbs: list    # Weak verbs found: ["worked on", "helped", ...]
    improvements: list         # List of improvement suggestion dicts

    # â”€â”€ Final Output (populated by final nodes) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    overall_score: int
    summary: str
