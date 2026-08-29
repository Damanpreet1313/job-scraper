"""Arbeitnow job scraper."""
from app.logging_config import get_logger
from app.scrapers.base import normalize_job
from app.scrapers.http_client import get_http_client
from app.scrapers.keywords import is_senior, is_junior_devops
from app.scrapers.locations import is_location_allowed

logger = get_logger(__name__)

URL = "https://arbeitnow.com/api/job-board-api"


async def fetch_jobs(timeout: int = 15) -> list[dict]:
    """Arbeitnow's public job-board API returns every tech category."""
    client = await get_http_client()
    try:
        resp = await client.get(URL, timeout=timeout)
        if resp.status_code != 200:
            logger.warning("arbeitnow_non_200", extra={"status": resp.status_code})
            return []

        data = resp.json()
        jobs = []
        for item in data.get("data", []):
            title = item.get("title", "Untitled")
            if is_senior(title):
                continue

            description = item.get("description", "")
            if not is_junior_devops(title, description):
                continue

            location = item.get("location") or ("Remote" if item.get("remote") else None)
            allowed, reason = is_location_allowed(location, description)
            if not allowed:
                continue

            jobs.append(
                normalize_job(
                    company=item.get("company_name", "Unknown"),
                    title=title,
                    location=location,
                    url=item.get("url", ""),
                    source="arbeitnow",
                    posted_date=item.get("created_at"),
                    description=description,
                )
            )
        return jobs
    except Exception as e:
        logger.error("arbeitnow_fetch_failed", extra={"error": str(e)})
        return []