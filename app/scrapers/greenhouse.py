import requests

from app.config import DEVOPS_KEYWORDS, JUNIOR_KEYWORDS
from app.scrapers.base import normalize_job

BASE_URL = "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"

DEVOPS_KWS = [k.lower() for k in DEVOPS_KEYWORDS]
JUNIOR_KWS = [k.lower() for k in JUNIOR_KEYWORDS]


def _title_matches(title: str) -> bool:
    t = title.lower()
    has_devops = any(kw in t for kw in DEVOPS_KWS)
    has_junior = any(kw in t for kw in JUNIOR_KWS)
    return has_devops and (has_junior or True)  # keep all devops roles for now; junior is bonus


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
        jobs.append(
            normalize_job(
                company=slug,
                title=title,
                location=location,
                url=item.get("absolute_url", ""),
                source="greenhouse",
                posted_date=item.get("updated_at"),
                description=item.get("content", ""),
            )
        )
    return jobs
