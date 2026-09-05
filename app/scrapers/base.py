import hashlib
import re
from datetime import datetime
from typing import Optional


def make_content_hash(company: str, title: str, url: str) -> str:
    """Stable dedupe key. Uses company+title+url (normalized) rather than
    just url, since some boards reissue the same posting under a new URL."""
    key = f"{company.strip().lower()}|{title.strip().lower()}|{url.strip().lower()}"
    key = re.sub(r"\s+", " ", key)
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def strip_html(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&nbsp;|&|<|>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def parse_posted_date(date_str: Optional[str]) -> Optional[datetime]:
    """Parse various date formats from job boards into datetime."""
    if not date_str:
        return None

    formats = [
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%d %b %Y",
        "%d %B %Y",
        "%b %d, %Y",
        "%B %d, %Y",
        "%m/%d/%Y",
        "%d/%m/%Y",
    ]

    date_str = date_str.strip()
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.replace(tzinfo=None) if dt.tzinfo else dt
        except ValueError:
            continue

    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.replace(tzinfo=None) if dt.tzinfo else dt
    except ValueError:
        pass

    return None


def normalize_title_company(company: str, title: str) -> tuple[str, str]:
    """Normalize company and title for better dedupe matching."""
    company = re.sub(r"\s+", " ", company.strip().lower())
    title = re.sub(r"\s+", " ", title.strip().lower())
    company = re.sub(r"\b(inc|llc|ltd|corp|corporation|company|co)\.?\b", "", company)
    company = re.sub(r"\s+", " ", company).strip("., ")
    return company, title


def make_content_hash_normalized(company: str, title: str, url: str) -> str:
    """Stable dedupe key using normalized company+title+url."""
    company, title = normalize_title_company(company, title)
    key = f"{company}|{title}|{url.strip().lower()}"
    key = re.sub(r"\s+", " ", key)
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def normalize_job(company, title, location, url, source, posted_date, description):
    description = strip_html(description or "")
    parsed_date = parse_posted_date(posted_date)
    return {
        "company": company,
        "title": title,
        "location": location,
        "url": url,
        "source": source,
        "posted_date": posted_date,
        "posted_date_parsed": parsed_date,
        "description": description,
        "content_hash": make_content_hash_normalized(company, title, url),
    }
