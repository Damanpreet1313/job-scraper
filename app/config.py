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

# --- Company/board seed list ---
# board_slug is the identifier the ATS uses in its public API URL, NOT the
# company's display name. Slugs drift and companies switch ATS providers,
# so treat this as a starting point — verify each slug still resolves
# (open the URL pattern in the relevant scraper file) and add your own.
GREENHOUSE_BOARDS = [
    "gitlab",
    "stripe",
    "cloudflare",
    "hashicorp",
    "datadog",
]

LEVER_BOARDS = [
    "netflix",
    "figma",
]

ASHBY_BOARDS = [
    "ramp",
    "linear",
]

# Keyword filters applied to remote job boards (RemoteOK, WWR) since those
# aggregate every category, not just DevOps/Cloud.
REMOTE_KEYWORDS = [
    "devops",
    "cloud",
    "sre",
    "platform engineer",
    "infrastructure",
    "kubernetes",
    "terraform",
]
