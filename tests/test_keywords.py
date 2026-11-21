import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.scrapers.keywords import (
    is_senior,
    is_junior_devops,
    is_devops_role,
    is_junior_devops_with_desc,
)


class TestSeniorExclusion:
    def test_senior_titles_detected(self):
        senior_titles = [
            "Senior DevOps Engineer",
            "Sr. DevOps Engineer",
            "Sr DevOps Engineer",
            "Lead DevOps Engineer",
            "Principal DevOps Engineer",
            "Staff DevOps Engineer",
            "DevOps Architect",
            "DevOps Manager",
            "Director of DevOps",
            "VP Engineering",
            "Vice President Engineering",
            "Chief Technology Officer",
            "CTO",
            "Founder",
            "Co-founder",
            "Site Reliability Engineer II",
            "Site Reliability Engineer III",
            "SRE 2",
            "SRE 3",
            "Level 3 DevOps",
            "L3 DevOps Engineer",
            "E3 DevOps",
        ]
        for title in senior_titles:
            assert is_senior(title) is True, f"Failed for: {title}"

    def test_junior_titles_not_senior(self):
        junior_titles = [
            "Junior DevOps Engineer",
            "Entry Level DevOps Engineer",
            "DevOps Intern",
            "DevOps Trainee",
            "Graduate DevOps Engineer",
            "Associate DevOps Engineer",
            "New Grad DevOps",
            "DevOps Engineer I",
            "Level 1 DevOps",
            "L1 DevOps",
            "E1 DevOps",
            "Early Career DevOps",
        ]
        for title in junior_titles:
            assert is_senior(title) is False, f"Failed for: {title}"

    def test_mid_level_not_senior(self):
        mid_titles = [
            "DevOps Engineer",
            "Cloud Engineer",
            "Site Reliability Engineer",
            "Platform Engineer",
            "Infrastructure Engineer",
        ]
        for title in mid_titles:
            assert is_senior(title) is False, f"Failed for: {title}"


class TestJuniorDevOpsDetection:
    def test_junior_devops_detected(self):
        junior_devops = [
            ("Junior DevOps Engineer", "AWS, Kubernetes, CI/CD"),
            ("Entry Level DevOps Engineer", "Docker, Terraform, Python"),
            ("DevOps Intern", "Learning Kubernetes and AWS"),
            ("DevOps Trainee", "CI/CD pipelines, GitLab"),
            ("Graduate DevOps Engineer", "AWS, Terraform, Docker"),
            ("DevOps Engineer I", "Kubernetes, Helm, Prometheus"),
            ("Level 1 DevOps Engineer", "AWS, Docker, CI/CD"),
            ("New Grad DevOps", "Terraform, Kubernetes, Python"),
            ("Early Career DevOps", "Cloud, Docker, CI/CD"),
        ]
        for title, desc in junior_devops:
            assert is_junior_devops(title, desc) is True, f"Failed for: {title}"

    def test_senior_devops_rejected(self):
        senior_devops = [
            ("Senior DevOps Engineer", "AWS, Kubernetes, Terraform"),
            ("Lead DevOps Engineer", "Manage team, Kubernetes"),
            ("Principal DevOps Engineer", "Architecture, AWS"),
        ]
        for title, desc in senior_devops:
            assert is_junior_devops(title, desc) is False, f"Failed for: {title}"

    def test_non_devops_rejected(self):
        non_devops = [
            ("Junior Frontend Engineer", "React, TypeScript"),
            ("Entry Level Backend Engineer", "Python, Django"),
            ("Software Engineer Intern", "Java, Spring"),
        ]
        for title, desc in non_devops:
            assert is_junior_devops(title, desc) is False, f"Failed for: {title}"

    def test_devops_role_detected(self):
        devops_titles = [
            "DevOps Engineer",
            "Site Reliability Engineer",
            "SRE",
            "Platform Engineer",
            "Cloud Engineer",
            "Infrastructure Engineer",
            "Production Engineer",
            "Build Engineer",
            "Release Engineer",
            "Deployment Engineer",
            "DevSecOps Engineer",
            "Kubernetes Engineer",
            "Terraform Engineer",
        ]
        for title in devops_titles:
            assert is_devops_role(title) is True, f"Failed for: {title}"

    def test_non_devops_role_rejected(self):
        non_devops = [
            "Frontend Engineer",
            "Backend Engineer",
            "Full Stack Engineer",
            "Mobile Engineer",
            "Data Engineer",
            "ML Engineer",
            "QA Engineer",
        ]
        for title in non_devops:
            assert is_devops_role(title) is False, f"Failed for: {title}"

    def test_false_positives_handled(self):
        false_positives = [
            "Senior Engineer - mentor junior team members",
            "Lead Developer - manage junior engineers",
            "Principal Engineer - guide junior staff",
            "Engineering Manager - supervise junior developers",
        ]
        for title in false_positives:
            desc = "We need someone to mentor junior team members and guide junior engineers"
            assert is_junior_devops(title, desc) is False, f"False positive for: {title}"