import os
import json
import re
from langchain_groq import ChatGroq
from langchain.schema import HumanMessage, SystemMessage

# ── LLM Setup ─────────────────────────────────────────────────────────────────
# FIX #10: Do NOT init LLM at module level — if GROQ_API_KEY is missing,
# the import itself crashes with a cryptic error instead of a clear config error.
# LLM is now created via get_llm() and validated at startup in main.py.
_llm_instance = None


def get_llm() -> ChatGroq:
    """
    Lazily initializes and returns the shared ChatGroq instance.
    Called at first use, not at import time.
    """
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = ChatGroq(
            groq_api_key=os.environ["GROQ_API_KEY"],   # Raises KeyError clearly
            # FIX #13: Updated to current recommended Groq model name
            model_name=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            temperature=0.1,
            max_tokens=2000,
        )
    return _llm_instance


def _call_llm(system_prompt: str, user_prompt: str) -> str:
    """
    Helper to call Groq LLM with system + user message.
    Returns the raw string response.
    """
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]
    response = get_llm().invoke(messages)
    return response.content


def _parse_json_response(response: str) -> dict:
    """
    Safely parse JSON from LLM response.
    LLMs sometimes wrap JSON in markdown code blocks — this handles that.
    Logs on failure so prompt drift is visible in prod.
    """
    cleaned = re.sub(r"```json\n?|\n?```", "", response).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        # FIX #3 (partial) / #14 helper: log instead of silently returning {}
        print(f"[WARN] JSON parse failed: {e}\nRaw response (first 300 chars): {response[:300]}")
        return {}


# ── NODE 1: Extract Sections ──────────────────────────────────────────────────
def extract_sections(state: dict) -> dict:
    """
    NODE 1 — Extract Resume Sections

    Identifies and extracts standard resume sections from the raw text.
    Returns a dict with section names as keys and content as values.
    """
    system_prompt = """You are a resume parser. Extract sections from the resume text.
Return ONLY a JSON object with these keys (use null if section is missing):
{
  "contact": "...",
  "summary": "...",
  "skills": "...",
  "experience": "...",
  "education": "...",
  "projects": "...",
  "certifications": "...",
  "achievements": "..."
}
Return ONLY the JSON. No explanation."""

    response = _call_llm(system_prompt, f"Resume text:\n{state['resume_text']}")
    sections = _parse_json_response(response)

    return {**state, "sections": sections}


# ── NODE 2: Extract Keywords ──────────────────────────────────────────────────
def extract_keywords(state: dict) -> dict:
    """
    NODE 2 — Extract Keywords

    Extracts technical and domain-specific keywords from both the resume
    and the job description (if provided).
    """
    system_prompt = """You are a technical recruiter. Extract keywords from the text.
Return ONLY a JSON object:
{
  "keywords": ["Python", "Spring Boot", "React", ...],
  "skills": ["Python", "Java", ...]
}
Focus on: programming languages, frameworks, tools, technologies, methodologies.
Return ONLY the JSON. No explanation."""

    resume_response = _call_llm(system_prompt, f"Text:\n{state['resume_text']}")
    resume_data = _parse_json_response(resume_response)

    jd_keywords = []
    if state.get("jd_text"):
        jd_response = _call_llm(system_prompt, f"Text:\n{state['jd_text']}")
        jd_data = _parse_json_response(jd_response)
        jd_keywords = jd_data.get("keywords", [])

    return {
        **state,
        "resume_keywords": resume_data.get("keywords", []),
        "extracted_skills": resume_data.get("skills", []),
        "jd_keywords": jd_keywords,
    }


