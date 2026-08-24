"""Wellfound (AngelList) job scraper via RSS feed."""
import feedparser

from app.scrapers.base import normalize_job
from app.scrapers.keywords import is_senior, is_devops_role, JUNIOR_PATTERNS
from app.scrapers.locations import is_location_allowed

# Wellfound RSS for DevOps/Cloud roles
WELLFOUND_FEEDS = [
    "https://wellfound.com/role/rss/devops-engineer",
    "https://wellfound.com/role/rss/cloud-engineer",
    "https://wellfound.com/role/rss/site-reliability-engineer",
    "https://wellfound.com/role/rss/platform-engineer",
    "https://wellfound.com/role/rss/infrastructure-engineer",
]


def fetch_jobs(timeout: int = 15) -> list[dict]:
    """Wellfound RSS feeds for startup DevOps/Cloud roles."""
    jobs = []
    for feed_url in WELLFOUND_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
        except Exception:
            continue

        for entry in feed.entries:
            title = entry.get("title", "Untitled")
            if is_senior(title):
                continue

            description = entry.get("summary", "")

            # Wellfound titles: "Company — Job Title"
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