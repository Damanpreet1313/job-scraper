import hashlib
import re


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
    text = re.sub(r"&nbsp;|&amp;|&lt;|&gt;", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def normalize_job(company, title, location, url, source, posted_date, description):
    description = strip_html(description or "")
    return {
        "company": company,
        "title": title,
        "location": location,
        "url": url,
        "source": source,
        "posted_date": posted_date,
        "description": description,
        "content_hash": make_content_hash(company, title, url),
    }
