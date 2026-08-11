import requests

from app.config import DEVOPS_KEYWORDS, JUNIOR_KEYWORDS
from app.scrapers.base import normalize_job

BASE_URL = "https://api.ashbyhq.com/posting-api/job-board/{slug}"

DEVOPS_KWS = [k.lower() for k in DEVOPS_KEYWORDS]
JUNIOR_KWS = [k.lower() for k in JUNIOR_KEYWORDS]


def _title_matches(title: str) -> bool:
    t = title.lower()
    has_devops = any(kw in t for kw in DEVOPS_KWS)
    has_junior = any(kw in t for kw in JUNIOR_KWS)
    return has_devops and (has_junior or True)


def fetch_jobs(slug: str, timeout: int = 15) -> list[dict]:
    """Pulls all postings for a company's Ashby job board.
    Ashby's public board API shape has changed before — if this returns
    empty, open the URL directly in a browser and adjust the field names
    below to match the current response.
    Filters to DevOps/Cloud roles by title only.
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
        jobs.append(
            normalize_job(
                company=slug,
                title=title,
                location=item.get("location") or item.get("locationName"),
                url=item.get("jobUrl") or item.get("applyUrl", ""),
                source="ashby",
                posted_date=item.get("publishedAt") or item.get("updatedAt"),
                description=item.get("descriptionPlain") or item.get("description", ""),
            )
        )
    return jobs
