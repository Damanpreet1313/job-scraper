from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Optional
import asyncio
from pathlib import Path

from fastapi import FastAPI, Depends, Query, HTTPException, Header, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc, text

from app.config import SCRAPE_API_KEY, REDIS_URL
from app.database import get_db_dependency as get_db, init_db, engine
from app.job_queue import get_redis_client, enqueue_scrape, get_scrape_status
from app.models import Job
from app.worker import start_worker

# Prometheus metrics
from prometheus_fastapi_instrumentator import Instrumentator


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    worker_task = await start_worker()
    yield
    # Shutdown
    worker_task.cancel()
    try:
        await worker_task
    except asyncio.CancelledError:
        pass


app = FastAPI(title="DevOps/Cloud Job Scraper", lifespan=lifespan)

# Prometheus metrics instrumentation
Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

# Serve static frontend
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
async def root():
    return FileResponse(static_dir / "index.html")


@app.get("/health")
def health():
    """Health check for K8s liveness/readiness probes.
    
    Checks:
    - Database connectivity
    - Redis connectivity (for job queue)
    """
    checks = {}
    overall = "healthy"
    
    # Check DB
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {e}"
        overall = "unhealthy"
    
    # Check Redis
    redis_client = get_redis_client()
    if redis_client:
        try:
            redis_client.ping()
            checks["redis"] = "ok"
        except Exception as e:
            checks["redis"] = f"error: {e}"
            overall = "degraded"  # Redis is optional for basic API functionality
    else:
        checks["redis"] = "unavailable"
        overall = "degraded"
    
    return {"status": overall, "checks": checks}


@app.get("/jobs")
def list_jobs(
    matched_only: bool = Query(False, description="Only return jobs above the match threshold"),
    source: Optional[str] = Query(None, description="Filter by source: greenhouse, lever, ashby, remoteok, weworkremotely, remotive, jobicy, arbeitnow, adzuna"),
    min_score: Optional[float] = Query(None, ge=0, le=1),
    posted_since_days: Optional[int] = Query(None, ge=1, description="Only jobs posted within last N days"),
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
    if posted_since_days is not None:
        cutoff = datetime.utcnow() - timedelta(days=posted_since_days)
        query = query.filter(Job.posted_date_parsed >= cutoff)

    query = query.order_by(desc(Job.match_score), desc(Job.created_at))
    total = query.count()
    rows = query.offset(offset).limit(limit).all()

    return {
        "total": total,
        "count": len(rows),
        "jobs": [r.to_dict() for r in rows],
    }


from fastapi import HTTPException

@app.get("/jobs/{job_id}")
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
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


@app.post("/scrape")
def trigger_scrape(
    sources: Optional[str] = Query(None, description="Comma-separated sources to scrape (default: all)"),
    x_api_key: str = Header(None, alias="X-API-Key"),
):
    """Trigger an async scrape job via Redis queue.
    
    Requires X-API-Key header matching SCRAPE_API_KEY env var.
    Returns immediately with job queued status; actual scrape runs in background worker.
    """
    if not SCRAPE_API_KEY:
        raise HTTPException(status_code=503, detail="Scrape endpoint disabled (SCRAPE_API_KEY not set)")
    if x_api_key != SCRAPE_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    source_list = [s.strip() for s in sources.split(",")] if sources else None
    if source_list:
        unknown = [s for s in source_list if s not in {
            "greenhouse", "lever", "ashby", "startup_greenhouse", "startup_lever", "startup_ashby",
            "remoteok", "weworkremotely", "remotive", "jobicy", "arbeitnow", "adzuna",
            "ycombinator", "remoteco", "himalayas", "wellfound", "otta", "levels_fyi",
            "indeed", "career_pages"
        }]
        if unknown:
            raise HTTPException(status_code=400, detail=f"Unknown source(s): {', '.join(unknown)}")
    
    queued = enqueue_scrape(source_list)
    if not queued:
        raise HTTPException(status_code=503, detail="Failed to queue scrape (Redis unavailable)")
    
    return {"status": "queued", "sources": source_list or "all"}


@app.get("/scrape/status")
def scrape_status():
    """Get status of last scrape job."""
    return get_scrape_status()
