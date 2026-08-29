"""Greenhouse job board scraper."""
from app.logging_config import get_logger
from app.scrapers.base import normalize_job
from app.scrapers.http_client import get_http_client
from app.scrapers.keywords import is_senior, is_junior_devops
from app.scrapers.locations import is_location_allowed

logger = get_logger(__name__)

BASE_URL = "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"


async def fetch_jobs(slug: str, timeout: int = 15) -> list[dict]:
    """Pulls all postings for a company's Greenhouse board."""
    url = BASE_URL.format(slug=slug)
    client = await get_http_client()
    try:
        resp = await client.get(url, timeout=timeout)
        if resp.status_code != 200:
            logger.warning("greenhouse_non_200", extra={"slug": slug, "status": resp.status_code})
            return []

        data = resp.json()
        jobs = []
        for item in data.get("jobs", []):
            title = item.get("title", "Untitled")
            if is_senior(title):
                continue
            description = item.get("content", "")
            if not is_junior_devops(title, description):
                continue
            location = (item.get("location") or {}).get("name")
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
    except Exception as e:
        logger.error("greenhouse_fetch_failed", extra={"slug": slug, "error": str(e)})
        return []