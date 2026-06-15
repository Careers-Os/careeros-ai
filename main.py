import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from api.routes import router
from api.embedding_routes import router as embedding_router
from embeddings.qdrant_client import ensure_collection

# Load environment variables from .env file
load_dotenv()


# ── FIX #10: Validate required env vars at startup, not at import time ────────
# Previously, ChatGroq was initialized at module level in nodes.py.
# If GROQ_API_KEY was missing, the error surfaced as a confusing ImportError.
# Now we validate here with a clear message before the app starts.
def _validate_env() -> None:
    required = ["GROQ_API_KEY"]
    missing = [var for var in required if not os.getenv(var)]
    if missing:
        raise EnvironmentError(
            f"Missing required environment variable(s): {', '.join(missing)}\n"
            f"Set them in your .env file or shell environment before starting."
        )


_validate_env()


# ── FIX #9: CORS origins driven by env var, not hardcoded to localhost ────────
# Previously: allow_origins=["http://localhost:8080", "http://localhost:3000"]
# This broke in any deployed environment with no way to override without
# changing code. Now reads from ALLOWED_ORIGINS env var (comma-separated).
# Default keeps localhost for local dev backward-compat.
_raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8080")
allowed_origins = [origin.strip() for origin in _raw_origins.split(",") if origin.strip()]

app = FastAPI(
    title="CareerOS AI Service",
    description="LangGraph-powered AI agents for CareerOS",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all routes
app.include_router(router)
app.include_router(embedding_router)


# ── AI-003: Ensure Qdrant collection exists on startup ─────────────────────────
@app.on_event("startup")
def on_startup():
    ensure_collection()