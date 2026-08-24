import feedparser

from app.scrapers.base import normalize_job
from app.scrapers.keywords import is_senior, is_junior_devops
from app.scrapers.locations import is_location_allowed

YC_FEED_URL = "https://www.ycombinator.com/jobs/rss"


def fetch_jobs(timeout: int = 15) -> list[dict]:
    """Y Combinator job board RSS feed - covers startup roles including DevOps/Cloud."""
    feed = feedparser.parse(YC_FEED_URL)

    jobs = []
    for entry in feed.entries:
        title = entry.get("title", "Untitled")
        if is_senior(title):
            continue

        description = entry.get("summary", "")
        if not is_junior_devops(title, description):
            continue

        # YC RSS format: "Company: Job Title"
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