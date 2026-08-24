import requests

from app.scrapers.base import normalize_job
from app.scrapers.keywords import is_senior, is_junior_devops
from app.scrapers.locations import is_location_allowed

URL = "https://jobicy.com/api/v2/remote-jobs"
# "count" caps the number of postings returned per request (1-50).
PARAMS = {"count": 50}


def fetch_jobs(timeout: int = 15) -> list[dict]:
    """Jobicy's public API returns remote postings across every industry, so
    results are filtered down to DevOps/Cloud-relevant junior roles."""
    resp = requests.get(URL, params=PARAMS, timeout=timeout)
    if resp.status_code != 200:
        return []

    data = resp.json()
    jobs = []
    for item in data.get("jobs", []):
        title = item.get("jobTitle", "Untitled")
        if is_senior(title):
            continue

        description = item.get("jobDescription", "")
        if not is_junior_devops(title, description):
            continue

        location = item.get("jobGeo") or "Remote"
        allowed, reason = is_location_allowed(location, description)
        if not allowed:
            continue

        jobs.append(
            normalize_job(
                company=item.get("companyName", "Unknown"),
                title=title,
                location=location,
                url=item.get("url", ""),
                source="jobicy",
                posted_date=item.get("pubDate"),
                description=description,
            )
        )
    return jobs
