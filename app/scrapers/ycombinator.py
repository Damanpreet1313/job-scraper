"""Y Combinator job scraper via RSS feed."""
import asyncio
import feedparser
from app.logging_config import get_logger
from app.scrapers.base import normalize_job
from app.scrapers.keywords import is_senior, is_junior_devops
from app.scrapers.locations import is_location_allowed

logger = get_logger(__name__)

YC_FEED_URL = "https://www.ycombinator.com/jobs/rss"


async def _fetch_feed(feed_url: str) -> list:
    """Fetch and parse a single RSS feed in executor."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, feedparser.parse, feed_url)


async def fetch_jobs(timeout: int = 15) -> list[dict]:
    """Y Combinator job board RSS feed - startup roles including DevOps/Cloud."""
    try:
        feed = await _fetch_feed(YC_FEED_URL)
    except Exception as e:
        logger.error("ycombinator_feed_error", extra={"error": str(e)})
        return []

    jobs = []
    for entry in feed.entries:
        title = entry.get("title", "Untitled")
        if is_senior(title):
            continue

        description = entry.get("summary", "")
        if not is_junior_devops(title, description):
            continue

        company = "Unknown"
        job_title = title
        if ":" in title:
            parts = title.split(":", 1)
            company = parts[0].strip()
            job_title = parts[1].strip()

        location = "Remote / SF Bay Area"
        allowed, reason = is_location_allowed(location, description)
        if not allowed:
            continue

        jobs.append(
            normalize_job(
                company=company,
                title=job_title,
                location=location,
                url=entry.get("link", ""),
                source="ycombinator",
                posted_date=entry.get("published"),
                description=description,
            )
        )
    return jobs