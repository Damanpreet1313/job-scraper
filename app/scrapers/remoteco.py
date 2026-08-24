import feedparser

from app.scrapers.base import normalize_job
from app.scrapers.keywords import is_senior, is_junior_devops
from app.scrapers.locations import is_location_allowed

REMOTE_CO_FEED_URL = "https://remote.co/remote-jobs/devops/feed/"


def fetch_jobs(timeout: int = 15) -> list[dict]:
    """Remote.co DevOps category RSS feed - already scoped to DevOps."""
    feed = feedparser.parse(REMOTE_CO_FEED_URL)

    jobs = []
    for entry in feed.entries:
        title = entry.get("title", "Untitled")
        if is_senior(title):
            continue

        description = entry.get("summary", "")
        # Remote.co DevOps feed is already filtered, but double-check for junior
        if not is_junior_devops(title, description):
            continue

        location = "Remote"
        allowed, reason = is_location_allowed(location, description)
        if not allowed:
            continue

        jobs.append(
            normalize_job(
                company="Unknown",  # Remote.co RSS doesn't include company in title
                title=title,
                location=location,
                url=entry.get("link", ""),
                source="remoteco",
                posted_date=entry.get("published"),
                description=description,
            )
        )
    return jobs