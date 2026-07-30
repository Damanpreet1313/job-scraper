import requests

from app.scrapers.base import normalize_job

BASE_URL = "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"


def fetch_jobs(slug: str, timeout: int = 15) -> list[dict]:
    """Pulls all postings for a company's Greenhouse board.
    Docs: https://developers.greenhouse.io/job-board.html
    """
    url = BASE_URL.format(slug=slug)
    resp = requests.get(url, timeout=timeout)
    if resp.status_code != 200:
        return []

    data = resp.json()
    jobs = []
    for item in data.get("jobs", []):
        location = (item.get("location") or {}).get("name")
        jobs.append(
            normalize_job(
                company=slug,
                title=item.get("title", "Untitled"),
                location=location,
                url=item.get("absolute_url", ""),
                source="greenhouse",
                posted_date=item.get("updated_at"),
                description=item.get("content", ""),
            )
        )
    return jobs
