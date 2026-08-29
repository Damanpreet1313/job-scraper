"""Remotive job scraper."""
from app.logging_config import get_logger
from app.scrapers.base import normalize_job
from app.scrapers.http_client import get_http_client
from app.scrapers.keywords import is_senior, is_junior_devops
from app.scrapers.locations import is_location_allowed

logger = get_logger(__name__)

URL = "https://remotive.com/api/remote-jobs"


async def fetch_jobs(timeout: int = 15, max_pages: int = 5) -> list[dict]:
    """Remotive's public job API returns every remote category."""
    client = await get_http_client()
    jobs = []
    url = URL
    for page in range(max_pages):
        try:
            resp = await client.get(url, timeout=timeout)
            if resp.status_code != 200:
                logger.warning("remotive_non_200", extra={"page": page, "status": resp.status_code})
                break

            data = resp.json()
            for item in data.get("jobs", []):
                title = item.get("title", "Untitled")
                if is_senior(title):
                    continue

                description = item.get("description", "")
                if not is_junior_devops(title, description):
                    continue

                location = item.get("candidate_required_location") or "Remote"
                allowed, reason = is_location_allowed(location, description)
                if not allowed:
                    continue

                jobs.append(
                    normalize_job(
                        company=item.get("company_name", "Unknown"),
                        title=title,
                        location=location,
                        url=item.get("url", ""),
                        source="remotive",
                        posted_date=item.get("publication_date"),
                        description=description,
                    )
                )

            next_url = data.get("next_url")
            if not next_url:
                break
            url = next_url
    return jobs