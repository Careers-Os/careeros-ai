# Contributing to CareerOS

Thank you for your interest in contributing to CareerOS! 🎉

This project is open-source and community-driven. Whether you're a frontend developer, backend engineer, AI enthusiast, or designer — there's a place for you here.

---

## 📋 Before You Start

1. **Read the docs** → [careeros-docs](https://github.com/career-os/careeros-docs) — understand the system architecture and roadmap
2. **Find an issue** → Filter by `good-first-issue` if you're new
3. **Comment on the issue** → Say "I'd like to work on this" before starting — avoids duplicate work
4. **Wait for assignment** → A maintainer will assign it to you within 24–48 hours

---

## 🛠️ Development Setup

### Frontend (careeros-web)
```bash
git clone https://github.com/career-os/careeros-web.git
cd careeros-web
npm install
cp .env.example .env.local
npm run dev
```

### Backend (careeros-api)
```bash
git clone https://github.com/career-os/careeros-api.git
cd careeros-api
docker-compose up -d        # starts PostgreSQL, Redis, RabbitMQ
./mvnw spring-boot:run
```

### AI Service (careeros-ai)
```bash
git clone https://github.com/career-os/careeros-ai.git
cd careeros-ai
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload --port 8090
```

---

## 📝 How to Submit a Pull Request

1. **Fork** the repository
2. **Create a branch** from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/bug-description
   ```
3. **Make your changes** — keep them focused on one thing
4. **Write clear commit messages**:
   ```
   feat: add resume upload drag-and-drop component
   fix: correct ATS scoring calculation for missing sections
   docs: update API endpoint documentation
   ```
5. **Test your changes** before submitting
6. **Open a Pull Request** against `main` with:
   - What the PR does (2–3 sentences)
   - Link to the issue it closes (`Closes #123`)
   - Screenshots if it's a UI change

---

## ✅ PR Checklist

Before submitting, make sure:

- [ ] Code compiles and runs without errors
- [ ] No console errors in the browser (frontend)
- [ ] Follows existing code style (no custom formatting rules yet)
- [ ] PR description explains what and why
- [ ] Linked to the relevant issue

---

## 🏷️ Issue Labels

| Label | Meaning |
|-------|---------|
| `good-first-issue` | Perfect for new contributors |
| `beginner` | Requires basic knowledge of the stack |
| `intermediate` | Requires some experience |
| `advanced` | Complex task, experience required |
| `frontend` | Next.js / React / TypeScript |
| `backend` | Spring Boot / Java |
| `ai` | LangGraph / Python / LLM |
| `documentation` | Docs, README, guides |
| `bug` | Something is broken |
| `enhancement` | New feature or improvement |

---

## 💬 Communication

- **GitHub Discussions** — architecture decisions, feature proposals, questions
- **Issue comments** — specific questions about a task
- Keep discussions respectful and constructive — see [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)

---

## 🎖️ Recognition

All contributors are credited in:
- The repository's contributor graph
- The project README (once you've had a PR merged)
- Release notes when your feature ships

---

## ❓ Questions?

Not sure where to start? Open a [GitHub Discussion](https://github.com/career-os/careeros-web/discussions) and ask. We're happy to help you find the right issue for your skill level.
