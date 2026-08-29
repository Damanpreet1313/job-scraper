"""
Run the full scrape -> dedupe -> match -> store pipeline.

Usage:
    python scripts/run_scrape.py
    python scripts/run_scrape.py --source remoteok,weworkremotely,remotive,jobicy

Sources are fetched concurrently to cut wall-clock time, then deduped,
scored against resume.txt, and stored.
"""
import argparse
import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import (
    ASHBY_BOARDS,
    GREENHOUSE_BOARDS,
    LEVER_BOARDS,
    STARTUP_ASHBY_BOARDS,
    STARTUP_GREENHOUSE_BOARDS,
    STARTUP_LEVER_BOARDS,
    GROQ_API_KEY,
    GROQ_MODEL,
    MATCH_RETENTION_DAYS,
    MATCH_THRESHOLD,
)
from app.database import SessionLocal, init_db
from app.llm_matcher import score_jobs
from app.logging_config import setup_logging, get_logger
from app.matcher import load_resume_text
from app.models import Job
from app.scrapers.adzuna import fetch_jobs as adzuna_fetch
from app.scrapers.arbeitnow import fetch_jobs as arbeitnow_fetch
from app.scrapers.ashby import fetch_jobs as ashby_fetch
from app.scrapers.career_pages import fetch_jobs as career_pages_fetch
from app.scrapers.greenhouse import fetch_jobs as greenhouse_fetch
from app.scrapers.himalayas import fetch_jobs as himalayas_fetch
from app.scrapers.indeed import fetch_jobs as indeed_fetch
from app.scrapers.jobicy import fetch_jobs as jobicy_fetch
from app.scrapers.lever import fetch_jobs as lever_fetch
from app.scrapers.levels_fyi import fetch_jobs as levels_fyi_fetch
from app.scrapers.linkedin import fetch_jobs as linkedin_fetch
from app.scrapers.otta import fetch_jobs as ota_fetch
from app.scrapers.remoteok import fetch_jobs as remoteok_fetch
from app.scrapers.remoteco import fetch_jobs as remoteco_fetch
from app.scrapers.remotive import fetch_jobs as remotive_fetch
from app.scrapers.weworkremotely import fetch_jobs as weworkremotely_fetch
from app.scrapers.wellfound import fetch_jobs as wellfound_fetch
from app.scrapers.ycombinator import fetch_jobs as ycombinator_fetch

# source -> (list of board slugs, fetch callable)
SOURCE_SCRAPERS = {
    "greenhouse": (GREENHOUSE_BOARDS, greenhouse_fetch),
    "lever": (LEVER_BOARDS, lever_fetch),
    "ashby": (ASHBY_BOARDS, ashby_fetch),
    "startup_greenhouse": (STARTUP_GREENHOUSE_BOARDS, greenhouse_fetch),
    "startup_lever": (STARTUP_LEVER_BOARDS, lever_fetch),
    "startup_ashby": (STARTUP_ASHBY_BOARDS, ashby_fetch),
    "remoteok": ([None], remoteok_fetch),
    "weworkremotely": ([None], weworkremotely_fetch),
    "remotive": ([None], remotive_fetch),
    "jobicy": ([None], jobicy_fetch),
    "arbeitnow": ([None], arbeitnow_fetch),
    "adzuna": ([None], adzuna_fetch),
    "ycombinator": ([None], ycombinator_fetch),
    "remoteco": ([None], remoteco_fetch),
    "himalayas": ([None], himalayas_fetch),
    "wellfound": ([None], wellfound_fetch),
    "otta": ([None], ota_fetch),
    "levels_fyi": ([None], levels_fyi_fetch),
    "indeed": ([None], indeed_fetch),
    "career_pages": ([None], career_pages_fetch),
}


logger = get_logger(__name__)


async def fetch_one(source: str, slug: str | None, fetcher) -> list[dict]:
    """Fetch one board (or one global source when slug is None)."""
    label = f"{source}/{slug}" if slug else source
    try:
        fetched = await fetcher(slug) if slug else await fetcher()
        logger.info("fetch_complete", extra={"source": label, "count": len(fetched)})
        return fetched
    except Exception as e:
        logger.error("fetch_failed", extra={"source": label, "error": str(e), "error_type": type(e).__name__})
        return []


