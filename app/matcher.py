from functools import lru_cache
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

RESUME_PATH = Path(__file__).resolve().parent.parent / "resume.txt"


@lru_cache(maxsize=1)
def load_resume_text() -> str:
    if not RESUME_PATH.exists():
        return ""
    return RESUME_PATH.read_text(encoding="utf-8")


def score_jobs(jobs: list[dict], resume_text: str | None = None) -> list[dict]:
    """Adds a `match_score` (0-1 cosine similarity) to each job dict by
    comparing title+description against resume_text.

    This uses TF-IDF rather than sentence-transformer embeddings on purpose:
    it's fast, has no model download, and works well for skill-keyword-heavy
    text like job postings and a resume. If you want semantic matching later
    (same approach as Vizzy-2's RAG setup), swap this function's body for a
    sentence-transformers encode() + cosine_similarity call — the call sites
    in run_scrape.py / main.py don't need to change.
    """
    resume_text = resume_text if resume_text is not None else load_resume_text()
    if not resume_text.strip() or not jobs:
        for job in jobs:
            job["match_score"] = 0.0
        return jobs

    corpus = [resume_text] + [f"{j['title']} {j.get('description', '')}" for j in jobs]

    vectorizer = TfidfVectorizer(stop_words="english", max_features=5000)
    tfidf = vectorizer.fit_transform(corpus)

    resume_vec = tfidf[0:1]
    job_vecs = tfidf[1:]
    scores = cosine_similarity(resume_vec, job_vecs)[0]

    for job, score in zip(jobs, scores):
        job["match_score"] = float(score)

    return jobs
