import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from fastapi.testclient import TestClient

from app.database import SessionLocal, init_db
from app.main import app
from app.models import Job

client = TestClient(app)


@pytest.fixture(scope="function", autouse=True)
def setup_db():
    init_db()
    now = datetime.utcnow()
    db = SessionLocal()
    try:
        db.query(Job).delete()
        db.commit()
        
        # Add test jobs with relative dates
        jobs = [
            Job(
                company="TestCorp",
                title="Junior DevOps Engineer",
                location="Noida",
                url="https://example.com/job1",
                source="remoteok",
                posted_date=(now - timedelta(days=1)).strftime("%Y-%m-%d"),
                posted_date_parsed=now - timedelta(days=1),
                description="AWS, Kubernetes, Terraform",
                content_hash="hash1",
                match_score=0.8,
                match_reason="Good match",
                matched=True,
                created_at=now,
            ),
            Job(
                company="AnotherCorp",
                title="Senior DevOps Engineer",
                location="Bangalore",
                url="https://example.com/job2",
                source="greenhouse",
                posted_date=(now - timedelta(days=5)).strftime("%Y-%m-%d"),
                posted_date_parsed=now - timedelta(days=5),
                description="Lead team, Kubernetes",
                content_hash="hash2",
                match_score=0.3,
                match_reason="Senior role",
                matched=False,
                created_at=now - timedelta(days=1),
            ),
            Job(
                company="RemoteCorp",
                title="DevOps Intern",
                location="Remote",
                url="https://example.com/job3",
                source="remotive",
                posted_date=(now - timedelta(hours=2)).strftime("%Y-%m-%d"),
                posted_date_parsed=now - timedelta(hours=2),
                description="Docker, CI/CD, Python",
                content_hash="hash3",
                match_score=0.6,
                match_reason="Junior role",
                matched=True,
                created_at=now - timedelta(hours=2),
            ),
        ]
        for job in jobs:
            db.add(job)
        db.commit()
    finally:
        db.close()
    yield
    # Cleanup
    db = SessionLocal()
    try:
        db.query(Job).delete()
        db.commit()
    finally:
        db.close()


class TestAPIEndpoints:
    def test_health_endpoint(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_list_jobs(self):
        response = client.get("/jobs")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert data["count"] == 3
        assert len(data["jobs"]) == 3

    def test_list_jobs_matched_only(self):
        response = client.get("/jobs?matched_only=true")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2  # Two matched jobs
        assert all(job["matched"] for job in data["jobs"])

    def test_list_jobs_by_source(self):
        response = client.get("/jobs?source=remoteok")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["jobs"][0]["source"] == "remoteok"

    def test_list_jobs_min_score(self):
        response = client.get("/jobs?min_score=0.5")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2  # Jobs with score >= 0.5
        assert all(job["match_score"] >= 0.5 for job in data["jobs"])

    def test_list_jobs_pagination(self):
        response = client.get("/jobs?limit=2&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2
        assert data["total"] == 3

        response = client.get("/jobs?limit=2&offset=2")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1

    def test_list_jobs_posted_since_days(self):
        response = client.get("/jobs?posted_since_days=2")
        assert response.status_code == 200
        data = response.json()
        # Should include jobs from last 2 days (job1 and job3)
        assert data["total"] == 2

    def test_get_job_by_id(self):
        response = client.get("/jobs/1")
        assert response.status_code == 200
        job = response.json()
        assert job["id"] == 1
        assert job["title"] == "Junior DevOps Engineer"
        assert "description" in job

    def test_get_job_not_found(self):
        response = client.get("/jobs/999")
        assert response.status_code == 200
        assert response.json() == {"error": "not found"}

    def test_stats_endpoint(self):
        response = client.get("/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["total_jobs"] == 3
        assert data["matched_jobs"] == 2
        assert "by_source" in data
        assert data["by_source"]["remoteok"] == 1
        assert data["by_source"]["greenhouse"] == 1
        assert data["by_source"]["remotive"] == 1

    def test_jobs_sorted_by_match_score_desc(self):
        response = client.get("/jobs")
        jobs = response.json()["jobs"]
        scores = [j["match_score"] for j in jobs]
        assert scores == sorted(scores, reverse=True)