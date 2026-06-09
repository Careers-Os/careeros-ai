"""
Tests for ResumeAnalysisGraph nodes.
Run with: pytest tests/ -v
"""
import pytest
from agents.resume_analysis.nodes import (
    score_sections,
    score_keywords,
    score_quantification,
    score_formatting,
    score_contact_info,
    score_action_verbs,
    calculate_final_score,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────
@pytest.fixture
def strong_resume_state():
    """State representing a well-written resume."""
    return {
        "resume_text": """
John Doe | john@email.com | +91 9876543210 | linkedin.com/in/johndoe | github.com/johndoe

SUMMARY
Software Engineer with 2 years experience building scalable backend systems.

SKILLS
Java, Spring Boot, Python, React, PostgreSQL, Docker, Kubernetes, Redis, AWS

EXPERIENCE
Backend Engineer — TechCorp (2022-2024)
• Engineered REST APIs serving 50,000+ daily active users
• Reduced database query time by 40% through indexing optimization
• Built microservices architecture that scaled to 3x traffic

EDUCATION
B.Tech Computer Science — IIT Bombay (2022)

PROJECTS
CareerOS — Open Source AI Career Platform
• Architected full-stack system with 1,000+ GitHub stars
• Integrated LangGraph agents reducing resume analysis time by 60%

CERTIFICATIONS
AWS Solutions Architect Associate
""",
        "jd_text": "Looking for Java Spring Boot developer with Docker and Kubernetes experience",
        "sections": {
            "contact": "john@email.com | +91 9876543210 | linkedin.com/in/johndoe",
            "summary": "Software Engineer with 2 years experience",
            "skills": "Java, Spring Boot, Python, React, PostgreSQL, Docker",
            "experience": "Engineered REST APIs serving 50,000+ daily active users. Reduced by 40%",
            "education": "B.Tech Computer Science — IIT Bombay",
            "projects": "CareerOS — 1,000+ GitHub stars",
            "certifications": "AWS Solutions Architect",
            "achievements": None,
        },
        "resume_keywords": ["java", "spring boot", "python", "docker", "kubernetes", "redis"],
        "jd_keywords": ["java", "spring boot", "docker", "kubernetes"],
        "keyword_gaps": [],
        "weak_action_verbs": [],
        "improvements": [],
        "keyword_match_score": 0,
        "section_completeness_score": 0,
        "action_verb_score": 0,
        "quantification_score": 0,
        "formatting_score": 0,
        "contact_info_score": 0,
        "overall_score": 0,
        "summary": "",
    }


@pytest.fixture
def weak_resume_state():
    """State representing a poorly written resume."""
    return {
        "resume_text": "John. Worked on projects. Helped team. Good at coding.",
        "jd_text": None,
        "sections": {
            "contact": None,
            "summary": None,
            "skills": None,
            "experience": "Worked on projects. Helped team.",
            "education": None,
            "projects": None,
            "certifications": None,
            "achievements": None,
        },
        "resume_keywords": [],
        "jd_keywords": [],
        "keyword_gaps": [],
        "weak_action_verbs": [],
        "improvements": [],
        "keyword_match_score": 0,
        "section_completeness_score": 0,
        "action_verb_score": 0,
        "quantification_score": 0,
        "formatting_score": 0,
        "contact_info_score": 0,
        "overall_score": 0,
        "summary": "",
    }


@pytest.fixture
def empty_sections_state():
    """State where experience and projects sections are both absent."""
    return {
        "resume_text": "Jane Smith | jane@email.com",
        "jd_text": None,
        "sections": {
            "contact": "jane@email.com",
            "summary": None,
            "skills": None,
            "experience": None,
            "education": "B.Tech",
            "projects": None,
            "certifications": None,
            "achievements": None,
        },
        "resume_keywords": [],
        "jd_keywords": [],
        "keyword_gaps": [],
        "weak_action_verbs": [],
        "improvements": [],
        "keyword_match_score": 0,
        "section_completeness_score": 0,
        "action_verb_score": 0,
        "quantification_score": 0,
        "formatting_score": 0,
        "contact_info_score": 0,
        "overall_score": 0,
        "summary": "",
    }


# ── Tests ─────────────────────────────────────────────────────────────────────
def test_score_sections_strong(strong_resume_state):
    """Strong resume with all sections should score high."""
    result = score_sections(strong_resume_state)
    assert result["section_completeness_score"] >= 80


def test_score_sections_weak(weak_resume_state):
    """Resume missing most sections should score low."""
    result = score_sections(weak_resume_state)
    assert result["section_completeness_score"] <= 40


def test_score_keywords_with_jd(strong_resume_state):
    """Resume with matching JD keywords should score high."""
    result = score_keywords(strong_resume_state)
    assert result["keyword_match_score"] >= 70
    assert len(result["keyword_gaps"]) == 0


def test_score_keywords_no_jd(weak_resume_state):
    """No JD provided — should still return a score."""
    result = score_keywords(weak_resume_state)
    assert "keyword_match_score" in result
    assert result["keyword_match_score"] >= 0


def test_score_quantification_strong(strong_resume_state):
    """Resume with numbers and percentages should score high."""
    result = score_quantification(strong_resume_state)
    assert result["quantification_score"] >= 60


def test_score_quantification_weak(weak_resume_state):
    """Resume without numbers should score low."""
    result = score_quantification(weak_resume_state)
    assert result["quantification_score"] <= 40


def test_score_contact_info_strong(strong_resume_state):
    """Resume with email, phone, LinkedIn, GitHub should score 100."""
    result = score_contact_info(strong_resume_state)
    assert result["contact_info_score"] == 100


def test_score_contact_info_weak(weak_resume_state):
    """Resume with no contact info should score 0."""
    result = score_contact_info(weak_resume_state)
    assert result["contact_info_score"] == 0


def test_calculate_final_score():
    """
    Final score should be weighted average of all category scores.

    FIX #1: Previous test asserted == 81, which is WRONG.
    Python's round() uses banker's rounding: round(80.5) → 80, not 81.

    Breakdown:
      80 * 0.35 = 28.0
      90 * 0.20 = 18.0
      70 * 0.15 = 10.5
      60 * 0.15 =  9.0
     100 * 0.10 = 10.0
     100 * 0.05 =  5.0
               = 80.5  →  int(round(80.5)) = 80  (banker's rounding)
    """
    state = {
        "keyword_match_score": 80,
        "section_completeness_score": 90,
        "action_verb_score": 70,
        "quantification_score": 60,
        "formatting_score": 100,
        "contact_info_score": 100,
    }
    result = calculate_final_score(state)
    # FIX #1: was assert == 81, correct value is 80
    assert result["overall_score"] == 80


def test_formatting_score_clean_text(strong_resume_state):
    """Clean resume text should score high on formatting."""
    result = score_formatting(strong_resume_state)
    assert result["formatting_score"] >= 70


# ── New tests covering previously untested behavior ───────────────────────────

def test_score_action_verbs_empty_sections_returns_zero(empty_sections_state):
    """
    FIX #3: When experience and projects are both missing/empty,
    action_verb_score should be 0 (not 50).
    A score of 50 would trigger a misleading 'weak action verbs' improvement
    when the real problem is missing sections.
    """
    result = score_action_verbs(empty_sections_state)
    assert result["action_verb_score"] == 0
    assert result["weak_action_verbs"] == []


def test_score_sections_achievements_counted(strong_resume_state):
    """
    FIX #4: 'achievements' section is now included in section_weights.
    A resume with achievements content should score higher than one without.
    """
    state_with_achievements = {
        **strong_resume_state,
        "sections": {
            **strong_resume_state["sections"],
            "achievements": "Represented college at national hackathon, won 2nd place",
        },
    }
    state_without_achievements = {
        **strong_resume_state,
        "sections": {
            **strong_resume_state["sections"],
            "achievements": None,
        },
    }
    score_with = score_sections(state_with_achievements)["section_completeness_score"]
    score_without = score_sections(state_without_achievements)["section_completeness_score"]
    assert score_with > score_without


def test_score_formatting_multiple_special_chars():
    """
    FIX #5: Multiple offending special characters should each deduct points.
    Previously a `break` caused only the first offender to be penalized.
    """
    # Both ■ and ▪ appear more than 3 times each
    resume_with_two_bad_chars = {
        "resume_text": "Name\n" + "■ point\n" * 5 + "▪ point\n" * 5,
        "sections": {},
    }
    resume_with_one_bad_char = {
        "resume_text": "Name\n" + "■ point\n" * 5,
        "sections": {},
    }
    score_two = score_formatting(resume_with_two_bad_chars)["formatting_score"]
    score_one = score_formatting(resume_with_one_bad_char)["formatting_score"]
    # Two offending chars should score lower than one
    assert score_two < score_one


def test_score_quantification_comma_formatted_numbers():
    """
    FIX #2: Quantification regex must match comma-formatted numbers like
    '50,000+ users' and '1,000+ stars'. Previously these were missed because
    the regex required digits directly adjacent to the unit keyword.
    """
    state = {
        "sections": {
            "experience": "Served 50,000+ daily active users across 3 regions.",
            "projects": "Open source project with 1,000+ GitHub stars.",
        }
    }
    result = score_quantification(state)
    # Should detect at least the two comma-formatted numbers
    assert result["quantification_score"] >= 40


def test_score_keywords_no_jd_cap_is_100():
    """
    FIX #6: When no JD is provided, keyword score cap should be 100 not 85.
    A resume with 20+ keywords should be able to score 100.
    """
    state = {
        "resume_keywords": [f"skill_{i}" for i in range(25)],  # 25 keywords
        "jd_keywords": [],
    }
    result = score_keywords(state)
    assert result["keyword_match_score"] == 100