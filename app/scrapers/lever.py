import requests

from app.config import DEVOPS_KEYWORDS, JUNIOR_KEYWORDS
from app.scrapers.base import normalize_job

BASE_URL = "https://api.lever.co/v0/postings/{slug}?mode=json"

DEVOPS_KWS = [k.lower() for k in DEVOPS_KEYWORDS]
JUNIOR_KWS = [k.lower() for k in JUNIOR_KEYWORDS]


def _title_matches(title: str) -> bool:
    t = title.lower()
    has_devops = any(kw in t for kw in DEVOPS_KWS)
    has_junior = any(kw in t for kw in JUNIOR_KWS)
    return has_devops and (has_junior or True)


def fetch_jobs(slug: str, timeout: int = 15) -> list[dict]:
    """Pulls all postings for a company's Lever board.
    Docs: https://github.com/lever/postings-api
    Filters to DevOps/Cloud roles by title only.
    """
    url = BASE_URL.format(slug=slug)
    resp = requests.get(url, timeout=timeout)
    if resp.status_code != 200:
        return []

    data = resp.json()
    jobs = []
    for item in data:
        title = item.get("text", "Untitled")
        if not _title_matches(title):
            continue
        categories = item.get("categories", {})
        description = item.get("descriptionPlain") or item.get("description", "")
        jobs.append(
            normalize_job(
                company=slug,
                title=title,
                location=categories.get("location"),
                url=item.get("hostedUrl", ""),
                source="lever",
                posted_date=str(item.get("createdAt", "")),
                description=description,
            )
        )
    return jobs
