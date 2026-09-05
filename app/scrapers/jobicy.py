"""Jobicy job scraper."""
from app.logging_config import get_logger
from app.scrapers.base import normalize_job
from app.scrapers.http_client import get_http_client
from app.scrapers.keywords import is_senior, is_junior_devops
from app.scrapers.locations import is_location_allowed

logger = get_logger(__name__)

URL = "https://jobicy.com/api/v2/remote-jobs"
PARAMS = {"count": 50}


async def fetch_jobs(timeout: int = 15) -> list[dict]:
    """Jobicy's public API returns remote postings across every industry."""
    client = await get_http_client()
    try:
        resp = await client.get(URL, params=PARAMS, timeout=timeout)
        if resp.status_code != 200:
            logger.warning("jobicy_non_200", extra={"status": resp.status_code})
            return []

        data = resp.json()
        jobs = []
        for item in data.get("jobs", []):
            title = item.get("jobTitle", "Untitled")
            if is_senior(title):
                continue

            description = item.get("jobDescription", "")
            if not is_junior_devops(title, description):
                continue

            location = item.get("jobGeo") or "Remote"
            allowed, reason = is_location_allowed(location, description)
            if not allowed:
                continue

            jobs.append(
                normalize_job(
                    company=item.get("companyName", "Unknown"),
                    title=title,
                    location=location,
                    url=item.get("url", ""),
                    source="jobicy",
                    posted_date=item.get("pubDate"),
                    description=description,
                )
            )
        return jobs
    except Exception as e:
        logger.error("jobicy_fetch_failed", extra={"error": str(e)})
        return []