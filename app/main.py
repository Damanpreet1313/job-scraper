from typing import Optional

from fastapi import FastAPI, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db, init_db
from app.models import Job

app = FastAPI(title="DevOps/Cloud Job Scraper")


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/jobs")
def list_jobs(
    matched_only: bool = Query(False, description="Only return jobs above the match threshold"),
    source: Optional[str] = Query(None, description="Filter by source: greenhouse, lever, ashby, remoteok, weworkremotely"),
    min_score: Optional[float] = Query(None, ge=0, le=1),
    limit: int = Query(50, le=500),
    offset: int = 0,
    db: Session = Depends(get_db),
):
    query = db.query(Job)
    if matched_only:
        query = query.filter(Job.matched.is_(True))
    if source:
        query = query.filter(Job.source == source)
    if min_score is not None:
        query = query.filter(Job.match_score >= min_score)

    query = query.order_by(desc(Job.match_score), desc(Job.created_at))
    total = query.count()
    rows = query.offset(offset).limit(limit).all()

    return {
        "total": total,
        "count": len(rows),
        "jobs": [r.to_dict() for r in rows],
    }


@app.get("/jobs/{job_id}")
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        return {"error": "not found"}
    result = job.to_dict()
    result["description"] = job.description
    return result


@app.get("/stats")
def stats(db: Session = Depends(get_db)):
    total = db.query(Job).count()
    matched = db.query(Job).filter(Job.matched.is_(True)).count()
    by_source = {}
    for source, in db.query(Job.source).distinct():
        by_source[source] = db.query(Job).filter(Job.source == source).count()
    return {"total_jobs": total, "matched_jobs": matched, "by_source": by_source}
