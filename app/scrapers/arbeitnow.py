import requests

from app.scrapers.base import normalize_job
from app.scrapers.keywords import is_senior, is_junior_devops
from app.scrapers.locations import is_location_allowed

URL = "https://arbeitnow.com/api/job-board-api"


def fetch_jobs(timeout: int = 15) -> list[dict]:
    """Arbeitnow's public job-board API returns every tech category, so
    results are filtered down to DevOps/Cloud-relevant junior roles."""
    resp = requests.get(URL, timeout=timeout)
    if resp.status_code != 200:
        return []

    data = resp.json()
    jobs = []
    for item in data.get("data", []):
        title = item.get("title", "Untitled")
        if is_senior(title):
            continue

        description = item.get("description", "")
        if not is_junior_devops(title, description):
            continue

        location = item.get("location") or ("Remote" if item.get("remote") else None)
        allowed, reason = is_location_allowed(location, description)
        if not allowed:
            continue

        jobs.append(
            normalize_job(
                company=item.get("company_name", "Unknown"),
                title=title,
                location=location,
                url=item.get("url", ""),
                source="arbeitnow",
                posted_date=item.get("created_at"),
                description=description,
            )
        )
    return jobs
