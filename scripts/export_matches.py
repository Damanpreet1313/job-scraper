"""
Writes every matched job (score >= MATCH_THRESHOLD) out to matches.txt,
sorted highest-score first. Overwrites the file each run so it always
reflects the current full set of matches — open it directly on GitHub,
no server or local pull needed.

Usage:
    python scripts/export_matches.py
"""
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import MATCH_RETENTION_DAYS
from app.database import SessionLocal, init_db
from app.models import Job

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "matches.txt"


def export():
    init_db()
    db = SessionLocal()
    try:
        # run_scrape.py already purges rows older than MATCH_RETENTION_DAYS,
        # but this filter is a safety net in case export runs on its own.
        cutoff = datetime.utcnow() - timedelta(days=MATCH_RETENTION_DAYS)
        jobs = (
            db.query(Job)
            .filter(Job.matched.is_(True))
            .filter(Job.created_at >= cutoff)
            .order_by(Job.match_score.desc())
            .all()
        )

        lines = [
            f"Matched jobs — updated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
            f"Showing matches from the last {MATCH_RETENTION_DAYS} day(s). Total: {len(jobs)}",
            "=" * 70,
            "",
        ]

        for job in jobs:
            lines.append(f"[{job.match_score:.2f}] {job.company} — {job.title}")
            if job.location:
                lines.append(f"  Location: {job.location}")
            lines.append(f"  Source:   {job.source}")
            if job.match_reason:
                lines.append(f"  Why:      {job.match_reason}")
            lines.append(f"  Link:     {job.url}")
            lines.append("")

        OUTPUT_PATH.write_text("\n".join(lines), encoding="utf-8")
        print(f"Wrote {len(jobs)} matched jobs to {OUTPUT_PATH}")
    finally:
        db.close()


if __name__ == "__main__":
    export()
