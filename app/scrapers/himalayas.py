"""Himalayas job scraper."""
from app.logging_config import get_logger
from app.scrapers.base import normalize_job
from app.scrapers.http_client import get_http_client
from app.scrapers.keywords import is_senior, is_junior_devops
from app.scrapers.locations import is_location_allowed

logger = get_logger(__name__)

HIMALAYAS_URL = "https://himalayas.app/jobs/api"


async def fetch_jobs(timeout: int = 15, max_pages: int = 5) -> list[dict]:
    """Himalayas.app public job API - returns remote jobs across categories."""
    client = await get_http_client()
    jobs = []
    for page in range(1, max_pages + 1):
        try:
            resp = await client.get(HIMALAYAS_URL, params={"page": page, "per_page": 50}, timeout=timeout)
            if resp.status_code != 200:
                logger.warning("himalayas_non_200", extra={"page": page, "status": resp.status_code})
                break

            data = resp.json()
            for item in data.get("jobs", []):
                title = item.get("title", "Untitled")
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
                        company=item.get("company_name", "Unknown"),
                        title=title,
                        location=location,
                        url=item.get("url", ""),
                        source="himalayas",
                        posted_date=item.get("published_at"),
                        description=description,
                    )
                )

            if not data.get("jobs"):
                break
        except Exception as e:
            logger.error("himalayas_fetch_error", extra={"page": page, "error": str(e)})
            break
    return jobs