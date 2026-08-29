"""Wellfound (AngelList) job scraper via RSS feed."""
import asyncio
import feedparser
from app.logging_config import get_logger
from app.scrapers.base import normalize_job
from app.scrapers.keywords import is_senior, is_devops_role, JUNIOR_PATTERNS
from app.scrapers.locations import is_location_allowed

logger = get_logger(__name__)

WELLFOUND_FEEDS = [
    "https://wellfound.com/role/rss/devops-engineer",
    "https://wellfound.com/role/rss/cloud-engineer",
    "https://wellfound.com/role/rss/site-reliability-engineer",
    "https://wellfound.com/role/rss/platform-engineer",
    "https://wellfound.com/role/rss/infrastructure-engineer",
]


async def _fetch_feed(feed_url: str) -> list:
    """Fetch and parse a single RSS feed in executor."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, feedparser.parse, feed_url)


async def fetch_jobs(timeout: int = 15) -> list[dict]:
    """Wellfound RSS feeds for startup DevOps/Cloud roles."""
    jobs = []
    for feed_url in WELLFOUND_FEEDS:
        try:
            feed = await _fetch_feed(feed_url)
        except Exception as e:
            logger.error("wellfound_feed_error", extra={"url": feed_url, "error": str(e)})
            continue

        for entry in feed.entries:
            title = entry.get("title", "Untitled")
            if is_senior(title):
                continue

            description = entry.get("summary", "")

            company = "Unknown"
            job_title = title
            if "—" in title:
                parts = title.split("—", 1)
                company = parts[0].strip()
                job_title = parts[1].strip()
            elif " - " in title:
                parts = title.split(" - ", 1)
                company = parts[0].strip()
                job_title = parts[1].strip()

            if not is_devops_role(job_title):
                continue

            haystack = f"{job_title} {description}"
            has_junior = any(p.search(haystack) for p in JUNIOR_PATTERNS)
            if not has_junior:
                continue

            location = entry.get("location", "Remote")
            allowed, reason = is_location_allowed(location, description)
            if not allowed:
                continue

            jobs.append(
                normalize_job(
                    company=company,
                    title=job_title,
                    location=location,
                    url=entry.get("link", ""),
                    source="wellfound",
                    posted_date=entry.get("published"),
                    description=description,
                )
            )
    return jobs