import requests

from app.config import REMOTE_KEYWORDS
from app.scrapers.base import normalize_job

URL = "https://remoteok.com/api"
HEADERS = {"User-Agent": "Mozilla/5.0 (job-scraper personal use)"}


def fetch_jobs(timeout: int = 15) -> list[dict]:
    """RemoteOK's API is unauthenticated but returns *every* category, so
    results are filtered down to DevOps/Cloud-relevant keywords."""
    resp = requests.get(URL, headers=HEADERS, timeout=timeout)
    if resp.status_code != 200:
        return []

    data = resp.json()
    jobs = []
    for item in data:
        # first element is metadata, not a job
        if not isinstance(item, dict) or "id" not in item:
            continue

        title = item.get("position", "Untitled")
        description = item.get("description", "")
        haystack = f"{title} {description} {' '.join(item.get('tags', []))}".lower()

        if not any(kw in haystack for kw in REMOTE_KEYWORDS):
            continue

        jobs.append(
            normalize_job(
                company=item.get("company", "Unknown"),
                title=title,
                location=item.get("location") or "Remote",
                url=item.get("url", ""),
                source="remoteok",
                posted_date=item.get("date"),
                description=description,
            )
        )
    return jobs
