# DevOps/Cloud Job Scraper

Standalone tool that pulls DevOps/Cloud postings from company job boards and
remote-job aggregators, dedupes them, scores each one against your resume,
and stores everything in a local (or hosted) database you can query via API.

## How it works

1. **Scrapers** (`app/scrapers/`) hit public JSON/RSS endpoints — no HTML
   scraping of LinkedIn/Indeed, which is fragile and ToS-risky. Sources:
   - Greenhouse & Lever & Ashby: public job-board APIs for individual companies (`app/config.py` seed list)
   - RemoteOK: public API, filtered by DevOps/Cloud keywords
   - WeWorkRemotely: RSS feed, already scoped to the DevOps/SysAdmin category
   - Remotive & Jobicy & Arbeitnow: public no-auth job APIs, filtered by DevOps/Cloud keywords
   - Adzuna: search API (free key), defaults to India region where internships are listed
   Boards are fetched concurrently, so adding sources doesn't add linear runtime.
2. **Dedupe**: each posting gets a hash of `company + title + url`, so
   re-running the scrape never inserts the same job twice.
3. **Matching**: `app/matcher.py` TF-IDF ranks every job first (fast, no API
   calls). If a `GROQ_API_KEY` is set, `app/llm_matcher.py` then re-scores the
   top candidates with Groq for a sharper semantic match plus a one-line
   reason; without a key it falls back to pure TF-IDF.
4. **Storage**: SQLAlchemy, SQLite by default, one env var away from Postgres.
5. **API**: FastAPI app to query/filter results.

## Setup

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `resume.txt` with your actual skills/resume text — this is what jobs get
scored against.

Edit `app/config.py` — the Greenhouse/Lever/Ashby board slugs are a small
seed list and **not guaranteed to still be valid**; ATS board slugs drift.
Verify each by opening the API URL pattern in the relevant scraper file
directly in a browser, then add the companies you actually care about.

## Run a scrape

```bash
python scripts/run_scrape.py
# or a subset of sources:
python scripts/run_scrape.py --source remoteok,remotive,jobicy
# control fetch concurrency:
python scripts/run_scrape.py --workers 4
```

This fetches all sources (concurrently), dedupes against what's already
stored, scores against `resume.txt`, and prints a summary.

## Query results

```bash
uvicorn app.main:app --reload
```

- `GET /jobs` — all stored jobs, newest/highest-scored first
- `GET /jobs?matched_only=true` — only jobs above `MATCH_THRESHOLD`
- `GET /jobs?source=greenhouse&min_score=0.2`
- `GET /jobs/{id}` — full posting including description
- `GET /stats` — counts by source, total matched

## Scheduling

`.github/workflows/scrape.yml` runs the scraper every 6 hours via GitHub
Actions (`workflow_dispatch` also lets you trigger it manually from the
Actions tab). Two options for persistence:

- **SQLite**: the workflow commits `jobs.db` back to the repo after each
  run. Simple, but not ideal for a long-lived DB in git history.
- **Postgres** (recommended): set a `DATABASE_URL` repo secret pointing at
  a hosted Postgres — e.g. reuse the Supabase/Render setup from Deckoviz —
  and delete the "commit sqlite db" step.

## Tests

```bash
pytest
```

Covers dedupe hashing and match scoring with fixed inputs — no network
calls, so these run offline/in CI without hitting live job boards.

## Extending

- Add more Greenhouse/Lever/Ashby companies in `app/config.py`.
- Add a new source by writing a `fetch_jobs()` function in
  `app/scrapers/` that returns a list of `normalize_job(...)` dicts, then
  wire it into `scripts/run_scrape.py`'s `SOURCE_SCRAPERS`.
- Swap TF-IDF for embeddings in `app/matcher.py` if keyword matching isn't
  precise enough.
