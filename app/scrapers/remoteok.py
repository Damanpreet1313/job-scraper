"""RemoteOK job scraper."""
from app.logging_config import get_logger
from app.scrapers.base import normalize_job
from app.scrapers.http_client import get_http_client
from app.scrapers.keywords import is_senior, is_junior_devops
from app.scrapers.locations import is_location_allowed

logger = get_logger(__name__)

URL = "https://remoteok.com/api"


async def fetch_jobs(timeout: int = 15) -> list[dict]:
    """RemoteOK's API returns every category, filtered to DevOps/Cloud junior roles."""
    client = await get_http_client()
    try:
        resp = await client.get(URL, timeout=timeout)
        if resp.status_code != 200:
            logger.warning("remoteok_non_200", extra={"status": resp.status_code})
            return []

        data = resp.json()
        jobs = []
        for item in data:
            if not isinstance(item, dict) or "id" not in item:
                continue

            title = item.get("position", "Untitled")
            if is_senior(title):
                continue

            description = item.get("description", "")

            if not is_junior_devops(title, description):
                continue

            location = item.get("location") or "Remote"
            allowed, reason = is_location_allowed(location, description)
            if not allowed:
                continue

            jobs.append(
                normalize_job(
                    company=item.get("company", "Unknown"),
                    title=title,
                    location=location,
                    url=item.get("url", ""),
                    source="remoteok",
                    posted_date=item.get("date"),
                    description=description,
                )
            )
        return jobs
    except Exception as e:
        logger.error("remoteok_fetch_failed", extra={"error": str(e)})
        return []