import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.scrapers.base import (
    make_content_hash,
    make_content_hash_normalized,
    strip_html,
    parse_posted_date,
    normalize_title_company,
    normalize_job,
)


class TestBaseFunctions:
    def test_make_content_hash_consistent(self):
        h1 = make_content_hash("GitLab", "Site Reliability Engineer", "https://example.com/1")
        h2 = make_content_hash("gitlab", "site reliability engineer", "https://example.com/1")
        assert h1 == h2

    def test_make_content_hash_different_jobs(self):
        h1 = make_content_hash("GitLab", "SRE", "https://example.com/1")
        h2 = make_content_hash("GitLab", "Backend Engineer", "https://example.com/2")
        assert h1 != h2

    def test_normalize_title_company(self):
        company, title = normalize_title_company("GitLab Inc.", "  Senior  DevOps Engineer  ")
        assert company == "gitlab"
        assert title == "senior devops engineer"

    def test_make_content_hash_normalized(self):
        h1 = make_content_hash_normalized("GitLab Inc.", "Senior DevOps Engineer", "https://example.com/1")
        h2 = make_content_hash_normalized("gitlab", "senior devops engineer", "https://example.com/1")
        assert h1 == h2

    def test_strip_html(self):
        html = "<p>We need <b>Kubernetes</b> experience.</p>"
        stripped = strip_html(html)
        assert "<" not in stripped
        assert "Kubernetes" in stripped

    def test_strip_html_empty(self):
        assert strip_html("") == ""
        assert strip_html(None) == ""

    def test_parse_posted_date_iso(self):
        dt = parse_posted_date("2024-01-15T10:30:00Z")
        assert dt == datetime(2024, 1, 15, 10, 30, 0)

    def test_parse_posted_date_iso_with_microseconds(self):
        dt = parse_posted_date("2024-01-15T10:30:00.123456Z")
        assert dt == datetime(2024, 1, 15, 10, 30, 0, 123456)

    def test_parse_posted_date_iso_with_timezone(self):
        dt = parse_posted_date("2024-01-15T10:30:00+00:00")
        assert dt == datetime(2024, 1, 15, 10, 30, 0)

    def test_parse_posted_date_simple(self):
        dt = parse_posted_date("2024-01-15")
        assert dt == datetime(2024, 1, 15)

    def test_parse_posted_date_us_format(self):
        dt = parse_posted_date("01/15/2024")
        assert dt == datetime(2024, 1, 15)

    def test_parse_posted_date_eu_format(self):
        dt = parse_posted_date("15/01/2024")
        assert dt == datetime(2024, 1, 15)

    def test_parse_posted_date_month_name(self):
        dt = parse_posted_date("15 Jan 2024")
        assert dt == datetime(2024, 1, 15)

    def test_parse_posted_date_full_month(self):
        dt = parse_posted_date("January 15, 2024")
        assert dt == datetime(2024, 1, 15)

    def test_parse_posted_date_none(self):
        assert parse_posted_date(None) is None
        assert parse_posted_date("") is None
        assert parse_posted_date("invalid") is None

    def test_normalize_job_includes_parsed_date(self):
        job = normalize_job(
            company="TestCo",
            title="DevOps Engineer",
            location="Remote",
            url="https://example.com/job",
            source="test",
            posted_date="2024-01-15",
            description="<p>We need <b>Kubernetes</b></p>",
        )
        assert job["company"] == "TestCo"
        assert job["title"] == "DevOps Engineer"
        assert job["location"] == "Remote"
        assert job["url"] == "https://example.com/job"
        assert job["source"] == "test"
        assert job["posted_date"] == "2024-01-15"
        assert job["posted_date_parsed"] == datetime(2024, 1, 15)
        assert "<" not in job["description"]
        assert "Kubernetes" in job["description"]
        assert len(job["content_hash"]) == 64

    def test_normalize_job_none_posted_date(self):
        job = normalize_job(
            company="TestCo",
            title="DevOps Engineer",
            location="Remote",
            url="https://example.com/job",
            source="test",
            posted_date=None,
            description="Description",
        )
        assert job["posted_date_parsed"] is None