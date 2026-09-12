"""Adzuna job scraper."""
import asyncio
from app.config import ADZUNA_APP_ID, ADZUNA_APP_KEY, ADZUNA_REGION, REMOTE_KEYWORDS
from app.logging_config import get_logger
from app.scrapers.base import normalize_job
from app.scrapers.http_client import get_http_client
from app.scrapers.keywords import is_senior
from app.scrapers.locations import is_location_allowed

logger = get_logger(__name__)

BASE_URL = "https://api.adzuna.com/v1/api/jobs/{region}/search/1"

ADZUNA_REGIONS = [
    "in", "us", "ca", "gb", "au", "nz", "de", "fr", "nl", "pl", "ie", "sg", "ae", "za", "br", "mx",
]


async def fetch_jobs(timeout: int = 15) -> list[dict]:
    """Adzuna's search API - searches multiple regions for junior devops/cloud roles."""
    if not ADZUNA_APP_ID or not ADZUNA_APP_KEY:
        logger.info("adzuna_skipped", extra={"reason": "no API keys configured"})
        return []

    search_terms = [
        "junior devops", "entry level devops", "devops intern", "devops trainee",
        "graduate devops", "associate devops", "junior cloud", "entry level cloud",
        "cloud intern", "junior sre", "entry level sre", "sre intern",
    ]

    client = await get_http_client()
    all_jobs = []

    for region in ADZUNA_REGIONS:
        for term in search_terms:
            try:
                resp = await client.get(
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
            except Exception as e:
                logger.error("adzuna_fetch_error", extra={"region": region, "term": term, "error": str(e)})

    # Deduplicate by content_hash
    seen = set()
    jobs = []
    for job in all_jobs:
        if job["content_hash"] not in seen:
            seen.add(job["content_hash"])
            jobs.append(job)

    return jobs