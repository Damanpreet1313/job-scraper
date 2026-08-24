import feedparser

from app.scrapers.base import normalize_job
from app.scrapers.keywords import is_senior, is_devops_role, JUNIOR_PATTERNS
from app.scrapers.locations import is_location_allowed

FEED_URL = "https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss"


def fetch_jobs(timeout: int = 15) -> list[dict]:
    """WWR publishes a per-category RSS feed, so this one is already
    scoped to DevOps/SysAdmin — filter for junior roles only."""
    feed = feedparser.parse(FEED_URL)

    jobs = []
    for entry in feed.entries:
        title = entry.get("title", "Untitled")
        if is_senior(title):
            continue

        description = entry.get("summary", "")
        # WWR titles are usually "Company: Job Title"
        company = title.split(":")[0].strip() if ":" in title else "Unknown"
        job_title = title.split(":", 1)[1].strip() if ":" in title else title

        # Feed is already DevOps-scoped, so check title for devops + junior
        # Check description only for junior keywords to avoid false positives
        # from career-path mentions in descriptions
        
        if not is_devops_role(job_title):
            continue
        
        # Check for junior keywords in title + description
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