# ── NODE 3: Score Section Completeness ───────────────────────────────────────
def score_sections(state: dict) -> dict:
    """
    NODE 3 — Score Section Completeness (Weight: 20%)

    Checks which key sections are present and scores accordingly.

    Scoring:
    - contact:        10 pts
    - summary:        10 pts
    - skills:         20 pts
    - experience:     25 pts  (reduced from 30 to fit achievements)
    - education:      15 pts
    - projects:       10 pts
    - certifications:  5 pts
    - achievements:    5 pts  FIX #4: was extracted but never scored (always 0)

    Total = 100 pts max
    """
    sections = state.get("sections", {})

    # FIX #4: Added "achievements" with 5 pts weight.
    # Reduced "experience" from 30 → 25 to keep total = 100.
    section_weights = {
        "contact": 10,
        "summary": 10,
        "skills": 20,
        "experience": 25,
        "education": 15,
        "projects": 10,
        "certifications": 5,
        "achievements": 5,
    }

    score = 0
    for section, weight in section_weights.items():
        if sections.get(section) and len(str(sections[section]).strip()) > 10:
            score += weight

    return {**state, "section_completeness_score": min(score, 100)}


# ── NODE 4: Score Action Verbs ────────────────────────────────────────────────
def score_action_verbs(state: dict) -> dict:
    """
    NODE 4 — Score Action Verbs (Weight: 15%)

    Detects weak action verbs (worked on, helped, assisted) vs strong ones
    (engineered, architected, optimized, reduced, increased).

    FIX #3: If experience + projects sections are both empty, return score=0
    (not 50) so the 'missing sections' improvement is triggered instead of
    a misleading 'weak action verbs' suggestion.
    """
    experience_text = state.get("sections", {}).get("experience", "") or ""
    projects_text = state.get("sections", {}).get("projects", "") or ""
    combined = f"{experience_text} {projects_text}"

    # FIX #3: Return 0 (not 50) for empty sections.
    # score_sections already flags missing sections — don't double-report as verb issue.
    if not combined.strip():
        return {**state, "action_verb_score": 0, "weak_action_verbs": []}

    system_prompt = """Analyze action verbs in this resume text.
Return ONLY a JSON object:
{
  "weak_verbs_found": ["worked on", "helped with", ...],
  "strong_verb_count": 8,
  "weak_verb_count": 3,
  "score": 75
}
Weak verbs: worked, helped, assisted, was responsible for, participated, involved
Strong verbs: engineered, architected, optimized, reduced, increased, built, designed, led, delivered
Score 0-100 based on ratio of strong to weak verbs.
Return ONLY the JSON."""

    response = _call_llm(system_prompt, f"Resume text:\n{combined}")
    data = _parse_json_response(response)

    return {
        **state,
        "action_verb_score": int(data.get("score", 60)),
        "weak_action_verbs": data.get("weak_verbs_found", []),
    }


# ── NODE 5: Score Keyword Match ───────────────────────────────────────────────
def score_keywords(state: dict) -> dict:
    """
    NODE 5 — Score Keyword Match (Weight: 35%)

    Compares resume keywords against JD keywords.

    FIX #6: No-JD branch previously capped at 85 (hardcoded silent ceiling).
    Now caps at 100 like every other scoring node.
    The 85 cap silently cost up to 5.25 points on the final score with
    no explanation to the user.
    """
    resume_keywords = [k.lower() for k in state.get("resume_keywords", [])]
    jd_keywords = [k.lower() for k in state.get("jd_keywords", [])]

    if not jd_keywords:
        # FIX #6: was min(..., 85) — now caps at 100
        score = min(len(resume_keywords) * 5, 100)
        return {**state, "keyword_match_score": score, "keyword_gaps": []}

    if not resume_keywords:
        return {**state, "keyword_match_score": 0, "keyword_gaps": jd_keywords}

    matched = [kw for kw in jd_keywords if kw in resume_keywords]
    gaps = [kw for kw in jd_keywords if kw not in resume_keywords]
    match_ratio = len(matched) / len(jd_keywords) if jd_keywords else 0
    score = int(match_ratio * 100)

    return {
        **state,
        "keyword_match_score": score,
        "keyword_gaps": gaps[:10],
    }


