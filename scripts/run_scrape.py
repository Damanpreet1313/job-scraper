"""
Run the full scrape -> dedupe -> match -> store pipeline.

Usage:
    python scripts/run_scrape.py
    python scripts/run_scrape.py --source remoteok,weworkremotely,remotive,jobicy

Sources are fetched concurrently to cut wall-clock time, then deduped,
scored against resume.txt, and stored.
"""
import argparse
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import (
    ASHBY_BOARDS,
    GREENHOUSE_BOARDS,
    LEVER_BOARDS,
    GROQ_API_KEY,
    GROQ_MODEL,
    MATCH_RETENTION_DAYS,
    MATCH_THRESHOLD,
)
from app.database import SessionLocal, init_db
from app.llm_matcher import score_jobs
from app.matcher import load_resume_text
from app.models import Job
from app.scrapers import (
    adzuna,
    arbeitnow,
    ashby,
    greenhouse,
    jobicy,
    lever,
    remoteok,
    remotive,
    weworkremotely,
)

# source -> (list of board slugs, fetch callable)
SOURCE_SCRAPERS = {
    "greenhouse": (GREENHOUSE_BOARDS, greenhouse.fetch_jobs),
    "lever": (LEVER_BOARDS, lever.fetch_jobs),
    "ashby": (ASHBY_BOARDS, ashby.fetch_jobs),
    "remoteok": ([None], remoteok.fetch_jobs),
    "weworkremotely": ([None], weworkremotely.fetch_jobs),
    "remotive": ([None], remotive.fetch_jobs),
    "jobicy": ([None], jobicy.fetch_jobs),
    "arbeitnow": ([None], arbeitnow.fetch_jobs),
    "adzuna": ([None], adzuna.fetch_jobs),
}


def fetch_one(source: str, slug: str | None, fetcher) -> list[dict]:
    """Fetch one board (or one global source when slug is None)."""
    label = f"{source}/{slug}" if slug else source
    try:
        fetched = fetcher(slug) if slug else fetcher()
        print(f"  {label}: {len(fetched)} jobs")
        return fetched
    except Exception as e:
        print(f"  {label} failed: {e}")
        return []


def collect_all_jobs(sources: list[str], max_workers: int = 8) -> list[dict]:
    jobs = []
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = []
        for source in sources:
            slugs, fetcher = SOURCE_SCRAPERS[source]
            for slug in slugs:
                futures.append(pool.submit(fetch_one, source, slug, fetcher))
        for future in as_completed(futures):
            jobs.extend(future.result())
    return jobs


def purge_old_jobs() -> int:
    """Deletes jobs older than MATCH_RETENTION_DAYS. A posting that's still
    live gets re-scraped and re-inserted with a fresh timestamp on the next
    run, so this only drops listings that have actually aged out — nothing
    still-relevant silently disappears for good."""
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


def main():
    parser = argparse.ArgumentParser(description="Scrape, dedupe, score, and store DevOps/Cloud jobs.")
    parser.add_argument(
        "--source",
        help="Comma-separated sources to scrape (default: all). "
        f"Options: {', '.join(SOURCE_SCRAPERS)}",
    )
    parser.add_argument("--workers", type=int, default=8, help="Max concurrent fetches (default: 8)")
    args = parser.parse_args()

    sources = [s.strip() for s in args.source.split(",")] if args.source else list(SOURCE_SCRAPERS)
    unknown = [s for s in sources if s not in SOURCE_SCRAPERS]
    if unknown:
        parser.error(f"Unknown source(s): {', '.join(unknown)}")

    init_db()

    purged = purge_old_jobs()
    print(f"Purged {purged} jobs older than {MATCH_RETENTION_DAYS} days.")

    if GROQ_API_KEY:
        print(f"Matcher: Groq ({GROQ_MODEL}) + TF-IDF prefilter")
    else:
        print("Matcher: TF-IDF only (no GROQ_API_KEY set)")

    print("Scraping sources...")
    jobs = collect_all_jobs(sources, max_workers=args.workers)
    print(f"Total raw postings fetched: {len(jobs)}")

    resume_text = load_resume_text()
    if not resume_text.strip():
        print("Warning: resume.txt is empty/placeholder — match scores will be 0. "
              "Fill it in with your skills/resume text for real matching.")

    print("Scoring against resume.txt...")
    jobs = score_jobs(jobs, resume_text)

    print("Storing (deduped)...")
    inserted, skipped = store_jobs(jobs)
    matched = sum(1 for j in jobs if j.get("match_score", 0) >= MATCH_THRESHOLD)

    print(f"\nDone. Inserted {inserted} new jobs, skipped {skipped} duplicates.")
    print(f"{matched} of this run's postings scored above the match threshold ({MATCH_THRESHOLD}).")


if __name__ == "__main__":
    main()
