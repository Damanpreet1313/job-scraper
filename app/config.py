import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL") or "sqlite:///./jobs.db"
MATCH_THRESHOLD = float(os.getenv("MATCH_THRESHOLD") or "0.15")

# Optional: if set, matching uses Groq for a sharper semantic score on top of
# the TF-IDF pre-filter. If unset, matching silently falls back to TF-IDF only.
GROQ_API_KEY = os.getenv("GROQ_API_KEY") or ""
GROQ_MODEL = os.getenv("GROQ_MODEL") or "openai/gpt-oss-20b"

# How many days a job stays in the DB / matches.txt before being purged.
# A still-active posting gets re-added with a fresh timestamp next scrape,
# so this doesn't hide long-running listings — it just keeps stale ones out.
MATCH_RETENTION_DAYS = int(os.getenv("MATCH_RETENTION_DAYS") or "3")

# Adzuna API (https://developer.adzuna.com — free account) covers regional
# listings including India ("in"), where a lot of DevOps internships live.
# Unset keys just skip the source.
ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID") or ""
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY") or ""
ADZUNA_REGION = os.getenv("ADZUNA_REGION") or "in"

# --- Company/board seed list ---
# board_slug is the identifier the ATS uses in its public API URL, NOT the
# company's display name. Slugs drift and companies switch ATS providers,
# so treat this as a starting point — verify each slug still resolves
# (open the URL pattern in the relevant scraper file) and add your own.
GREENHOUSE_BOARDS = [
    "gitlab",
    "stripe",
    "cloudflare",
    "datadog",
    "mongodb",
    "elastic",
]

LEVER_BOARDS = [
    "palantir",
]

ASHBY_BOARDS = [
    "ramp",
    "linear",
    "notion",
]

# Keyword filters applied to remote job boards (RemoteOK, WWR, Arbeitnow,
# Remotive, Jobicy, Adzuna) since those aggregate every category, not just
# DevOps/Cloud. "intern"/"trainee"/"fresher" catch entry-level roles that
# don't mention a cloud keyword in the title but match a junior job search.
REMOTE_KEYWORDS = [
    "devops",
    "cloud",
    "sre",
    "platform engineer",
    "infrastructure",
    "kubernetes",
    "terraform",
    "intern",
    "trainee",
    "fresher",
    "graduate",
]
