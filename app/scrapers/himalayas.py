import requests

from app.scrapers.base import normalize_job
from app.scrapers.keywords import is_senior, is_junior_devops
from app.scrapers.locations import is_location_allowed

HIMALAYAS_URL = "https://himalayas.app/jobs/api"


def fetch_jobs(timeout: int = 15, max_pages: int = 5) -> list[dict]:
    """Himalayas.app public job API - returns remote jobs across categories.
    Filtered to DevOps/Cloud-relevant junior roles."""
    jobs = []
    for page in range(1, max_pages + 1):
        resp = requests.get(
            HIMALAYAS_URL,
            params={"page": page, "per_page": 50},
            timeout=timeout,
        )
        if resp.status_code != 200:
            break

        data = resp.json()
        for item in data.get("jobs", []):
            title = item.get("title", "Untitled")
            if is_senior(title):
                continue

            description = item.get("description", "")
            if not is_junior_devops(title, description):
                continue

            location = item.get("location") or "Remote"
            allowed, reason = is_location_allowed(location, description)
            if not allowed:
                continue

            jobs.append(
                normalize_job(
                    company=item.get("company_name", "Unknown"),
                    title=title,
                    location=location,
                    url=item.get("url", ""),
                    source="himalayas",
                    posted_date=item.get("published_at"),
                    description=description,
                )
            )

        if not data.get("jobs"):
            break
    return jobs