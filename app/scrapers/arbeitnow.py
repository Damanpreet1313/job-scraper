import requests

from app.config import REMOTE_KEYWORDS
from app.scrapers.base import normalize_job

URL = "https://arbeitnow.com/api/job-board-api"


def fetch_jobs(timeout: int = 15) -> list[dict]:
    """Arbeitnow's public job-board API returns every tech category, so
    results are filtered down to DevOps/Cloud-relevant keywords."""
    resp = requests.get(URL, timeout=timeout)
    if resp.status_code != 200:
        return []

    data = resp.json()
    jobs = []
    for item in data.get("data", []):
        title = item.get("title", "Untitled")
        haystack = f"{title} {' '.join(item.get('tags', []))}".lower()
        if not any(kw in haystack for kw in REMOTE_KEYWORDS):
            continue

        jobs.append(
            normalize_job(
                company=item.get("company_name", "Unknown"),
                title=title,
                location=item.get("location") or ("Remote" if item.get("remote") else None),
                url=item.get("url", ""),
                source="arbeitnow",
                posted_date=item.get("created_at"),
                description=item.get("description", ""),
            )
        )
    return jobs
