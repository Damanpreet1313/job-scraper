import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.scrapers.base import make_content_hash, normalize_job


def test_same_job_same_hash():
    h1 = make_content_hash("GitLab", "Site Reliability Engineer", "https://example.com/1")
    h2 = make_content_hash("gitlab", "site reliability engineer", "https://example.com/1")
    assert h1 == h2


def test_different_job_different_hash():
    h1 = make_content_hash("GitLab", "SRE", "https://example.com/1")
    h2 = make_content_hash("GitLab", "Backend Engineer", "https://example.com/2")
    assert h1 != h2


def test_normalize_job_strips_html():
    job = normalize_job(
        company="Acme",
        title="DevOps Engineer",
        location="Remote",
        url="https://example.com/job/1",
        source="greenhouse",
        posted_date="2026-07-01",
        description="<p>We need <b>Kubernetes</b> experience.</p>",
    )
    assert "<" not in job["description"]
    assert "Kubernetes" in job["description"]
    assert len(job["content_hash"]) == 64
