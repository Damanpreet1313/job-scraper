import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL") or "sqlite:///./jobs.db"
MATCH_THRESHOLD = float(os.getenv("MATCH_THRESHOLD") or "0.02")

# Optional: if set, matching uses Groq for a sharper semantic score on top of
# the TF-IDF pre-filter. If unset, matching silently falls back to TF-IDF only.
GROQ_API_KEY = os.getenv("GROQ_API_KEY") or ""
GROQ_MODEL = os.getenv("GROQ_MODEL") or "llama-3.1-70b-versatile"

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

# DevOps/Cloud role keywords — match against job TITLE only (not description)
# to avoid false positives from company boilerplate text.
DEVOPS_KEYWORDS = [
    "devops",
    "sre",
    "site reliability engineer",
    "site reliability",
    "platform engineer",
    "infrastructure engineer",
    "kubernetes",
    "terraform",
    "docker",
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
    "reliability engineer",
    "production engineer",
    "build engineer",
    "release engineer",
    "deployment engineer",
    "cloud engineer",
    "k8s",
    "cloudformation",
    "pulumi",
    "devsecops",
]

# Junior/Entry-level/Internship keywords — match against job TITLE only
# Note: "associate" removed - too generic (matches "Sales Associate", "Retail Associate", etc.)
JUNIOR_KEYWORDS = [
    "intern",
    "internship",
    "trainee",
    "fresher",
    "graduate",
    "junior",
    "entry",
    "entry-level",
    "entry level",
    "apprentice",
    "co-op",
    "coop",
    "student",
    "new grad",
    "new-grad",
    # Additional keywords for real-world junior titles:
    # "associate" removed - too generic (matches "Sales Associate", "Cloud Native Associate cert", etc.)
    "level 1",
    "level 2",
    "l1",
    "l2",
    "e1",
    "e2",
    "e3",
    "early career",
    "early-career",
    "0-1 year",
    "0-2 years",
    "1-2 years",
]

# Senior/Lead/Principal/Staff keywords — EXCLUDE these from results
# Match against job TITLE only to avoid filtering out relevant junior roles
SENIOR_EXCLUSION_KEYWORDS = [
    "senior",
    "sr.",
    "sr ",
    "lead",
    "principal",
    "staff",
    "architect",
    "manager",
    "director",
    "head of",
    "vp ",
    "vice president",
    "chief",
    "cto",
    "cpo",
    "founder",
    "co-founder",
    "cofounder",
    # Level indicators
    " ii",
    " iii",
    " iv",
    " v",
    " 2 ",
    " 3 ",
    " 4 ",
    " 5 ",
    " level 2",
    " level 3",
    " level 4",
    " level 5",
    " l2 ",
    " l3 ",
    " l4 ",
    " l5 ",
]

# Keyword filters applied to remote job boards (RemoteOK, WWR, Arbeitnow,
# Remotive, Jobicy, Adzuna) since those aggregate every category, not just
# DevOps/Cloud. Used for title+tags filtering.
REMOTE_KEYWORDS = DEVOPS_KEYWORDS + JUNIOR_KEYWORDS

# --- Location Preferences ---
# User is based in Delhi, India - can commute to these NCR cities for onsite/hybrid
DELHI_NCR_LOCATIONS = [
    "delhi",
    "new delhi",
    "noida",
    "gurugram",
    "gurgaon",
    "faridabad",
    "ghaziabad",
    "greater noida",
    "ncr",
    "national capital region",
]

# Allowed work types for NCR locations (onsite/hybrid/remote all OK)
NCR_ALLOWED_WORK_TYPES = ["onsite", "hybrid", "remote", "on-site", "on site"]

# For non-NCR locations, only remote is allowed
NON_NCR_ALLOWED_WORK_TYPES = ["remote"]

