from langgraph.graph import StateGraph
from langgraph.graph import END
from agents.resume_analysis.state import ResumeAnalysisState
from agents.resume_analysis.nodes import (
    extract_sections,
    extract_keywords,
    score_sections,
    score_action_verbs,
    score_keywords,
    score_quantification,
    score_formatting,
    score_contact_info,
    generate_improvements,
    calculate_final_score,
    generate_summary,
)


def build_resume_analysis_graph():
    """
    Builds and compiles the ResumeAnalysisGraph.

    Linear graph flow:
        extract_sections -> extract_keywords -> score_sections
        -> score_action_verbs -> score_keywords -> score_quantification
        -> score_formatting -> score_contact_info -> generate_improvements
        -> calculate_final_score -> generate_summary -> END
    """
    graph = StateGraph(ResumeAnalysisState)

    # Add all nodes
    graph.add_node("extract_sections", extract_sections)
    graph.add_node("extract_keywords", extract_keywords)
    graph.add_node("score_sections", score_sections)
    graph.add_node("score_action_verbs", score_action_verbs)
    graph.add_node("score_keywords", score_keywords)
    graph.add_node("score_quantification", score_quantification)
    graph.add_node("score_formatting", score_formatting)
    graph.add_node("score_contact_info", score_contact_info)
    graph.add_node("generate_improvements", generate_improvements)
    graph.add_node("calculate_final_score", calculate_final_score)
    graph.add_node("generate_summary", generate_summary)

    # Define edges (linear execution order)
    graph.set_entry_point("extract_sections")
    graph.add_edge("extract_sections", "extract_keywords")
    graph.add_edge("extract_keywords", "score_sections")
    graph.add_edge("score_sections", "score_action_verbs")
    graph.add_edge("score_action_verbs", "score_keywords")
    graph.add_edge("score_keywords", "score_quantification")
    graph.add_edge("score_quantification", "score_formatting")
    graph.add_edge("score_formatting", "score_contact_info")
    graph.add_edge("score_contact_info", "generate_improvements")
    graph.add_edge("generate_improvements", "calculate_final_score")
    graph.add_edge("calculate_final_score", "generate_summary")
    graph.add_edge("generate_summary", END)

    return graph.compile()


# Single compiled graph instance reused across all requests
resume_analysis_graph = build_resume_analysis_graph()
