"""Otta job scraper via public API."""
import requests

from app.scrapers.base import normalize_job
from app.scrapers.keywords import is_senior, is_devops_role, JUNIOR_PATTERNS
from app.scrapers.locations import is_location_allowed

OTTA_API_URL = "https://api.otta.com/v2/jobs"
OTTA_PARAMS = {
    "roles[]": [
        "devops-engineer",
        "cloud-engineer",
        "site-reliability-engineer",
        "platform-engineer",
        "infrastructure-engineer",
    ],
    "locations[]": ["remote"],
    "experience_levels[]": ["junior", "entry", "intern"],
    "page": 1,
    "per_page": 50,
}


def fetch_jobs(timeout: int = 15, max_pages: int = 3) -> list[dict]:
    """Otta API - curated tech jobs, filter for junior DevOps/Cloud."""
    jobs = []
    for page in range(1, max_pages + 1):
        params = OTTA_PARAMS.copy()
        params["page"] = page

        try:
            resp = requests.get(OTTA_API_URL, params=params, timeout=timeout)
            if resp.status_code != 200:
                break
        except Exception:
            break

        data = resp.json()
        results = data.get("results", [])
        if not results:
            break

        for item in results:
            title = item.get("title", "Untitled")
            if is_senior(title):
                continue

            company = item.get("company", {}).get("name", "Unknown")
            description = item.get("description", "")
            location = item.get("location", "Remote")

            if not is_devops_role(title):
                continue

            haystack = f"{title} {description}"
            has_junior = any(p.search(haystack) for p in JUNIOR_PATTERNS)
            if not has_junior:
                continue

            allowed, reason = is_location_allowed(location, description)
            if not allowed:
                continue

            jobs.append(
                normalize_job(
                    company=company,
                    title=title,
                    location=location,
                    url=item.get("url", ""),
                    source="otta",
                    posted_date=item.get("published_at"),
                    description=description,
                )
            )
    return jobs