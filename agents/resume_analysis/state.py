from typing import TypedDict, Optional


class ResumeAnalysisState(TypedDict):
    """
    LangGraph state passed between all nodes in the ResumeAnalysisGraph.

    Execution order (matches graph.py add_edge calls):
        extract_sections -> extract_keywords -> score_sections
        -> score_action_verbs -> score_keywords -> score_quantification
        -> score_formatting -> score_contact_info -> generate_improvements
        -> calculate_final_score -> generate_summary
    """

    # Inputs
    resume_text: str
    jd_text: Optional[str]

    # Extracted data (populated by extraction nodes)
    sections: dict
    extracted_skills: list
    resume_keywords: list
    jd_keywords: list

    # Individual scores (populated by scoring nodes)
    keyword_match_score: int
    section_completeness_score: int
    action_verb_score: int
    quantification_score: int
    formatting_score: int
    contact_info_score: int

    # Analysis results
    keyword_gaps: list
    weak_action_verbs: list
    improvements: list

    # Final output
    overall_score: int
    summary: str
