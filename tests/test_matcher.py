import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.matcher import score_jobs

RESUME = "DevOps engineer. AWS, Kubernetes, Terraform, Docker, CI/CD, Python, FastAPI."


def test_relevant_job_scores_higher_than_irrelevant():
    jobs = [
        {"title": "DevOps Engineer", "description": "AWS, Kubernetes, Terraform, CI/CD pipelines."},
        {"title": "Pastry Chef", "description": "Bake bread and cakes at our restaurant."},
    ]
    scored = score_jobs(jobs, resume_text=RESUME)
    assert scored[0]["match_score"] > scored[1]["match_score"]


def test_empty_resume_gives_zero_scores():
    jobs = [{"title": "DevOps Engineer", "description": "AWS, Kubernetes"}]
    scored = score_jobs(jobs, resume_text="")
    assert scored[0]["match_score"] == 0.0


def test_no_jobs_returns_empty_list():
    assert score_jobs([], resume_text=RESUME) == []


def test_job_structure_preserved():
    jobs = [{"title": "DevOps Engineer", "description": "AWS", "url": "https://example.com/job1"}]
    scored = score_jobs(jobs, resume_text=RESUME)
    assert "match_score" in scored[0]
    assert scored[0]["url"] == "https://example.com/job1"
    assert scored[0]["title"] == "DevOps Engineer"