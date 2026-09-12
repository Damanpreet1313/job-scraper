import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.scrapers.locations import (
    is_ncr_location,
    detect_work_type,
    is_location_allowed,
    is_remote_friendly_country,
)


class TestLocationFiltering:
    def test_ncr_locations_detected(self):
        assert is_ncr_location("Noida") is True
        assert is_ncr_location("Gurugram") is True
        assert is_ncr_location("Gurgaon") is True
        assert is_ncr_location("Delhi") is True
        assert is_ncr_location("New Delhi") is True
        assert is_ncr_location("Faridabad") is True
        assert is_ncr_location("Ghaziabad") is True
        assert is_ncr_location("Greater Noida") is True
        assert is_ncr_location("NCR") is True

    def test_non_ncr_locations_rejected(self):
        assert is_ncr_location("Bangalore") is False
        assert is_ncr_location("Mumbai") is False
        assert is_ncr_location("Pune") is False
        assert is_ncr_location("Hyderabad") is False
        assert is_ncr_location("Remote") is False
        assert is_ncr_location("") is False
        assert is_ncr_location(None) is False

    def test_work_type_detection_remote(self):
        assert detect_work_type("Remote") == "remote"
        assert detect_work_type("Anywhere") == "remote"
        assert detect_work_type("Worldwide") == "remote"
        assert detect_work_type("Global") == "remote"
        assert detect_work_type("Distributed") == "remote"
        assert detect_work_type("Work from home") == "remote"
        assert detect_work_type("WFH") == "remote"

    def test_work_type_detection_onsite(self):
        assert detect_work_type("New York") == "onsite"
        assert detect_work_type("San Francisco") == "onsite"
        assert detect_work_type("Office") == "onsite"
        assert detect_work_type("On-site") == "onsite"
        assert detect_work_type("On site") == "onsite"
        assert detect_work_type("In-office") == "onsite"

    def test_work_type_detection_hybrid(self):
        assert detect_work_type("Hybrid") == "hybrid"
        assert detect_work_type("Hybrid - San Francisco") == "hybrid"

    def test_location_allowed_ncr_any_work_type(self):
        allowed, reason = is_location_allowed("Noida", "On-site work required")
        assert allowed is True
        assert "NCR" in reason

        allowed, reason = is_location_allowed("Gurugram", "Hybrid work model")
        assert allowed is True

        allowed, reason = is_location_allowed("Delhi", "Remote work")
        assert allowed is True

    def test_location_allowed_non_ncr_only_remote(self):
        allowed, reason = is_location_allowed("Bangalore", "Remote position")
        assert allowed is True
        assert "Remote" in reason

        allowed, reason = is_location_allowed("Bangalore", "On-site required")
        assert allowed is False
        assert "Non-NCR" in reason

        allowed, reason = is_location_allowed("Mumbai", "Hybrid work")
        assert allowed is False

    def test_location_allowed_unknown_work_type_ncr(self):
        allowed, reason = is_location_allowed("Noida", "")
        assert allowed is True

    def test_remote_friendly_countries(self):
        assert is_remote_friendly_country("United States") is True
        assert is_remote_friendly_country("Germany") is True
        assert is_remote_friendly_country("India") is True
        assert is_remote_friendly_country("Singapore") is True
        assert is_remote_friendly_country("Remote") is True
        assert is_remote_friendly_country("Worldwide") is True
        assert is_remote_friendly_country("") is True
        assert is_remote_friendly_country(None) is True