"""Lever job board scraper."""
from app.logging_config import get_logger
from app.scrapers.base import normalize_job
from app.scrapers.http_client import get_http_client
from app.scrapers.keywords import is_senior, is_junior_devops
from app.scrapers.locations import is_location_allowed

logger = get_logger(__name__)

BASE_URL = "https://api.lever.co/v0/postings/{slug}?mode=json"


async def fetch_jobs(slug: str, timeout: int = 15) -> list[dict]:
    """Pulls all postings for a company's Lever board."""
    url = BASE_URL.format(slug=slug)
    client = await get_http_client()
    try:
        resp = await client.get(url, timeout=timeout)
        if resp.status_code != 200:
            logger.warning("lever_non_200", extra={"slug": slug, "status": resp.status_code})
            return []

        data = resp.json()
        jobs = []
        for item in data:
            title = item.get("text", "Untitled")
            if is_senior(title):
                continue
            description = item.get("descriptionPlain") or item.get("description", "")
            if not is_junior_devops(title, description):
                continue
            categories = item.get("categories", {})
            location = categories.get("location")
            allowed, reason = is_location_allowed(location, description)
            if not allowed:
                continue
            jobs.append(
                normalize_job(
                    company=slug,
                    title=title,
                    location=location,
                    url=item.get("hostedUrl", ""),
                    source="lever",
                    posted_date=str(item.get("createdAt", "")),
                    description=description,
                )
            )
        return jobs
    except Exception as e:
        logger.error("lever_fetch_failed", extra={"slug": slug, "error": str(e)})
        return []