# ── NODE 6: Score Quantification ─────────────────────────────────────────────
def score_quantification(state: dict) -> dict:
    """
    NODE 6 — Score Quantification (Weight: 15%)

    Detects measurable impact: numbers, percentages, scale.

    FIX #2: Previous regex `\d+\s*(users|...)` missed comma-formatted numbers
    like "50,000+ users" or "1,000+ stars" because the comma and + between
    digits and the unit broke the match.
    Updated to `[\d,]+\+?\s*(users|...)` to handle both formats.
    """
    experience_text = state.get("sections", {}).get("experience", "") or ""
    projects_text = state.get("sections", {}).get("projects", "") or ""
    combined = f"{experience_text} {projects_text}"

    patterns = [
        r'\d+%',                                            # percentages: 40%
        r'\d+x',                                            # multipliers: 3x
        r'\$[\d,]+',                                        # dollar amounts: $50K
        # FIX #2: was r'\d+\s*(users|requests|ms|s)'
        # Now handles "50,000+ users", "1,000+ requests"
        r'[\d,]+\+?\s*(users|requests|ms|seconds|stars)',
        r'(increased|reduced|improved|decreased|grew|scaled)\s+by\s+\d+',
    ]

    matches = []
    for pattern in patterns:
        matches.extend(re.findall(pattern, combined, re.IGNORECASE))

    count = len(matches)
    if count == 0:
        score = 20
    elif count <= 2:
        score = 40
    elif count <= 4:
        score = 60
    elif count <= 6:
        score = 80
    else:
        score = 95

    return {**state, "quantification_score": score}


# ── NODE 7: Score Formatting ──────────────────────────────────────────────────
def score_formatting(state: dict) -> dict:
    """
    NODE 7 — Score Formatting (Weight: 10%)

    Checks for ATS-unfriendly formatting in raw resume text.

    FIX #5: The special character loop had a `break` that exited after the
    first offending character. A resume with multiple problem characters
    (e.g. both ■ and ▪ heavily used) only lost 10 pts instead of 20.
    Removed the `break` so each offending character is penalized independently.
    """
    resume_text = state.get("resume_text", "")
    score = 100
    issues = []

    if resume_text.count("|") > 5:
        score -= 20
        issues.append("Possible table formatting detected")

    # Handle both Unix (\n) and Windows (\r\n) line endings
    lines = resume_text.splitlines()
    long_lines = [l for l in lines if len(l) > 150]
    if len(long_lines) > 3:
        score -= 15
        issues.append("Possible multi-column layout detected")

    # FIX #5: Removed `break` — penalize EACH offending special character,
    # not just the first one found.
    special_chars = ["■", "▪", "◆", "★", "✓", "→"]
    for char in special_chars:
        if resume_text.count(char) > 3:
            score -= 10
            issues.append(f"Special character '{char}' may not parse correctly")
            # NO break here — continue checking remaining chars

    word_count = len(resume_text.split())
    if word_count < 200:
        score -= 20
        issues.append("Resume seems too short")
    elif word_count > 1200:
        score -= 10
        issues.append("Resume may be too long for ATS")

    return {**state, "formatting_score": max(score, 0)}


# ── NODE 8: Score Contact Info ────────────────────────────────────────────────
def score_contact_info(state: dict) -> dict:
    """
    NODE 8 — Score Contact Info (Weight: 5%)

    Checks for presence of essential contact information.
    """
    contact_text = str(state.get("sections", {}).get("contact", "") or "")
    resume_text = state.get("resume_text", "")
    combined = f"{contact_text} {resume_text[:500]}"

    score = 0

    if re.search(r'[\w.-]+@[\w.-]+\.\w+', combined):
        score += 30

    if re.search(r'(\+91|0)?[\s-]?[6-9]\d{9}|\+?\d[\d\s\-().]{7,}', combined):
        score += 25

    if re.search(r'linkedin\.com/in/', combined, re.IGNORECASE):
        score += 25

    if re.search(r'github\.com/', combined, re.IGNORECASE):
        score += 20

    return {**state, "contact_info_score": min(score, 100)}


