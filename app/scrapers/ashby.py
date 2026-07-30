import requests

from app.scrapers.base import normalize_job

BASE_URL = "https://api.ashbyhq.com/posting-api/job-board/{slug}"


def fetch_jobs(slug: str, timeout: int = 15) -> list[dict]:
    """Pulls all postings for a company's Ashby job board.
    Ashby's public board API shape has changed before — if this returns
    empty, open the URL directly in a browser and adjust the field names
    below to match the current response.
    """
    url = BASE_URL.format(slug=slug)
    resp = requests.get(url, timeout=timeout)
    if resp.status_code != 200:
        return []

    data = resp.json()
    jobs = []
    for item in data.get("jobs", []):
        jobs.append(
            normalize_job(
                company=slug,
                title=item.get("title", "Untitled"),
                location=item.get("location") or item.get("locationName"),
                url=item.get("jobUrl") or item.get("applyUrl", ""),
                source="ashby",
                posted_date=item.get("publishedAt") or item.get("updatedAt"),
                description=item.get("descriptionPlain") or item.get("description", ""),
            )
        )
    return jobs
