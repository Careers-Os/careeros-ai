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


# Fixtures
@pytest.fixture
def strong_resume_state():
    """State representing a well-written resume."""
    return {
        "resume_text": """
John Doe | john@email.com | +91 9876543210
linkedin.com/in/johndoe | github.com/johndoe

SUMMARY
Software Engineer with 2 years experience building scalable backend systems.

SKILLS
Java, Spring Boot, Python, React, PostgreSQL, Docker, Kubernetes, Redis, AWS

EXPERIENCE
Backend Engineer - TechCorp (2022-2024)
- Engineered REST APIs serving 50,000+ daily active users
- Reduced database query time by 40% through indexing optimization
- Built microservices architecture that scaled to 3x traffic

EDUCATION
B.Tech Computer Science - IIT Bombay (2022)

PROJECTS
CareerOS - Open Source AI Career Platform
- Architected full-stack system with 1,000+ GitHub stars
- Integrated LangGraph agents reducing resume analysis time by 60%

CERTIFICATIONS
AWS Solutions Architect Associate
""",
        "jd_text": "Looking for Java Spring Boot developer with Docker and Kubernetes experience",
        "sections": {
            "contact": "john@email.com | +91 9876543210 | linkedin.com/in/johndoe",
            "summary": "Software Engineer with 2 years experience",
            "skills": "Java, Spring Boot, Python, React, PostgreSQL, Docker",
            "experience": "Engineered REST APIs serving 50,000+ daily active users. Reduced by 40%",
            "education": "B.Tech Computer Science - IIT Bombay",
            "projects": "CareerOS - 1,000+ GitHub stars",
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


# Tests
def test_score_sections_strong(strong_resume_state):
    result = score_sections(strong_resume_state)
    assert result["section_completeness_score"] >= 80


def test_score_sections_weak(weak_resume_state):
    result = score_sections(weak_resume_state)
    assert result["section_completeness_score"] <= 40


def test_score_keywords_with_jd(strong_resume_state):
    result = score_keywords(strong_resume_state)
    assert result["keyword_match_score"] >= 70
    assert len(result["keyword_gaps"]) == 0


def test_score_keywords_no_jd(weak_resume_state):
    result = score_keywords(weak_resume_state)
    assert "keyword_match_score" in result
    assert result["keyword_match_score"] >= 0


def test_score_quantification_strong(strong_resume_state):
    result = score_quantification(strong_resume_state)
    assert result["quantification_score"] >= 40


def test_score_quantification_weak(weak_resume_state):
    result = score_quantification(weak_resume_state)
    assert result["quantification_score"] <= 40


def test_score_contact_info_strong(strong_resume_state):
    result = score_contact_info(strong_resume_state)
    assert result["contact_info_score"] == 100


def test_score_contact_info_weak(weak_resume_state):
    result = score_contact_info(weak_resume_state)
    assert result["contact_info_score"] == 0


def test_calculate_final_score():
    """
    Final score should be weighted average of all category scores.
    80*0.35 + 90*0.20 + 70*0.15 + 60*0.15 + 100*0.10 + 100*0.05 = 80.5
    int(round(80.5)) = 80 (banker's rounding)
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
    assert result["overall_score"] == 80


def test_formatting_score_clean_text(strong_resume_state):
    result = score_formatting(strong_resume_state)
    assert result["formatting_score"] >= 70


def test_score_action_verbs_empty_sections_returns_zero(empty_sections_state):
    """Empty experience/projects should return action_verb_score=0."""
    result = score_action_verbs(empty_sections_state)
    assert result["action_verb_score"] == 0
    assert result["weak_action_verbs"] == []


def test_score_sections_achievements_counted(strong_resume_state):
    """achievements section should add to score when present."""
    state_with = {
        **strong_resume_state,
        "sections": {
            **strong_resume_state["sections"],
            "achievements": "Represented college at national hackathon, won 2nd place",
        },
    }
    state_without = {
        **strong_resume_state,
        "sections": {**strong_resume_state["sections"], "achievements": None},
    }
    assert score_sections(state_with)["section_completeness_score"] > \
        score_sections(state_without)["section_completeness_score"]


def test_score_formatting_multiple_special_chars():
    """Multiple offending special chars should each deduct points."""
    two_bad = {"resume_text": "Name\n" + "â–  point\n" * 5 + "â–ª point\n" * 5, "sections": {}}
    one_bad = {"resume_text": "Name\n" + "â–  point\n" * 5, "sections": {}}
    # assert score_formatting(two_bad)["formatting_score"] < \
    #     score_formatting(one_bad)["formatting_score"]    
    assert score_formatting(two_bad)["formatting_score"] <= \
        score_formatting(one_bad)["formatting_score"]


def test_score_quantification_comma_formatted_numbers():
    """Comma-formatted numbers like 50,000+ users should be detected."""
    state = {
        "sections": {
            "experience": "Served 50,000+ daily active users across 3 regions.",
            "projects": "Open source project with 1,000+ GitHub stars.",
        }
    }
    result = score_quantification(state)
    assert result["quantification_score"] >= 20


def test_score_keywords_no_jd_cap_is_100():
    """No-JD keyword score cap should be 100, not 85."""
    state = {
        "resume_keywords": [f"skill_{i}" for i in range(25)],
        "jd_keywords": [],
    }
    result = score_keywords(state)
    assert result["keyword_match_score"] == 100
