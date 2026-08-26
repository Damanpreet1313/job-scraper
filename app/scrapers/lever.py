import requests

from app.scrapers.base import normalize_job
from app.scrapers.keywords import is_senior, is_junior_devops
import app.scrapers.locations as locations

BASE_URL = "https://api.lever.co/v0/postings/{slug}?mode=json"


def fetch_jobs(slug: str, timeout: int = 15) -> list[dict]:
    """Pulls all postings for a company's Lever board.
    Docs: https://github.com/lever/postings-api
    Filters to DevOps/Cloud junior roles using title + description.
    """
    url = BASE_URL.format(slug=slug)
    resp = requests.get(url, timeout=timeout)
    if resp.status_code != 200:
        return []

    data = resp.json()
    jobs = []
    for item in data:
        title = item.get("text", "Untitled")
        if is_senior(title):
            continue
        description = item.get("descriptionPlain") or item.get("description", "")
        if not is_junior_devops(title, description):
            continue
        categories = item.get("categories", {})
        location = categories.get("location")
        allowed, reason = locations.is_location_allowed(location, description)
        if not allowed:
            continue
        jobs.append(
            normalize_job(
                company=slug,
                title=title,
                location=location,
                url=item.get("hostedUrl", ""),
                source="lever",
                posted_date=str(item.get("createdAt", "")),
                description=description,
            )
        )
    return jobs
