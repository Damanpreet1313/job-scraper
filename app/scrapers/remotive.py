import requests

from app.config import REMOTE_KEYWORDS
from app.scrapers.base import normalize_job

URL = "https://remotive.com/api/remote-jobs"


def fetch_jobs(timeout: int = 15, max_pages: int = 5) -> list[dict]:
    """Remotive's public job API returns every remote category, so results
    are filtered down to DevOps/Cloud-relevant keywords. Paginates via the
    `next_url` field until `max_pages` or the end of the list."""
    jobs = []
    url = URL
    for _ in range(max_pages):
        resp = requests.get(url, timeout=timeout)
        if resp.status_code != 200:
            break

        data = resp.json()
        for item in data.get("jobs", []):
            title = item.get("title", "Untitled")
            haystack = f"{title} {' '.join(item.get('tags', []))}".lower()
            if not any(kw in haystack for kw in REMOTE_KEYWORDS):
                continue

            jobs.append(
                normalize_job(
                    company=item.get("company_name", "Unknown"),
                    title=title,
                    location=item.get("candidate_required_location") or "Remote",
                    url=item.get("url", ""),
                    source="remotive",
                    posted_date=item.get("publication_date"),
                    description=item.get("description", ""),
                )
            )

        next_url = data.get("next_url")
        if not next_url:
            break
        url = next_url
    return jobs
