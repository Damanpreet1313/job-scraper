import requests

from app.config import (
    ADZUNA_APP_ID,
    ADZUNA_APP_KEY,
    ADZUNA_REGION,
    REMOTE_KEYWORDS,
    SENIOR_EXCLUSION_KEYWORDS,
)
from app.scrapers.base import normalize_job
from app.scrapers.keywords import is_senior
from app.scrapers.locations import is_location_allowed

BASE_URL = "https://api.adzuna.com/v1/api/jobs/{region}/search/1"

# Search multiple regions for global remote opportunities
ADZUNA_REGIONS = [
    "in",      # India (for NCR onsite/hybrid + remote)
    "us",      # United States
    "ca",      # Canada
    "gb",      # United Kingdom
    "au",      # Australia
    "nz",      # New Zealand
    "de",      # Germany
    "fr",      # France
    "nl",      # Netherlands
    "pl",      # Poland
    "ie",      # Ireland
    "sg",      # Singapore
    "ae",      # UAE
    "za",      # South Africa
    "br",      # Brazil
    "mx",      # Mexico
]


def fetch_jobs(timeout: int = 15) -> list[dict]:
    """Adzuna's search API (free account at developer.adzuna.com).
    Searches multiple regions for junior devops/cloud roles globally.
    Returns [] if no API keys are configured."""
    if not ADZUNA_APP_ID or not ADZUNA_APP_KEY:
        print("  adzuna skipped: set ADZUNA_APP_ID / ADZUNA_APP_KEY in .env")
        return []

    # Search for junior devops roles specifically
    search_terms = [
        "junior devops",
        "entry level devops",
        "devops intern",
        "devops trainee",
        "graduate devops",
        "associate devops",
        "junior cloud",
        "entry level cloud",
        "cloud intern",
        "junior sre",
        "entry level sre",
        "sre intern",
    ]

    all_jobs = []
    for region in ADZUNA_REGIONS:
        for term in search_terms:
            resp = requests.get(
                BASE_URL.format(region=region),
                params={
                    "app_id": ADZUNA_APP_ID,
                    "app_key": ADZUNA_APP_KEY,
                    "what": term,
                    "results_per_page": 20,
                },
                timeout=timeout,
            )
            if resp.status_code != 200:
                continue

            for item in resp.json().get("results", []):
                title = item.get("title", "Untitled")
                if is_senior(title):
                    continue

                category = (item.get("category") or {}).get("label", "")
                haystack = f"{title} {category}".lower()
                if not any(kw in haystack for kw in REMOTE_KEYWORDS):
                    continue

                location = (item.get("location") or {}).get("display_name")
                description = item.get("description", "")
                
                # Apply location filtering
                allowed, reason = is_location_allowed(location, description)
                if not allowed:
                    continue

                all_jobs.append(
                    normalize_job(
                        company=(item.get("company") or {}).get("display_name", "Unknown"),
                        title=title,
                        location=location,
                        url=item.get("redirect_url", ""),
                        source="adzuna",
                        posted_date=item.get("created"),
                        description=description,
                    )
                )

    # Deduplicate by content_hash
    seen = set()
    jobs = []
    for job in all_jobs:
        if job["content_hash"] not in seen:
            seen.add(job["content_hash"])
            jobs.append(job)

    return jobs
