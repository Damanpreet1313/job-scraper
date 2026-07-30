"""
Run the full scrape -> dedupe -> match -> store pipeline.

Usage:
    python scripts/run_scrape.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import GREENHOUSE_BOARDS, LEVER_BOARDS, ASHBY_BOARDS, MATCH_THRESHOLD
from app.database import SessionLocal, init_db
from app.models import Job
from app.matcher import score_jobs, load_resume_text
from app.scrapers import greenhouse, lever, ashby, remoteok, weworkremotely


def collect_all_jobs() -> list[dict]:
    jobs = []

    for slug in GREENHOUSE_BOARDS:
        try:
            fetched = greenhouse.fetch_jobs(slug)
            print(f"  greenhouse/{slug}: {len(fetched)} jobs")
            jobs.extend(fetched)
        except Exception as e:
            print(f"  greenhouse/{slug} failed: {e}")

    for slug in LEVER_BOARDS:
        try:
            fetched = lever.fetch_jobs(slug)
            print(f"  lever/{slug}: {len(fetched)} jobs")
            jobs.extend(fetched)
        except Exception as e:
            print(f"  lever/{slug} failed: {e}")

    for slug in ASHBY_BOARDS:
        try:
            fetched = ashby.fetch_jobs(slug)
            print(f"  ashby/{slug}: {len(fetched)} jobs")
            jobs.extend(fetched)
        except Exception as e:
            print(f"  ashby/{slug} failed: {e}")

    try:
        fetched = remoteok.fetch_jobs()
        print(f"  remoteok: {len(fetched)} jobs")
        jobs.extend(fetched)
    except Exception as e:
        print(f"  remoteok failed: {e}")

    try:
        fetched = weworkremotely.fetch_jobs()
        print(f"  weworkremotely: {len(fetched)} jobs")
        jobs.extend(fetched)
    except Exception as e:
        print(f"  weworkremotely failed: {e}")

    return jobs


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
    init_db()

    print("Scraping sources...")
    jobs = collect_all_jobs()
    print(f"Total raw postings fetched: {len(jobs)}")

    if not load_resume_text().strip():
        print("Warning: resume.txt is empty/placeholder — match scores will be 0. "
              "Fill it in with your skills/resume text for real matching.")

    print("Scoring against resume.txt...")
    jobs = score_jobs(jobs)

    print("Storing (deduped)...")
    inserted, skipped = store_jobs(jobs)
    matched = sum(1 for j in jobs if j.get("match_score", 0) >= MATCH_THRESHOLD)

    print(f"\nDone. Inserted {inserted} new jobs, skipped {skipped} duplicates.")
    print(f"{matched} of this run's postings scored above the match threshold ({MATCH_THRESHOLD}).")


if __name__ == "__main__":
    main()
