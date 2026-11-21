"""WeWorkRemotely job scraper via RSS feed."""
import asyncio
import feedparser
from app.logging_config import get_logger
from app.scrapers.base import normalize_job
from app.scrapers.keywords import is_senior, is_devops_role, JUNIOR_PATTERNS
from app.scrapers.locations import is_location_allowed

logger = get_logger(__name__)

FEED_URL = "https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss"


async def _fetch_feed(feed_url: str) -> list:
    """Fetch and parse a single RSS feed in executor."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, feedparser.parse, feed_url)


async def fetch_jobs(timeout: int = 15) -> list[dict]:
    """WWR publishes a per-category RSS feed, scoped to DevOps/SysAdmin."""
    try:
        feed = await _fetch_feed(FEED_URL)
    except Exception as e:
        logger.error("weworkremotely_feed_error", extra={"error": str(e)})
        return []

    jobs = []
    for entry in feed.entries:
        title = entry.get("title", "Untitled")
        if is_senior(title):
            continue

        description = entry.get("summary", "")
        company = title.split(":")[0].strip() if ":" in title else "Unknown"
        job_title = title.split(":", 1)[1].strip() if ":" in title else title

        if not is_devops_role(job_title):
            continue

        haystack = f"{job_title} {description}"
        has_junior = any(p.search(haystack) for p in JUNIOR_PATTERNS)
        if not has_junior:
            continue

        location = "Remote"
        allowed, reason = is_location_allowed(location, description)
        if not allowed:
            continue

        jobs.append(
            normalize_job(
                company=company,
                title=job_title,
                location=location,
                url=entry.get("link", ""),
                source="weworkremotely",
                posted_date=entry.get("published"),
                description=description,
            )
        )
    return jobs