# Global remote-friendly countries/regions for expanded search
# These are countries known for remote-friendly hiring
REMOTE_FRIENDLY_COUNTRIES = [
    # North America
    "united states", "usa", "us", "canada",
    # Europe
    "united kingdom", "uk", "england", "scotland", "wales", "northern ireland",
    "ireland", "germany", "france", "netherlands", "holland", "poland",
    "sweden", "norway", "denmark", "finland", "switzerland", "austria",
    "belgium", "spain", "portugal", "italy", "czech republic", "czechia",
    "romania", "bulgaria", "estonia", "latvia", "lithuania", "croatia",
    "slovenia", "slovakia", "hungary", "greece", "malta", "cyprus",
    # Asia Pacific
    "singapore", "taiwan", "malaysia", "japan", "south korea", "korea",
    "australia", "new zealand", "nz", "philippines", "vietnam", "thailand",
    "indonesia", "hong kong", "hongkong",
    # Middle East
    "united arab emirates", "uae", "dubai", "abu dhabi", "qatar", "kuwait",
    "saudi arabia", "bahrain", "oman", "israel",
    # Africa
    "south africa", "nigeria", "kenya", "egypt", "morocco", "ghana",
    # Remote-first / anywhere
    "worldwide", "global", "anywhere", "remote",
]

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
    "vercel",
    "planetscale",
    "supabase",
    "railway",
    "render",
    "flyio",
    "temporal",
    "dagster",
    "prefect",
    "prefecthq",
    "dagster-io",
    "hashicorp",
    "confluent",
    "cockroachlabs",
    "timescale",
    "singlestore",
    "materialize",
    "redpanda",
    "temporalio",
    "ngrok",
    "cloudamqp",
    "heroku",
    "digitalocean",
    "linode",
    "vultr",
    "equinix",
    "packet",
    "scaleway",
    "ovh",
    "hetzner",
    "contabo",
]

LEVER_BOARDS = [
    "palantir",
    "vercel",
    "planetscale",
    "supabase",
    "railway",
    "temporal",
    "prefect",
    "dagster",
    "linear",
    "notion",
    "figma",
    "airtable",
    "webflow",
    "zapier",
    "segment",
    "amplitude",
    "mixpanel",
    "heap",
    "posthog",
    "rudderstack",
    "airbyte",
    "fivetran",
    "dbt-labs",
    "prefecthq",
    "dagster-io",
    "astronomer",
]

ASHBY_BOARDS = [
    "ramp",
    "linear",
    "notion",
    "vercel",
    "planetscale",
    "supabase",
    "railway",
    "render",
    "flyio",
    "temporal",
    "prefect",
    "dagster",
    "prefecthq",
    "dagster-io",
    "astronomer",
    "hashicorp",
    "confluent",
    "cockroachlabs",
    "timescale",
    "materialize",
    "redpanda",
    "ngrok",
    "airbyte",
    "fivetran",
    "dbt-labs",
    "posthog",
    "rudderstack",
    "heap",
    "mixpanel",
    "amplitude",
    "segment",
    "zapier",
    "webflow",
    "airtable",
    "figma",
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
    "hashicorp",
    "confluent",
    "cockroachlabs",
    "timescale",
    "materialize",
    "redpanda",
    "ngrok",
    "airbyte",
    "fivetran",
    "dbt-labs",
    "posthog",
    "rudderstack",
]

STARTUP_LEVER_BOARDS = [
    "vercel",
    "planetscale",
    "supabase",
    "railway",
    "temporal",
    "prefect",
    "dagster",
    "linear",
    "notion",
    "figma",
    "airtable",
    "webflow",
    "zapier",
    "segment",
    "amplitude",
    "mixpanel",
    "heap",
    "posthog",
    "rudderstack",
    "airbyte",
    "fivetran",
    "dbt-labs",
]

STARTUP_ASHBY_BOARDS = [
    "linear",
    "notion",
    "temporal",
    "prefect",
    "vercel",
    "planetscale",
    "supabase",
    "railway",
    "render",
    "flyio",
    "dagster",
    "prefecthq",
    "dagster-io",
    "astronomer",
]