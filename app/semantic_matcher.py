"""Semantic matching using sentence-transformers embeddings."""
import os
from functools import lru_cache
from pathlib import Path
from typing import Optional

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from app.matcher import load_resume_text

MODEL_NAME = os.getenv("EMBEDDING_MODEL") or "all-MiniLM-L6-v2"
EMBEDDING_CACHE_DIR = Path(__file__).resolve().parent.parent / ".embedding_cache"
EMBEDDING_CACHE_DIR.mkdir(exist_ok=True)


@lru_cache(maxsize=1)
def get_model() -> SentenceTransformer:
    """Load sentence-transformer model (cached)."""
    return SentenceTransformer(MODEL_NAME, cache_folder=str(EMBEDDING_CACHE_DIR))


def encode_texts(texts: list[str]) -> np.ndarray:
    """Encode texts to embeddings."""
    model = get_model()
    return model.encode(texts, convert_to_numpy=True, show_progress_bar=False)


def score_jobs_semantic(
    jobs: list[dict],
    resume_text: Optional[str] = None,
    batch_size: int = 32,
) -> list[dict]:
    """Score jobs using semantic embeddings (sentence-transformers).
    
    Falls back to TF-IDF if model fails to load.
    """
    from app.matcher import score_jobs as score_jobs_tfidf
    
    resume_text = resume_text if resume_text is not None else load_resume_text()
    if not resume_text.strip() or not jobs:
        for job in jobs:
            job["match_score"] = 0.0
        return jobs

    try:
        # Prepare corpus: resume + job titles + descriptions
        job_texts = [f"{j['title']} {j.get('description', '')}" for j in jobs]
        corpus = [resume_text] + job_texts

        # Encode in batches
        embeddings = []
        for i in range(0, len(corpus), batch_size):
            batch = corpus[i:i + batch_size]
            embeddings.append(encode_texts(batch))
        embeddings = np.vstack(embeddings)

        resume_emb = embeddings[0:1]
        job_embs = embeddings[1:]
        scores = cosine_similarity(resume_emb, job_embs)[0]

        for job, score in zip(jobs, scores):
            job["match_score"] = float(score)

        return jobs
    except Exception as e:
        print(f"Semantic matching failed ({e}), falling back to TF-IDF")
        return score_jobs_tfidf(jobs, resume_text)


def score_jobs_hybrid(
    jobs: list[dict],
    resume_text: Optional[str] = None,
    semantic_weight: float = 0.7,
    tfidf_weight: float = 0.3,
) -> list[dict]:
    """Hybrid scoring: combine semantic embeddings + TF-IDF.
    
    Uses weighted average of both scores for more robust matching.
    """
    from app.matcher import score_jobs as score_jobs_tfidf
    
    # Get TF-IDF scores
    jobs_tfidf = score_jobs_tfidf(jobs, resume_text)
    
    # Get semantic scores
    jobs_semantic = score_jobs_semantic(jobs, resume_text)
    
    # Combine
    for j_tfidf, j_sem in zip(jobs_tfidf, jobs_semantic):
        tfidf_score = j_tfidf.get("match_score", 0.0)
        sem_score = j_sem.get("match_score", 0.0)
        j_tfidf["match_score"] = (
            tfidf_weight * tfidf_score + semantic_weight * sem_score
        )
    
    return jobs_tfidf