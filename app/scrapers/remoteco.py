"""Remote.co job scraper via RSS feed."""
import asyncio
import feedparser
from app.logging_config import get_logger
from app.scrapers.base import normalize_job
from app.scrapers.keywords import is_senior, is_junior_devops
from app.scrapers.locations import is_location_allowed

logger = get_logger(__name__)

REMOTE_CO_FEED_URL = "https://remote.co/remote-jobs/devops/feed/"


async def _fetch_feed(feed_url: str) -> list:
    """Fetch and parse a single RSS feed in executor."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, feedparser.parse, feed_url)


async def fetch_jobs(timeout: int = 15) -> list[dict]:
    """Remote.co DevOps category RSS feed - already scoped to DevOps."""
    try:
        feed = await _fetch_feed(REMOTE_CO_FEED_URL)
    except Exception as e:
        logger.error("remoteco_feed_error", extra={"error": str(e)})
        return []

    jobs = []
    for entry in feed.entries:
        title = entry.get("title", "Untitled")
        if is_senior(title):
            continue

        description = entry.get("summary", "")
        if not is_junior_devops(title, description):
            continue

        location = "Remote"
        allowed, reason = is_location_allowed(location, description)
        if not allowed:
            continue

        jobs.append(
            normalize_job(
                company="Unknown",
                title=title,
                location=location,
                url=entry.get("link", ""),
                source="remoteco",
                posted_date=entry.get("published"),
                description=description,
            )
        )
    return jobs