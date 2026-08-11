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

# DevOps/Cloud role keywords — match against job TITLE only (not description)
# to avoid false positives from company boilerplate text.
DEVOPS_KEYWORDS = [
    "devops",
    "cloud",
    "sre",
    "site reliability",
    "platform engineer",
    "infrastructure",
    "kubernetes",
    "terraform",
    "docker",
    "aws",
    "azure",
    "gcp",
    "ci/cd",
    "cicd",
    "jenkins",
    "gitlab ci",
    "github actions",
    "argocd",
    "flux",
    "helm",
    "ansible",
    "prometheus",
    "grafana",
    "observability",
    "reliability engineer",
    "production engineer",
    "systems engineer",
    "network engineer",
    "security engineer",
    "devsecops",
]

# Junior/Entry-level/Internship keywords — match against job TITLE only
JUNIOR_KEYWORDS = [
    "intern",
    "trainee",
    "fresher",
    "graduate",
    "junior",
    "entry",
    "entry-level",
    "entry level",
    "associate",
    "apprentice",
    "co-op",
    "coop",
    "student",
    "new grad",
    "new-grad",
]

# Keyword filters applied to remote job boards (RemoteOK, WWR, Arbeitnow,
# Remotive, Jobicy, Adzuna) since those aggregate every category, not just
# DevOps/Cloud. Used for title+tags filtering.
REMOTE_KEYWORDS = DEVOPS_KEYWORDS + JUNIOR_KEYWORDS

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

# Startup-focused boards (smaller companies, earlier stage)
# These are in addition to the main boards above
STARTUP_GREENHOUSE_BOARDS = [
    "vercel",
    "planetscale",
    "supabase",
    "railway",
    "render",
    "flyio",
    "temporal",
    "dagster",
    "prefect",
    "dagster-io",
]

STARTUP_LEVER_BOARDS = [
    "vercel",
    "planetscale",
    "supabase",
    "railway",
]

STARTUP_ASHBY_BOARDS = [
    "linear",
    "notion",
    "temporal",
    "prefect",
]