# ── NODE 9: Generate Improvements ────────────────────────────────────────────
def generate_improvements(state: dict) -> dict:
    """
    NODE 9 — Generate Improvement Suggestions

    FIX #14: Was duplicating _parse_json_response logic inline with its own
    re.sub + json.loads block. Now uses the shared helper so any future
    improvements to the helper (logging, fence handling) apply here too.
    """
    low_scoring_areas = []
    if state.get("keyword_match_score", 100) < 70:
        low_scoring_areas.append(f"Keyword match is low. Missing keywords: {state.get('keyword_gaps', [])[:5]}")
    if state.get("section_completeness_score", 100) < 70:
        low_scoring_areas.append("Some important resume sections are missing")
    if state.get("action_verb_score", 100) < 70:
        low_scoring_areas.append(f"Weak action verbs found: {state.get('weak_action_verbs', [])[:3]}")
    if state.get("quantification_score", 100) < 70:
        low_scoring_areas.append("Resume lacks quantified achievements (numbers, percentages, scale)")
    if state.get("formatting_score", 100) < 70:
        low_scoring_areas.append("Formatting may cause ATS parsing issues")

    if not low_scoring_areas:
        return {**state, "improvements": []}

    system_prompt = """You are a professional resume coach. Generate specific, actionable improvements.
Return ONLY a JSON array:
[
  {"priority": "high", "section": "Experience", "message": "Replace 'worked on' with strong verbs like 'engineered' or 'built'"},
  {"priority": "medium", "section": "Skills", "message": "Add missing keywords: Docker, Kubernetes"},
  ...
]
Priority: high (score < 50), medium (score 50-70), low (score > 70).
Maximum 6 improvements. Be specific. Return ONLY the JSON array."""

    context = "\n".join(low_scoring_areas)
    response = _call_llm(system_prompt, f"Issues found:\n{context}")

    # FIX #14: Use the shared helper instead of duplicating re.sub + json.loads inline
    parsed = _parse_json_response(response)
    # _parse_json_response returns dict; for arrays the JSON root is a list
    # Handle both: if it returned a dict (parse error fallback), default to []
    if isinstance(parsed, list):
        improvements = parsed
    else:
        # Re-attempt: _parse_json_response only returns dict, so try raw parse for arrays
        cleaned = re.sub(r"```json\n?|\n?```", "", response).strip()
        try:
            improvements = json.loads(cleaned)
            if not isinstance(improvements, list):
                improvements = []
        except json.JSONDecodeError:
            improvements = []

    return {**state, "improvements": improvements}


# ── NODE 10: Calculate Final Score ───────────────────────────────────────────
def calculate_final_score(state: dict) -> dict:
    """
    NODE 10 — Calculate Weighted Final Score

    Weights:
    - Keyword Match:        35%
    - Section Completeness: 20%
    - Action Verbs:         15%
    - Quantification:       15%
    - Formatting:           10%
    - Contact Info:          5%
    """
    weights = {
        "keyword_match_score": 0.35,
        "section_completeness_score": 0.20,
        "action_verb_score": 0.15,
        "quantification_score": 0.15,
        "formatting_score": 0.10,
        "contact_info_score": 0.05,
    }

    overall = sum(
        state.get(key, 0) * weight
        for key, weight in weights.items()
    )

    return {**state, "overall_score": int(round(overall))}


# ── NODE 11: Generate Summary ─────────────────────────────────────────────────
def generate_summary(state: dict) -> dict:
    """
    NODE 11 — Generate Human-Readable Summary

    Final node — generates a 2-3 sentence summary of the overall assessment.
    """
    system_prompt = """You are a professional resume coach. Write a 2-3 sentence summary of this resume analysis.
Be honest but encouraging. Mention the overall score and 1-2 key areas to improve.
Return ONLY the summary text. No JSON."""

    context = f"""
Overall score: {state.get('overall_score')}/100
Keyword match: {state.get('keyword_match_score')}/100
Section completeness: {state.get('section_completeness_score')}/100
Action verbs: {state.get('action_verb_score')}/100
Quantification: {state.get('quantification_score')}/100
Key gaps: {state.get('keyword_gaps', [])[:3]}
"""
    summary = _call_llm(system_prompt, context)

    return {**state, "summary": summary.strip()}