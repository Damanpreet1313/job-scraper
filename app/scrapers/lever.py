import requests

from app.scrapers.base import normalize_job

BASE_URL = "https://api.lever.co/v0/postings/{slug}?mode=json"


def fetch_jobs(slug: str, timeout: int = 15) -> list[dict]:
    """Pulls all postings for a company's Lever board.
    Docs: https://github.com/lever/postings-api
    """
    url = BASE_URL.format(slug=slug)
    resp = requests.get(url, timeout=timeout)
    if resp.status_code != 200:
        return []

    data = resp.json()
    jobs = []
    for item in data:
        categories = item.get("categories", {})
        description = item.get("descriptionPlain") or item.get("description", "")
        jobs.append(
            normalize_job(
                company=slug,
                title=item.get("text", "Untitled"),
                location=categories.get("location"),
                url=item.get("hostedUrl", ""),
                source="lever",
                posted_date=str(item.get("createdAt", "")),
                description=description,
            )
        )
    return jobs
