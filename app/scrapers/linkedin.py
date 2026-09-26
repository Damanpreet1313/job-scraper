"""LinkedIn job scraper via RSS/Atom feeds (limited public access)."""
import feedparser

from app.scrapers.base import normalize_job
from app.scrapers.keywords import is_senior, is_devops_role, JUNIOR_PATTERNS
from app.scrapers.locations import is_location_allowed

# LinkedIn doesn't provide public RSS for job search anymore.
# This is a placeholder for if/when they restore it, or for company-specific feeds.
# For now, we'll use a generic approach with common LinkedIn job search URLs
# that might work via RSS if accessible.

LINKEDIN_SEARCH_URLS = [
    # These are example search URLs - LinkedIn RSS is very limited now
    # You may need to use their official API or partner access
]


def fetch_jobs(timeout: int = 15) -> list[dict]:
    """LinkedIn jobs - currently no public RSS feed available.
    
    Note: LinkedIn removed public RSS feeds. Options:
    1. Use LinkedIn Partner API (requires approval)
    2. Use third-party services that aggregate LinkedIn jobs
    3. Scrape company career pages directly (see career_pages.py)
    
    Returns empty list for now - implement when API access available.
    """
    return []


def fetch_company_linkedin_feed(company_slug: str, timeout: int = 15) -> list[dict]:
    """Fetch jobs from a specific company's LinkedIn feed if they have one public.
    
    Some companies have public job feeds at:
    https://www.linkedin.com/jobs/search/?f_C={company_id}&format=rss
    """
    # This would require knowing the company's LinkedIn ID
    # Not practical for general scraping without API access
    return []