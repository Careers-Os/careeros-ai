

import os

import pytest

from embeddings.pipeline import embed_resume, embed_jd, semantic_similarity
from embeddings.embedding_model import chunk_text

# These tests require downloading the sentence-transformers model from
# HuggingFace and a running Qdrant instance — both unavailable in CI.
# Run locally with: pytest tests/test_embeddings.py -v
pytestmark = pytest.mark.skipif(
    os.getenv("CI") == "true",
    reason="Requires HuggingFace model download and live Qdrant instance — run locally only"
)


SAMPLE_RESUME = """
John Doe — Backend Engineer

SKILLS
Java, Spring Boot, PostgreSQL, Docker, Kubernetes, REST APIs

EXPERIENCE
Backend Engineer at TechCorp (2022-2024)
Built and maintained REST APIs serving 50,000 daily active users.
Optimized database queries, reducing average response time by 40%.

EDUCATION
B.Tech in Computer Science, 2022
"""

SAMPLE_JD_MATCHING = """
We are looking for a Backend Engineer with strong experience in
Java and Spring Boot. The ideal candidate has worked with PostgreSQL,
Docker, and building scalable REST APIs.
"""

SAMPLE_JD_UNRELATED = """
Seeking a Graphic Designer with expertise in Adobe Photoshop,
Illustrator, and brand identity design for a marketing agency.
"""


class TestChunking:
    def test_short_text_returns_single_chunk(self):
        text = "This is a short resume."
        chunks = chunk_text(text)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_empty_text_returns_no_chunks(self):
        assert chunk_text("") == []
        assert chunk_text("   ") == []

    def test_long_text_returns_multiple_chunks(self):
        text = " ".join(["word"] * 500)
        chunks = chunk_text(text, chunk_size=200, overlap=30)
        assert len(chunks) > 1
        # Each chunk should have roughly chunk_size words (last one may be shorter)
        for chunk in chunks[:-1]:
            assert len(chunk.split()) == 200


class TestEmbeddingPipeline:

    pytestmark = pytest.mark.skipif(
        os.getenv("CI") == "true",
        reason="Requires HuggingFace model download and live Qdrant — run locally only"
    )

    def test_embed_resume_stores_chunks(self):
        chunks_stored = embed_resume("test-resume-1", SAMPLE_RESUME)
        assert chunks_stored >= 1

    def test_embed_jd_stores_chunks(self):
        chunks_stored = embed_jd("test-jd-1", SAMPLE_JD_MATCHING)
        assert chunks_stored >= 1

    def test_embed_empty_text_raises(self):
        with pytest.raises(ValueError):
            embed_resume("test-resume-empty", "")

    def test_re_embedding_overwrites_previous_chunks(self):
        embed_resume("test-resume-2", "Short version of resume text.")
        chunks_stored = embed_resume("test-resume-2", "A completely different, longer resume text. " * 50)
        # Should reflect the new chunking, not accumulate old + new
        assert chunks_stored >= 1


class TestSemanticSimilarity:

    pytestmark = pytest.mark.skipif(
        os.getenv("CI") == "true",
        reason="Requires HuggingFace model download and live Qdrant — run locally only"
    )

    def test_similarity_between_matching_resume_and_jd(self):
        embed_resume("sim-resume-match", SAMPLE_RESUME)
        embed_jd("sim-jd-match", SAMPLE_JD_MATCHING)

        score = semantic_similarity("sim-resume-match", "sim-jd-match")

        assert 0.0 <= score <= 1.0
        # A backend resume vs a backend JD should score reasonably high
        assert score > 0.5

    def test_similarity_between_unrelated_resume_and_jd(self):
        embed_resume("sim-resume-unrelated", SAMPLE_RESUME)
        embed_jd("sim-jd-unrelated", SAMPLE_JD_UNRELATED)

        score = semantic_similarity("sim-resume-unrelated", "sim-jd-unrelated")

        assert 0.0 <= score <= 1.0

    def test_similarity_raises_if_resume_not_embedded(self):
        embed_jd("sim-jd-only", SAMPLE_JD_MATCHING)
        with pytest.raises(ValueError):
            semantic_similarity("nonexistent-resume-id", "sim-jd-only")

    def test_similarity_raises_if_jd_not_embedded(self):
        embed_resume("sim-resume-only", SAMPLE_RESUME)
        with pytest.raises(ValueError):
            semantic_similarity("sim-resume-only", "nonexistent-jd-id")
            
