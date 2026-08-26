import requests

from app.scrapers.base import normalize_job
from app.scrapers.keywords import is_senior, is_junior_devops
import app.scrapers.locations as locations

BASE_URL = "https://api.ashbyhq.com/posting-api/job-board/{slug}"


def fetch_jobs(slug: str, timeout: int = 15) -> list[dict]:
    """Pulls all postings for a company's Ashby job board.
    Ashby's public board API shape has changed before — if this returns
    empty, open the URL directly in a browser and adjust the field names
    below to match the current response.
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
        description = item.get("descriptionPlain") or item.get("description", "")
        if not is_junior_devops(title, description):
            continue
        location = item.get("location") or item.get("locationName")
        allowed, reason = locations.is_location_allowed(location, description)
        if not allowed:
            continue
        jobs.append(
            normalize_job(
                company=slug,
                title=title,
                location=location,
                url=item.get("jobUrl") or item.get("applyUrl", ""),
                source="ashby",
                posted_date=item.get("publishedAt") or item.get("updatedAt"),
                description=description,
            )
        )
    return jobs
