"""
Writes every matched job (score >= MATCH_THRESHOLD) out to matches.txt,
sorted highest-score first. Overwrites the file each run so it always
reflects the current full set of matches — open it directly on GitHub,
no server or local pull needed.

Usage:
    python scripts/export_matches.py
"""
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal, init_db
from app.models import Job

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "matches.txt"


def export():
    init_db()
    db = SessionLocal()
    try:
        jobs = (
            db.query(Job)
            .filter(Job.matched.is_(True))
            .order_by(Job.match_score.desc())
            .all()
        )

        lines = [
            f"Matched jobs — updated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
            f"Total matches: {len(jobs)}",
            "=" * 70,
            "",
        ]

        for job in jobs:
            lines.append(f"[{job.match_score:.2f}] {job.company} — {job.title}")
            if job.location:
                lines.append(f"  Location: {job.location}")
            lines.append(f"  Source:   {job.source}")
            lines.append(f"  Link:     {job.url}")
            lines.append("")

        OUTPUT_PATH.write_text("\n".join(lines), encoding="utf-8")
        print(f"Wrote {len(jobs)} matched jobs to {OUTPUT_PATH}")
    finally:
        db.close()


if __name__ == "__main__":
    export()
