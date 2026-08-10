import requests

from app.config import (
    ADZUNA_APP_ID,
    ADZUNA_APP_KEY,
    ADZUNA_REGION,
    REMOTE_KEYWORDS,
)
from app.scrapers.base import normalize_job

BASE_URL = "https://api.adzuna.com/v1/api/jobs/{region}/search/1"


def fetch_jobs(timeout: int = 15) -> list[dict]:
    """Adzuna's search API (free account at developer.adzuna.com). Region
    defaults to "in" (India) since that's where most DevOps internships for
    this use case are listed. Returns [] if no API keys are configured."""
    if not ADZUNA_APP_ID or not ADZUNA_APP_KEY:
        print("  adzuna skipped: set ADZUNA_APP_ID / ADZUNA_APP_KEY in .env")
        return []

    resp = requests.get(
        BASE_URL.format(region=ADZUNA_REGION),
        params={
            "app_id": ADZUNA_APP_ID,
            "app_key": ADZUNA_APP_KEY,
            "what": "devops",
            "results_per_page": 50,
        },
        timeout=timeout,
    )
    if resp.status_code != 200:
        return []

    jobs = []
    for item in resp.json().get("results", []):
        title = item.get("title", "Untitled")
        category = (item.get("category") or {}).get("label", "")
        haystack = f"{title} {category}".lower()
        if not any(kw in haystack for kw in REMOTE_KEYWORDS):
            continue

        location = (item.get("location") or {}).get("display_name")
        jobs.append(
            normalize_job(
                company=(item.get("company") or {}).get("display_name", "Unknown"),
                title=title,
                location=location,
                url=item.get("redirect_url", ""),
                source="adzuna",
                posted_date=item.get("created"),
                description=item.get("description", ""),
            )
        )
    return jobs
