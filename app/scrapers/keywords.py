"""Keyword matching utilities with word-boundary support."""
import re
from typing import List

from app.config import DEVOPS_KEYWORDS, JUNIOR_KEYWORDS, SENIOR_EXCLUSION_KEYWORDS


def _compile_patterns(keywords: List[str]) -> List[re.Pattern]:
    """Compile patterns with flexible boundaries for keywords with punctuation or spaces."""
    patterns = []
    for kw in keywords:
        # For keywords ending with punctuation (like "sr."), use flexible boundary
        if kw.endswith((".", "!", "?")):
            escaped = re.escape(kw)
            patterns.append(re.compile(rf"(^|\s){escaped}(\s|$|[.,;:])", re.IGNORECASE))
        # For keywords with leading/trailing spaces (like " 2 "), use flexible boundaries
        elif kw.startswith(" ") or kw.endswith(" "):
            stripped = kw.strip()
            escaped = re.escape(stripped)
            patterns.append(re.compile(rf"(^|\s){escaped}(\s|$|[.,;:])", re.IGNORECASE))
        else:
            escaped = re.escape(kw)
            patterns.append(re.compile(rf"\b{escaped}\b", re.IGNORECASE))
    return patterns


# Pre-compile regex patterns for word-boundary matching
DEVOPS_PATTERNS = _compile_patterns(DEVOPS_KEYWORDS)
JUNIOR_PATTERNS = _compile_patterns(JUNIOR_KEYWORDS)
SENIOR_PATTERNS = _compile_patterns(SENIOR_EXCLUSION_KEYWORDS)

# False positive patterns - junior keywords used in non-junior contexts
JUNIOR_FALSE_POSITIVE_PATTERNS = [
    re.compile(r"\bjunior\s+(team\s+)?members?\b", re.IGNORECASE),      # "junior team members"
    re.compile(r"\bjunior\s+(engineer|developer|dev|staff)\b", re.IGNORECASE),  # "junior engineer" (refers to others)
    re.compile(r"\bmentor\s+(junior|entry)\b", re.IGNORECASE),          # "mentor junior"
    re.compile(r"\blead\s+(junior|entry)\b", re.IGNORECASE),            # "lead junior"
    re.compile(r"\bmanage\s+(junior|entry)\b", re.IGNORECASE),          # "manage junior"
    re.compile(r"\bsupervis\w+\s+(junior|entry)\b", re.IGNORECASE),     # "supervise junior"
    re.compile(r"\btrain\s+(junior|entry)\b", re.IGNORECASE),           # "train junior"
    re.compile(r"\bguide\s+(junior|entry)\b", re.IGNORECASE),           # "guide junior"
    re.compile(r"\bcollaborate\s+with\s+(junior|entry)\b", re.IGNORECASE),  # "collaborate with junior"
    re.compile(r"\bwork\s+with\s+(junior|entry)\b", re.IGNORECASE),     # "work with junior"
]


def _has_keyword(text: str, patterns: List[re.Pattern]) -> bool:
    """Check if any pattern matches in text."""
    return any(p.search(text) for p in patterns)


def _has_false_positive(text: str) -> bool:
    """Check if junior keyword matches are likely false positives."""
    return _has_keyword(text, JUNIOR_FALSE_POSITIVE_PATTERNS)


def is_senior(title: str) -> bool:
    """Check if title indicates a senior-level role."""
    return _has_keyword(title, SENIOR_PATTERNS)


def is_junior_devops(title: str, description: str) -> bool:
    """Check if job is a junior DevOps role (requires BOTH devops AND junior keywords).
    Checks title + description for junior keywords since many roles list
    '0-2 years', 'entry level', 'new grad' in description not title.
    Excludes false positives like 'mentor junior team members'."""
    has_devops = _has_keyword(title, DEVOPS_PATTERNS)
    haystack = f"{title} {description}"
    has_junior = _has_keyword(haystack, JUNIOR_PATTERNS)
    
    # Exclude false positives where "junior" refers to other people, not the role
    if has_junior and _has_false_positive(haystack):
        has_junior = False
    
    return has_devops and has_junior


def is_junior_devops_with_desc(title: str, description: str) -> bool:
    """Check if job is a junior DevOps role, also checking description for junior keywords.
    Use for sources where junior indicator might only be in description."""
    return is_junior_devops(title, description)


def is_devops_role(title: str, description: str = "") -> bool:
    """Check if job is a DevOps/Cloud role (devops keywords only)."""
    haystack = f"{title} {description}"
    return _has_keyword(haystack, DEVOPS_PATTERNS)