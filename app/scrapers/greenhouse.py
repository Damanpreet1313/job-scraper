import requests

from app.config import DEVOPS_KEYWORDS, JUNIOR_KEYWORDS, SENIOR_EXCLUSION_KEYWORDS
from app.scrapers.base import normalize_job
from app.scrapers.keywords import is_senior
from app.scrapers.locations import is_location_allowed

BASE_URL = "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"

DEVOPS_KWS = [k.lower() for k in DEVOPS_KEYWORDS]
JUNIOR_KWS = [k.lower() for k in JUNIOR_KEYWORDS]


def _has_keyword(text: str, keywords: list[str]) -> bool:
    t = text.lower()
    return any(kw in t for kw in keywords)


def _title_matches(title: str) -> bool:
    t = title.lower()
    has_devops = _has_keyword(t, DEVOPS_KWS)
    has_junior = _has_keyword(t, JUNIOR_KWS)
    is_senior_role = is_senior(title)
    return has_devops and has_junior and not is_senior_role


def fetch_jobs(slug: str, timeout: int = 15) -> list[dict]:
    """Pulls all postings for a company's Greenhouse board.
    Docs: https://developers.greenhouse.io/job-board.html
    Filters to DevOps/Cloud roles by title only (avoids boilerplate false positives).
    """
    url = BASE_URL.format(slug=slug)
    resp = requests.get(url, timeout=timeout)
    if resp.status_code != 200:
        return []

    data = resp.json()
    jobs = []
    for item in data.get("jobs", []):
        title = item.get("title", "Untitled")
        if not _title_matches(title):
            continue
        location = (item.get("location") or {}).get("name")
        description = item.get("content", "")
        allowed, reason = is_location_allowed(location, description)
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
