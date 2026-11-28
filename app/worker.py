"""Background worker to consume scrape jobs from Redis queue."""
import asyncio
import json
import sys
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
from app.database import SessionLocal, init_db, get_db
from app.job_queue import dequeue_scrape, update_scrape_status
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
from app.scrapers.http_client import close_http_client

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
    label = f"{source}/{slug}" if slug else source
    try:
        fetched = await fetcher(slug) if slug else await fetcher()
        logger.info("fetch_complete", extra={"source": label, "count": len(fetched)})
        return fetched
    except Exception as e:
        logger.error("fetch_failed", extra={"source": label, "error": str(e), "error_type": type(e).__name__})
        return []


async def collect_all_jobs(sources: list[str], max_workers: int = 8, timeout_seconds: int = 300) -> list[dict]:
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

    try:
        results = await asyncio.wait_for(
            asyncio.gather(*tasks, return_exceptions=True),
            timeout=timeout_seconds,
        )
    except asyncio.TimeoutError:
        logger.error("scrape_timeout", extra={"timeout_seconds": timeout_seconds})
        return jobs

    for result in results:
        if isinstance(result, Exception):
            logger.error("task_failed", extra={"error": str(result)})
        else:
            jobs.extend(result)

    await close_http_client()
    return jobs


def purge_old_jobs() -> int:
    from datetime import datetime, timedelta
    cutoff = datetime.utcnow() - timedelta(days=MATCH_RETENTION_DAYS)
    with get_db() as db:
        deleted = db.query(Job).filter(
            Job.posted_date_parsed.isnot(None),
            Job.posted_date_parsed < cutoff
        ).delete()
    return deleted


def store_jobs(jobs: list[dict]) -> tuple[int, int]:
    inserted, skipped = 0, 0
    with get_db() as db:
        existing_content_hashes = {row[0] for row in db.query(Job.content_hash).all()}
        existing_cross_source_hashes = {row[0] for row in db.query(Job.cross_source_hash).all() if row[0]}
        for job in jobs:
            if job["content_hash"] in existing_content_hashes:
                skipped += 1
                continue
            cross_hash = job.get("cross_source_hash")
            if cross_hash and cross_hash in existing_cross_source_hashes:
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
                    cross_source_hash=cross_hash,
                    match_score=job.get("match_score", 0.0),
                    match_reason=job.get("match_reason"),
                    matched=job.get("match_score", 0.0) >= MATCH_THRESHOLD,
                )
            )
            existing_content_hashes.add(job["content_hash"])
            if cross_hash:
                existing_cross_source_hashes.add(cross_hash)
            inserted += 1
    return inserted, skipped


async def run_scrape_job(sources: list[str] | None = None) -> dict:
    """Execute a full scrape job. Returns summary dict."""
    if sources is None:
        sources = list(SOURCE_SCRAPERS)
    
    unknown = [s for s in sources if s not in SOURCE_SCRAPERS]
    if unknown:
        return {"error": f"Unknown source(s): {', '.join(unknown)}"}

    init_db()
    purged = purge_old_jobs()
    logger.info("purged_old_jobs", extra={"count": purged, "retention_days": MATCH_RETENTION_DAYS})

    if GROQ_API_KEY:
        logger.info("matcher_config", extra={"mode": "groq", "model": GROQ_MODEL})
    else:
        logger.info("matcher_config", extra={"mode": "semantic+tfidf"})

    logger.info("scraping_started", extra={"sources": sources, "max_workers": 8})
    jobs = await collect_all_jobs(sources, max_workers=8, timeout_seconds=300)
    logger.info("scraping_completed", extra={"total_raw_postings": len(jobs)})

    resume_text = load_resume_text()
    if not resume_text.strip():
        logger.warning("resume_empty", extra={"message": "resume.txt is empty — match scores will be 0"})

    logger.info("scoring_started", extra={"use_semantic": True})
    jobs = score_jobs(jobs, resume_text, use_semantic=True)

    logger.info("storing_started")
    inserted, skipped = store_jobs(jobs)
    matched = sum(1 for j in jobs if j.get("match_score", 0) >= MATCH_THRESHOLD)

    summary = {
        "inserted": inserted,
        "skipped": skipped,
        "matched_above_threshold": matched,
        "threshold": MATCH_THRESHOLD,
    }
    logger.info("scrape_completed", extra=summary)
    return summary


async def worker_loop():
    """Main worker loop: wait for jobs, execute them."""
    logger.info("worker_started", extra={"queue": "job_scraper:scrape_queue"})
    while True:
        try:
            job = dequeue_scrape()
            if job:
                sources = job.get("sources")
                update_scrape_status("running", sources=json.dumps(sources) if sources else "all")
                try:
                    result = await run_scrape_job(sources)
                    update_scrape_status("completed", **result)
                except Exception as e:
                    logger.error("worker_job_failed", extra={"error": str(e)})
                    update_scrape_status("failed", error=str(e))
        except Exception as e:
            logger.error("worker_loop_error", extra={"error": str(e)})
            await asyncio.sleep(5)


async def start_worker():
    """Start the background worker task."""
    setup_logging(level="INFO", json_format=False)
    return asyncio.create_task(worker_loop())