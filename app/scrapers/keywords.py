"""Keyword matching utilities with word-boundary support."""
import re
from typing import List

from app.config import DEVOPS_KEYWORDS, JUNIOR_KEYWORDS, SENIOR_EXCLUSION_KEYWORDS

# Pre-compile regex patterns for word-boundary matching
DEVOPS_PATTERNS = [re.compile(rf"\b{re.escape(kw)}\b", re.IGNORECASE) for kw in DEVOPS_KEYWORDS]
JUNIOR_PATTERNS = [re.compile(rf"\b{re.escape(kw)}\b", re.IGNORECASE) for kw in JUNIOR_KEYWORDS]
SENIOR_PATTERNS = [re.compile(rf"\b{re.escape(kw)}\b", re.IGNORECASE) for kw in SENIOR_EXCLUSION_KEYWORDS]


def _has_keyword(text: str, patterns: List[re.Pattern]) -> bool:
    """Check if any pattern matches in text."""
    return any(p.search(text) for p in patterns)


def is_senior(title: str) -> bool:
    """Check if title indicates a senior-level role."""
    return _has_keyword(title, SENIOR_PATTERNS)


def is_junior_devops(title: str, description: str) -> bool:
    """Check if job is a junior DevOps role (requires BOTH devops AND junior keywords).
    Checks title + description for junior keywords since many roles list
    '0-2 years', 'entry level', 'new grad' in description not title."""
    has_devops = _has_keyword(title, DEVOPS_PATTERNS)
    haystack = f"{title} {description}"
    has_junior = _has_keyword(haystack, JUNIOR_PATTERNS)
    return has_devops and has_junior


def is_junior_devops_with_desc(title: str, description: str) -> bool:
    """Check if job is a junior DevOps role, also checking description for junior keywords.
    Use for sources where junior indicator might only be in description."""
    has_devops = _has_keyword(title, DEVOPS_PATTERNS)
    haystack = f"{title} {description}"
    has_junior = _has_keyword(haystack, JUNIOR_PATTERNS)
    return has_devops and has_junior


def is_devops_role(title: str, description: str = "") -> bool:
    """Check if job is a DevOps/Cloud role (devops keywords only)."""
    haystack = f"{title} {description}"
    return _has_keyword(haystack, DEVOPS_PATTERNS)