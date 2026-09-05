"""Levels.fyi job scraper via public API."""
from app.logging_config import get_logger
from app.scrapers.base import normalize_job
from app.scrapers.http_client import get_http_client
from app.scrapers.keywords import is_senior, is_devops_role, JUNIOR_PATTERNS
from app.scrapers.locations import is_location_allowed

logger = get_logger(__name__)

LEVELS_FYI_API = "https://www.levels.fyi/api/v2/jobs"


async def fetch_jobs(timeout: int = 15, max_pages: int = 3) -> list[dict]:
    """Levels.fyi API - big tech company jobs."""
    client = await get_http_client()
    jobs = []
    devops_categories = [
        "DevOps Engineer", "Cloud Engineer", "Site Reliability Engineer",
        "Platform Engineer", "Infrastructure Engineer", "Systems Engineer",
        "Production Engineer",
    ]

    for category in devops_categories:
        for page in range(1, max_pages + 1):
            params = {
                "category": category,
                "page": page,
                "limit": 50,
                "remote": "true",
            }

            try:
                resp = await client.get(LEVELS_FYI_API, params=params, timeout=timeout)
                if resp.status_code != 200:
                    logger.warning("levels_fyi_non_200", extra={"category": category, "page": page, "status": resp.status_code})
                    break
            except Exception as e:
                logger.error("levels_fyi_fetch_error", extra={"category": category, "page": page, "error": str(e)})
                break

            data = resp.json()
            items = data.get("jobs", [])
            if not items:
                break

            for item in items:
                title = item.get("title", "Untitled")
                if is_senior(title):
                    continue

                company = item.get("company", "Unknown")
                description = item.get("description", "")
                location = item.get("location", "Remote")
                level = item.get("level", "").lower()

                junior_levels = ["intern", "new grad", "entry", "junior", "level 1", "level 2", "l1", "l2", "e1", "e2", "e3"]
                if not any(jl in level for jl in junior_levels):
                    haystack = f"{title} {description}"
                    has_junior = any(p.search(haystack) for p in JUNIOR_PATTERNS)
                    if not has_junior:
                        continue

                if not is_devops_role(title):
                    continue

                allowed, reason = is_location_allowed(location, description)
                if not allowed:
                    continue

                jobs.append(
                    normalize_job(
                        company=company,
                        title=title,
                        location=location,
                        url=item.get("url", ""),
                        source="levels_fyi",
                        posted_date=item.get("posted_date"),
                        description=description,
                    )
                )
    return jobs