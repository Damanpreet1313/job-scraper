"""Indeed job scraper via RSS feeds."""
import feedparser

from app.scrapers.base import normalize_job
from app.scrapers.keywords import is_senior, is_devops_role, JUNIOR_PATTERNS
from app.scrapers.locations import is_location_allowed

# Indeed RSS feeds for DevOps/Cloud junior roles
# Format: https://rss.indeed.com/rss?q=QUERY&l=LOCATION&radius=50&sort=date
INDEED_FEEDS = [
    # Global remote
    "https://rss.indeed.com/rss?q=junior+devops+remote&l=remote&radius=50&sort=date",
    "https://rss.indeed.com/rss?q=entry+level+devops+remote&l=remote&radius=50&sort=date",
    "https://rss.indeed.com/rss?q=devops+intern+remote&l=remote&radius=50&sort=date",
    "https://rss.indeed.com/rss?q=junior+cloud+engineer+remote&l=remote&radius=50&sort=date",
    "https://rss.indeed.com/rss?q=site+reliability+engineer+intern+remote&l=remote&radius=50&sort=date",
    "https://rss.indeed.com/rss?q=platform+engineer+junior+remote&l=remote&radius=50&sort=date",
    # India NCR
    "https://rss.indeed.com/rss?q=junior+devops&l=noida&radius=50&sort=date",
    "https://rss.indeed.com/rss?q=devops+intern&l=gurugram&radius=50&sort=date",
    "https://rss.indeed.com/rss?q=entry+level+cloud&l=delhi&radius=50&sort=date",
    # US remote
    "https://rss.indeed.com/rss?q=junior+devops+remote&l=united+states&radius=50&sort=date",
    # Canada remote
    "https://rss.indeed.com/rss?q=junior+devops+remote&l=canada&radius=50&sort=date",
    # UK remote
    "https://rss.indeed.com/rss?q=junior+devops+remote&l=united+kingdom&radius=50&sort=date",
    # Germany remote
    "https://rss.indeed.com/rss?q=junior+devops+remote&l=germany&radius=50&sort=date",
    # Singapore remote
    "https://rss.indeed.com/rss?q=junior+devops+remote&l=singapore&radius=50&sort=date",
    # Australia remote
    "https://rss.indeed.com/rss?q=junior+devops+remote&l=australia&radius=50&sort=date",
]


def fetch_jobs(timeout: int = 15) -> list[dict]:
    """Indeed RSS feeds for junior DevOps/Cloud roles globally."""
    jobs = []
    for feed_url in INDEED_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
        except Exception:
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