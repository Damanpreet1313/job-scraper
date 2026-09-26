"""Indeed job scraper via RSS feeds."""
import asyncio
import feedparser
from app.logging_config import get_logger
from app.scrapers.base import normalize_job
from app.scrapers.keywords import is_senior, is_devops_role, JUNIOR_PATTERNS
from app.scrapers.locations import is_location_allowed

logger = get_logger(__name__)

INDEED_FEEDS = [
    "https://rss.indeed.com/rss?q=junior+devops+remote&l=remote&radius=50&sort=date",
    "https://rss.indeed.com/rss?q=entry+level+devops+remote&l=remote&radius=50&sort=date",
    "https://rss.indeed.com/rss?q=devops+intern+remote&l=remote&radius=50&sort=date",
    "https://rss.indeed.com/rss?q=junior+cloud+engineer+remote&l=remote&radius=50&sort=date",
    "https://rss.indeed.com/rss?q=site+reliability+engineer+intern+remote&l=remote&radius=50&sort=date",
    "https://rss.indeed.com/rss?q=platform+engineer+junior+remote&l=remote&radius=50&sort=date",
    "https://rss.indeed.com/rss?q=junior+devops&l=noida&radius=50&sort=date",
    "https://rss.indeed.com/rss?q=devops+intern&l=gurugram&radius=50&sort=date",
    "https://rss.indeed.com/rss?q=entry+level+cloud&l=delhi&radius=50&sort=date",
    "https://rss.indeed.com/rss?q=junior+devops+remote&l=united+states&radius=50&sort=date",
    "https://rss.indeed.com/rss?q=junior+devops+remote&l=canada&radius=50&sort=date",
    "https://rss.indeed.com/rss?q=junior+devops+remote&l=united+kingdom&radius=50&sort=date",
    "https://rss.indeed.com/rss?q=junior+devops+remote&l=germany&radius=50&sort=date",
    "https://rss.indeed.com/rss?q=junior+devops+remote&l=singapore&radius=50&sort=date",
    "https://rss.indeed.com/rss?q=junior+devops+remote&l=australia&radius=50&sort=date",
]


async def _fetch_feed(feed_url: str) -> list:
    """Fetch and parse a single RSS feed in executor."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, feedparser.parse, feed_url)


async def fetch_jobs(timeout: int = 15) -> list[dict]:
    """Indeed RSS feeds for junior DevOps/Cloud roles globally."""
    jobs = []
    for feed_url in INDEED_FEEDS:
        try:
            feed = await _fetch_feed(feed_url)
        except Exception as e:
            logger.error("indeed_feed_error", extra={"url": feed_url, "error": str(e)})
            continue

        for entry in feed.entries:
            title = entry.get("title", "Untitled")
            if is_senior(title):
                continue

            description = entry.get("summary", "")
            company = entry.get("company", "Unknown")
            location = entry.get("location", "Remote")

            if not is_devops_role(title):
                continue

            haystack = f"{title} {description}"
            has_junior = any(p.search(haystack) for p in JUNIOR_PATTERNS)
            if not has_junior:
                continue

            allowed, reason = is_location_allowed(location, description)
            if not allowed:
                continue

            jobs.append(
                normalize_job(
                    company=company,
                    title=title,
                    location=location,
                    url=entry.get("link", ""),
                    source="indeed",
                    posted_date=entry.get("published"),
                    description=description,
                )
            )
    return jobs