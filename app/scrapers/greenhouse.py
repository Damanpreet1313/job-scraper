import requests

from app.scrapers.base import normalize_job
from app.scrapers.keywords import is_senior, is_junior_devops
import app.scrapers.locations as locations

BASE_URL = "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"


def fetch_jobs(slug: str, timeout: int = 15) -> list[dict]:
    """Pulls all postings for a company's Greenhouse board.
    Docs: https://developers.greenhouse.io/job-board.html
    Filters to DevOps/Cloud junior roles using title + description.
    """
    url = BASE_URL.format(slug=slug)
    resp = requests.get(url, timeout=timeout)
    if resp.status_code != 200:
        return []

    data = resp.json()
    jobs = []
    for item in data.get("jobs", []):
        title = item.get("title", "Untitled")
        if is_senior(title):
            continue
        description = item.get("content", "")
        if not is_junior_devops(title, description):
            continue
        location = (item.get("location") or {}).get("name")
        allowed, reason = locations.is_location_allowed(location, description)
        if not allowed:
            continue
        jobs.append(
            normalize_job(
                company=slug,
                title=title,
                location=location,
                url=item.get("absolute_url", ""),
                source="greenhouse",
                posted_date=item.get("updated_at"),
                description=description,
            )
        )
    return jobs