async def collect_all_jobs(sources: list[str], max_workers: int = 8) -> list[dict]:
    """Fetch all jobs concurrently with semaphore for concurrency control."""
    semaphore = asyncio.Semaphore(max_workers)

    async def fetch_with_semaphore(source: str, slug: str | None, fetcher):
        async with semaphore:
            return await fetch_one(source, slug, fetcher)

    jobs = []
    tasks = []
    for source in sources:
        slugs, fetcher = SOURCE_SCRAPERS[source]
        for slug in slugs:
            tasks.append(fetch_with_semaphore(source, slug, fetcher))

    results = await asyncio.gather(*tasks, return_exceptions=True)
    for result in results:
        if isinstance(result, Exception):
            logger.error("task_failed", extra={"error": str(result)})
        else:
            jobs.extend(result)
    return jobs


def purge_old_jobs() -> int:
    """Deletes jobs older than MATCH_RETENTION_DAYS."""
    cutoff = datetime.utcnow() - timedelta(days=MATCH_RETENTION_DAYS)
    db = SessionLocal()
    try:
        deleted = db.query(Job).filter(Job.created_at < cutoff).delete()
        db.commit()
        return deleted
    finally:
        db.close()


def store_jobs(jobs: list[dict]) -> tuple[int, int]:
    db = SessionLocal()
    inserted, skipped = 0, 0
    try:
        existing_hashes = {row[0] for row in db.query(Job.content_hash).all()}
        for job in jobs:
            if job["content_hash"] in existing_hashes:
                skipped += 1
                continue
            db.add(
                Job(
                    company=job["company"],
                    title=job["title"],
                    location=job.get("location"),
                    url=job["url"],
                    source=job["source"],
                    posted_date=job.get("posted_date"),
                    posted_date_parsed=job.get("posted_date_parsed"),
                    description=job.get("description"),
                    content_hash=job["content_hash"],
                    match_score=job.get("match_score", 0.0),
                    match_reason=job.get("match_reason"),
                    matched=job.get("match_score", 0.0) >= MATCH_THRESHOLD,
                )
            )
            existing_hashes.add(job["content_hash"])
            inserted += 1
        db.commit()
    finally:
        db.close()
    return inserted, skipped


async def main_async():
    parser = argparse.ArgumentParser(description="Scrape, dedupe, score, and store DevOps/Cloud jobs.")
    parser.add_argument(
        "--source",
        help="Comma-separated sources to scrape (default: all). "
        f"Options: {', '.join(SOURCE_SCRAPERS)}",
    )
    parser.add_argument("--workers", type=int, default=8, help="Max concurrent fetches (default: 8)")
    parser.add_argument("--no-semantic", action="store_true", help="Disable semantic embeddings (use TF-IDF only)")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    parser.add_argument("--json-logs", action="store_true", help="Output logs as JSON")
    args = parser.parse_args()

    setup_logging(level=args.log_level, json_format=args.json_logs)

    sources = [s.strip() for s in args.source.split(",")] if args.source else list(SOURCE_SCRAPERS)
    unknown = [s for s in sources if s not in SOURCE_SCRAPERS]
    if unknown:
        parser.error(f"Unknown source(s): {', '.join(unknown)}")

    init_db()

    purged = purge_old_jobs()
    logger.info("purged_old_jobs", extra={"count": purged, "retention_days": MATCH_RETENTION_DAYS})

    if GROQ_API_KEY:
        logger.info("matcher_config", extra={"mode": "groq", "model": GROQ_MODEL})
    else:
        logger.info("matcher_config", extra={"mode": "semantic+tfidf"})

    logger.info("scraping_started", extra={"sources": sources, "max_workers": args.workers})
    jobs = await collect_all_jobs(sources, max_workers=args.workers)
    logger.info("scraping_completed", extra={"total_raw_postings": len(jobs)})

    resume_text = load_resume_text()
    if not resume_text.strip():
        logger.warning("resume_empty", extra={"message": "resume.txt is empty — match scores will be 0"})

    logger.info("scoring_started", extra={"use_semantic": not args.no_semantic})
    jobs = score_jobs(jobs, resume_text, use_semantic=not args.no_semantic)

    logger.info("storing_started")
    inserted, skipped = store_jobs(jobs)
    matched = sum(1 for j in jobs if j.get("match_score", 0) >= MATCH_THRESHOLD)

    logger.info(
        "scrape_completed",
        extra={
            "inserted": inserted,
            "skipped": skipped,
            "matched_above_threshold": matched,
            "threshold": MATCH_THRESHOLD,
        },
    )


def main():
    asyncio.run(main_async())


if __name__ == "__main__":
    main()