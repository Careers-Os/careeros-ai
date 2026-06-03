<div align="center">

<h1>🤖 CareerOS — AI</h1>
<p><strong>LangGraph agents powering CareerOS intelligence</strong></p>

<p>
  <a href="https://github.com/career-os/careeros-ai/stargazers"><img src="https://img.shields.io/github/stars/career-os/careeros-ai?style=flat-square&color=1A56DB" alt="Stars"></a>
  <a href="https://github.com/career-os/careeros-ai/issues"><img src="https://img.shields.io/github/issues/career-os/careeros-ai?style=flat-square&color=1A56DB" alt="Issues"></a>
  <a href="https://github.com/career-os/careeros-ai/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="License"></a>
</p>

</div>

---

## 🧠 AI Agents

| Agent | Description |
|-------|-------------|
| **ResumeAnalysisGraph** | parse → extract → ATS score → generate feedback |
| **RecruiterSimGraph** | parse resume → parse JD → semantic match → predict shortlist |
| **InterviewGraph** | load context → generate questions → evaluate answers → feedback |
| **SkillGapGraph** | extract skills → gap analysis → prioritize → resource mapping |
| **RoadmapGraph** | gap analysis → schedule → day-by-day plan generation |

---

## 🛠️ Tech Stack

- **Python 3.11+**
- **LangGraph** — stateful agent orchestration
- **LangChain** — LLM tooling and chains
- **OpenAI GPT-4o** — primary LLM
- **Groq (Llama 3)** — fast inference for real-time responses
- **Qdrant** — vector database for semantic search
- **FastAPI** — REST API exposing agents to careeros-api
- **sentence-transformers** — embedding generation

---

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Docker (for Qdrant)

### Installation

```bash
git clone https://github.com/career-os/careeros-ai.git
cd careeros-ai

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Start Qdrant
docker run -p 6333:6333 qdrant/qdrant

# Start FastAPI server
uvicorn main:app --reload --port 8090
```

API available at: `http://localhost:8090`  
Docs: `http://localhost:8090/docs`

---

## 📁 Project Structure

```
careeros-ai/
├── agents/
│   ├── resume_analysis/    # ResumeAnalysisGraph
│   ├── recruiter_sim/      # RecruiterSimGraph
│   ├── interview/          # InterviewGraph
│   ├── skill_gap/          # SkillGapGraph
│   └── roadmap/            # RoadmapGraph
├── tools/                  # LangChain tools
├── embeddings/             # Embedding pipeline
├── qdrant/                 # Vector DB client
├── api/                    # FastAPI routes
├── schemas/                # Pydantic models
└── main.py                 # FastAPI entry point
```

---

## 🤝 Contributing

Good first issues:

| Issue | Label | Difficulty |
|-------|-------|-----------|
| ATS keyword scoring tool | `ai` `good-first-issue` | Intermediate |
| Resume section parser | `ai` | Intermediate |
| Qdrant embedding pipeline | `ai` | Advanced |

---

## 📄 License

MIT License — see [LICENSE](LICENSE)
