import requests

from app.scrapers.base import normalize_job
from app.scrapers.keywords import is_senior, is_junior_devops
from app.scrapers.locations import is_location_allowed

URL = "https://remoteok.com/api"
HEADERS = {"User-Agent": "Mozilla/5.0 (job-scraper personal use)"}


def fetch_jobs(timeout: int = 15) -> list[dict]:
    """RemoteOK's API is unauthenticated but returns *every* category, so
    results are filtered down to DevOps/Cloud-relevant junior roles."""
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
        if is_senior(title):
            continue

        description = item.get("description", "")
        tags = item.get("tags", [])

        # Check title + description (not tags, which are too broad)
        if not is_junior_devops(title, description):
            continue

        location = item.get("location") or "Remote"
        allowed, reason = is_location_allowed(location, description)
        if not allowed:
            continue

        jobs.append(
            normalize_job(
                company=item.get("company", "Unknown"),
                title=title,
                location=location,
                url=item.get("url", ""),
                source="remoteok",
                posted_date=item.get("date"),
                description=description,
            )
        )
    return jobs
