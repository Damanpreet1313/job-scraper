"""Company career pages scraper - direct scraping of known company job boards."""
import asyncio
from bs4 import BeautifulSoup
from app.logging_config import get_logger
from app.scrapers.base import normalize_job
from app.scrapers.http_client import get_http_client
from app.scrapers.keywords import is_senior, is_devops_role, JUNIOR_PATTERNS
from app.scrapers.locations import is_location_allowed

logger = get_logger(__name__)

COMPANY_CAREER_PAGES = [
    ("google", "https://careers.google.com/jobs/results/", {
        "list_selector": "li.lst__item", "title_selector": "h3", "link_selector": "a",
        "location_selector": ".location", "description_selector": ".description",
    }),
    ("microsoft", "https://careers.microsoft.com/us/en/search-results", {
        "list_selector": ".job-tile", "title_selector": "h2", "link_selector": "a",
        "location_selector": ".location", "description_selector": ".description",
    }),
    ("amazon", "https://www.amazon.jobs/en/search", {
        "list_selector": ".job-tile", "title_selector": "h3", "link_selector": "a",
        "location_selector": ".location", "description_selector": ".description",
    }),
    ("meta", "https://www.metacareers.com/jobs/", {
        "list_selector": ".job-result-card", "title_selector": "h3", "link_selector": "a",
        "location_selector": ".location", "description_selector": ".description",
    }),
    ("apple", "https://jobs.apple.com/en-us/search", {
        "list_selector": ".job-tile", "title_selector": "h3", "link_selector": "a",
        "location_selector": ".location", "description_selector": ".description",
    }),
    ("netflix", "https://jobs.netflix.com/search", {
        "list_selector": ".job-listing", "title_selector": "h3", "link_selector": "a",
        "location_selector": ".location", "description_selector": ".description",
    }),
    ("uber", "https://www.uber.com/global/en/careers/list/", {
        "list_selector": ".job-listing", "title_selector": "h3", "link_selector": "a",
        "location_selector": ".location", "description_selector": ".description",
    }),
    ("airbnb", "https://careers.airbnb.com/positions/", {
        "list_selector": ".position", "title_selector": "h3", "link_selector": "a",
        "location_selector": ".location", "description_selector": ".description",
    }),
    ("stripe", "https://stripe.com/jobs/search", {
        "list_selector": ".job-listing", "title_selector": "h3", "link_selector": "a",
        "location_selector": ".location", "description_selector": ".description",
    }),
    ("datadog", "https://www.datadoghq.com/careers/", {
        "list_selector": ".job-listing", "title_selector": "h3", "link_selector": "a",
        "location_selector": ".location", "description_selector": ".description",
    }),
]


async def fetch_jobs(timeout: int = 30) -> list[dict]:
    """Scrape company career pages directly for DevOps/Cloud junior roles."""
    client = await get_http_client()
    jobs = []
    devops_queries = [
        "devops", "cloud", "sre", "site reliability", "platform engineer",
        "infrastructure", "kubernetes", "terraform", "docker"
    ]
    junior_queries = [
        "intern", "internship", "junior", "entry", "new grad", "graduate", "trainee"
    ]

    for company, url, selectors in COMPANY_CAREER_PAGES:
        try:
            resp = await client.get(url, timeout=timeout)
            if resp.status_code != 200:
                logger.warning("career_page_non_200", extra={"company": company, "status": resp.status_code})
                continue

            soup = BeautifulSoup(resp.content, "html.parser")
            listings = soup.select(selectors["list_selector"])

            for listing in listings[:50]:
                try:
                    title_elem = listing.select_one(selectors["title_selector"])
                    link_elem = listing.select_one(selectors["link_selector"])
                    location_elem = listing.select_one(selectors["location_selector"])
                    desc_elem = listing.select_one(selectors["description_selector"])

                    if not title_elem or not link_elem:
                        continue

                    title = title_elem.get_text(strip=True)
                    if is_senior(title):
                        continue

                    title_lower = title.lower()
                    has_devops = any(q in title_lower for q in devops_queries)
                    has_junior = any(q in title_lower for q in junior_queries)
                    if not (has_devops and has_junior):
                        continue

                    description = desc_elem.get_text(strip=True) if desc_elem else ""
                    location = location_elem.get_text(strip=True) if location_elem else "Unknown"
                    job_url = link_elem.get("href", "")
                    if job_url and not job_url.startswith("http"):
                        from urllib.parse import urljoin
                        job_url = urljoin(url, job_url)

                    allowed, reason = is_location_allowed(location, description)
                    if not allowed:
                        continue

                    jobs.append(
                        normalize_job(
                            company=company.title(),
                            title=title,
                            location=location,
                            url=job_url,
                            source="career_page",
                            posted_date=None,
                            description=description,
                        )
                    )
                except Exception as e:
                    logger.debug("career_page_listing_error", extra={"company": company, "error": str(e)})
                    continue

        except Exception as e:
            logger.error("career_page_fetch_error", extra={"company": company, "error": str(e)})
            continue

    return jobs