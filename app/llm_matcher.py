import json
import re

import requests

from app.config import GROQ_API_KEY, GROQ_MODEL
from app.matcher import score_jobs as score_jobs_tfidf

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


def score_jobs(jobs: list[dict], resume_text: str, candidate_pool: int = 40) -> list[dict]:
    """Two-stage matching: TF-IDF ranks every job first (cheap, no API
    calls), then only the top `candidate_pool` jobs get sent to Groq for a
    sharper semantic score + a one-line reason. Keeps API usage bounded
    regardless of how many postings a run scrapes. Falls back to pure
    TF-IDF entirely if no GROQ_API_KEY is set.
    """
    jobs = score_jobs_tfidf(jobs, resume_text)  # every job gets a baseline tfidf match_score

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
            job["match_score"] = score  # replace tfidf score with Groq's sharper one

    return jobs
