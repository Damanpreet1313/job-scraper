import feedparser

from app.scrapers.base import normalize_job

FEED_URL = "https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss"


def fetch_jobs(timeout: int = 15) -> list[dict]:
    """WWR publishes a per-category RSS feed, so this one is already
    scoped to DevOps/SysAdmin — no keyword filtering needed."""
    feed = feedparser.parse(FEED_URL)

    jobs = []
    for entry in feed.entries:
        title = entry.get("title", "Untitled")
        # WWR titles are usually "Company: Job Title"
        company = title.split(":")[0].strip() if ":" in title else "Unknown"
        job_title = title.split(":", 1)[1].strip() if ":" in title else title

        jobs.append(
            normalize_job(
                company=company,
                title=job_title,
                location="Remote",
                url=entry.get("link", ""),
                source="weworkremotely",
                posted_date=entry.get("published"),
                description=entry.get("summary", ""),
            )
        )
    return jobs
