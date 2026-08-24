"""Location filtering utilities for job preferences."""
import re
from typing import Optional

from app.config import (
    DELHI_NCR_LOCATIONS,
    NCR_ALLOWED_WORK_TYPES,
    NON_NCR_ALLOWED_WORK_TYPES,
    REMOTE_FRIENDLY_COUNTRIES,
)


# Pre-compile patterns for location matching
NCR_PATTERNS = [re.compile(rf"\b{re.escape(loc)}\b", re.IGNORECASE) for loc in DELHI_NCR_LOCATIONS]

# More specific patterns - only match work arrangement phrases, not incidental words
# Avoid false positives like "worldwide" in "agencies worldwide" or "distributed" in "distributed systems"
REMOTE_PATTERNS = [
    re.compile(r"\b(fully\s+remote|fully-remote|100%\s*remote|work\s+(from|remotely)\b|remote\s+(work|position|job|role|opportunity)\b|wfh\b|work\s+from\s+home\b|distributed\s+(team|company|workforce)\b|anywhere\s+(in\s+the\s+world)?\b|global\s+(remote|work))\b", re.IGNORECASE),
]
# Keep simple patterns for location field only (not description)
LOCATION_REMOTE_PATTERNS = [
    re.compile(r"\b(remote|anywhere|worldwide|global|distributed)\b", re.IGNORECASE),
]

ONSITE_PATTERNS = [
    re.compile(r"\b(on-?site|on site|office|in-?office|in office)\b", re.IGNORECASE),
]
HYBRID_PATTERNS = [
    re.compile(r"\bhybrid\b", re.IGNORECASE),
]


def _has_pattern(text: str, patterns: list[re.Pattern]) -> bool:
    """Check if any pattern matches in text."""
    return any(p.search(text) for p in patterns)


def is_ncr_location(location: str) -> bool:
    """Check if location is in Delhi NCR region."""
    if not location:
        return False
    return _has_pattern(location, NCR_PATTERNS)


def detect_work_type(location: str, description: str = "") -> str:
    """Detect work type from location and description.
    Returns: 'remote', 'onsite', 'hybrid', or 'unknown'"""
    # Check location field with simple patterns
    loc_lower = location.lower()
    if _has_pattern(loc_lower, LOCATION_REMOTE_PATTERNS):
        return "remote"
    if _has_pattern(loc_lower, HYBRID_PATTERNS):
        return "hybrid"
    if _has_pattern(loc_lower, ONSITE_PATTERNS):
        return "onsite"
    
    # Check description with more specific patterns (avoid false positives like "remote teams")
    if description:
        desc_lower = description.lower()
        if _has_pattern(desc_lower, REMOTE_PATTERNS):
            return "remote"
    
    # If location is a specific city/office but no explicit work type, assume onsite
    if location and location.lower() not in ["remote", "anywhere", "worldwide", "global", "distributed"]:
        return "onsite"
    
    return "unknown"


def is_location_allowed(location: str, description: str = "") -> tuple[bool, str]:
    """
    Check if job location is allowed based on user preferences.
    
    Rules:
    - Delhi NCR locations: allow onsite, hybrid, remote
    - All other locations: only allow remote
    
    Returns: (allowed: bool, reason: str)
    """
    if not location:
        return True, "no location specified"
    
    location_lower = location.lower().strip()
    work_type = detect_work_type(location, description)
    
    # Check if it's NCR
    if is_ncr_location(location_lower):
        if work_type in NCR_ALLOWED_WORK_TYPES or work_type == "unknown":
            return True, f"NCR location ({location}) allows {work_type or 'any'}"
        return False, f"NCR location but work type '{work_type}' not in allowed list"
    
    # Non-NCR: only remote allowed
    if work_type == "remote":
        return True, f"Remote work allowed for {location}"
    
    return False, f"Non-NCR location '{location}' requires remote work (detected: {work_type})"


def is_remote_friendly_country(location: str) -> bool:
    """Check if location is in a remote-friendly country."""
    if not location:
        return True  # No location = could be remote
    location_lower = location.lower()
    return any(country in location_lower for country in REMOTE_FRIENDLY_COUNTRIES)