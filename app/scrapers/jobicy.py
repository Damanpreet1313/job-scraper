import requests

from app.config import REMOTE_KEYWORDS
from app.scrapers.base import normalize_job

URL = "https://jobicy.com/api/v2/remote-jobs"
# "count" caps the number of postings returned per request (1-50).
PARAMS = {"count": 50}


def fetch_jobs(timeout: int = 15) -> list[dict]:
    """Jobicy's public API returns remote postings across every industry, so
    results are filtered down to DevOps/Cloud-relevant keywords."""
    resp = requests.get(URL, params=PARAMS, timeout=timeout)
    if resp.status_code != 200:
        return []

    data = resp.json()
    jobs = []
    for item in data.get("jobs", []):
        title = item.get("jobTitle", "Untitled")
        haystack = f"{title} {item.get('jobIndustry', '')}".lower()
        if not any(kw in haystack for kw in REMOTE_KEYWORDS):
            continue

        jobs.append(
            normalize_job(
                company=item.get("companyName", "Unknown"),
                title=title,
                location=item.get("jobGeo") or "Remote",
                url=item.get("url", ""),
                source="jobicy",
                posted_date=item.get("pubDate"),
                description=item.get("jobDescription", ""),
            )
        )
    return jobs
