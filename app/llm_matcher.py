import json
import os
import re

import requests

from app.config import GROQ_API_KEY, GROQ_MODEL
from app.matcher import score_jobs as score_jobs_tfidf
from app.semantic_matcher import score_jobs_semantic, score_jobs_hybrid

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

SYSTEM_PROMPT = (
    "You are a strict job-relevance scorer. Given a candidate's resume/skills "
    "and a single job posting, output ONLY a JSON object with two fields: "
    '"score" (a number from 0.0 to 1.0 for how well the job fits the '
    'candidate\'s skills/experience) and "reason" (one short sentence, under '
    "15 words, explaining the score). No other text, no markdown — just the "
    "JSON object."
)


def _extract_json(content: str) -> dict:
    try:
        return json.loads(content)
    except (json.JSONDecodeError, TypeError):
        pass
    # Fallback: model wrapped the JSON in prose or code fences
    match = re.search(r"\{.*\}", content or "", re.DOTALL)
    if match:
        return json.loads(match.group(0))
    raise ValueError("no JSON object found in response")


def _score_one(resume_text: str, job: dict, timeout: int = 20) -> tuple[float | None, str]:
    user_prompt = (
        f"RESUME/SKILLS:\n{resume_text}\n\n"
        f"JOB TITLE: {job.get('title', '')}\n"
        f"JOB DESCRIPTION:\n{(job.get('description') or '')[:2000]}"
    )
    try:
        resp = requests.post(
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": GROQ_MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.1,
                "max_tokens": 100,
            },
            timeout=timeout,
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        parsed = _extract_json(content)
        score = float(parsed.get("score", 0.0))
        reason = str(parsed.get("reason", ""))[:200]
        return max(0.0, min(1.0, score)), reason
    except Exception as e:
        return None, f"llm scoring unavailable ({type(e).__name__})"


def score_jobs(
    jobs: list[dict],
    resume_text: str,
    candidate_pool: int = 40,
    use_semantic: bool = True,
) -> list[dict]:
    """Three-stage matching:
    1. TF-IDF ranks every job (cheap, no API calls)
    2. Sentence-transformers semantic embeddings (local, no API) for better matching
    3. Top `candidate_pool` jobs get sent to Groq for sharpest score + reason
    
    Falls back gracefully: semantic -> TF-IDF, Groq -> semantic.
    """
    # Stage 1: TF-IDF baseline
    jobs = score_jobs_tfidf(jobs, resume_text)
    
    # Stage 2: Semantic embeddings (sentence-transformers) - local, fast
    if use_semantic:
        try:
            jobs = score_jobs_semantic(jobs, resume_text)
        except Exception as e:
            print(f"Semantic matching failed ({e}), keeping TF-IDF scores")
    
    # Stage 3: Groq LLM for top candidates (if API key available)
    if not GROQ_API_KEY or not jobs:
        for job in jobs:
            job.setdefault("match_reason", None)
        return jobs

    ranked = sorted(jobs, key=lambda j: j.get("match_score", 0), reverse=True)
    candidate_urls = {j["url"] for j in ranked[:candidate_pool]}

    for job in jobs:
        if job["url"] not in candidate_urls:
            job["match_reason"] = None
            continue
        score, reason = _score_one(resume_text, job)
        job["match_reason"] = reason
        if score is not None:
            job["match_score"] = score  # replace with Groq's sharper score

    return jobs
